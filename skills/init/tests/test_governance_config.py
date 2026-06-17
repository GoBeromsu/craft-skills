#!/usr/bin/env python3
"""Tests for shared init governance config resolution."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "skills/init/scripts"
sys.path.insert(0, str(SCRIPTS))

from governance_config import all_label_specs, is_non_logic_path, resolve_config, type_label_names  # noqa: E402


class GovernanceConfigTest(unittest.TestCase):

    def test_defaults_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = resolve_config(tmp)
            self.assertEqual(config["churn_threshold"], 1000)
            self.assertEqual(config["default_branch"], "main")
            self.assertEqual(config["allowed_base"], ["main", "release/*", "hotfix/*"])
            names = [label["name"] for label in all_label_specs(config)]
            self.assertIn("type: feat", names)
            self.assertIn("type: fix", names)
            self.assertIn("size/S", names)
            self.assertIn("size/override", names)
            self.assertEqual(type_label_names(config), ["type: feat", "type: fix", "type: chore", "type: docs", "type: refactor", "type: test"])
            self.assertEqual(config["labels"]["domain"], [])
            self.assertIn("**/tests/**", config["non_logic_globs"])
            self.assertIn("pnpm-lock.yaml", config["non_logic_globs"])
            self.assertIn("test_*.py", config["non_logic_globs"])

    def test_sparse_repo_override_merges_with_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / ".github/issue-driven-governance.yml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "\n".join([
                    "churn_threshold: 2500",
                    "allowed_base: [main, release/*, staging]",
                    "labels:",
                    "  domain:",
                    "    - name: domain/api",
                    "      color: 1d76db",
                    "      description: API surface",
                ]),
                encoding="utf-8",
            )
            config = resolve_config(root)
            self.assertEqual(config["churn_threshold"], 2500)
            self.assertEqual(config["default_branch"], "main")
            self.assertEqual(config["allowed_base"], ["main", "release/*", "staging"])
            self.assertEqual(config["labels"]["domain"][0]["name"], "domain/api")
            self.assertIn("size/XL", [label["name"] for label in config["labels"]["size"]])

    def test_env_config_path_and_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            override = root / "custom.yml"
            override.write_text(
                "\n".join([
                    "default_branch: ${GOV_BRANCH}",
                    "non_logic_globs:",
                    "  - ${DOCS_GLOB}",
                    "  - generated/**",
                ]),
                encoding="utf-8",
            )
            old_config = os.environ.get("ISSUE_GOVERNANCE_CONFIG")
            old_branch = os.environ.get("GOV_BRANCH")
            old_docs = os.environ.get("DOCS_GLOB")
            os.environ["ISSUE_GOVERNANCE_CONFIG"] = "${CONFIG_DIR}/custom.yml"
            os.environ["CONFIG_DIR"] = str(root)
            os.environ["GOV_BRANCH"] = "trunk"
            os.environ["DOCS_GLOB"] = "docs/**"
            try:
                config = resolve_config(root)
            finally:
                if old_config is None:
                    os.environ.pop("ISSUE_GOVERNANCE_CONFIG", None)
                else:
                    os.environ["ISSUE_GOVERNANCE_CONFIG"] = old_config
                if old_branch is None:
                    os.environ.pop("GOV_BRANCH", None)
                else:
                    os.environ["GOV_BRANCH"] = old_branch
                if old_docs is None:
                    os.environ.pop("DOCS_GLOB", None)
                else:
                    os.environ["DOCS_GLOB"] = old_docs
                os.environ.pop("CONFIG_DIR", None)
            self.assertEqual(config["default_branch"], "trunk")
            self.assertEqual(config["non_logic_globs"], ["docs/**", "generated/**"])


    def test_multi_language_test_paths_are_non_logic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = resolve_config(tmp)
            self.assertTrue(is_non_logic_path("ml/training/test_evaluate_nh.py", config))
            self.assertTrue(is_non_logic_path("ml/tests/test_serving_model.py", config))
            self.assertTrue(is_non_logic_path("backend/src/foo_test.ts", config))
            self.assertFalse(is_non_logic_path("ml/training/evaluate_nh.py", config))


if __name__ == "__main__":
    unittest.main()
