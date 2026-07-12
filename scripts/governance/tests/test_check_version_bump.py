"""Tests for the skill version and changelog diff checker."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_TOOL = _ROOT / "scripts" / "governance" / "tools" / "check_version_bump.py"


def _skill(version: str, body: str = "original") -> str:
    return f"""---
name: demo
description: Demo skill.
metadata:
  version: {version}
---

# demo

{body}
"""


class CheckVersionBumpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        package = self.root / "skills" / "demo"
        package.mkdir(parents=True)
        (package / "SKILL.md").write_text(_skill("1.0.0"), encoding="utf-8")
        (package / "CHANGELOG.md").write_text("- 2026-01-01 — initial release\n", encoding="utf-8")
        subprocess.run(["git", "init"], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "skills"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "base"], cwd=self.root, check=True, capture_output=True, text=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _run(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(_TOOL), "--diff-base", "HEAD~1"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )

    def _commit_change(self, version: str, body: str, changelog: str) -> None:
        package = self.root / "skills" / "demo"
        (package / "SKILL.md").write_text(_skill(version, body), encoding="utf-8")
        (package / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
        subprocess.run(["git", "add", "skills"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "change"], cwd=self.root, check=True, capture_output=True, text=True)

    def test_accepts_substantive_change_with_increased_version_and_dated_changelog(self) -> None:
        self._commit_change("1.0.1", "updated guidance", "- 2026-07-12 — updated guidance\n- 2026-01-01 — initial release\n")
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_rejects_missing_version_bump_and_dated_changelog_entry(self) -> None:
        self._commit_change("1.0.0", "updated guidance", "- 2026-01-01 — initial release\n")
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertIn("metadata.version must increase", result.stdout)
        self.assertIn("CHANGELOG.md must gain a dated bullet", result.stdout)

    def test_rejects_version_only_churn(self) -> None:
        self._commit_change("1.0.1", "original", "- 2026-07-12 — maintenance\n- 2026-01-01 — initial release\n")
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertIn("version bump has no package content change", result.stdout)
    def test_accepts_new_package_with_note(self) -> None:
        package = self.root / "skills" / "new-demo"
        package.mkdir()
        (package / "SKILL.md").write_text(_skill("1.0.0", "new guidance"), encoding="utf-8")
        (package / "CHANGELOG.md").write_text("- 2026-07-12 — initial release\n", encoding="utf-8")
        subprocess.run(["git", "add", "skills"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "new package"], cwd=self.root, check=True, capture_output=True, text=True)
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("new package", result.stdout)


if __name__ == "__main__":
    unittest.main()
