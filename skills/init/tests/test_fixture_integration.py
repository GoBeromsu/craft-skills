#!/usr/bin/env python3
"""Semantic fixture-repo proof for init GitHub governance installer/verifier."""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "skills/init/scripts"
sys.path.insert(0, str(SCRIPTS))

from governance_config import all_label_specs, resolve_config, type_label_names  # noqa: E402
from install_github_governance import (  # noqa: E402
    AUTO_LABEL_WORKFLOW_PATH,
    ISSUE_TEMPLATE_PATH,
    PR_CHECK_WORKFLOW_PATH,
    desired_files,
)

INSTALLER = REPO_ROOT / "skills/init/scripts/install_github_governance.py"
VERIFIER = REPO_ROOT / "skills/init/scripts/verify_github_governance.py"
GOVERNANCE_FILES = [ISSUE_TEMPLATE_PATH, AUTO_LABEL_WORKFLOW_PATH, PR_CHECK_WORKFLOW_PATH]


FAKE_GH = r'''#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

state_path = Path(os.environ["FAKE_GH_STATE"])
log_path = Path(os.environ["FAKE_GH_LOG"])
args = sys.argv[1:]
with log_path.open("a", encoding="utf-8") as log:
    log.write(" ".join(args) + "\n")

if state_path.exists():
    labels = json.loads(state_path.read_text(encoding="utf-8"))
else:
    labels = []


def save() -> None:
    labels.sort(key=lambda item: item["name"])
    state_path.write_text(json.dumps(labels, sort_keys=True), encoding="utf-8")


if args[:2] == ["label", "list"]:
    print(json.dumps(labels))
    raise SystemExit(0)

if args[:2] == ["label", "create"]:
    name = args[2]
    color = args[args.index("--color") + 1] if "--color" in args else ""
    description = args[args.index("--description") + 1] if "--description" in args else ""
    if not any(label["name"] == name for label in labels):
        labels.append({"name": name, "color": color, "description": description})
    save()
    raise SystemExit(0)

if args[:2] == ["label", "edit"]:
    name = args[2]
    color = args[args.index("--color") + 1] if "--color" in args else None
    description = args[args.index("--description") + 1] if "--description" in args else None
    for label in labels:
        if label["name"] == name:
            if color is not None:
                label["color"] = color
            if description is not None:
                label["description"] = description
            break
    else:
        labels.append({"name": name, "color": color or "", "description": description or ""})
    save()
    raise SystemExit(0)

raise SystemExit(9)
'''


class FixtureIntegrationTest(unittest.TestCase):
    def make_fixture(self, root: Path, initial_labels: list[dict[str, str]] | None = None) -> tuple[dict[str, str], Path, Path]:
        bin_dir = root / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        gh.write_text(FAKE_GH, encoding="utf-8")
        gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
        state_path = root / "gh-labels.json"
        state_path.write_text(json.dumps(initial_labels or [], sort_keys=True), encoding="utf-8")
        log_path = root / "gh.log"
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
        env["FAKE_GH_STATE"] = str(state_path)
        env["FAKE_GH_LOG"] = str(log_path)
        env.pop("ISSUE_GOVERNANCE_CONFIG", None)
        return env, state_path, log_path

    def run_script(self, script: Path, root: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python", str(script), "--repo-root", str(root), *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def snapshot(self, root: Path, state_path: Path) -> dict[str, str]:
        data = {str(path): (root / path).read_text(encoding="utf-8") for path in GOVERNANCE_FILES}
        data["labels"] = state_path.read_text(encoding="utf-8")
        return data

    def assert_resolved_outputs(self, root: Path) -> None:
        config = resolve_config(root)
        labels = json.loads((root / "gh-labels.json").read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(label["name"] for label in labels),
            sorted(label["name"] for label in all_label_specs(config)),
        )
        for path, expected in desired_files(config).items():
            self.assertEqual((root / path).read_text(encoding="utf-8"), expected)
        template = (root / ISSUE_TEMPLATE_PATH).read_text(encoding="utf-8")
        for name in type_label_names(config):
            self.assertIn(f"        - {name}", template)

    def test_fixture_repo_install_verify_and_reinstall_are_semantic_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, state_path, log_path = self.make_fixture(root)

            install = self.run_script(INSTALLER, root, env)
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
            self.assert_resolved_outputs(root)

            verify = self.run_script(VERIFIER, root, env, "--check")
            self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
            self.assertIn("All GitHub governance labels", verify.stdout)

            before = self.snapshot(root, state_path)
            reinstall = self.run_script(INSTALLER, root, env)
            self.assertEqual(reinstall.returncode, 0, reinstall.stdout + reinstall.stderr)
            self.assertIn("already up to date", reinstall.stdout)
            self.assertEqual(self.snapshot(root, state_path), before)
            log = log_path.read_text(encoding="utf-8")
            self.assertIn("label create feat", log)
            self.assertIn("label list --limit 1000 --json name,color,description", log)

    def test_override_fixture_changes_resolved_behavior_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / ".github/issue-driven-governance.yml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "\n".join([
                    "churn_threshold: 77",
                    "allowed_base: [trunk]",
                    "labels:",
                    "  type:",
                    "    - name: spike",
                    "      color: 5319e7",
                    "      description: Research spike",
                    "    - name: bug",
                    "      color: d73a4a",
                    "      description: Bug fix",
                    "  domain:",
                    "    - name: area/api",
                    "      color: 1d76db",
                    "      description: API domain",
                ]),
                encoding="utf-8",
            )
            env, _, _ = self.make_fixture(root)

            install = self.run_script(INSTALLER, root, env)
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
            self.assert_resolved_outputs(root)
            verify = self.run_script(VERIFIER, root, env, "--check")
            self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)

            template = (root / ISSUE_TEMPLATE_PATH).read_text(encoding="utf-8")
            pr_check = (root / PR_CHECK_WORKFLOW_PATH).read_text(encoding="utf-8")
            labels = json.loads((root / "gh-labels.json").read_text(encoding="utf-8"))
            self.assertIn("        - spike", template)
            self.assertIn("        - bug", template)
            self.assertNotIn("        - feat", template)
            self.assertIn("CHURN_THRESHOLD: '77'", pr_check)
            self.assertIn("ALLOWED_BASES: '[\"trunk\"]'", pr_check)
            self.assertIn("area/api", [label["name"] for label in labels])


if __name__ == "__main__":
    unittest.main()
