# Backend Hexagonal Architecture

The domain is a framework-agnostic core; a port is an interface the domain defines for something it needs from the outside world, and an adapter is the concrete implementation plugged in at the edge — every import points inward, never out.

## Hard rules

### Domain core has zero framework imports

```bash
grep -rEln "fastapi|flask|django|sqlalchemy|express|nestjs|prisma|typeorm" \
  --include='*.py' --include='*.ts' -r ./src/domain 2>/dev/null
```

Any hit inside `domain/` means a web framework or ORM leaked into the core. Fix: define a port (a `Protocol`/TypeScript `interface`) that expresses what the domain needs, and let an adapter implement it using the framework.

### Ports are defined by the domain; adapters implement them at the edge

A port is a `Protocol` (Python) or an `interface` (TypeScript) declared inside `domain/` or `ports/`, naming a capability the domain needs (`OrderRepository`, `PaymentGateway`, `Clock`). An adapter is a concrete class implementing that port, living under `adapters/`, and wired in at the composition root — the single place that constructs concrete adapters and injects them into use cases.

```python
# ports/order_repository.py — defined by the domain, zero framework imports
class OrderRepository(Protocol):
    def get(self, order_id: OrderId) -> Order | None: ...
    def save(self, order: Order) -> None: ...
```

```python
# adapters/persistence/sqlalchemy_order_repository.py — implements the port
class SqlAlchemyOrderRepository:
    def get(self, order_id: OrderId) -> Order | None:
        row = self._session.get(OrderRow, order_id)
        return _to_domain(row) if row else None
```

### Dependency rule — imports point inward only

| From | May import | Never imports |
|---|---|---|
| `domain/` | nothing outside `domain/` (plus stdlib) | `ports/`, `use_cases/`, `adapters/` |
| `ports/` | `domain/` types (for method signatures) | `adapters/`, any framework |
| `use_cases/` | `domain/`, `ports/` | `adapters/` directly, any framework |
| `adapters/` | `domain/`, `ports/` (to implement them) | nothing forbidden — this is the outermost layer |

```bash
# Domain must not import ports, use-cases, or adapters
grep -rEln "from (ports|use_cases|adapters)|import.*(Port|UseCase|Adapter)" \
  --include='*.py' -r ./src/domain 2>/dev/null

# Use-cases must not import adapters directly (only through injected ports)
grep -rEln "from adapters|import.*Adapter" --include='*.py' -r ./src/use_cases 2>/dev/null
```

Any hit is an inverted dependency. The fix is always the same shape: introduce or use a port instead of reaching for the concrete adapter directly.

### Use-case layer orchestrates ports

A use case (`use_cases/create_order.py`) is a function or class that calls one or more ports to fulfill exactly one business operation. It contains no framework code and no direct persistence calls — those go through the injected repository port.

### Composition root

The composition root is the single place — typically the application entrypoint (`main.py`, `app.py`, `server.ts`) — that constructs every concrete adapter and injects it into the use cases that need it. No other file decides which adapter implementation to use.

```python
# main.py — the only file that knows about concrete adapters
def build_app() -> FastAPI:
    order_repo = SqlAlchemyOrderRepository(session_factory)
    create_order = CreateOrder(order_repo, StripePaymentGateway())
    app = FastAPI()
    app.include_router(order_router(create_order))
    return app
```

```bash
grep -rEln "SqlAlchemy|Stripe|Sendgrid|Redis" --include='*.py' -r ./src/use_cases 2>/dev/null
```

Any hit means a use case names a concrete adapter class instead of depending on its port — construction leaked out of the composition root.

**SMELL — domain code constructs a concrete adapter:**

```python
# domain/order.py
from adapters.persistence.sqlalchemy_order_repository import SqlAlchemyOrderRepository

class Order:
    def reload(self) -> None:
        self._repo = SqlAlchemyOrderRepository(get_session())  # domain depends on a concrete adapter
```

**CLEAN — the port is injected, domain never constructs its own dependency:**

```python
# domain/order.py
class Order:
    def __init__(self, repo: OrderRepository) -> None:
        self._repo = repo  # injected port, no concrete adapter reference
```

### When hexagonal is over-engineering

A CRUD service behind a single delivery mechanism — one HTTP API, no CLI/queue/second consumer, no plausible port swap on the horizon — does not need the ports/adapters split. The indirection buys optionality nobody will use, and the domain rarely outlives a framework it was never protected from in the first place. Default a CRUD-only, single-consumer service to layered instead of hexagonal.

## Testing benefit (why the ceremony pays off when it's earned)

A domain with no framework imports, and use-cases wired only to ports, can be tested entirely with in-memory fakes implementing each port — no database, no HTTP server, no framework test client required. This is the concrete payoff that justifies the indirection: if a service cannot show this benefit (its use-case tests still spin up a real database because the fakes never get used), the split has not earned its keep yet.

## Incumbent-respect clause

Detect the port/adapter boundaries already established (see the dependency-direction commands above) and match them for every edit. Do not introduce a new port "for consistency" without a second adapter that will actually implement it — a port with exactly one implementation and no plausible second is speculative generality; wait until a real second adapter (a different persistence backend, a test double beyond the standard fake) justifies it.

## Grey zones

- A port with exactly one production adapter plus the standard in-memory test fake is not speculative generality — the fake counts as the second implementation that justifies the port. A port with one production adapter and no fake anywhere in the test suite is the actual smell.
- A thin use case that does nothing but call one repository method does not need its own elaborate structure — it is fine to keep as a short function even in an otherwise-hexagonal service, provided it still goes through the port and never calls a concrete adapter directly.

## Folder shape (see `folders.md` for full framework-specific trees)

```
src/
  domain/         # entities, value objects — zero framework imports
  ports/          # interfaces the domain depends on
  use_cases/      # orchestrates ports to fulfill one use case
  adapters/
    http/         # inbound adapter — framework routers
    persistence/  # outbound adapter — ORM repository implementations
```
