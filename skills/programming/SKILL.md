---
name: programming
description: Guides correctness-first, type-strict Python and TypeScript implementation. Use when asked to write a `.py` or `.ts` file, scaffold a Python/TypeScript project, add strict types, assess an implementation diff for correctness or type holes, or fix a reproducible defect. Not for smell-only assessment or behavior-preserving restructuring — use refactor; not for suite-level test architecture — use testing.
metadata:
  version: 2.2.0
---

# programming

Write Python and TypeScript under one discipline: **correctness first, maintainability second, brevity third.** The type system is the proof, the test is the safety net, and the smallest code that satisfies both — never either alone — is the goal. Success looks like a clean type-check + lint pass, evidence for changed observable behavior, and each changed file considered against the LOC review signal below. `testing` owns suite-level architecture, while `refactor` owns smell-only review and behavior-preserving restructuring.

## Load the task-relevant reference first

Load only the references the task needs before touching code; a one-off script does not need every language guide.

| Scope | Read |
|---|---|
| Any implementation or code edit | `references/workflow.md` — understand → plan → change → verify → report, and the completion contract |
| `.py`, `.pyi`, or Python task | `references/python.md` — tooling table, iron list, data-modeling map |
| `.ts`, `.tsx`, `.mts`, `.cts`, or TypeScript task | `references/typescript.md` — tooling table, iron list, tsconfig flags; load `references/typescript/clean-code.md` when naming, function shape, or structure is in scope |
| Smell-only review | Route to `refactor`; it owns `references/code-smells.md` and the resulting restructuring |

## Write only what the task needs

Stop at the first rung that holds, after the correctness requirements are already known — this ladder never substitutes for them:

1. **Does this need to exist?** Speculative need → skip it, say so in one line (YAGNI).
2. **Does the codebase already have it?** Reuse the existing helper, util, or pattern — never rewrite it.
3. **Does the stdlib do it?** Use it.
4. **Does a native platform feature cover it?** `<input type="date">` over a date-picker library, CSS over JS layout, a DB constraint over an app-side check.
5. **Does an already-installed dependency solve it?** Use it; never add a dependency for what a few lines cover.
6. **Can it be one line?** One line.
7. **Only then:** the minimum code that works.

When two rungs hold, take the higher one. When two options are the same size, take the one correct on edge cases — fewer lines never means the flimsier algorithm. Validation at trust boundaries, error handling that prevents data loss, security, and accessibility are correctness, not brevity — never skimp on these.

Deletion beats addition, boring beats clever, fewest files wins — and a complex request earns one question before it earns code: "do you actually need X, or does Y already cover it?" A bug report names a symptom, not the cause: grep every caller of the function you touch and fix the shared function once — one guard there is a smaller diff than one per caller, and patching only the reported path leaves a sibling caller broken.

A deliberate shortcut carries a `craft:` comment naming its ceiling and upgrade path, so a reader sees intent, not ignorance:

```python
# craft: in-memory dedup, fine to ~10k ids; swap for a Redis set if this grows multi-process
```

## Core decisions

- Make illegal states unrepresentable when a bug can become a type error.
- Parse untrusted input into a typed value once at the boundary, then trust that contract internally.
- Give each concept its own type and name; match tagged variants exhaustively.
- Keep a change as one logical, independently reversible unit; split unrelated work rather than using file count as a proxy.

## The 250 pure LOC review signal

A source file over 250 pure LOC deserves a cohesion review, not an automatic split. Split it when independent responsibilities make the file hard to reason about; keep a cohesive unit intact when extraction would only scatter its contract. For an existing large file, improve the unit being touched when that is a bounded, clearer change rather than expanding the task to reorganize it. Generated tables and genuinely indivisible state machines may exceed the signal with a one-line justification comment.

Use the repository's incumbent measurement when it has one; otherwise this command gives a comparable pure-LOC count:

```bash
awk '!/^[[:space:]]*$/ && !/^[[:space:]]*(\/\/|#)/' <file> | wc -l
```

## TDD — red, green, refactor

Use red-first TDD when adding or changing observable behavior, or when risk warrants a regression net: write a failing Given/When/Then test, confirm it fails for the intended reason, then write the minimum code to pass. For a localized low-risk mechanical edit, run the cheapest credible verification instead of manufacturing a test.

For every reproducible defect, retain a failing-first regression test at the defect's natural layer before the fix makes it pass. Assert the contract, not the dump; prefer the real object, then an in-memory fake, then a wire-level fake. Mock only true unmockables (clock, randomness) at the narrowest seam, and inject a clock or subscribe to events instead of sleeping.
## Logging decisions

When adding logs, follow the project's established logging practice. Choose the level by the consumer's need, place logs at decisions rather than every step, and keep messages stable while putting variable context in structured fields. This is the transferable logging decision rule from [omo analysis](../../docs/research/omo-analysis.md).

## Requirements

Use the repository's incumbent package manager, type checker, linter, test runner, and LOC measurement first; use these defaults only when the project has no established equivalent:

- Python: `uv`, `basedpyright` (`typeCheckingMode = "all"`), `ruff` (`select = ["ALL"]`), `pytest`.
- TypeScript: `bun` (or `pnpm`), `tsc` (strict + `noUncheckedIndexedAccess` + `exactOptionalPropertyTypes` + `verbatimModuleSyntax`), `biome`.
- `awk` + `wc` for the fallback LOC measurement.

## Anti-patterns

- Skipping types on a throwaway script → use the smallest project-compatible setup; disposable code still needs an honest contract.
- Leaving a shortcut uncommented → mark it with a `craft:` comment naming its ceiling and upgrade path.
- Using `except Exception` / an empty `catch` that swallows the stack trace → catch specific exceptions and handle or log them explicitly.
- Introducing an interface/Protocol with exactly one implementation, or a factory for one product → use the concrete type directly until a second implementation exists.
- Adding `# type: ignore` / `@ts-ignore` with no explanation → fix the type, or add a comment explaining why the escape hatch is unavoidable.
- Logging every operation or interpolating unstable context into messages → log decision points with stable messages and structured fields.

## Verification

- [ ] Task-relevant references were read before writing code.
- [ ] The [core decisions](#core-decisions), [LOC review signal](#the-250-pure-loc-review-signal), and relevant [TDD](#tdd--red-green-refactor) or [logging](#logging-decisions) guidance were applied.
- [ ] The incumbent type checker, linter, and focused verification pass clean.
