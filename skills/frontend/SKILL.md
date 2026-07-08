---
name: frontend
description: 'Gates frontend engineering on a rendering-architecture decision before UI code is written, then applies component-reuse layering, state-placement rules, and folder conventions. Use when building a React/Vue/Svelte page or component ("프론트엔드 구조 잡아줘"), asking "should this be a client or server component", choosing SPA vs SSR/RSC vs SSG vs islands for a new or existing app, deciding where a piece of state should live, or picking a folder convention (type-based, feature-based, layered feature-sliced) for a codebase. Not for API/server design — use backend; not for authoring design.md itself — use document.'
metadata:
  version: 2.1.0
---

# frontend

Frontend code is correct only relative to its rendering model: architecture first, component shape second, state placement third, folder convention fourth. Success looks like: the rendering architecture is detected (or chosen) before any UI code lands, `docs/design.md` exists before the first component is written, and the matching reference below was read before its topic was touched.

Four rendering models recur: **SPA** (empty HTML shell, browser renders everything client-side), **SSR/RSC** (server produces markup per request; RSC lets some components run server-only), **SSG** (every page built once, before any request), and **islands** (static HTML by default, a named few components hydrate in the browser). Full rules per model live in `references/architectures.md`.

## Phase 0 — rendering-architecture gate

Run before writing or editing any UI code, every time.

1. Detect the existing architecture:

   ```bash
   test -f next.config.js -o -f next.config.mjs -o -f next.config.ts && echo "SSR/RSC (Next.js)"
   test -d app && grep -rlE "[\"']use client[\"']" app 2>/dev/null | head -1 >/dev/null && echo "RSC boundary present"
   test -f astro.config.mjs -o -f astro.config.ts && echo "SSG/islands (Astro)"
   test -f gatsby-config.js && echo "SSG (Gatsby)"
   test -f vite.config.ts -o -f vite.config.js && ! test -f next.config.js -o -f next.config.mjs -o -f next.config.ts && echo "SPA (Vite) — confirm no server entry:"
   find . -maxdepth 2 -iname 'server.*' -not -path '*/node_modules/*'
   ```

   No hit on any of these → new project; run the decision table in `references/architectures.md`.

2. Read `references/architectures.md` in full, always — it carries the per-model absolute rules and the incumbent-respect rule. Then read whichever of these match scope:

   | Scope | Read |
   |---|---|
   | Component reuse, prop-API shape, extraction timing | `references/components.md` |
   | "Where does this state live" | `references/state.md` |
   | New project layout or folder-convention audit | `references/folders.md` |

3. Existing project → the detected architecture wins. Never introduce a second rendering runtime/framework (e.g. bolting a Vite/react-router SPA onto a Next.js `app/` router project), and never let a rendering-mode drift (SSR ↔ SSG ↔ client) inside the incumbent framework go unrecorded in `design.md`. Mixing SSR/SSG/client *within* one detected framework (Next.js, Astro both do this natively) is that framework's own architecture, not a second one. New project → run the decision table in `references/architectures.md` before scaffolding.

## The design.md gate

No UI component code — not a button, not a page shell — before the project has a `docs/design.md`.

```bash
test -f docs/design.md && echo "design.md present" || echo "MISSING — scaffold before writing UI code"
```

Missing → load the `document` skill's `references/design.md` and scaffold `docs/design.md` from its `templates/design.md` before the first component is written; this skill does not own the 7-section structure, lifecycle, or staleness/anti-generic detection — `document` does. Every commit that adds or changes a token, primitive, or pattern updates `design.md` in that same commit (law and detection command owned by `document`).

## Requirements

A project-local package manager and dev server (`npm`/`pnpm`/`bun` + the framework's dev command) for the detection commands above and any build-output checks in `references/architectures.md`; `git`, `grep`, `find` (POSIX) for the detection commands throughout this skill and its references.

## API boundary

Centralize the common API base, path prefix, version prefix, proxy, and BFF boundary once per app. React-only/Vite apps use env (`VITE_*`) plus one API client module; components and feature hooks call that client, not hardcoded host/base strings. Next.js apps use the incumbent boundary: `rewrites` for proxying, Route Handlers for a BFF, or server-component/server-action fetch for server-only calls. Detect the incumbent style; do not prescribe `/api/v1` universally.

## Anti-patterns

- Skipping the `docs/design.md` gate because the component is small → scaffold or update design.md first.
- Deferring SPA/SSR/SSG/islands choice until the app grows → choose the rendering model before the first route.
- Copying a pattern from a different rendering model → re-check it against `references/architectures.md`.
- Leaving state unclassified because it works → classify it against `references/state.md`.
- A component in a primitives/design-system layer importing from a feature directory → keep dependencies downward only (see `references/components.md`).
- Server-fetched data copied into a global UI store via `useEffect` + `setState` → keep server data in the server-data layer (see `references/state.md`).
- Mixing type-based and feature-based folders with no stated migration → follow one incumbent convention or plan a migration.
- Repeating API base URLs, path/version prefixes, proxies, or BFF routing in components/features → use the API boundary above instead of restating transport rules in feature code.

## Verification

- [ ] Phase 0 detection ran and its output is stated in the work notes or final report.
- [ ] `docs/design.md` exists (or was scaffolded via `document`) before any UI component code was written.
- [ ] `references/architectures.md` was read always; `components.md` / `state.md` / `folders.md` as the task touched them.
- [ ] No second rendering runtime was introduced; any rendering-mode drift is recorded in `design.md`.
- [ ] Every new or moved piece of state was classified against `references/state.md`.
- [ ] Component-dependency direction stayed downward only (primitives → composed → feature-bound).
- [ ] API base/prefix/version/proxy/BFF routing was centralized once and not repeated in components/features.
