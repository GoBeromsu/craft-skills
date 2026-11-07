---
name: principle-testing
description: Designs, improves, and audits test suites around behavior and risk, independent oracles, counterfactual evidence, deterministic diagnosis, and cost. Use for generated-test review, unit/component/integration/e2e or smoke placement, test-suite health, surviving-mutant triage on changed code, flaky-test policy, fixtures, and test audits. Not for production-code red-green implementation, which belongs to principle-programming; diagnosis or repair of one currently failing or intermittent test, which belongs to debug; structural-change characterization, which belongs to refactor; ML evaluation methodology, which belongs to ml; or project-specific agent evaluation methodology.
metadata:
  version: 3.4.0
---

# principle-testing

Decide for each proposed or changed test which behavior can fail, which independent oracle proves it, and whether to add, rewrite, delete, or omit the test.
Leave a reviewable strategy that selects the cheapest credible layer and records why a check exists.
Keep deterministic protocol, schema, version, registration, containment, secret, permission, and routing contracts in code when a current consumer or independent obligation needs them.
Keep taste, context, and judgment in docs; a policy document is a legitimate subject when its instruction is the contract under test.

## Principle references

- [prove-it-works](references/prove-it-works.md) verifies the real artifact, not a proxy.
- [sequence-verifiable-units](references/sequence-verifiable-units.md) ends each small unit in a check before starting the next.
- [test-behavior-not-implementation](references/test-behavior-not-implementation.md) asserts what the code's users can observe, so that the test fails when that behavior breaks and keeps passing when only the internals change.
- [explain-the-number](references/explain-the-number.md) names what limits a measured number and rules out that it measured something else, before you measure and before anyone trusts or reports it. `/benchmark-checklist` in the benchmark-checklist skill turns it into seven questions you answer from real runs.

## Output contract

Record the decision, independent oracle, cheapest credible evidence, and residual risk in the existing task summary before adding or changing tests.
For a small or low-impact reversible change, a short rationale with the evidence state is enough; do not emit a full-column strategy table unless the change spans several distinct risks.
Use `templates/test-strategy.md` as an optional audit aid when a multi-risk review needs comparable rows, not as proof that testing happened.
Name the existing higher contract test when a `no-test` decision relies on coverage, and return the decision with its evidence state.
When a failure cannot be reproduced, report unavailable reproduction evidence and the limit rather than inventing a failing test.
Choose `no-test` when no credible additional check is justified; lack of reproduction does not invalidate independent contract evidence.
Apply [test-behavior-not-implementation](references/test-behavior-not-implementation.md) when writing, changing, or keeping a test.
When reporting measured results, apply [explain-the-number](references/explain-the-number.md).
When the oracle is the implementation, rewrite the test against a specification, contract, recorded fixture, or independent reference.
When a test is flaky, quarantine it with a root-cause investigation and remove the nondeterminism instead of retrying in a loop.
When behavior is ambiguous, ask which contract governs it before choosing a test layer.

## Admission and workflow

Read `references/admission.md` before placing, retaining, rewriting, deleting, or adding a test.
Admit a test only when it names a behavior or invariant, covers a distinct failure mode, uses an independent oracle, and runs at the cheapest layer that can observe the failure.
Each retained check needs a current consumer or an independent safety, security, or data-integrity obligation; do not keep a check because a process artifact, extra approval, or repeated full suite exists.
When the task is codebase reduction, account in the existing rationale for retired, retained, and replacement implementation or support code; more tests, replacement guards, or new catalogs do not substitute for that objective.
Apply `references/structure.md` to keep regression setup proportional and `references/integration.md` before replacing a fake.
For a reproducible defect, obtain a strong fail-before and pass-after result in a disposable consumer when that demonstration is safe.
Scale observed, safely demonstrable, and unavailable evidence to the risk and lifecycle, as defined in `references/conventions.md`.
Use [prove-it-works](references/prove-it-works.md) for direct artifact checks and [sequence-verifiable-units](references/sequence-verifiable-units.md) for multi-step work.
A green run alone does not prove sensitivity, and missing history alone does not authorize deletion.

## Workflow and references

Read this file for every testing task and read the matching reference before changing tests.

| Work | Read |
|---|---|
| Admission, test strategy, audit decision, oracle, counterfactual evidence, determinism, suite health, or quarantine | `references/admission.md` and `references/conventions.md` |
| Location, incumbent layout, fixture scope, or builders | `references/structure.md` |
| Database, cache, queue, service boundary, contract, fake, seam, or mock | `references/integration.md` |
| Browser, CLI, user journey, startup wiring, selector, wait, or smoke | `references/e2e.md` |
| Create or maintain a project-local verification skill that drives the app the way a user does | `references/verification-skills.md` |
| Mutant checks on changed logic, or tests that still pass when changed code is wrong | `references/mutation.md` |

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
Have `principle-programming` own production-code red-green implementation and return pass evidence after this skill supplies the test design and the strongest available evidence for the named risk.
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
- A test that copies the implementation's discount formula merely reproduces its bug → derive the expected amount from the independent pricing contract.
- A check requiring a doc's `Verification` heading or forbidding an old directory name anywhere in prose locks wording or historical examples without a consumer → review the policy meaning and retain executable path-containment or registration checks where those contracts actually apply.
- JSON key order or whitespace asserted without a wire or parser consumer tests formatting rather than meaning → assert the decoded contract or the consumer that actually depends on the bytes.
- Two tests with identical setup, inputs, and oracle under different names add no evidence → keep one unless the execution environment exposes a distinct risk.
- Mandatory strategy tables, extra approvals, or repeated full-suite and runtime checks treated as proof add process cost without new evidence → record the distinct risk and the cheapest credible check in the existing summary.
- Fixture-generator, source-string-mutation, or checker-of-checker layers without an independent oracle protect test topology rather than product risk → test the public checker contract directly or delete the layer; do not ban a checker or topology test that protects a real contract.
- Test count as a metric rewards volume rather than unique evidence → review distinct failure modes and decision rationale instead.
- A mutation score treated as a target, quota, or merge gate rewards killing mutants over naming risk → triage each surviving mutant on the changed code and record the decision instead.
- A narrow regression or fixture retirement grows shared catalogs, duplicate test matrices, or a replacement application emulator → preserve the reduction objective with case-local inputs and the smallest faithful consumer proof; retain independently useful guards after a document migration rather than imposing filename bans or line-count quotas.

## Portable runtime facts

Use the target package's incumbent runner, order-randomization mechanism, and property-testing library.
Consult the deployed tool's official primary documentation and the repository's matching-version configuration before claiming support.
Do not install dependencies, assume a global executable, or invent a command when the target package does not establish it.
