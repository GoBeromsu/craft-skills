---
name: guardrails
description: Turns a convention into local, deterministic enforcement — runtime hooks, linter and formatter configuration, and pre-commit guards — so a violation is blocked before it happens rather than corrected after. Use when asked to force a rule locally, add a pre-commit or lint guard, configure eslint, ruff, or prettier, stage a linter rule set, adopt a formatter, block edits to a read-only path, stop a risky command in-loop, or wire a Claude Code or Codex runtime hook without relying on CI. Owns the repo's core.hooksPath mechanism and its linter and formatter configuration. Not for git workflow craft (branching, worktrees, commit hygiene) — use git — or pipeline wiring, which belongs to cicd.
metadata:
  version: 2.0.0
---

# guardrails

Turn one convention into a local, deterministic block so a violation is caught *before* it happens, not fixed after.
CI is only a backstop for whoever skipped local — the enforcement itself runs in-loop.

## Overview

The point of enforcement is not preventing permanent harm — it's giving a deterministic "you are wrong" signal fast.
Pick a surface on signal delay × clarity × confidence, not reversibility: for the same rule, use the earliest local surface available.
A guardrail only amplifies whatever check runs inside it — a good check becomes inevitable, a bad one becomes a tax on every run.
That is why a blocking hook or a newly enabled rule set is a graduation, not a starting point.

## When to Use

- A prose rule (`AGENTS.md`) keeps getting violated → raise it to a deterministic surface.
- Forbidden-path edits, dangerous commands, or read-only mutation need to stop in-loop → tier-1 runtime hook.
- A linter or formatter needs configuring, a rule set needs staging, or a repo needs `eslint`/`ruff`/`prettier` set up → tier-2 configuration.
- Secrets, direct commits to a protected branch, or large blobs need to stop before they're permanent → tier-3 pre-commit.
- The same rule needs to hold in both Claude Code and Codex.

Not now: the rule is still drifting or noisy (fails the 3-gate check below) — put it in prose or a non-blocking lint instead of a blocking hook.

## Ownership

Two mechanisms belong to this skill, and both are single-owner for the same reason: two owners for one config file is how installs collide.

**`core.hooksPath` / `.githooks`.**
This skill installs `.githooks/pre-commit` as a dispatcher (`scripts/pre-commit.sh`) that runs every executable file in `.githooks/guards.d/` in lexical order and carries no rule logic itself.
Any other skill or hand-authored check registers by dropping an executable into `.githooks/guards.d/` — never by pointing `core.hooksPath` elsewhere or shipping a competing `pre-commit` file.
`init` routes hook-install requests to `git`; `git` registers its git-guard through this dispatcher.

**Linter and formatter configuration.**
The repo's linter rule selection, per-file ignores, and formatter adoption are this skill's surface, not a caller's ad-hoc edit.
A rule that needs enforcing is expressed in the linter's own configuration before anyone writes a bespoke checker script; configuration is already wired into the checks that run, and the next person edits one file instead of learning a private tool.
`refactor` uses the linter as a lever to shrink a package and routes the configuration decisions here; `cicd` owns making the resulting command a required check.

## Core Process

### Phase 0 — State the rule in one sentence

Write what you're enforcing as violation condition + fix, in one sentence.
If it doesn't fit, the rule isn't ready to enforce — state it in prose first and observe.

### Phase 1 — Pick the surface

Follow the ladder in `references/surface-and-tier.md`.
In short:

1. State it in prose first (tier 0) — enforcement is the backstop for where prose failed.
2. Pick the earliest local surface that catches it deterministically: a violation visible in tool behavior (edited path, command) → tier-1 runtime hook; file-content quality expressible as a rule → tier-2 lint or formatter configuration; irreversible only once committed → tier-3 pre-commit.
3. CI backstops whoever skipped local — it isn't this skill's focus.

### Phase 2 — 3-gate graduation check

Before a rule goes behind a blocking hook or into the enabled rule set, it must pass all three:

- **G1 Local and cheap** — measured latency fits the local workflow and the check needs no external state (network, live backend).
- **G2 Accurate and repeatable** — repeated representative inputs show acceptable false-positive rate and no meaningful nondeterminism.
- **G3 Stable** — the structure being enforced has stopped drifting.

Any failure → non-blocking lint warning while it is observed; graduate when measured evidence supports blocking.

### Phase 3 — Author the guard, or choose the rule set

For a bespoke rule, copy `scripts/guard-skeleton.py` and narrow it to exactly one rule.
A guard reads its target (path or content) from stdin or args, and on violation exits non-zero with the rule and the exact fix on one stderr line — a vague reason gets bypassed.
For a nontrivial parsing or content guard, add focused red/green regression tests around the decision boundary; do not broaden them into a full application suite.
The same guard is reused unmodified across tiers 1, 2, and 3.

For a rule the incumbent linter already ships, prefer its configuration over a bespoke guard and stage the rule set by measured hit count rather than switching everything on at once — the procedure, the ignore policy, and the commit split live in `references/lint-config.md`.
For an architectural boundary rule — who may import whom — follow `references/boundary-lint.md`.

### Phase 4 — Install at the surface

For mutable runtime hook, event, tool, or linter-rule capabilities, consult official primary docs first and disclose conflicts; a more-specific local contract or matching-version/platform reproducible evidence may override general or stale docs.
Unresolved capability stays unknown: do not invent surfaces or rule codes; use a known supported surface or stop.

- **Claude Code runtime hook:** merge `scripts/claude-code-pretooluse-guard.sh` + `scripts/settings-hooks.example.json` into `.claude/settings.json` (detail: `references/claude-code-hooks.md`). Only `PreToolUse` blocks a side effect — `PostToolUse` cannot.
- **Codex runtime hook:** merge `scripts/codex-hook.example.toml` into `.codex/config.toml`, reusing the same guard (detail: `references/codex-hooks.md`).
- **lint and formatter configuration:** add the rule to the project linter's own config file and stage it per `references/lint-config.md`, or expose the guard as a command the agent runs mid-task. Read every autofix diff against `references/autofix-failure-classes.md` before trusting it.
- **pre-commit:** drop the guard executable into `.githooks/guards.d/` (create it if absent) and point `core.hooksPath` at `.githooks` once, via `scripts/pre-commit.sh` — see Ownership above.

### Phase 5 — Prove it red

An installed guardrail that has never been watched firing is unfinished.
Run a violating input → blocked, and a clean input → passes, and see both happen; use `guard-skeleton.py --selfcheck` as smoke proof, not as a replacement for those focused regression tests.
For a newly enabled rule set, the equivalent proof is the recorded before-and-after hit count plus a green suite after the autofix commit.

## Anti-patterns

- Relying on CI alone to catch a violation, with no local enforcement → move it to a local surface; CI is the latest possible signal, after push/merge, when the agent has already finished the bad behavior.
- Treating a guard test suite as proof it belongs outside enforcement → keep focused parsing/content regression tests when the guard is nontrivial; choose the surface from measured latency, external state, nondeterminism, and false-positive rate.
- Adding more guards for broader coverage → keep guards few and sharp; blocking hooks spend a finite trust budget, and one false positive teaches `--no-verify` (human) or a workaround (agent), eroding trust in every other hook.
- Leaving a guard's block message vague → name the rule and the exact fix in one line; a vague reason gets bypassed.
- Installing a blocking hook without ever watching it fire on a violation → prove it red first: run a violating input and a clean input and observe both (Phase 5).
- Trying to enforce a rule that can't be stated in one sentence → state it in prose first and observe until it's ready (Phase 0).
- Writing a guard that reaches the network or a live backend → disqualify it from a blocking hook (fails G1); use a softer surface instead.
- Trying to block a side effect from `PostToolUse` → move it to `PreToolUse`; only `PreToolUse` can block a side effect.
- Writing a script that greps imports to check layering → express the rule in the linter's own boundary configuration; a bespoke checker is a private tool the next person has to learn and CI has to be taught to call.
- Leaving a boundary rule in a contributor guide because reviewers will catch it → encode it in configuration and point the prose at the config file; prose has no failure mode.
- Deleting a module a boundary contract names without updating the contract → update both in the same commit, or the checker errors on an unknown module.
- Enabling a linter's full recommended rule set in one commit → count each candidate set's hits on the target first and enable only what pays (`references/lint-config.md`).
- Applying `--fix` or `--unsafe-fixes` and committing without reading the diff → every class in `references/autofix-failure-classes.md` is silent until the suite runs.
- Committing configuration, autofix output, and hand judgment together → split them; judgment changes reviewed inside a mechanical diff are not reviewed.
- Disabling a rule globally because it fires in tests or vendored code → scope it to those files and write the reason next to the ignore.
- Hand-editing whitespace in a file a formatter owns → change the formatter's configuration instead, or the next run reverts the edit and the diff churns forever.
- Adopting a formatter with a repo-wide reformat commit in the same change as a behavior fix → land the sweep alone, or ratchet it directory by directory (`references/lint-config.md`).

## Verification

- [ ] The rule is stated in one sentence: violation condition + fix.
- [ ] The earliest local surface was chosen and the ladder explains why.
- [ ] If it's a blocking hook, all 3 gates (cheap, accurate, stable) pass.
- [ ] The guard message states the rule and the fix in one line.
- [ ] Proved red: a violating input was blocked and a clean input passed, both observed directly.
- [ ] For a boundary rule, the deliberate-violation run was captured with the rule name in its output, and the enforcing command runs in CI.
- [ ] For a lint or formatter change, candidate rule sets were counted before being enabled, the autofix diff was read against the failure classes, and configuration plus autofix landed in a separate commit from any hand edit.
- [ ] Every ignore is scoped to the narrowest surface that works and records its reason inline.

## Requirements

- `bash`, `jq` — Claude Code / Codex runtime guards.
- `python3` — guard skeleton and `--selfcheck`.
- `git` — pre-commit `core.hooksPath` and `.githooks/guards.d/`.
- The repository's incumbent linter and formatter when tier-2 configuration applies. Consult the official documentation for the installed version before enabling a rule set, run that tool's documented version probe, and support only rule and fix behavior verified for that version.
- Dependency trigger — a linter or formatter release that changes a rule's fix behavior, or a runtime hook-event capability change, requires official-documentation review and a rerun of the affected proof before the recipe is trusted.
