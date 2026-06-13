#!/usr/bin/env python3
"""Tests for the validate-routing.py deterministic Layer-1 routing validator.

Each test uses a self-contained tempdir fixture so results never depend on the
real repo tree.
"""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "skills/skillify/scripts/validate-routing.py"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _area_resolver(area: str, leaf_a: str, leaf_b: str) -> str:
    """Minimal valid RESOLVER.md for a two-leaf area with resolving load keys."""
    return (
        f"dispatcher for: {area}\n\n"
        "## Routing Table\n\n"
        "| Trigger intent | Skill / Area | Load key | Boundary | Sibling delta | Compatibility | Notes |\n"
        "|----------------|--------------|----------|----------|---------------|---------------|-------|\n"
        f'| "do {leaf_a}" | {leaf_a} | `{area}/{leaf_a}` | n/a | vs {leaf_b} | claude-code | — |\n'
        f'| "do {leaf_b}" | {leaf_b} | `{area}/{leaf_b}` | n/a | vs {leaf_a} | claude-code | — |\n'
    )


class RoutingValidatorTest(unittest.TestCase):

    def run_validator(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), "--root", str(root), *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def _make_skill(self, root: Path, rel_path: str) -> None:
        """Create a minimal SKILL.md at root/rel_path/SKILL.md."""
        d = root / rel_path
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(f"# {d.name}\n", encoding="utf-8")

    def _write_resolver(self, root: Path, rel_dir: str, content: str) -> None:
        """Write content to root/rel_dir/RESOLVER.md."""
        d = root / rel_dir
        d.mkdir(parents=True, exist_ok=True)
        (d / "RESOLVER.md").write_text(content, encoding="utf-8")

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_good_area_passes(self) -> None:
        """Area with ≥2 leaves + RESOLVER with valid load keys exits 0."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "my-area/leaf-one")
            self._make_skill(root, "my-area/leaf-two")
            self._write_resolver(
                root, "my-area",
                _area_resolver("my-area", "leaf-one", "leaf-two"),
            )
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("UNRESOLVED_LOAD_KEY", result.stdout)
            self.assertNotIn("SPURIOUS_RESOLVER", result.stdout)
            self.assertNotIn("MISSING_AREA_RESOLVER", result.stdout)

    # ------------------------------------------------------------------
    # UNRESOLVED_LOAD_KEY
    # ------------------------------------------------------------------

    def test_unresolved_load_key(self) -> None:
        """A load key pointing to a non-existent skill → UNRESOLVED_LOAD_KEY, exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "my-area/leaf-one")
            self._make_skill(root, "my-area/leaf-two")
            resolver = (
                "dispatcher for: my-area\n\n"
                "## Routing Table\n\n"
                "| Trigger intent | Skill / Area | Load key | Boundary | Sibling delta | Compatibility | Notes |\n"
                "|----------------|--------------|----------|----------|---------------|---------------|-------|\n"
                '| "do one" | leaf-one | `my-area/leaf-one` | n/a | n/a | claude-code | — |\n'
                # This load key references a skill directory that does not exist.
                '| "do missing" | missing | `my-area/does-not-exist` | n/a | n/a | claude-code | — |\n'
            )
            self._write_resolver(root, "my-area", resolver)
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("UNRESOLVED_LOAD_KEY", result.stdout)

    # ------------------------------------------------------------------
    # SPURIOUS_RESOLVER
    # ------------------------------------------------------------------

    def test_spurious_resolver_on_flat_skill(self) -> None:
        """Flat skill (0 leaf sub-skills) with a RESOLVER.md → SPURIOUS_RESOLVER, exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Only a SKILL.md at the flat level; no sub-skill directories.
            self._make_skill(root, "my-flat")
            # Resolver load key points to `my-flat` which resolves (SKILL.md exists),
            # so no UNRESOLVED_LOAD_KEY noise — test stays focused on SPURIOUS_RESOLVER.
            self._write_resolver(
                root, "my-flat",
                (
                    "dispatcher for: my-flat\n\n"
                    "## Routing Table\n\n"
                    "| Trigger intent | Skill / Area | Load key | Boundary | Sibling delta | Compatibility | Notes |\n"
                    "|---|---|---|---|---|---|---|\n"
                    '| "do flat" | my-flat | `my-flat` | n/a | n/a | claude-code | — |\n'
                ),
            )
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("SPURIOUS_RESOLVER", result.stdout)

    # ------------------------------------------------------------------
    # MISSING_AREA_RESOLVER
    # ------------------------------------------------------------------

    def test_missing_area_resolver(self) -> None:
        """Area with ≥2 leaf skills but no RESOLVER.md → MISSING_AREA_RESOLVER, exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_skill(root, "my-area/leaf-one")
            self._make_skill(root, "my-area/leaf-two")
            # Intentionally no RESOLVER.md written in my-area/.
            result = self.run_validator(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("MISSING_AREA_RESOLVER", result.stdout)

    # ------------------------------------------------------------------
    # --advisory always exits 0
    # ------------------------------------------------------------------

    def test_advisory_exits_zero_despite_findings(self) -> None:
        """--advisory reports findings but always returns exit code 0."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Spurious resolver: flat skill with a RESOLVER.md.
            self._make_skill(root, "my-flat")
            self._write_resolver(
                root, "my-flat",
                (
                    "dispatcher for: my-flat\n\n"
                    "## Routing Table\n\n"
                    "| Trigger intent | Skill / Area | Load key | Boundary | Sibling delta | Compatibility | Notes |\n"
                    "|---|---|---|---|---|---|---|\n"
                    '| "flat" | my-flat | `my-flat` | n/a | n/a | claude-code | — |\n'
                ),
            )
            result = self.run_validator(root, "--advisory")
            self.assertEqual(result.returncode, 0)
            self.assertIn("SPURIOUS_RESOLVER", result.stdout)


if __name__ == "__main__":
    unittest.main()
