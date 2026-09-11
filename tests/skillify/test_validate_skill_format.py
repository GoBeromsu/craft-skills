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
        if not (root / ".git").exists():
            self._git(root, "init")
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

    def test_rejects_missing_contract_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            no_contract = GOOD_SKILL.replace("## Output contract\nA demo transcript in the working directory.\nMissing input stops the run with a message.\n\n", "")
            self._make_skill(root, "demo", no_contract, GOOD_CHANGELOG)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("MISSING_CONTRACT_SECTION", result.stdout)

    def test_contract_failure_wording_is_not_lexically_enforced(self) -> None:
        """The section is required; its cannot-succeed wording is judged, not scanned."""
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
            for filename in ("SKILL.md", "evals.json"):
                for flags in ((), ("--advisory",)):
                    with self.subTest(filename=filename, flags=flags):
                        result = subprocess.run(
                            [sys.executable, "-c", wrapper, filename, str(SCRIPT),
                             "--root", str(root), *flags],
                            cwd=root, text=True, capture_output=True, check=False,
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

    def test_supplied_small_corpus_is_checked_without_fixed_minimum(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evals = json.loads(GOOD_EVALS)
            evals["cases"] = evals["cases"][:1]
            triggers = {"should_trigger": ["demo this"], "should_not_trigger": []}
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG,
                             evals=json.dumps(evals), triggers=json.dumps(triggers))
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_malformed_eval_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_evals = json.dumps({"skill": "demo", "cases": [
                {"id": "a", "prompt": "p", "expected_behavior": "e", "grading": "verifiable"},
                {"id": "b", "prompt": "p", "expected_behavior": "e", "grading": "subjective", "assertions": ["x"]},
            ]})
            bad_triggers = json.dumps({"skill": "demo", "should_trigger": [42], "should_not_trigger": "not a list"})
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG, evals=bad_evals, triggers=bad_triggers)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            out = result.stdout
            self.assertIn("verifiable case a needs non-empty `assertions`", out)
            self.assertIn("subjective case b needs non-empty `rubric`", out)
            self.assertIn("`should_trigger` must be a list", out)
            self.assertIn("`should_not_trigger` must be a list", out)

    def test_duplicate_ids_and_scalar_assertions_are_malformed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evals = json.loads(GOOD_EVALS)
            evals["cases"][0]["assertions"] = "not a list"
            evals["cases"][1]["id"] = evals["cases"][0]["id"]
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG, evals=json.dumps(evals))
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("duplicate case id", result.stdout)
            self.assertIn("string list", result.stdout)

    def test_wrong_corpus_owner_and_unhashable_grading_are_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evals = json.loads(GOOD_EVALS)
            evals["skill"] = "other"
            evals["cases"][0]["grading"] = []
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG, evals=json.dumps(evals))
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("does not match its owner", result.stdout)
            self.assertIn("grading must be", result.stdout)
            self.assertNotIn("Traceback", result.stderr)

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
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)

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

    def test_corpus_only_change_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "demo", GOOD_SKILL, GOOD_CHANGELOG)
            self._init_git_repo(root)
            base = self._git_head(root)
            (root / "tests/demo/evals/evals.json").write_text("{broken")
            result = self.run_validator(root, "--diff-base", base)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("BAD_EVAL_CORPUS", result.stdout)

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
                            env={**os.environ, "PATH": str(empty_bin)},
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
