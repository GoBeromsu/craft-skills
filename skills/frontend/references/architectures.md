# Frontend Rendering Architectures

A rendering model is a contract about *when* and *where* markup is produced: at build time, at request time on a server, or at runtime in the browser. Each model below is a closed set of absolute rules. Bolting a **second rendering runtime/framework** — a distinct framework or hand-rolled pipeline not native to the incumbent one — onto an app breaks the contract silently, usually as a hydration mismatch or a leaked secret. This does not forbid mixed rendering *modes* that are the detected framework's own native architecture: Next.js's `app/` router natively renders some routes as SSR, some as SSG via `generateStaticParams`, and some leaf components as pure client; Astro natively mixes SSG pages with islands and on-demand SSR. That mixing is the framework's contract, not a violation of it — as long as each mode choice is recorded in `design.md` rather than drifting unrecorded.

## Hard rules

| Concern | Do | Never |
|---|---|---|
| Rendering model per app | Pick exactly one framework/runtime (SPA / SSR-RSC / SSG / islands, or the multi-mode architecture native to the detected framework) and apply its rules everywhere | Introduce a second rendering runtime/framework into the app (e.g. an SSR/Next.js app with a hand-rolled client router bypassing the framework's routing) |
| Existing project | Detect the incumbent framework (PHASE 0 in `SKILL.md`) and follow its rules — including whatever rendering-mode mixing is native to it — for every edit | Let a rendering-mode drift (SSR ↔ SSG ↔ client) inside the incumbent framework go unrecorded in `design.md`, or bolt on a second framework "just for this one page" without a stated migration plan |
| New project | Choose from the decision table below before scaffolding | Default to the model you personally know best regardless of the project's needs |

## Decision table — new project

| Need | Choose | Why |
|---|---|---|
| SEO-critical content, fast Time-To-First-Byte, marketing/blog/docs pages | SSG | Pages are static HTML at request time; nothing to compute per request |
| Content that changes per request but still needs SEO/fast TTFB (product pages, dashboards with public URLs) | SSR/RSC | Server renders per request; client hydrates only the interactive parts |
| Auth-gated app behind a login wall, no SEO requirement, rich client interactivity | SPA | No server-rendering cost to pay for pages search engines never see |
| Mostly static content with a few interactive widgets (a comment box, a carousel) | Islands | Ships HTML by default; hydrates only the named interactive islands |

When it's genuinely ambiguous (an app with both a public marketing site and a gated dashboard) → split into two apps/rendering models at the routing boundary, not one model straining to cover both.

## SSR / RSC (React Server Components, Next.js `app/` router and equivalents)

**Absolute rules:**
- The server/client boundary is explicit and one-directional: a module marked as a client component (`"use client"` or framework equivalent) can be imported by a server component, but a server-only module is never imported into client code.
- No browser-only API (`window`, `document`, `localStorage`) runs in server-rendered code. A server component that needs one delegates to a client leaf.
- No secret (API key, DB credential, unprefixed env var) reaches client bundles. Framework env-var prefixing (`NEXT_PUBLIC_`, `VITE_PUBLIC_`) is the only sanctioned crossing point.
- Data is fetched on the server by default; a client component fetches only when the data is genuinely request-time-interactive (search-as-you-type, live polling) and cannot be server-rendered.
- Client components are leaves: push the `"use client"` boundary as far down the tree as possible so the largest share of the tree stays server-rendered.

**Detect: `"use client"` density (should be low relative to total component count).**

```bash
total=$(find app src/app -type f \( -name '*.tsx' -o -name '*.jsx' \) 2>/dev/null | wc -l)
client=$(grep -rlE "^[\"']use client[\"']" app src/app 2>/dev/null | wc -l)
echo "client components: $client / $total"
```

Reading: no fixed pass/fail ratio — this is a grey zone judged by tree shape, not a percentage. A `"use client"` directive on a top-level layout or page (rather than on the specific interactive leaf inside it) is the actual smell; audit those files by hand.

**Detect: browser API used without a client boundary.**

```bash
grep -rlE '\bwindow\.|\bdocument\.|localStorage\.' app src/app 2>/dev/null \
  | xargs -I{} sh -c 'head -1 "{}" | grep -q "use client" || echo "{}"'
```

Any file printed uses a browser API with no `"use client"` directive at its head → server-side crash risk, fix now.

**Detect: server secret reachable from a client file.**

```bash
grep -rlE "^[\"']use client[\"']" app src/app 2>/dev/null \
  | xargs grep -nE 'process\.env\.[A-Z_]+' 2>/dev/null \
  | grep -v 'process\.env\.NEXT_PUBLIC_'
```

Any match → an unprefixed env var referenced inside a client-marked file → the value ships to the browser bundle. Move the read to a server component or an API route.

**SMELL:**

```tsx
"use client";
export function ApiKeyBanner() {
  return <div>{process.env.STRIPE_SECRET_KEY ? "configured" : "missing"}</div>;
}
```

**CLEAN:**

```tsx
// server component (no "use client") — checks the secret server-side,
// ships only the boolean result down to a client leaf if needed
export async function ApiKeyBanner() {
  const configured = Boolean(process.env.STRIPE_SECRET_KEY);
  return <ApiKeyBadge configured={configured} />;
}
```

## SPA (client-rendered, e.g. Vite + React Router with no server entry)

**Absolute rules:**
- Route-level code splitting is mandatory: every top-level route is a separate lazily-loaded chunk, never all routes bundled into one file.
- State that should be shareable via a link (a filter, a selected tab, a search query, a pagination page) lives in the URL, not in component or global state — see `state.md`'s URL-state row.
- No server-only assumption leaks in (reading a request header, assuming a Node runtime) — an SPA has no server; treat every module as browser-executable.

**Detect: single-chunk build output (code splitting failed or was never set up).**

```bash
npm run build >/dev/null 2>&1
find dist build -maxdepth 1 -name '*.js' 2>/dev/null | wc -l
```

Reading: 1 JS chunk for an app with more than one route → code splitting is missing; wire up lazy route imports (`React.lazy` + `import()`, or the router's built-in lazy-loading). More than 1 → passing, but confirm route count roughly tracks chunk count for a genuinely route-split build.

## SSG (build-time-only, e.g. Gatsby, Astro without islands, static export mode)

**Absolute rules:**
- All data is resolved at build time. No request-time data coupling (no per-request DB call, no reading a request header) — anything that varies per request belongs in SSR/RSC or a client-side fetch, not SSG.
- Personalization or per-user content is a client-side island bolted onto the static shell, never baked into the static build.

**Detect: request-time coupling inside a build-time data function.**

```bash
dirs=$(find . -maxdepth 3 -iname 'getStaticProps*' -o -iname '*.astro' 2>/dev/null | xargs -n1 dirname 2>/dev/null | sort -u)
[ -n "$dirs" ] && grep -rlE 'req\.(headers|cookies)|request\.(headers|cookies)' \
  --include='*.ts' --include='*.tsx' --include='*.js' $dirs
```

Any match inside a static-data function → the build assumes request context it does not have at build time → fix by moving that logic to a client-side fetch or an SSR route.

## Islands (Astro, and equivalent partial-hydration frameworks)

**Absolute rules:**
- HTML ships with zero JavaScript by default; a component hydrates only when it declares an explicit hydration directive (`client:load`, `client:visible`, or equivalent).
- Each island is independently interactive and does not assume a shared client-side router or global client state with another island — islands communicate through the DOM or a narrow, explicit shared store, never through implicit module-level state.
- Choose the narrowest hydration directive that satisfies the interaction (`client:visible` over `client:load` for below-the-fold widgets) to keep the shipped JS minimal.

**Detect: hydration directive count vs. interactive-looking component count (grey zone).**

```bash
grep -rl 'client:load\|client:visible\|client:idle' src/pages src/components 2>/dev/null | wc -l
```

Grey zone — judge by whether components with obvious interactivity (forms, dropdowns, carousels) appear in the hydrated set; a component with visible `onClick`/`onChange` handlers but no `client:*` directive silently does nothing in the browser.

## Incumbent-respect clause

Detect the project's existing rendering model with the PHASE 0 commands in `SKILL.md` before writing any code. Follow the incumbent model's rules for every edit inside that project. Apply the decision table above only to a genuinely new project or a new, separately-routed app inside a monorepo — never mid-feature convert an existing app from one rendering model to another; propose that migration as its own separately-scoped change.

## Hand-offs

- Per-file TypeScript/JavaScript discipline once the rendering-model decision is made → `programming`.
- Component-level reuse rules within any rendering model → `components.md` in this skill.
- State placement within any rendering model → `state.md` in this skill.
