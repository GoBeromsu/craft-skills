"""Smoke coverage for portable skill package validation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SMOKE = _ROOT / "scripts" / "governance" / "smoke" / "smoke-generic.py"


class GenericSmokeTest(unittest.TestCase):
    def test_real_repository_passes_generic_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            env = os.environ.copy()
            env["SMOKE_OUT"] = output_dir
            result = subprocess.run(
                [sys.executable, str(_SMOKE)],
                cwd=_ROOT,
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            artifact = json.loads((Path(output_dir) / "generic.json").read_text(encoding="utf-8"))
            self.assertEqual(artifact["runtime"], "generic")
            self.assertEqual(artifact["status"], "passed")
            self.assertEqual(
                artifact["checks"],
                ["manifest_matches_skills_tree", "frontmatter", "name_matches_directory", "self_contained"],
            )
    def test_reports_manifest_and_tree_package_differences_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            skill_dir = root / "skills" / "tree-only"
            skill_dir.mkdir(parents=True)
            (root / "skills-manifest.yaml").write_text(
                '{"packages": [{"name": "manifest-only"}]}\n', encoding="utf-8"
            )
            (skill_dir / "SKILL.md").write_text(
                "---\nname: tree-only\ndescription: portable test skill\nmetadata:\n  version: 1.0.0\n---\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(_SMOKE), "--root", str(root)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "skills-manifest.yaml packages missing from skills tree: manifest-only",
            result.stdout,
        )
        self.assertIn(
            "skills tree packages missing from skills-manifest.yaml: tree-only",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
