"""Tests for the structural evaluation receipt CLI."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_TOOL = _ROOT / "scripts" / "governance" / "tools" / "run_evals.py"


def _hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class RunEvalsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        evals = self.root / "skills" / "demo" / "evals"
        evals.mkdir(parents=True)
        (evals / "evals.json").write_text(
            json.dumps(
                {
                    "skill": "demo",
                    "cases": [
                        {"prompt": f"behavior prompt {index}", "expected_behavior": f"behavior {index}"}
                        for index in range(3)
                    ],
                }
            ),
            encoding="utf-8",
        )
        (evals / "triggers.json").write_text(
            json.dumps(
                {
                    "should": [f"should trigger {index}" for index in range(8)],
                    "should_not": [f"near miss {index}" for index in range(8)],
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(["git", "init"], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.root, check=True)
        (self.root / "README.md").write_text("fixture\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "branch", "baseline"], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "branch", "without-demo"], cwd=self.root, check=True, capture_output=True, text=True)
        self.receipt_path = self.root / "receipt.json"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(_TOOL), *args],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )

    def _emit(self) -> dict[str, object]:
        result = self._run(
            "demo",
            "--emit",
            str(self.receipt_path),
            "--pr",
            "123",
            "--baseline-ref",
            "baseline",
            "--candidate-ref",
            "HEAD",
            "--no-skill-ref",
            "without-demo",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(self.receipt_path.read_text(encoding="utf-8"))

    def _complete(self, receipt: dict[str, object]) -> None:
        runtimes = receipt["runtimes"]
        self.assertIsInstance(runtimes, list)
        all_cases = []
        for runtime in runtimes:
            self.assertIsInstance(runtime, dict)
            cases = runtime["cases"]
            self.assertIsInstance(cases, list)
            for case in cases:
                self.assertIsInstance(case, dict)
                case["actual"] = case["expected"]
                case["result"] = "passed"
            runtime["raw_result_hash"] = _hash(cases)
            runtime["pass_rate"] = 1.0
            all_cases.extend(cases)
        receipt["pass_rate"] = sum(case["result"] == "passed" for case in all_cases) / len(all_cases)
        self.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    def test_emit_creates_pending_four_runtime_receipt(self) -> None:
        receipt = self._emit()
        self.assertEqual(receipt["protocol_version"], 1)
        self.assertEqual(receipt["skill"], "demo")
        self.assertEqual(receipt["pr"], "123")
        self.assertEqual(receipt["inputs"], {"baseline_ref": "baseline", "candidate_ref": "HEAD", "no_skill_ref": "without-demo"})
        self.assertEqual([runtime["runtime"] for runtime in receipt["runtimes"]], ["Claude Code", "Codex", "Hermes", "generic"])
        for runtime in receipt["runtimes"]:
            self.assertEqual(len(runtime["cases"]), 19)
            self.assertTrue(all(case["result"] == "pending" for case in runtime["cases"]))
            self.assertEqual(runtime["raw_result_hash"], _hash(runtime["cases"]))
        self.assertEqual(
            [case["case_id"] for case in receipt["runtimes"][0]["cases"]],
            [f"trigger-should-{index:02d}" for index in range(1, 9)]
            + [f"trigger-nomiss-{index:02d}" for index in range(1, 9)]
            + [f"behavior-{index:02d}" for index in range(1, 4)],
        )

    def test_validate_rejects_pending_and_accepts_completed_receipt(self) -> None:
        receipt = self._emit()
        pending = self._run("--validate", str(self.receipt_path))
        self.assertEqual(pending.returncode, 1)
        self.assertIn("non-passing", pending.stdout)
        self._complete(receipt)
        completed = self._run("--validate", str(self.receipt_path))
        self.assertEqual(completed.returncode, 0, completed.stdout)

    def test_validate_rejects_tampered_runtime_hash(self) -> None:
        receipt = self._emit()
        self._complete(receipt)
        receipt["runtimes"][0]["raw_result_hash"] = "bad"
        self.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        result = self._run("--validate", str(self.receipt_path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("raw_result_hash", result.stdout)
    def test_validate_rejects_mismatched_tree_protocol_and_missing_evals(self) -> None:
        receipt = self._emit()
        self._complete(receipt)

        receipt["tested_tree_sha"] = "bad"
        self.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        tree_result = self._run("--validate", str(self.receipt_path))
        self.assertEqual(tree_result.returncode, 1)
        self.assertIn("tested_tree_sha", tree_result.stdout)

        receipt = self._emit()
        self._complete(receipt)
        evals_path = self.root / "skills" / "demo" / "evals" / "evals.json"
        source = json.loads(evals_path.read_text(encoding="utf-8"))
        source["cases"][0]["expected_behavior"] = "changed"
        evals_path.write_text(json.dumps(source), encoding="utf-8")
        protocol_result = self._run("--validate", str(self.receipt_path))
        self.assertEqual(protocol_result.returncode, 1)
        self.assertIn("protocol_hash", protocol_result.stdout)

        evals_path.unlink()
        absent_result = self._run("--validate", str(self.receipt_path))
        self.assertEqual(absent_result.returncode, 1)
        self.assertIn("cannot read JSON input", absent_result.stdout)

    def test_validate_rejects_unresolvable_input_ref(self) -> None:
        receipt = self._emit()
        self._complete(receipt)
        receipt["inputs"]["baseline_ref"] = "missing-ref"
        self.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        result = self._run("--validate", str(self.receipt_path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("inputs.baseline_ref", result.stdout)
    def test_validate_accepts_explicit_tree(self) -> None:
        receipt = self._emit()
        self._complete(receipt)
        receipt["tested_tree_sha"] = "expected-tree"
        self.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        result = self._run("--validate", str(self.receipt_path), "--tree", "expected-tree")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_validate_diagnoses_malformed_cases_without_crashing(self) -> None:
        receipt = self._emit()
        self._complete(receipt)
        # Missing result field must fail validation, not raise KeyError.
        del receipt["runtimes"][0]["cases"][0]["result"]
        self.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        result = self._run("--validate", str(self.receipt_path))
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("invalid result", result.stdout)

    def test_validate_diagnoses_unhashable_ids_and_runtime_names(self) -> None:
        receipt = self._emit()
        self._complete(receipt)
        # Non-string case_id and runtime name must fail validation, not TypeError.
        receipt["runtimes"][0]["cases"][0]["case_id"] = ["not", "a", "string"]
        receipt["runtimes"][1]["runtime"] = {"name": "Codex"}
        self.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        result = self._run("--validate", str(self.receipt_path))
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("case_id", result.stdout)
        self.assertIn("required runtime", result.stdout)


if __name__ == "__main__":
    unittest.main()
