#!/usr/bin/env python3
"""Install GitHub governance labels for a repository."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from governance_config import all_label_specs, resolve_config


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


def build_change_plan(config: dict[str, Any], existing: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
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


def apply_change_plan(plan: list[dict[str, Any]], repo_root: Path) -> None:
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


def print_change_plan(plan: list[dict[str, Any]]) -> None:
    if not plan:
        print("GitHub governance labels are already up to date.")
        return
    print("GitHub governance label change plan:")
    for change in plan:
        label = change["label"]
        if change["action"] == "create":
            print(f"CREATE {label['name']} color={label['color']} description={label['description']}")
        else:
            updates = ", ".join(f"{key}={value}" for key, value in sorted(change["updates"].items()))
            print(f"UPDATE {label['name']} {updates}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install GitHub governance labels from resolved init config.")
    parser.add_argument("--repo-root", default=".", help="repository root (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="print change plan without mutating labels")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    try:
        config = resolve_config(repo_root)
        existing = list_existing_labels(repo_root)
        plan = build_change_plan(config, existing)
        print_change_plan(plan)
        if not args.dry_run and plan:
            apply_change_plan(plan, repo_root)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
