#!/usr/bin/env python3
"""Tests for skillify skill-format validator."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "skills/skillify/scripts/validate-skill-format.py"

GOOD_SKILL = """---
name: demo
description: Does a demo thing. Use when the user asks for a demo.
version: 1.0.0
allowed-tools: [Bash, Read, Edit]
compatibility: claude-code, codex
---

# demo

## Overview
A demo skill.
"""
GOOD_CHANGELOG = "# Change Log\n\n- 2026-06-07 — initial; created the demo skill.\n"

# A sub-recipe carries only the agentskills.io minimum: name + description.
GOOD_SUBRECIPE = """---
name: adr
description: Author an Architecture Decision Record. Loaded by the documents waypoint when the user asks to write an ADR.
---

# adr

## Overview
Deep recipe for ADR authoring.
"""


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

    def _make_subrecipe(self, root: Path, parent: str, child: str, skill_md: str) -> Path:
        """Create a nested sub-recipe under a full parent package.

        The parent gets a well-formed 5-key SKILL.md + CHANGELOG; the child carries
        only the supplied SKILL.md (no version / CHANGELOG of its own).
        """
        self._make_skill(root, parent, GOOD_SKILL.replace("name: demo", f"name: {parent}"),
                         GOOD_CHANGELOG)
        d = root / "skills" / parent / child
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(skill_md, encoding="utf-8")
        return d

    def test_accepts_well_formed_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_missing_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            no_ver = GOOD_SKILL.replace("version: 1.0.0\n", "")
            self._make_skill(root, "demo", no_ver, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NO_VERSION", result.stdout)

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

    def test_rejects_missing_allowed_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            no_tools = GOOD_SKILL.replace("allowed-tools: [Bash, Read, Edit]\n", "")
            self._make_skill(root, "demo", no_tools, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NO_ALLOWED_TOOLS", result.stdout)

    def test_rejects_non_list_allowed_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scalar_tools = GOOD_SKILL.replace(
                "allowed-tools: [Bash, Read, Edit]",
                "allowed-tools: Bash",
            )
            self._make_skill(root, "demo", scalar_tools, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("BAD_ALLOWED_TOOLS", result.stdout)

    def test_rejects_missing_compatibility(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            no_compat = GOOD_SKILL.replace("compatibility: claude-code, codex\n", "")
            self._make_skill(root, "demo", no_compat, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NO_COMPATIBILITY", result.stdout)

    # ------------------------------------------------------------------
    # nested sub-recipe (thick-skill / progressive-disclosure) support
    # ------------------------------------------------------------------

    def test_accepts_subrecipe_with_only_name_and_description(self) -> None:
        """A nested SKILL.md whose parent dir has its own SKILL.md is a sub-recipe:
        it needs only name + description, no version/allowed-tools/compatibility/CHANGELOG."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_subrecipe(root, "documents", "adr", GOOD_SUBRECIPE)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_subrecipe_still_enforces_name_dir_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_subrecipe(root, "documents", "adr",
                                 GOOD_SUBRECIPE.replace("name: adr", "name: wrong"))
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NAME_MISMATCH", result.stdout)

    def test_subrecipe_requires_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            no_desc = "---\nname: adr\n---\n\n# adr\n"
            self._make_subrecipe(root, "documents", "adr", no_desc)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NO_DESCRIPTION", result.stdout)

    def test_subrecipe_bans_changelog_section_in_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = GOOD_SUBRECIPE + "\n## Change Log\n- 2026-06-07 — nope\n"
            self._make_subrecipe(root, "documents", "adr", bad)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("CHANGELOG_IN_SKILL", result.stdout)

    def test_area_leaf_is_not_a_subrecipe(self) -> None:
        """An area folder (no SKILL.md of its own) does NOT make its leaves sub-recipes;
        those leaves stay full packages and must carry the full 5-key shape + CHANGELOG."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # skills/area/leaf where skills/area has NO SKILL.md → leaf is a full package.
            leaf = root / "skills" / "area" / "leaf"
            leaf.mkdir(parents=True)
            (leaf / "SKILL.md").write_text(GOOD_SUBRECIPE.replace("name: adr", "name: leaf"),
                                           encoding="utf-8")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NO_VERSION", result.stdout)

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

    def test_diff_base_sibling_resolver_change_not_enforced(self) -> None:
        """Regression: a package whose SKILL.md is unchanged but whose sibling
        RESOLVER.md changed must NOT be pulled into diff-base enforcement.
        A package whose own SKILL.md changed MUST be enforced."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills_dir = root / "skills"

            # pkg-a: BAD SKILL.md (missing allowed-tools).  Only its RESOLVER.md
            # will change after the base commit → must NOT be enforced.
            bad_skill_a = (
                GOOD_SKILL
                .replace("name: demo", "name: pkg-a")
                .replace("allowed-tools: [Bash, Read, Edit]\n", "")
            )
            self._make_skill(root, "pkg-a", bad_skill_a, GOOD_CHANGELOG)
            (skills_dir / "pkg-a" / "RESOLVER.md").write_text(
                "# original resolver\n", encoding="utf-8"
            )

            # pkg-b: GOOD SKILL.md initially.  Its SKILL.md will be rewritten to
            # a BAD version after the base commit → MUST be enforced and fail.
            good_skill_b = GOOD_SKILL.replace("name: demo", "name: pkg-b")
            self._make_skill(root, "pkg-b", good_skill_b, GOOD_CHANGELOG)

            # Commit the initial state.
            self._init_git_repo(root)
            base = self._git_head(root)

            # Working-tree changes:
            #   pkg-a → only RESOLVER.md changes (SKILL.md untouched)
            #   pkg-b → SKILL.md changed to a BAD version
            (skills_dir / "pkg-a" / "RESOLVER.md").write_text(
                "# updated resolver\n", encoding="utf-8"
            )
            bad_skill_b = good_skill_b.replace("allowed-tools: [Bash, Read, Edit]\n", "")
            (skills_dir / "pkg-b" / "SKILL.md").write_text(bad_skill_b, encoding="utf-8")

            result = self.run_validator(root, "--diff-base", base)

            # pkg-b's SKILL.md changed → enforced → BAD → exit 1
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("pkg-b", result.stdout)
            self.assertIn("NO_ALLOWED_TOOLS", result.stdout)

            # pkg-a's RESOLVER.md changed but SKILL.md did NOT → NOT enforced
            self.assertNotIn("pkg-a", result.stdout)


if __name__ == "__main__":
    unittest.main()
