#!/usr/bin/env python3
"""Read-only adapter for the AGENTS lifecycle audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lifecycle_core import audit, operation_root


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
    parser = argparse.ArgumentParser(description="Inspect an AGENTS lifecycle without changing it.")
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: current directory)")
    args = parser.parse_args(argv)
    try:
        root = _root(args.root)
        with operation_root(root):
            report = audit(root)
        if not isinstance(report, dict):
            raise ValueError("audit returned an invalid report")
        _emit(report)
        findings = report.get("findings", [])
        return 1 if findings else 0
    except (OSError, ValueError) as error:
        _emit({"diagnostics": [{"code": "audit-unavailable", "message": str(error)}]}, sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
