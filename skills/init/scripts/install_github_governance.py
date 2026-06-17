#!/usr/bin/env python3
"""Install GitHub governance labels, issue templates, and auto-label workflow."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from governance_config import all_label_specs, resolve_config, type_label_names

ISSUE_TEMPLATE_PATH = Path(".github/ISSUE_TEMPLATE/issue.yml")
AUTO_LABEL_WORKFLOW_PATH = Path(".github/workflows/auto-label.yml")


def _run_gh(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )




def list_existing_labels(repo_root: Path) -> dict[str, dict[str, str]]:
    result = _run_gh(
        ["label", "list", "--limit", "1000", "--json", "name,color,description"],
        repo_root,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh label list failed")
    labels = json.loads(result.stdout or "[]")
    return {str(item["name"]): item for item in labels}


def build_label_change_plan(config: dict[str, Any], existing: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    for spec in all_label_specs(config):
        current = existing.get(spec["name"])
        if current is None:
            plan.append({"action": "create", "label": spec})
            continue
        updates: dict[str, str] = {}
        for key in ("color", "description"):
            if str(current.get(key, "")).lstrip("#") != spec[key]:
                updates[key] = spec[key]
        if updates:
            plan.append({"action": "update", "label": spec, "updates": updates})
    return plan


def render_issue_template(config: dict[str, Any]) -> str:
    options = "\n".join(f"        - {name}" for name in type_label_names(config))
    return f"""name: Issue
description: File work that should be governed by issue-driven labels.
title: ""
labels: []
body:
  - type: markdown
    attributes:
      value: |
        ### Type
        Select exactly one Type. This heading is parsed by the auto-label workflow.
  - type: dropdown
    id: type
    attributes:
      label: Type
      description: Select the issue Type label to apply.
      options:
{options}
    validations:
      required: true
  - type: textarea
    id: summary
    attributes:
      label: Summary
      description: Describe the requested work.
    validations:
      required: true
"""


def render_auto_label_workflow(config: dict[str, Any]) -> str:
    type_labels_json = json.dumps(type_label_names(config), ensure_ascii=False)
    return f"""name: Auto-label issue Type

on:
  issues:
    types: [opened, edited]

permissions:
  issues: write
  contents: read

jobs:
  issue-type:
    runs-on: ubuntu-latest
    steps:
      - name: Apply exactly one Type label
        uses: actions/github-script@v7
        env:
          TYPE_LABELS: '{type_labels_json}'
        with:
          script: |
            const typeLabels = JSON.parse(process.env.TYPE_LABELS);
            const body = context.payload.issue.body || '';
            const match = body.match(/^### Type\\s*\\r?\\n+([^#\\r\\n][^\\r\\n]*)/m);
            if (!match) {{
              core.setFailed('Missing ### Type section; refusing to apply a default type label.');
              return;
            }}
            const selected = match[1].trim();
            if (!typeLabels.includes(selected)) {{
              core.setFailed(`Unknown Type '${{selected}}'; refusing to apply a default type label.`);
              return;
            }}
            for (const label of typeLabels.filter((label) => label !== selected)) {{
              await github.rest.issues.removeLabel({{
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                name: label,
              }}).catch((error) => {{
                if (error.status !== 404) throw error;
              }});
            }}
            await github.rest.issues.addLabels({{
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              labels: [selected],
            }});
"""


def desired_files(config: dict[str, Any]) -> dict[Path, str]:
    return {
        ISSUE_TEMPLATE_PATH: render_issue_template(config),
        AUTO_LABEL_WORKFLOW_PATH: render_auto_label_workflow(config),
    }


def build_file_change_plan(repo_root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    for relative_path, desired in desired_files(config).items():
        path = repo_root / relative_path
        if not path.exists():
            plan.append({"action": "write", "path": str(relative_path), "reason": "missing"})
        elif path.read_text(encoding="utf-8") != desired:
            plan.append({"action": "write", "path": str(relative_path), "reason": "outdated"})
    return plan


def build_change_plan(config: dict[str, Any], existing: dict[str, dict[str, str]], repo_root: Path | None = None) -> list[dict[str, Any]]:
    plan = build_label_change_plan(config, existing)
    if repo_root is not None:
        plan.extend(build_file_change_plan(repo_root, config))
    return plan


def apply_label_change_plan(plan: list[dict[str, Any]], repo_root: Path) -> None:
    for change in plan:
        label = change["label"]
        if change["action"] == "create":
            result = _run_gh(
                [
                    "label", "create", label["name"],
                    "--color", label["color"],
                    "--description", label["description"],
                ],
                repo_root,
            )
        else:
            result = _run_gh(
                [
                    "label", "edit", label["name"],
                    "--color", label["color"],
                    "--description", label["description"],
                ],
                repo_root,
            )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"gh label {change['action']} failed")


def apply_file_change_plan(repo_root: Path, config: dict[str, Any]) -> None:
    for relative_path, desired in desired_files(config).items():
        path = repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(desired, encoding="utf-8")


def apply_change_plan(plan: list[dict[str, Any]], repo_root: Path, config: dict[str, Any] | None = None) -> None:
    label_plan = [change for change in plan if change["action"] in {"create", "update"}]
    if label_plan:
        apply_label_change_plan(label_plan, repo_root)
    if config is not None and any(change["action"] == "write" for change in plan):
        apply_file_change_plan(repo_root, config)


def print_change_plan(plan: list[dict[str, Any]]) -> None:
    if not plan:
        print("GitHub governance labels, issue template, and auto-label workflow are already up to date.")
        return
    print("GitHub governance change plan:")
    for change in plan:
        if change["action"] in {"create", "update"}:
            label = change["label"]
            if change["action"] == "create":
                print(f"CREATE label {label['name']} color={label['color']} description={label['description']}")
            else:
                updates = ", ".join(f"{key}={value}" for key, value in sorted(change["updates"].items()))
                print(f"UPDATE label {label['name']} {updates}")
        else:
            print(f"WRITE {change['path']} reason={change['reason']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install GitHub governance from resolved init config.")
    parser.add_argument("--repo-root", default=".", help="repository root (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="print change plan without mutating labels or files")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    try:
        config = resolve_config(repo_root)
        existing = list_existing_labels(repo_root)
        plan = build_change_plan(config, existing, repo_root)
        print_change_plan(plan)
        if not args.dry_run and plan:
            apply_change_plan(plan, repo_root, config)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
