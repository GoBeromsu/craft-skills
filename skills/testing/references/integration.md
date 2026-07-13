# Testing Integration Reference

An integration test earns trust by touching something real — the ladder below picks the cheapest real thing that still catches the bugs that live at the boundary.

## Contents

- [Hard rules](#hard-rules)
- [Fakes and mocks — a worked example](#fakes-and-mocks--a-worked-example)
- [Grey zones](#grey-zones)

## Hard rules

### Real-dependency ladder

| Rung | What it is | Choose when | Never when |
|---|---|---|---|
| Real service in a container | Actual DB/queue/cache running via Docker or testcontainers | The dependency's behavior meaningfully differs across versions/config (constraints, migrations, query semantics, ordering guarantees) | The dependency is trivial to fake correctly and container startup dominates suite time |
| In-memory fake | A real implementation with the same interface, backed by memory (an in-memory queue, an embedded DB with portable schema) | You need speed and the fake is provably equivalent for what's under test | The fake's semantics diverge from production in ways the code depends on (vendor-only SQL features, specific ordering) |
| Wire-level fake | Intercepts the actual network call and returns canned responses (`respx`, `msw`, `nock`) | Testing your client's request/response handling against a third-party HTTP API | Testing your own service's internal logic — that belongs at the unit level |
| Mock (function/module mock) | Replaces the dependency's code path entirely | Only a true unmockable at its narrowest seam (system clock, RNG, `uuid4()`) | Any dependency you could instead fake at the wire or in-memory level — a mock that encodes what you expect the dependency to do stops catching real bugs in that dependency's use |

### DB test isolation options

| Option | Mechanics | Choose when | Trade-off |
|---|---|---|---|
| Transaction rollback | Wrap each test in a transaction; roll back after | The application does not own commit/rollback and no transaction-local security state must cross the wrapper | Application-owned transaction boundaries or `SET LOCAL` RLS state can make the test unlike production |
| Truncate between tests | Delete all rows from touched tables after each test | The application owns transactions or commits, including transaction-local RLS flows | Slower than rollback; must track which tables to truncate as the schema grows |
| Per-test schema/database | Spin up a fresh schema or database per test (or per worker) | Parallel workers, application-owned transactions, or RLS state make shared cleanup unsafe | Slowest, most isolated; needs automated schema/database provisioning |

Choose isolation from the application's transaction ownership and security-state behavior. Transaction rollback is conditional, not universal: use it only when the code under test does not control the transaction and transaction-local RLS cannot be masked. Otherwise use truncate or a per-test schema/database.

### Amortizing container startup cost

A containerized dependency's slow part is starting it, not querying it — start the container once per test session (or once per CI job), not once per test, and isolate between tests using the table above instead of a fresh container each time.

```python
@pytest.fixture(scope="session")
def postgres_container():
    production_image = os.environ["TEST_POSTGRES_IMAGE"]
    with PostgresContainer(production_image) as pg:
        yield pg
```

Set `TEST_POSTGRES_IMAGE` from the production manifest or managed-database declaration so the integration suite uses the detected production engine and major version. Do not encode a convenient fixed major in the fixture.

A per-test container restart turns a 200ms test into a multi-second test; the same isolation guarantee comes from transaction rollback inside one long-lived container.

```python
# Conditional transaction-rollback isolation for code that does not own transactions
@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

This fixture is valid only when the application does not commit, roll back, open an application-owned transaction, or depend on transaction-local RLS state. Use truncate or an isolated schema/database when any of those behaviors are part of the path under test.

### Contract tests for service boundaries

A contract test asserts that a producer's response shape and a consumer's expected request/response shape agree, independent of full end-to-end wiring — it catches a breaking API change before either side is deployed together. Write one per service-to-service or client-to-API boundary that deploys independently on each side. A contract test is not a substitute for an integration test against a real instance of the dependency; it substitutes for having to spin up the *other team's service* to catch shape drift.

```python
# A contract test validates shape, not full behavior — no real Orders service needed
def test_order_response_matches_contract():
    response = client.get("/orders/1")
    validate(instance=response.json(), schema=ORDER_RESPONSE_SCHEMA)
```

This catches the case where the API team silently renames or drops a field the consumer's parsing code depends on, without requiring the consumer's test suite to boot the producer's real service.

### Test env parity rules

The dependency version under test matches the dependency version in production — a passing suite against a different major version proves nothing about production behavior.

```bash
grep -h 'image:' docker-compose.test.yml docker-compose.prod.yml 2>/dev/null | sort -u
```

Pass: each service name appears with the same tag in both files. Fail: the same service name paired with two different tags — test/prod drift that invalidates the suite's guarantees.

Config differences between test and prod stay explicit and minimal:

| Concern | Allowed to differ | Never differs |
|---|---|---|
| Connection target | host, port, credentials | — |
| Scale | replica count, resource limits | — |
| Behavior | — | query semantics, isolation level, feature flags, schema version |

A test environment that silently diverges on a *behavior* row is not testing the thing that ships — treat any such diff as a bug in the test setup, not an acceptable shortcut.

### Database roles and RLS assertions

Provision and migrate the same-major real database with the privileged migration/admin role, then run repository and service behavior through the runtime application role. RLS coverage proves both allowed and denied tenant paths through that application role; an admin-role-only passing test bypasses the production authorization boundary.

If cleanup needs truncate, reset, or broad seed access, first prove the target is a dedicated disposable non-production database using a repository-owned guard or target identity. Do not reuse privileged cleanup credentials as the application's test credential.

## Fakes and mocks — a worked example

```python
# SMELL — mocking your own repository hides real query bugs
def test_get_active_users(mocker):
    mocker.patch.object(UserRepo, "get_active", return_value=[User(id=1)])
    result = service.list_active_users()
    assert result == [User(id=1)]  # tautology: mock returns what the test told it to
```

```python
# CLEAN — real repository against a containerized/test DB, isolated by transaction rollback
def test_get_active_users(db_session):
    db_session.add(User(id=1, active=True))
    db_session.add(User(id=2, active=False))
    result = UserRepo(db_session).get_active()
    assert [u.id for u in result] == [1]
```

The clean version fails if the query's `WHERE active = true` clause is deleted; the mocked version does not — it asserts the mock's own configuration, never the code under test.

Detection — mocking a project-owned repository/service class inside an integration test is the pattern above in disguise:

```bash
grep -rnE "mocker\.patch\.object\((\w*Repo|\w*Repository|\w*Service)|(jest|vi)\.mock\(['\"]\.\./?" \
  --include='test_*integration*.py' --include='*.integration.test.ts' <test-dir>
```

Pass: no output. Fail: any hit — grey zone if the mocked class wraps a genuine unmockable (an external SDK client with no fake available); judge by whether the ladder above has a cheaper real option first.

## Grey zones

- "Is this dependency trivial enough to fake in-memory?" — judge by whether the fake needs to reimplement more than a handful of the real dependency's semantics to stay correct; past that point, use the container.
- "Do we need a contract test or is the integration test enough?" — if both sides of the boundary deploy together (same repo, same release), skip the contract test; the integration test against the real dependency already covers it.
