# Backend API Design

Design the contract before the handler; once an API is observed by a caller, every field and status code it returns is a promise, and breaking a promise is a break whether it was documented or not.

## Contents

- [Hard rules](#hard-rules)
  - [Contract-first](#contract-first)
  - [The observed-behavior law](#the-observed-behavior-law)
  - [One-version rule](#one-version-rule)
  - [API base and prefix boundary](#api-base-and-prefix-boundary)
  - [When a version bump is unavoidable](#when-a-version-bump-is-unavoidable)
  - [Additive vs breaking — the quick checklist](#additive-vs-breaking--the-quick-checklist)
  - [Resource naming](#resource-naming)
  - [Error model](#error-model)
  - [Pagination — cursor over offset](#pagination--cursor-over-offset)
  - [Idempotency keys for unsafe retries](#idempotency-keys-for-unsafe-retries)
  - [Timeouts and retries are part of the contract](#timeouts-and-retries-are-part-of-the-contract)
  - [Idempotency key storage](#idempotency-key-storage)
  - [Rate limiting is a security boundary, not a design contract (hand-off)](#rate-limiting-is-a-security-boundary-not-a-design-contract-hand-off)
- [Grey zones](#grey-zones)
- [Incumbent-respect clause](#incumbent-respect-clause)

## Hard rules

### Contract-first

Write the request/response schema (Pydantic model, zod schema, or OpenAPI fragment) before writing the handler body. The schema is the source of truth the handler is implemented against, not a description generated from the handler afterward.

```bash
# Detect a handler file with no schema definitions anywhere in it
grep -rlE "@(app|router)\.(get|post|put|delete|patch)" --include='*.py' --include='*.ts' -r ./src 2>/dev/null \
  | xargs grep -L "BaseModel\|z\.object(" 2>/dev/null
```

A file listed here has route handlers with no schema definitions anywhere in it — a strong signal the contract was never written down, only inferred from the code.

### The observed-behavior law

Every observable behavior of an API — a field's presence, its type, its meaning, a status code, an error shape, ordering, even undocumented ones — will be depended on by some caller. Changing it is a break whether or not it was ever written down. Prefer additive change (add a new field, add a new optional parameter) over repurposing an existing one (changing what a field means, narrowing its type, removing a value from an enum).

Grey zone — judge by asking: "would an existing client's parsing logic silently misinterpret the new meaning, or would it simply not notice a new addition?" Silent misinterpretation is a break; a client ignoring an unrecognized new field is safe.

### One-version rule

Avoid maintaining long-lived parallel API versions. Evolve the current version additively for as long as possible; version only when a genuine incompatible break is unavoidable, and set a deprecation date for the old version the same day the new one ships.

```bash
find . -maxdepth 3 -type d -iregex '.*/v[0-9]+$' -not -path '*/node_modules/*'
```

Two or more results means two versions are live at once. Read: is there a tracked deprecation date for the older one? If not, that is drift — either commit to a sunset date or fold the divergence back into additive changes on the single live version.

### API base and prefix boundary

The common API base, proxy mount, and version prefix belong in one app/bootstrap/router composition layer, not in every controller or feature router. Do not prescribe `/api/v1` universally; detect the incumbent mount style and extend it in the one place the framework composes routes. Handlers and child routers own resource-local paths only (`/orders`, `/{order_id}`), so a future base-path or version change is one composition edit.

### When a version bump is unavoidable

Signal the version explicitly — a URL prefix (`/v2/...`) or an `Accept`/custom header — never an implicit behavior change gated on a request's shape or a client's identity. Extend whichever mechanism the API already uses; check existing routes and headers first, and never introduce a second versioning mechanism alongside the first.

### Additive vs breaking — the quick checklist

| Change | Safe (additive) | Breaking |
|---|---|---|
| Field | add a new optional field | remove a field, change its type, repurpose its meaning |
| Endpoint | add a new endpoint | remove or rename an existing endpoint |
| Enum | add a new value a client can ignore | remove a value, change what an existing value means |
| Status code | add a new code for a new situation | change the code returned for an existing situation |
| Required-ness | relax required → optional | tighten optional → required |

### Resource naming

| Concern | Do | Never |
|---|---|---|
| Resource path | plural noun, `orders/{order_id}` | verb in the path, `getOrder/{id}` |
| Nesting | one level of real ownership, `orders/{id}/items` | deep nesting beyond a true parent-child relationship |
| Casing | consistent within the API (`snake_case` fields for a Python-first API, `camelCase` for a JS-first one) | mixed casing across endpoints of the same API |

### Error model

One envelope shape for every error response, carrying a machine-readable code and a human-readable message. A caller should never need to branch on the HTTP status code plus a string-matched message body just to know what happened.

```json
{ "error": { "code": "order_not_found", "message": "Order ORD-123 does not exist." } }
```

```bash
grep -rEn "raise HTTPException\(|res\.status\([0-9]+\)\.json\(" \
  --include='*.py' --include='*.ts' -r ./src 2>/dev/null
```

Scan the matches by hand: every one should construct the same envelope, ideally through one shared error-response helper, never an ad-hoc dict/object shape per handler.

### Pagination — cursor over offset

An unbounded list endpoint — one whose result count can grow without a known ceiling — uses cursor-based pagination, not offset/limit. Offset pagination re-scans skipped rows on every page and produces duplicate or missing rows when the underlying data mutates between requests.

```bash
grep -rEn "(offset|page)\s*:\s*(int|number)" --include='*.py' --include='*.ts' -r ./src 2>/dev/null
```

Any hit on a genuinely unbounded resource is offset pagination. Fix: replace it with an opaque cursor token derived from the last-seen item.

Grey zone — a resource with a known small bound (a user's own settings list, a fixed enum-backed lookup) may use offset/limit; the rule targets resources that grow without bound.

### Idempotency keys for unsafe retries

Every unsafe-method endpoint (a `POST` that creates or mutates state, not a pure read) that a caller might legitimately retry — payment, order creation — accepts and enforces an idempotency key, so a network-retried request does not double-execute.

```bash
grep -rlE "@(app|router)\.post|\.post\(" --include='*.py' --include='*.ts' -r ./src 2>/dev/null \
  | xargs grep -L "Idempotency-Key\|idempotency_key" 2>/dev/null
```

Any file listed defines a `POST` handler with no idempotency-key handling anywhere in it. Read each hit: an endpoint where duplicate execution is harmless (e.g., appending a log entry) can be exempted; a payment or order-mutating endpoint cannot.

### Timeouts and retries are part of the contract

Document the timeout budget and retry behavior an endpoint expects from its callers — and that it applies to any downstream service it calls — as explicitly as the schema. A caller that does not know whether a call is safe to retry will guess, and guess wrong under load.

### Idempotency key storage

An idempotency key's first-seen response is stored, keyed by the caller-supplied key, for at least as long as a client might plausibly retry; a repeated request with the same key returns the stored response instead of re-executing the operation. A key store with no expiry is a slow leak; one that expires before a realistic retry window defeats the guarantee.

```bash
grep -rEln "idempotency_key|Idempotency-Key" --include='*.py' --include='*.ts' -r ./src 2>/dev/null
```

Any matching file should also show a lookup-before-execute step, not just a header read with no dedupe logic — read the surrounding code to confirm the key is actually consulted, not merely accepted and ignored.

### Rate limiting is a security boundary, not a design contract (hand-off)

An API's rate-limit thresholds and abuse-detection rules belong to the `security` skill. This file only requires that a rate limit's existence and its retry-after behavior are part of the documented contract — a throttled client must be able to tell it was throttled and when to retry — not the specific threshold values or detection heuristics.

## Grey zones

- A field whose new meaning is genuinely ambiguous under the observed-behavior test defaults to breaking, not additive — the cost of an unnecessary version bump is lower than the cost of a silently broken client.
- A webhook payload is an outbound contract with the same rules as an inbound response: adding a field is safe, changing an existing field's meaning or removing one is a break for whoever already parses it.

## Incumbent-respect clause

Detect the naming, error-envelope, and pagination conventions this API already ships and match them for every new endpoint. Do not introduce a second error-envelope shape or a second pagination style "because it is cleaner" — propose a migration for the whole API as its own change.
