"""Governance guard tests.

Several modules here build throwaway git fixture repositories via subprocess.
When the suite runs inside a git hook (pre-push) or a rebase exec, git exports
GIT_DIR and friends, which override cwd-based repository discovery in every
child git process — fixture `git add`/`git commit` calls would then target the
real repository instead of the tempdir fixture. Scrub those variables once,
at package import, so fixtures stay isolated no matter who invokes the suite.
"""

import os

for _var in (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_COMMON_DIR",
    "GIT_PREFIX",
    "GIT_QUARANTINE_PATH",
):
    os.environ.pop(_var, None)
