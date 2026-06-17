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
from install_github_governance import AUTO_LABEL_WORKFLOW_PATH, ISSUE_TEMPLATE_PATH, render_auto_label_workflow, render_issue_template


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

    print("All GitHub governance labels, issue template, and auto-label workflow are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
