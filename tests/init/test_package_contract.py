"""Static contract tests for the portable init package surface."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / "skills" / "init"
SKILL = PACKAGE / "SKILL.md"


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise AssertionError("SKILL.md must open with a frontmatter block")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if line.startswith("  ") and ":" in line:
            key, _, value = line.strip().partition(":")
            fields[f"metadata.{key.strip()}"] = value.strip()
        elif ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


class InitPackageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_text = SKILL.read_text(encoding="utf-8")
        cls.fields = frontmatter(cls.skill_text)

    def test_frontmatter_is_portable_and_versioned(self) -> None:
        self.assertEqual(self.fields["name"], PACKAGE.name)
        self.assertRegex(self.fields["metadata.version"], r"^\d+\.\d+\.\d+$")
        self.assertNotIn("license", self.fields)

    def test_description_states_what_and_when_with_a_boundary(self) -> None:
        description = self.fields["description"]
        self.assertIn("AGENTS", description)
        self.assertIn("Use when", description)
        self.assertIn("Not for", description)
        self.assertIn("document", description)
        self.assertIn("git-hook", description)

    def test_body_stays_within_authoring_limits(self) -> None:
        body = self.skill_text.split("---\n", 2)[-1].splitlines()
        self.assertLessEqual(len(body), 500, "body hard-caps at 500 lines")

    def test_every_relative_link_resolves(self) -> None:
        for target in set(re.findall(r"\]\((?!https?:)([^)#]+)", self.skill_text)):
            with self.subTest(target=target):
                self.assertTrue((PACKAGE / target).exists(), f"dangling link: {target}")

    def test_package_ships_only_the_one_executable_step(self) -> None:
        scripts = sorted(path.name for path in (PACKAGE / "scripts").glob("*.py"))
        self.assertEqual(scripts, ["agents_region.py"])
        for module in scripts:
            self.assertTrue(
                (Path(__file__).resolve().parent / f"test_{module}").exists(),
                "every scripts/ module ships with a matching test module",
            )

    def test_removed_machinery_and_routes_are_not_referenced(self) -> None:
        for obsolete in (
            "lifecycle_core",
            "lifecycle_map",
            "lifecycle_prune",
            "lifecycle_audit",
            "_transaction",
            "loading_probe",
            "snapshot.schema.json",
            "transaction.schema.json",
            "--create-new",
            "phase-0",
            "docs-bootstrap",
        ):
            with self.subTest(obsolete=obsolete):
                self.assertNotIn(obsolete, self.skill_text)
                self.assertFalse(list(PACKAGE.rglob(f"*{obsolete}*")))

    def test_claude_adapter_bytes_are_documented_exactly(self) -> None:
        self.assertIn("`@AGENTS.md` plus one LF", self.skill_text)

    def test_init_retains_no_deletion_authority(self) -> None:
        self.assertIn("report-stale", self.skill_text)
        self.assertIn("no deletion authority", self.skill_text)
        self.assertNotIn("init prune", self.skill_text)


if __name__ == "__main__":
    unittest.main()
