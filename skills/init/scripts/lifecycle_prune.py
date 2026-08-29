#!/usr/bin/env python3
"""Guarded effects adapter for stale, proven-managed lifecycle content."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _transaction import apply
from lifecycle_core import plan_prune, validate_ownership_snapshot

_SNAPSHOT = ".agents-map.json"


def _emit(value: dict, stream: object = sys.stdout) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")), file=stream)


def _root(value: str) -> Path:
    root = Path(value).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("repository root is not a directory")
    return root


def _snapshot(root: Path) -> dict:
    path = root / _SNAPSHOT
    # resolve(strict=True) rejects a missing snapshot and containment rejects a
    # symlinked snapshot before its contents can influence deletion planning.
    if path.is_symlink():
        raise ValueError("ownership snapshot must not be a symlink")
    resolved = path.resolve(strict=True)
    if resolved.parent != root or not resolved.is_file():
        raise ValueError("ownership snapshot is not a regular root-local file")
    with resolved.open("r", encoding="utf-8", newline="") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("ownership snapshot must be an object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prune only stale regions proven managed by the ownership snapshot.")
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: current directory)")
    parser.add_argument("--accept", action="append", default=[], metavar="ID", required=True)
    args = parser.parse_args(argv)
    try:
        root = _root(args.root)
        snapshot = _snapshot(root)
        validation = validate_ownership_snapshot(root, snapshot)
        if not isinstance(validation, dict) or not validation.get("valid", False):
            raise ValueError("ownership snapshot validation failed")
        plan = plan_prune(root, snapshot, set(args.accept))
        if not isinstance(plan, dict) or not isinstance(plan.get("effects"), list):
            raise ValueError("prune planning returned an invalid result")
        result = apply(root, plan["effects"], set(args.accept), snapshot_payload=plan["snapshot"], operation="prune")
        if not isinstance(result, dict):
            raise ValueError("transaction application returned an invalid result")
        _emit({"operation": "prune", **result})
        return int(result.get("exit_code", 0))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        _emit({"diagnostics": [{"code": "prune-blocked", "message": str(error)}], "operation": "prune"}, sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
