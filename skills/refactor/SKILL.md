---
name: refactor
description: '"refactor this", "리팩토링 해줘", "clean up this code", "is this a code smell?" — behavior-preserving restructuring: when-to-refactor triggers, a legacy/untested-code safety protocol (characterization tests), a mechanical code-smell detection catalog, and a 12-move refactoring catalog. Routes to references/code-smells.md, references/catalog.md, and scripts/detect-smells.sh.'
version: 1.0.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
compatibility: claude-code, codex
---

# refactor

**Behavior first, always: a refactor changes how code is organized, never what it does — the moment behavior changes, it's a feature or a fix, not a refactor.**

## Overview

This skill is an index. Its signature move is mechanical detection: every smell below ships a copy-pasteable command with a threshold, never a vague "this looks off." Shared rules live here; the smell catalog, the move catalog, and the detection script live in `references/` and `scripts/` — load them before acting.

## When to Use

- "refactor this", "clean up this code", "this function is a mess", "리팩토링 해줘", or spotting a named smell (long function, duplicated logic, deep nesting) while reading code.
- Restructuring a file, module, or class with no intended behavior change.
- Preparing a codebase for an upcoming feature ("make the change easy, then make the easy change").

Do NOT use for adding a feature, fixing a bug, or any change where the observable behavior is meant to differ afterward — that is `programming`'s red-green-refactor loop, not this skill. A change that genuinely needs both belongs to two separate commits (see Safety Protocol), never one.

## PHASE 0 — is refactoring warranted? (gate)

Do not restructure a line of code before this gate.

| Trigger | Recognize it by | Action |
|---|---|---|
| Rule of three | This is the THIRD time the same shape is copied | Extract now — not the first or second time; earlier is premature abstraction, its own smell |
| Preparatory refactoring | The feature about to be added is hard because of the current shape | Refactor first, in its own commit; add the feature second, in a separate commit |
| Comprehension refactoring | The code had to be read twice, or annotated with a scratch comment, to be understood | Rename/extract while the understanding is fresh — don't just move on |
| Boy-scout opportunistic | Already in a file for unrelated work, and an unrelated smell is visible | Fix ONLY if trivial and local to the lines already touched; anything larger → flag it and STOP — never expand scope via a drive-by refactor |

Safety preconditions — all must hold before touching structure:

1. A test suite exists for the code path and is green right now. Run it; do not trust memory.
2. If step 1 fails because there is no coverage for this path → STOP. Go to the Legacy/Untested Code Safety Protocol below FIRST. Restructuring un-pinned behavior is a guess, not a refactor.
3. The working tree is clean, or the refactor is isolated on its own commit lineage — never mixed with in-flight feature work.

## Legacy/Untested Code Safety Protocol — characterization tests

Refactoring code with no test coverage, without doing this first, is how "harmless cleanup" silently changes behavior.

1. **Find the untested surface.** Run coverage against the target and read the gaps:
   ```bash
   uv run pytest --cov=<package> --cov-report=term-missing <path>   # Python
   npx vitest run --coverage                                        # TypeScript
   ```
2. **Write characterization tests first.** Call the code with representative inputs — including the odd, already-in-production ones — and assert on the actual observed output, not the output assumed to be correct. Ugly-but-true beats pretty-but-guessed: `assert compute(weird_input) == 47` is the right test if `47` is genuinely what today's code returns, even if `47` looks wrong.
3. **Get the characterization tests green against current behavior.** They pin what the code does now, bugs included — they are not yet a bug fix.
4. **Only then refactor**, keeping every characterization test green after each step of the Safety Protocol below.
5. **A real bug surfaces while characterizing?** Do not fix it in the same pass. Flag it (a comment plus a note to the user, or a separate issue) and keep this pass scoped to preserving behavior — unless the task at hand IS "fix this bug," in which case that is its own red-green-refactor cycle via `programming`, run before or after the restructuring, never blended into it.

## Safety Protocol — behavior-preserving steps

1. Tests green before starting (from PHASE 0, or from characterization above).
2. One mechanical move at a time, from `references/catalog.md` — never combine two moves into one step.
3. Run the test suite after every step. Red → revert that one step immediately; never debug forward on top of a refactor that just broke something.
4. **Refactor commits stay separate from behavior commits, always.** A commit that both restructures code and changes what a test asserts is two changes wearing one commit message.

Detect a commit mixing the two before it lands:

```bash
git diff --staged -- '*test*' '*spec*' '*_test.*' '*.test.*' | grep -E '^[+-][^+-].*\b(assert|expect)\b'
```

Any output here on a commit being called "refactor" means a test's expected behavior changed — split the commit: the assertion change is a behavior commit, the rest is the refactor commit.

## Scope Guard

- A refactor commit or PR touches at most ~10–15 files before it needs a split into a stack of smaller ones:
  ```bash
  git diff --stat main...HEAD | tail -1
  ```
- Boy-scout boundary, restated as a hard rule: spotting an unrelated smell while working on task X is never license to fix it inline. Flag it — a comment, a `craft:`-style note, or a message to the user proposing a follow-up — and keep task X's diff scoped to task X.

## Routing

- Which smell, which command, which threshold → `references/code-smells.md` (the detection catalog — load this before calling anything a "smell").
- Which mechanical move fixes which smell → `references/catalog.md`.
- A one-shot terminal scan across a whole directory → `scripts/detect-smells.sh <dir>` (reporter, not a gate — always exits 0; read every finding before acting, false-positive profile documented per rule).
- File-size ceiling (250 pure LOC) and its escape hatches → the `programming` skill; this skill owns function-level size, not file-level.
- Turning any rule below into an enforced pre-commit/lint/hook check → the `hookify` skill.

## Requirements

- `git` — co-change/churn detection, the refactor/behavior commit-separation check.
- `grep`, `awk`, `find` (POSIX) — used directly and inside `scripts/detect-smells.sh`.
- A test runner for the language in play: `pytest` (+ `pytest-cov`) for Python, `vitest` (`--coverage`) for TypeScript.
- Optional, per `references/code-smells.md`'s Dead Code entry: `vulture` (Python), `ts-prune` (TypeScript).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'm already in here, might as well fix everything I see." | That's drive-by scope creep. Flag anything beyond the trivial and local — a bigger diff hides the actual change under unrelated noise. |
| "It's just a rename, I'll bundle it with the fix." | A rename is a refactor commit; a fix is a behavior commit. Bundling them means reverting one reverts the other. |
| "There's no time for characterization tests, I already know what it does." | "I know what it does" is exactly the guess this protocol replaces with an assertion. Untested legacy code has surprised every engineer who was sure. |
| "Two duplicates is basically three, I'll extract now." | Rule of three means three. The second occurrence is exactly when the right shape for the abstraction still isn't known. |
| "The tests still pass, so the commit is fine as one." | Passing tests don't prove the commit is ONE change — check whether any assertion's expected value moved; if it did, split the commit. |
| "It's a huge mess, so the PR has to be huge too." | Restructure in a stack of small, independently revertible commits/PRs instead — see Scope Guard. |

## Red Flags

- A "refactor" commit whose diff also changes what a test asserts (run the detection command above).
- Restructuring a function with zero test coverage and no characterization tests written first.
- A PR/commit touching far more files than the stated task, with no flag or follow-up noted.
- The same code duplicated a second time and already being "extracted just in case" — that's speculative generality, not the rule of three.
- A smell fixed with a catalog move applied all at once, tests only checked at the very end.

## Verification

- [ ] PHASE 0 gate passed: trigger identified, tests confirmed green (or the characterization protocol completed first).
- [ ] Every step used exactly one move from `references/catalog.md`, with tests run after each.
- [ ] No commit mixes a structural change with a change to a test's asserted behavior (checked with the detection command).
- [ ] Any smell fixed cites its `references/code-smells.md` entry and the detection command's result.
- [ ] Scope stayed within the stated task; any spotted-but-out-of-scope smell was flagged, not fixed inline.
- [ ] `scripts/detect-smells.sh` run on the touched directory at least once, findings reviewed rather than blindly auto-fixed.
