"""Behaviour tests for the only executable step in the AGENTS lifecycle."""
from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "init" / "scripts" / "agents_region.py"
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))

import agents_region as region

PREFIX = b"# user prefix\n\n"
SUFFIX = b"# user suffix\n"


class AgentsRegionTests(unittest.TestCase):
    def test_missing_file_is_created_as_a_single_managed_region(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            result = region.apply_region(path, "init-root", b"# managed\n")
            self.assertTrue(result["changed"])
            self.assertEqual(path.read_bytes(), region.envelope("init-root", b"# managed\n"))

    def test_replacement_preserves_surrounding_bytes_and_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            path.write_bytes(PREFIX + region.envelope("init-root", b"# old\n") + SUFFIX)
            os.chmod(path, 0o640)
            region.apply_region(path, "init-root", b"# new\n")
            written = path.read_bytes()
            self.assertTrue(written.startswith(PREFIX))
            self.assertTrue(written.endswith(SUFFIX))
            self.assertNotIn(b"# old", written)
            self.assertIn(b"# new", written)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)

    def test_incumbent_instructions_are_appended_to_not_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            path.write_bytes(b"# hand written\nrun make test\n")
            region.apply_region(path, "init-root", b"# managed\n")
            written = path.read_bytes()
            self.assertTrue(written.startswith(b"# hand written\nrun make test\n"))
            self.assertIn(b"init:managed", written)

    def test_rerunning_the_same_payload_is_a_byte_identical_no_op(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            region.apply_region(path, "init-root", b"# managed\n")
            first = path.read_bytes()
            result = region.apply_region(path, "init-root", b"# managed\n")
            self.assertFalse(result["changed"])
            self.assertEqual(path.read_bytes(), first)

    def test_symlinked_target_is_refused_without_touching_its_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.write_bytes(b"do not touch")
            os.symlink(outside, root / "AGENTS.md")
            with self.assertRaises(ValueError):
                region.apply_region(root / "AGENTS.md", "init-root", b"# managed\n")
            self.assertEqual(outside.read_bytes(), b"do not touch")

    def test_duplicate_region_ids_are_refused_instead_of_guessed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            path.write_bytes(region.envelope("init-root", b"# a\n") + region.envelope("init-root", b"# b\n"))
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                region.apply_region(path, "init-root", b"# c\n")
            self.assertEqual(path.read_bytes(), before)

    def test_hand_edited_region_is_refused_instead_of_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            path.write_bytes(region.envelope("init-root", b"# generated\n"))
            path.write_bytes(
                path.read_bytes().replace(b"# generated\n", b"# generated\nnever deploy on Friday\n")
            )
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                region.apply_region(path, "init-root", b"# generated\n")
            self.assertEqual(path.read_bytes(), before)
            self.assertIn(b"never deploy on Friday", path.read_bytes())

    def test_ordinary_payload_update_still_replaces_a_consistent_region(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            path.write_bytes(PREFIX + region.envelope("init-root", b"# v1\n") + SUFFIX)
            self.assertTrue(region.apply_region(path, "init-root", b"# v2\n")["changed"])
            written = path.read_bytes()
            self.assertIn(b"# v2", written)
            self.assertNotIn(b"# v1", written)
            self.assertTrue(written.startswith(PREFIX))
            self.assertTrue(written.endswith(SUFFIX))

    def test_marker_without_a_valid_payload_hash_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            path.write_bytes(region.envelope("init-root", b"# x\n").replace(b"sha256=", b"sha256=zz"))
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                region.apply_region(path, "init-root", b"# y\n")
            self.assertEqual(path.read_bytes(), before)

    def test_payload_without_trailing_newline_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            region.envelope("init-root", b"# no newline")

    def test_cli_reports_json_and_rejects_an_unsafe_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            accepted = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--id", "init-root", "--payload-file", "-"],
                input=b"# via cli\n",
                capture_output=True,
            )
            refused = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--id", "bad id", "--payload-file", "-"],
                input=b"# via cli\n",
                capture_output=True,
            )
            self.assertEqual(accepted.returncode, 0)
            self.assertIn(b'"changed": true', accepted.stdout)
            self.assertEqual(refused.returncode, 2)
            self.assertIn(b'"error"', refused.stderr)
            self.assertIn(b"# via cli", path.read_bytes())


if __name__ == "__main__":
    unittest.main()
