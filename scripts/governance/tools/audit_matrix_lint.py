#!/usr/bin/env python3
"""Validate the craft-skills audit matrix (docs/governance/audit-matrix.md).

Blocking checks:
- the matrix table exposes exactly the nine required fields, in order;
- the table has exactly the expected number of rows (default 17);
- no cell is empty;
- no duplicate skill names;
- every disposition is one of candidate / change / no-change.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REQUIRED_FIELDS = [
    "skill",
    "계약준수",
    "과잉지시",
    "라우팅겹침",
    "가이드정합",
    "원칙반영도",
    "Layer-1",
    "처분",
    "증거링크",
]
ALLOWED_DISPOSITIONS = {"candidate", "change", "no-change"}


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _find_matrix_table(text: str) -> tuple[list[str], list[list[str]]]:
    """Return (header, body rows) of the first table whose header starts with 'skill'."""
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        header = _split_row(stripped)
        if header and header[0].lower() == "skill":
            body: list[list[str]] = []
            for row_line in lines[idx + 1 :]:
                row_stripped = row_line.strip()
                if not row_stripped.startswith("|"):
                    break
                cells = _split_row(row_stripped)
                if set("".join(cells).replace(" ", "")) <= {"-", ":"}:
                    continue  # separator
                body.append(cells)
            return header, body
    raise SystemExit("no matrix table with a 'skill' header column found")


def lint(text: str, expected_rows: int) -> list[str]:
    errors: list[str] = []
    header, body = _find_matrix_table(text)

    if header != REQUIRED_FIELDS:
        errors.append(
            f"header mismatch: expected {REQUIRED_FIELDS}, found {header}"
        )

    if len(body) != expected_rows:
        errors.append(f"expected {expected_rows} rows, found {len(body)}")

    seen: set[str] = set()
    for lineno, cells in enumerate(body, start=1):
        if len(cells) != len(REQUIRED_FIELDS):
            errors.append(f"row {lineno}: expected {len(REQUIRED_FIELDS)} cells, found {len(cells)}")
            continue
        row = dict(zip(REQUIRED_FIELDS, cells))
        for field, value in row.items():
            if not value:
                errors.append(f"row {lineno} ({row['skill'] or '?'}): empty cell in {field!r}")
        skill = row["skill"]
        if skill in seen:
            errors.append(f"row {lineno}: duplicate skill {skill!r}")
        seen.add(skill)
        if row["처분"] not in ALLOWED_DISPOSITIONS:
            errors.append(
                f"row {lineno} ({skill}): disposition {row['처분']!r} not in {sorted(ALLOWED_DISPOSITIONS)}"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="audit matrix markdown file")
    parser.add_argument("--rows", type=int, default=17, help="expected body row count")
    args = parser.parse_args()

    errors = lint(args.path.read_text(encoding="utf-8"), args.rows)
    for error in errors:
        print(f"audit-matrix-lint: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"audit-matrix-lint: OK ({args.rows} rows, {len(REQUIRED_FIELDS)} fields)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
