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
            self.assertIn(
                "codex plugin marketplace add GoBeromsu/craft-skills",
                result.stdout,
            )
            self.assertFalse((Path(tmp) / ".agents").exists())


class HermesTapCheckTest(unittest.TestCase):
    def _hermes(self, taps: str | None) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            if taps is not None:
                hub = Path(tmp) / "skills" / ".hub"
                hub.mkdir(parents=True)
                (hub / "taps.json").write_text(taps, encoding="utf-8")
            return _run("hermes", env={"HERMES_HOME": tmp})

    def test_registered_tap_passes(self) -> None:
        result = self._hermes('{"taps": [{"repo": "GoBeromsu/craft-skills", "path": "skills/"}]}\n')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("is registered", result.stdout)
        self.assertIn("hermes skills tap add GoBeromsu/craft-skills", result.stdout)

    def test_missing_tap_fails(self) -> None:
        result = self._hermes('{"taps": []}\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not registered", result.stdout)

    def test_missing_taps_file_fails(self) -> None:
        result = self._hermes(None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not registered", result.stdout)


if __name__ == "__main__":
    unittest.main()
