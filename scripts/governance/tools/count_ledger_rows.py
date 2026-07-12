#!/usr/bin/env python3
"""Count markdown table body rows inside a named section of a document.

Used by the omo-analysis acceptance check: the disposition ledger section
must contain exactly one table row per omo skill (25 at the pinned commit).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def _section_lines(text: str, section: str) -> list[str]:
    """Return the lines belonging to the first heading whose text contains *section*.

    The section ends at the next heading of the same or higher level.
    Raises SystemExit when the section is missing.
    """
    lines = text.splitlines()
    start = None
    level = 0
    for idx, line in enumerate(lines):
        match = _HEADING_RE.match(line)
        if match and section in match.group(2):
            start = idx + 1
            level = len(match.group(1))
            break
    if start is None:
        raise SystemExit(f"section containing {section!r} not found")
    body: list[str] = []
    for line in lines[start:]:
        match = _HEADING_RE.match(line)
        if match and len(match.group(1)) <= level:
            break
        body.append(line)
    return body


def count_table_rows(text: str, section: str) -> int:
    """Count table body rows (excluding header and separator) in the section."""
    rows = 0
    in_table = False
    header_seen = False
    for line in _section_lines(text, section):
        stripped = line.strip()
        if stripped.startswith("|"):
            if not in_table:
                in_table = True
                header_seen = True
                continue  # header row
            if header_seen and set(stripped.replace("|", "").replace(" ", "")) <= {"-", ":"}:
                header_seen = False
                continue  # separator row
            rows += 1
        else:
            in_table = False
            header_seen = False
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="markdown document to inspect")
    parser.add_argument("--section", required=True, help="substring of the section heading")
    parser.add_argument(
        "--expect",
        type=int,
        default=None,
        help="exit non-zero unless the row count equals this value",
    )
    args = parser.parse_args()

    count = count_table_rows(args.path.read_text(encoding="utf-8"), args.section)
    print(count)
    if args.expect is not None and count != args.expect:
        print(
            f"expected {args.expect} rows in section {args.section!r}, found {count}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
