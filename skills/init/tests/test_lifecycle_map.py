"""Instruction-contract tests for the map adapter."""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
import re
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lifecycle_map
import lifecycle_core


class LifecycleMapTests(unittest.TestCase):
    def test_bare_invocation_is_map_with_document_scaffolding_out_of_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seen: dict[str, object] = {}

            def outputs(actual_root: Path, max_depth: int, shim: str) -> dict:
                seen.update(root=actual_root, max_depth=max_depth, shim=shim)
                return lifecycle_core.build_managed_outputs(lifecycle_core.discover_topology(actual_root, max_depth=max_depth))

            def apply(actual_root: Path, effects: list[dict], accepted: set[str], *, snapshot_payload: dict) -> dict:
                seen.update(effects=effects, accepted=accepted, snapshot=snapshot_payload)
                return {"exit_code": 0, "phase": "complete", "effects": []}

            output = io.StringIO()
            with mock.patch.object(lifecycle_map, "_root", return_value=root), mock.patch.object(lifecycle_map, "_outputs", side_effect=outputs), mock.patch.object(lifecycle_map, "apply", side_effect=apply), contextlib.redirect_stdout(output):
                self.assertEqual(lifecycle_map.main([]), 0)
            self.assertEqual(seen["root"], root)
            self.assertEqual(seen["max_depth"], 3)
            self.assertEqual(seen["shim"], "keep")
            self.assertEqual([effect["path"] for effect in seen["effects"]], ["AGENTS.md"])
            self.assertEqual(seen["accepted"], set())
            self.assertIn('"operation":"map"', output.getvalue())

    def test_keep_resolves_to_safe_off_without_snapshot_and_prior_policy_when_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            captured: list[tuple[int, str]] = []
            real_discover = lifecycle_core.discover_topology
            def discover(actual_root: Path, *, max_depth: int, shim_policy: str) -> dict:
                captured.append((max_depth, shim_policy))
                return real_discover(actual_root, max_depth=max_depth, shim_policy=shim_policy)
            with mock.patch.object(lifecycle_map, "discover_topology", side_effect=discover):
                lifecycle_map._outputs(root, 4, "keep")
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(lifecycle_map.main([str(root), "--max-depth=5", "--claude-shim=on"]), 0)
                lifecycle_map._outputs(root, 5, "keep")
            self.assertEqual(captured, [(4, "off"), (5, "on"), (5, "on")])

    def test_idempotent_plan_reuses_the_same_effects_and_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls: list[tuple[list[dict], set[str]]] = []
            original_apply = lifecycle_map.apply

            def apply(actual_root: Path, effects: list[dict], accepted: set[str], *, snapshot_payload: dict) -> dict:
                calls.append((effects, accepted))
                return original_apply(actual_root, effects, accepted, snapshot_payload=snapshot_payload)

            with mock.patch.object(lifecycle_map, "apply", side_effect=apply), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(lifecycle_map.main([str(root)]), 0)
            first_agents = (root / "AGENTS.md").read_bytes()
            self.assertRegex(first_agents.decode("utf-8").splitlines()[0], r"^<!-- init:managed id=\S+ sha256=[0-9a-f]{64} -->$")
            first_snapshot = (root / ".agents-map.json").read_bytes()
            with mock.patch.object(lifecycle_map, "apply", side_effect=apply), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(lifecycle_map.main([str(root)]), 0)
            self.assertEqual((root / ".agents-map.json").read_bytes(), first_snapshot)
            self.assertEqual((root / "AGENTS.md").read_bytes(), first_agents)
            self.assertFalse((root / ".agents-map.transaction.json").exists())
            self.assertFalse((root / "docs").exists(), "map must not scaffold document-owned docs")
            self.assertEqual(len(calls), 1, "byte-identical rerun must not enter the transaction layer")

    def test_only_accepted_proposals_reach_transaction_apply(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            captured: dict[str, object] = {}
            plan = {
                "effects": [{"action": "write", "path": "AGENTS.md", "content": "x", "proposal_id": "P-consolidate"}],
                "proposals": [{"id": "P-consolidate"}],
                "snapshot": {},
            }

            def apply(_root: Path, effects: list[dict], accepted: set[str], *, snapshot_payload: dict) -> dict:
                captured.update(effects=effects, accepted=accepted)
                return {"exit_code": 0, "phase": "complete", "effects": []}

            valid_snapshot = lifecycle_core.build_managed_outputs(lifecycle_core.discover_topology(root))["snapshot"]
            plan["snapshot"] = valid_snapshot
            with mock.patch.object(lifecycle_map, "_outputs", return_value=plan), mock.patch.object(lifecycle_map, "apply", side_effect=apply), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(lifecycle_map.main([str(root)]), 2)
            self.assertEqual(captured, {})
            with mock.patch.object(lifecycle_map, "_outputs", return_value=plan), mock.patch.object(lifecycle_map, "apply", side_effect=apply), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(lifecycle_map.main([str(root), "--accept=P-consolidate"]), 0)
            self.assertEqual(captured["accepted"], {"P-consolidate"})
            self.assertEqual(captured["effects"][0]["proposal_id"], "P-consolidate")

    def test_unsafe_topology_blocks_before_any_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.write_text("external\n", encoding="utf-8")
            os.symlink(outside, root / "unsafe-link")
            before = sorted((path.relative_to(root).as_posix(), path.is_symlink(), path.read_bytes() if path.is_file() and not path.is_symlink() else b"") for path in root.iterdir())
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(lifecycle_map.main([str(root)]), 2)
            after = sorted((path.relative_to(root).as_posix(), path.is_symlink(), path.read_bytes() if path.is_file() and not path.is_symlink() else b"") for path in root.iterdir())
            self.assertEqual(after, before)
            self.assertFalse((root / ".agents-map.json").exists())

    def test_substantive_claude_is_preserved_in_agents_before_exact_shim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            incumbent = "# Claude-only rule\n\nRun `python3 -m unittest` before delivery.\n"
            (root / "CLAUDE.md").write_text(incumbent, encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(lifecycle_map.main([str(root), "--claude-shim=on"]), 2)
            proposal = re.search(r"P-MERGE-CLAUDE-AND-REPLACE-SHIM-[0-9a-f]{12}", stderr.getvalue())
            self.assertIsNotNone(proposal)
            self.assertFalse((root / "AGENTS.md").exists())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    lifecycle_map.main([str(root), "--claude-shim=on", f"--accept={proposal.group()}"]),
                    0,
                )
            self.assertEqual((root / "CLAUDE.md").read_bytes(), b"@AGENTS.md\n")
            self.assertIn(incumbent.rstrip(), (root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_bound_loading_receipt_reaches_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture_sha = lifecycle_core.probe_loading(root)["fixture_sha256"]
            observations = {
                "root": ["ROOT"],
                "child": ["ROOT", "CHILD"],
                "sibling": ["ROOT", "SIBLING"],
                "precedence": {"child": "CHILD", "sibling": "SIBLING"},
            }
            receipt = {
                "source_id": "test-runtime",
                "runtime_version": "1.0.0",
                "source_probe_result": {"status": "available", "source_id": "test-runtime"},
                "version_probe_result": {"status": "available", "runtime_version": "1.0.0"},
                "execution_status": "applicable",
                "fixture_sha256": fixture_sha,
                "raw_result_sha256": lifecycle_core.sha256_bytes(lifecycle_core.canonical_json(observations)),
                "observations": observations,
            }
            evidence_path = root / "loading-receipt.json"
            evidence_path.write_text(json.dumps(lifecycle_core.probe_loading(root, receipt)), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(lifecycle_map.main([str(root), f"--loading-evidence={evidence_path}"]), 0)
            snapshot = json.loads((root / ".agents-map.json").read_text(encoding="utf-8"))
            loader = snapshot["last_applied_topology"]["loader"]
            self.assertEqual(loader["loader_class"], "ancestor-only")
            self.assertEqual(loader["evidence_status"], "probe-verified")

    def test_claude_acceptance_is_invalidated_by_coupled_agents_mode_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(lifecycle_map.main([str(root)]), 0)
            (root / "CLAUDE.md").write_text("# preserve me\n", encoding="utf-8")
            first = lifecycle_map._outputs(root, 3, "on")
            proposal_id = next(
                proposal["id"]
                for proposal in first["proposals"]
                if proposal["action"] == "merge-claude-and-replace-shim"
            )
            os.chmod(root / "AGENTS.md", 0o600)
            before_agents = (root / "AGENTS.md").read_bytes()
            before_claude = (root / "CLAUDE.md").read_bytes()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    lifecycle_map.main([str(root), "--claude-shim=on", f"--accept={proposal_id}"]),
                    2,
                )
            self.assertEqual((root / "AGENTS.md").read_bytes(), before_agents)
            self.assertEqual((root / "CLAUDE.md").read_bytes(), before_claude)

    def test_dangling_journal_symlink_blocks_before_noop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            os.symlink(root / "missing-journal-target", root / ".agents-map.transaction.json")
            before = sorted(path.name for path in root.iterdir())
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(lifecycle_map.main([str(root)]), 2)
            self.assertEqual(sorted(path.name for path in root.iterdir()), before)
            self.assertFalse((root / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()
