---
name: programming
description: '"write/edit Python or TypeScript", "refactor this module", "review strict TS or Python types", "fix code smells", "split an oversized file" — correctness-first code work for Python and TypeScript, routed through a PHASE 0 surface/language gate, shared workflow, per-language references, and code-smell checks.'
version: 1.2.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
compatibility: claude-code, codex
---

# programming

Write Python and TypeScript under one discipline: **correctness first, maintainability second, brevity third.** The type system is the proof; the test is the safety net; the smallest code that satisfies both is the goal — in that order, never reordered.

## Overview

This skill is an index. Shared rules live here; the hard per-language iron list lives in `references/`. Load the matching reference before writing a line of code. Brevity is the byproduct of writing only what the task needs — it is never bought by cutting validation, error handling, security, or accessibility.

## When to Use

- Writing or editing any `.py`, `.pyi`, `.ts`, `.tsx`, `.mts`, `.cts` file — including one-off scripts.
- Touching a manifest: `pyproject.toml`, `package.json`, `tsconfig.json`, `biome.json`.
- Starting a new Python or TypeScript project.
- Reviewing code for over-engineering, type holes, escape hatches, code smells, or oversized files.
- Refactoring pure code, libraries, CLIs, scripts, tests, or shared modules.

Do not use for Rust, Go, shell, or config-only languages — this skill covers Python and TypeScript only. If UI/UX or backend contracts dominate the task, load `frontend` or `backend` as the surface owner and keep this skill for language-level discipline.

## PHASE 0 — surface and language gate (run first, every time)

Do not write or edit a line of code before this gate.

1. Identify the surface:
   - UI/UX, accessibility, visual QA, frontend performance, or component behavior → load `frontend` as the surface owner, then continue here for Python/TypeScript edits.
   - API/RPC, database, auth/secret, background job, queue, or observability work → load `backend` as the surface owner, then continue here for Python/TypeScript edits.
   - Pure library, CLI, script, test, refactor, or language-level correctness work → stay in this skill.
2. Identify the language from the file extension or the request.
3. STOP and read the matching reference in full:

   | Scope | Read |
   |---|---|
   | Every code task (always) | `references/workflow.md` — the task procedure |
   | `.py`, `.pyi`, "Python" | `references/python.md` |
   | `.ts`, `.tsx`, `.mts`, `.cts`, "TypeScript" | `references/typescript.md` |

4. Check the code-smell triggers below before adding lines.
5. Apply the shared philosophy below plus the per-language iron list from the reference.

No exception for "small" or "throwaway" code. `uv run` + PEP 723 (Python) and `bun run` (TypeScript) make disposable scripts cost nothing to write with full discipline.

## Code-smell triggers

Treat these as activation triggers for refactor pressure, not as permission to broaden the task beyond the requested behavior.

| Trigger | Required response |
|---|---|
| File will cross 200 pure LOC | Plan the split before adding code; crossing 250 is a defect unless the file is indivisible and justified. |
| New helper has one caller | Inline it unless it names a real domain concept or is the seam under test. |
| New dependency is proposed | Re-check stdlib, platform, and installed dependencies first. |
| `Any`, `unknown`, `cast`, `!`, `# type: ignore`, or `@ts-ignore` appears | Encode the contract in types or leave a narrow, explained escape hatch only when no type-safe option exists. |
| A tagged variant is matched by `if`/`elif` or non-exhaustive `switch` | Replace with exhaustive matching. |
| Validation repeats inside business logic | Move parsing to the trust boundary and pass typed values inward. |

## Working discipline (non-negotiable, every task)

The task procedure in `references/workflow.md` is mandatory; these invariants are the part that must hold even when that file is not in front of you.

- **Understand before you touch.** Locate the exact target and read it; reuse the patterns already in the file instead of inventing a parallel one.
- **Verify before you claim done.** Run the specific test or command that exercises your change. A "done" / "passing" claim must match what you actually ran — never describe a result you did not observe.
- **Never fabricate.** No invented command output, test results, or source facts. If you did not run it or did not read it, say so.
- **Never ship a placeholder as a feature.** No stub, no-op, fake fallback, or TODO-only code presented as complete work.
- **Finish the blast radius.** Update every callsite, test, and doc the change touches — or state explicitly why one is left unchanged. Before changing an exported symbol, find its references first.
- **Fix at the source; never suppress.** Do not silence a warning, skip a test, or delete a failing assertion to go green. Remove obsolete code rather than leaving dead aliases.
- **Respect the repo.** Unexpected changes are a teammate's work — never revert, stash, commit, or delete them to clear your path.

## The write-only-what-the-task-needs ladder

Before adding code, stop at the first rung that holds. The ladder runs *after* the correctness requirements are known, never instead of them.

1. **Does this need to exist?** Speculative need → skip it, say so in one line (YAGNI — you aren't gonna need it).
2. **Does the stdlib do it?** Use it.
3. **Does a native platform feature cover it?** Use it: `<input type="date">` over a date-picker library, CSS over JS layout, a DB constraint over an app-side check, `URL` / `Intl` / `structuredClone` / `pathlib` over a dependency.
4. **Does an already-installed dependency solve it?** Use it. Never add a new dependency for what a few lines cover.
5. **Can it be one line?** One line.
6. **Only then:** the minimum code that works.

Two rungs both hold → take the higher one and move on. When two options are the same size, take the one that is correct on edge cases — fewer lines never means the flimsier algorithm.

### Never lazy about

Validation at trust boundaries, error handling that prevents data loss, security, accessibility, and anything explicitly requested. These are correctness, and correctness outranks brevity. When the user wants the full version, build it — no re-arguing.

### craft: annotation (mandatory for every deliberate shortcut)

A deliberate simplification carries a `craft:` comment so a reader sees intent, not ignorance. When the shortcut has a known ceiling — a global lock, an O(n²) scan, a naive heuristic — the comment names the ceiling and the upgrade path.

```python
# craft: in-memory dedup, fine to ~10k ids; swap for a Redis set if this grows multi-process
```
```typescript
// craft: linear scan, n is the nav menu (<50); index by id if this ever holds a dataset
```

An unmarked shortcut is indistinguishable from a bug. A marked shortcut is a decision.

## Shared philosophy (Python and TypeScript)

1. **The type system is your proof system.** Make illegal states unrepresentable. If a bug can be expressed as a type error, it is required to be a type error.
2. **Parse, don't validate.** Untrusted input crosses a boundary once, where it is parsed into a typed value (Pydantic v2 / Zod). Inside the boundary, code receives typed values and never re-validates.
3. **One name = one concept.** A `UserId` is not a `str`/`string`. Brand every distinct semantic primitive (`NewType` / branded type). The checker refuses to let two units mix.
4. **Exhaustive variant matching.** Discriminated unions and enums are matched exhaustively — `match` + `assert_never` (Python), `switch` + `assertNever` (TypeScript). `if`/`elif`/`else` on a tagged variant is banned; it silently swallows new variants.
5. **Trust the type system; validate only at boundaries.** No null check for a value the type proves non-null. No `try`/`catch` around code that cannot throw. No escape hatch (`any`, `cast`, `unwrap`, `!`, `# type: ignore`, `@ts-ignore`) papering over a contract you should have encoded in types.
6. **Test-driven.** No production line ships without a failing test that proved it was needed.

## The 250 pure LOC ceiling

A source file whose pure LOC (non-blank, non-comment) exceeds 250 is architecturally broken — a defect, not a style preference. At 250 a reviewer still holds the whole file in working memory; past it they stop trying.

- **Creating** a file that will exceed 250 → split it before the first commit, by responsibility (one cohesive unit per file). Barrels (`__init__.py`, `index.ts`) re-export only; never hold logic.
- **Editing** a file already over 250 and adding lines → extract the unit you are touching into its own file first.
- **Reading** one over 250 while building a feature → surface the smell, propose a concrete split, do not silently pile on.

Measure pure LOC:

```bash
awk '!/^[[:space:]]*$/ && !/^[[:space:]]*(\/\/|#)/' <file> | wc -l
```

Split by what each file *does*, never by token count (`utils_2.ts`). Catch-all dumps (`utils.py`, `helpers.ts`, `common.py`, `shared.ts`) just relocate the smell — reject them. A genuinely indivisible unit (a generated table, a single state machine) may exceed the ceiling with a one-line justification comment.

## TDD — red, green, refactor

1. **Red.** Write a failing test naming the behavior in Given / When / Then. Run it; confirm it fails for the *right* reason (the function does not exist yet — not an import typo).
2. **Green.** Write the minimum code to pass. The second case is the next red.
3. **Refactor.** With the test green, restructure freely; the test is the net.

- Assert the contract, not the dump: assert the value, not `is not None`. One `When` per test.
- Less mock, the better: prefer the real object, then an in-memory fake, then a wire-level fake (`respx` / `msw`), and only mock true unmockables (clock, randomness) at the narrowest seam. A test that fails when the implementation changes but the behavior did not is over-mocked.
- Deterministic: inject a clock and subscribe to events — never `sleep`.

## Post-write review loop (run before declaring done)

For every file created or modified:

1. **Size.** Pure LOC ≤ 200 healthy; 200–250 warn and plan a split; > 250 defect — split now.
2. **Single responsibility.** Can you name what the file owns in one noun phrase without "and"? If not, split.
3. **Boundary purity.** Untrusted input parsed into a typed value at the boundary — not passed deeper as `dict[str, Any]` / `unknown`?
4. **Exhaustiveness.** No `if`/`elif`, and no `switch` without `assertNever`, discriminating a tagged type?
5. **Escape hatches.** No `any`, `cast`, `# type: ignore`, `!`, `@ts-ignore`, `@ts-expect-error`? Each survivor is fixed or carries a comment saying why.
6. **Dead defense.** No null check / try-except guarding a value the type already proves?
7. **One-off helper.** No function/class introduced for a single caller that will never get a second?
8. **craft: annotations.** Every deliberate shortcut is marked with its ceiling and upgrade path?
9. **Test.** The new behavior is locked by a test that fails if you revert the change?

Any answer fails → fix it before declaring done.

## Requirements

- Python: `uv`, `basedpyright` (`typeCheckingMode = "all"`), `ruff` (`select = ["ALL"]`), `pytest`.
- TypeScript: `bun` (or `pnpm`), `tsc` (strict + `noUncheckedIndexedAccess` + `exactOptionalPropertyTypes` + `verbatimModuleSyntax`), `biome`.
- `awk` + `wc` for the LOC measurement.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's a throwaway script, skip the types." | `uv run` + PEP 723 and `bun run` give full discipline at zero setup cost. Throwaway code still reaches production once. |
| "Fewer lines is the goal." | Correctness is the goal; fewer lines is the byproduct. Never cut validation, security, or error handling to shrink a diff. |
| "`any` / `cast` just here to ship." | The escape hatch hides the bug the type system was about to catch. Encode the contract in the type. |
| "`if/elif` on the enum is clearer." | It silently swallows the next variant. `match` / `switch` + an exhaustiveness check fails the build instead. |
| "The file is 240 lines, close enough." | A 240-line file about to grow is already over. Split now; do not race the ceiling. |
| "I'll add the test after." | Tests-after rationalize the design you already wrote. Red first, always. |
| "It's an obvious shortcut, no comment needed." | An unmarked shortcut reads as a bug to the next person. Mark it `craft:` with its ceiling. |

## Red Flags

- A `dict[str, Any]` / `unknown` flowing past the boundary into business logic.
- `except Exception` / an empty `catch` swallowing a stack trace.
- A new file named `utils`, `helpers`, `common`, `shared`, or `misc`.
- An interface / Protocol with exactly one implementation, or a factory for one product.
- A `# type: ignore` / `@ts-ignore` with no explanation.
- A shortcut with no `craft:` comment.
- A feature with passing unit tests but no test that fails when the behavior is reverted.

## Verification

- [ ] PHASE 0 surface owner was selected and the matching language reference was read before writing code.
- [ ] Every changed file is ≤ 250 pure LOC (or carries a justified exception comment).
- [ ] Boundaries parse untrusted input into typed values; no `Any` / `unknown` leaks inward.
- [ ] Every tagged-variant branch is an exhaustive `match` / `switch` with `assert_never` / `assertNever`.
- [ ] No unexplained escape hatch (`any`, `cast`, `# type: ignore`, `!`, `@ts-ignore`).
- [ ] Every deliberate shortcut carries a `craft:` comment with ceiling + upgrade path.
- [ ] New behavior is locked by a test that fails when the change is reverted.
- [ ] Type checker + linter pass clean (`basedpyright` + `ruff` / `tsc` + `biome`).
