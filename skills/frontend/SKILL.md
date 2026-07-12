---
name: frontend
description: 'Routes frontend engineering through incumbent-aware rendering and design-scope decisions, then applies component-reuse layering, state-placement rules, and folder conventions. Use when building a React/Vue/Svelte page or component ("프론트엔드 구조 잡아줘"), asking "should this be a client or server component", choosing SPA vs SSR/RSC vs SSG vs islands for a new or existing app, deciding where a piece of state should live, or picking a folder convention (type-based, feature-based, layered feature-sliced) for a codebase. Not for API/server design — use api(공개 HTTP 계약)/backend(서비스 구조); not for authoring design.md itself — use document.'
metadata:
  version: 2.2.0
---

# frontend

Frontend code is correct relative to its rendering model and incumbent UI system: establish the relevant evidence before structural work, then shape components, state, and folders to match. Success looks like a known rendering decision for architecture work, documented design-system changes, and verification that reflects the user-facing result.

Four rendering models recur: **SPA** (empty HTML shell, browser renders everything client-side), **SSR/RSC** (server produces markup per request; RSC lets some components run server-only), **SSG** (every page built once, before any request), and **islands** (static HTML by default, a named few components hydrate in the browser). Full rules per model live in `references/architectures.md`.

## Phase 0 — rendering and design routing

Run this before structural frontend work; a small fix or composition using an existing primitive does not need a new architecture or design-document gate.

1. Classify the repository from `package.json` dependencies and scripts, framework configuration, explicit entrypoints (`app/`, `pages/`, `src/main.*`, `src/index.*`, server entries), and existing route/component source.

   | Evidence | Classification | Action |
   |---|---|---|
   | These sources consistently identify a framework and rendering model | Known incumbent | Follow that framework and its native rendering modes; do not add a second runtime. |
   | Source or a manifest exists, but evidence is missing or conflicts | Unknown incumbent | Inspect the local entrypoint and imports, make the smallest compatible change, and do not scaffold or migrate a rendering runtime. |
   | No manifest, framework config, entrypoint, or frontend source exists | Truly greenfield | Choose a model with the decision table in `references/architectures.md` before scaffolding. |

   Framework configuration remains useful corroboration:

   ```bash
   test -f next.config.js -o -f next.config.mjs -o -f next.config.ts && echo "SSR/RSC (Next.js)"
   test -d app && grep -rlE "[\"']use client[\"']" app 2>/dev/null | head -1 >/dev/null && echo "RSC boundary present"
   test -f astro.config.mjs -o -f astro.config.ts && echo "SSG/islands (Astro)"
   test -f gatsby-config.js && echo "SSG (Gatsby)"
   test -f vite.config.ts -o -f vite.config.js && echo "SPA (Vite) — confirm no server entry:"
   find . -maxdepth 2 -iname 'server.*' -not -path '*/node_modules/*'
   ```

2. Read `references/architectures.md` when choosing or changing a rendering architecture. Read it for a truly-greenfield app before scaffolding. Then read whichever of these match scope:

   | Scope | Read |
   |---|---|
   | Component reuse, prop-API shape, extraction timing | `references/components.md` |
   | "Where does this state live" | `references/state.md` |
   | New project layout or folder-convention audit | `references/folders.md` |

3. An incumbent architecture wins. Do not introduce a second rendering runtime/framework (for example, a Vite/react-router SPA beside a Next.js `app/` router); rendering-mode migration is separately scoped. Native SSR/SSG/client mixing within Next.js or Astro remains that framework's own architecture.

## The design.md gate

Before a change to rendering architecture, a design system, tokens, or a material visual change, read or update `docs/design.md`. A small rendering/interaction fix or use of an existing primitive proceeds without pre-documentation; preserve the incumbent pattern and verify the result.

```bash
test -f docs/design.md && echo "design.md present" || echo "MISSING — document this structural design change before implementation"
```

When the gate applies and the document is missing, load the `document` skill's `references/design.md` and scaffold `docs/design.md` from its `templates/design.md`; this skill does not own the 7-section structure, lifecycle, or staleness/anti-generic detection — `document` does. Record a changed rendering decision, token, primitive, or material visual result in that document with its implementation.

## Requirements

A project-local package manager and dev server (`npm`/`pnpm`/`bun` + the framework's dev command) for the detection commands above and any build-output checks in `references/architectures.md`; `git`, `grep`, `find` (POSIX) for the detection commands throughout this skill and its references.

## API boundary

Centralize the common API base, path prefix, version prefix, proxy, and BFF boundary once per app. React-only/Vite apps use env (`VITE_*`) plus one API client module; components and feature hooks call that client, not hardcoded host/base strings. Next.js apps use the incumbent boundary: `rewrites` for proxying, Route Handlers for a BFF, or server-component/server-action fetch for server-only calls. Detect the incumbent style; do not prescribe `/api/v1` universally.
Use `programming` alongside this skill for per-file TypeScript/JavaScript discipline; a rendering decision does not replace that language-level contract.


## Anti-patterns

- Skipping `docs/design.md` for a rendering-architecture, design-system, token, or material visual change → document the structural decision before implementation.
- Deferring SPA/SSR/SSG/islands choice until the app grows → choose the rendering model before the first route.
- Copying a pattern from a different rendering model → re-check it against `references/architectures.md`.
- Leaving state unclassified because it works → classify it against `references/state.md`.
- A component in a primitives/design-system layer importing from a feature directory → keep dependencies downward only (see `references/components.md`).
- Server-fetched data copied into a global UI store via `useEffect` + `setState` → keep server data in the server-data layer (see `references/state.md`).
- Mixing type-based and feature-based folders with no stated migration → follow one incumbent convention or plan a migration.
- Repeating API base URLs, path/version prefixes, proxies, or BFF routing in components/features → use the API boundary above instead of restating transport rules in feature code.
- Treating missing framework-config hits as proof of a greenfield app → inspect manifests, entrypoints, and source; preserve an unknown incumbent rather than scaffolding over it.

## Verification

- [ ] Structural work was classified as known incumbent, unknown incumbent, or truly greenfield from manifests, configs, entrypoints, and source.
- [ ] `references/architectures.md` was read for a rendering-architecture decision; `components.md` / `state.md` / `folders.md` were read only as the task touched them.
- [ ] `docs/design.md` was updated before a rendering-architecture, design-system, token, or material visual change; small fixes and existing-primitive usage were not blocked on pre-documentation.
- [ ] No second rendering runtime was introduced; any rendering-mode change is separately scoped and documented.
- [ ] Every new or moved piece of state was classified against `references/state.md`.
- [ ] Component-dependency direction stayed downward only (primitives → composed → feature-bound).
- [ ] API base/prefix/version/proxy/BFF routing was centralized once and not repeated in components/features.
- [ ] For a visual result, capture every relevant state and viewport after the last edit, compare same-size captures, and use diff numbers to direct reviewer attention rather than declare a verdict.
