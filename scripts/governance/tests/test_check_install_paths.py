"""Tests for runtime install path consistency checking."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_TOOL = _ROOT / "scripts" / "governance" / "tools" / "check_install_paths.py"


class CheckInstallPathsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / ".hermes").mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_surfaces(self, clone_path: str = ".agents/skills/craft-skills") -> None:
        shared = f"""/plugin marketplace add GoBeromsu/craft-skills
/plugin install craft-skills@craft-skills
.codex-plugin/plugin.json
Codex auxiliary clone path: `{clone_path}`
Hermes mount path: `~/dev/GoBeromsu/craft-skills/skills`
"""
        for name in ("README.md", "AGENTS.md"):
            (self.root / name).write_text(shared, encoding="utf-8")
        (self.root / "install.sh").write_text(
            shared
            + f"""CLONE_DIR="${{PWD}}/{clone_path}"
SKILLS_PATH="${{HOME}}/dev/GoBeromsu/craft-skills/skills"
""",
            encoding="utf-8",
        )
        (self.root / ".hermes" / "README.md").write_text(
            "Hermes mount path: `~/dev/GoBeromsu/craft-skills/skills`\n", encoding="utf-8"
        )

    def _run(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(_TOOL), "--root", str(self.root)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_accepts_consistent_runtime_declarations(self) -> None:
        self._write_surfaces()
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_rejects_inconsistent_codex_clone_path(self) -> None:
        self._write_surfaces()
        agents = self.root / "AGENTS.md"
        agents.write_text(
            agents.read_text(encoding="utf-8").replace(
                ".agents/skills/craft-skills", ".agents/skills/other-skills"
            ),
            encoding="utf-8",
        )
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertIn("codex_clone: inconsistent declarations", result.stdout)
    def test_rejects_stale_install_comment_when_assignment_changes(self) -> None:
        self._write_surfaces()
        install = self.root / "install.sh"
        install.write_text(
            install.read_text(encoding="utf-8").replace(
                'CLONE_DIR="${PWD}/.agents/skills/craft-skills"',
                'CLONE_DIR="${PWD}/.agents/skills/other-skills"',
            ),
            encoding="utf-8",
        )
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertIn("codex_clone: inconsistent declarations", result.stdout)

    def test_rejects_inconsistent_hermes_mount_path(self) -> None:
        self._write_surfaces()
        hermes = self.root / ".hermes" / "README.md"
        hermes.write_text("Hermes mount path: `~/other/craft-skills/skills`\n", encoding="utf-8")
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertIn("hermes: inconsistent declarations", result.stdout)


if __name__ == "__main__":
    unittest.main()
