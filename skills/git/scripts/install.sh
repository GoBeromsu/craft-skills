#!/usr/bin/env sh
# Bundled first-run installer for the git-guard checks.
#
# Scaffolds the guard scripts into the TARGET repo and registers the pre-commit
# checks as .githooks/guards.d/ entries — the composable convention owned by
# the `hookify` skill (issue #29: hookify is the sole owner of core.hooksPath
# and .githooks/pre-commit; this installer never writes either). Also installs
# .githooks/pre-push directly, since hookify has no push-time surface to
# collide with. This is the single entry point the `worktree` reference (git
# skill) and `init` skill delegate to.
#
# Safe to re-run: existing files are never clobbered, and the git config / chmod
# performed by setup-hooks.sh are idempotent.
#
# Run from anywhere inside the target repo:
#   sh /path/to/skills/git/scripts/install.sh
set -eu

# Source: this script lives in scripts/; githooks/ is a sibling.
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
hooks_src=$(CDPATH= cd -- "$src/../githooks" && pwd)

# Target: the repo we are standing in.
root=$(git rev-parse --show-toplevel)
cd "$root"

mkdir -p scripts/git-guard .githooks/guards.d

# 1. Guard scripts -> scripts/git-guard/ (copy if absent; never clobber local edits).
#    Keep this list in sync with setup-hooks.sh's chmod set.
for f in lib.sh assert-not-main.sh check-freshness.sh deny-assets.sh wt.sh setup-hooks.sh; do
  if [ -f "scripts/git-guard/$f" ]; then
    echo "Skipped (exists): scripts/git-guard/$f"
  elif [ -f "$src/$f" ]; then
    cp "$src/$f" "scripts/git-guard/$f"
    echo "Copied: scripts/git-guard/$f"
  else
    echo "Notice: $src/$f not present in this release — skipped."
  fi
done

# 2. Pre-commit checks -> .githooks/guards.d/ (copy if absent). hookify's own
#    dispatcher runs every executable here in lexical order; this installer
#    never writes .githooks/pre-commit and never touches core.hooksPath.
for g in 10-assert-not-main.sh 20-deny-assets.sh 30-check-freshness.sh; do
  if [ -f ".githooks/guards.d/$g" ]; then
    echo "Skipped (exists): .githooks/guards.d/$g"
  else
    cp "$hooks_src/guards.d/$g" ".githooks/guards.d/$g"
    echo "Copied: .githooks/guards.d/$g"
  fi
done

# 3. pre-push hook -> .githooks/ (copy if absent). Installed directly, not via
#    guards.d — hookify owns pre-commit only, so there is no push-time surface
#    to collide with here.
if [ -f ".githooks/pre-push" ]; then
  echo "Skipped (exists): .githooks/pre-push"
else
  cp "$hooks_src/pre-push" ".githooks/pre-push"
  echo "Copied: .githooks/pre-push"
fi

# 4. Wire the `git wt` alias + chmod everything (idempotent). core.hooksPath is
#    deliberately not set here — see setup-hooks.sh and references/worktree.md
#    Step 1's hand-off note.
sh scripts/git-guard/setup-hooks.sh
