#!/usr/bin/env python3
"""Fixture tests for init GitHub governance installer and verifier."""
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

from governance_config import resolve_config  # noqa: E402
from install_github_governance import AUTO_LABEL_WORKFLOW_PATH, ISSUE_TEMPLATE_PATH, PR_CHECK_WORKFLOW_PATH, desired_files  # noqa: E402

INSTALLER = REPO_ROOT / "skills/init/scripts/install_github_governance.py"
VERIFIER = REPO_ROOT / "skills/init/scripts/verify_github_governance.py"

DEFAULT_LABEL_NAMES = [
    "chore", "docs", "feat", "fix", "refactor", "test",
    "size/L", "size/M", "size/S", "size/XL", "size/override",
]


def _write_fake_gh(bin_dir: Path, labels: list[dict[str, str]], log_path: Path) -> None:
    script = bin_dir / "gh"
    script.write_text(
        "\n".join([
            "#!/usr/bin/env python3",
            "import json, os, sys",
            "labels = json.loads(os.environ.get('FAKE_GH_LABELS', '[]'))",
            "with open(os.environ['FAKE_GH_LOG'], 'a', encoding='utf-8') as log:",
            "    log.write(' '.join(sys.argv[1:]) + '\\n')",
            "if sys.argv[1:3] == ['label', 'list']:",
            "    print(json.dumps(labels))",
            "    raise SystemExit(0)",
            "if sys.argv[1:3] in (['label', 'create'], ['label', 'edit']):",
            "    raise SystemExit(0)",
            "raise SystemExit(9)",
        ]),
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    os.environ["FAKE_GH_LABELS"] = json.dumps(labels)
    os.environ["FAKE_GH_LOG"] = str(log_path)


def _write_desired_files(root: Path) -> None:
    for relative_path, content in desired_files(resolve_config(root)).items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


class LabelGovernanceTest(unittest.TestCase):

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

    def fake_env(self, root: Path, labels: list[dict[str, str]]) -> tuple[dict[str, str], Path]:
        bin_dir = root / "bin"
        bin_dir.mkdir()
        log_path = root / "gh.log"
        _write_fake_gh(bin_dir, labels, log_path)
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
        env["FAKE_GH_LABELS"] = os.environ["FAKE_GH_LABELS"]
        env["FAKE_GH_LOG"] = os.environ["FAKE_GH_LOG"]
        return env, log_path

    def test_install_dry_run_prints_change_plan_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env, log_path = self.fake_env(root, [{"name": "feat", "color": "000000", "description": "old"}])

            result = self.run_script(INSTALLER, root, env, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("GitHub governance change plan:", result.stdout)
            self.assertIn("UPDATE label feat", result.stdout)
            self.assertIn("CREATE label size/override", result.stdout)
            self.assertIn(f"WRITE {ISSUE_TEMPLATE_PATH}", result.stdout)
            self.assertIn(f"WRITE {AUTO_LABEL_WORKFLOW_PATH}", result.stdout)
            self.assertIn(f"WRITE {PR_CHECK_WORKFLOW_PATH}", result.stdout)
            log = log_path.read_text(encoding="utf-8")
            self.assertIn("label list --limit 1000 --json name,color,description", log)
            self.assertNotIn("label create", log)
            self.assertNotIn("label edit", log)
            self.assertFalse((root / ISSUE_TEMPLATE_PATH).exists())

    def test_install_writes_template_and_auto_label_from_resolved_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / ".github/issue-driven-governance.yml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "\n".join([
                    "labels:",
                    "  type:",
                    "    - name: spike",
                    "      color: 5319e7",
                    "      description: Research spike",
                    "    - name: bug",
                    "      color: d73a4a",
                    "      description: Bug fix",
                ]),
                encoding="utf-8",
            )
            env, _ = self.fake_env(root, [{"name": "spike", "color": "5319e7", "description": "Research spike"}, {"name": "bug", "color": "d73a4a", "description": "Bug fix"}])

            result = self.run_script(INSTALLER, root, env)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            template = (root / ISSUE_TEMPLATE_PATH).read_text(encoding="utf-8")
            workflow = (root / AUTO_LABEL_WORKFLOW_PATH).read_text(encoding="utf-8")
            self.assertIn("### Type", template)
            self.assertIn("        - spike", template)
            self.assertIn("        - bug", template)
            self.assertNotIn("        - feat", template)
            self.assertIn("TYPE_LABELS: '[\"spike\", \"bug\"]'", workflow)
            self.assertIn("core.setFailed('Missing ### Type section", workflow)
            self.assertIn("Unknown Type", workflow)
            self.assertIn("labels: [selected]", workflow)


    def test_install_writes_pr_check_from_resolved_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / ".github/issue-driven-governance.yml"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "\n".join([
                    "churn_threshold: 42",
                    "allowed_base: [trunk, release/*]",
                    "non_logic_globs:",
                    "  - docs/**",
                    "  - **/fixtures/**",
                    "labels:",
                    "  size:",
                    "    - name: xs",
                    "    - name: md",
                    "    - name: lg",
                    "    - name: huge",
                    "  override:",
                    "    - name: governance/size-override",
                ]),
                encoding="utf-8",
            )
            env, _ = self.fake_env(root, [{"name": name} for name in DEFAULT_LABEL_NAMES])

            result = self.run_script(INSTALLER, root, env)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            workflow = (root / PR_CHECK_WORKFLOW_PATH).read_text(encoding="utf-8")
            self.assertIn("CHURN_THRESHOLD: '42'", workflow)
            self.assertIn("ALLOWED_BASES: '[\"trunk\", \"release/*\"]'", workflow)
            self.assertIn("NON_LOGIC_GLOBS: '[\"docs/**\", \"**/fixtures/**\"]'", workflow)
            self.assertIn("SIZE_LABELS: '[\"xs\", \"md\", \"lg\", \"huge\"]'", workflow)
            self.assertIn("OVERRIDE_LABEL: '\"governance/size-override\"'", workflow)
            self.assertIn("// === SIZE-CHECK-LOGIC-START ===", workflow)
            self.assertIn("logicChurn > threshold && !hasOverride", workflow)

    def test_verify_check_passes_when_all_governance_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_desired_files(root)
            env, log_path = self.fake_env(root, [{"name": name} for name in DEFAULT_LABEL_NAMES])

            result = self.run_script(VERIFIER, root, env, "--check")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("All GitHub governance labels, issue template, auto-label workflow, and PR check workflow are present.", result.stdout)
            self.assertIn("label list --limit 1000 --json name", log_path.read_text(encoding="utf-8"))

    def test_verify_check_fails_when_labels_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_desired_files(root)
            env, log_path = self.fake_env(root, [{"name": "feat"}])

            result = self.run_script(VERIFIER, root, env, "--check")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Missing GitHub governance labels:", result.stdout)
            self.assertIn("- fix", result.stdout)
            log = log_path.read_text(encoding="utf-8")
            self.assertIn("label list --limit 1000 --json name", log)
            self.assertNotIn("label create", log)
            self.assertNotIn("label edit", log)

    def test_verify_check_fails_when_issue_template_type_options_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_desired_files(root)
            template = root / ISSUE_TEMPLATE_PATH
            template.write_text(template.read_text(encoding="utf-8").replace("        - fix", "        - unknown"), encoding="utf-8")
            env, _ = self.fake_env(root, [{"name": name} for name in DEFAULT_LABEL_NAMES])

            result = self.run_script(VERIFIER, root, env, "--check")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Issue template Type options do not match resolved type labels.", result.stdout)

    def test_verify_check_fails_when_auto_label_mapping_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_desired_files(root)
            workflow = root / AUTO_LABEL_WORKFLOW_PATH
            workflow.write_text(workflow.read_text(encoding="utf-8").replace('"fix"', '"unknown"', 1), encoding="utf-8")
            env, _ = self.fake_env(root, [{"name": name} for name in DEFAULT_LABEL_NAMES])

            result = self.run_script(VERIFIER, root, env, "--check")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Auto-label workflow TYPE_LABELS do not match resolved type labels.", result.stdout)


    def test_verify_check_fails_when_pr_check_resolved_values_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_desired_files(root)
            pr_check = root / PR_CHECK_WORKFLOW_PATH
            pr_check.write_text(pr_check.read_text(encoding="utf-8").replace("CHURN_THRESHOLD: '1000'", "CHURN_THRESHOLD: '5'"), encoding="utf-8")
            env, _ = self.fake_env(root, [{"name": name} for name in DEFAULT_LABEL_NAMES])

            result = self.run_script(VERIFIER, root, env, "--check")

            self.assertEqual(result.returncode, 1)
            self.assertIn("PR check workflow threshold does not match resolved config.", result.stdout)


if __name__ == "__main__":
    unittest.main()
