#!/usr/bin/env python3
"""Tests for skillify skill-format validator (v4 contract)."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "skills/skillify/scripts/validate-skill-format.py"

GOOD_SKILL = """---
name: demo
description: Does a demo thing end to end. Use when the user asks for a demo, wants a demo run, or says demo this for me please right now.
metadata:
  version: 1.0.0
---

# demo

## Overview
A demo skill.
"""
GOOD_CHANGELOG = "# Change Log\n\n- 2026-06-07 — initial; created the demo skill.\n"


class SkillFormatValidatorTest(unittest.TestCase):
    def run_validator(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), "--root", str(root), *args],
            cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )

    def _make_skill(self, root: Path, name: str, skill_md: str, changelog: str | None) -> Path:
        d = root / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(skill_md, encoding="utf-8")
        if changelog is not None:
            (d / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
        return d

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

    def test_rejects_body_over_line_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            huge = GOOD_SKILL + ("\nline\n" * 600)
            self._make_skill(root, "demo", huge, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("BODY_TOO_LONG", result.stdout)

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

    # ------------------------------------------------------------------
    # diff-base scoping regression
    # ------------------------------------------------------------------

    def _init_git_repo(self, root: Path) -> None:
        """Initialise a throwaway git repo, add all files, and make the first commit."""
        for cmd in [
            ["git", "init", str(root)],
            ["git", "-C", str(root), "config", "user.email", "test@example.com"],
            ["git", "-C", str(root), "config", "user.name", "Test"],
            ["git", "-C", str(root), "add", "-A"],
            ["git", "-C", str(root), "commit", "-m", "init", "--allow-empty"],
        ]:
            subprocess.run(cmd, check=True, capture_output=True)

    def _git_head(self, root: Path) -> str:
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    def test_diff_base_sibling_reference_change_not_enforced(self) -> None:
        """Regression: a package whose SKILL.md is unchanged but whose sibling
        references/*.md changed must NOT be pulled into diff-base enforcement.
        A package whose own SKILL.md changed MUST be enforced."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_dir = root / "skills"

            # pkg-a: BAD SKILL.md (missing metadata). Only its references/ file
            # will change after the base commit → must NOT be enforced.
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
            self.assertNotIn("pkg-a", result.stdout)


if __name__ == "__main__":
    unittest.main()
