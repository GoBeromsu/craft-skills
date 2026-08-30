"""Crash-boundary and byte-contract tests for private lifecycle transactions."""
from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import unittest
import re
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import _transaction as transaction
import lifecycle_core as core


class TransactionTests(unittest.TestCase):
    def _snapshot(self) -> dict:
        return {"schema_version": 1, "repository_root": ".", "owned_artifacts": [], "last_applied_topology": {"max_depth": 3, "shim_policy": "off", "coverage_units": [], "exclusions": []}}

    def test_golden_identity_serialization_and_derived_paths(self) -> None:
        golden = json.loads((Path(__file__).with_name("transaction-golden.json")).read_text(encoding="utf-8"))
        basis = golden["basis"]
        self.assertEqual(core.canonical_json(basis), golden["identity_bytes_utf8"].encode("utf-8"))
        identifier = core.transaction_id(basis)
        self.assertEqual(identifier, golden["transaction_id"])
        self.assertEqual(identifier[:12], golden["prefix"])
        snapshot_names = core.derived_transaction_paths(identifier, ".agents-map.json")
        self.assertEqual(snapshot_names["next_path"], golden["derived_paths"]["journal_next_path"])
        for key in ("apply_path", "pre_recovery_path", "post_recovery_path"):
            self.assertEqual(snapshot_names[key], golden["derived_paths"]["snapshot"][key])

    def test_apply_preserves_non_0644_destination_modes_and_cleans_last(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            product = root / "AGENTS.md"
            product.write_bytes(b"before")
            os.chmod(product, 0o640)
            result = transaction.apply(root, [{"path": "AGENTS.md", "bytes": b"after", "mode": 0o640}], set(), snapshot_payload=self._snapshot())
            self.assertEqual(result["phase"], "complete")
            self.assertEqual(product.read_bytes(), b"after")
            self.assertEqual(stat.S_IMODE(product.stat().st_mode), 0o640)
            self.assertEqual(stat.S_IMODE((root / ".agents-map.json").stat().st_mode), 0o644)
            self.assertFalse((root / core.JOURNAL_NAME).exists())
            self.assertEqual([path.name for path in root.iterdir() if ".craft-init-v4-" in path.name], [])

    def test_apply_temp_uses_selected_destination_mode_not_recovery_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = b"post image"
            identifier = "a" * 64
            names = core.derived_transaction_paths(identifier, "nested/AGENTS.md")
            (root / "nested").mkdir()
            entry = {"path": "nested/AGENTS.md", "post_exists": True, "post_sha256": core.sha256_bytes(data), "post_mode": 0o640, "pre_exists": False, "pre_sha256": None, "pre_mode": None, **{key: names[key] for key in ("apply_path", "post_recovery_path")}}
            transaction._image_copy(root, names["post_recovery_path"], data)
            apply_path = transaction._prepare_apply(root, entry, "forward")
            assert apply_path is not None
            self.assertEqual(apply_path.read_bytes(), data)
            self.assertEqual(stat.S_IMODE(apply_path.stat().st_mode), 0o640)
            self.assertNotEqual(stat.S_IMODE(apply_path.stat().st_mode), 0o600)

    def test_snapshot_is_consumed_after_products_and_journal_is_removed_last(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seen: list[tuple[str, bool]] = []
            original = transaction._consume_apply

            def consume(actual_root: Path, entry: dict, direction: str) -> None:
                seen.append((entry["path"], (actual_root / core.JOURNAL_NAME).exists()))
                original(actual_root, entry, direction)

            with mock.patch.object(transaction, "_consume_apply", side_effect=consume):
                transaction.apply(root, [{"path": "AGENTS.md", "bytes": b"product"}], set(), snapshot_payload=self._snapshot())
            self.assertEqual([path for path, _ in seen], ["AGENTS.md", ".agents-map.json"])
            self.assertTrue(all(journal_present for _, journal_present in seen))
            self.assertFalse((root / core.JOURNAL_NAME).exists())

    def test_product_rename_crash_recovers_by_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            product = root / "AGENTS.md"
            product.write_bytes(b"before")
            os.chmod(product, 0o640)
            original_replace = os.replace

            def fail_product(source: os.PathLike[str], destination: os.PathLike[str], **kwargs: object) -> None:
                if Path(destination).name == product.name:
                    raise OSError("simulated product rename crash")
                original_replace(source, destination, **kwargs)

            with mock.patch.object(transaction.os, "replace", side_effect=fail_product):
                with self.assertRaises(OSError):
                    transaction.apply(root, [{"path": "AGENTS.md", "bytes": b"after", "mode": 0o640}], set(), snapshot_payload=self._snapshot())
            self.assertTrue((root / core.JOURNAL_NAME).exists())
            with self.assertRaises(transaction.RecoveryBlocked):
                transaction.recover(root, {"P-STALE-RECOVERY-000000000000"})
            self.assertEqual(product.read_bytes(), b"before")
            recovered = transaction.recover(root)
            self.assertEqual(recovered["phase"], "rolled-back")
            self.assertEqual(product.read_bytes(), b"before")
            self.assertEqual(stat.S_IMODE(product.stat().st_mode), 0o640)
            self.assertFalse((root / core.JOURNAL_NAME).exists())

    def test_snapshot_rename_crash_rolls_back_products_on_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            product = root / "AGENTS.md"
            product.write_bytes(b"before")
            original_replace = os.replace

            def fail_snapshot(source: os.PathLike[str], destination: os.PathLike[str], **kwargs: object) -> None:
                if Path(destination).name == ".agents-map.json":
                    raise OSError("simulated snapshot rename crash")
                original_replace(source, destination, **kwargs)

            with mock.patch.object(transaction.os, "replace", side_effect=fail_snapshot):
                with self.assertRaises(OSError):
                    transaction.apply(root, [{"path": "AGENTS.md", "bytes": b"after"}], set(), snapshot_payload=self._snapshot())
            self.assertEqual(product.read_bytes(), b"after")
            self.assertEqual(transaction.recover(root)["phase"], "rolled-back")
            self.assertEqual(product.read_bytes(), b"before")

    def test_symlink_and_special_file_targets_are_rejected_before_journal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.write_bytes(b"do not alter")
            os.symlink(outside, root / "AGENTS.md")
            with self.assertRaises(ValueError):
                transaction.apply(root, [{"path": "AGENTS.md", "bytes": b"new"}], set(), snapshot_payload=self._snapshot())
            self.assertEqual(outside.read_bytes(), b"do not alter")
            self.assertFalse((root / core.JOURNAL_NAME).exists())
        if not hasattr(os, "mkfifo"):
            self.skipTest("mkfifo is unavailable on this platform")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            os.mkfifo(root / "AGENTS.md")
            with self.assertRaises(ValueError):
                transaction.apply(root, [{"path": "AGENTS.md", "bytes": b"new"}], set(), snapshot_payload=self._snapshot())
            self.assertFalse((root / core.JOURNAL_NAME).exists())

    def test_exclusive_write_retries_posix_short_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "artifact"
            original_write = os.write
            calls: list[bytes] = []

            def short_write(descriptor: int, data: bytes) -> int:
                calls.append(data)
                return original_write(descriptor, data[:2])

            with mock.patch.object(transaction.os, "write", side_effect=short_write):
                transaction._exclusive_write_relative(root, "artifact", b"abcdef", 0o640)
            self.assertEqual(path.read_bytes(), b"abcdef")
            self.assertGreater(len(calls), 1)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)

    def test_exclusive_write_rejects_zero_progress_and_keeps_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "artifact"
            with mock.patch.object(transaction.os, "write", return_value=0):
                with self.assertRaisesRegex(OSError, "no progress"):
                    transaction._exclusive_write_relative(root, "artifact", b"abcdef", 0o600)
            self.assertTrue(path.exists())
            self.assertEqual(path.read_bytes(), b"")

    def test_recovery_rejects_malicious_derived_artifact_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            transaction.apply(root, [{"path": "AGENTS.md", "bytes": b"product"}], set())
            journal_path = root / core.JOURNAL_NAME
            journal = json.loads(journal_path.read_text(encoding="utf-8"))
            journal["targets"][0]["apply_path"] = "outside.apply"
            journal_path.write_text(json.dumps(journal), encoding="utf-8")
            os.chmod(journal_path, 0o600)
            with self.assertRaises(RuntimeError) as caught:
                transaction.recover(root)
            self.assertIsInstance(caught.exception.__cause__, ValueError)
            self.assertTrue(journal_path.exists())

    def test_all_forward_apply_temps_exist_before_prepared_phase(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            observed: list[dict] = []
            original = transaction._journal_write

            def inspect_before_prepared(actual_root: Path, journal: dict) -> None:
                if journal["phase"] == "prepared":
                    observed.append(dict(journal))
                    for entry in list(journal["targets"]) + [journal["snapshot"]]:
                        if entry["post_exists"]:
                            self.assertTrue((actual_root / entry["apply_path"]).exists())
                    raise OSError("stop after preparation")
                original(actual_root, journal)

            with mock.patch.object(transaction, "_journal_write", side_effect=inspect_before_prepared):
                with self.assertRaisesRegex(OSError, "stop after preparation"):
                    transaction.apply(root, [{"path": "AGENTS.md", "bytes": b"product"}], set(), snapshot_payload=self._snapshot())
            self.assertEqual(len(observed), 1)
            self.assertTrue((root / core.JOURNAL_NAME).exists())

    def test_preimage_race_is_rejected_before_recovery_image_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            product = root / "AGENTS.md"
            product.write_bytes(b"before")
            original = transaction._exclusive_write_relative

            def race(actual_root: Path, relative: str, data: bytes, mode: int) -> None:
                if relative == core.JOURNAL_NAME:
                    product.write_bytes(b"changed")
                original(actual_root, relative, data, mode)

            with mock.patch.object(transaction, "_exclusive_write_relative", side_effect=race):
                with self.assertRaisesRegex(ValueError, "preimage changed"):
                    transaction.apply(root, [{"path": "AGENTS.md", "bytes": b"after"}], set(), snapshot_payload=self._snapshot())
            self.assertTrue((root / core.JOURNAL_NAME).exists())

    def test_accepted_effect_rejects_changed_bound_preimage_before_journal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            product = root / "AGENTS.md"
            product.write_bytes(b"current")
            os.chmod(product, 0o640)
            with self.assertRaisesRegex(ValueError, "accepted target preimage changed"):
                transaction.apply(
                    root,
                    [{
                        "path": "AGENTS.md",
                        "bytes": b"replacement",
                        "mode": 0o640,
                        "expected_pre_sha256": core.sha256_bytes(b"accepted-earlier"),
                        "expected_pre_mode": 0o640,
                    }],
                    set(),
                    snapshot_payload=self._snapshot(),
                )
            self.assertEqual(product.read_bytes(), b"current")
            self.assertFalse((root / core.JOURNAL_NAME).exists())

    def test_unexpected_target_requires_evidence_bound_rollback_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            product = root / "AGENTS.md"
            product.write_bytes(b"before")
            original_replace = os.replace

            def fail_product(source: os.PathLike[str], destination: os.PathLike[str], **kwargs: object) -> None:
                if Path(destination).name == "AGENTS.md":
                    raise OSError("stop before product rename")
                original_replace(source, destination, **kwargs)

            with mock.patch.object(transaction.os, "replace", side_effect=fail_product):
                with self.assertRaises(OSError):
                    transaction.apply(root, [{"path": "AGENTS.md", "bytes": b"after"}], set(), snapshot_payload=self._snapshot())
            product.write_bytes(b"unexpected")
            with self.assertRaises(transaction.RecoveryBlocked) as blocked:
                transaction.recover(root)
            proposal = re.search(r"P-RECOVER-ROLLBACK-TRANSACTION-[0-9a-f]{12}", str(blocked.exception))
            self.assertIsNotNone(proposal)
            with self.assertRaises(transaction.RecoveryBlocked):
                transaction.recover(root, {proposal.group(), "P-STALE-RECOVERY-000000000000"})
            self.assertEqual(product.read_bytes(), b"unexpected")
            journal = json.loads((root / core.JOURNAL_NAME).read_text(encoding="utf-8"))
            (root / journal["targets"][0]["apply_path"]).unlink()
            with self.assertRaises(transaction.RecoveryBlocked):
                transaction.recover(root, {proposal.group()})
            with self.assertRaises(transaction.RecoveryBlocked) as changed:
                transaction.recover(root)
            changed_proposal = re.search(r"P-RECOVER-ROLLBACK-TRANSACTION-[0-9a-f]{12}", str(changed.exception))
            self.assertIsNotNone(changed_proposal)
            self.assertNotEqual(changed_proposal.group(), proposal.group())
            self.assertEqual(transaction.recover(root, {changed_proposal.group()})["phase"], "rolled-back")
            self.assertEqual(product.read_bytes(), b"before")

    def test_preparing_transaction_with_unchanged_products_aborts_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            product = root / "AGENTS.md"
            product.write_bytes(b"before")
            with mock.patch.object(transaction, "_image_copy", side_effect=OSError("stop during preparation")):
                with self.assertRaises(OSError):
                    transaction.apply(root, [{"path": "AGENTS.md", "bytes": b"after"}], set(), snapshot_payload=self._snapshot())
            self.assertTrue((root / core.JOURNAL_NAME).exists())
            with self.assertRaises(transaction.RecoveryBlocked):
                transaction.recover(root, {"P-STALE-RECOVERY-000000000000"})
            self.assertEqual(transaction.recover(root)["phase"], "aborted")
            self.assertEqual(product.read_bytes(), b"before")
            self.assertFalse((root / core.JOURNAL_NAME).exists())

    def test_pinned_root_fd_cannot_be_redirected_by_path_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "repo"
            moved = parent / "repo-original"
            root.mkdir()
            with transaction._pinned_root(root):
                root.rename(moved)
                root.mkdir()
                transaction._exclusive_write_relative(root, "artifact", b"bound", 0o600)
            self.assertEqual((moved / "artifact").read_bytes(), b"bound")
            self.assertFalse((root / "artifact").exists())

    def test_invalid_journal_json_types_are_typed_recovery_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            product = root / "AGENTS.md"
            product.write_bytes(b"before")
            with mock.patch.object(transaction, "_image_copy", side_effect=OSError("stop during preparation")):
                with self.assertRaises(OSError):
                    transaction.apply(root, [{"path": "AGENTS.md", "bytes": b"after"}], set(), snapshot_payload=self._snapshot())
            journal_path = root / core.JOURNAL_NAME
            journal = json.loads(journal_path.read_text(encoding="utf-8"))
            journal["schema_version"] = True
            journal_path.write_text(json.dumps(journal), encoding="utf-8")
            os.chmod(journal_path, 0o600)
            with self.assertRaises(transaction.RecoveryBlocked):
                transaction.recover(root)
            self.assertEqual(product.read_bytes(), b"before")


if __name__ == "__main__":
    unittest.main()
