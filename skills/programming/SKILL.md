---
name: programming
description: Applies correctness-first, type-strict engineering discipline when writing or editing Python or TypeScript. Use when asked to write a `.py` or `.ts` file, scaffold a new Python/TypeScript project, add strict types to existing code, or review a diff for over-engineering, type holes, or an oversized file. Routes to `references/python.md` or `references/typescript.md` for the per-language iron list, plus the always-loaded `references/workflow.md` task discipline. Not for suite-level test architecture (use testing) or behavior-preserving restructuring of already-working code (use refactor).
metadata:
  version: 2.0.0
---

# programming

Write Python and TypeScript under one discipline: **correctness first, maintainability second, brevity third.** The type system is the proof, the test is the safety net, and the smallest code that satisfies both — never either alone — is the goal. Success looks like a clean type-check + lint pass, a test that locks the new behavior in, and every changed file inside the LOC ceiling below. `testing` owns suite-level architecture and `refactor` owns behavior-preserving restructuring of existing code; this skill owns writing and editing the code itself.

## Load the reference first

Read the matching file in full before writing or editing a line — including a one-off or throwaway script; `uv run` + PEP 723 (Python) and `bun run` (TypeScript) make full discipline free even for disposable code.

| Scope | Read |
|---|---|
| Every code task, always | `references/workflow.md` — understand → plan → change → verify → report, and the completion contract (no fabrication, no placeholder-as-feature, no suppressing to go green) |
| `.py`, `.pyi`, or "Python" | `references/python.md` — tooling table, iron list, data-modeling map |
| `.ts`, `.tsx`, `.mts`, `.cts`, or "TypeScript" | `references/typescript.md` — tooling table, iron list, tsconfig flags |

## Write only what the task needs

Stop at the first rung that holds, after the correctness requirements are already known — this ladder never substitutes for them:

1. **Does this need to exist?** Speculative need → skip it, say so in one line (YAGNI).
2. **Does the stdlib do it?** Use it.
3. **Does a native platform feature cover it?** `<input type="date">` over a date-picker library, CSS over JS layout, a DB constraint over an app-side check.
4. **Does an already-installed dependency solve it?** Use it; never add a dependency for what a few lines cover.
5. **Can it be one line?** One line.
6. **Only then:** the minimum code that works.

When two rungs hold, take the higher one. When two options are the same size, take the one correct on edge cases — fewer lines never means the flimsier algorithm. Validation at trust boundaries, error handling that prevents data loss, security, and accessibility are correctness, not brevity — never skimp on these.

A deliberate shortcut carries a `craft:` comment naming its ceiling and upgrade path, so a reader sees intent, not ignorance:

```python
# craft: in-memory dedup, fine to ~10k ids; swap for a Redis set if this grows multi-process
```

## Shared philosophy

1. **The type system is your proof system.** Make illegal states unrepresentable — if a bug can be a type error, it must be one.
2. **Parse, don't validate.** Untrusted input is parsed into a typed value once, at the boundary; inside it, code never re-validates.
3. **One name = one concept.** Brand every distinct primitive (`NewType` / branded type) — a `UserId` is not a bare `str`/`string`.
4. **Exhaustive variant matching.** Discriminated unions and enums are matched with `match`/`assert_never` or `switch`/`assertNever`; `if`/`elif`/`else` on a tagged variant is banned — it silently swallows new variants.
5. **Trust the type system past the boundary.** No null check for a value the type proves non-null, no escape hatch (`any`, `cast`, `!`, `# type: ignore`, `@ts-ignore`) papering over a contract that belongs in types.
6. **Test-driven.** No production line ships without a failing test that proved it was needed.

## The 250 pure LOC ceiling

A source file whose pure LOC (non-blank, non-comment) exceeds 250 is architecturally broken, not a style call — past 250 a reviewer stops holding the whole file in working memory.

```bash
awk '!/^[[:space:]]*$/ && !/^[[:space:]]*(\/\/|#)/' <file> | wc -l
```

Creating a file that will exceed 250 → split by responsibility before the first commit. Editing one already over → extract the unit you're touching first. Reading one while building a feature → surface the smell and propose a split, don't pile on. Split by what each file *does*; a catch-all (`utils.py`, `helpers.ts`, `common.py`) relocates the smell. A genuinely indivisible unit (a generated table, one state machine) may exceed the ceiling with a one-line justification comment.

## TDD — red, green, refactor

1. **Red.** Write a failing test naming the behavior in Given/When/Then; confirm it fails for the right reason (missing behavior, not an import typo).
2. **Green.** Write the minimum code to pass. The next case is the next red.
3. **Refactor.** With the test green, restructure freely — the test is the net.

Assert the contract, not the dump — the value, not `is not None`. Prefer the real object, then an in-memory fake, then a wire-level fake (`respx`/`msw`); mock only true unmockables (clock, randomness) at the narrowest seam. Inject a clock and subscribe to events instead of `sleep`.

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
| "`if`/`elif` on the enum is clearer." | It silently swallows the next variant. `match`/`switch` + an exhaustiveness check fails the build instead. |
| "The file is 240 lines, close enough." | A file about to grow past the ceiling is already over. Split now; don't race it. |
| "I'll add the test after." | Tests-after rationalize the design already written. Red first, always. |
| "It's an obvious shortcut, no comment needed." | An unmarked shortcut reads as a bug to the next person. Mark it `craft:` with its ceiling. |

## Red Flags

- A `dict[str, Any]` / `unknown` flowing past the boundary into business logic.
- `except Exception` / an empty `catch` swallowing a stack trace.
- A new file named `utils`, `helpers`, `common`, `shared`, or `misc`.
- An interface/Protocol with exactly one implementation, or a factory for one product.
- A `# type: ignore` / `@ts-ignore` with no explanation.
- A shortcut with no `craft:` comment.
- A feature with passing unit tests but no test that fails when the behavior is reverted.

## Verification

- [ ] The matching reference (`python.md` / `typescript.md`) was read before writing code.
- [ ] Every changed file is ≤250 pure LOC (or carries a justified exception) and names one responsibility.
- [ ] Boundaries parse untrusted input into typed values; no `Any`/`unknown` leaks inward.
- [ ] Every tagged-variant branch is an exhaustive `match`/`switch` with `assert_never`/`assertNever`.
- [ ] No unexplained escape hatch, and no dead null-check/try-except guarding an already-proven value.
- [ ] No one-off helper/class introduced for a single caller.
- [ ] Every deliberate shortcut carries a `craft:` comment with its ceiling and upgrade path.
- [ ] New behavior is locked by a test that fails when the change is reverted.
- [ ] Type checker + linter pass clean (`basedpyright` + `ruff` / `tsc` + `biome`).
