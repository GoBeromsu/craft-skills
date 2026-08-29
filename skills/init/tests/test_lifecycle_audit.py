"""Read-only and deterministic behavior tests for lifecycle audit."""
from __future__ import annotations

import contextlib
import hashlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lifecycle_audit
import lifecycle_core


def tree_digest(root: Path) -> dict[str, tuple[bytes, int]]:
    result: dict[str, tuple[bytes, int]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            result[path.relative_to(root).as_posix()] = (path.read_bytes(), path.stat().st_mode & 0o7777)
    return result


class LifecycleAuditTests(unittest.TestCase):
    def test_audit_is_byte_for_byte_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_bytes(b"print('x')\r\n")
            (root / "AGENTS.md").write_bytes(b"operator owned\n")
            os.chmod(root / "AGENTS.md", 0o640)
            before = tree_digest(root)
            first = lifecycle_core.audit(root)
            second = lifecycle_core.audit(root)
            self.assertEqual(first, second)
            self.assertEqual(tree_digest(root), before)
            self.assertEqual(first["mutations"], [])

    def test_findings_are_deterministic_and_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".agents-map.json").write_text("not json", encoding="utf-8")
            (root / ".agents-map.transaction.json").write_text("active", encoding="utf-8")
            (root / "z").mkdir()
            (root / "a").mkdir()
            os.symlink(root / "z", root / "link-z")
            report = lifecycle_core.audit(root)
            findings = report["findings"]
            self.assertEqual(findings, sorted(findings, key=lambda item: (item["code"], item.get("path", ""))))
            self.assertIn({"code": "INITV4-E-SNAPSHOT-INVALID", "path": ".agents-map.json"}, findings)
            self.assertIn({"code": "INITV4-E-TRANSACTION-ACTIVE", "path": ".agents-map.transaction.json"}, findings)
            self.assertIn({"code": "INITV4-E-SYMLINK", "path": "link-z"}, findings)

    def test_owned_hash_and_mode_drift_are_reported_without_repair(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "AGENTS.md"
            target.write_bytes(b"owned bytes\n")
            os.chmod(target, 0o600)
            discovered = lifecycle_core.discover_topology(root)
            topology = {key: discovered[key] for key in ("max_depth", "shim_policy", "loader", "nodes", "coverage", "root_fallback_payload_sha256")}
            snapshot = {
                "schema_version": 1,
                "repository_root": ".",
                "owned_artifacts": [{
                    "path": "AGENTS.md", "artifact_type": "agents-file", "managed_id": "root", "status": "active",
                    "payload_sha256": hashlib.sha256(b"payload").hexdigest(),
                    "file_sha256": hashlib.sha256(b"different").hexdigest(), "mode": 0o640,
                }],
                "last_applied_topology": topology,
            }
            (root / ".agents-map.json").write_bytes(lifecycle_core.canonical_json(snapshot, pretty=True))
            original = target.read_bytes()
            report = lifecycle_core.audit(root)
            codes = [item["code"] for item in report["findings"]]
            self.assertIn("INITV4-E-OWNED-DRIFT", codes)
            self.assertIn("INITV4-E-MODE-DRIFT", codes)
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(target.stat().st_mode & 0o7777, 0o600)

    def test_symlinked_snapshot_is_refused_as_unsafe_inspection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            external = root / "external.json"
            external.write_text("{}", encoding="utf-8")
            os.symlink(external, root / ".agents-map.json")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(lifecycle_audit.main([str(root)]), 2)
            self.assertIn("ownership snapshot is unsafe", stderr.getvalue())
            self.assertEqual(external.read_text(encoding="utf-8"), "{}")

    def test_cli_emits_compact_stable_json_and_exit_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            clean_out, clean_err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(clean_out), contextlib.redirect_stderr(clean_err):
                clean_status = lifecycle_audit.main([str(root)])
            self.assertEqual(clean_status, 0)
            self.assertEqual(clean_err.getvalue(), "")
            self.assertEqual(clean_out.getvalue(), lifecycle_audit.json.dumps(lifecycle_core.audit(root), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            (root / ".agents-map.transaction.json").write_text("active", encoding="utf-8")
            finding_out = io.StringIO()
            with contextlib.redirect_stdout(finding_out):
                finding_status = lifecycle_audit.main([str(root)])
            self.assertEqual(finding_status, 1)
            self.assertIn("INITV4-E-TRANSACTION-ACTIVE", finding_out.getvalue())


if __name__ == "__main__":
    unittest.main()
