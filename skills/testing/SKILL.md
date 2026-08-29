---
name: testing
description: Designs, improves, and audits test suites around behavior and risk, independent oracles, counterfactual evidence, deterministic diagnosis, and cost. Use for generated-test review, unit/component/integration/e2e or smoke placement, test-suite health, flaky-test policy, fixtures, and test audits. Not for production-code red-green implementation, which belongs to programming; diagnosis or repair of one currently failing or intermittent test, which belongs to debug; structural-change characterization, which belongs to refactor; or ML and agent evaluation methodology, which belongs to ml and agents.
metadata:
  version: 2.3.0
---

# testing

A valuable test names behavior or risk, uses an independent oracle, has lifecycle-appropriate counterfactual evidence, survives behavior-preserving refactors, is deterministic and diagnostic, and adds unique suite value proportional to cost.

## Test다운 Test admission contract

Admit, retain, rewrite, delete, or add a test only after answering these six questions.

1. What behavior, contract, invariant, failure mode, or user risk does it name?
2. What independent oracle establishes the expected outcome?
3. What lifecycle-appropriate counterfactual evidence supports the claim?
4. Does it survive a behavior-preserving refactor rather than encode implementation topology?
5. Does it control state, time, randomness, ordering, and waits well enough to diagnose a failure?
6. What distinct residual risk justifies its cost over existing cheaper evidence?

Choose the cheapest credible evidence scope that exposes the named risk.

## Workflow and references

Read this file for every testing task and read the matching reference before changing tests.

| Work | Read |
|---|---|
| New test, modified test, audit, oracle, counterfactual evidence, determinism, suite health, or quarantine | `references/conventions.md` |
| Location, incumbent layout, fixture scope, or builders | `references/structure.md` |
| Database, cache, queue, service boundary, contract, fake, seam, or mock | `references/integration.md` |
| Browser, CLI, user journey, startup wiring, selector, wait, or smoke | `references/e2e.md` |

For a new or behavior-changed test, require an observed red for the named reason in its disposable consumer before production implementation.

For an audit, classify evidence as `observed`, `safely demonstrable`, or `unavailable` as defined in `references/conventions.md`.

Do not delete a historical test from unavailable evidence alone.

Use retain, rewrite, delete, or add as the audit decision rather than preserving tests by count, filename, source adjacency, or assertion tokens.

## Evidence scopes and resource size

Evidence scope names what the test proves and resource size names what it consumes.

| Scope | Evidence | Use when |
|---|---|---|
| Unit | A focused behavior or invariant behind a stable public seam | The risk is credible without assembled collaborators or I/O |
| Component | Behavior of a composed in-process component and its real collaborators | Assembly, configuration, or collaboration is the distinct risk |
| Integration | A boundary contract with a real dependency or faithful substitute | Database, protocol, adapter, or independently deployed boundary semantics are the risk |
| E2E | A user-visible outcome through the real application interface | A critical journey leaves material residual risk after cheaper evidence |

| Resource size | Typical resources |
|---|---|
| Small | CPU and memory in one process |
| Medium | Local database, file system, loopback, or one managed local dependency |
| Large | Browser, networked services, or multiple real processes |

Smoke is a portfolio purpose that proves narrow startup or wiring viability.

Smoke is not an evidence scope, a size, a quota, or a substitute for a critical journey.

Flaky is a suite-health defect, not a test kind or a reason to hide a failure.

Property and contract are techniques applied within an evidence scope.

## Ownership and handoffs

Testing supplies risk, oracle, scope, test-quality review, placement, audit decisions, suite policy, quarantine policy, and post-fix suite health.

`programming` owns production-code red-green implementation and returns pass evidence after testing supplies the failing test or test design.

`debug` owns reproduction, diagnosis, and repair of a specific currently failing or intermittent test and returns diagnosis and fix evidence before testing resumes quarantine or health decisions.

`refactor` owns characterization before structural change and hands characterization tests to testing for quality and placement review.

Do not turn unknown incumbent output into a permanent golden master without an independent contract, invariant, reference, or explicit approval.

## Anti-patterns

- Source-to-test 1:1 mappings, missing-sibling claims, filename-touch proof, assertion-token gates, coverage quotas, or pyramid quotas substitute topology or counting for evidence.
- Generated tests that only repeat implementation details, mock returns, private calls, or unreviewed snapshots lack an independent oracle.
- A project-internal mock that returns the expected answer tests its own configuration rather than the behavior under test.
- Fixed sleeps, unbounded retries, unseeded randomness, shared mutable state, and order-dependent data make failures nondiagnostic.
- Duplicating smoke and e2e coverage without a distinct residual risk wastes suite budget.
- Deleting from `unavailable` evidence alone discards protection without proof.
- Wrapping database tests in rollback when application-owned transactions or transaction-local RLS are part of the path masks production behavior.
- Using broad seeds, resets, or privileged cleanup without proving a dedicated disposable non-production target risks real data.

## Portable runtime facts

Use the target package's incumbent runner, order-randomization mechanism, and property-testing library.

Consult the deployed tool's official primary documentation and the repository's matching-version configuration before claiming support.

Do not install dependencies, assume a global executable, or invent a command when the target package does not establish it.
