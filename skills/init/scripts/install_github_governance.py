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
PR_CHECK_WORKFLOW_PATH = Path(".github/workflows/pr-check.yml")


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


def _label_names(config: dict[str, Any], group: str) -> list[str]:
    return [label["name"] for label in config["labels"].get(group, [])]


def render_pr_check_workflow(config: dict[str, Any]) -> str:
    threshold = int(config["churn_threshold"])
    allowed_bases_json = json.dumps(config["allowed_base"], ensure_ascii=False)
    non_logic_globs_json = json.dumps(config["non_logic_globs"], ensure_ascii=False)
    size_labels_json = json.dumps(_label_names(config, "size"), ensure_ascii=False)
    override_labels = _label_names(config, "override")
    override_label = override_labels[0] if override_labels else "size/override"
    override_label_json = json.dumps(override_label, ensure_ascii=False)
    return f"""name: PR size check

on:
  pull_request:
    types: [opened, edited, synchronize, reopened, ready_for_review, labeled, unlabeled]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  pr-size:
    runs-on: ubuntu-latest
    steps:
      - name: Enforce PR logic churn policy
        uses: actions/github-script@v7
        env:
          CHURN_THRESHOLD: '{threshold}'
          ALLOWED_BASES: '{allowed_bases_json}'
          NON_LOGIC_GLOBS: '{non_logic_globs_json}'
          SIZE_LABELS: '{size_labels_json}'
          OVERRIDE_LABEL: '{override_label_json}'
        with:
          script: |
            // === SIZE-CHECK-LOGIC-START ===
            const threshold = Number(process.env.CHURN_THRESHOLD);
            const allowedBases = JSON.parse(process.env.ALLOWED_BASES);
            const nonLogicGlobs = JSON.parse(process.env.NON_LOGIC_GLOBS);
            const sizeLabels = JSON.parse(process.env.SIZE_LABELS);
            const overrideLabel = JSON.parse(process.env.OVERRIDE_LABEL);
            const pr = context.payload.pull_request;

            function escapeRegex(value) {{
              return value.replace(/[|\\{{}}()[\\]^$+*?.]/g, '\\$&');
            }}

            function globToRegex(glob) {{
              let regex = '^';
              for (let i = 0; i < glob.length; i += 1) {{
                const char = glob[i];
                if (char === '*') {{
                  if (glob[i + 1] === '*') {{
                    i += 1;
                    if (glob[i + 1] === '/') {{
                      i += 1;
                      regex += '(?:.*/)?';
                    }} else {{
                      regex += '.*';
                    }}
                  }} else {{
                    regex += '[^/]*';
                  }}
                }} else if (char === '?') {{
                  regex += '[^/]';
                }} else {{
                  regex += escapeRegex(char);
                }}
              }}
              return new RegExp(`${{regex}}$`);
            }}

            const nonLogicMatchers = nonLogicGlobs.map((glob) => globToRegex(glob));
            function isNonLogicPath(path) {{
              const basename = path.split('/').pop();
              return nonLogicMatchers.some((matcher) => matcher.test(path) || matcher.test(basename));
            }}

            function allowedBaseMatches(base) {{
              return allowedBases.some((pattern) => globToRegex(pattern).test(base));
            }}

            function sizeBucket(churn) {{
              if (churn <= 100) return sizeLabels[0];
              if (churn <= 300) return sizeLabels[1];
              if (churn <= threshold) return sizeLabels[2];
              return sizeLabels[3];
            }}

            if (!allowedBaseMatches(pr.base.ref)) {{
              core.setFailed(`Base branch '${{pr.base.ref}}' is not allowed for issue governance.`);
              return;
            }}
            if (pr.draft) {{
              core.info('Draft PR; skipping size enforcement.');
              return;
            }}
            const currentLabels = pr.labels.map((label) => label.name);
            const hasOverride = currentLabels.includes(overrideLabel);
            const files = await github.paginate(github.rest.pulls.listFiles, {{
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: pr.number,
              per_page: 100,
            }});
            const logicChurn = files
              .filter((file) => !isNonLogicPath(file.filename))
              .reduce((sum, file) => sum + file.additions + file.deletions, 0);
            const bucket = sizeBucket(logicChurn);
            for (const label of sizeLabels.filter((label) => currentLabels.includes(label) && label !== bucket)) {{
              await github.rest.issues.removeLabel({{
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: pr.number,
                name: label,
              }}).catch((error) => {{
                if (error.status !== 404) throw error;
              }});
            }}
            if (!currentLabels.includes(bucket)) {{
              await github.rest.issues.addLabels({{
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: pr.number,
                labels: [bucket],
              }});
            }}
            if (logicChurn > threshold && !hasOverride) {{
              core.setFailed(`Logic churn ${{logicChurn}} exceeds threshold ${{threshold}}; add '${{overrideLabel}}' only with reviewer-approved exception.`);
            }} else {{
              core.info(`Logic churn ${{logicChurn}} classified as ${{bucket}}.`);
            }}
            // === SIZE-CHECK-LOGIC-END ===
"""


def desired_files(config: dict[str, Any]) -> dict[Path, str]:
    return {
        ISSUE_TEMPLATE_PATH: render_issue_template(config),
        AUTO_LABEL_WORKFLOW_PATH: render_auto_label_workflow(config),
        PR_CHECK_WORKFLOW_PATH: render_pr_check_workflow(config),
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
        print("GitHub governance labels, issue template, auto-label workflow, and PR check workflow are already up to date.")
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
