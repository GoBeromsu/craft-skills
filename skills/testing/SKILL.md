---
name: testing
description: Architects and audits project test suites by selecting the cheapest layer that proves behavior and contract risk, then placing tests and fixtures for a fast, deterministic suite. Use when choosing test placement, organizing fixtures, adding an integration or e2e test, designing contract coverage, or triaging flaky suites. Not for isolated function-level red-green-refactor TDD — use programming; not for diagnosing a currently failing test — use debug; not for ML or agent eval methodology — use ml or agents.
metadata:
  version: 2.1.0
---

# testing

Builds and maintains a test suite under one discipline: confidence first, speed second, coverage third. Choose evidence for the behavior and contract risk at the cheapest credible layer, then place it so the suite stays fast and deterministic. `programming` owns isolated function-level red-green-refactor TDD; this skill owns suite placement, fixtures, resource layers, and cross-boundary coverage.

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

| Kind | Scope | Typical cost | Choose when |
|---|---|---|---|
| Unit | single function/class, no I/O | milliseconds | it catches the logic or invariant regression credibly |
| Integration | crosses one process boundary (DB, cache, queue, another service) | usually under a second | the contract or adapter behavior needs that boundary |
| E2E | drives the real app through its real interface | seconds | a critical user journey cannot be proved credibly at a cheaper layer |

| Size | May touch | Avoid unless the risk needs it |
|---|---|---|
| Small | single process, CPU + memory only | disk I/O, network, subprocess, `sleep` |
| Medium | localhost I/O (local DB, local file, loopback socket) | any other host, real network egress |
| Large | network, multiple real services | — |

Choose the cheapest layer that catches the regression. Logic with no I/O usually belongs in unit/small; a boundary you own (DB, cache, queue) often needs integration/medium; a third-party boundary can use an integration fake or a contract test. Use e2e/large for a user-visible flow through the real app when lower layers leave material risk. The pyramid ratio is a sanity check, not a target.

Before adding a fixture, builder, or helper, reuse the repository's established test pattern when it fits. A bug report is a symptom: test the shared upstream behavior that protects all callers rather than only the reported path.

## Reproducible behavior defects

For a reproducible behavior defect, start with the smallest failing reproduction at its natural layer (usually unit; integration when the defect lives at a boundary). Confirm it fails for the reported reason, then let the fix make it pass and ship the regression test with the fix.

When the behavior cannot yet be reproduced or isolated, do not invent a failing test. Record that evidence limitation and retain the strongest available evidence, such as logs, a captured scenario, or monitored production behavior; turn it into a regression test when reproduction becomes possible.

### Advisory commit scan

This filename-based scan is a review lead, not proof: tests may live under nonstandard names and a test-file touch may not cover the defect.

```bash
git log --oneline -20 --grep="fix" -i | cut -d' ' -f1 | while read -r sha; do
  git diff-tree --no-commit-id --name-only -r "$sha" | grep -qEi 'test|spec' || echo "$sha: review evidence for this fix"
done
```

Review each reported commit for behavior evidence instead of treating output as a pass/fail gate.

## Core conventions (detail and detection commands in `references/conventions.md`)

A test name states the behavior as Given/When/Then (`test_given_empty_cart_when_checkout_then_rejects`), never the implementation. Test code favors DAMP (readable repetition) over DRY: a factory returning a fresh instance beats a shared mutable fixture; a builder with sensible defaults and explicit overrides beats one giant shared fixture file every test partially depends on. No `sleep`, wall-clock read, or unseeded randomness inside a unit/small test — each is a flake built in on day one. Every test asserts something specific about behavior; a test incapable of failing proves nothing.

## Requirements

Python: `pytest`, `pytest-randomly` (order-dependency flake detection), `hypothesis` for property tests. TypeScript: `vitest`, `fast-check` for property tests. Any stack: `grep`, `find`, `git` for the detection commands above and in `references/`. For any other stack, keep the rules unchanged and swap in that stack's incumbent test runner, order-randomization plugin, and property-testing library.
