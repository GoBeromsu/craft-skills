# REST conventions

Use these conventions when an incumbent API does not already establish a compatible public contract. Preserve an existing published convention unless changing it is explicitly scoped and versioned.

## URL and naming

| Concern | Default | Example |
|---|---|---|
| API base | One global server prefix and one client base URL | `/api/v1` |
| Collection | Plural kebab-case noun | `/projects`, `/team-members` |
| Member | Collection plus identifier | `/projects/{projectId}` |
| Containment | Parent member plus contained collection | `/teams/{teamId}/members` |
| Non-resource operation | Action only when resource modeling is misleading | `/exports/{exportId}:retry` |
| JSON property | camelCase | `createdAt`, `teamId` |
| Boolean property | `is`, `has`, or `can` prefix | `isArchived`, `hasAccess` |
| Enum value | Upper snake case | `PAYMENT_PENDING` |

Do not repeat `/api`, version, or a common resource prefix in each controller. Composition owns the global prefix; each handler declares only its resource-local segment.

## Pagination

Paginate every collection, including small collections; unbounded lists turn a harmless endpoint into a future availability problem.

| Situation | Default model | Request shape | Response shape |
|---|---|---|---|
| Stable, ordered feed or large mutable collection | Cursor | `?cursor=<opaque>&limit=50` | `items`, `nextCursor` |
| Administrative list with stable total and random access need | Offset | `?offset=0&limit=50` | `items`, `offset`, `limit`, `total` when practical |

Cap `limit` at a documented maximum and use a deterministic sort. Keep cursors opaque: clients pass them back but do not construct or parse them. Define whether a missing `nextCursor` means the final page, and return an empty `items` array rather than omitting the field.

## DTO boundary

Expose request and response DTOs, not database entities or framework objects. Validate required fields, type, range, format, and cross-field rules as the request enters the transport boundary. Translate validated DTOs to domain values once; later layers enforce business invariants rather than restating HTTP-shape validation.

Document field semantics, mutability, nullability, and default behavior. Add fields compatibly; do not silently change a field's meaning or reuse a retired enum value.
