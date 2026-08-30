"""Contract tests for pure init lifecycle calculations."""
from __future__ import annotations

import os
import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lifecycle_core as core


class LifecycleCoreTests(unittest.TestCase):
    def test_canonical_serialization_and_stable_id_are_byte_stable(self) -> None:
        value = {"z": "e\u0301", "a": [True, None, 2]}
        self.assertEqual(core.canonical_json(value), '{"a":[true,null,2],"z":"e\u0301"}'.encode("utf-8"))
        self.assertEqual(core.canonical_json(value, pretty=True), '{\n  "a": [\n    true,\n    null,\n    2\n  ],\n  "z": "e\u0301"\n}\n'.encode("utf-8"))
        self.assertEqual(core.stable_id("P", value), core.stable_id("P", {"a": [True, None, 2], "z": "e\u0301"}))

    def test_paths_are_normalized_contained_and_reject_links(self) -> None:
        for unsafe in ("", ".", "../x", "a/../b", "/tmp/x", "a\\b", "a//b", "a/./b", "a\x00b"):
            with self.assertRaises(ValueError, msg=unsafe):
                core.normalize_path(unsafe)
        self.assertEqual(core.normalize_path("lib/AGENTS.md"), "lib/AGENTS.md")
        self.assertEqual(core.normalize_path(".", allow_root=True), ".")
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "root"
            root.mkdir()
            (root / "safe").mkdir()
            (root / "safe" / "file").write_bytes(b"ok")
            self.assertEqual(core.safe_path(root, "safe/file", require_exists=True), root / "safe" / "file")
            outside = parent / "outside"
            outside.mkdir()
            os.symlink(outside, root / "link")
            with self.assertRaises(ValueError):
                core.safe_path(root, "link/file")

    def test_managed_envelope_requires_exact_markers_and_payload_hash(self) -> None:
        payload = b"# scoped instructions\n"
        envelope = core.managed_envelope("api", payload)
        parsed = core.parse_managed_envelope(envelope)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["managed_id"], "api")
        self.assertEqual(parsed["payload"], "# scoped instructions\n")
        self.assertEqual(parsed["payload_sha256"], core.sha256_bytes(payload))
        self.assertIsNone(core.parse_managed_envelope(envelope.replace(b"scoped", b"changed")))
        self.assertIsNone(core.parse_managed_envelope(b"<!-- managed id=api -->\nx\n<!-- /managed id=api -->"))
        with self.assertRaises(ValueError):
            core.managed_envelope("two words", payload)

    def test_loading_classification_and_coverage_scoring(self) -> None:
        verified = {"status": "verified", "loading_class": "recursive"}
        self.assertEqual(core.loading_result(verified), verified)
        self.assertEqual(core.loading_result({"status": "verified", "loading_class": "invented"}), {"status": "unknown", "loading_class": "unknown"})
        self.assertEqual(core.loading_result({"status": "conflicted", "loading_class": "recursive"}), {"status": "conflicted", "loading_class": "unknown"})
        expected = ["AGENTS.md", "packages/AGENTS.md"]
        self.assertEqual(core.coverage_status(expected, expected, verified), {"status": "covered", "basis": "native"})
        self.assertEqual(core.coverage_status(expected, ["AGENTS.md"], verified), {"status": "gap", "basis": "native"})
        self.assertEqual(core.coverage_status(expected, ["packages/AGENTS.md", "AGENTS.md", "extra"], verified), {"status": "ambiguous", "basis": "native"})
        self.assertEqual(core.coverage_status(expected, None, {}, fallback_present=True), {"status": "unverified", "basis": "root-fallback"})

    def test_topology_is_sorted_and_reports_unsafe_entries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "z").mkdir()
            (root / "a").mkdir()
            (root / "a" / "work.py").write_text("x", encoding="utf-8")
            (root / "z" / "AGENTS.md").write_text("z", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "ignored").write_text("x", encoding="utf-8")
            os.symlink(root / "a" / "work.py", root / "linked")
            topology = core.discover_topology(root)
            self.assertEqual([item["path"] for item in topology["exclusions"]], ["node_modules"])
            self.assertEqual(topology["nodes"][0]["directory"], ".")
            self.assertEqual(topology["coverage"][0]["directory"], ".")
            self.assertIn({"code": "INITV4-E-SYMLINK", "path": "linked"}, topology["findings"])

    def test_managed_outputs_are_schema_exact_and_emit_root_product(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
            outputs = core.build_managed_outputs(core.discover_topology(root))
            self.assertEqual([effect["path"] for effect in outputs["effects"]], ["AGENTS.md"])
            self.assertTrue(outputs["effects"][0]["bytes"].startswith(b"<!-- init:managed id="))
            payload = core.parse_managed_envelope(outputs["effects"][0]["bytes"])
            self.assertIsNotNone(payload)
            payload_lines = payload["payload"].splitlines()
            self.assertGreaterEqual(len(payload_lines), 50)
            self.assertLessEqual(len(payload_lines), 150)
            self.assertIn("`main.py`", payload["payload"])
            topology = outputs["snapshot"]["last_applied_topology"]
            self.assertEqual(set(topology), {"max_depth", "shim_policy", "loader", "nodes", "coverage", "root_fallback_payload_sha256"})
            schema = json.loads((Path(__file__).resolve().parents[1] / "templates" / "snapshot.schema.json").read_text(encoding="utf-8"))
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            core.validate_snapshot(outputs["snapshot"])

    def test_scoring_records_all_factors_and_marks_unmeasured_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "package"
            package.mkdir()
            (package / "package.json").write_text("{}\n", encoding="utf-8")
            (package / "index.ts").write_text("export const x = 1\n", encoding="utf-8")
            for index in range(19):
                (package / f"file-{index}.ts").write_text("export {}\n", encoding="utf-8")
            node = next(item for item in core.discover_topology(root)["nodes"] if item["directory"] == "package")
            self.assertEqual(len(node["factors"]), 8)
            self.assertEqual(node["score"], 8)
            self.assertEqual([factor["measured"] for factor in node["factors"][-3:]], [False, False, False])

    def test_snapshot_validator_rejects_wrong_json_types_without_optional_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = core.build_managed_outputs(core.discover_topology(root))["snapshot"]
            cases = [
                {**snapshot, "schema_version": True},
                {**snapshot, "owned_artifacts": {}},
                {
                    **snapshot,
                    "last_applied_topology": {
                        **snapshot["last_applied_topology"],
                        "max_depth": "3",
                    },
                },
                {
                    **snapshot,
                    "last_applied_topology": {
                        **snapshot["last_applied_topology"],
                        "shim_policy": [],
                    },
                },
                {
                    **snapshot,
                    "last_applied_topology": {
                        **snapshot["last_applied_topology"],
                        "nodes": [{**snapshot["last_applied_topology"]["nodes"][0], "agents_path": 42}],
                    },
                },
            ]
            for candidate in cases:
                with self.subTest(candidate=candidate):
                    with self.assertRaises(ValueError):
                        core.validate_snapshot(candidate)

    def test_makefile_targets_are_rendered_as_declared_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Makefile").write_text(
                ".PHONY: test\nFLAGS:=one\nMORE::=two\nEXTRA:::=three\ntest: deps\n\tpython3 -m unittest\n",
                encoding="utf-8",
            )
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            outputs = core.build_managed_outputs(core.discover_topology(root))
            payload = core.parse_managed_envelope(outputs["effects"][0]["bytes"])
            self.assertIn("`make test` — declared Makefile target.", payload["payload"])
            self.assertNotIn("`make .PHONY`", payload["payload"])
            self.assertNotIn("`make FLAGS`", payload["payload"])
            self.assertNotIn("`make MORE`", payload["payload"])
            self.assertNotIn("`make EXTRA`", payload["payload"])

    def test_dense_eligible_child_is_summarized_within_physical_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = root / "package"
            child.mkdir()
            scripts = {f"task-{index}": f"echo {index}" for index in range(12)}
            (child / "package.json").write_text(json.dumps({"scripts": scripts}), encoding="utf-8")
            (child / "index.ts").write_text("export const entry = 1\n", encoding="utf-8")
            for index in range(21):
                (child / f"module-{index}.ts").write_text(f"export const value{index} = {index}\n", encoding="utf-8")
            for index in range(12):
                subdirectory = child / f"scope-{index}"
                subdirectory.mkdir()
                (subdirectory / "package.json").write_text("{}\n", encoding="utf-8")
                (subdirectory / "index.ts").write_text("export const entry = 1\n", encoding="utf-8")
                for file_index in range(21):
                    (subdirectory / f"file-{file_index}.ts").write_text("export {}\n", encoding="utf-8")
            outputs = core.build_managed_outputs(core.discover_topology(root))
            child_effect = next(effect for effect in outputs["effects"] if effect["path"] == "package/AGENTS.md")
            payload = core.parse_managed_envelope(child_effect["bytes"])
            self.assertGreaterEqual(len(payload["payload"].splitlines()), 30)
            self.assertLessEqual(len(payload["payload"].splitlines()), 80)
            self.assertIn("additional direct files are summarized", payload["payload"])
            self.assertIn("7 additional managed child scopes are summarized here.", payload["payload"])

    def test_file_observation_preserves_non_0644_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "AGENTS.md"
            path.write_bytes(b"content")
            os.chmod(path, 0o640)
            observed = core.file_observation(root, "AGENTS.md")
            self.assertEqual(observed["mode"], 0o640)
            self.assertEqual(observed["size"], 7)
            self.assertTrue(stat.S_ISREG(path.stat().st_mode))


if __name__ == "__main__":
    unittest.main()
