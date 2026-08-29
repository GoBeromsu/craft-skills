---
name: frontend
description: 'Routes frontend engineering through incumbent-aware rendering, ownership, reuse, state, CSS, and performance decisions. Use when building or reorganizing a React/Vue/Svelte UI ("프론트엔드 구조 잡아줘"); choosing a React + Vite or Next.js shell, folder/public-API, or server/client boundary; improving component reuse or state ownership; selecting CSS Modules/Tailwind/CSS-in-JS and token structure; or setting frontend dependency, bundle, and CSS performance strategy. Not for material visual/UX judgment or DESIGN.md — use design; public API/server contracts — use api/backend; TypeScript-only work — use programming/refactor; test suites — use testing; skill updates — use skillify.'
metadata:
  version: 3.0.0
---

# frontend

Frontend structure is correct only relative to the incumbent framework, rendering model, product boundaries, and styling system. Establish those facts first, then keep framework mechanics in the shell, product behavior in cohesive slices, and shared code behind narrow supported APIs.

## Governing principles

1. Preserve the incumbent framework, router, package manager, styling system, and state tools unless migration is separately approved.
2. Let the framework shell own runtime mechanics; let routes, features, and domains own product behavior.
3. Evaluate dependency legality before public API access; a barrel never legalizes an invalid import.
4. Promote reuse only after real consumers share semantics and a reason to change.
5. Measure a production baseline and candidate with the same method; never claim an unobserved optimization.

## Runtime fact verification

Before relying on mutable framework, CLI, CSS-tool, or bundler behavior, inspect `package.json`, the authoritative lockfile, framework config, entrypoints, router mode, and installed styling/state tools. Follow the evidence contract in [Requirements](#requirements). A matching-version repository contract or reproducible local result overrides generic guidance. Leave unresolved capabilities unknown and preserve incumbent behavior.

## Phase 0 — classify before changing

1. Classify the repository:

   | Evidence | Classification | Action |
   |---|---|---|
   | Manifest, config, entrypoint, and imports agree | Known incumbent | Use its native runtime and conventions. |
   | Frontend evidence exists but conflicts or is incomplete | Unknown incumbent | Inspect local entrypoints/imports; make only the smallest compatible change. |
   | No manifest, framework config, entrypoint, or frontend source exists | Truly greenfield | Choose a rendering model before scaffolding. |

2. Classify the work:

   | Concern | Owner | Read |
   |---|---|---|
   | Rendering model, framework shell, React/Vite or Next runtime | Shell / route adapter | [`references/architectures.md`](references/architectures.md) |
   | Folder convention, slices, public APIs, promotion | Route / feature / entity / shared | [`references/folders.md`](references/folders.md) |
   | Reusable component API, composition, accessibility | Owning component or slice | [`references/components.md`](references/components.md) |
   | Server, URL, form, global, or local state | Closest coherent state owner | [`references/state.md`](references/state.md) |
   | Stylesheet organization, tokens, theming, CSS delivery/performance | Shell, component, or route-private style owner | [`references/css.md`](references/css.md) |

3. Read only the references touched by the request. A rendering-architecture change reads `architectures.md`; a CSS-only correction does not load every reference.

## Shell, slice, and promotion rules

| Level | Owns | Must not own |
|---|---|---|
| Framework shell | Bootstrap, router, providers, layouts, loading/error surfaces, metadata, global-style entry | Product workflows or feature-specific data rules |
| Route/page | URL composition and route-private UI | Reusable lower-layer internals exposed by deep paths |
| Feature/domain slice | One user capability or stable product concept with its model, API, and UI | Peer-slice internals or framework bootstrap |
| Shared | Business-neutral primitives and focused libraries with named ownership | Code placed there only because its owner is unclear |

These are logical owners, not mandatory folder names. Map them onto a coherent incumbent route-colocated, module-based, type-based, feature-based, or FSD structure. Introducing `features/`, `entities/`, or `shared/` into a different incumbent convention is a separately approved migration, not a feature-edit default.

Keep code route- or feature-private first. Promote it only when multiple real consumers share semantics and a reason to change, then expose the smallest environment-safe public API and remove obsolete deep paths in the same change. Exact import and promotion rules live in `references/folders.md`.

## Design judgment handoff

Call `design` only when work changes what users perceive, understand, decide, or can accomplish, or changes reusable visual/interaction language, tokens, primitives, cross-state/cross-viewport presentation, or accessibility experience.
`design` owns `DESIGN.md` and the design judgment; `frontend` implements approved design decisions.
Keep rendering architecture, established-system implementation, faithful use of existing primitives, small fixes, CSS regressions, state placement, components, folders, and API boundaries within `frontend`.

## Requirements

- Node.js for project-local tooling. Probe with `node --version`; use the Node range supported by the detected framework version.
- Inspect dependencies and package manager without mutating them:

  ```bash
  node -e "const p=require('./package.json'); console.log(JSON.stringify({packageManager:p.packageManager,dependencies:p.dependencies,devDependencies:p.devDependencies},null,2))"
  for f in package-lock.json npm-shrinkwrap.json pnpm-lock.yaml yarn.lock bun.lock bun.lockb; do test -f "$f" && printf '%s\n' "$f"; done
  ```

- Use one authoritative lockfile. If multiple lockfiles exist, resolve ownership before an install or version claim.
- For every mutable React, Next.js, Vite, CSS-tool, router, or state capability, record: detected version/probe, official source, support boundary, and the release/update condition that requires re-review. Use a versioned official page, release tag, commit permalink, matching local types, or reproducible behavior for version-sensitive claims. Treat `main`, `canary`, and latest-branch pages as discovery sources, not proof of installed behavior.
- Official discovery sources: [React](https://react.dev/), [Next.js](https://nextjs.org/docs), [Vite](https://vite.dev/guide/), [Vue](https://vuejs.org/guide/), [Svelte](https://svelte.dev/docs), and [Astro](https://docs.astro.build/).
- Add a dependency only after the platform, framework, and incumbent stack cannot meet a concrete requirement. Record maintenance, bundle/runtime, SSR/RSC, security/license, and lockfile consequences. Do not add a router, global store, CSS framework, component kit, or analyzer by default.

## API boundary

Centralize the API base, path/version prefix, proxy, and BFF boundary once per app. React/Vite apps use `VITE_*` environment values plus one API client; components call slice APIs, not hardcoded hosts. Next apps preserve the incumbent server-fetch, Route Handler, Server Action, or rewrite boundary. Public HTTP contracts belong to `api`; service architecture belongs to `backend`.

## Anti-patterns

- Framework shell contains checkout/catalog/user business logic → move behavior to its route or slice and keep the shell as composition.
- Root `components/`, `hooks/`, `types/`, or `utils/` becomes the primary product architecture → colocate by capability or retain a separately documented small-app convention ([`folders.md`](references/folders.md)).
- Upward, forbidden peer-slice, or deep internal import → fix dependency direction first, then import a narrow public API ([`folders.md`](references/folders.md)).
- First similar implementation moves to `shared` → keep it local until semantics, consumers, ownership, and regression coverage justify promotion ([`folders.md`](references/folders.md)).
- Primitive knows routing, fetching, authorization, or analytics; component API grows boolean matrices → restore a semantic reusable contract ([`components.md`](references/components.md)).
- Derived data, URL state, or server data is mirrored through effects/global stores → return it to its single owner ([`state.md`](references/state.md)).
- Global selectors, duplicated tokens, competing styling systems, or `!important` escalation spread across features → restore scoped ownership and the incumbent cascade ([`css.md`](references/css.md)).
- Version-blind install/upgrade advice → inspect the manifest, lockfile, and matching-version evidence first.
- Memoization, chunking, critical CSS, preload, or client-boundary changes lack a production baseline → measure before and after or make no optimization claim.

## Verification

- [ ] Incumbent framework, router, package manager, lockfile, styling/state tools, and relevant versions were recorded.
- [ ] The framework shell contains runtime mechanics, not product behavior; route and slice ownership is explicit.
- [ ] Dependency legality, public APIs, server/client graph safety, and obsolete-path removal were checked.
- [ ] Component semantics, keyboard/focus behavior, variants, and controlled/uncontrolled ownership were tested where applicable.
- [ ] State refresh, back/forward navigation, mutation invalidation, serialization, and hydration were checked where applicable.
- [ ] CSS computed states, responsive/forced-colors/reduced-motion behavior, visual stability, and route delivery were checked where applicable.
- [ ] Production measurements use the same collection method for baseline and candidate and record source, delta, project threshold, and interpretation. Mark unavailable consumer telemetry N/A; never fabricate it.
- [ ] Visual work captures relevant states and viewports after the final edit; diff numbers direct review attention but do not decide correctness alone.
- [ ] `design` was called only for material visual/UX judgment; implementation stayed in `frontend`, and `DESIGN.md` ownership stayed in `design`.
