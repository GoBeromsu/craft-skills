# REST conventions

## Contents

- [Incumbent contract gate](#incumbent-contract-gate)
- [URL, success DTOs, and naming](#url-success-dtos-and-naming)
- [Pagination](#pagination)
- [Auditing an existing surface for drift](#auditing-an-existing-surface-for-drift)
- [Method completeness](#method-completeness)
- [The client side of the contract](#the-client-side-of-the-contract)

## Incumbent contract gate

Before applying a default, inspect the published routes, client configuration, API descriptions, and representative responses. For an existing API, preserve its URL base, success envelope, pagination model, JSON naming, and error shape. A public change requires an explicit version or migration scope and a client-compatibility note; do not normalize an incumbent as cleanup.

Apply the following defaults only to a greenfield API or an explicitly new API version.

## URL, success DTOs, and naming

| Concern | Default | Example |
|---|---|---|
| API base | One global server prefix and one client base URL | `/api/v1` |
| Collection | Plural kebab-case noun | `/projects`, `/team-members` |
| Member | Collection plus identifier | `/projects/{projectId}` |
| Containment | Parent member plus contained collection | `/teams/{teamId}/members` |
| Non-resource operation | Action only when resource modeling is misleading | `/exports/{exportId}:retry` |
| Success payload | Response DTO without a generic envelope | `{ "projectId": "…" }` |
| JSON property | camelCase | `createdAt`, `teamId` |
| Boolean property | `is`, `has`, or `can` prefix | `isArchived`, `hasAccess` |
| Enum value | Upper snake case | `PAYMENT_PENDING` |

Composition owns the global prefix; each handler declares only its resource-local segment. Expose request and response DTOs rather than database entities or framework objects. Validate transport shape once at the DTO boundary, then translate to typed domain values; later layers enforce business invariants rather than repeating HTTP-shape validation.

## Pagination

Paginate every greenfield collection. Use cursor pagination for a stable ordered feed or large mutable collection; otherwise use bounded offset pagination for an administrative list that needs stable totals or random access.

| Model | Request shape | Response shape |
|---|---|---|
| Cursor | `?cursor=<opaque>&limit=50` | `items`, `nextCursor` |
| Offset | `?offset=0&limit=50` | `items`, `offset`, `limit`, `total` when practical |

Cap `limit` at a documented maximum, use a deterministic sort, and keep cursors opaque. Define whether a missing `nextCursor` means the final page, and return an empty `items` array rather than omitting it. Document field semantics, mutability, nullability, and defaults; add fields compatibly and never silently repurpose a field or retired enum value.

## Auditing an existing surface for drift

A convention that lives only in a contributor guide decays, because nothing fails when it is ignored.
Audit the incumbent surface with one grep per rule and treat the table as the review checklist until each row becomes a lint rule.
The drift column records what one such audit actually found, as calibration for how far a written-but-unenforced convention drifts.

| Rule | Drift found in one audit | Check |
|---|---|---|
| One router per slice carries the prefix; decorators declare only the relative segment | 8 routers set a prefix and 8 spelled out full paths | `grep -n "APIRouter(" <features>/*/router*.py` |
| Wire models are validating schema classes with unknown fields forbidden, never plain data classes | frozen dataclasses used as wire models in three router modules | `grep -n "@dataclass" <features>/*/router*.py` |
| DTOs live in the slice's schema module | only one slice had one; another router carried 18 inline models | `grep -c "class .*BaseModel" <features>/*/router.py` |
| Every route declares its response model | about 15 routes had none | grep the decorators and filter for the response-model argument |
| Structured errors use exactly one discriminator key | three were in use at once: `code`, `error`, `error_class` | `grep -rn '"code":\|"error":\|"error_class":' <features>` |
| Status codes use the framework's named constants, one spelling per code | raw `206`/`416`/`400` literals, plus two spellings of the same 422 constant | `grep -rn "status_code=[0-9]" <features>` |

Two spellings of one constant are grep noise that hides real drift; standardise on one.
Which discriminator key wins is a team decision rather than a derivable one — record the choice in the repository's own contract document and grep for the rejected alternatives in CI.

## Method completeness

A route registered for one method answers 404 for its siblings, and a framework does not necessarily synthesise `HEAD` from `GET`.
Confirm this against the incumbent framework's official routing documentation and one real request rather than assuming either behavior: in one measured case the framework's own route class did not synthesise `HEAD` while its underlying toolkit's plain route did, so a media route answered 200 to `GET` and 404 to `HEAD`.

Register both methods on **one** endpoint so headers, authorization, range handling, and audit are computed once, and make `HEAD` send zero bytes — verified by measuring both responses, which returned 0 and 2,770,760 bytes for the same resource.
Leave an unbounded stream with no content length `GET`-only, and pin its 405 with a test.

## The client side of the contract

Route every call through one client module rather than scattered fetches, and give each success envelope a normalizer that rejects an unknown shape instead of asserting a type over it.
A cast is not parsing: it silently accepts whatever arrived.

Features never reach into an error response's body; narrow helpers for that live beside the client, because a feature that reads an error's inner field re-implements the error contract in one screen.
When client DTOs are hand-written with no generation from the server schema, a server field change is invisible until a normalizer test fails — so keep those tests table-driven against real captured fixtures.
