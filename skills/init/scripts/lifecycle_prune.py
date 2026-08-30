#!/usr/bin/env python3
"""Guarded effects adapter for stale, proven-managed lifecycle content."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path

from _transaction import apply, recover
from lifecycle_core import JOURNAL_NAME, plan_prune, validate_ownership_snapshot

_SNAPSHOT = ".agents-map.json"


def _emit(value: dict, stream: object | None = None) -> None:
    if stream is None:
        stream = sys.stdout
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
    parser.add_argument("--accept", action="append", default=[], metavar="ID")
    args = parser.parse_args(argv)
    try:
        root = _root(args.root)
        journal_path = root / JOURNAL_NAME
        try:
            journal_info = os.lstat(journal_path)
        except FileNotFoundError:
            journal_info = None
        if journal_info is not None:
            if not stat.S_ISREG(journal_info.st_mode):
                raise ValueError("transaction journal is unsafe")
            try:
                result = recover(root, set(args.accept))
            except RuntimeError as error:
                code = "prune-blocked" if "recovery requires acceptance:" in str(error) else "prune-failed"
                _emit({"diagnostics": [{"code": code, "message": str(error)}], "operation": "prune"}, sys.stderr)
                return 2 if code == "prune-blocked" else 3
            _emit({"operation": "prune", **result})
            return 0
        snapshot = _snapshot(root)
        validation = validate_ownership_snapshot(root, snapshot)
        if not isinstance(validation, dict) or not validation.get("valid", False):
            raise ValueError("ownership snapshot validation failed")
        plan = plan_prune(root, snapshot, set(args.accept))
        if not isinstance(plan, dict) or not isinstance(plan.get("effects"), list):
            raise ValueError("prune planning returned an invalid result")
        # An acceptance that the current evidence no longer offers is stale consent:
        # refuse it instead of committing a snapshot the operator never approved.
        unmatched = sorted(set(args.accept) - {proposal["id"] for proposal in plan["proposals"]})
        if unmatched:
            raise ValueError("accepted proposal is not offered by current evidence: " + ", ".join(unmatched))
        if not plan["effects"]:
            # The default is no accepted deletion: report the offered proposals and
            # leave every byte, mode, and the committed snapshot untouched.
            _emit({"operation": "prune", "exit_code": 0, "phase": "complete", "effects": [], "no_op": True, "proposals": plan["proposals"]})
            return 0
        try:
            result = apply(root, plan["effects"], set(args.accept), snapshot_payload=plan["snapshot"], operation="prune")
        except (OSError, RuntimeError, ValueError) as error:
            _emit({"diagnostics": [{"code": "prune-failed", "message": str(error)}], "operation": "prune"}, sys.stderr)
            return 3
        if not isinstance(result, dict):
            raise ValueError("transaction application returned an invalid result")
        _emit({"operation": "prune", **result})
        return int(result.get("exit_code", 0))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        _emit({"diagnostics": [{"code": "prune-blocked", "message": str(error)}], "operation": "prune"}, sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
