"""CLI exit-contract tests for scripts/governance/tools (subprocess-based)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_TOOLS = _ROOT / "scripts" / "governance" / "tools"
_FIXTURE_NAMES = _ROOT / "scripts" / "governance" / "fixtures" / "omo-skills-25.txt"

LEDGER_OK = """# doc

## 처분 원장

| omo skill | disposition | 근거 요약 |
|---|---|---|
| alpha | candidate | reason a |
| beta | rejected | reason b |
"""

LEDGER_BAD = """# doc

## 처분 원장

| omo skill | disposition | 근거 요약 |
|---|---|---|
| alpha | candidate | reason a |
| alpha | maybe | reason b |
"""


def _run(tool: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_TOOLS / tool), *args],
        capture_output=True,
        text=True,
        cwd=_ROOT,
    )


def _tmp(content: str) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    handle.write(content)
    handle.close()
    return Path(handle.name)


class CountLedgerRowsCliTest(unittest.TestCase):
    def test_expect_match_exits_zero(self) -> None:
        path = _tmp(LEDGER_OK)
        result = _run("count_ledger_rows.py", str(path), "--section", "처분 원장", "--expect", "2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "2")

    def test_expect_mismatch_exits_one(self) -> None:
        path = _tmp(LEDGER_OK)
        result = _run("count_ledger_rows.py", str(path), "--section", "처분 원장", "--expect", "3")
        self.assertEqual(result.returncode, 1)
        self.assertIn("expected 3 rows", result.stderr)

    def test_missing_section_exits_nonzero(self) -> None:
        path = _tmp(LEDGER_OK)
        result = _run("count_ledger_rows.py", str(path), "--section", "없는 섹션")
        self.assertNotEqual(result.returncode, 0)

    def test_ledger_semantics_reject_duplicate_and_bad_disposition(self) -> None:
        path = _tmp(LEDGER_BAD)
        result = _run("count_ledger_rows.py", str(path), "--section", "처분 원장", "--ledger")
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate skill", result.stderr)
        self.assertIn("disposition", result.stderr)

    def test_names_file_set_equality_enforced(self) -> None:
        path = _tmp(LEDGER_OK)
        result = _run(
            "count_ledger_rows.py",
            str(path),
            "--section",
            "처분 원장",
            "--names-file",
            str(_FIXTURE_NAMES),
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("ledger missing skills", result.stderr)

    def test_committed_ledger_passes_full_contract(self) -> None:
        result = _run(
            "count_ledger_rows.py",
            "docs/research/omo-analysis.md",
            "--section",
            "처분 원장",
            "--expect",
            "25",
            "--ledger",
            "--names-file",
            str(_FIXTURE_NAMES),
        )
        self.assertEqual(result.returncode, 0, result.stderr)


class AuditMatrixLintCliTest(unittest.TestCase):
    def test_committed_matrix_exits_zero(self) -> None:
        result = _run("audit_matrix_lint.py", "docs/governance/audit-matrix.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OK", result.stdout)

    def test_row_count_flag_mismatch_exits_one(self) -> None:
        result = _run("audit_matrix_lint.py", "docs/governance/audit-matrix.md", "--rows", "16")
        self.assertEqual(result.returncode, 1)
        self.assertIn("expected 16 rows", result.stderr)


if __name__ == "__main__":
    unittest.main()
