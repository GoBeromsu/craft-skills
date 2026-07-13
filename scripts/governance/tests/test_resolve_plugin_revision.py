from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_RESOLVER = _ROOT / "scripts" / "governance" / "tools" / "resolve_plugin_revision.py"
_INSTALL_WORKFLOW = _ROOT / ".github" / "workflows" / "test-plugin-install.yml"


def _plugin(version: str) -> str:
    return json.dumps({"name": "craft-skills", "version": version}) + "\n"


class ResolvePluginRevisionTest(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.tempdir: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()
        self.root: Path = Path(self.tempdir.name)
        self.previous_ref: str = ""

    def setUp(self) -> None:
        (self.root / ".codex-plugin").mkdir()
        subprocess.run(["git", "init"], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.root, check=True)
        self.previous_ref = self._commit_manifest("0.5.0", "previous")
        self._commit_manifest("0.5.1", "candidate")
        manifest = self.root / ".codex-plugin" / "plugin.json"
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        payload["description"] = "candidate manifest touched again"
        manifest.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        subprocess.run(["git", "add", str(manifest)], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "touch candidate manifest again"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _commit_manifest(self, version: str, message: str) -> str:
        manifest = self.root / ".codex-plugin" / "plugin.json"
        manifest.write_text(_plugin(version), encoding="utf-8")
        subprocess.run(["git", "add", str(manifest)], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def _run(self, version: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(_RESOLVER),
                "--manifest",
                ".codex-plugin/plugin.json",
                "--expected-version",
                version,
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_given_candidate_manifest_touched_twice_when_resolving_previous_then_selects_exact_version(self) -> None:
        result = self._run("0.5.0")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), self.previous_ref)

    def test_given_missing_previous_version_when_resolving_then_fails_closed(self) -> None:
        result = self._run("0.4.9")

        self.assertEqual(result.returncode, 1)
        self.assertIn("no revision contains .codex-plugin/plugin.json at version 0.4.9", result.stdout)

    def test_upgrade_workflow_resolves_and_asserts_explicit_previous_version(self) -> None:
        workflow = _INSTALL_WORKFLOW.read_text(encoding="utf-8")

        self.assertNotIn("sed -n '2p'", workflow)
        self.assertIn("resolve_plugin_revision.py", workflow)
        self.assertIn('--expected-version "$PREVIOUS_PLUGIN_VERSION"', workflow)
        self.assertIn("entry.get('version') != expected_version", workflow)


if __name__ == "__main__":
    unittest.main()
