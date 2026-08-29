# Frontend Rendering Architectures

A rendering model defines when and where markup, data access, and interactivity run. Preserve the detected framework's native model and keep its runtime shell separate from product slices. Version-sensitive behavior follows the evidence owner in [`../SKILL.md#requirements`](../SKILL.md#requirements).

## Contents

- [Framework shell contract](#framework-shell-contract)
- [Rendering decision](#rendering-decision)
- [React and Vite SPA shell](#react-and-vite-spa-shell)
- [Next.js App Router shell](#nextjs-app-router-shell)
- [SSR and RSC](#ssr-and-rsc)
- [SPA](#spa)
- [SSG](#ssg)
- [Islands](#islands)
- [Dependency admission](#dependency-admission)
- [Measurement-led verification](#measurement-led-verification)
- [Incumbent-respect clause](#incumbent-respect-clause)
- [Hand-offs](#hand-offs)

## Framework shell contract

| Shell owns | Product slices own |
|---|---|
| Bootstrap and framework entrypoint | User capabilities and domain behavior |
| Router, layouts, loading/error boundaries, metadata | Feature/entity model, API adapters, and UI |
| Providers and runtime-only adapters | Route-private and reusable compositions |
| Global style entry, root tokens, fonts, document defaults | Locally scoped component and route styles |

The shell composes product slices; lower layers never import the shell. Do not put catalog, checkout, account, or other product workflows in providers, layouts, middleware, or root entrypoints merely because those files are globally reachable.

## Rendering decision

| Need | Prefer | Verify before choosing |
|---|---|---|
| Auth-gated, interaction-heavy app with no public SEO requirement | SPA | Browser-only execution and client data/runtime cost are acceptable. |
| Request-varying or protected data plus server rendering/streaming | SSR/RSC | Installed framework supports the required server/client and cache behavior. |
| Content resolved at build time | SSG | No request-specific data or headers are required. |
| Mostly static HTML with isolated interactivity | Islands | Interactive pieces can remain independent and narrowly hydrated. |

A framework can natively combine modes. Next App Router can compose server and client components and static/dynamic routes; Astro can combine static pages, islands, and supported server routes. That native combination is one framework contract, not permission to add a second router or rendering runtime.

## React and Vite SPA shell

Use this as a semantic map only when a feature-sliced layout is incumbent or separately approved:

```text
<current source root>/
  <current shell owner>/
    <current browser entry>
    router/
    providers/
    styles/
  pages/
  features/
  entities/
  shared/
```

- Confirm Vite plus a browser entry and absence of a framework/server entry before classifying the app as an SPA. Vite is build tooling, not a rendering model by itself.
- In a coherent route-colocated, `modules/`, or type-based incumbent, map these logical responsibilities onto existing paths. Do not create parallel `features/`, `entities/`, or `shared/` roots without a separately approved folder migration.
- Shell ownership does not authorize relocating `src/main.*`, the router, providers, or the global-style entry.
- Preserve the incumbent router. If none exists, do not add one until navigation requirements justify it.
- Keep `main`, router registration, providers, error boundary, and global-style import in the shell.
- Keep route composition in the incumbent route/page location; keep product behavior in route-private code or slices.
- Read client-exposed values only through the installed Vite version's documented `VITE_*` mechanism. Never expose secrets to the client bundle.
- Split heavy or deferred routes/components only when the installed router/build supports the boundary and production output proves the work leaves the initial path. Declare `lazy` components at module scope.
- Run a separate typecheck because Vite transpilation and application type checking are distinct concerns; use the repository's existing script rather than inventing one.

## Next.js App Router shell

The incumbent root `app/` or `src/app/` directory is the routing shell. When feature-sliced product folders are already incumbent or separately approved, use this mapping:

```text
src/
  app/                 # route segments, layouts, loading/error, metadata
  features/
  entities/
  shared/
```

This is an incumbent-friendly FSD subset, not the canonical FSD Next mapping. It absorbs FSD App and Pages responsibilities into Next's routing shell and may omit Widgets. The canonical [FSD Next.js guide](https://fsd.how/docs/guides/tech/with-nextjs/) separates the framework `app/` from prefixed `_app` and `_pages` layers. Preserve either incumbent; never migrate between them as a feature side effect.

- If the incumbent instead colocates code under route-private folders, uses `modules/`, or follows a type-based convention, preserve that physical layout. Map shell, route, domain, and shared ownership onto its existing paths and introduce feature-sliced siblings only through an explicit architecture migration.
- Shell ownership never authorizes moving the root `app/`, route-private modules, or global-style import.
- Pages and layouts remain Server Components by default when the installed Next version supports App Router semantics.
- Put `'use client'` on the smallest interactive entry. Everything imported by that entry belongs to the client graph, so a high boundary can enlarge shipped JavaScript.
- Fetch and authorize server data in server-only modules or an incumbent data-access boundary. Pass minimal serializable values to client leaves.
- Keep server-only and client-safe exports separate when one public entry would leak environment-specific code; an `index.server.ts`-style entry is valid only when supported and needed.
- Route groups/private folders organize routing and colocation; they do not enforce product-module boundaries.
- Keep global CSS at the framework-supported root entry. Colocate route-private and component styles without turning route files into global selector patches.
- Use the installed Next build/analyzer surfaces for server/client and route output. Do not mix Vite into a Next application.

## SSR and RSC

- A server-only module never enters a client import graph.
- Browser APIs run only below an explicit client boundary.
- Secrets and authorization remain server-side.
- Server data is read on the server by default; client fetching is for genuinely client-interactive or live behavior.
- Treat exported server operations as externally reachable: validate and authorize every call.
- Pass purpose-built minimal DTOs rather than raw database records or broad objects.

A percentage of client components is not a verdict. Review tree placement: a client root layout or broad provider is more consequential than several small client leaves.

## SPA

- Treat every application module as browser-executable unless an explicit build-time boundary says otherwise.
- Keep shareable filter/tab/search/page state in the URL.
- Split only meaningful deferred routes or heavy interactions; many tiny chunks can add request and compression costs.
- Centralize API transport once and keep backend authority on the server.

## SSG

- Resolve static content at build time.
- Do not read request headers, cookies, or per-user data in build-time code.
- Add client fetching or a supported dynamic route only for data that truly varies after build.
- Verify generated HTML, metadata, links, and stale-content/rebuild behavior.

## Islands

- Ship static HTML by default and hydrate only named interactive islands.
- Choose the narrowest supported hydration trigger.
- Do not assume implicit shared client state across independent islands.
- Verify that non-hydrated controls do not appear interactive and that each island works after isolated hydration.

## Dependency admission

Start from platform and framework capabilities, then existing packages. Add a dependency only when a concrete requirement remains unmet and record its bundle/runtime, SSR/RSC, maintenance, security/license, and lockfile effects. Branch-head documentation can discover an option; matching-version documentation, types, release tags, commit permalinks, or local reproduction prove support.

Do not add a router, store, CSS system, component kit, analyzer, or compatibility plugin as a baseline stack. Next uses its framework toolchain; React SPA projects may use Vite when selected, but Vite is not a Next dependency.

## Measurement-led verification

Record a production baseline and candidate with the same commands, route, state, device/network assumptions, and artifact source.

| Surface | Evidence |
|---|---|
| Rendering | Generated HTML/RSC behavior, metadata, loading/error states, hydration/runtime errors |
| Client boundary | Client-entry tree and unexpected server-only/client imports |
| JavaScript | Initial and route chunk bytes, request count, parse/long-task evidence when relevant |
| CSS | Initial/route CSS bytes, order, unused coverage after representative interactions |
| User experience | LCP, INP, CLS, accessibility, and visual-state evidence against project thresholds |

A smaller bundle is not automatically better if it creates a waterfall or delays interaction. When no consumer application exists, verify that the skill prescribes collection source, baseline, delta, threshold, and interpretation; mark actual runtime values N/A.

## Incumbent-respect clause

Detect the framework, router, version, rendering model, and entrypoints before changing structure. Follow native framework modes and preserve an existing folder mapping. A rendering-model, router, or canonical-FSD migration is a separately approved change.

## Hand-offs

- Slice ranks, public APIs, and promotion → [`folders.md`](folders.md).
- Component server/client compatibility and reusable APIs → [`components.md`](components.md).
- Server-cache, URL, and local state → [`state.md`](state.md).
- CSS ownership and delivery → [`css.md`](css.md).
