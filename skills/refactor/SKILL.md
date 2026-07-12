---
name: refactor
description: "Restructures code without changing what it does — extracting functions, renaming, removing duplication, flattening nested conditionals, and other mechanical moves backed by a detection command and threshold. Use when the user says \"refactor this\", \"clean up this code\", \"리팩토링 해줘\", or \"this function is a mess\", or a named smell (long function, deep nesting, feature envy) surfaces while reading code with no intended behavior change. Gates untested legacy code behind a characterization-test protocol first. Not for diagnosing why something is broken — use debug — or for behavior-changing feature work and bug fixes, which belong to programming's red-green-refactor loop."
metadata:
  version: 2.2.0
---

# refactor

Restructures code so it is easier to work with without changing what it runs — the moment behavior changes, the work is a feature or a fix, not a refactor. Done well: verification stays green at checkpoints proportional to the change's blast radius, each move is mechanical, and the diff never mixes structure with behavior.

## Phase 0 — is refactoring warranted?

| Trigger | Recognize it by | Action |
|---|---|---|
| Rule of three | This is the third copy of the same shape | Extract now — the first or second copy is premature abstraction, a smell of its own |
| Preparatory | The upcoming feature is hard because of the current shape | Refactor first in its own commit, add the feature second in a separate one |
| Comprehension | The code needed a second read, or a scratch comment, to understand | Rename/extract while the understanding is fresh |
| Boy-scout | An unrelated smell is visible while already in the file for other work | Fix only if trivial and local to the touched lines; anything bigger gets flagged, not fixed inline |

Before touching structure: a test suite exists for the path and is green right now (run it, don't trust memory), and the working tree isn't mixing this with in-flight feature work. No coverage for the path → the legacy-code protocol below runs first; restructuring un-pinned behavior is a guess.

## Legacy-code protocol — characterization tests first

1. Run coverage against the target and read the gaps: `uv run pytest --cov=<pkg> --cov-report=term-missing <path>` (Python) or `npx vitest run --coverage` (TypeScript).
2. Write characterization tests against representative inputs, including the odd already-in-production ones, asserting the actual observed output — not the output assumed correct. `assert compute(weird_input) == 47` is right if `47` is genuinely what today's code returns, even if it looks wrong.
3. Get them green against current behavior. They pin what the code does now, bugs included — not yet a fix.
4. Only then refactor, keeping every characterization test green after each step below.
5. A real bug surfacing mid-characterization gets flagged (a comment, a note, a follow-up issue), never fixed in this pass — unless the task at hand is that fix, which runs as its own red-green-refactor cycle via `programming`, before or after the restructuring, never blended into it.

## Safety protocol

1. Tests green before starting (from Phase 0, or from the characterization protocol).
2. One move at a time from `references/catalog.md` — never combine two into one step.
3. Verify proportionally to blast radius: run a focused test after a local move, a broader suite after a cohesive checkpoint, and the final relevant suite when the refactor is complete. A red result reverts the move or cohesive group that caused it rather than debugging forward on a refactor that just broke something.
4. Refactor commits stay separate from behavior commits. Detect a commit mixing the two before it lands:
   ```bash
   git diff --staged --diff-filter=M -- '*test*' '*spec*' '*_test.*' '*.test.*' | grep -E '^[+-][^+-].*\b(assert|expect)\b'
   ```
   `--diff-filter=M` exempts brand-new test files (characterization tests, added coverage) by construction — no output means clean. An existing assertion's expected value flipping (a `-`/`+` pair changing `assert x == 47` to `== 48`, or a deletion) is the behavior-change signal — split the commit. A `+`-only line adding a new assertion beside untouched ones is just added coverage, not proof of a mix.

## Scope guard

- Split when the change no longer forms one cohesive, independently reviewable and revertible structural unit. File count is a reviewability signal, not a fixed ceiling.
- Boy-scout boundary, restated: spotting an unrelated smell mid-task is never license to fix it inline — flag it (a comment, a `craft:`-style note, or a message proposing a follow-up) and keep the current diff scoped to the stated task.

## Routing

- Which smell, which detect command, which threshold → `references/code-smells.md`.
- Which mechanical move fixes which smell, with worked Python/TypeScript examples → `references/catalog.md`.
- A one-shot terminal scan across a whole directory → `scripts/detect-smells.sh <dir>` when the stated refactor concerns a smell class the script can detect (a reporter, always exits 0 — review relevant findings; false-positive profile documented per rule). Route it by the skill package's own directory, not the target project's cwd, since the agent's cwd at invocation time is the project being scanned: `bash <skill-dir>/scripts/detect-smells.sh <target-dir>`.
- When symbol safety matters, prefer language-server diagnostics, definition, references, or rename over text search; check server status first and restore it before relying on textual results when it is unavailable.
- File-size ceiling (250 pure LOC) and its escape hatches → `programming`; this skill owns function-level size, not file-level.
- Turning any rule here into an enforced lint/hook/pre-commit check → `hookify`.

## Requirements

- `git` — the commit-separation check and churn-based smell detection.
- `grep`, `awk`, `find` (POSIX) — used directly and inside `scripts/detect-smells.sh`.
- A test runner: `pytest` (+ `pytest-cov`) for Python, `vitest` (`--coverage`) for TypeScript.
- Optional: `vulture` (Python) / `ts-prune` (TypeScript) for the Dead Code entry in `references/code-smells.md`.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Already in here, might as well fix everything I see." | Drive-by scope creep — flag anything beyond trivial and local instead. |
| "It's just a rename, I'll bundle it with the fix." | A rename is a refactor commit; a fix is a behavior commit — bundling means reverting one reverts both. |
| "No time for characterization tests, I already know what it does." | That certainty is exactly the guess this protocol replaces with a pinned assertion. |
| "Two duplicates is basically three, I'll extract now." | Rule of three means three — the second occurrence is too early to know the right shape. |
| "Tests still pass, so the commit is one change." | Passing tests don't prove that; check whether any assertion's expected value moved before assuming so. |

## Verification

- [ ] Phase 0 passed: trigger identified, tests confirmed green (or the characterization protocol completed first).
- [ ] Verification matched blast radius: focused test after each local move, broader suite at cohesive checkpoints, and final relevant suite at completion.
- [ ] No commit mixes a structural change with a changed test assertion (checked with the detection command above).
- [ ] Any applicable smell fixed cites its `references/code-smells.md` entry and the detect command's result.
- [ ] Scope stayed within the stated task; anything spotted-but-out-of-scope was flagged, not fixed inline.
