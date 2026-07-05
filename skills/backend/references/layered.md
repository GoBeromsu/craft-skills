# Backend Layered Architecture

Three layers, one direction: a request enters at the controller, business logic runs in the service, persistence happens in the repository — and nothing calls upward or sideways past its neighbor.

## Hard rules

### Responsibility law

| Layer | Owns | Never | Detect |
|---|---|---|---|
| Controller | transport ↔ DTO mapping (parsing the request, choosing the status code, shaping the response) | business rules, direct database/ORM access | grep for db/ORM calls in controller files (below); business conditionals are grey zone — judge by whether the branch shapes the response (fine) or decides a business outcome (move to the service) |
| Service | business logic, orchestration across repositories, the transaction boundary | HTTP framework types (`Request`, `Response`, `APIRouter`) in its function signatures | grep for HTTP types in service files (below) |
| Repository | persistence — running queries, mapping ORM rows to domain types before returning | business rules inside a query (a `WHERE` clause encoding a policy, not a filter) | grey zone — judge by whether the condition is data selection (fine) or a business decision (move to the service) |

### Controller must not touch the database or the ORM directly

```bash
grep -rEn "\.query\(|\.objects\.(filter|get|all)\(|session\.execute\(|SELECT |INSERT INTO " \
  --include='*controller*' --include='*route*' -r ./src 2>/dev/null
```

Any hit inside a controller file means persistence logic leaked into the transport layer. Move the call into the service the controller invokes.

**SMELL — controller runs a query directly:**

```python
@router.get("/orders/{order_id}")
def get_order(order_id: OrderId, db: Session = Depends(get_db)):
    row = db.query(OrderRow).filter(OrderRow.id == order_id).first()
    if row is None:
        raise HTTPException(404)
    return row
```

**CLEAN — controller delegates to the service:**

```python
@router.get("/orders/{order_id}")
def get_order(order_id: OrderId, orders: OrderService = Depends(get_order_service)):
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(404)
    return OrderResponse.from_domain(order)
```

### Service must not depend on HTTP types

```bash
grep -rEn "\bRequest\b|\bResponse\b|APIRouter|@(app|router)\.(get|post|put|delete)" \
  --include='*service*' -r ./src 2>/dev/null
```

Any hit inside a service file means the business logic is coupled to a specific transport. Fix: accept and return plain typed values; let the controller do the HTTP-specific mapping.

### Repository returns domain types, never ORM rows, across the boundary

```bash
grep -rEn -e "-> *(models\.|orm\.|Row\b)" --include='*service*' -r ./src 2>/dev/null
```

Any hit means a service function's return type is an ORM row shape instead of a domain type. Fix: map the ORM row to a frozen domain type inside the repository, before it crosses into the service.

Grey zone — a repository method with a `WHERE status = 'active'` filter is fine (data selection); a repository method that decides *which* orders are eligible for a discount is a business rule and belongs in the service, even when it happens to be expressible as a query.

### Dependency direction — controller → service → repository, never reversed, never skipped

```bash
grep -rEln "from.*repositor|import.*Repository" --include='*controller*' -r ./src 2>/dev/null
```

Any hit means a controller imports a repository directly, skipping the service layer. Route the call through the service even when the controller "just needs a lookup" — the skip normalizes the next skip, and the service is where the transaction boundary and business rules live.

```bash
grep -rEln "from.*controller|import.*Controller" --include='*service*' --include='*repositor*' -r ./src 2>/dev/null
```

Any hit means a lower layer imports upward from a controller — a structural inversion. Fix immediately; this breaks the lower layer's testability in isolation.

**SMELL — a service reaches upward for a controller-owned response type (TypeScript):**

```typescript
// services/order-service.ts
import { OrderResponse } from "../controllers/order-controller"; // upward import
```

**CLEAN — the response type is built in the controller from a plain domain value:**

```typescript
// services/order-service.ts
export function getOrder(id: OrderId): Order | null { /* ... */ }
```

### DTO / domain-model separation

A request/response schema (the DTO — the shape the wire actually sends and receives) is a distinct type from the domain model (the shape the business logic reasons about). A domain model is never serialized straight to the wire; a mapping step — however thin — sits at the controller boundary.

Grey zone — a trivial CRUD resource where the DTO and domain model are structurally identical may share a base type, provided the mapping step still exists explicitly (a `from_domain()` classmethod, a `toResponse()` function) rather than passing the domain object straight into the framework's response serializer. This keeps a later field split (add a wire-only field, hide an internal one) a one-file change instead of a domain-model rewrite.

## Transaction ownership

The service is the transaction boundary: it opens the unit of work, calls one or more repository methods inside it, and commits or rolls back as one atomic step. A repository method never opens or commits its own transaction — that decision belongs to whoever is orchestrating the use case.

```bash
grep -rEn "\.commit\(\)|\.begin\(\)" --include='*repositor*' -r ./src 2>/dev/null
```

Any hit inside a repository file means the repository is managing its own transaction — a service calling two repository methods in sequence can no longer roll both back together. Move the `commit`/`begin` call to the service.

## Incumbent-respect clause

Detect the layer boundaries already in use in this service (see the `backend` `SKILL.md` PHASE 0 gate) and follow them for every edit. The strict responsibility law above is the default for new services and new files; it is never a reason to rewrite an existing controller/service/repository split mid-feature. Propose a boundary correction as its own change, scoped and reviewed on its own.

## Folder shape (see `folders.md` for full framework-specific trees)

```
src/
  api/            # controllers — routers, request/response DTOs
  services/       # business logic, orchestration, transaction boundary
  repositories/   # persistence — queries, ORM-row to domain mapping
  domain/         # shared domain types used across services/repositories
```

## Grey zones

- A repository method with a join across two aggregates for read efficiency is fine; a repository method that decides *whether* the join's result satisfies a business rule (rather than just returning it) has crossed into service territory.
- A tiny CRUD endpoint where the "service" would be a single pass-through call to the repository is still worth keeping as its own function — not collapsed into the controller — so the layer boundary stays uniform across the codebase even where one layer is thin.

## Grey zones

- A repository method with a join across two aggregates for read efficiency is fine; a repository method that decides *whether* the join's result satisfies a business rule (rather than just returning it) has crossed into service territory.
- A tiny CRUD endpoint where the "service" would be a single pass-through call to the repository is still worth keeping as its own function — not collapsed into the controller — so the layer boundary stays uniform across the codebase even where one layer is thin.
