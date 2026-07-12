# REST conventions

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
