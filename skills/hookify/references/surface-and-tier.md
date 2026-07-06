# Enforcement Surface Selection and Tier Grading

The point of enforcement is not preventing permanent harm — it's giving an agent (or a human) a deterministic "you are wrong" signal. So the axis for picking a surface is signal delay × clarity × confidence, not reversibility. For the same rule, use the earliest local surface available.

## Enforcement Surface Ladder (local-first, earliest first)

| Tier | Surface | Fires | Enforces | Fits |
|---|---|---|---|---|
| 0 | Prose (`AGENTS.md` / `CLAUDE.md`) | Read as context before work | Nothing — prevention only | Every rule is stated here first |
| 1 | **Agent runtime hook** (Claude Code PreToolUse/PostToolUse, Codex hook) | Immediately before/after a tool call, in-loop | Blocks the behavior itself | Forbidden-path edits, dangerous commands, read-only mutation |
| 2 | **lint** (editor/local, continuous) | Any time, continuously | Fast feedback (advisory → autofix) | Style/quality the agent runs repeatedly |
| 3 | **pre-commit hook** (local) | At commit time | Blocks the commit | Irreversible: secrets, direct commits to a protected branch, large blobs |
| (backstop) | CI | After push | Blocks the merge | Whoever skipped local — not hookify's focus |

Tier 1 is the fastest deterministic signal — earlier than pre-commit, before the agent has *done* the thing. It's the end of local enforcement.

## Surface Selection Procedure

Given one rule, in order:

1. **State it in prose first.** Put the norm in context without enforcement (tier 0). Enforcement is the backstop for where prose failed.
2. **Pick the earliest local surface that catches it deterministically.** A violation expressed in the agent's tool behavior (edited path, command) → tier 1. File-content quality → tier 2 (lint). Irreversible only once committed → tier 3.
3. **Author and install a starter guard.** Make sure the message states the violated rule and the fix *clearly*.
4. **Prove it blocks, for real.** Run a violating input → blocked, a clean input → passes, and watch both happen directly. An installed guard nobody has seen fire is unfinished.

## 3-Gate Graduation Check — does this rule earn a blocking hook?

A hook is an **amplifier**. It only amplifies the quality of whatever check runs inside it — the concept itself carries no quality. A good rule becomes inevitable; a bad one becomes a tax on every firing. A blocking hook (tier 1 or 3) is a **graduation, not a starting point.** Put a rule behind one only once it passes all three gates:

- **G1 — Cheap:** the check is fast and doesn't depend on external state (network, live backend).
- **G2 — Accurate:** near-zero false positives. **If the guard itself needs a test suite, it has already become application code** — the wrong tier. Drop it to a softer surface.
- **G3 — Stable:** the structure being enforced has stopped drifting. If the rule is still evolving, keep it as a non-blocking lint warning or in prose, and observe.

Any single failure disqualifies it from a blocking hook. *Observe* it on an earlier/softer surface until it's proven cheap, accurate, and stable — then graduate it.

```
prose (stated) → lint warning / non-blocking (observe, tune) → blocking hook (only once proven)
```

## Trust Budget

A blocking hook spends from a finite **trust budget**. One false positive on legitimate work and a human reaches for `--no-verify`, an agent reaches for a workaround — and that erodes trust in every hook, not just the one that misfired. A hook's power comes from never being bypassed.

So:

- **Few and sharp.** Don't grow a guard's coverage for its own sake — every addition spends from the budget.
- **Spend it on irreversibles.** Late-but-before-permanent is the right timing for tier 3 (secrets, protected branches) — that's its legitimate slot.
- **The message builds the trust.** A vague block reason gets bypassed. State the violated rule and the exact fix, in one line.

## Enforcement Mechanism per Surface

- **Claude Code runtime hook:** register a matcher + command per event (`PreToolUse`, etc.) under `hooks` in `settings.json`. The command receives the tool-call JSON on stdin and blocks on violation. Detail and examples: `references/claude-code-hooks.md`; starters: `scripts/`.
- **Codex runtime hook:** Codex CLI's hook/notify mechanism. Detail: `references/codex-hooks.md`.
- **lint:** add the rule to the project's linter (ruff/eslint, …), or wrap a domain rule in a guard script exposed as a command the agent runs during work.
- **pre-commit:** hookify owns `core.hooksPath` as the single install point — `scripts/pre-commit.sh` is the committed dispatcher. It runs every executable file in `.githooks/guards.d/` in lexical order and carries no rule logic itself; a guard registers by dropping an executable script there, never by setting `core.hooksPath` itself.
