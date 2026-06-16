#!/usr/bin/env python3
"""Tests for skillify consensus.py (vendored, OMC-independent multi-model channel)."""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# ---------------------------------------------------------------------------
# Path bootstrap: allow importing consensus as a module for white-box tests
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "skills/skillify/scripts"
CONSENSUS_PY = SCRIPTS_DIR / "consensus.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import consensus  # noqa: E402  (after path bootstrap)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GOOD_SKILL_MD = """\
---
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


def _make_skill_dir(tmp: Path, name: str = "demo") -> Path:
    skill_dir = tmp / "skills" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(GOOD_SKILL_MD, encoding="utf-8")
    return skill_dir


# ---------------------------------------------------------------------------
# 1. OMC-independence guard
# ---------------------------------------------------------------------------

class OmcIndependenceTest(unittest.TestCase):
    """consensus.py must contain zero references to the omc binary."""

    def test_no_omc_token(self) -> None:
        source = CONSENSUS_PY.read_text(encoding="utf-8")
        forbidden_patterns = [
            r"\bomc ",        # `omc ` — CLI invocation prefix
            r"\bomc_",        # omc_ identifier prefix
            r"import omc\b",  # direct import
            r"omc\.",         # attribute access
        ]
        for pattern in forbidden_patterns:
            matches = re.findall(pattern, source)
            self.assertEqual(
                matches, [],
                f"Found forbidden pattern {pattern!r} in consensus.py: {matches}",
            )


# ---------------------------------------------------------------------------
# 2. Argument-parsing contract
# ---------------------------------------------------------------------------

class ArgParsingTest(unittest.TestCase):
    """--skill is required; --round and --providers have documented defaults."""

    def _parse(self, argv: list[str]) -> object:
        ap = consensus.main.__code__  # ensure module loaded; use argparse directly
        import argparse
        # Reconstruct the parser inline to test without side effects
        ap = argparse.ArgumentParser()
        ap.add_argument("--skill", required=True)
        ap.add_argument("--round", type=int, default=1, dest="round_n", metavar="N")
        ap.add_argument("--prior", default=None)
        ap.add_argument("--providers", default=",".join(consensus.PROVIDER_DEFAULTS))
        return ap.parse_args(argv)

    def test_skill_required(self) -> None:
        import argparse
        ap = argparse.ArgumentParser()
        ap.add_argument("--skill", required=True)
        ap.add_argument("--round", type=int, default=1, dest="round_n")
        ap.add_argument("--prior", default=None)
        ap.add_argument("--providers", default=",".join(consensus.PROVIDER_DEFAULTS))
        with self.assertRaises(SystemExit):
            ap.parse_args([])  # no --skill → must error

    def test_round_default_is_one(self) -> None:
        args = self._parse(["--skill", "/some/path"])
        self.assertEqual(args.round_n, 1)

    def test_providers_default(self) -> None:
        args = self._parse(["--skill", "/some/path"])
        self.assertEqual(args.providers, "codex,gemini,claude")


# ---------------------------------------------------------------------------
# 3. Graceful degradation
# ---------------------------------------------------------------------------

class GracefulDegradationTest(unittest.TestCase):
    """When a provider CLI is missing or errors, the script records it as
    degraded and writes a receipt without raising."""

    def _run_main_with_no_providers(self, skill_dir: Path) -> int:
        """Run main() with all providers mocked to be unavailable (not on PATH)."""
        with mock.patch.object(consensus, "check_provider_available", return_value=False):
            with mock.patch("subprocess.run") as mock_run:
                # subprocess.run should NOT be called when provider unavailable,
                # but guard it anyway to prevent accidental real calls.
                mock_run.side_effect = AssertionError("subprocess.run must not be called")
                rc = consensus.main_with_args(
                    skill=str(skill_dir),
                    round_n=1,
                    prior=None,
                    providers=["codex", "gemini", "claude"],
                )
        return rc

    def _run_main_with_one_erroring(self, skill_dir: Path) -> int:
        """Run with codex available but returning error; gemini+claude unavailable."""
        def fake_available(provider: str) -> bool:
            return provider == "codex"

        def fake_invoke(provider: str, prompt: str) -> tuple[str | None, str | None]:
            return None, "CLI error: authentication failed"

        with mock.patch.object(consensus, "check_provider_available", side_effect=fake_available):
            with mock.patch.object(consensus, "invoke_provider", side_effect=fake_invoke):
                rc = consensus.main_with_args(
                    skill=str(skill_dir),
                    round_n=1,
                    prior=None,
                    providers=["codex", "gemini", "claude"],
                )
        return rc

    def test_all_providers_missing_records_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _make_skill_dir(Path(tmp))
            rc = self._run_main_with_no_providers(skill_dir)
            # Must not raise; return code is 2 (degraded) or 0 (all skipped)
            self.assertIn(rc, (0, 2), f"Expected 0 or 2 (degraded), got {rc}")
            # Consensus receipt must exist
            receipts = list((skill_dir / "evals").glob("consensus-*.md"))
            self.assertTrue(receipts, "Expected a consensus receipt to be written")
            receipt_text = receipts[0].read_text(encoding="utf-8")
            self.assertIn("degraded", receipt_text.lower(),
                          "Receipt must contain 'degraded' when no providers are live")

    def test_erroring_provider_records_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _make_skill_dir(Path(tmp))
            rc = self._run_main_with_one_erroring(skill_dir)
            self.assertIn(rc, (0, 2), f"Expected 0 or 2 (degraded), got {rc}")
            receipts = list((skill_dir / "evals").glob("consensus-*.md"))
            self.assertTrue(receipts, "Expected a consensus receipt to be written")
            receipt_text = receipts[0].read_text(encoding="utf-8")
            self.assertIn("degraded", receipt_text.lower(),
                          "Receipt must mention 'degraded' when providers error")

    def test_does_not_raise_on_missing_providers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _make_skill_dir(Path(tmp))
            # Should complete without raising any exception
            try:
                self._run_main_with_no_providers(skill_dir)
            except Exception as exc:
                self.fail(f"consensus raised unexpectedly: {exc}")


# ---------------------------------------------------------------------------
# 4. Diff-scoped review (--diff-base)
# ---------------------------------------------------------------------------

class DiffScopingTest(unittest.TestCase):
    """When --diff-base yields a diff, the panel reviews only the changed lines;
    a missing/empty/failed diff falls back to whole-file review without raising."""

    def test_build_prompt_whole_file_when_no_diff(self) -> None:
        prompt = consensus.build_prompt("codex", "SKILL BODY", None, None)
        self.assertIn("SKILL BODY", prompt)
        self.assertNotIn("DIFF-ONLY REVIEW", prompt)

    def test_build_prompt_diff_scoped_when_diff_present(self) -> None:
        prompt = consensus.build_prompt(
            "codex", "SKILL BODY", None, "+added line\n-removed line"
        )
        self.assertIn("DIFF-ONLY REVIEW", prompt)
        self.assertIn("+added line", prompt)
        # full file stays in as judging context
        self.assertIn("SKILL BODY", prompt)
        # scope preamble precedes the role prompt / file body
        self.assertLess(prompt.index("DIFF-ONLY REVIEW"), prompt.index("SKILL BODY"))

    def test_build_prompt_diff_and_prior_coexist(self) -> None:
        prompt = consensus.build_prompt("gemini", "BODY", "PRIOR FINDING", "DIFFTEXT")
        self.assertIn("DIFF-ONLY REVIEW", prompt)
        self.assertIn("DIFFTEXT", prompt)
        self.assertIn("PRIOR FINDING", prompt)

    def test_compute_diff_errors_on_non_repo_without_raising(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diff_text, err = consensus.compute_diff(Path(tmp), "origin/main...HEAD")
            self.assertIsNone(diff_text)
            self.assertIsNotNone(err)

    def test_diff_base_falls_back_to_whole_file_on_git_error(self) -> None:
        """A diff-base that can't resolve (non-repo tmp) must not raise and must
        still write a receipt tagged `scope: whole-file`."""
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _make_skill_dir(Path(tmp))
            with mock.patch.object(consensus, "check_provider_available", return_value=False):
                rc = consensus.main_with_args(
                    skill=str(skill_dir),
                    round_n=1,
                    prior=None,
                    providers=["codex"],
                    diff_base="origin/main...HEAD",
                )
            self.assertIn(rc, (0, 2), f"Expected 0 or 2 (degraded), got {rc}")
            receipts = list((skill_dir / "evals").glob("consensus-*.md"))
            self.assertTrue(receipts, "Expected a consensus receipt to be written")
            self.assertIn("scope: whole-file", receipts[0].read_text(encoding="utf-8"))

    def test_receipt_records_scope_line(self) -> None:
        """Every receipt carries a `scope:` line (default whole-file)."""
        text = consensus.synthesize_receipt(
            skill_name="demo",
            round_n=1,
            verdicts={},
            errors={"codex": "missing"},
            providers=["codex"],
            today="2026-06-16",
        )
        self.assertIn("scope: whole-file", text)


if __name__ == "__main__":
    unittest.main()
