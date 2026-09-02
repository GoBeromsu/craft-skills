#!/usr/bin/env python3
"""Tests for skillify skill-format validator (v4 contract)."""
from __future__ import annotations

import json
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

## Output contract
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
        )

    def _make_skill(self, root: Path, name: str, skill_md: str, changelog: str | None,
                    evals: str | None = GOOD_EVALS, triggers: str | None = GOOD_TRIGGERS) -> Path:
        d = root / "skills" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(skill_md, encoding="utf-8")
        if changelog is not None:
            (d / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
        (d / "tests" / "evals").mkdir(parents=True)
        if evals is not None:
            (d / "tests" / "evals" / "evals.json").write_text(evals, encoding="utf-8")
        if triggers is not None:
            (d / "tests" / "evals" / "triggers.json").write_text(triggers, encoding="utf-8")
        return d

    def test_rejects_missing_contract_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            no_contract = GOOD_SKILL.replace("## Output contract\nA demo transcript in the working directory.\nMissing input stops the run with a message.\n\n", "")
            self._make_skill(root, "demo", no_contract, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("MISSING_CONTRACT_SECTION", result.stdout)

    def test_rejects_output_contract_without_failure_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            happy_only = GOOD_SKILL.replace("Missing input stops the run with a message.\n", "")
            self._make_skill(root, "demo", happy_only, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("CONTRACT_LACKS_FAILURE_BRANCH", result.stdout)

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
            self.assertIn("scripts/deploy.py", result.stdout)
            self.assertNotIn("references/schema.md", result.stdout)
            (d / "scripts").mkdir()
            (d / "scripts" / "deploy.py").write_text("", encoding="utf-8")
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_rejects_missing_eval_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG, evals=None)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("NO_EVAL_CORPUS", result.stdout)
            self.assertIn("evals.json", result.stdout)

    def test_rejects_malformed_eval_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_evals = json.dumps({"skill": "demo", "cases": [
                {"id": "a", "prompt": "p", "expected_behavior": "e", "grading": "verifiable"},
                {"id": "b", "prompt": "p", "expected_behavior": "e", "grading": "subjective", "assertions": ["x"]},
            ]})
            bad_triggers = json.dumps({"skill": "demo", "should_trigger": ["only one"], "should_not_trigger": []})
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG, evals=bad_evals, triggers=bad_triggers)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            out = result.stdout
            self.assertIn("has 2 cases < 3", out)
            self.assertIn("verifiable case a needs non-empty `assertions`", out)
            self.assertIn("subjective case b needs non-empty `rubric`", out)
            self.assertIn("`should_trigger` needs >= 8", out)
            self.assertIn("`should_not_trigger` needs >= 8", out)

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
    # parsed description routing-directive grammar
    # ------------------------------------------------------------------

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

    def test_description_without_directive_tokens_remains_compatible(self) -> None:
        result = self._description_result("Use this skill for ordinary requests.")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("DIRECTIVE_", result.stdout)
        self.assertNotIn("MUST_USE", result.stdout)

    def test_accepts_valid_directive_with_and_without_any(self) -> None:
        for description in (
            "MUST USE for deployment requests. Handle production deployments.",
            "MUST USE for ANY deployment request. Handle production deployments.",
        ):
            with self.subTest(description=description):
                result = self._description_result(description)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validates_decoded_double_quoted_description(self) -> None:
        valid = self._description_result(
            r'"\u004dUST USE for ANY deployment request. Handle production deployments."'
        )
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)

        hidden_any = self._description_result(
            r'"\u004dUST USE for deployment requests. Handle \u0041NY deployment."'
        )
        self.assertEqual(hidden_any.returncode, 1)
        self.assertIn("MISPLACED_DIRECTIVE_ANY", hidden_any.stdout)

    def test_rejects_noncanonical_double_quoted_yaml_escape(self) -> None:
        result = self._description_result(
            r'"\x4dUST USE for deployment requests. Handle production deployments."'
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("NO_DESCRIPTION", result.stdout)

    def test_accepts_lowercase_any_and_non_tokens(self) -> None:
        for description in (
            "MUST USE for any deployment request. Handle production deployments.",
            "MUST USE for ANYTHING and ANY_1. Handle production deployments.",
            "MUST USE for API and CI requests. Handle production deployments.",
        ):
            with self.subTest(description=description):
                result = self._description_result(description)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_accepts_sentence_case_must_use_without_any(self) -> None:
        for description in (
            "Must use this skill for deployment requests.",
            "must use this skill for deployment requests.",
        ):
            with self.subTest(description=description):
                result = self._description_result(description)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_leading_all_caps_directive_lookalikes(self) -> None:
        for description in (
            "MUST  USE this skill for deployment requests.",
            "MUST USE: this skill for deployment requests.",
            "MUST-USE this skill for deployment requests.",
            "MUST: USE this skill for deployment requests.",
            "MUST - USE this skill for deployment requests.",
            "MUST_USE this skill for deployment requests.",
            "MUST\tUSE this skill for deployment requests.",
            "MUST  USE ANY deployment skill.",
            "MUST USE: ANY deployment skill.",
            "MUST-USE ANY deployment skill.",
        ):
            with self.subTest(description=description):
                result = self._description_result(description)
                self.assertEqual(result.returncode, 1)
                self.assertIn("BAD_MUST_USE_LOOKALIKE", result.stdout)

    def test_sentence_case_must_use_still_rejects_standalone_any(self) -> None:
        for description in (
            "Must use ANY deployment skill.",
            "must use ANY deployment skill.",
        ):
            with self.subTest(description=description):
                result = self._description_result(description)
                self.assertEqual(result.returncode, 1)
                self.assertIn("MISPLACED_DIRECTIVE_ANY", result.stdout)

    def test_plain_scalar_comments_do_not_create_hidden_directives(self) -> None:
        result = self._description_result(
            "Use this skill for ordinary requests. # MUST USE for ANY deployment."
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("DIRECTIVE_", result.stdout)
        self.assertNotIn("MUST_USE", result.stdout)

    def test_rejects_multiline_description_scalar(self) -> None:
        result = self._description_result(
            ">-\n  MUST USE for ANY deployment request. Handle deployments."
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("NO_DESCRIPTION", result.stdout)

    def test_rejects_every_directive_grammar_branch(self) -> None:
        cases = (
            ("MUST USE first clause. Remainder. MUST USE second clause. Remainder.",
             "MULTIPLE_MUST_USE"),
            ("Use this skill. MUST USE for deployment requests. Handle deployments.",
             "MISPLACED_MUST_USE"),
            ("MUST USE clause without a delimiter", "BAD_MUST_USE_CLAUSE"),
            ("MUST USE    . Remainder.", "BAD_MUST_USE_CLAUSE"),
            ("MUST USE clause.    ", "BAD_MUST_USE_CLAUSE"),
            ("MUST USE  clause. Remainder.", "BAD_MUST_USE_CLAUSE"),
            ("MUST USE clause . Remainder.", "BAD_MUST_USE_CLAUSE"),
            ("MUST USE clause.  Remainder.", "BAD_MUST_USE_CLAUSE"),
            ("MUST USE for deployments. Handle ANY deployment.", "MISPLACED_DIRECTIVE_ANY"),
            ("Use this skill for ANY deployment.", "MISPLACED_DIRECTIVE_ANY"),
            ("MUST USE for ANY deployment and ANY rollback. Handle deployments.",
             "DIRECTIVE_ANY_LIMIT"),
        )
        for description, code in cases:
            with self.subTest(description=description):
                result = self._description_result(description)
                self.assertEqual(result.returncode, 1)
                self.assertIn(code, result.stdout)

    def test_directive_finding_precedence(self) -> None:
        cases = (
            # MULTIPLE_MUST_USE outranks every lower directive finding.
            ("Use MUST USE first clause. MUST USE second clause.", "MULTIPLE_MUST_USE"),
            ("MUST USE no delimiter ANY MUST USE second directive.", "MULTIPLE_MUST_USE"),
            ("MUST USE clause. ANY MUST USE second directive.", "MULTIPLE_MUST_USE"),
            ("MUST USE ANY and ANY. Remainder. MUST USE second directive.", "MULTIPLE_MUST_USE"),
            # MISPLACED_MUST_USE outranks BAD_MUST_USE_CLAUSE,
            # MISPLACED_DIRECTIVE_ANY, and DIRECTIVE_ANY_LIMIT.
            ("Use this. MUST USE no delimiter", "MISPLACED_MUST_USE"),
            ("Use ANY. MUST USE clause. Remainder.", "MISPLACED_MUST_USE"),
            ("Use this. MUST USE ANY and ANY. Remainder.", "MISPLACED_MUST_USE"),
            # BAD_MUST_USE_CLAUSE outranks the two ANY findings.
            ("MUST USE no delimiter ANY", "BAD_MUST_USE_CLAUSE"),
            ("MUST USE no delimiter ANY ANY", "BAD_MUST_USE_CLAUSE"),
            # MISPLACED_DIRECTIVE_ANY outranks DIRECTIVE_ANY_LIMIT.
            ("MUST USE ANY and ANY. Remainder ANY", "MISPLACED_DIRECTIVE_ANY"),
        )
        for description, code in cases:
            with self.subTest(description=description):
                result = self._description_result(description)
                self.assertEqual(result.returncode, 1)
                self.assertIn(code, result.stdout)
                for other_code in {
                    "MULTIPLE_MUST_USE",
                    "MISPLACED_MUST_USE",
                    "BAD_MUST_USE_CLAUSE",
                    "MISPLACED_DIRECTIVE_ANY",
                    "DIRECTIVE_ANY_LIMIT",
                } - {code}:
                    self.assertNotIn(other_code, result.stdout)

    def test_directive_violation_is_advisory_when_requested(self) -> None:
        result = self._description_result(
            "MUST USE for ANY deployment and ANY rollback. Handle deployments.",
            "--advisory",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("DIRECTIVE_ANY_LIMIT", result.stdout)

    def test_body_uppercase_any_does_not_affect_description(self) -> None:
        skill = GOOD_SKILL + "\nANY MUST USE appears only in the body.\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", skill, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("MISPLACED_DIRECTIVE_ANY", result.stdout)

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
