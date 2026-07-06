# Testing Core Conventions Reference

Naming, DAMP-over-DRY, determinism, and assertion quality apply to every test regardless of taxonomy kind or size — this is the detail behind the "Core conventions" summary in `../SKILL.md`.

## Naming — behavior sentence, Given/When/Then

A test name states the behavior using Given/When/Then (GWT: precondition / action / expected result), never the implementation. `test_given_empty_cart_when_checkout_then_rejects` names the scenario; `test_checkout_2` or `test_it_works` names nothing.

## DAMP over DRY in test code

DAMP (Descriptive And Meaningful Phrases) means readable repetition beats clever abstraction in test code. A test must be understandable without following helpers across files. Production code shares logic to avoid divergence bugs; test code repeats setup so a reader sees the whole scenario in one place.

| Concern | Do / Use | Never |
|---|---|---|
| Setup shared by many tests | a factory function returning a fresh built object, called inline per test | a shared mutable fixture instance mutated across tests |
| A short assertion block reused elsewhere | inline it again | extract a one-caller `assertFooIsValid` that hides what's actually checked |
| Test data | a builder with sensible defaults + explicit overrides for what the test cares about | one giant shared fixture file every test partially depends on |

The one sanctioned exception is a navigation helper in e2e suites (log in, reach a page) — see `e2e.md`'s "Navigation helpers are the one DAMP exception".

## Determinism law

No `sleep`, wall-clock read, or unseeded randomness inside a unit/small test — each is a flake built in on day one.

```bash
grep -rnE '\bsleep\(|Date\.now\(\)|time\.sleep|Math\.random\(\)|random\.random\(\)' \
  --include='*.test.*' --include='test_*.py' --include='*_test.py' <test-dir>
```

Pass: no output, or every hit lives in an e2e/large test file (which uses auto-wait / a fake clock per `e2e.md` instead of `sleep`). Fail: any hit inside a unit-labeled test file.

## Assertion quality

Every test asserts something specific about behavior; no test exists that is incapable of failing.

```bash
grep -rLE 'assert|expect\(|\.should|assertThat\(|assertEquals\(|\bt\.(is|true|false|deepEqual|truthy|falsy|throws)\(' \
  --include='*.test.*' --include='test_*.py' --include='*_test.py' <test-dir>
```

Pass: no output. Fail: any file listed — a test file with zero assertion keywords across the major families (`assert`/`assertEquals`/`assertThat`, `expect(...)` incl. chai's `expect().to`, `.should`, AVA's `t.is`/`t.true`/etc.). Helper-only support files with no test cases (`conftest.py`, a fixtures/factories module) can trip this same grep even though nothing is actually missing — grey zone — judge by whether the file defines test cases. One behavior per test — grey zone: two `assert` statements checking unrelated facts about unrelated code paths is two tests in one; multiple assertions confirming one behavior (a response's status *and* its body) are fine — judge by whether reverting one code path would fail only one of the assertions.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "It's just a helper, extract it to keep DRY." | Test code optimizes for readability under change, not for avoiding repetition. DAMP over DRY — a reader should not need to open three files to see one scenario. |
| "The bug is obvious, I'll skip the reproduction test." | An obvious bug with no test is a bug that returns silently. Prove it first, every time. |
| "This test touches localhost so it's not really a unit test." | Taxonomy and size are separate axes. Label it by what it verifies; size it by what it touches. |
| "Adding a small sleep fixes the flaky test." | A `sleep` hides a race; it does not resolve it. Wait on the actual condition or event. |
| "One e2e test per feature keeps the pyramid honest." | The pyramid ratio is a sanity check, not a quota. Pick the cheapest layer that gives the confidence needed. |
| "There's already a `tests/` folder somewhere, I'll add another one for this package." | Scattered test directories fragment discovery. One convention per project or package — see `structure.md` for the default. |

## Red flags

- A new `tests/` directory appears alongside an existing one at a different path.
- A test file with no `assert`/`expect` reachable by grep.
- `sleep` / `Date.now()` / unseeded random inside a unit-labeled test file.
- A bug-fix commit with no test file in its diff.
- A shared mutable fixture object written by one test and read by another.
- Retries configured on a flaky test in place of a fix or a tracked quarantine.

## Verification

- [ ] The gate's matching reference was read before writing the test.
- [ ] The test's taxonomy label and resource size were both chosen deliberately, not copied from the nearest existing file.
- [ ] Bug fixes ship with a failing-then-passing reproduction test in the same change.
- [ ] Test names read as Given/When/Then behavior sentences.
- [ ] No `sleep`/wall-clock/unseeded-random inside unit/small tests (grep clean).
- [ ] Every test file has at least one reachable assertion (grep clean).
- [ ] New test directories follow the project's existing convention, not a newly invented one.
