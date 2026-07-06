#!/usr/bin/env sh
# Idempotent post-clone setup:
#   - registers the `git wt` alias      (simple worktree front door)
#   - chmod +x all hooks, guards.d entries, and guard scripts
#
# Deliberately does NOT set core.hooksPath: hookify is the sole owner of that
# setting and of .githooks/pre-commit (issue #29). The three checks registered
# into .githooks/guards.d/ by install.sh stay inert until core.hooksPath points
# at .githooks — wire that by installing hookify in this repo, or by hand if
# this repo doesn't use hookify: git config core.hooksPath .githooks
#
# Safe to re-run — git config is idempotent, chmod on already-executable files is a no-op.
set -eu

root=$(git rev-parse --show-toplevel)
cd "$root"

# 1. Register `git wt` as an alias that runs wt.sh from the repo root.
git config alias.wt '!sh "$(git rev-parse --show-toplevel)/scripts/git-guard/wt.sh"'

# 2. Ensure all hook + guard scripts are executable.
chmod +x .githooks/pre-push \
         .githooks/guards.d/10-assert-not-main.sh \
         .githooks/guards.d/20-deny-assets.sh \
         .githooks/guards.d/30-check-freshness.sh \
         scripts/git-guard/lib.sh \
         scripts/git-guard/assert-not-main.sh \
         scripts/git-guard/check-freshness.sh \
         scripts/git-guard/deny-assets.sh \
         scripts/git-guard/wt.sh \
         scripts/git-guard/setup-hooks.sh

# 3. Confirmation summary.
hooks_path=$(git config core.hooksPath 2>/dev/null || true)
printf '[git-guard] alias.wt        = %s\n' "$(git config alias.wt)"
printf '[git-guard] guards.d        : .githooks/guards.d/{10-assert-not-main,20-deny-assets,30-check-freshness}.sh\n'
printf '[git-guard] pre-push hook   : .githooks/pre-push\n'
if [ "$hooks_path" = ".githooks" ]; then
  printf '[git-guard] core.hooksPath  = .githooks (already active — checks will fire)\n'
else
  printf '[git-guard] core.hooksPath  is not ".githooks" yet — install hookify, or run: git config core.hooksPath .githooks\n'
fi
printf '[git-guard] setup complete  — run `git wt <name>` to create a worktree.\n'
