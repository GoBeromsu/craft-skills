---
name: testing
description: '"write tests for this", "테스트 짜줘", "flaky test", "how should I structure my test suite" — suite-level test architecture: taxonomy, resource-based sizing, placement, structure conventions, integration/e2e discipline, and flakiness elimination. Routes through a PHASE 0 gate to references/structure.md, references/integration.md, references/e2e.md.'
version: 1.0.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
compatibility: claude-code, codex
---

# testing

Build and maintain a test suite under one discipline: **confidence first, speed second, coverage third.**

## Overview

This skill is an index. Shared rules live here; the per-kind iron list lives in `references/`. Load the matching reference before writing a suite-level test. `programming` owns the in-file red-green-refactor loop — write the failing test, make it pass, refactor with the net. `testing` owns everything above that single file: what to test at what layer, where a test lives, how a suite stays fast and deterministic, and how a bug fix proves itself.

## When to Use

- Deciding what kind of test a piece of behavior needs (unit, integration, e2e, contract, property) and how big it should be.
- Setting up or reorganizing test structure, fixtures, or test data for a project or package.
- Writing the reproduction test for a bug fix.
- Diagnosing a flaky, slow, or untrustworthy test suite.
- Writing an integration test that crosses a process boundary, or an e2e test that drives the real app.

Not for the in-file red/when/then loop while implementing one function — load `programming` for that. Not for ML model evaluation methodology (accuracy, F1, eval-set curation) — load `ml`. Not for LLM-agent behavioral evals — load `agents`.

## PHASE 0 — test-kind gate (run first, every time)

Do not write a test before this gate.

1. Identify the work: new test authoring, suite/fixture structure setup, an integration test, an e2e test, or a bug-fix reproduction (a bug fix always needs a reproduction test, regardless of kind — see the prove-it law below).
2. STOP and read the matching reference in full:

   | Scope | Read |
   |---|---|
   | Every test task (always) | Core rules below — taxonomy, sizing, placement, prove-it law, naming, DAMP-over-DRY (defined below), determinism, assertion quality |
   | Test-file location, fixture organization, test data builders | `references/structure.md` |
   | A test crosses a process boundary you or a container manage (DB, cache, queue, another internal service) | `references/integration.md` |
   | A test drives the real app through its user-visible interface (browser, CLI) | `references/e2e.md` |

3. Apply the core rules below plus the per-kind iron list from the reference.

## Test taxonomy (MECE)

The five kinds below are MECE (Mutually Exclusive, Collectively Exhaustive): every test fits exactly one row, and the rows together cover every kind of test a suite needs.

| Kind | Scope | Speed budget | Mandatory when |
|---|---|---|---|
| Unit | single function/class, no I/O | <10ms each; whole suite <10s | every non-trivial logic branch |
| Integration | crosses one process boundary (DB, cache, queue, another service) | <1s each | every repository/adapter and every external-service client |
| E2E | drives the real app through its real interface | seconds each; whole suite minutes | every critical user journey (auth, checkout, primary CRUD) |
| Contract | verifies a boundary's request/response shape both sides agree on | <1s each | every service-to-service or client-to-API boundary with independently deployed sides |
| Property | generates inputs to check an invariant holds | budget like unit | an invariant with a large or infinite input space (parsers, serializers, math) |

## Resource-based size model — orthogonal to taxonomy

Size constrains what a test may *touch*, independent of its taxonomy label above. This resolves "is this really a unit test" arguments — ask about resources, not the label.

| Size | May touch | May NOT touch |
|---|---|---|
| Small | single process, CPU + memory only | disk I/O, network, subprocess, `sleep` |
| Medium | localhost I/O (local DB, local file, loopback socket) | any other host, real network egress |
| Large | network, multiple real services | — (this is the ceiling) |

A test can be "unit" in taxonomy but "medium" in size if it touches a local sqlite file — taxonomy answers *what it verifies*, size answers *what it costs*.

## Placement decision tree

Logic with no I/O → unit / small. Crosses a process boundary you own (DB, cache, queue) → integration / medium. Crosses a boundary you don't own (a third-party API) → integration / medium against a fake, or a contract test. A user-visible flow through the real app → e2e / large. The pyramid ratio (many unit, some integration, few e2e) is a sanity check, not a quota — never force a third e2e test where a second integration test proves the same thing cheaper.

## The prove-it bug-fix law

Every bug fix starts with a failing reproduction test committed in the same change as the fix.

1. Write the smallest test that reproduces the bug at its natural size — usually unit; integration if the bug lives at a boundary.
2. Run it and confirm it fails for the reported reason, not an unrelated one.
3. The fix makes that test pass. It ships together with the fix, never as a follow-up.

Detection — scan recent fix commits for one that touched no test file:

```bash
git log --oneline -20 --grep="fix" -i | cut -d' ' -f1 | while read -r sha; do
  git diff-tree --no-commit-id --name-only -r "$sha" | grep -qEi 'test|spec' || echo "$sha: fix with no test file touched"
done
```

Pass: no output. Fail: any `fix with no test file touched` line — a bug fix landed with no proof it stays fixed.

## Naming — behavior sentence, Given/When/Then

A test name states the behavior using Given/When/Then (GWT: precondition / action / expected result), never the implementation. `test_given_empty_cart_when_checkout_then_rejects` names the scenario; `test_checkout_2` or `test_it_works` names nothing.

## DAMP over DRY in test code

DAMP (Descriptive And Meaningful Phrases) means readable repetition beats clever abstraction in test code. A test must be understandable without following helpers across files. Production code shares logic to avoid divergence bugs; test code repeats setup so a reader sees the whole scenario in one place.

| Concern | Do / Use | Never |
|---|---|---|
| Setup shared by many tests | a factory function returning a fresh built object, called inline per test | a shared mutable fixture instance mutated across tests |
| A short assertion block reused elsewhere | inline it again | extract a one-caller `assertFooIsValid` that hides what's actually checked |
| Test data | a builder with sensible defaults + explicit overrides for what the test cares about | one giant shared fixture file every test partially depends on |

## Determinism law

No `sleep`, wall-clock read, or unseeded randomness inside a unit/small test — each is a flake built in on day one.

```bash
grep -rnE '\bsleep\(|Date\.now\(\)|time\.sleep|Math\.random\(\)|random\.random\(\)' \
  --include='*.test.*' --include='test_*.py' --include='*_test.py' <test-dir>
```

Pass: no output, or every hit lives in an e2e/large test file (which uses auto-wait / a fake clock per `references/e2e.md` instead of `sleep`). Fail: any hit inside a unit-labeled test file.

## Assertion quality

Every test asserts something specific about behavior; no test exists that is incapable of failing.

```bash
grep -rLE 'assert|expect\(|\.should' --include='*.test.*' --include='test_*.py' --include='*_test.py' <test-dir>
```

Pass: no output. Fail: any file listed — a test file with zero assertion keywords. One behavior per test — grey zone: two `assert` statements checking unrelated facts about unrelated code paths is two tests in one; multiple assertions confirming one behavior (a response's status *and* its body) are fine — judge by whether reverting one code path would fail only one of the assertions.

## Requirements

- Python: `pytest`, `pytest-randomly` (order-dependency flake detection), `hypothesis` for property tests.
- TypeScript: `vitest`, `fast-check` for property tests.
- `grep`, `find`, `git` for the detection commands above.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's just a helper, extract it to keep DRY." | Test code optimizes for readability under change, not for avoiding repetition. DAMP over DRY — a reader should not need to open three files to see one scenario. |
| "The bug is obvious, I'll skip the reproduction test." | An obvious bug with no test is a bug that returns silently. Prove it first, every time. |
| "This test touches localhost so it's not really a unit test." | Taxonomy and size are separate axes. Label it by what it verifies; size it by what it touches. |
| "Adding a small sleep fixes the flaky test." | A `sleep` hides a race; it does not resolve it. Wait on the actual condition or event. |
| "One e2e test per feature keeps the pyramid honest." | The pyramid ratio is a sanity check, not a quota. Pick the cheapest layer that gives the confidence needed. |
| "There's already a `tests/` folder somewhere, I'll add another one for this package." | Scattered test directories fragment discovery. One convention per project or package — see `references/structure.md` for the default. |

## Red Flags

- A new `tests/` directory appears alongside an existing one at a different path.
- A test file with no `assert`/`expect` reachable by grep.
- `sleep` / `Date.now()` / unseeded random inside a unit-labeled test file.
- A bug-fix commit with no test file in its diff.
- A shared mutable fixture object written by one test and read by another.
- Retries configured on a flaky test in place of a fix or a tracked quarantine.

## Verification

- [ ] The PHASE 0 reference matching the test kind was read before writing the test.
- [ ] The test's taxonomy label and resource size were both chosen deliberately, not copied from the nearest existing file.
- [ ] Bug fixes ship with a failing-then-passing reproduction test in the same change.
- [ ] Test names read as Given/When/Then behavior sentences.
- [ ] No `sleep`/wall-clock/unseeded-random inside unit/small tests (grep clean).
- [ ] Every test file has at least one reachable assertion (grep clean).
- [ ] New test directories follow the project's existing convention, not a newly invented one.
