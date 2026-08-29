#!/usr/bin/env python3
"""Effects adapter for a planned AGENTS lifecycle map."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path

from _transaction import apply
from lifecycle_core import SNAPSHOT_NAME, build_managed_outputs, canonical_json, discover_topology, validate_ownership_snapshot, validate_snapshot


def _emit(value: dict, stream: object | None = None) -> None:
    if stream is None:
        stream = sys.stdout
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")), file=stream)


def _root(value: str) -> Path:
    root = Path(value).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("repository root is not a directory")
    return root


def _outputs(root: Path, max_depth: int, claude_shim: str) -> dict:
    prior = _prior_snapshot(root)
    shim_policy = str(prior["last_applied_topology"]["shim_policy"]) if claude_shim == "keep" and prior is not None else ("off" if claude_shim == "keep" else claude_shim)
    topology = discover_topology(root, max_depth=max_depth, shim_policy=shim_policy)
    if not isinstance(topology, dict):
        raise ValueError("topology discovery returned an invalid result")
    topology["_prior_owned_artifacts"] = prior["owned_artifacts"] if prior is not None else []
    outputs = build_managed_outputs(topology)
    if (
        not isinstance(outputs, dict)
        or not isinstance(outputs.get("effects"), list)
        or not isinstance(outputs.get("snapshot"), dict)
    ):
        raise ValueError("managed-output planning returned an invalid result")
    return outputs


def _is_byte_identical_noop(root: Path, outputs: dict) -> bool:
    if outputs["effects"]:
        return False
    path = root / SNAPSHOT_NAME
    try:
        info = os.lstat(path)
        return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode) and path.read_bytes() == canonical_json(outputs["snapshot"], pretty=True)
    except (FileNotFoundError, OSError):
        return False


def _prior_snapshot(root: Path) -> dict | None:
    path = root / SNAPSHOT_NAME
    try:
        info = os.lstat(path)
        if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
            return None
        snapshot = json.loads(path.read_bytes().decode("utf-8"))
        validate_snapshot(snapshot)
        validation = validate_ownership_snapshot(root, snapshot)
        if not validation.get("valid", False):
            return None
        return snapshot
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Map repository instructions into managed AGENTS files.")
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: current directory)")
    parser.add_argument("--max-depth", type=int, default=3, metavar="N")
    parser.add_argument("--claude-shim", choices=("keep", "on", "off"), default="keep")
    parser.add_argument("--accept", action="append", default=[], metavar="ID")
    args = parser.parse_args(argv)
    try:
        if not 1 <= args.max_depth <= 32:
            raise ValueError("--max-depth must be in 1..32")
        root = _root(args.root)
        outputs = _outputs(root, args.max_depth, args.claude_shim)
        validate_snapshot(outputs["snapshot"])
        if _is_byte_identical_noop(root, outputs):
            result = {"exit_code": 0, "phase": "complete", "effects": [], "no_op": True}
        else:
            result = apply(root, outputs["effects"], set(args.accept), snapshot_payload=outputs["snapshot"])
        if not isinstance(result, dict):
            raise ValueError("transaction application returned an invalid result")
        _emit({"operation": "map", **result})
        return int(result.get("exit_code", 0))
    except (OSError, ValueError) as error:
        _emit({"diagnostics": [{"code": "map-blocked", "message": str(error)}], "operation": "map"}, sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
