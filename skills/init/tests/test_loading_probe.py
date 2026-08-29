"""Contract tests for the effect-free loading probe adapter and classifier."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
SCRIPTS = PACKAGE / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lifecycle_core  # noqa: E402
import loading_probe  # noqa: E402


class LoadingProbeTests(unittest.TestCase):
    def test_verified_classifications_are_preserved(self) -> None:
        for loading_class in ("file-scoped", "recursive", "ancestor-only"):
            with self.subTest(loading_class=loading_class):
                self.assertEqual(
                    lifecycle_core.loading_result({"status": "verified", "loading_class": loading_class}),
                    {"status": "verified", "loading_class": loading_class},
                )

    def test_unavailable_and_contradictory_evidence_never_classify(self) -> None:
        for evidence in (
            {"status": "unavailable", "loading_class": "recursive"},
            {"status": "conflicted", "loading_class": "ancestor-only"},
            {"status": "verified", "loading_class": "contradictory"},
        ):
            with self.subTest(evidence=evidence):
                self.assertEqual(
                    lifecycle_core.loading_result(evidence),
                    {"status": evidence["status"] if evidence["status"] in {"unavailable", "conflicted"} else "unknown", "loading_class": "unknown"},
                )

    def test_probe_report_is_deterministic_and_explicitly_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = lifecycle_core.probe_loading(root)
            second = lifecycle_core.probe_loading(root)

        self.assertEqual(first, second)
        self.assertEqual(first["root"], ".")
        self.assertEqual(first["status"], "unknown")
        self.assertEqual(first["loading_class"], "unknown")
        self.assertEqual(first["reason"], "no applicable sentinel observations")
        self.assertEqual(first["fixture"]["child"], {"path": "child/AGENTS.md", "marker": "CHILD"})
        self.assertEqual(len(first["fixture_sha256"]), 64)
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            json.dumps(second, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )

    def _receipt(self, root: Path, observations: dict | None = None) -> dict:
        fixture_sha256 = lifecycle_core.probe_loading(root)["fixture_sha256"]
        observations = observations or {
            "root": ["ROOT"],
            "child": ["ROOT", "CHILD"],
            "sibling": ["ROOT", "SIBLING"],
            "precedence": {"child": "CHILD", "sibling": "SIBLING"},
        }
        return {
            "source_id": "codex",
            "runtime_version": "1.2.3",
            "source_probe_result": {"source_id": "codex", "status": "available"},
            "version_probe_result": {"runtime_version": "1.2.3", "status": "available"},
            "fixture_sha256": fixture_sha256,
            "raw_result_sha256": lifecycle_core.sha256_bytes(lifecycle_core.canonical_json(observations)),
            "execution_status": "applicable",
            "observations": observations,
        }

    def test_marker_arrays_without_a_bound_receipt_are_unknown(self) -> None:
        observations = {"root": ["ROOT"], "child": ["ROOT", "CHILD"], "sibling": ["ROOT", "SIBLING"]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = lifecycle_core.probe_loading(root, observations)
        self.assertEqual({"status": result["status"], "loading_class": result["loading_class"]}, {"status": "unknown", "loading_class": "unknown"})

    def test_bound_receipt_classifies_exact_complete_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = lifecycle_core.probe_loading(root, self._receipt(root))
        self.assertEqual({"status": result["status"], "loading_class": result["loading_class"]}, {"status": "verified", "loading_class": "ancestor-only"})

    def test_wrong_fixture_or_raw_result_hash_remains_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for field in ("fixture_sha256", "raw_result_sha256"):
                with self.subTest(field=field):
                    receipt = self._receipt(root)
                    receipt[field] = "0" * 64
                    result = lifecycle_core.probe_loading(root, receipt)
                    self.assertEqual(result["status"], "unknown")
                    self.assertEqual(result["loading_class"], "unknown")

    def test_missing_source_or_version_remains_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for field in ("source_id", "runtime_version"):
                with self.subTest(field=field):
                    receipt = self._receipt(root)
                    del receipt[field]
                    result = lifecycle_core.probe_loading(root, receipt)
                    self.assertEqual(result["status"], "unknown")
                    self.assertEqual(result["loading_class"], "unknown")

    def test_contradictory_precedence_never_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = self._receipt(root)
            receipt["observations"]["precedence"]["child"] = "ROOT"
            receipt["raw_result_sha256"] = lifecycle_core.sha256_bytes(lifecycle_core.canonical_json(receipt["observations"]))
            result = lifecycle_core.probe_loading(root, receipt)
        self.assertEqual({"status": result["status"], "loading_class": result["loading_class"]}, {"status": "unknown", "loading_class": "unknown"})

    def test_adapter_reports_unavailable_root_as_structured_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = loading_probe.main([str(missing)])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        diagnostic = json.loads(stderr.getvalue())
        self.assertEqual(diagnostic["diagnostics"][0]["code"], "loading-probe-unavailable")
        self.assertIn("No such file", diagnostic["diagnostics"][0]["message"])


if __name__ == "__main__":
    unittest.main()
