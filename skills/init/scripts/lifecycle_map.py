#!/usr/bin/env python3
"""Effects adapter for a planned AGENTS lifecycle map."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path

from _transaction import apply, recover
from lifecycle_core import JOURNAL_NAME, SNAPSHOT_NAME, build_managed_outputs, canonical_json, discover_topology, probe_loading, validate_ownership_snapshot, validate_snapshot
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


def _emit(value: dict, stream: object | None = None) -> None:
    if stream is None:
        stream = sys.stdout
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")), file=stream)


def _root(value: str) -> Path:
    root = Path(value).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("repository root is not a directory")
    return root


def _outputs(root: Path, max_depth: int, claude_shim: str, loading_receipt: dict | None = None) -> dict:
    prior = _prior_snapshot(root)
    shim_policy = str(prior["last_applied_topology"]["shim_policy"]) if claude_shim == "keep" and prior is not None else ("off" if claude_shim == "keep" else claude_shim)
    loading_evidence = probe_loading(root, loading_receipt) if loading_receipt is not None else None
    if loading_evidence is None:
        topology = discover_topology(root, max_depth=max_depth, shim_policy=shim_policy)
    else:
        topology = discover_topology(root, max_depth=max_depth, shim_policy=shim_policy, loading_evidence=loading_evidence)
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
            raise ValueError("ownership snapshot is unsafe")
        descriptor = os.open(path, os.O_RDONLY | _NOFOLLOW)
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                raise ValueError("ownership snapshot is unsafe")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            snapshot = json.loads(b"".join(chunks).decode("utf-8"))
        finally:
            os.close(descriptor)
        validate_snapshot(snapshot)
        validation = validate_ownership_snapshot(root, snapshot)
        if not validation.get("valid", False):
            raise ValueError("ownership snapshot drift blocks mapping")
        return snapshot
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"ownership snapshot is unreadable or invalid: {error}") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Map repository instructions into managed AGENTS files.")
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: current directory)")
    parser.add_argument("--max-depth", type=int, default=3, metavar="N")
    parser.add_argument("--claude-shim", choices=("keep", "on", "off"), default="keep")
    parser.add_argument("--accept", action="append", default=[], metavar="ID")
    parser.add_argument("--loading-evidence", type=Path, metavar="JSON")
    args = parser.parse_args(argv)
    try:
        if not 1 <= args.max_depth <= 32:
            raise ValueError("--max-depth must be in 1..32")
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
                code = "map-blocked" if "recovery requires acceptance:" in str(error) else "map-failed"
                _emit({"diagnostics": [{"code": code, "message": str(error)}], "operation": "map"}, sys.stderr)
                return 2 if code == "map-blocked" else 3
            _emit({"operation": "map", **result})
            return 0
        loading_receipt = None
        if args.loading_evidence is not None:
            loading_receipt = json.loads(args.loading_evidence.read_text(encoding="utf-8"))
            if not isinstance(loading_receipt, dict):
                raise ValueError("--loading-evidence must contain a JSON object")
        outputs = (
            _outputs(root, args.max_depth, args.claude_shim)
            if loading_receipt is None
            else _outputs(root, args.max_depth, args.claude_shim, loading_receipt)
        )
        validate_snapshot(outputs["snapshot"])
        offered = {proposal["id"] for proposal in outputs.get("proposals", [])}
        unmatched = sorted(set(args.accept) - offered)
        if unmatched:
            raise ValueError("accepted proposal is not offered by current evidence: " + ", ".join(unmatched))
        missing = sorted(
            {
                effect["proposal_id"]
                for effect in outputs["effects"]
                if effect.get("proposal_id") and effect["proposal_id"] not in set(args.accept)
            }
        )
        if missing:
            raise ValueError("mapping requires acceptance: " + ", ".join(missing))
        if not (root / JOURNAL_NAME).exists() and _is_byte_identical_noop(root, outputs):
            result = {"exit_code": 0, "phase": "complete", "effects": [], "no_op": True}
        else:
            try:
                result = apply(root, outputs["effects"], set(args.accept), snapshot_payload=outputs["snapshot"])
            except (OSError, RuntimeError, ValueError) as error:
                _emit({"diagnostics": [{"code": "map-failed", "message": str(error)}], "operation": "map"}, sys.stderr)
                return 3
        if not isinstance(result, dict):
            raise ValueError("transaction application returned an invalid result")
        _emit({"operation": "map", **result})
        return int(result.get("exit_code", 0))
    except (OSError, ValueError) as error:
        _emit({"diagnostics": [{"code": "map-blocked", "message": str(error)}], "operation": "map"}, sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
