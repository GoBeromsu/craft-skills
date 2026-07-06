#!/usr/bin/env sh
# hookify pre-commit dispatcher (tier 3: local commit gate).
#
# hookify owns core.hooksPath / .githooks as the repo's single pre-commit
# install point. Every other skill or hand-authored check registers a guard
# by dropping an executable script into .githooks/guards.d/ — never by
# pointing core.hooksPath elsewhere or shipping a competing pre-commit file.
# This dispatcher carries no rule logic of its own; every check lives in
# guards.d so there is exactly one place installs can collide.
#
# Install once:
#   mkdir -p .githooks/guards.d
#   cp scripts/pre-commit.sh .githooks/pre-commit && chmod +x .githooks/pre-commit
#   git config core.hooksPath .githooks
#
# Register a guard:
#   cp your-guard.sh .githooks/guards.d/10-your-guard.sh && chmod +x "$_"
#   (numeric prefixes are a convention for ordering; ties break alphabetically)
#
# Tier-3 rule: only put irreversible-at-commit checks in a guard (secrets,
# protected-branch commits, large blobs). Reversible/structural rules belong
# in lint (tier 2) or a runtime hook (tier 1) — an earlier, cheaper signal.
# A guard that needs its own test suite is application code in the wrong
# tier; move it down the ladder (see references/surface-and-tier.md).
set -eu

root="$(git rev-parse --show-toplevel)"
guards_dir="$root/.githooks/guards.d"

[ -d "$guards_dir" ] || exit 0

status=0
for guard in "$guards_dir"/*; do
	[ -e "$guard" ] || continue # empty dir: glob did not expand
	if [ -x "$guard" ]; then
		"$guard" || status=1
	fi
done

exit "$status"
