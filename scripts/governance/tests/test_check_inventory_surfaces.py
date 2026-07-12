"""Tests for the inventory-surface drift checker."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_TOOL = _ROOT / "scripts" / "governance" / "tools" / "check_inventory_surfaces.py"
_SPEC = importlib.util.spec_from_file_location("check_inventory_surfaces", _TOOL)
assert _SPEC and _SPEC.loader
check_inventory_surfaces = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(check_inventory_surfaces)


class InventorySurfacesTest(unittest.TestCase):
    def _fixture(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for name in ("alpha", "beta"):
            (root / "skills" / name).mkdir(parents=True)
            (root / "skills" / name / "SKILL.md").write_text("# skill\n", encoding="utf-8")
        (root / "AGENTS.md").write_text(
            "The 2 packages (alphabetical): `alpha`, `beta`.\n", encoding="utf-8"
        )
        (root / "docs/governance").mkdir(parents=True)
        (root / ".codex-plugin").mkdir()
        (root / ".claude-plugin").mkdir()
        (root / "skills-manifest.yaml").write_text(
            json.dumps({"packages": [{"name": "alpha"}, {"name": "beta"}]}), encoding="utf-8"
        )
        (root / "docs/governance/routing-eval-coverage.json").write_text(
            json.dumps({"expected_craft_packages": ["alpha", "beta"]}), encoding="utf-8"
        )
        (root / "docs/governance/routing-eval-cases.yaml").write_text(
            json.dumps(
                {
                    "cases": [
                        {"expected_package": "craft-skills/alpha"},
                        {"expected_package": "craft-skills/beta"},
                        {"expected_package": "other-repo/ignored"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        for relative_path in (".codex-plugin/plugin.json", ".claude-plugin/marketplace.json"):
            (root / relative_path).write_text(
                json.dumps({"description": "Skills across 2 packages."}), encoding="utf-8"
            )
        return temp

    def test_matching_surfaces_pass(self) -> None:
        with self._fixture() as temp:
            self.assertEqual(check_inventory_surfaces.check_inventory_surfaces(Path(temp)), [])

    def test_reports_per_surface_drift(self) -> None:
        with self._fixture() as temp:
            root = Path(temp)
            (root / "docs/governance/routing-eval-coverage.json").write_text(
                json.dumps({"expected_craft_packages": ["alpha"]}), encoding="utf-8"
            )
            errors = check_inventory_surfaces.check_inventory_surfaces(root)
            self.assertTrue(any("routing-eval-coverage.json names" in error for error in errors))

    def test_cli_returns_nonzero_for_drift(self) -> None:
        with self._fixture() as temp:
            root = Path(temp)
            (root / "AGENTS.md").write_text(
                "The 1 packages (alphabetical): `alpha`.\n", encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(_TOOL), "--root", str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("AGENTS.md list", result.stdout)


if __name__ == "__main__":
    unittest.main()
