"""Regression tests for install.sh safety guards (subprocess-based)."""

from __future__ import annotations

import os
import signal
import stat
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

    def test_refuses_existing_valid_subdirectory(self) -> None:
        result = _run("codex", "--clone", str(_ROOT / "skills" / "api"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("REFUSED", result.stderr)
        self.assertNotIn("not a directory", result.stderr)

    def test_refuses_symlink_into_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "linked-project"
            link.symlink_to(_ROOT / "skills" / "api")
            result = _run("codex", "--clone", str(link))
            self.assertEqual(result.returncode, 1)
            self.assertIn("REFUSED", result.stderr)

    def test_refuses_native_plugin_identity_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkout = Path(tmp) / "alt-checkout"
            checkout.mkdir()
            plugin = checkout / ".codex-plugin"
            plugin.mkdir()
            (plugin / "plugin.json").write_text('{"name": "craft-skills"}\n', encoding="utf-8")
            result = _run("codex", "--clone", str(checkout))
            self.assertEqual(result.returncode, 1)
            self.assertIn("native plugin identity", result.stderr)
            self.assertFalse((checkout / ".agents").exists())

    def test_refuses_escaping_agents_symlink_before_mkdir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "consumer"
            outside = Path(tmp) / "outside"
            project.mkdir()
            outside.mkdir()
            agents = project / ".agents"
            agents.symlink_to(outside)
            result = _run("codex", "--clone", str(project))
            self.assertEqual(result.returncode, 1)
            self.assertIn("escapes the consumer project", result.stderr)
            self.assertFalse((outside / "skills").exists())
            self.assertFalse((outside / "craft-skills").exists())

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

    def test_unrelated_string_does_not_pass(self) -> None:
        result = self._hermes('{"notes": "GoBeromsu/craft-skills", "taps": []}\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not registered", result.stdout)

    def test_malformed_json_does_not_pass(self) -> None:
        result = self._hermes('{"taps": [{"repo": "GoBeromsu/craft-skills", "path": "skills/"}')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not registered", result.stdout)

    def test_wrong_path_does_not_pass(self) -> None:
        result = self._hermes('{"taps": [{"repo": "GoBeromsu/craft-skills", "path": "other/"}]}\n')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not registered", result.stdout)


class GjcPluginCheckTest(unittest.TestCase):
    def _gjc(self, script: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            gjc = bin_dir / "gjc"
            gjc.write_text(script, encoding="utf-8")
            gjc.chmod(gjc.stat().st_mode | stat.S_IEXEC)
            env = {
                "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            }
            return _run("gjc", env=env)

    def test_structured_marketplace_entries_pass(self) -> None:
        payload = {
            "npm": [],
            "marketplace": [
                {
                    "id": "craft-skills@craft-skills",
                    "scope": "user",
                    "entries": [
                        {
                            "installPath": "/tmp/isolated/craft-skills",
                            "installedAt": "2026-09-20T00:00:00Z",
                            "lastUpdated": "2026-09-20T00:00:00Z",
                            "scope": "user",
                            "version": "0.21.0",
                        }
                    ],
                }
            ],
            "gjc": [],
        }
        import json
        script = (
            "#!/usr/bin/env bash\n"
            "if [ \"$1\" = plugin ] && [ \"$2\" = list ] && [ \"$3\" = --json ]; then\n"
            f"  printf '%s\\n' '{json.dumps(payload)}'\n"
            "  exit 0\n"
            "fi\n"
            "exit 1\n"
        )
        result = self._gjc(script)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("is installed", result.stdout)

    def test_command_failure_with_matching_id_does_not_pass(self) -> None:
        script = """#!/usr/bin/env bash
printf 'craft-skills@craft-skills not found\\n' >&2
exit 1
"""
        result = self._gjc(script)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("plugin list --json failed", result.stdout)
        self.assertNotIn("is installed", result.stdout)


if __name__ == "__main__":
    unittest.main()
