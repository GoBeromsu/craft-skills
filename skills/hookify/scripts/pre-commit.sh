#!/usr/bin/env sh
# Starter pre-commit hook (tier 3: local commit gate).
#
# Install: keep committed guards under <repo>/scripts/guards/ and point git at a
# committed hooks dir so every actor (human, Claude Code, Codex) enforces by
# construction:
#   git config core.hooksPath .githooks
#   cp this file to .githooks/pre-commit && chmod +x .githooks/pre-commit
#
# Tier-3 rule: ONLY put irreversible-at-commit checks here (secrets, protected
# branch, large blobs). Reversible/structural rules belong in lint (tier 2) or a
# runtime hook (tier 1) — an earlier, cheaper signal. A guard that needs its own
# test suite is application code in the wrong tier; move it down the ladder.
set -eu

root="$(git rev-parse --show-toplevel)"
guards="$root/scripts/guards"

# Each guard is a small executable that exits non-zero with a legible reason.
# Add one line per guard. Keep the set small — every guard spends trust budget.
run() {
	if [ -x "$1" ]; then
		"$@"
	fi
}

# --- irreversible-at-commit guards (examples; replace with your real ones) ---

# Refuse commits on a protected branch.
branch="$(git rev-parse --abbrev-ref HEAD)"
case "$branch" in
	main | master)
		echo "pre-commit: direct commits to '$branch' are blocked — branch first." >&2
		exit 1
		;;
esac

# Block staged secrets / large blobs via dedicated guards (you author these).
run "$guards/deny-secrets.sh" staged
run "$guards/deny-large-blobs.sh" staged

# Reminder, not a gate: a hook fires AFTER the work is done. The earliest signal
# for agent behavior is a tier-1 runtime hook — see scripts/ for those starters.
