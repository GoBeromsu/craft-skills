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
            json.dumps([{"case_id": f"behavior-{index}", "expected": f"behavior {index}"} for index in range(3)]),
            encoding="utf-8",
        )
        (evals / "triggers.json").write_text(
            json.dumps([{"case_id": f"trigger-{index}", "expected": "demo"} for index in range(16)]),
            encoding="utf-8",
        )
        subprocess.run(["git", "init"], cwd=self.root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.root, check=True)
        (self.root / "README.md").write_text("fixture\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=self.root, check=True, capture_output=True, text=True)
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
            "main",
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
        self.assertEqual(receipt["inputs"], {"baseline_ref": "main", "candidate_ref": "HEAD", "no_skill_ref": "without-demo"})
        self.assertEqual([runtime["runtime"] for runtime in receipt["runtimes"]], ["Claude Code", "Codex", "Hermes", "generic"])
        for runtime in receipt["runtimes"]:
            self.assertEqual(len(runtime["cases"]), 19)
            self.assertTrue(all(case["result"] == "pending" for case in runtime["cases"]))
            self.assertEqual(runtime["raw_result_hash"], _hash(runtime["cases"]))

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


if __name__ == "__main__":
    unittest.main()
