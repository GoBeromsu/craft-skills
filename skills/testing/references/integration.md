# Testing Integration Reference

Use integration evidence when boundary semantics are the named risk and preserve the fidelity that makes those semantics credible.

## Contents

- [Fidelity and isolation](#fidelity-and-isolation)
- [Seams, fakes, mocks, and spies](#seams-fakes-mocks-and-spies)
- [Boundary evidence](#boundary-evidence)

## Fidelity and isolation

Use a real dependency in a container when engine, major version, configuration, migrations, query semantics, ordering, transaction behavior, or protocol behavior is the risk.

Use a faithful in-memory or wire-level fake only when it preserves the semantics relevant to the named risk at lower cost.

Use a narrow mock only under the admission rules below.

Match the production database engine, major version, schema behavior, and behavior-affecting configuration.

Run application behavior through the runtime application role rather than an administrative migration or cleanup role.

For RLS, prove both allowed and denied tenant paths through that application role.

Choose rollback isolation only when the application does not own commits, rollbacks, transaction boundaries, or transaction-local RLS state.

Use truncate or a per-test schema or database when application-owned transactions or security state make rollback unfaithful.

Guard privileged cleanup, broad seed, reset, or truncate operations with proof of a dedicated disposable non-production target.

Start expensive immutable dependencies once per session when per-test isolation retains faithful behavior.

Bootstrap only prerequisites needed by the boundary under test.

Keep deployment-aware contracts narrow and distinguish independently deployed request or response shape from full behavior.

## Seams, fakes, mocks, and spies

Introduce a seam only at a meaningful external or nondeterministic boundary such as a clock, random source, external SDK, transport, queue, or payment provider.

Do not create an interface or dependency-injection layer solely to mock project internals.

Admit a mock or spy only when its interaction is independently specified or no faithful cheaper fake can expose the named risk.

Assert an independently specified request, externally visible effect, or error translation rather than the mock return configured by the test.

Reject return-equals-expectation tests and private-call expectations because they are tautologies.

Prefer this ladder for the named risk: real container or service, faithful in-memory or wire fake, then narrow mock.

```python
# The oracle is the public query behavior, not a repository mock return.
def test_active_user_query_excludes_inactive_users(db_session):
    db_session.add(User(id=1, active=True))
    db_session.add(User(id=2, active=False))
    db_session.commit()

    users = UserRepo(db_session).get_active()

    assert [user.id for user in users] == [1]
```

This test goes red if the query predicate that excludes inactive users is removed.

## Boundary evidence

Require `observed` red evidence for every new or behavior-changed boundary test in a named disposable consumer.

Use `observed`, `safely demonstrable`, and `unavailable` for audits as defined in `conventions.md`.

An unavailable historical counterfactual alone does not justify deleting boundary coverage.

Use a contract test for independently deployed sides that need request or response shape evidence without full journey wiring.

Do not use a contract test to replace real dependency behavior when the dependency semantics are the risk.

Return to `../SKILL.md` for scope and resource-size selection and to `conventions.md` for oracle, audit, and suite-health rules.
