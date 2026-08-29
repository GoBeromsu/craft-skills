# Testing Core Conventions Reference

Naming, DAMP-over-DRY, determinism, and assertion quality apply to every test regardless of taxonomy kind or size — this is the detail behind the "Core conventions" summary in `../SKILL.md`.

## Contents

- [Naming — behavior sentence, Given/When/Then](#naming--behavior-sentence-givenwhenthen)
- [DAMP over DRY in test code](#damp-over-dry-in-test-code)
- [Determinism law](#determinism-law)
- [Assertion quality](#assertion-quality)
- [Environment stickiness and silent skips](#environment-stickiness-and-silent-skips)
- [Doc-existence tests and executable docs](#doc-existence-tests-and-executable-docs)
- [Proxy assertions: log strings and private attributes](#proxy-assertions-log-strings-and-private-attributes)
- [Tests without teeth](#tests-without-teeth)
- [Common rationalizations](#common-rationalizations)
- [Red flags](#red-flags)
- [Verification](#verification)

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

## Environment stickiness and silent skips

A sticky test's outcome depends on the machine rather than the code, so it passes on the machine that wrote it and vanishes or fails elsewhere.
Three shapes recur, each with its own detection command:

```bash
grep -rn "Path.home()" <test-dir>                                  # home-layout pins
grep -rn '"/tmp/' <test-dir>                                       # hard-coded build dirs
grep -rn "skipif\|importorskip\|pytest.skip" <test-dir>            # silent skips
```

Home-layout pins and hard-coded temporary directories are replaced by the runner's per-test temporary-path fixture.
Silent skips are the dangerous one: a skip conditioned on a gitignored asset, an optional binary, a build flag, or a sibling checkout disappears on a fresh worktree, and the suite then "passes" while proving less.
An audit of one repository found four such skips in the default suite, gated on model weights, a media binary, a decoder build flag, and a model manifest.
Route a test with a gitignored or environment-dependent input to an `integration`, `heavy`, or `real_stack` marker that the default run deselects and CI fetches deliberately, rather than a condition on the input's existence.
Failing loudly is the acceptable middle: one benchmark instead raises `RuntimeError: fall model weights missing`, which is better than a skip but still means a "0 failed" result carries an environmental caveat that has to be stated.

Hermeticity is what makes the rest safe.
A shared conftest that redirects the home directory, sets a per-test database path, stubs DNS, and fixes the umask exists because a test once wrote to the developer's real application state file.
Any new global side-channel — an environment variable, a socket directory, a state directory — needs its fixture there before the test that uses it.

Waiting is the fourth shape: a fixed `sleep` in place of a wait-for-condition helper is a race deferred, not resolved.
Two such sites, one sleeping a flat 2.0 seconds, were found by the [determinism grep](#determinism-law) above; replace each with the repository's wait-until helper.

## Doc-existence tests and executable docs

A test asserting that a document exists, or that a heading string appears in it, passes when the document is wrong and fails when it is reworded.

```bash
grep -rn "is_file()\|\.exists()\|in text\b" <test-dir> | grep -iE "docs/|AGENTS|README|runbook"
```

The largest offender found in one audit was a documentation-contract module of 28 tests, two of them permanently skipped because the tree they described no longer existed — dead tests asserting a dead layout.
Substring pins on a container file or workflow file are the same defect in another costume.

The counter-pattern is an executable-docs test: assert what the document *instructs*, not that it exists.
One such test extracts the SQL from a runbook and runs it against seeded databases; another parses the runbook's shell blocks, checks the command order, and compares each flag against the real command-line tool's own help output.
A reworded heading then costs nothing, while an instruction that stopped working fails.

## Proxy assertions: log strings and private attributes

Two habits assert a proxy for behavior instead of behavior.
Matching against the captured log *text* couples the test to message formatting; asserting on the structured record's rendered message is the sanctioned form, and an audit found 9 text-matching sites against roughly 70 correct ones.

```bash
grep -rn "caplog.text" <test-dir>
grep -rnc "noqa: SLF001" <test-dir>          # compare against the linter's enabled rule set
```

A private-attribute assertion silenced with a lint suppression is decorative unless that rule is actually enabled; check the linter configuration before trusting the suppression to mean anything.

## Tests without teeth

A test that asserts a pure helper's return value while claiming to pin a guard never executes that guard.
For every new guard, prove the test can fail: delete the guard, run the test, confirm it goes red, restore the guard.
Record that the mutation was exercised in the change description, so the next reader does not have to re-derive whether the assertion is load-bearing.
The same discipline applied to a workflow or lint policy is owned by `security`'s untrusted-CI reference.

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
- [ ] No new skip is conditioned on a gitignored asset, optional binary, build flag, or sibling checkout in the default suite.
- [ ] A fresh worktree reports the same pass count as CI, and any remaining skip is explained.
- [ ] No added test asserts a document's existence or a heading substring; runbook tests execute the commands the runbook instructs.
- [ ] Each new guard test was demonstrated failing once with the guard removed.
