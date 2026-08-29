#!/usr/bin/env bash
# Claude Code PreToolUse guard (tier 1: in-loop, blocks BEFORE the tool runs).
#
# Blocks Edit/Write targeting a read-only path. PreToolUse is the earliest
# deterministic signal — the mutation has not happened yet, so the agent gets a
# legible refusal it can act on instead of an after-the-fact failure.
#
# Wire it in settings.json under hooks.PreToolUse with matcher "Edit|Write"
# (see settings-hooks.example.json). Requires `jq`.
#
# Block styles (both stop the tool):
#   - exit 0 + JSON permissionDecision=deny → structured, legible reason the
#     agent reasons about (used here).
#   - exit 2 + reason on stderr → blunt hard abort, no JSON.
set -euo pipefail

input="$(cat)"
tool="$(printf '%s' "$input" | jq -r '.tool_name')"
file="$(printf '%s' "$input" | jq -r '.tool_input.file_path // ""')"

# Read-only path prefix. Replace with your real protected dir.
prefix="${READONLY_PREFIX:-/REPLACE/with/your/readonly/dir}"

case "$file" in
"$prefix" | "$prefix"/*)
	# Name the rule AND the fix — a vague block gets bypassed (trust budget).
	reason="$tool blocked: $file is under read-only path $prefix. Write elsewhere or request operator access."
	jq -nc --arg reason "$reason" '{
		hookSpecificOutput: {
			hookEventName: "PreToolUse",
			permissionDecision: "deny",
			permissionDecisionReason: $reason
		}
	}'
	exit 0
	;;
esac

# Not restricted → implicit allow (no output, exit 0).
exit 0
