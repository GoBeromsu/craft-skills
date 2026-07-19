from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Final, Sequence

_ROOT: Final = Path(__file__).resolve().parent.parent.parent.parent
_PLUGIN_NAME: Final = "craft-skills"
_PLUGIN_VERSION: Final = "0.5.2"
_PACKAGE_COUNT: Final = 31
_SUBPROCESS_TIMEOUT_SECONDS: Final = 20
_RUNTIME_PROBE: Final = "\n".join(
    (
        "import json",
        "from hermes_cli.plugins import get_plugin_manager",
        "manager = get_plugin_manager()",
        "manager.discover_and_load(force=True)",
        "plugin = next(item for item in manager.list_plugins() ",
        "              if item['name'] == 'craft-skills')",
        "print(json.dumps({'plugin': plugin, ",
        "                  'skills': manager.list_plugin_skills('craft-skills')}))",
    )
)


def _run(
    command: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    with subprocess.Popen(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd,
        env=env,
        start_new_session=True,
    ) as process:
        try:
            stdout, stderr = process.communicate(
                timeout=_SUBPROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=_SUBPROCESS_TIMEOUT_SECONDS)
            raise
        return subprocess.CompletedProcess(
            list(command),
            process.wait(),
            stdout,
            stderr,
        )


def _resolve_hermes_runtime() -> tuple[Path, Path, Path]:
    launcher_name = shutil.which("hermes")
    if launcher_name is None:
        raise unittest.SkipTest("Hermes CLI is unavailable")

    launcher = Path(launcher_name)
    launcher_text = launcher.read_text(encoding="utf-8")
    first_line = launcher_text.splitlines()[0]
    if first_line.startswith("#!") and "python" in first_line:
        console_script = launcher
    else:
        match = re.search(r'exec\s+"([^"]+/bin/hermes)"', launcher_text)
        if match is None:
            raise unittest.SkipTest("Hermes console script cannot be resolved")
        console_script = Path(match.group(1))

    console_lines = console_script.read_text(encoding="utf-8").splitlines()
    if not console_lines or not console_lines[0].startswith("#!"):
        raise unittest.SkipTest("Hermes Python interpreter cannot be resolved")

    python = Path(console_lines[0][2:])
    source_root = console_script.resolve().parents[2]
    return launcher, python, source_root


def _build_source_checkout(destination: Path, env: dict[str, str]) -> None:
    destination.mkdir()
    for filename in ("plugin.yaml", "__init__.py"):
        source = _ROOT / filename
        if source.exists():
            shutil.copy2(source, destination / filename)
    shutil.copytree(_ROOT / "skills", destination / "skills")
    shutil.copytree(_ROOT / ".hermes", destination / ".hermes")
    (destination / ".hermes" / "plugin.yaml").write_text(
        'name: "."\n',
        encoding="utf-8",
    )

    init_result = _run(
        ["git", "init", "--quiet", str(destination)],
        cwd=destination.parent,
        env=env,
    )
    if init_result.returncode != 0:
        raise RuntimeError(init_result.stderr)

    add_result = _run(
        ["git", "add", "."],
        cwd=destination,
        env=env,
    )
    if add_result.returncode != 0:
        raise RuntimeError(add_result.stderr)

    commit_result = _run(
        ["git", "commit", "--quiet", "-m", "test fixture"],
        cwd=destination,
        env=env,
    )
    if commit_result.returncode != 0:
        raise RuntimeError(commit_result.stderr)


class HermesPluginIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls._temporary_root = Path(cls._temporary_directory.name)
        cls._launcher, cls._python, cls._hermes_source = _resolve_hermes_runtime()
        cls._hermes_home = cls._temporary_root / "hermes-home"
        cls._source = cls._temporary_root / "source"
        cls._env = dict(os.environ)
        cls._env.update(
            {
                "GIT_AUTHOR_EMAIL": "test@example.com",
                "GIT_AUTHOR_NAME": "Hermes Plugin Test",
                "GIT_COMMITTER_EMAIL": "test@example.com",
                "GIT_COMMITTER_NAME": "Hermes Plugin Test",
                "HERMES_ENABLE_PROJECT_PLUGINS": "0",
                "HERMES_HOME": str(cls._hermes_home),
                "HERMES_SAFE_MODE": "0",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        _build_source_checkout(cls._source, cls._env)

        cls._install_result = _run(
            [
                str(cls._launcher),
                "plugins",
                "install",
                cls._source.as_uri(),
                "--enable",
            ],
            cwd=cls._temporary_root,
            env=cls._env,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def test_root_install_lists_exact_enabled_plugin(self) -> None:
        self.assertEqual(
            self._install_result.returncode,
            0,
            self._install_result.stdout + self._install_result.stderr,
        )

        result = _run(
            [
                str(self._launcher),
                "plugins",
                "list",
                "--user",
                "--json",
            ],
            cwd=self._temporary_root,
            env=self._env,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["name"], _PLUGIN_NAME)
        self.assertEqual(payload[0]["version"], _PLUGIN_VERSION)
        self.assertEqual(payload[0]["status"], "enabled")

    def test_installed_checkout_retains_flat_skill_tree(self) -> None:
        installed = self._hermes_home / "plugins" / _PLUGIN_NAME
        skill_files = sorted((installed / "skills").rglob("SKILL.md"))
        self.assertTrue((installed / "skills").is_dir())
        self.assertEqual(len(skill_files), _PACKAGE_COUNT)
        self.assertEqual(
            {len(path.relative_to(installed / "skills").parts) for path in skill_files},
            {2},
        )

    def test_initialization_registers_nothing(self) -> None:
        result = _run(
            [str(self._python), "-c", _RUNTIME_PROBE],
            cwd=self._hermes_source,
            env=self._env,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout.splitlines()[-1])
        plugin = payload["plugin"]
        self.assertTrue(plugin["enabled"])
        self.assertIsNone(plugin["error"])
        self.assertEqual(plugin["hooks"], 0)
        self.assertEqual(plugin["tools"], 0)
        self.assertEqual(plugin["middleware"], 0)
        self.assertEqual(plugin["commands"], 0)
        self.assertEqual(payload["skills"], [])

    def test_hermes_subdirectory_install_is_rejected(self) -> None:
        failure_home = self._temporary_root / "failure-home"
        failure_env = dict(self._env)
        failure_env["HERMES_HOME"] = str(failure_home)
        result = _run(
            [
                str(self._launcher),
                "plugins",
                "install",
                f"{self._source.as_uri()}#.hermes",
                "--enable",
            ],
            cwd=self._temporary_root,
            env=failure_env,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((failure_home / "plugins" / ".hermes").exists())


if __name__ == "__main__":
    unittest.main()
