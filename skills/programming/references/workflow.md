# Task workflow reference

How to carry a coding task from request to done without guessing, faking, or leaving a mess. Load this on every code task. The rules are tool-agnostic: where a specific capability is named (find-references, rename, structural search), use whatever your environment provides for it.

## The loop

```
understand → plan → change → verify → report
```

Never skip straight to `change`. Never stop before `verify`. Each step below expands one stage.

## 1. Understand before you touch

- **Locate, don't guess.** Find the exact file and symbol first. Do not open files at random hoping to land on the right one.
- **Read the target and its neighbours.** Read the section you will change and the code around it. Read sections, not whole files, when the file is large.
- **Reuse the local pattern.** Match how the surrounding code already does the thing (naming, error style, structure). A second, parallel way of doing one thing is a defect — it splits every future change in two.
- **Confirm the contract.** Before changing an exported or public symbol, find every reference to it. The change is not "edit this function" — it is "edit this function and every caller."

## 2. Use the right instrument

- **Symbol-aware operations use symbol-aware tools.** Go-to-definition, find-references, and rename belong to the language server / IDE intelligence — not to text search-and-replace. A cross-file rename done by hand-editing each occurrence misses shadowed names, re-exports, and usages in files you forgot.
- **Search by shape when shape matters.** When you are looking for a code construct (a call form, a declaration), use structural / AST search. Use plain text or regex search only when structure is irrelevant.
- **Re-read on staleness.** If a tool fails, a command errors, or a file may have changed since you last read it, read it again before acting. Acting on a stale mental model corrupts the change.

## 3. Change with the blast radius in mind

The *blast radius* of a change is everything that must move with it. A change is unfinished until its whole radius is handled.

- **Update every callsite, test, and doc** the change touches — or state explicitly why one is intentionally left unchanged.
- **Fix at the source.** When a value is wrong upstream, fix it upstream; do not patch each downstream symptom.
- **Delete obsolete code.** Remove the dead function, the unused branch, the old alias — do not leave it behind "just in case". Comments that describe code that no longer exists are noise.
- **Prefer editing an existing file** over creating a new one. A new file is justified by a new responsibility, not by reluctance to touch the old one.

## 4. Decompose and delegate

- **Three or more distinct steps → track them.** Write the steps down and complete them in order; mark each done before starting the next. Do not hold a multi-step plan only in your head.
- **Large or parallelizable work → delegate bounded slices**, if your environment supports sub-tasks. Hand off concrete, file-scoped pieces; keep integration and final verification for yourself. Delegating is the alternative to silently shrinking the task to what is easy.
- **Never silently shrink scope.** If the full task is too large, say so and split it — do not quietly deliver a fraction and present it as the whole.

## 5. The completion contract

These are absolute. Breaking any one of them makes the work untrustworthy even when it looks finished.

- **Never present partial work as complete.**
- **Never fabricate.** No invented command output, test result, or source fact. If you did not run it, did not read it, or are inferring it, say exactly that.
- **Never ship a placeholder as a feature.** No stub, no-op, fake fallback, hardcoded "sample" answer, or TODO-only body delivered as a working feature.
- **Never substitute an easier problem.** Solve the task that was asked, not the adjacent one that is convenient.
- **Never suppress to go green.** Do not silence a warning, skip or delete a failing test, or weaken an assertion to make a build pass. A green build bought that way is a lie.
- **Verification claims must match what was actually run.** "Tests pass" means you ran them and saw them pass.

## 6. Verify

- **Run the specific check that exercises your change** — the unit test, the command, the scenario — not a vague "looks right". "Run the test and read the output" beats "the code looks correct".
- **Test observable behavior**, not internals: the value returned, the state changed, the error raised. Cover the happy path, the edge values, each branch condition, and the error path.
- **Do not test tautologies.** A test that asserts a default equals itself, or that a mock returns what you told it to, proves nothing. Delete it.
- **If verification is genuinely impossible**, state plainly why (no runtime, no fixture, external dependency) instead of claiming success.

## 7. Repo safety

You are not alone in the repository. Treat anything you did not change as a teammate's in-progress work.

- Never revert, stash, commit, push, or delete changes you did not make, unless explicitly asked.
- When you see unexpected edits, leave them; do not "clean up" someone else's work to clear your path.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The code looks correct, no need to run it." | Looking correct and being correct diverge exactly where the bugs live. Run the check. |
| "I'll just update this function; callers are fine." | A signature or behavior change ripples to callers. Find references first; update the whole radius. |
| "A stub unblocks the rest; I'll fill it later." | A stub presented as done is a hidden failure. Either implement it or report it as not-done. |
| "Tests are failing for an unrelated reason, I'll skip them." | A skipped test is a removed bug report. Diagnose it; do not silence it. |
| "Text replace is faster than a proper rename." | Text replace misses shadowing, re-exports, and other files. Use a symbol-aware rename. |
| "This new `utils.ts` is the easy place to put it." | A catch-all file relocates the mess. Put the code with the responsibility it belongs to. |
| "It mostly works; close enough to done." | Partial work presented as complete breaks trust. Report what works and what does not. |
| "Someone else's stray change is in my way, I'll revert it." | That is a teammate's work. Leave it; route around it or ask. |

## Red Flags

- A "done" or "passing" claim with no command output behind it.
- An edit to an exported symbol with no check of its references.
- A new file named `utils`, `helpers`, `common`, `misc`, or `temp`.
- A test that was skipped, deleted, or weakened to make the suite pass.
- A function body that is `pass` / `return null` / `throw new Error("TODO")` in delivered work.
- A described result ("the output shows…") that was never actually produced.
- Obsolete code or stale comments left behind after a change.

## Verification

- [ ] The exact target was located and read before editing — not guessed at.
- [ ] Every reference to a changed exported symbol was found and updated.
- [ ] The change's full blast radius (callsites, tests, docs) is handled or explicitly excused.
- [ ] The specific test/command exercising the change was run, and the claim matches the observed output.
- [ ] No fabricated output, no stub-as-feature, no suppressed warning or skipped test.
- [ ] No unexpected teammate changes were reverted, committed, or deleted.
