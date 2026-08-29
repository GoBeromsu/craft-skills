# Testing E2E Reference

Use e2e evidence only for a critical user-visible risk that no cheaper credible scope proves.

## Selector and wait rules

Select elements by role, accessible label, or a dedicated test id.

Reject CSS chains, XPath, and selectors tied to incidental DOM structure because behavior-preserving markup changes should not break the test.

Use framework auto-wait or wait for the actual state, event, or user-visible condition that proves progress.

Do not use fixed sleeps or whole-test retries to wait for a transition.

Keep assertions on independent user-observable outcomes rather than private implementation effects.

## Data and setup

Create isolated data for each test and clean it up with the narrowest safe mechanism.

Do not rely on state, ordering, or side effects left by another test.

Create prerequisites through an application API or narrow idempotent bootstrap when they are not part of the behavior under test.

Do not use broad demo seeds, resets, or cleanup without proof that the target is dedicated, disposable, and non-production.

Use the minimal browser and device matrix that preserves the named residual risk.

Navigation-only helpers may reach a starting state but must not hide the test's assertions or behavior-specific setup.

## Smoke and critical journeys

Smoke tests prove narrow startup, deployment, or wiring viability.

Critical e2e journeys prove a user outcome such as authentication, checkout, or data preservation that remains risky after cheaper evidence.

Do not duplicate smoke and journey coverage unless each test names a distinct residual risk and independent oracle.

Do not require the full e2e suite on every commit.

Schedule or gate e2e execution according to the risk, feedback need, and incumbent delivery policy.

## Evidence and flake policy

Require `observed` red evidence for every new or behavior-changed e2e test in a named disposable consumer.

Use the audit evidence states in `conventions.md` for historical tests.

Treat a flaky e2e test as a suite-health defect under the quarantine, retry, age, and readmission policy in `conventions.md`.

Route reproduction, diagnosis, and repair of one intermittent e2e failure to `debug`.

Resume testing after `debug` returns diagnosis and fix evidence to decide quarantine removal, retry removal, and portfolio health.

Return to `../SKILL.md` for scope and size selection and to `conventions.md` for independent-oracle and deterministic-test rules.
