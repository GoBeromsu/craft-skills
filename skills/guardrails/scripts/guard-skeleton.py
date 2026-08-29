#!/usr/bin/env python3
"""Starter domain-guard (reusable across tiers).

A guard is a small executable that checks ONE rule and exits non-zero with a
legible reason when violated. The same guard wires into:
  - tier 1 (runtime hook): invoked on the agent's tool input,
  - tier 2 (lint):         invoked over changed files,
  - tier 3 (pre-commit):   invoked over staged files.

Keep it cheap, correct, stable (the 3 gates). If this guard grows its own test
suite, it has become application code — move the rule to a softer surface.

Usage:
  guard-skeleton.py <path> [<path> ...]
Exit:
  0  clean
  1  violation (reason on stderr — name the rule AND the fix)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Example rule: forbid a TODO marker that ships as if it were done.
# Replace with your real, cheap, stable check.
FORBIDDEN = re.compile(r"TODO\(ship\)")


def check(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None  # unreadable/binary: out of scope, not a violation
    if FORBIDDEN.search(text):
        return (
            f"{path}: contains TODO(ship) — resolve or remove it before this lands. "
            "(rule: no ship-blocking TODO; fix: finish the work or delete the marker)"
        )
    return None


def main(argv: list[str]) -> int:
    violations = [msg for arg in argv if (msg := check(Path(arg)))]
    for msg in violations:
        print(f"guard: {msg}", file=sys.stderr)
    return 1 if violations else 0


def _selfcheck() -> None:
    # ponytail minimum: prove the guard actually fires.
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        bad = Path(d) / "bad.txt"
        bad.write_text("x = 1  # TODO(ship) wire this\n", encoding="utf-8")
        good = Path(d) / "good.txt"
        good.write_text("x = 1\n", encoding="utf-8")
        assert check(bad) is not None, "guard must flag a violation"
        assert check(good) is None, "guard must pass clean input"
    print("guard-skeleton self-check: OK")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selfcheck":
        _selfcheck()
        raise SystemExit(0)
    raise SystemExit(main(sys.argv[1:]))
