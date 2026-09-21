#!/usr/bin/env python3
"""Tests for skillify's package selection and format contract."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills/skillify/scripts/validate-skill-format.py"
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

GOOD_SKILL = """---
name: demo
description: Does a demo thing end to end. Use when the user asks for a demo, wants a demo run, or says demo this for me please right now.
metadata:
  version: 1.0.0
---

# demo

A demo transcript in the working directory.
Missing input stops the run with a message.

## Overview
A demo skill.
"""
GOOD_CHANGELOG = "# Change Log\n\n- 2026-06-07 — initial; created the demo skill.\n"
GOOD_EVALS = json.dumps({
    "skill": "demo",
    "cases": [
        {"id": "run", "prompt": "demo this", "expected_behavior": "runs", "grading": "verifiable",
         "assertions": ["transcript exists"]},
        {"id": "judge", "prompt": "demo nicely", "expected_behavior": "reads well", "grading": "subjective",
         "rubric": ["clear"]},
        {"id": "stop", "prompt": "demo nothing", "expected_behavior": "stops", "grading": "verifiable",
         "assertions": ["no transcript"]},
    ],
})
GOOD_TRIGGERS = json.dumps({
    "skill": "demo",
    "should_trigger": [f"demo case {i}" for i in range(8)],
    "should_not_trigger": [f"unrelated case {i}" for i in range(8)],
})


class SkillFormatValidatorTest(unittest.TestCase):
    def run_validator(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), "--root", str(root), *args],
            cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            env=_isolated_git_env(),
        )

    def _make_skill(self, root: Path, name: str, skill_md: str, changelog: str | None,
                    evals: str | None = GOOD_EVALS, triggers: str | None = GOOD_TRIGGERS) -> Path:
        d = root / "skills" / name
        d.mkdir(parents=True)
        if not (root / ".git").exists():
            self._git(root, "init", "--template=")
            self._git(root, "config", "--local", "user.email", "test@example.com")
            self._git(root, "config", "--local", "user.name", "Test")
            self._git(root, "config", "--local", "commit.gpgsign", "false")
            self._git(root, "config", "--local", "tag.gpgsign", "false")
            self._git(root, "config", "--local", "core.hooksPath", "/dev/null")
        (d / "SKILL.md").write_text(skill_md, encoding="utf-8")
        if changelog is not None:
            (d / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
        corpus = root / "tests" / name / "evals"
        corpus.mkdir(parents=True)
        if evals == GOOD_EVALS:
            evals = json.dumps({**json.loads(GOOD_EVALS), "skill": name}, ensure_ascii=False)
        if triggers == GOOD_TRIGGERS:
            triggers = json.dumps({**json.loads(GOOD_TRIGGERS), "skill": name}, ensure_ascii=False)
        if evals is not None:
            (corpus / "evals.json").write_text(evals, encoding="utf-8")
        if triggers is not None:
            (corpus / "triggers.json").write_text(triggers, encoding="utf-8")
        return d

    def test_does_not_require_output_contract_heading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("MISSING_CONTRACT_SECTION", result.stdout)

    def test_contract_failure_wording_is_not_lexically_enforced(self) -> None:
        """Outcome/failure meaning is judged, not scanned for headings or keywords."""
        for replacement in ("", "Produce nonstop output."):
            with self.subTest(replacement=replacement):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    body = GOOD_SKILL.replace(
                        "Missing input stops the run with a message.\n" if not replacement
                        else "Missing input stops the run with a message.",
                        replacement,
                    )
                    self._make_skill(root, "demo", body, GOOD_CHANGELOG)
                    result = self.run_validator(root)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertNotIn("CONTRACT_LACKS_FAILURE_BRANCH", result.stdout)
                    self.assertNotIn("MISSING_CONTRACT_SECTION", result.stdout)

    def test_rejects_traversal_link_out_of_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = GOOD_SKILL + "\nSee [the contract](../skillify/references/contract.md) for provenance.\n"
            self._make_skill(root, "demo", body, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("TRAVERSAL_LINK", result.stdout)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = GOOD_SKILL + "\nThe `skillify` skill's contract reference owns provenance.\n"
            self._make_skill(root, "demo", body, GOOD_CHANGELOG)
            self.assertEqual(self.run_validator(root).returncode, 0)

    def test_rejects_referenced_path_that_does_not_ship(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = GOOD_SKILL + "\nRun `$SKILL_DIR/scripts/deploy.py` then read `references/schema.md`.\nGlob forms like `references/*.md` and `scripts/<name>` are fine.\n"
            d = self._make_skill(root, "demo", body, GOOD_CHANGELOG)
            (d / "references").mkdir()
            (d / "references" / "schema.md").write_text("# schema\n", encoding="utf-8")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("MISSING_REFERENCED_PATH", result.stdout)
            self.assertNotIn("references/schema.md", result.stdout)
            (d / "scripts").mkdir()
            (d / "scripts" / "deploy.py").write_text("", encoding="utf-8")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_sibling_package_support_file_is_not_this_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sibling = self._make_skill(
                root, "skillify", GOOD_SKILL.replace("name: demo", "name: skillify"),
                GOOD_CHANGELOG, evals=None, triggers=None,
            )
            (sibling / "references").mkdir()
            (sibling / "references" / "schema.md").write_text("# sibling\n", encoding="utf-8")
            body = GOOD_SKILL + "\nRead `references/schema.md`.\n"
            demo = self._make_skill(root, "demo", body, GOOD_CHANGELOG)
            (demo / "references").mkdir()
            (demo / "references" / "schema.md").symlink_to(sibling / "references" / "schema.md")
            result = self.run_validator(root, "--package", "skills/demo")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("MISSING_REFERENCED_PATH", result.stdout)

    def test_in_package_symlink_to_contained_file_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = GOOD_SKILL + "\nRead `references/alias.md`.\n"
            demo = self._make_skill(root, "demo", body, GOOD_CHANGELOG)
            (demo / "references").mkdir()
            (demo / "references" / "schema.md").write_text("# local\n", encoding="utf-8")
            (demo / "references" / "alias.md").symlink_to("schema.md")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("MISSING_REFERENCED_PATH", result.stdout)

    def test_dangling_in_package_symlink_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = GOOD_SKILL + "\nRead `references/missing.md`.\n"
            demo = self._make_skill(root, "demo", body, GOOD_CHANGELOG)
            (demo / "references").mkdir()
            (demo / "references" / "missing.md").symlink_to("no-such.md")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("MISSING_REFERENCED_PATH", result.stdout)

    def test_support_symlink_escaping_the_package_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            body = GOOD_SKILL + "\nRead `references/external.md`.\n"
            demo = self._make_skill(root, "demo", body, GOOD_CHANGELOG)
            external = Path(outside) / "fixture.md"
            external.write_text("outside\n", encoding="utf-8")
            (demo / "references").mkdir()
            (demo / "references" / "external.md").symlink_to(external)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("MISSING_REFERENCED_PATH", result.stdout)

    def test_repository_test_reference_is_not_package_local(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = GOOD_SKILL + "\nUse repo-root `tests/demo/evals/evals.json` for scenarios.\n"
            self._make_skill(root, "demo", body, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unreadable_package_inputs_fail_closed_even_when_advisory(self) -> None:
        wrapper = """import pathlib, runpy, sys
filename = sys.argv.pop(1)
script = sys.argv.pop(1)
original = pathlib.Path.read_text
def checked_read(path, *args, **kwargs):
    if path.name == filename:
        raise PermissionError('injected read failure: ' + filename)
    return original(path, *args, **kwargs)
pathlib.Path.read_text = checked_read
runpy.run_path(script, run_name='__main__')
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            for filename in ("SKILL.md", "CHANGELOG.md"):
                for flags in ((), ("--advisory",)):
                    with self.subTest(filename=filename, flags=flags):
                        result = subprocess.run(
                            [sys.executable, "-c", wrapper, filename, str(SCRIPT),
                             "--root", str(root), *flags],
                            cwd=root, text=True, capture_output=True, check=False,
                            env=_isolated_git_env(),
                        )
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                        self.assertIn("injected read failure", result.stderr)

    def test_corpus_absence_does_not_impose_a_quality_quota(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG, evals=None, triggers=None)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("NO_EVAL_CORPUS", result.stdout)

    def test_optional_eval_files_are_not_a_format_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evals = json.loads(GOOD_EVALS)
            evals["cases"] = evals["cases"][:1]
            evals["cases"][0]["assertions"] = "not a list"
            evals["skill"] = "other"
            triggers = {"should_trigger": [42], "should_not_trigger": "not a list"}
            self._make_skill(
                root, "demo", GOOD_SKILL, GOOD_CHANGELOG,
                evals=json.dumps(evals), triggers=json.dumps(triggers),
            )
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("BAD_EVAL_CORPUS", result.stdout)
            self.assertNotIn("NO_EVAL_CORPUS", result.stdout)

    def test_accepts_well_formed_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_missing_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            no_meta = GOOD_SKILL.replace("metadata:\n  version: 1.0.0\n", "")
            self._make_skill(root, "demo", no_meta, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NO_METADATA", result.stdout)

    def test_rejects_bad_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_ver = GOOD_SKILL.replace("version: 1.0.0", "version: v1")
            self._make_skill(root, "demo", bad_ver, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("BAD_VERSION", result.stdout)

    def test_rejects_missing_changelog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, None)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NO_CHANGELOG", result.stdout)

    def test_rejects_changelog_section_in_skill_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = GOOD_SKILL + "\n## Change Log\n- 2026-06-07 — nope\n"
            self._make_skill(root, "demo", bad, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("CHANGELOG_IN_SKILL", result.stdout)

    def test_rejects_name_dir_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL.replace("name: demo", "name: other"), GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NAME_MISMATCH", result.stdout)

    def test_rejects_non_kebab_case_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = GOOD_SKILL.replace("name: demo", "name: Demo_Skill")
            self._make_skill(root, "Demo_Skill", bad, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NAME_NOT_KEBAB_CASE", result.stdout)

    def test_accepts_name_at_64_character_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            name = "a" * 64
            skill = GOOD_SKILL.replace("name: demo", f"name: {name}")
            self._make_skill(root, name, skill, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_name_over_64_character_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            name = "a" * 65
            skill = GOOD_SKILL.replace("name: demo", f"name: {name}")
            self._make_skill(root, name, skill, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NAME_TOO_LONG", result.stdout)

    def test_rejects_non_string_metadata_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = (
                "  labels: [one, two]\n",
                "  labels:\n    - one\n    - two\n",
                "  source: {owner: team}\n",
                "  source:\n    owner: team\n",
                "  enabled: true\n",
                "  priority: 1\n",
            )
            for index, value in enumerate(cases):
                with self.subTest(value=value):
                    skill = GOOD_SKILL.replace(
                        "  version: 1.0.0\n",
                        f"  version: 1.0.0\n{value}",
                    )
                    case_root = root / str(index)
                    self._make_skill(case_root, "demo", skill, GOOD_CHANGELOG)
                    result = self.run_validator(case_root)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("BAD_METADATA", result.stdout)

    def test_rejects_changelog_without_dated_bullet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, "# Change Log\n\n- created the skill\n")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("CHANGELOG_NO_DATED_BULLET", result.stdout)

    def test_accepts_changelog_at_100_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lines = ["# Changelog", "", "- 2026-06-07 — initial; created the demo skill."]
            lines.extend([""] * (100 - len(lines)))
            self.assertEqual(len(lines), 100)
            self._make_skill(root, "demo", GOOD_SKILL, "\n".join(lines) + "\n")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("CHANGELOG_TOO_LONG", result.stdout)

    def test_rejects_changelog_over_100_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lines = ["# Changelog", "", "- 2026-06-07 — initial; created the demo skill."]
            lines.extend([""] * (101 - len(lines)))
            self.assertEqual(len(lines), 101)
            self._make_skill(root, "demo", GOOD_SKILL, "\n".join(lines) + "\n")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("CHANGELOG_TOO_LONG", result.stdout)
            self.assertNotIn("CHANGELOG_NO_DATED_BULLET", result.stdout)

    def test_escaping_changelog_symlink_is_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            secret = Path(outside) / "secret.md"
            secret.write_text("SENTINEL-OUTSIDE-CHANGELOG\n", encoding="utf-8")
            demo = self._make_skill(root, "demo", GOOD_SKILL, None)
            (demo / "CHANGELOG.md").symlink_to(secret)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("escapes root", result.stderr)
            self.assertNotIn("SENTINEL-OUTSIDE-CHANGELOG", result.stdout)
            self.assertNotIn("SENTINEL-OUTSIDE-CHANGELOG", result.stderr)

    def test_contained_changelog_symlink_is_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            demo = self._make_skill(root, "demo", GOOD_SKILL, None)
            real = demo / "HISTORY.md"
            real.write_text("- 2026-06-07 — initial; created the demo skill.\n", encoding="utf-8")
            (demo / "CHANGELOG.md").symlink_to("HISTORY.md")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_advisory_always_exit_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, None)  # missing changelog
            result = self.run_validator(root, "--advisory")
            self.assertEqual(result.returncode, 0)
            self.assertIn("NO_CHANGELOG", result.stdout)

    def test_rejects_forbidden_top_level_version_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = GOOD_SKILL.replace(
                "metadata:\n  version: 1.0.0\n",
                "version: 1.0.0\nmetadata:\n  version: 1.0.0\n",
            )
            self._make_skill(root, "demo", legacy, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("FORBIDDEN_KEY", result.stdout)
            self.assertIn("version", result.stdout)

    def test_accepts_agent_skills_optional_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            optional = GOOD_SKILL.replace(
                "metadata:\n  version: 1.0.0\n",
                "metadata:\n  version: 1.0.0\n"
                "license: Apache-2.0\n"
                "compatibility: Requires a POSIX shell.\n"
                "allowed-tools: Bash Read\n",
            )
            self._make_skill(root, "demo", optional, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_invalid_agent_skills_optional_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = [
                ("license: []\n", "BAD_LICENSE"),
                ("license: '   '\n", "BAD_LICENSE"),
                ("compatibility: []\n", "BAD_COMPATIBILITY"),
                ("compatibility: \n", "BAD_COMPATIBILITY"),
                (f"compatibility: {'x' * 501}\n", "BAD_COMPATIBILITY"),
                ("allowed-tools: [Bash, Read]\n", "BAD_ALLOWED_TOOLS"),
                ("allowed-tools: \n", "BAD_ALLOWED_TOOLS"),
            ]
            for index, (field, finding) in enumerate(cases):
                with self.subTest(field=field):
                    skill = GOOD_SKILL.replace(
                        "metadata:\n  version: 1.0.0\n",
                        f"metadata:\n  version: 1.0.0\n{field}",
                    )
                    case_root = root / str(index)
                    self._make_skill(case_root, "demo", skill, GOOD_CHANGELOG)
                    result = self.run_validator(case_root)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(finding, result.stdout)

    def test_rejects_cursor_and_grok_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index, field in enumerate((
                "paths: src/**\n",
                "disable-model-invocation: true\n",
                "when-to-use: Use for runtime-specific routing.\n",
                "argument-hint: <request>\n",
            )):
                with self.subTest(field=field):
                    skill = GOOD_SKILL.replace(
                        "metadata:\n  version: 1.0.0\n",
                        f"metadata:\n  version: 1.0.0\n{field}",
                    )
                    case_root = root / str(index)
                    self._make_skill(case_root, "demo", skill, GOOD_CHANGELOG)
                    result = self.run_validator(case_root)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("FORBIDDEN_KEY", result.stdout)

    def test_long_body_is_not_a_format_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            huge = GOOD_SKILL + ("\nline\n" * 600)
            self._make_skill(root, "demo", huge, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("BODY_TOO_LONG", result.stdout)

    def test_rejects_nested_skill_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            nested = d / "child"
            nested.mkdir()
            (nested / "SKILL.md").write_text(GOOD_SKILL.replace("name: demo", "name: child"),
                                             encoding="utf-8")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NESTED_SKILL_MD", result.stdout)

    def test_rejects_nested_agent_skill_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            nested = d / "agents"
            nested.mkdir()
            (nested / "SKILL.md").write_text(GOOD_SKILL.replace("name: demo", "name: child"),
                                             encoding="utf-8")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NESTED_SKILL_MD", result.stdout)

    def test_description_short_is_warning_not_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            short = GOOD_SKILL.replace(
                "description: Does a demo thing end to end. Use when the user asks for a demo, wants a demo run, or says demo this for me please right now.",
                "description: Does a demo thing. Use when asked.",
            )
            self._make_skill(root, "demo", short, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("DESCRIPTION_SHORT", result.stdout)

    def test_description_over_hard_max_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            long_desc = "x" * 1025
            too_long = GOOD_SKILL.replace(
                "description: Does a demo thing end to end. Use when the user asks for a demo, wants a demo run, or says demo this for me please right now.",
                f"description: {long_desc}",
            )
            self._make_skill(root, "demo", too_long, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("DESCRIPTION_TOO_LONG", result.stdout)

    def _description_result(self, description: str, *args: str) -> subprocess.CompletedProcess[str]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        skill = GOOD_SKILL.replace(
            "Does a demo thing end to end. Use when the user asks for a demo, wants a demo run, or says demo this for me please right now.",
            description,
        )
        self._make_skill(root, "demo", skill, GOOD_CHANGELOG)
        return self.run_validator(root, *args)

    def test_routing_phrases_are_not_a_format_gate(self) -> None:
        for description in (
            "Use this skill for ordinary requests.",
            "MUST USE for deployment requests. Handle production deployments.",
            "MUST USE for ANY deployment request. Handle production deployments.",
            "MUST  USE this skill for deployment requests.",
            "MUST-USE this skill for deployment requests.",
            "Must use ANY deployment skill.",
            "Use this skill for ANY deployment.",
        ):
            with self.subTest(description=description):
                result = self._description_result(description)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn("MUST_USE", result.stdout)
                self.assertNotIn("DIRECTIVE_", result.stdout)
                self.assertNotIn("MISPLACED_DIRECTIVE_ANY", result.stdout)

    def test_rejects_noncanonical_double_quoted_yaml_escape(self) -> None:
        result = self._description_result(
            r'"\x4dUST USE for deployment requests. Handle production deployments."'
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("NO_DESCRIPTION", result.stdout)

    def test_rejects_multiline_description_scalar(self) -> None:
        result = self._description_result(
            ">-\n  MUST USE for ANY deployment request. Handle deployments."
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("NO_DESCRIPTION", result.stdout)

    def test_multi_suffix_tracked_env_is_rejected_example_exempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            demo = self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            (demo / ".env.example").write_text("KEY=\n", encoding="utf-8")
            self._git(root, "add", "skills/demo/.env.example")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("TRACKED_ENV", result.stdout)
            secrets = (
                ".env",
                ".env.production.local",
                ".env.local",
                ".env.staging.bak",
            )
            for name in secrets:
                (demo / name).write_text("SECRET=1\n", encoding="utf-8")
                self._git(root, "add", f"skills/demo/{name}")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            out = result.stdout
            self.assertIn("TRACKED_ENV", out)
            self.assertIn(".env.production.local", out)
            self.assertNotIn(".env.example", out)

    def test_unusual_tracked_env_path_names_are_still_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            demo = self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            weird = demo / "dir with tab\tand 강의.part"
            weird.mkdir()
            secret = weird / ".env.production.local"
            secret.write_text("SECRET=1\n", encoding="utf-8")
            self._git(root, "add", "-A")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("TRACKED_ENV", result.stdout)
            self.assertIn(".env.production.local", result.stdout)

    # ------------------------------------------------------------------
    # diff-base scoping regression
    # ------------------------------------------------------------------

    def _init_git_repo(self, root: Path) -> None:
        """Initialise a throwaway git repo, add all files, and make the first commit."""
        if not (root / ".git").exists():
            self._git(root, "init", "--template=")
            self._git(root, "config", "--local", "user.email", "test@example.com")
            self._git(root, "config", "--local", "user.name", "Test")
            self._git(root, "config", "--local", "commit.gpgsign", "false")
            self._git(root, "config", "--local", "tag.gpgsign", "false")
            self._git(root, "config", "--local", "core.hooksPath", "/dev/null")
        self._git(root, "add", "-A")
        self._git(root, "commit", "-m", "init", "--allow-empty")

    def _git_head(self, root: Path) -> str:
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
            env=_isolated_git_env(),
        ).stdout.strip()

    def test_support_changes_select_the_actual_package(self) -> None:
        """References and primary-body changes both select their owners."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_dir = root / "skills"

            # A bad package is relevant when its support file changes.
            bad_skill_a = (
                GOOD_SKILL
                .replace("name: demo", "name: pkg-a")
                .replace("metadata:\n  version: 1.0.0\n", "")
            )
            self._make_skill(root, "pkg-a", bad_skill_a, GOOD_CHANGELOG)
            (skills_dir / "pkg-a" / "references").mkdir(parents=True)
            (skills_dir / "pkg-a" / "references" / "notes.md").write_text(
                "original\n", encoding="utf-8"
            )

            # pkg-b: GOOD SKILL.md initially. Its SKILL.md will be rewritten to
            # a BAD version after the base commit → MUST be enforced and fail.
            good_skill_b = GOOD_SKILL.replace("name: demo", "name: pkg-b")
            self._make_skill(root, "pkg-b", good_skill_b, GOOD_CHANGELOG)

            self._init_git_repo(root)
            base = self._git_head(root)

            (skills_dir / "pkg-a" / "references" / "notes.md").write_text(
                "updated\n", encoding="utf-8"
            )
            bad_skill_b = good_skill_b.replace("metadata:\n  version: 1.0.0\n", "")
            (skills_dir / "pkg-b" / "SKILL.md").write_text(bad_skill_b, encoding="utf-8")

            result = self.run_validator(root, "--diff-base", base)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("pkg-b", result.stdout)
            self.assertIn("NO_METADATA", result.stdout)
            self.assertIn("pkg-a", result.stdout)

    def _git(self, root: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            env=_isolated_git_env(),
        )

    def test_four_git_states_select_support_without_widening_to_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("committed", "staged", "unstaged", "untracked", "legacy"):
                skill = GOOD_SKILL.replace("name: demo", f"name: {name}")
                if name == "legacy":
                    skill = skill.replace("metadata:\n  version: 1.0.0\n", "")
                package = self._make_skill(root, name, skill, GOOD_CHANGELOG)
                (package / "references").mkdir()
                (package / "references" / "notes.md").write_text("original\n")
            self._init_git_repo(root)
            base = self._git_head(root)
            (root / "skills/committed/references/notes.md").write_text("committed\n")
            self._git(root, "add", "skills/committed")
            self._git(root, "commit", "-m", "committed support")
            (root / "skills/staged/references/notes.md").write_text("staged\n")
            self._git(root, "add", "skills/staged")
            (root / "skills/unstaged/references/notes.md").write_text("unstaged\n")
            (root / "skills/untracked/references/new\n notes.md").write_text("untracked\n")
            (root / "skills/untracked/references/new\\ notes.md").write_text("literal backslash\n")
            result = self.run_validator(root, "--diff-base", base)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for name in ("committed", "staged", "unstaged", "untracked"):
                self.assertIn(f"scope: package skills/{name}\n", result.stdout)
            self.assertNotIn("legacy", result.stdout)
            full = self.run_validator(root)
            self.assertEqual(full.returncode, 1, full.stdout + full.stderr)
            self.assertIn("NO_METADATA", full.stdout)

    def test_staged_then_unstaged_cancellation_still_selects_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            self._init_git_repo(root)
            base = self._git_head(root)
            (package / "CHANGELOG.md").write_text(GOOD_CHANGELOG + "staged\n")
            self._git(root, "add", ".")
            (package / "CHANGELOG.md").write_text(GOOD_CHANGELOG)
            result = self.run_validator(root, "--diff-base", base)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("scope: package skills/demo", result.stdout)

    def test_corpus_only_change_still_selects_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            self._init_git_repo(root)
            base = self._git_head(root)
            (root / "tests/demo/evals/evals.json").write_text("{broken")
            result = self.run_validator(root, "--diff-base", base)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("scope: package skills/demo", result.stdout)
            self.assertNotIn("BAD_EVAL_CORPUS", result.stdout)

    def test_new_untracked_and_explicit_owners_form_a_deduplicated_union(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            self._init_git_repo(root)
            base = self._git_head(root)
            self._make_skill(root, "new-skill", GOOD_SKILL.replace("name: demo", "name: new-skill"),
                             GOOD_CHANGELOG, evals=None, triggers=None)
            result = self.run_validator(root, "--diff-base", base, "--package", "skills/demo",
                                        "--package", "skills/new-skill", "--package", "skills/demo")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.count("scope: package skills/demo\n"), 1)
            self.assertEqual(result.stdout.count("scope: package skills/new-skill\n"), 1)
            explicit = self.run_validator(root, "--package", "skills/new-skill")
            self.assertEqual(explicit.returncode, 0, explicit.stdout + explicit.stderr)
            self.assertNotIn("scope: package skills/demo", explicit.stdout)

    def test_invalid_base_and_range_fail_even_in_advisory_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            self._init_git_repo(root)
            for base in ("missing-ref", "HEAD...HEAD", "HEAD..HEAD", "--help"):
                with self.subTest(base=base):
                    result = self.run_validator(root, f"--diff-base={base}", "--advisory")
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("input error", result.stderr)

    def test_non_git_diff_scope_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_validator(Path(tmp), "--diff-base", "HEAD", "--advisory")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("Git", result.stderr)

    def test_missing_git_binary_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            empty_bin = root / "empty-bin"
            empty_bin.mkdir()
            for scope in ((), ("--package", "skills/demo"), ("--diff-base", "HEAD")):
                for advisory in ((), ("--advisory",)):
                    with self.subTest(scope=scope, advisory=advisory):
                        result = subprocess.run(
                            [sys.executable, str(SCRIPT), "--root", str(root),
                             *scope, *advisory],
                            env=_isolated_git_env({"PATH": str(empty_bin)}),
                            capture_output=True, text=True, check=False,
                        )
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                        self.assertIn("Git", result.stderr)

    def test_failed_git_inventory_is_not_an_empty_result(self) -> None:
        wrapper = """import runpy, subprocess, sys
script = sys.argv.pop(1)
original = subprocess.run
def checked_run(argv, *args, **kwargs):
    if argv[:2] == ['git', 'ls-files']:
        raise subprocess.CalledProcessError(128, argv, stderr=b'injected inventory denial')
    return original(argv, *args, **kwargs)
subprocess.run = checked_run
runpy.run_path(script, run_name='__main__')
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            for scope in ((), ("--package", "skills/demo")):
                for advisory in ((), ("--advisory",)):
                    with self.subTest(scope=scope, advisory=advisory):
                        result = subprocess.run(
                            [sys.executable, "-c", wrapper, str(SCRIPT),
                             "--root", str(root), *scope, *advisory],
                            capture_output=True, text=True, check=False,
                            env=_isolated_git_env(),
                        )
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                        self.assertIn("injected inventory denial", result.stderr)

    def test_repeated_diff_base_is_an_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            self._init_git_repo(root)
            for last in ("HEAD", "missing-ref"):
                for advisory in ((), ("--advisory",)):
                    with self.subTest(last=last, advisory=advisory):
                        result = self.run_validator(
                            root, "--diff-base", "HEAD", "--diff-base", last, *advisory,
                        )
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                        self.assertIn("only once", result.stderr)

    def test_full_scan_rejects_missing_skills_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_git_repo(root)
            for advisory in ((), ("--advisory",)):
                with self.subTest(advisory=advisory):
                    result = self.run_validator(root, *advisory)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("skills/", result.stderr)

    def test_git_scope_rejects_untracked_and_staged_external_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            package = self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            self._init_git_repo(root)
            base = self._git_head(root)
            external = Path(outside) / "fixture.md"
            external.write_text("Fixture outside the repository.\n")
            reference = package / "references/external.md"
            reference.parent.mkdir()
            reference.symlink_to(external)
            for state in ("untracked", "staged"):
                if state == "staged":
                    self._git(root, "add", "skills/demo/references/external.md")
                for advisory in ((), ("--advisory",)):
                    with self.subTest(state=state, advisory=advisory):
                        result = self.run_validator(root, "--diff-base", base, *advisory)
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                        self.assertIn("escapes root", result.stderr)

    def test_shared_contract_change_selects_skillify_not_unrelated_debt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "skillify",
                             GOOD_SKILL.replace("name: demo", "name: skillify"), GOOD_CHANGELOG)
            bad = GOOD_SKILL.replace("name: demo", "name: legacy").replace(
                "metadata:\n  version: 1.0.0\n", "")
            self._make_skill(root, "legacy", bad, GOOD_CHANGELOG)
            (root / "AGENTS.md").write_text("original\n")
            self._init_git_repo(root)
            (root / "AGENTS.md").write_text("updated contract\n")
            result = self.run_validator(root, "--diff-base", "HEAD")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("scope: package skills/skillify", result.stdout)
            self.assertNotIn("legacy", result.stdout)

    def test_ci_local_change_selects_skillify_not_unrelated_debt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "skillify",
                             GOOD_SKILL.replace("name: demo", "name: skillify"), GOOD_CHANGELOG)
            bad = GOOD_SKILL.replace("name: demo", "name: legacy").replace(
                "metadata:\n  version: 1.0.0\n", "")
            self._make_skill(root, "legacy", bad, GOOD_CHANGELOG)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "ci-local.sh").write_text("echo original\n")
            self._init_git_repo(root)
            (scripts / "ci-local.sh").write_text("echo updated gates\n")
            result = self.run_validator(root, "--diff-base", "HEAD")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("scope: package skills/skillify", result.stdout)
            self.assertNotIn("legacy", result.stdout)

    def test_ci_local_change_fails_when_shared_owner_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "ci-local.sh").write_text("echo original\n")
            self._init_git_repo(root)
            (scripts / "ci-local.sh").write_text("echo missing owner\n")
            result = self.run_validator(root, "--diff-base", "HEAD")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("shared format owner skills/skillify is missing", result.stderr)

    def test_explicit_owner_rejects_escape_and_non_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            (root / "skills/external").symlink_to(outside, target_is_directory=True)
            for package in ("skills", "skills/missing", "skills/*", "../skills/demo",
                            "skills/../skills/demo", "skills/demo/SKILL.md",
                            "skills/./demo", "skills//demo", "skills/demo/", "./skills/demo",
                            str(root / "skills/demo"), "skills/external"):
                with self.subTest(package=package):
                    result = self.run_validator(root, "--package", package, "--advisory")
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_late_head_and_index_owners_remain_retirement_evidence(self) -> None:
        for state in ("head", "index"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
                self._init_git_repo(root)
                base = self._git_head(root)
                late = self._make_skill(
                    root, "late", GOOD_SKILL.replace("name: demo", "name: late"),
                    GOOD_CHANGELOG,
                )
                self._git(root, "add", "skills/late", "tests/late")
                if state == "head":
                    self._git(root, "commit", "-m", "new owner after base")
                shutil.rmtree(late)
                partial = self.run_validator(root, "--diff-base", base)
                self.assertEqual(partial.returncode, 1, partial.stdout + partial.stderr)
                self.assertIn("INCOMPLETE_RETIREMENT", partial.stdout)
                shutil.rmtree(root / "tests/late")
                retired = self.run_validator(root, "--diff-base", base)
                self.assertEqual(retired.returncode, 0, retired.stdout + retired.stderr)
                self.assertIn("scope: tombstone skills/late", retired.stdout)
                self.assertNotIn("scope: package skills/demo", retired.stdout)

    def test_retirement_requires_no_files_or_inbound_package_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            (root / "README.md").write_text("Read `skills/demo/SKILL.md`.\n")
            self._init_git_repo(root)
            base = self._git_head(root)
            (package / "SKILL.md").unlink()
            partial = self.run_validator(root, "--diff-base", base)
            self.assertEqual(partial.returncode, 1, partial.stdout + partial.stderr)
            self.assertIn("INCOMPLETE_RETIREMENT", partial.stdout)
            self._git(root, "rm", "-r", "-f", "skills/demo")
            test_remains = self.run_validator(root, "--diff-base", base)
            self.assertEqual(test_remains.returncode, 1, test_remains.stdout + test_remains.stderr)
            self.assertIn("INCOMPLETE_RETIREMENT", test_remains.stdout)
            self._git(root, "rm", "-r", "-f", "tests/demo")
            dangling = self.run_validator(root, "--diff-base", base)
            self.assertEqual(dangling.returncode, 1, dangling.stdout + dangling.stderr)
            self.assertIn("DANGLING_PACKAGE_REFERENCE", dangling.stdout)
            (root / "README.md").write_text("No active package paths.\n")
            retired = self.run_validator(root, "--diff-base", base)
            self.assertEqual(retired.returncode, 0, retired.stdout + retired.stderr)
            self.assertIn("scope: tombstone skills/demo", retired.stdout)

    def test_retirement_checks_script_references_but_not_ignored_scratch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            consumer = self._make_skill(
                root, "consumer", GOOD_SKILL.replace("name: demo", "name: consumer"),
                GOOD_CHANGELOG, evals=None, triggers=None,
            )
            (root / ".gitignore").write_text("skills/**/evals/\n")
            script = consumer / "scripts" / "consume.py"
            script.parent.mkdir()
            script.write_text("resource = 'skills/demo/SKILL.md'\n")
            self._init_git_repo(root)
            base = self._git_head(root)
            self._git(root, "rm", "-r", "-f", "skills/demo", "tests/demo")
            dangling = self.run_validator(root, "--diff-base", base)
            self.assertEqual(dangling.returncode, 1, dangling.stdout + dangling.stderr)
            self.assertIn("DANGLING_PACKAGE_REFERENCE", dangling.stdout)
            script.unlink()
            scratch = consumer / "evals" / "capture.md"
            scratch.parent.mkdir()
            scratch.write_text("Historical command: skills/demo/SKILL.md\n")
            retired = self.run_validator(root, "--diff-base", base)
            self.assertEqual(retired.returncode, 0, retired.stdout + retired.stderr)
            self.assertNotIn("DANGLING_PACKAGE_REFERENCE", retired.stdout)

    def test_rename_tracks_old_and_new_owners(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            self._init_git_repo(root)
            base = self._git_head(root)
            self._git(root, "mv", "skills/demo", "skills/renamed")
            self._git(root, "mv", "tests/demo", "tests/renamed")
            (root / "skills/renamed/SKILL.md").write_text(
                GOOD_SKILL.replace("name: demo", "name: renamed"))
            for file in (root / "tests/renamed/evals").iterdir():
                data = json.loads(file.read_text())
                data["skill"] = "renamed"
                file.write_text(json.dumps(data, ensure_ascii=False))
            result = self.run_validator(root, "--diff-base", base)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("scope: tombstone skills/demo", result.stdout)
            self.assertIn("scope: package skills/renamed", result.stdout)

    def test_unowned_support_path_is_not_silently_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_git_repo(root)
            (root / "scripts").mkdir()
            (root / "scripts/unowned.py").write_text("pass\n")
            result = self.run_validator(root, "--diff-base", "HEAD")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("unresolved package/support ownership", result.stderr)


if __name__ == "__main__":
    unittest.main()
