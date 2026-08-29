# Frontend Folder Conventions

A folder convention is useful only when it communicates ownership and constrains imports. Preserve an incumbent convention; for new or structurally failing applications, prefer a framework shell with cohesive product slices and explicit public APIs.

## Contents

- [Decision table](#decision-table)
- [Type-based](#type-based)
- [Feature-based](#feature-based)
- [Framework shell and feature-sliced layers](#framework-shell-and-feature-sliced-layers)
- [React and Vite mapping](#react-and-vite-mapping)
- [Next.js App Router mapping](#nextjs-app-router-mapping)
- [Public APIs and dependency direction](#public-apis-and-dependency-direction)
- [Controlled promotion](#controlled-promotion)
- [Review procedure](#review-procedure)
- [Incumbent-respect clause](#incumbent-respect-clause)
- [Hand-offs](#hand-offs)

## Decision table

| Convention | Fits when | Contract |
|---|---|---|
| Type-based | Small, low-domain app where technical buckets remain easy to navigate | Name folders by technical kind; acknowledge weak product ownership. |
| Feature-based | Product capabilities are the main unit of change | Colocate UI, model, and API by capability; expose deliberate cross-feature contracts. |
| Layered feature-sliced | Import direction, domain ranks, and team boundaries need stronger enforcement | Framework shell composes lower product layers; slices are isolated by default. |

Route count is a signal, not policy. Team/domain ownership, change locality, import cycles, and navigation cost decide when a simple convention has failed. Do not mix conventions during an unrelated feature; propose migration separately.

## Type-based

Typical shape: `components/`, `hooks/`, `pages/`, `services/`, `types/`, `utils/`.

- Use while the codebase is genuinely small and cohesive.
- Name focused libraries by purpose (`date/`, `currency/`, `validation/`) rather than allowing `utils/` to become an unowned dump.
- Keep route-specific code close to its route even if the top-level structure remains type-based.
- When one product change repeatedly touches many distant technical buckets, record that as evidence for a separately scoped feature-based migration.

## Feature-based

```text
src/
  app/
  features/
    checkout/
      ui/
      model/
      api/
      index.ts
  shared/
```

- A feature owns one meaningful user capability.
- Another feature does not deep-import its `ui/`, `model/`, `api/`, or `lib/` internals.
- Route-private code remains route-private until reuse is demonstrated.
- `shared` admits only business-neutral or deliberately stable cross-context contracts with named ownership.

A feature folder is not proof of a boundary. Its imports and supported exports must enforce the same ownership.

## Framework shell and feature-sliced layers

Current FSD documents seven historical layers: App, Processes, Pages, Widgets, Features, Entities, and Shared. Processes is deprecated, leaving six non-deprecated layers. Projects may omit layers that add no value; current guidance also treats Widgets as optional and often unnecessary. Source: [FSD layers](https://fsd.how/docs/reference/layers/).

| Rank, high to low | Responsibility |
|---|---|
| App / framework shell | Bootstrap, routing, providers, global runtime concerns |
| Pages | Route/screen compositions when not already absorbed by the framework router |
| Widgets, optional | Large reusable page blocks; omit when Features/Pages express ownership better |
| Features | Reused user capabilities and interactions |
| Entities | Stable product/domain concepts and their model/UI/API |
| Shared | Business-neutral UI, integrations, config, and focused libraries |

A layer contains slices partitioned by product meaning; a slice contains technical-purpose segments such as `ui`, `model`, `api`, and `lib`. Segment names are local details, not global root buckets. Sources: [slices and segments](https://fsd.how/docs/reference/slices-segments/) and [public API](https://fsd.how/docs/reference/public-api/).

Dependency rule: a slice may import lower layers, its own internals, and only documented exceptions. Lower layers never import higher layers. Same-layer slices do not import one another by default.

## React and Vite mapping

For a confirmed React SPA using Vite or equivalent browser tooling, this mapping applies only when feature-sliced folders are incumbent or separately approved:

```text
src/
  app/                 # main, router, providers, error boundary, global-style entry
  pages/               # route composition when the incumbent router uses it
  widgets/             # optional
  features/
  entities/
  shared/
```

Vite owns build integration, not route semantics. Preserve the incumbent router and aliases. Omit unused layers; do not scaffold empty directories to appear compliant. For a coherent route-colocated, `modules/`, or type-based incumbent, retain its paths and map shell/domain/shared responsibilities logically. Do not add parallel `features/`, `entities/`, or `shared/` roots during an unrelated feature. The example does not authorize relocating `src/main.*`, router/provider registration, or the global-style entry.

## Next.js App Router mapping

For an App Router project where feature-sliced product folders are incumbent or separately approved:

```text
src/
  app/                 # Next route shell; absorbs FSD App and Pages responsibilities
  features/
  entities/
  shared/
```

This is an incumbent-friendly FSD subset, not canonical FSD Next topology. Next `app/` owns route segments, layouts, loading/error boundaries, metadata, and route composition. Product slices live as siblings. Do not create a second `app` or parallel `pages` router.

The canonical [FSD Next.js guide](https://fsd.how/docs/guides/tech/with-nextjs/) keeps the framework `app/` beside prefixed `_app` and `_pages` layers. Preserve that structure when incumbent or adopt it only through an explicit architecture change. Never silently migrate between the canonical and one-shell mappings.

In either mapping, server/client module graphs remain an additional boundary: client entries cannot expose server-only internals. For a coherent route-colocated, `modules/`, or type-based Next incumbent, preserve those physical paths and apply the same dependency/public-API rules there. Do not introduce FSD-shaped siblings merely because the framework uses one `app` shell.

## Public APIs and dependency direction

Evaluate dependency legality first. If an edge is upward or forbidden between peer slices, importing through `index.ts` does not make it valid.

For a legal external consumer:

- Export only supported capabilities from the slice root or incumbent package entry.
- Import slice internals relatively from within the same slice; do not route internal imports back through the public barrel.
- Prefer explicit exports over wildcard exports.
- Avoid one application-wide barrel and broad `shared/ui` re-export trees; they can create cycles, unnecessary transforms, and accidental surfaces.
- Use environment-specific entries only when one surface would expose server-only code to a client graph. Keep a client-safe default entry such as `index.ts` and a server-only entry such as `index.server.ts`; neither entry re-exports the other. Client consumers import only the client-safe surface, and server consumers name the server surface explicitly.
- Check type-only imports and aliases too; they still express architectural coupling even when erased at runtime.

FSD documents a narrow Entities-layer `@x` exception for entities that genuinely contain or must refactor with one another. Keep the default same-layer ban. Use `@x` only when the relationship is explicit, limited to the named consumer, and maintained as one refactor unit; do not generalize it to Features or arbitrary peers.

Example legal consumer:

```ts
import { CheckoutForm } from "@/features/checkout";
```

Deep import to reject:

```ts
import { CheckoutForm } from "@/features/checkout/ui/internal/CheckoutForm";
```

## Controlled promotion

Use this ladder:

1. Keep the first implementation inside its route or owning feature.
2. When another consumer appears, compare semantics and expected reason to change; do not extract on visual similarity alone.
3. Review promotion after three real consumers, but treat three as a trigger rather than automatic approval.
4. Promote only when the target layer is legal, ownership is named, the API is narrow, and regression coverage protects all consumers.
5. Rewrite consumers to the supported API and remove obsolete/deep paths in the same change. Do not leave compatibility barrels.

An Entity requires one stable domain meaning across higher-level capabilities. A Shared module must be business-neutral or an intentionally stable cross-context contract. Small duplicated presentation can be cheaper than a wrong shared abstraction.

## Review procedure

1. Identify the framework shell and incumbent convention.
2. Map changed files to route, feature, entity, or shared ownership.
3. Inspect actual imports with the project's TypeScript/lint/workspace tooling; regex examples are hints, not proof.
4. Reject upward and forbidden peer edges before reviewing barrels.
5. Inspect public exports, internal deep imports, cycles, aliases, and server/client graph crossings.
6. For moved code, verify every consumer and delete obsolete paths.
7. Record any convention migration as a separate plan with its own build, route, and behavior verification.

## Incumbent-respect clause

Follow the existing convention when it has coherent ownership and enforceable imports. A flat unowned bucket is evidence of missing architecture, but it is not permission for a feature request to migrate the whole application. Add the smallest local boundary and separately propose structural migration.

## Hand-offs

- Runtime shell and server/client rules → [`architectures.md`](architectures.md).
- Component abstraction and supported props → [`components.md`](components.md).
- State ownership inside slices → [`state.md`](state.md).
- CSS locality and token/style ownership → [`css.md`](css.md).
- Per-file TypeScript and circular-import discipline → `programming`.
