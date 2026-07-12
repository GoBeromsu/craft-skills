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
                ["frontmatter", "name_matches_directory", "self_contained"],
            )


if __name__ == "__main__":
    unittest.main()
