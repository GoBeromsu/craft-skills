---
name: testing
description: Designs, improves, and audits test suites around behavior and risk, independent oracles, counterfactual evidence, deterministic diagnosis, and cost. Use for generated-test review, unit/component/integration/e2e or smoke placement, test-suite health, flaky-test policy, fixtures, and test audits. Not for production-code red-green implementation, which belongs to programming; diagnosis or repair of one currently failing or intermittent test, which belongs to debug; structural-change characterization, which belongs to refactor; or ML and agent evaluation methodology, which belongs to ml and agents.
metadata:
  version: 2.5.0
---

# testing

## Goal

Decide for each proposed or changed test which behavior can fail, which independent oracle proves it, and whether to add, rewrite, delete, or omit the test.
Leave a strategy that selects the cheapest credible layer and makes no-test decisions reviewable.

## Output contract

Emit one `templates/test-strategy.md`-shaped strategy table per change before adding or changing tests.
Include every required column, name the existing higher contract test for each `no-test` row that relies on coverage, and return the decision with its evidence state.
Treat the table as the deliverable rather than counting tests added.

## Admission and workflow

Read `references/admission.md` before placing, retaining, rewriting, deleting, or adding a test.
Admit a test only when it names a behavior or invariant, covers a distinct failure mode, uses an independent oracle, and runs at the cheapest layer that can observe the failure.
Record `add`, `rewrite`, `delete`, or `no-test` in `templates/test-strategy.md` before implementation.
Require an observed red for the named reason in a disposable consumer before production implementation when adding or behavior-changing a test.
Classify audit evidence as `observed`, `safely demonstrable`, or `unavailable` as defined in `references/conventions.md`.
Do not delete a historical test from unavailable evidence alone.

## Workflow and references

Read this file for every testing task and read the matching reference before changing tests.

| Work | Read |
|---|---|
| Admission, test strategy, audit decision, oracle, counterfactual evidence, determinism, suite health, or quarantine | `references/admission.md` and `references/conventions.md` |
| Location, incumbent layout, fixture scope, or builders | `references/structure.md` |
| Database, cache, queue, service boundary, contract, fake, seam, or mock | `references/integration.md` |
| Browser, CLI, user journey, startup wiring, selector, wait, or smoke | `references/e2e.md` |

## Evidence scopes and resource size

Choose the cheapest credible scope that exposes the named risk.

| Scope | Evidence | Use when |
|---|---|---|
| Unit | A focused behavior or invariant behind a stable public seam | The risk is credible without assembled collaborators or I/O |
| Component | Behavior of a composed in-process component and its real collaborators | Assembly, configuration, or collaboration is the distinct risk |
| Integration | A boundary contract with a real dependency or faithful substitute | Database, protocol, adapter, concurrency, ordering, or independently deployed boundary semantics are the risk |
| E2E | A user-visible outcome through the real application interface | A critical journey leaves material residual risk after cheaper evidence |

| Resource size | Typical resources |
|---|---|
| Small | CPU and memory in one process |
| Medium | Local database, file system, loopback, or one managed local dependency |
| Large | Browser, networked services, or multiple real processes |

Treat smoke as a portfolio purpose that proves narrow startup or wiring viability.
Do not treat smoke as an evidence scope, a size, a quota, or a substitute for a critical journey.
Treat flaky as a suite-health defect rather than a test kind or a reason to hide a failure.
Apply property and contract techniques within an evidence scope.

## Ownership and handoffs

Supply risk, oracle, scope, test-quality review, placement, audit decisions, suite policy, quarantine policy, and post-fix suite health.
Have `programming` own production-code red-green implementation and return pass evidence after this skill supplies the failing test or test design.
Have `debug` own reproduction, diagnosis, and repair of a specific currently failing or intermittent test and return diagnosis and fix evidence before quarantine or health decisions resume.
Have `refactor` own characterization before structural change and hand characterization tests to this skill for quality and placement review.
Do not turn unknown incumbent output into a permanent golden master without an independent contract, invariant, reference, or explicit approval.

## Anti-patterns

- Source-to-test 1:1 mappings, missing-sibling claims, filename-touch proof, assertion-token gates, coverage quotas, or pyramid quotas substitute topology or counting for evidence → name the behavior and distinct residual risk instead.
- Generated tests that only repeat implementation details, mock returns, private calls, or unreviewed snapshots lack an independent oracle → assert a public contract, invariant, or approved fixture instead.
- A project-internal mock that returns the expected answer tests its own configuration rather than the behavior under test → use a faithful substitute or a boundary contract instead.
- Fixed sleeps, unbounded retries, unseeded randomness, shared mutable state, and order-dependent data make failures nondiagnostic → control time, randomness, state, and ordering instead.
- Duplicating smoke and e2e coverage without a distinct residual risk wastes suite budget → retain only the cheapest evidence that observes the risk.
- Deleting from `unavailable` evidence alone discards protection without proof → retain the test until independent evidence supports a decision.
- Wrapping database tests in rollback when application-owned transactions or transaction-local RLS are part of the path masks production behavior → exercise the application-owned transaction and role path instead.
- Using broad seeds, resets, or privileged cleanup without proving a dedicated disposable non-production target risks real data → prove and use a dedicated disposable target instead.
- A test that mirrors implementation copy locks in an answer without proving the contract → rewrite it against the specification or approved fixture.
- Fixture-generator, source-string-mutation, or checker-of-checker layers without an independent oracle protect test topology rather than product risk → test the public checker contract directly or delete the layer.
- Test count as a metric rewards volume rather than unique evidence → review distinct failure modes and decision rows instead.

## Portable runtime facts

Use the target package's incumbent runner, order-randomization mechanism, and property-testing library.
Consult the deployed tool's official primary documentation and the repository's matching-version configuration before claiming support.
Do not install dependencies, assume a global executable, or invent a command when the target package does not establish it.

## Non-goals

Route production-code red-green implementation to `programming`.
Route diagnosis or repair of one currently failing test to `debug`.
Route characterization before structural change to `refactor`.
Route ML and agent evaluation methodology to `ml` or `agents`.
Do not add tests merely to increase count, preserve implementation text, or re-check topology.

## Failure modes

Record `no-test` and the unavailable reproduction evidence when the failure cannot be reproduced rather than inventing a failing test.
Rewrite the test against a specification, contract, recorded fixture, or independent reference when its oracle is the implementation.
Quarantine a flaky test with its root-cause investigation and remove the nondeterminism rather than adding a retry loop.
