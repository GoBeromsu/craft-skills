"""Filesystem absence of retired init lifecycle artifacts."""

from __future__ import annotations

import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / "skills" / "init"

RETIRED_MODULES = (
    "lifecycle_core",
    "lifecycle_map",
    "lifecycle_prune",
    "lifecycle_audit",
    "_transaction",
    "loading_probe",
)
RETIRED_SCHEMAS = (
    "snapshot.schema.json",
    "transaction.schema.json",
)


class InitPackageContractTests(unittest.TestCase):
    def test_retired_lifecycle_artifacts_are_absent(self) -> None:
        for stem in RETIRED_MODULES:
            with self.subTest(artifact=stem):
                candidates = (
                    PACKAGE / "scripts" / f"{stem}.py",
                    PACKAGE / "scripts" / stem,
                    PACKAGE / stem,
                )
                present = [str(path.relative_to(PACKAGE)) for path in candidates if path.exists()]
                self.assertEqual(present, [])
        for name in RETIRED_SCHEMAS:
            with self.subTest(artifact=name):
                candidates = (
                    PACKAGE / name,
                    PACKAGE / "scripts" / name,
                    PACKAGE / "references" / name,
                )
                present = [str(path.relative_to(PACKAGE)) for path in candidates if path.exists()]
                self.assertEqual(present, [])


if __name__ == "__main__":
    unittest.main()
