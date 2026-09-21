"""Governance guard tests.

Several modules here build throwaway git fixture repositories via subprocess.
When the suite runs inside a git hook (pre-push) or a rebase exec, git exports
GIT_DIR and friends, which override cwd-based repository discovery in every
child git process — fixture `git add`/`git commit` calls would then target the
real repository instead of the tempdir fixture. Scrub those variables once,
at package import, so fixtures stay isolated no matter who invokes the suite.
Deliberate GIT_DIR/GIT_WORK_TREE injection in a test subprocess env is not
this module's concern and must remain intact in that test.
"""

import os
import tempfile
from pathlib import Path

for _var in list(os.environ):
    if _var.startswith("GIT_"):
        os.environ.pop(_var, None)

# Configure the subprocess environment before any fixture's first git init.
# Keep its owner alive for the test process; TemporaryDirectory cleans up at exit.
_git_fixture_home = tempfile.TemporaryDirectory(prefix="craft-governance-git-")
_git_fixture_root = Path(_git_fixture_home.name)
_hooks = _git_fixture_root / "hooks"
_templates = _git_fixture_root / "templates"
_hooks.mkdir()
_templates.mkdir()
os.environ.update(
    {
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_TEMPLATE_DIR": str(_templates),
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_AUTHOR_NAME": "Governance Tests",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Governance Tests",
        "GIT_COMMITTER_EMAIL": "test@example.com",
        "GIT_CONFIG_COUNT": "2",
        "GIT_CONFIG_KEY_0": "core.hooksPath",
        "GIT_CONFIG_VALUE_0": str(_hooks),
        "GIT_CONFIG_KEY_1": "commit.gpgsign",
        "GIT_CONFIG_VALUE_1": "false",
    }
)
