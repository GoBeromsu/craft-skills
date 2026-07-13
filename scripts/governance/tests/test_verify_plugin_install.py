from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import TypedDict

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_TOOL = _ROOT / "scripts" / "governance" / "tools" / "verify_plugin_install.py"


class PluginSource(TypedDict):
    source: str
    path: str


class InstalledEntry(TypedDict):
    pluginId: str
    version: str
    installed: bool
    enabled: bool
    source: PluginSource


class VerifyPluginInstallTest(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.tempdir: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()
        self.root: Path = Path(self.tempdir.name)
        self.previous: Path = self.root / "previous" / "0.5.0"
        self.candidate: Path = self.root / "candidate" / "0.5.1"
        self.plugin_list: Path = self.root / "plugin-list.json"

    def setUp(self) -> None:
        self.previous.mkdir(parents=True)
        (self.candidate / "skills" / "backend" / "references").mkdir(parents=True)
        (self.candidate / "skills" / "testing" / "references").mkdir(parents=True)
        (self.candidate / "skills" / "cicd" / "references").mkdir(parents=True)
        self._write_guidance_files()
        self._write_plugin_list([self._valid_entry()])

    def _valid_entry(self) -> InstalledEntry:
        return {
            "pluginId": "craft-skills@craft-skills",
            "version": "0.5.1",
            "installed": True,
            "enabled": True,
            "source": {"source": "local", "path": str(self.candidate)},
        }

    def _write_plugin_list(self, entries: list[InstalledEntry]) -> None:
        self.plugin_list.write_text(
            json.dumps({"installed": entries}),
            encoding="utf-8",
        )

    def _write_guidance_files(self) -> None:
        (self.candidate / "skills" / "backend" / "references" / "persistence.md").write_text(
            "runtime application role\nprivileged migration/admin role\ndedicated disposable non-production target\n",
            encoding="utf-8",
        )
        (self.candidate / "skills" / "testing" / "references" / "integration.md").write_text(
            "application-owned transaction\ntransaction-local RLS\nallowed and denied tenant paths\n",
            encoding="utf-8",
        )
        (self.candidate / "skills" / "cicd" / "references" / "pipeline-safety.md").write_text(
            "immutable release resolver\nno schema change or backward compatibility\ncode rollback is not database recovery\n",
            encoding="utf-8",
        )

    def _run(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(_TOOL),
                "--plugin-list",
                str(self.plugin_list),
                "--expected-version",
                "0.5.1",
                "--forbid-source",
                str(self.previous),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_codex_upgrade_replaces_previous_version_and_contains_changed_guidance(self) -> None:
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_given_duplicate_entries_when_verifying_then_rejects(self) -> None:
        self._write_plugin_list([self._valid_entry(), self._valid_entry()])
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stdout,
            "verify_plugin_install: expected one installed craft-skills@craft-skills entry, found 2\n",
        )

    def test_given_not_installed_when_verifying_then_rejects(self) -> None:
        entry = self._valid_entry()
        entry["installed"] = False
        self._write_plugin_list([entry])
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "verify_plugin_install: craft-skills@craft-skills must be installed and enabled\n")

    def test_given_disabled_when_verifying_then_rejects(self) -> None:
        entry = self._valid_entry()
        entry["enabled"] = False
        self._write_plugin_list([entry])
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "verify_plugin_install: craft-skills@craft-skills must be installed and enabled\n")

    def test_given_wrong_version_when_verifying_then_rejects(self) -> None:
        entry = self._valid_entry()
        entry["version"] = "0.5.0"
        self._write_plugin_list([entry])
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "verify_plugin_install: expected version 0.5.1, found '0.5.0'\n")

    def test_given_forbidden_prior_source_when_verifying_then_rejects(self) -> None:
        entry = self._valid_entry()
        entry["source"]["path"] = str(self.previous)
        self._write_plugin_list([entry])
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "verify_plugin_install: installed plugin still resolves to the forbidden prior source\n")

    def test_given_missing_source_directory_when_verifying_then_rejects(self) -> None:
        entry = self._valid_entry()
        entry["source"]["path"] = str(self.root / "missing")
        self._write_plugin_list([entry])
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "verify_plugin_install: installed plugin source path is missing\n")

    def test_given_each_missing_fingerprint_when_verifying_then_rejects(self) -> None:
        cases = (
            ("skills/backend/references/persistence.md", "runtime application role"),
            ("skills/backend/references/persistence.md", "privileged migration/admin role"),
            ("skills/backend/references/persistence.md", "dedicated disposable non-production target"),
            ("skills/testing/references/integration.md", "application-owned transaction"),
            ("skills/testing/references/integration.md", "transaction-local RLS"),
            ("skills/testing/references/integration.md", "allowed and denied tenant paths"),
            ("skills/cicd/references/pipeline-safety.md", "immutable release resolver"),
            ("skills/cicd/references/pipeline-safety.md", "no schema change or backward compatibility"),
            ("skills/cicd/references/pipeline-safety.md", "code rollback is not database recovery"),
        )
        for relative, fingerprint in cases:
            with self.subTest(relative=relative, fingerprint=fingerprint):
                self._write_guidance_files()
                path = self.candidate / relative
                path.write_text(path.read_text(encoding="utf-8").replace(fingerprint, ""), encoding="utf-8")
                result = self._run()
                self.assertEqual(result.returncode, 1)
                self.assertEqual(
                    result.stdout,
                    f"verify_plugin_install: {relative} is missing required guidance: {fingerprint}\n",
                )
if __name__ == "__main__":
    unittest.main()
