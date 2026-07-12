#!/usr/bin/env python3
"""Count and validate markdown table rows inside a named section of a document.

Acceptance tool for the omo-analysis audit workflow (invoked manually and by
the audit acceptance checks documented in docs/research/omo-analysis.md and
docs/governance/audit-matrix.md; CI wiring is decided in the harness-profile
work package). Beyond counting, ``--ledger`` enforces the disposition-ledger
semantic contract: exact header, three cells per row, unique skill names,
allowed dispositions, and (optionally) exact set equality with a checked-in
name fixture so a duplicated or fabricated inventory cannot pass.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")

LEDGER_HEADER = ["omo skill", "disposition", "근거 요약"]
LEDGER_DISPOSITIONS = {"candidate", "rejected", "no-delta"}


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


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    joined = "".join(cells).replace(" ", "")
    return bool(joined) and set(joined) <= {"-", ":"}


def _section_table(text: str, section: str) -> tuple[list[str] | None, list[list[str]]]:
    """Return (header, body rows) of the first table in the section."""
    header: list[str] | None = None
    rows: list[list[str]] = []
    in_table = False
    for line in _section_lines(text, section):
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = _split_row(stripped)
            if not in_table:
                in_table = True
                header = cells
                continue
            if _is_separator(cells):
                continue
            rows.append(cells)
        elif in_table:
            break
    return header, rows


def count_table_rows(text: str, section: str) -> int:
    """Count table body rows (excluding header and separator) in the section."""
    _, rows = _section_table(text, section)
    return len(rows)


def validate_ledger(text: str, section: str, expected_names: set[str] | None) -> list[str]:
    """Validate the disposition-ledger semantic contract; return error strings."""
    errors: list[str] = []
    header, rows = _section_table(text, section)
    if header != LEDGER_HEADER:
        errors.append(f"ledger header mismatch: expected {LEDGER_HEADER}, found {header}")
    seen: set[str] = set()
    for lineno, cells in enumerate(rows, start=1):
        if len(cells) != len(LEDGER_HEADER):
            errors.append(f"ledger row {lineno}: expected {len(LEDGER_HEADER)} cells, found {len(cells)}")
            continue
        name, disposition, reason = cells
        if not name or not reason:
            errors.append(f"ledger row {lineno}: empty cell")
        if name in seen:
            errors.append(f"ledger row {lineno}: duplicate skill {name!r}")
        seen.add(name)
        if disposition not in LEDGER_DISPOSITIONS:
            errors.append(
                f"ledger row {lineno} ({name}): disposition {disposition!r} not in {sorted(LEDGER_DISPOSITIONS)}"
            )
    if expected_names is not None and seen != expected_names:
        missing = sorted(expected_names - seen)
        extra = sorted(seen - expected_names)
        if missing:
            errors.append(f"ledger missing skills: {missing}")
        if extra:
            errors.append(f"ledger unexpected skills: {extra}")
    return errors


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
    parser.add_argument(
        "--ledger",
        action="store_true",
        help="validate the disposition-ledger semantic contract (header, cells, uniqueness, dispositions)",
    )
    parser.add_argument(
        "--names-file",
        type=Path,
        default=None,
        help="newline-separated skill-name fixture; requires exact set equality (implies --ledger)",
    )
    args = parser.parse_args()

    text = args.path.read_text(encoding="utf-8")
    count = count_table_rows(text, args.section)
    print(count)

    failed = False
    if args.expect is not None and count != args.expect:
        print(
            f"expected {args.expect} rows in section {args.section!r}, found {count}",
            file=sys.stderr,
        )
        failed = True

    if args.ledger or args.names_file is not None:
        expected_names: set[str] | None = None
        if args.names_file is not None:
            expected_names = {
                line.strip()
                for line in args.names_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            }
        for error in validate_ledger(text, args.section, expected_names):
            print(f"ledger-lint: {error}", file=sys.stderr)
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
