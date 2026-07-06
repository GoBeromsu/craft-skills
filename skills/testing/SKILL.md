---
name: testing
description: 'Architects and audits the test suite for a project: classifies each test by taxonomy (unit, integration, e2e) and resource-based size, places it via a decision tree, and enforces the prove-it law that every bug fix ships with a failing-then-passing reproduction test. Use when writing tests for a change, setting up or reorganizing test structure and fixtures, adding an integration or e2e test, or triaging a flaky suite. Not for diagnosing why one test is failing right now — use debug. Not for the in-file red-green-refactor loop on one function — use programming. Not for ML eval-set methodology — use ml. Not for LLM-agent behavioral evals — use agents.'
metadata:
  version: 2.0.0
---

# testing

Builds and maintains a test suite under one discipline: confidence first, speed second, coverage third. Success looks like every test labeled by what it verifies and sized by what it touches — deliberately, not copied from the nearest existing file — and no bug fix landing without a failing-then-passing reproduction test.

`programming` owns the in-file red-green-refactor loop for one function. This skill owns everything above that: what to test at what layer, where a test lives, how a suite stays fast and deterministic, and how a fix proves itself.

## Gate — read the matching reference before writing a test

| Task | Read |
|---|---|
| Any test task (always) | Core rules below |
| Test-file location, fixture scope, test data builders | `references/structure.md` |
| Crosses a process boundary you or a container manage (DB, cache, queue, another internal service) | `references/integration.md` |
| Drives the real app through its user-visible interface (browser, CLI) | `references/e2e.md` |
| A contract check (independently-deployed sides agreeing on a request/response shape) | `references/integration.md` — contract is an integration-sized technique |
| A property check (generated inputs proving an invariant over a large/infinite space) | Core rules below — property is a unit-sized technique |
| Naming, DAMP-over-DRY, determinism, assertion-quality detail and detection commands | `references/conventions.md` |

Property and contract are techniques layered onto a taxonomy kind below, not a fourth or fifth kind: a property test is still a unit test that generates its inputs instead of hand-picking them; a contract test is still an integration test that checks shape instead of full behavior.

## Taxonomy × resource size

Taxonomy names what a test verifies; resource size names what it costs — these are orthogonal axes, not one label. A test can be "unit" in taxonomy and "medium" in size if it touches a local sqlite file.

| Kind | Scope | Speed budget | Mandatory when |
|---|---|---|---|
| Unit | single function/class, no I/O | <10ms each; whole suite <10s | every non-trivial logic branch |
| Integration | crosses one process boundary (DB, cache, queue, another service) | <1s each | every repository/adapter and every external-service client |
| E2E | drives the real app through its real interface | seconds each; whole suite minutes | every critical user journey (auth, checkout, primary CRUD) |

| Size | May touch | May NOT touch |
|---|---|---|
| Small | single process, CPU + memory only | disk I/O, network, subprocess, `sleep` |
| Medium | localhost I/O (local DB, local file, loopback socket) | any other host, real network egress |
| Large | network, multiple real services | — (this is the ceiling) |

## Placement decision tree

Logic with no I/O → unit / small. Crosses a process boundary you own (DB, cache, queue) → integration / medium. Crosses a boundary you don't own (a third-party API) → integration / medium against a fake, or a contract test. A user-visible flow through the real app → e2e / large. The pyramid ratio (many unit, some integration, few e2e) is a sanity check, not a quota — never force a third e2e test where a second integration test proves the same thing cheaper.

## The prove-it bug-fix law

Every bug fix starts with a failing reproduction test committed in the same change as the fix. Write the smallest test that reproduces the bug at its natural size (usually unit; integration if the bug lives at a boundary), run it and confirm it fails for the reported reason, then let the fix make it pass — it ships together with the fix, never as a follow-up.

Detection — scan recent fix commits for one that touched no test file:

```bash
git log --oneline -20 --grep="fix" -i | cut -d' ' -f1 | while read -r sha; do
  git diff-tree --no-commit-id --name-only -r "$sha" | grep -qEi 'test|spec' || echo "$sha: fix with no test file touched"
done
```

Pass: no output. Fail: any `fix with no test file touched` line — a bug fix landed with no proof it stays fixed.

## Core conventions (detail and detection commands in `references/conventions.md`)

A test name states the behavior as Given/When/Then (`test_given_empty_cart_when_checkout_then_rejects`), never the implementation. Test code favors DAMP (readable repetition) over DRY: a factory returning a fresh instance beats a shared mutable fixture; a builder with sensible defaults and explicit overrides beats one giant shared fixture file every test partially depends on. No `sleep`, wall-clock read, or unseeded randomness inside a unit/small test — each is a flake built in on day one. Every test asserts something specific about behavior; a test incapable of failing proves nothing.

## Requirements

Python: `pytest`, `pytest-randomly` (order-dependency flake detection), `hypothesis` for property tests. TypeScript: `vitest`, `fast-check` for property tests. Any stack: `grep`, `find`, `git` for the detection commands above and in `references/`. For any other stack, keep the rules unchanged and swap in that stack's incumbent test runner, order-randomization plugin, and property-testing library.
