"""Tests for scripts/governance/tools (count_ledger_rows, audit_matrix_lint)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent.parent / "tools"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _TOOLS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


count_ledger_rows = _load("count_ledger_rows")
audit_matrix_lint = _load("audit_matrix_lint")


LEDGER_DOC = """# omo analysis

## 처분 원장

| omo skill | disposition | reason |
|---|---|---|
| git-master | candidate | read-only history mode |
| ultrawork | rejected | runtime execution mode |
| frontend | no-delta | covered locally |

## 다음 섹션

| a | b |
|---|---|
| 1 | 2 |
"""


class CountLedgerRowsTest(unittest.TestCase):
    def test_counts_only_section_body_rows(self) -> None:
        self.assertEqual(count_ledger_rows.count_table_rows(LEDGER_DOC, "처분 원장"), 3)

    def test_other_section_not_counted(self) -> None:
        self.assertEqual(count_ledger_rows.count_table_rows(LEDGER_DOC, "다음 섹션"), 1)

    def test_missing_section_raises(self) -> None:
        with self.assertRaises(SystemExit):
            count_ledger_rows.count_table_rows(LEDGER_DOC, "없는 섹션")


def _matrix(rows: list[str]) -> str:
    header = "| " + " | ".join(audit_matrix_lint.REQUIRED_FIELDS) + " |"
    sep = "|" + "---|" * len(audit_matrix_lint.REQUIRED_FIELDS)
    return "# audit matrix\n\n" + "\n".join([header, sep, *rows]) + "\n"


def _row(skill: str, disposition: str = "no-change", empty_field: int | None = None) -> str:
    cells = [skill, "pass", "low", "none", "good", "high", "pass", disposition, "skills/x/SKILL.md:1"]
    if empty_field is not None:
        cells[empty_field] = ""
    return "| " + " | ".join(cells) + " |"


class AuditMatrixLintTest(unittest.TestCase):
    def test_clean_matrix_passes(self) -> None:
        text = _matrix([_row(f"skill-{i}") for i in range(17)])
        self.assertEqual(audit_matrix_lint.lint(text, 17), [])

    def test_wrong_row_count_fails(self) -> None:
        text = _matrix([_row("only-one")])
        errors = audit_matrix_lint.lint(text, 17)
        self.assertTrue(any("expected 17 rows" in error for error in errors))

    def test_duplicate_skill_fails(self) -> None:
        text = _matrix([_row("dup"), _row("dup")])
        errors = audit_matrix_lint.lint(text, 2)
        self.assertTrue(any("duplicate skill" in error for error in errors))

    def test_empty_cell_fails(self) -> None:
        text = _matrix([_row("a", empty_field=4)])
        errors = audit_matrix_lint.lint(text, 1)
        self.assertTrue(any("empty cell" in error for error in errors))

    def test_bad_disposition_fails(self) -> None:
        text = _matrix([_row("a", disposition="maybe")])
        errors = audit_matrix_lint.lint(text, 1)
        self.assertTrue(any("disposition" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
