#!/usr/bin/env python3
"""Tests for skillify runtime hygiene guard."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills/skillify/scripts/validate-runtime-hygiene.py"
_GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def _isolated_git_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(_GIT_IDENTITY)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["GIT_TEMPLATE_DIR"] = ""
    if extra:
        env.update(extra)
    return env


class RuntimeHygieneGuardTest(unittest.TestCase):
    def run_guard(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), "--root", str(root), *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=_isolated_git_env(),
        )

    def _git(self, root: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            env=_isolated_git_env(),
        )
    def _git_head(self, root: Path) -> str:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            env=_isolated_git_env(),
        ).strip()

    def _init_git(self, root: Path) -> None:
        self._git(root, "init", "--template=")
        self._git(root, "config", "--local", "user.email", "test@example.com")
        self._git(root, "config", "--local", "user.name", "Test")
        self._git(root, "config", "--local", "commit.gpgsign", "false")
        self._git(root, "config", "--local", "tag.gpgsign", "false")
        self._git(root, "config", "--local", "core.hooksPath", "/dev/null")

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
            self.assertNotIn(leaked_path, result.stderr)
            self.assertNotIn("someone/projects", result.stderr)

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
            token = "real_live_" + "value_1234567890"
            secret_line = "api_" + "key = " + token + "\n"
            target.write_text(secret_line, encoding="utf-8")

            result = self.run_guard(root, "skills/demo/SKILL.md")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SECRET_ASSIGNMENT", result.stderr)
            self.assertNotIn(token, result.stderr)
            self.assertNotIn(token, result.stdout)

    def test_accepts_secret_lookup_expressions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "skills/demo/script.py"
            target.parent.mkdir(parents=True)
            target.write_text("client_secret = credentials.get('client_secret')\n", encoding="utf-8")

            result = self.run_guard(root, "skills/demo/script.py")

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_accepts_python_name_and_attribute_lookups(self) -> None:
        expressions = (
            "configured_access_token",
            "self.config.token",
            "self.config.token if token is None else token",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "script.py"
            for expression in expressions:
                with self.subTest(expression=expression):
                    target.write_text(
                        "def request(self, token=None):\n    token = " + expression + "\n",
                        encoding="utf-8",
                    )
                    result = self.run_guard(root, "script.py")
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_lookup_exemption_requires_python_code_not_literal_text(self) -> None:
        value = "self.config.token"
        cases = (
            ("script.sh", "token=" + value + "\n"),
            ("script.sh", "token=configured_" + "access_token\n"),
            ("SKILL.md", "token = " + value + "\n"),
            ("SKILL.md", "token = abcd." + "efghijklmnopqr.stuv\n"),
            ("script.py", "token = '" + value + "'\n"),
            ("script.py", 'token = "' + value + '"\n'),
            ("script.py", 'message = "token = ' + value + '"\n'),
            ("script.py", "# token = " + value + "\n"),
            ("script.py", "token = abc." + "1234567890123456\n"),
            ("config.json", '{"token": "' + value + '"}\n'),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for filename, content in cases:
                with self.subTest(filename=filename, content=content):
                    (root / filename).write_text(content, encoding="utf-8")
                    result = self.run_guard(root, filename)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertIn("SECRET_ASSIGNMENT", result.stderr)
                    self.assertNotIn(value, result.stderr)

    def test_rejects_github_fine_grained_pat_in_markdown_script_and_json(self) -> None:
        body = "A" * 20
        token = "github_" + "pat_" + body
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            demo = root / "skills/demo"
            demo.mkdir(parents=True)
            (demo / "SKILL.md").write_text("GITHUB_" + "TOKEN=" + token + "\n", encoding="utf-8")
            md = self.run_guard(root, "skills/demo/SKILL.md")
            self.assertEqual(md.returncode, 1, md.stdout + md.stderr)
            self.assertIn("SECRET_GITHUB_TOKEN", md.stderr)
            self.assertNotIn(token, md.stderr)
            self.assertNotIn(token, md.stdout)
            (demo / "script.py").write_text("token = '" + token + "'\n", encoding="utf-8")
            py = self.run_guard(root, "skills/demo/script.py")
            self.assertEqual(py.returncode, 1, py.stdout + py.stderr)
            self.assertIn("SECRET_GITHUB_TOKEN", py.stderr)
            self.assertNotIn(token, py.stderr)
            self.assertNotIn(token, py.stdout)
            plugin = root / ".claude-plugin"
            plugin.mkdir()
            (plugin / "marketplace.json").write_text(
                '{\n  "name": "craft-skills",\n  "github_' + 'pat": "' + token + '"\n}\n',
                encoding="utf-8",
            )
            leaked = self.run_guard(root, ".claude-plugin/marketplace.json")
            self.assertEqual(leaked.returncode, 1, leaked.stdout + leaked.stderr)
            self.assertIn("SECRET_GITHUB_TOKEN", leaked.stderr)
            self.assertNotIn(token, leaked.stderr)
            self.assertNotIn(token, leaked.stdout)

    def test_accepts_github_pat_placeholders_and_lookups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            demo = root / "skills/demo"
            demo.mkdir(parents=True)
            (demo / "SKILL.md").write_text(
                "GITHUB_" + "TOKEN=${GITHUB_TOKEN}\n"
                "Example: github_" + "pat_<YOUR_FINE_GRAINED_PAT>\n",
                encoding="utf-8",
            )
            md = self.run_guard(root, "skills/demo/SKILL.md")
            self.assertEqual(md.returncode, 0, md.stderr)
            (demo / "script.py").write_text(
                "token = os.environ.get('GITHUB_" + "TOKEN')\n",
                encoding="utf-8",
            )
            py = self.run_guard(root, "skills/demo/script.py")
            self.assertEqual(py.returncode, 0, py.stderr)

    def test_diff_mode_rejects_only_new_runtime_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_git(root)
            target = root / "skills/demo/SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("VAULT=${VAULT_PATH}\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "base")
            base = self._git_head(root)

            leaked_path = "/Users/" + "someone/projects/my-vault/notes"
            target.write_text(target.read_text(encoding="utf-8") + f"LEAK={leaked_path}\n", encoding="utf-8")

            result = self.run_guard(root, "--diff-base", base)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("RUNTIME_HOME_PATH", result.stderr)
            self.assertNotIn(leaked_path, result.stderr)

    def test_diff_mode_validates_current_worktree_not_stale_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_git(root)
            target = root / "skills/demo/SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("VAULT=${VAULT_PATH}\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "base")
            base = self._git_head(root)

            leaked_path = "/Users/" + "someone/projects/my-vault/notes"
            target.write_text(target.read_text(encoding="utf-8") + f"LEAK={leaked_path}\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "add leak")
            target.write_text("VAULT=<OS_HOME>/projects/my-vault\n", encoding="utf-8")

            result = self.run_guard(root, "--diff-base", base)

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_diff_base_rejects_ranges_and_repeats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_git(root)
            (root / "skills/demo").mkdir(parents=True)
            (root / "skills/demo/SKILL.md").write_text("ok\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "base")
            for base in ("HEAD...HEAD", "HEAD..HEAD", "--help"):
                with self.subTest(base=base):
                    result = self.run_guard(root, f"--diff-base={base}")
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("input error", result.stderr)
            result = self.run_guard(root, "--diff-base", "HEAD", "--diff-base", "HEAD")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("only once", result.stderr)

    def test_diff_mode_scans_untracked_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_git(root)
            tracked = root / "skills/demo/SKILL.md"
            tracked.parent.mkdir(parents=True)
            tracked.write_text("VAULT=${VAULT_PATH}\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "base")
            base = self._git_head(root)
            leaked_path = "/Users/" + "someone/projects/my-vault/notes"
            untracked = root / "skills/demo/notes.md"
            untracked.write_text(f"LEAK={leaked_path}\n", encoding="utf-8")
            result = self.run_guard(root, "--diff-base", base)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("RUNTIME_HOME_PATH", result.stderr)
            self.assertNotIn(leaked_path, result.stderr)

    def test_diff_mode_handles_unicode_pathname(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_git(root)
            target = root / "skills/demo/강의.part notes.md"
            target.parent.mkdir(parents=True)
            target.write_text("VAULT=${VAULT_PATH}\n", encoding="utf-8")
            self._git(root, "add", "-A")
            self._git(root, "commit", "-m", "base")
            base = self._git_head(root)
            leaked_path = "/Users/" + "someone/projects/my-vault/notes"
            target.write_text(f"LEAK={leaked_path}\n", encoding="utf-8")
            result = self.run_guard(root, "--diff-base", base)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("RUNTIME_HOME_PATH", result.stderr)
            self.assertNotIn(leaked_path, result.stderr)

    def test_diff_mode_reads_markdown_despite_binary_and_textconv(self) -> None:
        body = "A" * 20
        token = "github_" + "pat_" + body
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_git(root)
            target = root / "skills/demo/notes.md"
            target.parent.mkdir(parents=True)
            target.write_text("safe\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "base")
            base = self._git_head(root)
            attributes = root / ".gitattributes"
            attributes.write_text("*.md -diff\n*.md diff=hide\n", encoding="utf-8")
            config = root / ".git" / "config"
            config.write_text(
                config.read_text(encoding="utf-8")
                + "[diff \"hide\"]\n\ttextconv = printf hidden\\n\n",
                encoding="utf-8",
            )
            target.write_text("GITHUB_" + "TOKEN=" + token + "\n", encoding="utf-8")
            result = self.run_guard(root, "--diff-base", base)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("SECRET_GITHUB_TOKEN", result.stderr)
            self.assertNotIn(token, result.stderr)
            self.assertNotIn(token, result.stdout)

    def test_diff_mode_keeps_plus_prefixed_added_line_and_numbers_after_removal(self) -> None:
        body = "A" * 20
        token = "github_" + "pat_" + body
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_git(root)
            target = root / "skills/demo/notes.md"
            target.parent.mkdir(parents=True)
            target.write_text("keep\nold secret line\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "base")
            base = self._git_head(root)
            target.write_text("keep\n+" + token + "\nGITHUB_" + "TOKEN=" + token + "\n", encoding="utf-8")
            result = self.run_guard(root, "--diff-base", base)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("SECRET_GITHUB_TOKEN", result.stderr)
            self.assertIn("skills/demo/notes.md:3:", result.stderr)
            self.assertNotIn(token, result.stderr)
            self.assertNotIn(token, result.stdout)

    def test_explicit_missing_path_exits_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills/demo").mkdir(parents=True)
            result = self.run_guard(root, "skills/demo/missing.md")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("input error", result.stderr)
            self.assertIn("missing path", result.stderr)

    def test_explicit_outside_path_exits_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            (root / "skills/demo").mkdir(parents=True)
            foreign = Path(outside) / "secret.md"
            token = "real_live_" + "value_1234567890"
            foreign.write_text("api_" + f"key = {token}\n", encoding="utf-8")
            result = self.run_guard(root, str(foreign))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("input error", result.stderr)
            self.assertNotIn(token, result.stderr)

    def test_escaped_symlink_is_not_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            self._init_git(root)
            package = root / "skills/demo"
            package.mkdir(parents=True)
            (package / "SKILL.md").write_text("VAULT=${VAULT_PATH}\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "base")
            base = self._git_head(root)
            token = "real_live_" + "value_1234567890"
            foreign = Path(outside) / "secret.md"
            foreign.write_text("api_" + f"key = {token}\n", encoding="utf-8")
            link = package / "references" / "external.md"
            link.parent.mkdir()
            link.symlink_to(foreign)
            explicit = self.run_guard(root, "skills/demo/references/external.md")
            self.assertEqual(explicit.returncode, 2, explicit.stdout + explicit.stderr)
            self.assertIn("input error", explicit.stderr)
            self.assertNotIn(token, explicit.stderr)
            self._git(root, "add", "skills/demo/references/external.md")
            diff = self.run_guard(root, "--diff-base", base)
            self.assertEqual(diff.returncode, 2, diff.stdout + diff.stderr)
            self.assertIn("input error", diff.stderr)
            self.assertNotIn(token, diff.stderr)

    def test_multi_suffix_env_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            demo = root / "skills/demo"
            demo.mkdir(parents=True)
            (demo / "SKILL.md").write_text("ok\n", encoding="utf-8")
            (demo / ".env.example").write_text("KEY=\n", encoding="utf-8")
            example = self.run_guard(root, "skills/demo/.env.example")
            self.assertEqual(example.returncode, 0, example.stderr)
            secret = demo / ".env.production.local"
            secret.write_text("KEY=1\n", encoding="utf-8")
            result = self.run_guard(root, "skills/demo/.env.production.local")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("RUNTIME_ENV_FILE", result.stderr)
            self.assertNotIn("KEY=1", result.stderr)

    def test_unreadable_explicit_file_exits_two(self) -> None:
        wrapper = """import pathlib, runpy, sys
script = sys.argv.pop(1)
original = pathlib.Path.read_text
def checked_read(path, *args, **kwargs):
    if path.name == 'SKILL.md':
        raise PermissionError('injected read failure')
    return original(path, *args, **kwargs)
pathlib.Path.read_text = checked_read
runpy.run_path(script, run_name='__main__')
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "skills/demo/SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("VAULT=${VAULT_PATH}\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-c", wrapper, str(SCRIPT),
                 "--root", str(root), "skills/demo/SKILL.md"],
                cwd=root, text=True, capture_output=True, check=False,
                env=_isolated_git_env(),
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("injected read failure", result.stderr)

    def test_git_failure_does_not_scan_the_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            leaked_path = "/Users/" + "someone/projects/my-vault/notes"
            target = root / "skills/demo/SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text(f"VAULT={leaked_path}\n", encoding="utf-8")
            empty_bin = root / "empty-bin"
            empty_bin.mkdir()
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--root", str(root)],
                env=_isolated_git_env({"PATH": str(empty_bin)}),
                capture_output=True, text=True, check=False, cwd=root,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("input error", result.stderr)
            self.assertNotIn("RUNTIME_HOME_PATH", result.stderr)
            self.assertNotIn(leaked_path, result.stderr)

    def test_claude_plugin_manifest_secret_is_detected_and_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / ".claude-plugin"
            plugin.mkdir()
            token = "real_live_" + "value_1234567890"
            (plugin / "marketplace.json").write_text(
                '{\n  "name": "craft-skills",\n  "api_' + 'key": "' + token + '"\n}\n',
                encoding="utf-8",
            )
            (plugin / "plugin.json").write_text(
                '{\n  "name": "craft-skills",\n  "version": "1.0.0"\n}\n',
                encoding="utf-8",
            )
            leaked = self.run_guard(root, ".claude-plugin/marketplace.json")
            self.assertEqual(leaked.returncode, 1, leaked.stdout + leaked.stderr)
            self.assertIn("SECRET_ASSIGNMENT", leaked.stderr)
            self.assertNotIn(token, leaked.stderr)
            self.assertNotIn(token, leaked.stdout)
            clean = self.run_guard(root, ".claude-plugin/plugin.json")
            self.assertEqual(clean.returncode, 0, clean.stderr)

    def test_explicit_file_mode_does_not_write_source_cache(self) -> None:
        format_src = REPO_ROOT / "skills/skillify/scripts/validate-skill-format.py"
        with tempfile.TemporaryDirectory() as tmp:
            layout = Path(tmp)
            scripts = layout / "skills" / "skillify" / "scripts"
            scripts.mkdir(parents=True)
            hygiene_src = scripts / "validate-runtime-hygiene.py"
            hygiene_src.write_bytes(SCRIPT.read_bytes())
            (scripts / "validate-skill-format.py").write_bytes(format_src.read_bytes())
            scan_root = layout / "scan"
            target = scan_root / "skills" / "demo" / "SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("VAULT=${VAULT_PATH}\n", encoding="utf-8")
            before = sorted(path.relative_to(layout).as_posix() for path in layout.rglob("*") if path.is_file())
            result = subprocess.run(
                [sys.executable, str(hygiene_src), "--root", str(scan_root), "skills/demo/SKILL.md"],
                cwd=scan_root,
                text=True,
                capture_output=True,
                check=False,
                env=_isolated_git_env(),
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            after = sorted(path.relative_to(layout).as_posix() for path in layout.rglob("*") if path.is_file())
            self.assertEqual(after, before)
            self.assertEqual(list(layout.rglob("__pycache__")), [])
            self.assertEqual(list(layout.rglob("*.pyc")), [])
            self.assertEqual(list(layout.rglob("*.pyo")), [])


if __name__ == "__main__":
    unittest.main()
