# Testing Structure Reference

Place tests according to the incumbent repository convention without treating layout as a coverage claim.

## Placement

Detect the existing convention before adding a test and preserve it for the package being changed.

An incumbent mirror tree, colocated test file, `__tests__` directory, or monorepo package boundary guides placement but does not require a source-to-test 1:1 mapping.

Do not infer a missing test or a coverage gap from a source file without a matching sibling.

Do not migrate an established layout incidentally while changing behavior.

For a greenfield package, use the language's established repository default rather than introducing a competing convention.

Place unit and component tests near the stable behavior they describe.

Place integration tests with the package that owns the boundary contract.

Place e2e and smoke tests in the incumbent journey or deployment suite.

Treat scattered test-directory searches as review leads rather than automatic consolidation orders.

In a monorepo, keep tests within the owning package unless an existing cross-package suite owns the user journey.

## Fixture isolation

Keep mutable fixtures at the narrowest scope that safely serves their consumers.

Return a factory or fresh object whenever a test can mutate the fixture.

An expensive immutable resource such as a container, compiled schema, or read-only reference data may use session scope when its lifecycle and isolation remain explicit.

Do not promote a fixture merely because copy-pasted setup looks similar.

Promote setup only when consumers need the same behavior and shared lifecycle does not hide state.

Use transaction, truncate, or isolated-schema cleanup according to the database behavior in `integration.md`.

## Builders and inline data

Use builders with sensible defaults and explicit overrides when repeated setup obscures the behavior under test.

Keep minimal behavior-relevant inline data when it makes the scenario clearer than a builder call.

Do not require one builder per entity or force every object through a shared fixture.

Avoid giant shared fixture files that make unrelated tests depend on one complete object shape.

Prefer readable local setup over helpers that conceal the oracle or important preconditions.
