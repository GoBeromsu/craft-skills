"""Regression tests for install.sh safety guards (subprocess-based)."""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_INSTALL = _ROOT / "install.sh"
_SKILLS_PATH = os.path.expanduser("~/dev/GoBeromsu/craft-skills/skills")
_SUBPROCESS_TIMEOUT_SECONDS = 5


def _run(
    *args: str,
    env: dict[str, str] | None = None,
    cwd: Path = _ROOT,
) -> subprocess.CompletedProcess[str]:
    merged = dict(os.environ)
    if env:
        merged.update(env)
    command = ["bash", str(_INSTALL), *args]
    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd,
        env=merged,
        start_new_session=True,
    ) as process:
        try:
            stdout, stderr = process.communicate(timeout=_SUBPROCESS_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=_SUBPROCESS_TIMEOUT_SECONDS)
            raise
        return subprocess.CompletedProcess(
            command,
            process.wait(),
            stdout,
            stderr,
        )


class CodexCloneGuardTest(unittest.TestCase):
    def test_refuses_repo_root(self) -> None:
        result = _run("codex", "--clone", ".")
        self.assertEqual(result.returncode, 1)
        self.assertIn("REFUSED", result.stderr)

    def test_refuses_repo_subdirectory(self) -> None:
        result = _run("codex", "--clone", "skills/api")
        self.assertEqual(result.returncode, 1)
        self.assertIn("REFUSED", result.stderr)

    def test_refuses_symlink_into_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "linked-project"
            link.symlink_to(_ROOT / "skills" / "api")
            result = _run("codex", "--clone", str(link))
            self.assertEqual(result.returncode, 1)
            self.assertIn("REFUSED", result.stderr)

    def test_default_invocation_does_not_clone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = _run("codex", cwd=Path(tmp))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((Path(tmp) / ".agents").exists())


class HermesConfigGuardTest(unittest.TestCase):
    def _hermes(self, config: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "config.yaml").write_text(config, encoding="utf-8")
            return _run("hermes", env={"HERMES_HOME": tmp})

    def test_canonical_entry_passes(self) -> None:
        result = self._hermes(f"skills:\n  external_dirs:\n    - {_SKILLS_PATH}\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("canonical", result.stdout)

    def test_wrong_parent_key_fails(self) -> None:
        result = self._hermes(f"other:\n  external_dirs:\n    - {_SKILLS_PATH}\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("noncanonical", result.stdout)

    def test_wrong_path_fails(self) -> None:
        result = self._hermes("skills:\n  external_dirs:\n    - /tmp/craft-skills/skills\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("noncanonical", result.stdout)


class HermesAncestryGuardTest(unittest.TestCase):
    def _hermes(self, config: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "config.yaml").write_text(config, encoding="utf-8")
            return _run("hermes", env={"HERMES_HOME": tmp})

    def test_nested_intermediate_mapping_fails(self) -> None:
        result = self._hermes(
            f"skills:\n  nested:\n    external_dirs:\n      - {_SKILLS_PATH}\n"
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("noncanonical", result.stdout)

    def test_non_toplevel_skills_parent_fails(self) -> None:
        result = self._hermes(
            f"other:\n  skills:\n    external_dirs:\n      - {_SKILLS_PATH}\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("noncanonical", result.stdout)


if __name__ == "__main__":
    unittest.main()
