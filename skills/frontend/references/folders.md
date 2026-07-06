# Frontend Folder Conventions

A folder convention is a contract about import direction: which directories may import from which others. Pick one convention per app and enforce its import direction — a folder tree with no enforced direction accumulates cycles silently.

## Contents

- [Hard rules](#hard-rules)
- [Decision table (MECE)](#decision-table-mece)
- [Type-based](#type-based)
- [Feature-based](#feature-based)
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
| Layered feature-sliced | Large app needing strict enforcement of both feature boundaries and architectural layers | Six layers (`app`, `pages`, `widgets`/`features`, `entities`, `shared`) import strictly downward; a layer never imports from a layer above it or from a sibling at the same layer without going through `shared` | `app/`, `pages/`, `features/`, `entities/`, `shared/` |

**Default recommendation:** feature-based for an app with more than roughly 10 routes; type-based below that threshold. Apply the default at route count 1 in a new project — do not wait for the app to outgrow type-based before migrating, since the migration cost grows with every file added under the wrong convention.

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

Detect the project's existing convention (type-based, feature-based, or layered feature-sliced) by inspecting the top-level `src/` structure before adding a file. Follow that convention for every edit. Apply the default recommendation only to a new project or a new, independently-routed app in a monorepo; never migrate an existing app's folder convention as a side effect of an unrelated feature change — propose the migration as its own change.

## Hand-offs

- Which layer inside `features/`/`widgets/` a given component belongs to (primitive vs. composed vs. feature-bound) → `components.md` in this skill.
- Server-cache vs. global-store placement inside `shared/`/`entities/` → `state.md` in this skill.
- Per-file import/module discipline (barrel files, circular-import detection at the file level) → `programming`.
