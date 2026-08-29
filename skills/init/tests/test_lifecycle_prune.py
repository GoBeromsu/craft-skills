"""Ownership-safe pruning tests."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lifecycle_core
import lifecycle_prune


def stale_row(path: str, data: bytes, mode: int = 0o640, artifact_type: str = "agents-file") -> dict:
    return {"path": path, "artifact_type": artifact_type, "managed_id": "owned-" + path, "status": "stale", "payload_sha256": hashlib.sha256(b"payload").hexdigest() if artifact_type != "claude-shim" else None, "file_sha256": hashlib.sha256(data).hexdigest(), "mode": mode}


def snapshot_for(root: Path, rows: list[dict]) -> dict:
    discovered = lifecycle_core.discover_topology(root)
    return {
        "schema_version": 1,
        "repository_root": ".",
        "owned_artifacts": rows,
        "last_applied_topology": {key: discovered[key] for key in ("max_depth", "shim_policy", "loader", "nodes", "coverage", "root_fallback_payload_sha256")},
    }


class LifecyclePruneTests(unittest.TestCase):
    def test_plan_only_emits_deletes_for_accepted_stale_owned_artifacts(self) -> None:
        snapshot = snapshot_for(Path.cwd(), [stale_row("z.md", b"z"), stale_row("a.md", b"a"), {**stale_row("live.md", b"live"), "status": "active"}])
        planned = lifecycle_core.plan_prune(Path("."), snapshot, set())
        self.assertEqual([proposal["path"] for proposal in planned["proposals"]], ["a.md", "z.md"])
        self.assertEqual(planned["effects"], [])
        accepted = lifecycle_core.plan_prune(Path("."), snapshot, {planned["proposals"][0]["id"]})
        self.assertEqual(accepted["effects"], [{"action": "delete", "path": "a.md", "proposal_id": planned["proposals"][0]["id"]}])
        self.assertNotIn("a.md", [row["path"] for row in accepted["snapshot"]["owned_artifacts"]])

    def test_drifted_or_missing_ownership_fails_closed_and_preserves_unowned_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owned = root / "owned.md"
            unowned = root / "unowned.md"
            owned.write_bytes(b"edited after mapping")
            unowned.write_bytes(b"do not touch\x00")
            os.chmod(owned, 0o640)
            snapshot = snapshot_for(root, [stale_row("owned.md", b"original")])
            (root / ".agents-map.json").write_text(json.dumps(snapshot), encoding="utf-8")
            before = {path.name: path.read_bytes() for path in (owned, unowned)}
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = lifecycle_prune.main([str(root), "--accept", "anything"])
            self.assertEqual(status, 2)
            self.assertEqual({path.name: path.read_bytes() for path in (owned, unowned)}, before)
            self.assertIn("prune-blocked", stderr.getvalue())

    def test_snapshot_symlink_is_rejected_before_it_can_authorize_delete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            external = root / "snapshot-source.json"
            external.write_text('{"owned_artifacts": []}', encoding="utf-8")
            os.symlink(external, root / ".agents-map.json")
            with self.assertRaises(ValueError):
                lifecycle_prune._snapshot(root)

    def test_validated_prune_never_includes_unowned_files_in_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owned = root / "owned.md"
            unowned = root / "unowned.md"
            owned.write_bytes(b"owned")
            unowned.write_bytes(b"operator content")
            os.chmod(owned, 0o640)
            snapshot = snapshot_for(root, [stale_row("owned.md", b"owned")])
            (root / ".agents-map.json").write_text(json.dumps(snapshot), encoding="utf-8")
            proposal = lifecycle_core.plan_prune(root, snapshot, set())["proposals"][0]
            captured: dict[str, object] = {}

            def apply(_root: Path, effects: list[dict], accepted: set[str], *, snapshot_payload: dict, operation: str) -> dict:
                captured.update(effects=effects, accepted=accepted, snapshot=snapshot_payload, operation=operation)
                return {"exit_code": 0, "phase": "complete", "effects": effects}

            with mock.patch.object(lifecycle_prune, "apply", side_effect=apply), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(lifecycle_prune.main([str(root), "--accept", proposal["id"]]), 0)
            self.assertEqual(captured["effects"], [{"action": "delete", "path": "owned.md", "proposal_id": proposal["id"]}])
            self.assertEqual(captured["operation"], "prune")
            self.assertEqual(captured["snapshot"]["owned_artifacts"], [])
            self.assertEqual(unowned.read_bytes(), b"operator content")

    def test_structurally_incomplete_snapshot_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".agents-map.json").write_text('{"owned_artifacts": []}', encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(lifecycle_prune.main([str(root), "--accept", "anything"]), 2)

    def test_accepted_prune_deletes_product_and_commits_row_removal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            owned = root / "stale.md"
            owned.write_bytes(b"stale managed bytes")
            os.chmod(owned, 0o640)
            snapshot = snapshot_for(root, [stale_row("stale.md", owned.read_bytes())])
            (root / ".agents-map.json").write_bytes(lifecycle_core.canonical_json(snapshot, pretty=True))
            proposal = lifecycle_core.plan_prune(root, snapshot, set())["proposals"][0]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(lifecycle_prune.main([str(root), "--accept", proposal["id"]]), 0)
            self.assertFalse(owned.exists())
            committed = json.loads((root / ".agents-map.json").read_text(encoding="utf-8"))
            self.assertEqual(committed["owned_artifacts"], [])
            self.assertFalse((root / ".agents-map.transaction.json").exists())


if __name__ == "__main__":
    unittest.main()
