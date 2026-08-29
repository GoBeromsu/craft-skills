#!/usr/bin/env python3
"""Run the package-local loader sentinel probe and report only observations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lifecycle_core import probe_loading


def _emit(value: dict, stream: object | None = None) -> None:
    if stream is None:
        stream = sys.stdout
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")), file=stream)


def _root(value: str) -> Path:
    root = Path(value).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("repository root is not a directory")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe observable root, child, and sibling instruction loading.")
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: current directory)")
    parser.add_argument(
        "--observations-json",
        type=Path,
        help="JSON observation receipt from an applicable sentinel run; this adapter never runs commands",
    )
    args = parser.parse_args(argv)
    try:
        observations = None
        if args.observations_json is not None:
            observations = json.loads(args.observations_json.read_text(encoding="utf-8"))
            if not isinstance(observations, dict):
                raise ValueError("observations JSON must be an object")
        result = probe_loading(_root(args.root), observations)
        if not isinstance(result, dict):
            raise ValueError("loading probe returned an invalid result")
        # The core owns classification: this adapter intentionally publishes
        # raw root/child/sibling observations rather than inferring support.
        _emit(result)
        return int(result.get("exit_code", 0))
    except (OSError, ValueError) as error:
        _emit({"diagnostics": [{"code": "loading-probe-unavailable", "message": str(error)}]}, sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
