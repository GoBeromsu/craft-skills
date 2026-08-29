# Testing Conventions Reference

This reference owns test quality, lifecycle evidence, audit decisions, and suite health.

## Contents

- [Test value rubric](#test-value-rubric)
- [Evidence and oracles](#evidence-and-oracles)
- [New and modified tests](#new-and-modified-tests)
- [Audits](#audits)
- [Static audit leads](#static-audit-leads)
- [Test-first and characterization quality](#test-first-and-characterization-quality)
- [Readable deterministic tests](#readable-deterministic-tests)
- [Suite health and quarantine](#suite-health-and-quarantine)
- [Cross-skill ownership](#cross-skill-ownership)

## Test value rubric

A valuable test names behavior or risk, uses an independent oracle, has lifecycle-appropriate counterfactual evidence, survives behavior-preserving refactors, is deterministic and diagnostic, and adds unique suite value proportional to cost.

Name the contract, invariant, failure mode, or user outcome rather than a file, method, private call, assertion count, or implementation path.

Choose the cheapest credible scope and resource size from `../SKILL.md`.

Retain repetition only when it protects a distinct residual risk that cheaper existing evidence does not prove.

Reject generated tautologies, implementation proxies, unreviewed snapshots, duplicates, and tests that cannot establish their claimed value.

## Evidence and oracles

An independent oracle comes from a public contract, business rule, invariant, user-visible outcome, approved fixture, or independent reference.

A mock return, private-call expectation, current implementation output, or uncontrolled snapshot is not an independent oracle.

Controlled observation or a snapshot is provisional characterization evidence until a contract, invariant, independent reference, or explicit approval corroborates it.

| Evidence state | Meaning | Use |
|---|---|---|
| `observed` | The test or precise counterfactual was run and went red for the named reason | Required for new and behavior-changed tests |
| `safely demonstrable` | A precise, disposable counterfactual demonstration is specified but has not run | Records auditable potential evidence |
| `unavailable` | The historical counterfactual cannot safely or credibly be obtained | Records a limitation and never alone authorizes deletion |

Evidence state describes the counterfactual, not whether a test happens to pass.

## New and modified tests

1. Name the behavior or risk and search for existing evidence that already proves it.
2. Choose the cheapest credible scope and resource size that retains the relevant fidelity.
3. Define the independent oracle before encoding setup or assertions.
4. Design a deterministic counterfactual that would fail for the named reason and survive a behavior-preserving refactor.
5. Obtain `observed` red evidence in a named disposable consumer for every new or behavior-changed test.
6. Hand production-code red-green implementation to `programming` and provide the risk, oracle, and failing evidence.
7. Review returned pass evidence for the named behavior, diagnosis, determinism, and marginal cost.

Do not invent a failing test when a reported behavior cannot be reproduced safely.

Record the limitation and preserve the strongest available evidence until a credible reproduction exists.

## Audits

Inventory tests by behavior and risk rather than by source file, filename, or assertion count.

For each test, record the decision, independent oracle, evidence state, residual risk, and cost.

| Decision | Use when |
|---|---|
| Retain | It independently protects a distinct risk at acceptable cost |
| Rewrite | The protected risk matters but the oracle, determinism, diagnosis, or refactor resilience is weak |
| Delete | Separate evidence proves it obsolete or duplicate and remaining coverage protects its meaningful risk |
| Add | A material residual risk lacks credible evidence |

New and behavior-changed tests need `observed` counterfactual evidence.

Historical `unavailable` evidence requires separate obsolete, duplicate, or remaining-coverage proof before deletion.

Search results and static patterns are review leads only.

Do not use assertion tokens, filenames, or source-test cardinality as pass/fail gates.

## Static audit leads

Use static searches to identify candidates, then apply the audit record and counterfactual evidence; a match never decides retain, rewrite, delete, or add by itself.

- Search for host-layout pins and silent skips such as `Path.home()`, literal `/tmp` paths, `skipif`, `importorskip`, or unconditional skip calls.
- Search documentation tests for existence, heading, or substring assertions that never execute the documented instruction.
- Search for log-text, private-attribute, or lint-suppression assertions used as proxies for public behavior.

Replace host-layout pins with runner-provided per-test paths and put every global side channel behind a shared fixture. Do not condition a default-suite test on a gitignored asset, optional binary, build flag, or sibling checkout: deliberately mark and select the required heavier environment instead.

Replace document-existence or heading assertions with executable checks of the instruction. Replace captured log-text or private-attribute proxies with a structured record or public result; confirm any lint suppression corresponds to an enabled rule.

For a new guard, `observed` evidence may be a disposable removal of the guard that makes the test red, followed by restoration. A fixed sleep remains a nondiagnostic wait; wait for the condition or event instead.

## Test-first and characterization quality

Test-first work starts from a named risk, independent oracle, and observed red evidence before `programming` changes production behavior.

`refactor` may hand off characterization tests that record incumbent behavior before structural change.

Testing reviews handed-off characterization for placement, determinism, diagnostics, and whether its observation remains provisional.

Do not treat unknown incumbent output as an approved specification or permanent golden master.

## Readable deterministic tests

Write names as behavior sentences such as `test_given_empty_cart_when_checkout_then_rejects`.

Prefer DAMP over DRY so a reader can understand a scenario without chasing helpers.

Use fresh factories and builders with sensible defaults and explicit relevant overrides.

Keep behavior-relevant inline data when it explains the scenario more clearly than a builder.

Control clocks, randomness, external state, test order, and asynchronous conditions.

Wait for the condition or event that proves progress instead of sleeping or retrying a whole test.

Keep diagnostic context close to the oracle so a failure identifies the broken behavior.

Navigation-only helpers are the limited e2e exception described in `e2e.md`.

## Suite health and quarantine

Treat a flaky test as a suite-health defect and track its trust cost, duplicate coverage, runtime trend, age, and effect on signal.

Quarantine only with a visible reason, owner or tracker, bounded review age, and retained diagnostic evidence.

Do not silently skip a test or use retries as a long-term repair.

Use a narrow documented retry only for demonstrated infrastructure instability and review its continuing cost.

Route reproduction, diagnosis, and repair of one specific intermittent failure to `debug`.

After `debug` returns diagnosis and fix evidence, testing decides readmission, duplicate removal, retry removal, and the suite-health follow-up.

## Cross-skill ownership

`refactor` initiates characterization before structural change.

Testing accepts handed-off characterization tests for quality, oracle, placement, and provisional-observation review.

`programming` owns production-code red-green implementation after testing supplies test design or observed red evidence.

`debug` owns a specific failure's reproduction, diagnosis, and repair.

Testing owns new-test quality, audits, placement, quarantine policy, and post-fix health.

`ml` and `agents` own their evaluation domains.
