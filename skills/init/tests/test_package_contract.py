"""Static contract tests for the portable init v4 package surface."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
SKILL = PACKAGE / "SKILL.md"
REFERENCES = PACKAGE / "references"
TEMPLATES = PACKAGE / "templates"
sys.path.insert(0, str(PACKAGE / "scripts"))

import lifecycle_core  # noqa: E402


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if match is None:
        raise AssertionError("SKILL.md must start with YAML frontmatter")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator and not line.startswith((" ", "\t")):
            fields[key] = value.strip().strip('"')
    return fields


class InitPackageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_text = SKILL.read_text(encoding="utf-8")
        cls.fields = frontmatter(cls.skill_text)

    def test_frontmatter_version_and_routing_description(self) -> None:
        self.assertEqual(self.fields["name"], "init")
        self.assertEqual(self.fields["metadata"], "")
        self.assertIn("version: 4.0.0", self.skill_text)
        description = self.fields["description"]
        for trigger in (
            "init this repo",
            "deep-init a codebase",
            "generate or update AGENTS.md",
            "map repository conventions",
            "audit an existing AGENTS lifecycle",
            "prune accepted stale managed AGENTS artifacts",
        ):
            with self.subTest(trigger=trigger):
                self.assertIn(trigger, description)

    def test_body_and_reference_layout_stay_within_authoring_limits(self) -> None:
        self.assertLessEqual(len(self.skill_text.splitlines()), 500)
        reference_files = sorted(REFERENCES.glob("*.md"))
        self.assertTrue(reference_files)
        self.assertEqual(reference_files, sorted(REFERENCES.iterdir()))
        for reference in reference_files:
            lines = reference.read_text(encoding="utf-8").splitlines()
            with self.subTest(reference=reference.name):
                if len(lines) > 100:
                    self.assertTrue(
                        {"## Contents", "## Table of Contents"} & set(lines[:20]),
                        "references over 100 lines must have a table of contents near the top",
                    )

    def test_removed_phase_zero_and_docs_routes_are_not_active(self) -> None:
        active_links = re.findall(r"\]\(([^)]+)\)", self.skill_text)
        for link in active_links:
            with self.subTest(link=link):
                self.assertNotRegex(link.lower(), r"(?:phase-0|docs-(?:bootstrap|scaffold))")

        route_and_map = self.skill_text.split("## Route", 1)[1].split("## Safety and canonicality", 1)[0]
        self.assertNotRegex(route_and_map.lower(), r"\bphase\s*0\b")
        self.assertNotRegex(route_and_map.lower(), r"\bdocs?\s+bootstrap\b")
        self.assertIn("Documentation scaffolding, README, ADRs, and substantive docs content | `document`", self.skill_text)
        self.assertIn("Git hooks and enforcement rails | `git`", self.skill_text)

    def test_lifecycle_and_loading_contracts_are_linked_once(self) -> None:
        expected_links = {
            "references/state-contract.md",
            "references/loading-contract.md",
            "references/phase-1-discovery.md",
            "references/phase-2-scoring.md",
            "references/phase-3-reconcile.md",
            "references/phase-4-verify.md",
        }
        links = set(re.findall(r"\]\((references/[^)]+)\)", self.skill_text))
        self.assertTrue(expected_links.issubset(links))

    def test_claude_shim_is_exact_and_schemas_are_valid_json_schema_documents(self) -> None:
        self.assertEqual(lifecycle_core.SHIM_BYTES, b"@AGENTS.md\n")
        for schema_path in sorted(TEMPLATES.glob("*.schema.json")):
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            with self.subTest(schema=schema_path.name):
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(schema["type"], "object")
                self.assertIn("required", schema)
                self.assertIn("properties", schema)

    def test_obsolete_phase_zero_and_docs_reference_files_do_not_exist(self) -> None:
        obsolete = {
            "phase-0-bootstrap.md",
            "phase-0-discovery.md",
            "docs-bootstrap.md",
            "docs-scaffold.md",
            "documentation.md",
        }
        self.assertFalse(obsolete & {path.name for path in REFERENCES.iterdir()})


if __name__ == "__main__":
    unittest.main()
