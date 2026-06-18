#!/usr/bin/env sh
# Bundled first-run installer for the git-guard rails.
#
# Scaffolds the guard scripts and git hooks into the TARGET repo, then wires
# git config via setup-hooks.sh. This is the single entry point the `worktree`
# and `init` skills delegate to so git-guard comes by default after a clone.
#
# Safe to re-run: existing files are never clobbered, and the git config / chmod
# performed by setup-hooks.sh are idempotent.
#
# Run from anywhere inside the target repo:
#   sh /path/to/skills/worktree/scripts/install.sh
set -eu

# Source: this script lives in the worktree skill's scripts/ dir; hooks are a sibling.
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
hooks_src=$(CDPATH= cd -- "$src/../githooks" && pwd)

# Target: the repo we are standing in.
root=$(git rev-parse --show-toplevel)
cd "$root"

mkdir -p scripts/git-guard .githooks

# 1. Guard scripts -> scripts/git-guard/ (copy if absent; never clobber local edits).
#    Keep this list in sync with setup-hooks.sh's chmod set.
for f in lib.sh assert-not-main.sh check-freshness.sh deny-assets.sh wt.sh tmux-fanout.sh setup-hooks.sh; do
  if [ -f "scripts/git-guard/$f" ]; then
    echo "Skipped (exists): scripts/git-guard/$f"
  elif [ -f "$src/$f" ]; then
    cp "$src/$f" "scripts/git-guard/$f"
    echo "Copied: scripts/git-guard/$f"
  else
    echo "Notice: $src/$f not present in this release — skipped."
  fi
done

# 2. Git hooks -> .githooks/ (copy if absent).
for h in pre-commit pre-push; do
  if [ -f ".githooks/$h" ]; then
    echo "Skipped (exists): .githooks/$h"
  else
    cp "$hooks_src/$h" ".githooks/$h"
    echo "Copied: .githooks/$h"
  fi
done

# 3. Wire git config + chmod (idempotent).
sh scripts/git-guard/setup-hooks.sh
