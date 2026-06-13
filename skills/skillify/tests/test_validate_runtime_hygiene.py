#!/usr/bin/env python3
"""Tests for skillify runtime hygiene guard."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "skills/skillify/scripts/validate-runtime-hygiene.py"


class RuntimeHygieneGuardTest(unittest.TestCase):
    def run_guard(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), "--root", str(root), *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_rejects_literal_home_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "skills/demo/SKILL.md"
            target.parent.mkdir(parents=True)
            leaked_path = "/Users/" + "someone/projects/my-vault/notes"
            target.write_text(f"VAULT={leaked_path}\n", encoding="utf-8")

            result = self.run_guard(root, "skills/demo/SKILL.md")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("RUNTIME_HOME_PATH", result.stderr)

    def test_accepts_env_indirection_and_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "skills/demo/SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text(
                "VAULT=${VAULT_PATH}\n"
                "Example path: <VAULT_PATH>/80. Resources\n",
                encoding="utf-8",
            )

            result = self.run_guard(root, "skills/demo/SKILL.md")

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_secret_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "skills/demo/SKILL.md"
            target.parent.mkdir(parents=True)
            secret_line = "api_" + "key = " + "real_live_value_1234567890\n"
            target.write_text(secret_line, encoding="utf-8")

            result = self.run_guard(root, "skills/demo/SKILL.md")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SECRET_ASSIGNMENT", result.stderr)

    def test_accepts_secret_lookup_expressions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "skills/demo/script.py"
            target.parent.mkdir(parents=True)
            target.write_text("client_secret = credentials.get('client_secret')\n", encoding="utf-8")

            result = self.run_guard(root, "skills/demo/script.py")

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_diff_mode_rejects_only_new_runtime_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            target = root / "skills/demo/SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("VAULT=${VAULT_PATH}\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "base"], cwd=root, check=True, stdout=subprocess.DEVNULL)
            base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

            leaked_path = "/Users/" + "someone/projects/my-vault/notes"
            target.write_text(target.read_text(encoding="utf-8") + f"LEAK={leaked_path}\n", encoding="utf-8")

            result = self.run_guard(root, "--diff-base", base)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("RUNTIME_HOME_PATH", result.stderr)

    def test_diff_mode_validates_current_worktree_not_stale_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            target = root / "skills/demo/SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("VAULT=${VAULT_PATH}\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "base"], cwd=root, check=True, stdout=subprocess.DEVNULL)
            base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

            leaked_path = "/Users/" + "someone/projects/my-vault/notes"
            target.write_text(target.read_text(encoding="utf-8") + f"LEAK={leaked_path}\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "add leak"], cwd=root, check=True, stdout=subprocess.DEVNULL)
            target.write_text("VAULT=<OS_HOME>/projects/my-vault\n", encoding="utf-8")

            result = self.run_guard(root, "--diff-base", base)

            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
