"""Profile and routing coverage tests for the governance harness."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_GOVERNANCE = _ROOT / "scripts" / "governance"
_FIXTURE = _GOVERNANCE / "fixtures" / "repos.portable.json"
sys.path.insert(0, str(_GOVERNANCE))

import harness
from checkers import provenance, routing_eval


class HarnessProfilesTest(unittest.TestCase):
    def test_portable_checker_set_excludes_adapter_parity(self) -> None:
        expected = [module for module in harness.CHECKER_MODULES if module != "checkers.adapter_parity"]
        self.assertEqual(harness.PROFILE_CHECKERS["portable"], expected)

    def test_cross_repo_checker_set_is_portable_plus_adapter_parity(self) -> None:
        portable = set(harness.PROFILE_CHECKERS["portable"])
        cross_repo = set(harness.PROFILE_CHECKERS["cross-repo"])
        self.assertEqual(cross_repo, portable | {"checkers.adapter_parity"})

    def test_casesets_match_profile_scope(self) -> None:
        portable = ["docs/governance/routing-eval-cases.yaml"]
        self.assertEqual(harness.PROFILE_CASESETS["portable"], portable)
        self.assertEqual(
            harness.PROFILE_CASESETS["cross-repo"],
            portable + ["docs/governance/routing-eval-cases.cross-repo.yaml"],
        )

    def test_portable_run_succeeds_and_lexical_verdicts_are_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            result = subprocess.run(
                [
                    sys.executable,
                    str(_GOVERNANCE / "harness.py"),
                    "--profile",
                    "portable",
                    "--config",
                    str(_FIXTURE),
                    "--json-out",
                    str(output / "report.json"),
                    "--text-out",
                    str(output / "report.txt"),
                ],
                capture_output=True,
                text=True,
                cwd=_ROOT,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))

        lexical_codes = {
            "routing_eval.expected_trigger_missing",
            "routing_eval.forbidden_neighbor_tie",
            "routing_eval.forbidden_neighbor_stronger",
        }
        lexical_findings = [finding for finding in report["findings"] if finding["code"] in lexical_codes]
        self.assertTrue(lexical_findings)
        self.assertTrue(all(finding["severity"] == "advisory" for finding in lexical_findings))

    def test_coverage_mismatch_blocks(self) -> None:
        builder = harness._load_build_aggregate()
        aggregate = builder.build(_FIXTURE, visibility="all")
        with tempfile.TemporaryDirectory() as directory:
            coverage_path = Path(directory) / "coverage.json"
            coverage_path.write_text(
                json.dumps({"schemaVersion": 1, "expected_craft_packages": ["wrong-name"]}),
                encoding="utf-8",
            )
            findings = routing_eval.run(
                aggregate,
                {
                    "repos": [{"name": "craft-skills", "path": str(_ROOT)}],
                    "profile": "portable",
                    "routing_eval_casesets": harness.PROFILE_CASESETS["portable"],
                    "routing_eval_coverage_path": str(coverage_path),
                },
            )
        mismatch = [finding for finding in findings if finding["code"] == "routing_eval.coverage_mismatch"]
        self.assertEqual(len(mismatch), 1)
        self.assertEqual(mismatch[0]["severity"], "blocking")

    def test_external_lineage_is_advisory_only_in_portable_profile(self) -> None:
        aggregate = {
            "packages": [
                {
                    "id": "craft-skills/example",
                    "owner_repo": "craft-skills",
                    "provenance": {"absorbed_from": ["bstack/example"]},
                }
            ]
        }
        repos = [{"name": "craft-skills", "path": str(_ROOT)}]
        portable = provenance.run(
            aggregate,
            {"repos": repos, "profile": "portable", "external_repos": ["bstack", "oh-my-secondbrain"]},
        )
        cross_repo = provenance.run(
            aggregate,
            {"repos": repos, "profile": "cross-repo", "external_repos": ["bstack", "oh-my-secondbrain"]},
        )
        self.assertEqual(portable[0]["severity"], "advisory")
        self.assertEqual(cross_repo[0]["severity"], "blocking")
    def test_unknown_provenance_namespace_blocks_in_portable_profile(self) -> None:
        aggregate = {
            "packages": [
                {
                    "id": "craft-skills/example",
                    "owner_repo": "craft-skills",
                    "provenance": {"absorbed_from": ["bstak/example"]},
                }
            ]
        }
        findings = provenance.run(
            aggregate,
            {
                "repos": [{"name": "craft-skills", "path": str(_ROOT)}],
                "profile": "portable",
                "external_repos": ["bstack", "oh-my-secondbrain"],
            },
        )
        self.assertEqual(findings[0]["severity"], "blocking")

    def test_active_missing_forbidden_neighbor_blocks_when_expected_score_is_zero(self) -> None:
        builder = harness._load_build_aggregate()
        aggregate = builder.build(_FIXTURE, visibility="all")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "cases.json"
            coverage = Path(directory) / "coverage.json"
            source.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "cases": [
                            {
                                "trigger": "unmatched-token",
                                "expected_package": "craft-skills/skillify",
                                "forbidden_neighbors": ["craft-skills/missing"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            coverage.write_text(
                json.dumps({"schemaVersion": 1, "expected_craft_packages": ["skillify"]}),
                encoding="utf-8",
            )
            findings = routing_eval.run(
                aggregate,
                {
                    "repos": [{"name": "craft-skills", "path": str(_ROOT)}],
                    "profile": "portable",
                    "routing_eval_casesets": [str(source)],
                    "routing_eval_coverage_path": str(coverage),
                },
            )
        missing = [finding for finding in findings if finding["code"] == "routing_eval.forbidden_neighbor_missing"]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["severity"], "blocking")

    def test_caseset_schema_version_and_duplicate_coverage_block(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = root / "cases.json"
            coverage = root / "coverage.json"
            cases.write_text(json.dumps({"cases": []}), encoding="utf-8")
            coverage.write_text(
                json.dumps({"schemaVersion": 1, "expected_craft_packages": ["skillify", "skillify"]}),
                encoding="utf-8",
            )
            config = {
                "repos": [{"name": "craft-skills", "path": str(_ROOT)}],
                "routing_eval_casesets": [str(cases)],
                "routing_eval_coverage_path": str(coverage),
            }
            schema_findings = routing_eval.run({"packages": []}, config)
            self.assertEqual(schema_findings[0]["code"], "routing_eval.cases_invalid_schema_version")
            cases.write_text(json.dumps({"schema_version": 1, "cases": []}), encoding="utf-8")
            coverage_findings = routing_eval.run({"packages": []}, config)
        self.assertIn("routing_eval.coverage_invalid", [finding["code"] for finding in coverage_findings])

    def test_cross_repo_missing_sibling_writes_blocking_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            config = output / "repos.json"
            config.write_text(
                json.dumps(
                    {
                        "repos": [
                            {"name": "craft-skills", "path": str(_ROOT)},
                            {"name": "bstack", "path": str(output / "missing-bstack")},
                        ],
                        "external_repos": ["bstack"],
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(_GOVERNANCE / "harness.py"),
                    "--profile",
                    "cross-repo",
                    "--config",
                    str(config),
                    "--json-out",
                    str(output / "report.json"),
                    "--text-out",
                    str(output / "report.txt"),
                ],
                capture_output=True,
                text=True,
                cwd=_ROOT,
            )
            report_path = output / "report.json"
            text_path = output / "report.txt"
            self.assertEqual(result.returncode, 1)
            self.assertTrue(report_path.is_file())
            self.assertTrue(text_path.is_file())
            self.assertIn("harness.unresolved_repo", text_path.read_text(encoding="utf-8"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["findings"][0]["code"], "harness.unresolved_repo")
        self.assertEqual(report["findings"][0]["severity"], "blocking")


if __name__ == "__main__":
    unittest.main()
