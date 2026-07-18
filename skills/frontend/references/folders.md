# Frontend Folder Conventions

A folder convention is a contract about import direction: which directories may import from which others. Pick one convention per app and enforce its import direction — a folder tree with no enforced direction accumulates cycles silently.

## Contents

- [Hard rules](#hard-rules)
- [Decision table (MECE)](#decision-table-mece)
- [Type-based](#type-based)
- [Feature-based](#feature-based)
- [Next.js App Router (route colocation + domain features)](#nextjs-app-router-route-colocation--domain-features)
- [Layered feature-sliced](#layered-feature-sliced)
- [Monorepo / repo-topology rule](#monorepo--repo-topology-rule)
- [Incumbent-respect clause](#incumbent-respect-clause)
- [Hand-offs](#hand-offs)

## Hard rules

| Concern | Do | Never |
|---|---|---|
| Convention choice | Pick one of type-based / feature-based / layered feature-sliced per app | Mix two conventions in one app with no stated migration |
| Import direction | Follow the chosen convention's direction rule on every new file | Add an import that violates the direction "just this once" |
| New app scaffold | Apply the default recommendation below | Copy whatever convention the last project used regardless of route count |

## Decision table (MECE)

| Convention | Choose when | Absolute rules | Folder shape |
|---|---|---|---|
| Type-based | Small app, few routes (roughly < 10), team of 1-3 | Every file's folder is named after its technical kind, not its feature | `components/`, `hooks/`, `pages/`, `services/`, `utils/` |
| Feature-based | Medium-to-large app (roughly ≥ 10 routes), multiple teams or clear feature boundaries | Each feature folder is self-contained (its own components/hooks/api calls); cross-feature imports go through a stated shared layer only | `features/<name>/{components,hooks,api}`, `shared/` |
| Next.js App Router colocation | A Next.js `app/` router project, any route count | Page-only UI stays colocated per route; domain state/logic/API/types move to `features/<domain>/` on first use, not second; a shared UI component promotes to top-level `components/` only on its second real reuse | `app/<route>/_components/`, `features/<domain>/{api,state,components}`, `components/`, `lib/api-client.ts` |
| Layered feature-sliced | Large app needing strict enforcement of both feature boundaries and architectural layers | Six layers (`app`, `pages`, `widgets`/`features`, `entities`, `shared`) import strictly downward; a layer never imports from a layer above it or from a sibling at the same layer without going through `shared` | `app/`, `pages/`, `features/`, `entities/`, `shared/` |

**Default recommendation:** feature-based for an app with more than roughly 10 routes; type-based below that threshold. Apply the default at route count 1 in a new project — do not wait for the app to outgrow type-based before migrating, since the migration cost grows with every file added under the wrong convention. A Next.js `app/` router project takes the Next.js App Router row above instead of the generic feature-based/type-based split — the framework's own route-folder convention already gives page colocation for free, and layered feature-sliced's full layer taxonomy is deliberately not required to get its unidirectional-dependency benefit (see that row's rules).

## Type-based

**Absolute rules:**
- Folder name is the technical kind of the file (`components/`, `hooks/`, `services/`), never a feature name.
- Acceptable only while the app is small enough that "everything imports from everything" has not yet become a navigation cost. Re-evaluate against the route-count threshold as the app grows.

**Detect: route count, to sanity-check the convention still fits.**

```bash
find src/pages src/app -maxdepth 2 -type f \( -name 'page.tsx' -o -name '*.route.tsx' \) 2>/dev/null | wc -l
```

Reading: a type-based app with a route count printed above ~10 has outgrown the convention; plan the migration to feature-based rather than continuing to add routes to a flat `pages/`.

## Feature-based

**Absolute rules:**
- A feature folder owns its own components, hooks, and API calls — another feature never reaches into `features/other-feature/components/` directly.
- Genuinely shared code lives in `shared/` (or `common/` by project convention), and `shared/` has a stated admission rule (see the rule-of-three note below) — it does not become a second dumping ground for anything not yet placed.

**Detect: a cross-feature import bypassing `shared/`.**

```bash
grep -rlE "from ['\"](\.\./)+features/[a-zA-Z0-9_-]+/" src/features 2>/dev/null \
  | while read -r f; do
      owner=$(echo "$f" | sed -E 's#.*features/([^/]+)/.*#\1#')
      grep -oE "features/[a-zA-Z0-9_-]+/" "$f" | grep -v "features/$owner/"
    done
```

Any output → a file inside one feature imports from a different feature's internal path → move the shared piece to `shared/` (after a rule-of-three check) or expose it through that feature's own public entry point instead of a deep import.

**SMELL:**

```ts
// features/checkout/summary.ts
import { formatPrice } from "../../features/catalog/pricing";
```

**CLEAN:**

```ts
// features/checkout/summary.ts
import { formatPrice } from "@/shared/format";
```

**Rule of three for `shared/` admission:** the first time a piece of logic looks reusable across features, leave it in its originating feature. The second time another feature needs the same logic, note the duplication. The third time, promote it to `shared/` with a named owner. Promoting on the first occurrence produces a `shared/` shaped around one feature's assumptions.

## Next.js App Router (route colocation + domain features)

Core principle: state and logic are reused; UI is repeated. A Next.js `app/` router
project gets route-local colocation for free from the framework's own file conventions
(`_components/` is a private folder Next.js never treats as a route), so this convention
replaces the generic type-based/feature-based split above for that framework rather than
layering underneath it.

**Absolute rules:**
- Page-only UI/markup stays colocated in `app/<route>/_components/`. Do not unify
  similar-looking page UI across routes early — domain UI that looks alike today typically
  diverges as routes evolve independently, and early unification produces branch-heavy
  components serving multiple unrelated callers.
- Domain state, logic, API calls, and types spanning more than one page (a business
  concept — session, user) live in `features/<domain>/` from their first usage, not their
  second. Scattered domain logic is the main cost driver when a domain rule changes and
  every copy has to be found by hand.
- A page-local UI component promotes to the top-level `components/` only once a second
  page actually reuses it — this 2-reuse threshold is specific to promoting an
  already-colocated component out of `app/`; it does not change `components.md`'s rule of
  three for extracting a newly-noticed duplicate JSX shape.
- Dependencies run one way: `app/` → `features/` → `lib/`. A `features/` module never
  imports from `app/`; a `lib/` module never imports from `features/`; no feature reaches
  into another feature's internal path directly.
- All HTTP calls go through the single client in `lib/api-client.ts` (see `SKILL.md`'s API
  boundary).
- Do not adopt FSD's full layers/slices/segments taxonomy for this pattern — carry over
  only its unidirectional-dependency principle. Assigning every file a
  feature/entity/widget classification adds a per-ticket triage cost that outweighs its
  benefit for a small or lower-experience team; `features/<domain>/` is the one
  non-`app`, non-`lib` layer this convention needs.

**Detect: a feature module reaching into another feature's internals.**

```bash
grep -rlE "from ['\"](\.\./)+features/[a-zA-Z0-9_-]+/" src/features 2>/dev/null \
  | while read -r f; do
      owner=$(echo "$f" | sed -E 's#.*features/([^/]+)/.*#\1#')
      grep -oE "features/[a-zA-Z0-9_-]+/" "$f" | grep -v "features/$owner/"
    done
```

**Detect: a page-local component name repeated across two different routes' `_components/`.**

```bash
find src/app -type d -name '_components' | xargs -I{} find {} -name '*.tsx' 2>/dev/null \
  | xargs -n1 basename | sort | uniq -d
```

Any name printed → the same component file name already exists under two routes'
`_components/` → it has reached its second caller; promote it to `components/` instead of
leaving a second page-local copy.

Folder shape:

```
src/
├── app/
│   ├── page.tsx + _components/     # static page, no domain state — never leaves app/
│   └── signup/
│       ├── page.tsx
│       └── _components/            # page-only UI
├── features/auth/
│   ├── api.ts                      # domain API (e.g. signup() lands here)
│   ├── session-state.ts            # domain state
│   └── components/login-button.tsx # only a widget that actually repeats across pages
├── components/                     # promoted on the second real reuse; empty at project start is normal
└── lib/api-client.ts
```

## Layered feature-sliced

**Absolute rules:**
- Layers, from outermost to innermost: `app` (app-wide setup, providers, routing) → `pages` (route compositions) → `widgets`/`features` (self-contained UI blocks with logic) → `entities` (business domain models and their UI) → `shared` (framework-agnostic, business-agnostic utilities and UI primitives).
- Import direction is strictly downward: a layer imports only from itself or a layer below it. A `shared` module never imports from `entities`, `features`, `pages`, or `app`.
- Same-layer imports (a `feature` importing another `feature`) are treated the same as an upward import — banned; route the dependency down through `entities` or `shared` instead.

**Detect: an upward or same-layer import violating the layer order.**

```bash
rank() {
  case "$1" in
    shared) echo 1 ;;
    entities) echo 2 ;;
    features|widgets) echo 3 ;;
    pages) echo 4 ;;
    app) echo 5 ;;
  esac
}
for f in $(find src -type f \( -name '*.ts' -o -name '*.tsx' \)); do
  from_layer=$(echo "$f" | grep -oE '/(shared|entities|features|widgets|pages|app)/' | head -1 | tr -d '/')
  [ -z "$from_layer" ] && continue
  from_rank=$(rank "$from_layer")
  grep -oE "from ['\"](\.\./)+(shared|entities|features|widgets|pages|app)/" "$f" 2>/dev/null \
    | grep -oE '(shared|entities|features|widgets|pages|app)' \
    | while read -r to_layer; do
        to_rank=$(rank "$to_layer")
        [ "$to_rank" -ge "$from_rank" ] && echo "$f: $from_layer -> $to_layer"
      done
done
```

Any line printed → a file in `from_layer` imports a module ranked at or above its own layer → the import direction is violated; move the dependency down or restructure which layer owns the logic.

## Monorepo / repo-topology rule

A manifests repository (Kubernetes/kustomize configuration only) carries zero application source. An application repository never embeds cluster manifests beyond its own `deploy/` directory.

**Detect: application source living inside what should be a manifests-only repository.**

```bash
find . -name '*.py' -o -name '*.ts' -o -name '*.tsx' | grep -v -E '(^\./scripts/|node_modules)'
```

Any match inside a repository whose purpose is kustomize/manifests-only → flag; application logic belongs in its own source repository, not the deploy repository.

**Detect: an application repository embedding cluster manifests outside its own `deploy/` directory.**

```bash
find . -iname '*.yaml' -o -iname '*.yml' | xargs grep -l '^kind: ' 2>/dev/null | grep -v -E '^\./deploy/'
```

Any match outside `./deploy/` in an application repository → cluster manifests are leaking into application source control at the wrong path; move them under the repo's own `deploy/` directory or into the separate manifests repository.

## Incumbent-respect clause

Detect the project's existing convention (type-based, feature-based, Next.js App Router colocation, or layered feature-sliced) by inspecting the top-level `src/` structure before adding a file. Follow that convention for every edit. Apply the default recommendation only to a new project or a new, independently-routed app in a monorepo; never migrate an existing app's folder convention as a side effect of an unrelated feature change — propose the migration as its own change.

## Hand-offs

- Which layer inside `features/`/`widgets/` a given component belongs to (primitive vs. composed vs. feature-bound) → `components.md` in this skill.
- Server-cache vs. global-store placement inside `shared/`/`entities/` → `state.md` in this skill.
- Per-file import/module discipline (barrel files, circular-import detection at the file level) → `programming`.
- Extraction timing for a newly-noticed duplicate JSX shape (rule of three) vs. promoting an already-colocated `app/<route>/_components/` file (2-reuse threshold) → `components.md`'s "Extraction timing" row in this skill governs the former; the Next.js App Router section above governs the latter.
