---
name: frontend
description: '"build a React page", "프론트엔드 구조 잡아줘", "make this component reusable", "SSR or SPA", "build a landing page", "fix this UI", "how should I organize state", "which folder structure for this app" — rendering-architecture-gated frontend engineering: SPA/SSR-RSC/SSG/islands absolute rules, component reuse layers, state taxonomy, and folder conventions, gated on a project design.md.'
version: 1.0.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
compatibility: claude-code, codex
---

# frontend

Frontend code is correct only relative to its rendering model: **rendering architecture first, component shape second, state placement third, folder convention fourth.** Get the first one wrong and the other three inherit the mistake.

## Overview

This skill is an index. Shared rules and both hard gates live here; the per-topic iron list lives in `references/`. Load the matching reference before writing a line of UI code. A rendering model is the contract a browser or server makes about when and where a component's markup is produced (build time, request time, or client runtime) — get this contract wrong and every downstream choice (data fetching, state, bundle shape) is built on sand.

Four rendering models recur through this skill: **SPA** (single-page app — an empty HTML shell ships once, and the browser renders everything client-side afterward), **SSR/RSC** (server-side rendering / React Server Components — the server produces markup per request; RSC additionally lets some components render only on the server and never ship their code to the browser), **SSG** (static site generation — every page's HTML is produced once at build time, before any request arrives), and **islands** (a static HTML page by default, with a small number of named components individually made interactive in the browser — a process called hydration).

## When to Use

- Building or changing a web page, layout, component, route, or client-side data flow.
- Choosing or auditing a rendering architecture (SPA, SSR/RSC, SSG, islands) for a new or existing app.
- Deciding where a piece of state should live, or whether a component is reusable or feature-bound.
- Deciding a folder convention for a frontend codebase, or auditing an existing one for drift.

Do not use for backend contracts, database access, auth policy, or server-only business logic — load `backend`. Do not use for per-file TypeScript/JavaScript discipline (types, escape hatches, LOC ceiling) — load `programming` for that layer once the frontend-specific decision is made. Do not use for XSS/CSP/token-storage hardening — load `security`. Do not use for e2e or component-test suite design — load `testing`.

## PHASE 0 — rendering-architecture gate (run first, every time)

Do not write or edit UI code before this gate.

1. Detect the existing rendering architecture. Run in the project root:

   ```bash
   test -f next.config.js -o -f next.config.mjs -o -f next.config.ts && echo "SSR/RSC (Next.js)"
   test -d app && grep -rlE "[\"']use client[\"']" app 2>/dev/null | head -1 >/dev/null && echo "RSC boundary present"
   test -f astro.config.mjs -o -f astro.config.ts && echo "SSG/islands (Astro)"
   test -f gatsby-config.js && echo "SSG (Gatsby)"
   test -f vite.config.ts -o -f vite.config.js && ! test -f next.config.js -o -f next.config.mjs -o -f next.config.ts && echo "SPA (Vite) — confirm no server entry:"
   find . -maxdepth 2 -iname 'server.*' -not -path '*/node_modules/*'
   ```

   Reading: a hit on `next.config.*` or an `app/` dir with `"use client"` markers → SSR/RSC. A hit on `astro.config.*` → SSG or islands (Astro ships both; confirm by counting hydration directives — see `references/architectures.md`). A hit on `gatsby-config.js` → SSG. A `vite.config.*` with no server entrypoint file and a client-only router (`react-router`, `@tanstack/router`) → SPA. No hit on any of these → new project; use the decision table in `references/architectures.md`.

2. STOP and read `references/architectures.md` in full before writing code — always, on every task this skill handles, since PHASE 0's detection and incumbent-respect rules live there. Then read whichever of the remaining references match scope:

   | Scope | Read |
   |---|---|
   | Component reuse, prop-API shape, or "should this be extracted" decision | `references/components.md` |
   | "Where does this state live" decision | `references/state.md` |
   | New project layout or folder-convention audit | `references/folders.md` |

3. Existing project → the detected architecture and its absolute rules win. The rule is precise: never introduce a **second rendering runtime/framework** — a distinct framework or hand-rolled pipeline not native to the incumbent one (e.g. bolting a Vite/react-router SPA onto a Next.js `app/` router project) — and never let a rendering-mode drift (SSR ↔ SSG ↔ client) inside the incumbent framework go unrecorded in `design.md`. Mixing SSR, SSG, and client output *within* the one detected framework (Next.js and Astro both do this natively) is that framework's own architecture, not a second one — see the incumbent-respect rule in `references/architectures.md`. New project → run the decision table in `references/architectures.md` before scaffolding.

## The design.md GATE (no UI code before this exists)

Do not write UI component code — not a button, not a page shell — before the project has a `design.md`.

1. Check for it:

   ```bash
   test -f docs/design.md && echo "design.md present" || echo "MISSING — scaffold before writing UI code"
   ```

2. Missing on a greenfield project → STOP, load the `document` skill's `references/design.md` sub-recipe and scaffold `docs/design.md` from its `templates/design.md` before the first component is written. This skill does not own `design.md`'s 7-section structure, its lifecycle rules, or its staleness/anti-generic detection commands — `document/design` owns all of that; read it there rather than re-deriving it here.
3. Missing on an existing project with no design system yet → same hand-off: scaffold via `document/design` before adding new UI surface, rather than inventing an ad hoc one-off style per component.
4. Every commit that adds or changes a token, primitive, or pattern updates `design.md` in that same commit — see `document/design` for the update law and its detection command; do not duplicate the check here.

## Requirements

- A project-local package manager and dev server (`npm`/`pnpm`/`bun` + the framework's dev command) to run detection commands and any build-output checks named in `references/architectures.md`.
- `git` for the same-commit design.md check delegated to `document/design`.
- `grep`, `find`, `comm` (POSIX) for the detection commands in this file and in `references/`.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's one small component, I'll skip the design.md gate." | One undocumented component is how a design system never starts. The gate is binary: `docs/design.md` exists or it does not — there is no small-enough exception. |
| "I'll pick SPA/SSR/SSG later once the app grows." | The rendering model determines data-fetching, auth, and bundling patterns from the first route. Retrofitting is a rewrite, not a refactor — decide at PHASE 0. |
| "This app is small, folder convention doesn't matter yet." | Convention drift compounds silently until an import-direction violation is load-bearing. Apply the folder default from `references/folders.md` at route count 1, not at route count 20. |
| "I copied this pattern from another project that used a different rendering model." | A pattern's safety (e.g. reading `window` at module scope) is rendering-model-specific. Re-verify against `references/architectures.md` for *this* project's detected model before reusing it. |
| "The state works, I don't need to name which kind it is." | Untyped state placement is exactly how server data ends up duplicated in a global store. Classify every piece of state against the taxonomy in `references/state.md` before deciding where it lives. |

## Red Flags

- A UI component landing in a commit with no `docs/design.md` in the repository at all.
- A second rendering runtime/framework bolted onto an app with an incumbent one (a Next.js `app/` router page manually re-implementing client-side-only routing via react-router, or an SPA entry point importing a server-only data accessor) — or a rendering-mode drift (SSR ↔ SSG ↔ client) inside the incumbent framework that `design.md` does not record.
- A component in a primitives/design-system layer importing from a feature directory (upward or sideways dependency — see `references/components.md`).
- Server-fetched data copied into a global UI store via `useEffect` + `setState` (see the iron rule in `references/state.md`).
- A folder tree that mixes type-based and feature-based conventions in the same app with no stated migration in progress.

## Verification

- [ ] PHASE 0 rendering-architecture detection ran and its output is stated in the work notes or final report.
- [ ] `docs/design.md` exists (or its scaffolding via `document/design` was completed first) before any UI component code was written.
- [ ] The matching reference file(s) were read before code was written: `architectures.md` always; `components.md` / `state.md` / `folders.md` as the task touched them.
- [ ] No second rendering runtime/framework was introduced into an app with an existing incumbent architecture, and any rendering-mode drift (SSR ↔ SSG ↔ client) within that framework is recorded in `design.md`.
- [ ] Every piece of new or moved state was classified against the taxonomy in `references/state.md`.
- [ ] Component-dependency direction stayed downward only (primitives → composed → feature-bound).
