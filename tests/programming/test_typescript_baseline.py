#!/usr/bin/env python3
"""Execute tsc against the programming package TypeScript baseline."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "skills" / "programming"
BASELINE = PACKAGE_ROOT / "assets" / "tsconfig.strict.json"
FIXTURE_COMPILER = {
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "noEmit": True,
    "types": [],
}


def _require_tsc() -> str:
    tsc = shutil.which("tsc")
    if tsc is None:
        raise AssertionError("tsc is not on PATH; parent-installed typescript@latest is required")
    return tsc


class TypeScriptBaselineTest(unittest.TestCase):
    def _write_fixture(self, directory: Path, source: str) -> Path:
        (directory / "src").mkdir()
        (directory / "src" / "index.ts").write_text(source, encoding="utf-8")
        config = {
            "extends": str(BASELINE.resolve()),
            "compilerOptions": dict(FIXTURE_COMPILER),
            "include": ["src/**/*.ts"],
        }
        path = directory / "tsconfig.json"
        path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        return path

    def _tsc(self, directory: Path) -> subprocess.CompletedProcess[str]:
        tsc = _require_tsc()
        return subprocess.run(
            [tsc, "--pretty", "false", "--project", "tsconfig.json"],
            cwd=directory,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )

    def test_used_code_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(
                root,
                "export function greet(name: string): string {\n"
                "  return `hello ${name}`;\n"
                "}\n",
            )
            result = self._tsc(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unused_local_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(
                root,
                "export function greet(name: string): string {\n"
                "  const unused = name;\n"
                "  return `hello`;\n"
                "}\n",
            )
            result = self._tsc(root)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            combined = result.stdout + result.stderr
            self.assertEqual(re.findall(r"error (TS\d+):", combined), ["TS6133"], combined)
            self.assertRegex(combined, r"\bunused\b")

    def test_unused_import_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(
                root,
                "import { readValue } from \"./dependency.js\";\n"
                "export function greet(name: string): string {\n"
                "  return `hello ${name}`;\n"
                "}\n",
            )
            (root / "src" / "dependency.ts").write_text(
                "export function readValue(): number { return 1; }\n", encoding="utf-8"
            )
            result = self._tsc(root)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            combined = result.stdout + result.stderr
            self.assertEqual(re.findall(r"error (TS\d+):", combined), ["TS6133"], combined)
            self.assertRegex(combined, r"readValue")

    def test_used_import_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(
                root,
                'import { readValue } from "./dependency.js";\n'
                "export const value = readValue();\n",
            )
            (root / "src" / "dependency.ts").write_text(
                "export function readValue(): number { return 1; }\n", encoding="utf-8"
            )
            result = self._tsc(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unused_parameter_is_permitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(
                root,
                "export function greet(name: string): string {\n"
                "  return `hello`;\n"
                "}\n",
            )
            result = self._tsc(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            combined = result.stdout + result.stderr
            self.assertNotIn("TS6133", combined)


if __name__ == "__main__":
    unittest.main()
