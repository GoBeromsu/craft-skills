---
name: hookify
description: Turns a convention or best practice into local, deterministic enforcement so a violation is blocked before it happens, not corrected after. Use when asked to force a rule locally, hookify a convention, add a pre-commit or lint guard, block edits to a read-only path, stop a risky command in-loop, or wire a Claude Code or Codex runtime hook without relying on CI. Owns the repo's core.hooksPath / .githooks pre-commit mechanism as the sole install point — every other skill registers a guard by dropping an executable into .githooks/guards.d/, never by pointing core.hooksPath elsewhere. Not for git workflow craft itself (branching, worktrees, commit hygiene) — use git.
metadata:
  version: 1.0.0
---

# hookify

Turn one convention into a local, deterministic block so a violation is caught *before* it happens, not fixed after. CI is only a backstop for whoever skipped local — the enforcement itself runs in-loop.

## Overview

The point of enforcement is not preventing permanent harm — it's giving a deterministic "you are wrong" signal fast. Pick a surface on signal delay × clarity × confidence, not reversibility: for the same rule, use the earliest local surface available. A hook only amplifies whatever check runs inside it — a good check becomes inevitable, a bad one becomes a tax on every run. That is why a blocking hook is a graduation, not a starting point.

## When to Use

- A prose rule (`AGENTS.md`) keeps getting violated → raise it to a deterministic surface.
- Forbidden-path edits, dangerous commands, or read-only mutation need to stop in-loop → tier-1 runtime hook.
- Secrets, direct commits to a protected branch, or large blobs need to stop before they're permanent → tier-3 pre-commit.
- The same rule needs to hold in both Claude Code and Codex.

Not now: the rule is still drifting or noisy (fails the 3-gate check below) — put it in prose or a non-blocking lint instead of a blocking hook.

## Ownership: core.hooksPath / .githooks

hookify is the sole owner of the repo's `core.hooksPath` / `.githooks` pre-commit mechanism. It installs `.githooks/pre-commit` as a dispatcher (`scripts/pre-commit.sh`) that runs every executable file in `.githooks/guards.d/` in lexical order and carries no rule logic itself. Any other skill or hand-authored check registers by dropping an executable into `.githooks/guards.d/` — never by pointing `core.hooksPath` somewhere else or shipping a competing `pre-commit` file. Two owners for the same hooksPath is how installs collide; guards.d is the one place that changes. git workflow craft (branching, worktrees, commit conventions) stays owned by `git` — it plugs a guard into this mechanism the same way any other skill does.

## Core Process

### Phase 0 — State the rule in one sentence

Write what you're enforcing as violation condition + fix, in one sentence. If it doesn't fit, the rule isn't ready to enforce — state it in prose first and observe.

### Phase 1 — Pick the surface

Follow the ladder in `references/surface-and-tier.md`. In short:

1. State it in prose first (tier 0) — enforcement is the backstop for where prose failed.
2. Pick the earliest local surface that catches it deterministically: a violation visible in tool behavior (edited path, command) → tier-1 runtime hook; file-content quality → tier-2 lint; irreversible only once committed → tier-3 pre-commit.
3. CI backstops whoever skipped local — it isn't hookify's focus.

### Phase 2 — 3-gate graduation check

Before a rule goes behind a blocking hook, it must pass all three:

- **G1 Cheap** — fast, no external state (network, live backend).
- **G2 Accurate** — near-zero false positives. If the guard needs its own test suite, it has become application code — drop it to a softer surface.
- **G3 Stable** — the structure being enforced has stopped drifting.

Any failure → non-blocking lint warning while it's observed; graduate once proven.

### Phase 3 — Author the guard

Copy `scripts/guard-skeleton.py` and narrow it to exactly one rule. A guard reads its target (path or content) from stdin or args, and on violation exits non-zero with the rule and the exact fix on one stderr line — a vague reason gets bypassed. The same guard is reused unmodified across tiers 1, 2, and 3.

### Phase 4 — Install at the surface

- **Claude Code runtime hook:** merge `scripts/claude-code-pretooluse-guard.sh` + `scripts/settings-hooks.example.json` into `.claude/settings.json` (detail: `references/claude-code-hooks.md`). Only `PreToolUse` blocks a side effect — `PostToolUse` cannot.
- **Codex runtime hook:** merge `scripts/codex-hook.example.toml` into `.codex/config.toml`, reusing the same guard (detail: `references/codex-hooks.md`).
- **lint:** add the rule to the project linter (ruff/eslint) or expose the guard as a command the agent runs mid-task.
- **pre-commit:** drop the guard executable into `.githooks/guards.d/` (create it if absent) and point `core.hooksPath` at `.githooks` once, via `scripts/pre-commit.sh` — see Ownership above.

### Phase 5 — Prove it red

An installed guard that's never been watched firing is unfinished. Run a violating input → blocked, and a clean input → passes, and see both happen (`echo | guard` examples in `references/claude-code-hooks.md`). The guard itself proves red/green via `guard-skeleton.py --selfcheck`.

## Common Rationalizations

- *"CI will catch it."* CI is the latest signal, after push/merge — the agent has already finished the bad behavior. Only a before-the-fact local block corrects it.
- *"Give the guard a test suite, it'll be sturdier."* A guard needing its own tests is application code in the wrong tier (G2) — drop it to a softer surface.
- *"Add more guards for coverage."* Blocking hooks spend a finite trust budget; one false positive teaches `--no-verify` (human) or a workaround (agent), and that erodes every other hook's trust too. Fewer, sharper guards.
- *"The message can be vague."* A vague block reason gets bypassed. Name the rule and the fix, in one line.

## Red Flags

- A blocking hook is installed but has never been watched firing on a violation → unfinished (Phase 5).
- The rule can't be stated in one sentence → not ready to enforce (Phase 0).
- A guard reaches the network or a live backend → fails G1, disqualified from a blocking hook.
- Trying to block a side effect from `PostToolUse` → can't; move it to `PreToolUse`.
- The same rule lives only in CI, nothing local → latest possible signal; move it to a local surface.

## Verification

- [ ] The rule is stated in one sentence: violation condition + fix.
- [ ] The earliest local surface was chosen and the ladder explains why.
- [ ] If it's a blocking hook, all 3 gates (cheap, accurate, stable) pass.
- [ ] The guard message states the rule and the fix in one line.
- [ ] Proved red: a violating input was blocked and a clean input passed, both observed directly.

## Requirements

- `bash`, `jq` — Claude Code / Codex runtime guards.
- `python3` — guard skeleton and `--selfcheck`.
- `git` — pre-commit `core.hooksPath` and `.githooks/guards.d/`.
