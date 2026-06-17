#!/usr/bin/env python3
"""Fixture tests for init GitHub label installer and verifier."""
from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
INSTALLER = REPO_ROOT / "skills/init/scripts/install_github_governance.py"
VERIFIER = REPO_ROOT / "skills/init/scripts/verify_github_governance.py"


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

    def test_install_dry_run_prints_change_plan_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            log_path = root / "gh.log"
            _write_fake_gh(
                bin_dir,
                [{"name": "feat", "color": "000000", "description": "old"}],
                log_path,
            )
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["FAKE_GH_LABELS"] = os.environ["FAKE_GH_LABELS"]
            env["FAKE_GH_LOG"] = os.environ["FAKE_GH_LOG"]

            result = self.run_script(INSTALLER, root, env, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("GitHub governance label change plan:", result.stdout)
            self.assertIn("UPDATE feat", result.stdout)
            self.assertIn("CREATE size/override", result.stdout)
            log = log_path.read_text(encoding="utf-8")
            self.assertIn("label list --limit 1000 --json name,color,description", log)
            self.assertNotIn("label create", log)
            self.assertNotIn("label edit", log)

    def test_verify_check_passes_when_all_labels_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            log_path = root / "gh.log"
            names = ["chore", "docs", "feat", "fix", "refactor", "test", "size/L", "size/M", "size/S", "size/XL", "size/override"]
            _write_fake_gh(bin_dir, [{"name": name} for name in names], log_path)
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["FAKE_GH_LABELS"] = os.environ["FAKE_GH_LABELS"]
            env["FAKE_GH_LOG"] = os.environ["FAKE_GH_LOG"]

            result = self.run_script(VERIFIER, root, env, "--check")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("All GitHub governance labels are present.", result.stdout)
            self.assertIn("label list --limit 1000 --json name", log_path.read_text(encoding="utf-8"))

    def test_verify_check_fails_when_labels_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            log_path = root / "gh.log"
            _write_fake_gh(bin_dir, [{"name": "feat"}], log_path)
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["FAKE_GH_LABELS"] = os.environ["FAKE_GH_LABELS"]
            env["FAKE_GH_LOG"] = os.environ["FAKE_GH_LOG"]

            result = self.run_script(VERIFIER, root, env, "--check")

            self.assertEqual(result.returncode, 1)
            self.assertIn("Missing GitHub governance labels:", result.stdout)
            self.assertIn("- fix", result.stdout)
            log = log_path.read_text(encoding="utf-8")
            self.assertIn("label list --limit 1000 --json name", log)
            self.assertNotIn("label create", log)
            self.assertNotIn("label edit", log)


if __name__ == "__main__":
    unittest.main()
