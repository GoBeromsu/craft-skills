"""Tests for the skill version and changelog diff checker."""

from __future__ import annotations

import json
import os
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


def _plugin(version: str) -> str:
    return json.dumps({"name": "craft-skills", "version": version}) + "\n"


class CheckVersionBumpTest(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.tempdir: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()
        self.root: Path = Path(self.tempdir.name)

    def setUp(self) -> None:
        package = self.root / "skills" / "demo"
        package.mkdir(parents=True)
        (package / "SKILL.md").write_text(_skill("1.0.0"), encoding="utf-8")
        (package / "CHANGELOG.md").write_text("- 2026-01-01 — initial release\n", encoding="utf-8")
        (self.root / ".codex-plugin").mkdir()
        (self.root / ".claude-plugin").mkdir()
        self._write_plugin_versions("0.5.0")
        subprocess.run(["git", "init"], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "skills", ".codex-plugin", ".claude-plugin"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "base"], cwd=self.root, check=True, capture_output=True, text=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _run(self, *extra: str) -> subprocess.CompletedProcess[str]:
        args = [sys.executable, str(_TOOL), *(extra or ("--diff-base", "HEAD~1"))]
        return subprocess.run(
            args,
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )

    def _write_plugin_versions(self, codex: str, claude: str | None = None) -> None:
        (self.root / ".codex-plugin" / "plugin.json").write_text(_plugin(codex), encoding="utf-8")
        (self.root / ".claude-plugin" / "plugin.json").write_text(_plugin(claude or codex), encoding="utf-8")

    def _commit_change(
        self,
        version: str,
        body: str,
        changelog: str,
        *,
        plugin_version: str | None = "0.5.1",
        claude_plugin_version: str | None = None,
    ) -> None:
        package = self.root / "skills" / "demo"
        (package / "SKILL.md").write_text(_skill(version, body), encoding="utf-8")
        (package / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
        if plugin_version is not None:
            self._write_plugin_versions(plugin_version, claude_plugin_version)
        subprocess.run(["git", "add", "skills", ".codex-plugin", ".claude-plugin"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "change"], cwd=self.root, check=True, capture_output=True, text=True)

    def test_accepts_substantive_change_with_increased_version_and_dated_changelog(self) -> None:
        self._commit_change("1.0.1", "updated guidance", "- 2026-07-12 — updated guidance\n- 2026-01-01 — initial release\n")
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_accepts_retired_package_with_git_owner(self) -> None:
        subprocess.run(["git", "rm", "-r", "skills/demo"], cwd=self.root, check=True, capture_output=True)
        self._write_plugin_versions("0.5.1")
        subprocess.run(["git", "add", ".codex-plugin", ".claude-plugin"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "delete package"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("retired package with Git-established former owner", result.stdout)

    def test_rejects_partial_retirement_remnant(self) -> None:
        skill = self.root / "skills" / "demo" / "SKILL.md"
        skill.unlink()
        remnant = self.root / "skills" / "demo" / "notes.md"
        remnant.write_text("left behind\n", encoding="utf-8")
        self._write_plugin_versions("0.5.1")
        subprocess.run(["git", "add", "skills", ".codex-plugin", ".claude-plugin"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "partial retirement"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        result = self._run()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("retired package still has remnant files", result.stdout)

    def test_rejects_missing_skill_without_former_owner(self) -> None:
        package = self.root / "skills" / "ghost"
        package.mkdir()
        (package / "notes.md").write_text("not a skill\n", encoding="utf-8")
        self._write_plugin_versions("0.5.1")
        subprocess.run(["git", "add", "skills", ".codex-plugin", ".claude-plugin"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "unowned remnant"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )
        result = self._run()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("missing SKILL.md with no Git-established former owner", result.stdout)

    def test_package_local_tests_tree_is_not_a_package_change(self) -> None:
        tests_dir = self.root / "skills" / "demo" / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_demo.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        subprocess.run(["git", "add", "skills"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "add tests"], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "rm", "-rq", "skills/demo/tests"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "move tests out"], cwd=self.root, check=True, capture_output=True, text=True)
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

    def test_skill_change_requires_root_plugin_version_bump(self) -> None:
        self._commit_change(
            "1.0.1",
            "updated guidance",
            "- 2026-07-12 — updated guidance\n- 2026-01-01 — initial release\n",
            plugin_version=None,
        )
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertIn(".codex-plugin/plugin.json: root plugin version must increase", result.stdout)
        self.assertIn(".claude-plugin/plugin.json: root plugin version must increase", result.stdout)

    def test_plugin_only_change_still_rejects_root_version_divergence(self) -> None:
        self._write_plugin_versions("0.5.1", "0.5.0")
        subprocess.run(
            ["git", "add", ".codex-plugin", ".claude-plugin"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "diverge plugin manifests"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )

        result = self._run()

        self.assertEqual(result.returncode, 1)
        self.assertIn("root plugin versions must match", result.stdout)
        self.assertIn(".claude-plugin/plugin.json: root plugin version must increase", result.stdout)

    def test_plugin_only_change_accepts_synchronized_version_increase(self) -> None:
        self._write_plugin_versions("0.5.1")
        subprocess.run(
            ["git", "add", ".codex-plugin", ".claude-plugin"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "bump plugin manifests"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )

        result = self._run()

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_plugin_only_change_rejects_invalid_root_version(self) -> None:
        self._write_plugin_versions("invalid", "0.5.1")
        subprocess.run(
            ["git", "add", ".codex-plugin", ".claude-plugin"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "write invalid plugin version"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )

        result = self._run()

        self.assertEqual(result.returncode, 1)
        self.assertIn(".codex-plugin/plugin.json: root plugin version is not valid semver", result.stdout)

    def test_plugin_only_manifest_content_change_requires_version_increase(self) -> None:
        for relative in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
            path = self.root / relative
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["description"] = "changed without a version bump"
            path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", ".codex-plugin", ".claude-plugin"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "change plugin metadata"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        )

        result = self._run()

        self.assertEqual(result.returncode, 1)
        self.assertIn(".codex-plugin/plugin.json: root plugin version must increase", result.stdout)
        self.assertIn(".claude-plugin/plugin.json: root plugin version must increase", result.stdout)

    def test_codex_and_claude_plugin_versions_match(self) -> None:
        self._commit_change(
            "1.0.1",
            "updated guidance",
            "- 2026-07-12 — updated guidance\n- 2026-01-01 — initial release\n",
            plugin_version="0.5.1",
            claude_plugin_version="0.5.2",
        )
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertIn("root plugin versions must match", result.stdout)

    def test_given_changed_skill_when_claude_manifest_stays_stale_then_rejects(self) -> None:
        self._commit_change(
            "1.0.1",
            "updated guidance",
            "- 2026-07-12 — updated guidance\n- 2026-01-01 — initial release\n",
            plugin_version="0.5.1",
            claude_plugin_version="0.5.0",
        )
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertIn(".claude-plugin/plugin.json: root plugin version must increase", result.stdout)

    def test_accepts_new_package_with_note(self) -> None:
        package = self.root / "skills" / "new-demo"
        package.mkdir()
        (package / "SKILL.md").write_text(_skill("1.0.0", "new guidance"), encoding="utf-8")
        (package / "CHANGELOG.md").write_text("- 2026-07-12 — initial release\n", encoding="utf-8")
        self._write_plugin_versions("0.5.1")
        subprocess.run(["git", "add", "skills", ".codex-plugin", ".claude-plugin"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "new package"], cwd=self.root, check=True, capture_output=True, text=True)
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("new package", result.stdout)

    def test_rejects_new_package_with_invalid_version(self) -> None:
        package = self.root / "skills" / "new-demo"
        package.mkdir()
        (package / "SKILL.md").write_text(_skill("invalid", "new guidance"), encoding="utf-8")
        (package / "CHANGELOG.md").write_text("- 2026-07-12 — initial release\n", encoding="utf-8")
        self._write_plugin_versions("0.5.1")
        subprocess.run(["git", "add", "skills", ".codex-plugin", ".claude-plugin"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "new package"], cwd=self.root, check=True, capture_output=True, text=True)
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertIn("new-demo: metadata.version is not valid semver", result.stdout)

    def test_rejects_new_package_without_dated_changelog(self) -> None:
        package = self.root / "skills" / "new-demo"
        package.mkdir()
        (package / "SKILL.md").write_text(_skill("1.0.0", "new guidance"), encoding="utf-8")
        (package / "CHANGELOG.md").write_text("initial release\n", encoding="utf-8")
        self._write_plugin_versions("0.5.1")
        subprocess.run(["git", "add", "skills", ".codex-plugin", ".claude-plugin"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "new package"], cwd=self.root, check=True, capture_output=True, text=True)
        result = self._run()
        self.assertEqual(result.returncode, 1)
        self.assertIn("new-demo: CHANGELOG.md must gain a dated bullet", result.stdout)

    def test_covers_unstaged_unicode_support_filename(self) -> None:
        support = self.root / "skills" / "demo" / "references"
        support.mkdir()
        (support / "강의.part notes.md").write_text("updated support\n", encoding="utf-8")
        (self.root / "skills" / "demo" / "SKILL.md").write_text(_skill("1.0.1", "updated guidance"), encoding="utf-8")
        (self.root / "skills" / "demo" / "CHANGELOG.md").write_text(
            "- 2026-07-12 — updated guidance\n- 2026-01-01 — initial release\n",
            encoding="utf-8",
        )
        self._write_plugin_versions("0.5.1")
        result = self._run("--diff-base", "HEAD")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_rejects_range_and_option_diff_base(self) -> None:
        for base in ("HEAD...HEAD", "HEAD..HEAD", "--help"):
            with self.subTest(base=base):
                result = self._run(f"--diff-base={base}")
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("one commit-ish", result.stdout)

    def test_rejects_redirected_git_worktree_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_repo = Path(tmp) / "base"
            target = Path(tmp) / "target"
            for repo in (base_repo, target):
                repo.mkdir()
                subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
                subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
                subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
                subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo, check=True, capture_output=True, text=True)
            plugin = target / ".claude-plugin"
            plugin.mkdir()
            (plugin / "plugin.json").write_text("{not-json\n", encoding="utf-8")
            ordinary = subprocess.run(
                [sys.executable, str(_TOOL), "--diff-base=HEAD"],
                cwd=target,
                text=True,
                capture_output=True,
                check=False,
                env={key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
            )
            self.assertEqual(ordinary.returncode, 1, ordinary.stdout + ordinary.stderr)
            redirected = dict(os.environ)
            redirected["GIT_DIR"] = str(base_repo / ".git")
            redirected["GIT_WORK_TREE"] = str(base_repo)
            result = subprocess.run(
                [sys.executable, str(_TOOL), "--diff-base=HEAD"],
                cwd=target,
                text=True,
                capture_output=True,
                check=False,
                env=redirected,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("Git worktree root", result.stdout)
            self.assertNotIn("note:", result.stdout)

    def test_escaping_live_plugin_symlink_is_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            secret = Path(outside) / "plugin.json"
            secret.write_text('{"name": "craft-skills", "version": "9.9.9", "sentinel": "SENTINEL-OUTSIDE-PLUGIN"}\n', encoding="utf-8")
            plugin = self.root / ".claude-plugin" / "plugin.json"
            plugin.unlink()
            plugin.symlink_to(secret)
            result = self._run("--diff-base", "HEAD")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("escapes root", result.stdout)
            self.assertNotIn("SENTINEL-OUTSIDE-PLUGIN", result.stdout)
            self.assertNotIn("SENTINEL-OUTSIDE-PLUGIN", result.stderr)

    def test_contained_live_plugin_is_still_checked(self) -> None:
        plugin = self.root / ".claude-plugin" / "plugin.json"
        target = self.root / "contained-plugin.json"
        target.write_bytes(plugin.read_bytes())
        plugin.unlink()
        plugin.symlink_to(target)
        result = self._run("--diff-base", "HEAD")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("root plugin version must increase", result.stdout)


if __name__ == "__main__":
    unittest.main()
