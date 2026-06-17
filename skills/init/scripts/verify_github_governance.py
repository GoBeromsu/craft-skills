#!/usr/bin/env python3
"""Verify GitHub governance labels without mutating the repository."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check required GitHub governance labels without mutation.")
    parser.add_argument("--repo-root", default=".", help="repository root (default: current directory)")
    parser.add_argument("--check", action="store_true", help="verify labels and exit non-zero when any are missing")
    args = parser.parse_args(argv)

    if not args.check:
        print("ERROR: verify_github_governance.py is non-mutating; pass --check.", file=sys.stderr)
        return 2

    repo_root = Path(args.repo_root).resolve()
    try:
        missing = missing_labels(repo_root)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if missing:
        print("Missing GitHub governance labels:")
        for name in missing:
            print(f"- {name}")
        return 1

    print("All GitHub governance labels are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
