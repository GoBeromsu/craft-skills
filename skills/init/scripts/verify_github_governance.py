#!/usr/bin/env python3
"""Verify GitHub governance labels, issue template, and auto-label workflow."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from governance_config import all_label_specs, resolve_config, type_label_names
from install_github_governance import AUTO_LABEL_WORKFLOW_PATH, ISSUE_TEMPLATE_PATH, PR_CHECK_WORKFLOW_PATH, render_auto_label_workflow, render_issue_template, render_pr_check_workflow


def _run_gh(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def existing_label_names(repo_root: Path) -> set[str]:
    result = _run_gh(
        ["label", "list", "--limit", "1000", "--json", "name"],
        repo_root,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh label list failed")
    labels = json.loads(result.stdout or "[]")
    return {str(item["name"]) for item in labels}


def missing_labels(repo_root: Path) -> list[str]:
    config = resolve_config(repo_root)
    expected = [label["name"] for label in all_label_specs(config)]
    present = existing_label_names(repo_root)
    return [name for name in expected if name not in present]




def extract_template_type_options(text: str) -> list[str]:
    lines = text.splitlines()
    in_type_dropdown = False
    in_options = False
    options_indent = -1
    options: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == "id: type":
            in_type_dropdown = True
            continue
        if not in_type_dropdown:
            continue
        indent = len(line) - len(line.lstrip(" "))
        if stripped == "options:":
            in_options = True
            options_indent = indent
            continue
        if in_options:
            if indent <= options_indent and stripped:
                break
            match = re.match(r"\s*-\s+(.+?)\s*$", line)
            if match:
                options.append(match.group(1))
    return options


def auto_label_type_labels(text: str) -> list[str] | None:
    match = re.search(r"TYPE_LABELS:\s*'([^']+)'", text)
    if not match:
        return None
    try:
        labels = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    if not isinstance(labels, list) or not all(isinstance(item, str) for item in labels):
        return None
    return labels


def extract_size_check_logic(text: str) -> str | None:
    match = re.search(r"// === SIZE-CHECK-LOGIC-START ===\n(?P<body>.*?)\n\s*// === SIZE-CHECK-LOGIC-END ===", text, re.DOTALL)
    return match.group("body") if match else None


def workflow_env_value(text: str, name: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(name)}:\s*'([^']*)'\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def workflow_env_json(text: str, name: str) -> object | None:
    value = workflow_env_value(text, name)
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def pr_check_resolved_errors(text: str, config: dict[str, object]) -> list[str]:
    errors: list[str] = []
    logic = extract_size_check_logic(text)
    if logic is None:
        return ["PR check workflow is missing an extractable SIZE-CHECK-LOGIC block."]

    threshold_value = workflow_env_value(text, "CHURN_THRESHOLD")
    if threshold_value is None or int(threshold_value) != int(config["churn_threshold"]):
        errors.append("PR check workflow threshold does not match resolved config.")
    if workflow_env_json(text, "ALLOWED_BASES") != config["allowed_base"]:
        errors.append("PR check workflow allowed bases do not match resolved config.")
    if workflow_env_json(text, "NON_LOGIC_GLOBS") != config["non_logic_globs"]:
        errors.append("PR check workflow non-logic globs do not match resolved config.")
    size_labels = [label["name"] for label in config["labels"]["size"]]  # type: ignore[index]
    if workflow_env_json(text, "SIZE_LABELS") != size_labels:
        errors.append("PR check workflow size labels do not match resolved config.")
    override_labels = [label["name"] for label in config["labels"].get("override", [])]  # type: ignore[union-attr,index]
    expected_override = override_labels[0] if override_labels else "size/override"
    if workflow_env_json(text, "OVERRIDE_LABEL") != expected_override:
        errors.append("PR check workflow override label does not match resolved config.")

    behavior_fragments = [
        "function isNonLogicPath(path)",
        "function allowedBaseMatches(base)",
        "function sizeBucket(churn)",
        "logicChurn > threshold && !hasOverride",
        "github.paginate(github.rest.pulls.listFiles",
        "pr.draft",
    ]
    for fragment in behavior_fragments:
        if fragment not in logic:
            errors.append(f"PR check workflow logic is missing behavior fragment: {fragment}")
    return errors


def governance_file_errors(repo_root: Path) -> list[str]:
    config = resolve_config(repo_root)
    expected_types = type_label_names(config)
    errors: list[str] = []

    template = repo_root / ISSUE_TEMPLATE_PATH
    if not template.exists():
        errors.append(f"Missing issue template: {ISSUE_TEMPLATE_PATH}")
    else:
        text = template.read_text(encoding="utf-8")
        if "### Type" not in text:
            errors.append("Issue template must contain a literal ### Type heading.")
        if extract_template_type_options(text) != expected_types:
            errors.append("Issue template Type options do not match resolved type labels.")
        if text != render_issue_template(config):
            errors.append("Issue template content is not the resolved installer output.")

    workflow = repo_root / AUTO_LABEL_WORKFLOW_PATH
    if not workflow.exists():
        errors.append(f"Missing auto-label workflow: {AUTO_LABEL_WORKFLOW_PATH}")
    else:
        text = workflow.read_text(encoding="utf-8")
        if auto_label_type_labels(text) != expected_types:
            errors.append("Auto-label workflow TYPE_LABELS do not match resolved type labels.")
        required_fragments = [
            "Missing ### Type section; refusing to apply a default type label.",
            "Unknown Type",
            "core.setFailed",
            "labels: [selected]",
            "typeLabels.filter((label) => label !== selected)",
        ]
        for fragment in required_fragments:
            if fragment not in text:
                errors.append(f"Auto-label workflow missing fail-closed mapping fragment: {fragment}")
        if text != render_auto_label_workflow(config):
            errors.append("Auto-label workflow content is not the resolved installer output.")

    pr_check = repo_root / PR_CHECK_WORKFLOW_PATH
    if not pr_check.exists():
        errors.append(f"Missing PR check workflow: {PR_CHECK_WORKFLOW_PATH}")
    else:
        text = pr_check.read_text(encoding="utf-8")
        errors.extend(pr_check_resolved_errors(text, config))
        if text != render_pr_check_workflow(config):
            errors.append("PR check workflow content is not the resolved installer output.")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check required GitHub governance without mutation.")
    parser.add_argument("--repo-root", default=".", help="repository root (default: current directory)")
    parser.add_argument("--check", action="store_true", help="verify governance and exit non-zero on drift")
    args = parser.parse_args(argv)

    if not args.check:
        print("ERROR: verify_github_governance.py is non-mutating; pass --check.", file=sys.stderr)
        return 2

    repo_root = Path(args.repo_root).resolve()
    try:
        missing = missing_labels(repo_root)
        file_errors = governance_file_errors(repo_root)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if missing or file_errors:
        if missing:
            print("Missing GitHub governance labels:")
            for name in missing:
                print(f"- {name}")
        if file_errors:
            print("GitHub governance file drift:")
            for error in file_errors:
                print(f"- {error}")
        return 1

    print("All GitHub governance labels, issue template, auto-label workflow, and PR check workflow are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
