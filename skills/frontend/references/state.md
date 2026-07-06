# Frontend State Placement

Every piece of frontend state belongs to exactly one of five kinds. Classify a piece of state before deciding where it lives — placing it correctly the first time is cheaper than migrating it once a component tree has grown around the wrong choice.

## Contents

- [Hard rules](#hard-rules)
- [The taxonomy (MECE)](#the-taxonomy-mece)
- [Classification flow](#classification-flow)
- [The iron rule: server data is never copied into a global store](#the-iron-rule-server-data-is-never-copied-into-a-global-store)
- [URL state — the shareability test](#url-state--the-shareability-test)
- [Form state](#form-state)
- [Global-store scope check](#global-store-scope-check)
- [Incumbent-respect clause](#incumbent-respect-clause)
- [Hand-offs](#hand-offs)

## Hard rules

| Concern | Do | Never |
|---|---|---|
| Server-fetched data | Keep it in a server-cache layer (a query cache library, or the framework's server-rendered data) | Copy it into a global UI store via `useEffect` + `setState` |
| State a URL could describe | Put it in the URL (query params, route params) | Duplicate it in component or global state, letting the two drift out of sync |
| Cross-cutting UI-only state | Put it in a small, purpose-scoped global store | Reach for one monolithic global store for every piece of state regardless of kind |
| Ephemeral form input | Keep it local to the form until submit | Push every keystroke into a global store |

## The taxonomy (MECE)

| Kind | Lives in | Never do |
|---|---|---|
| Server-cache state | A dedicated server-cache layer (query-cache library, or server-rendered props in SSR/RSC) — data whose source of truth is the backend | Copy it into component state or a global UI store "for convenience"; the copy goes stale the moment the server value changes |
| Global UI state | A small, purpose-scoped store (theme, active modal, sidebar-collapsed) — state with no backend source of truth that many unrelated components read | Store server data here, or create one store per app for everything regardless of scope |
| Local state | The component that owns the interaction (`useState`/`useReducer` or framework equivalent) — state no sibling or ancestor needs | Lift it to global scope "in case something else needs it later" before a second consumer actually exists |
| URL state | Query params or route params — state a user should be able to bookmark, share, or navigate back to (filters, selected tab, pagination page, search query) | Keep it in memory-only state, breaking back-navigation and link-sharing |
| Form state | A form-scoped state container (local state or a form library) — in-progress input before submission | Sync every keystroke into global or server state before the user submits |

## Classification flow

Run this before writing a `useState`, store slice, or query hook:

```
Does the value come from the backend (a fetch/query/mutation)?
  yes → server-cache state (query-cache layer or server-rendered props)
  no  ↓
Should a copied URL reproduce this value on load?
  yes → URL state (query/route params)
  no  ↓
Is this in-progress input before a form submit?
  yes → form state (local to the form)
  no  ↓
Do 2+ unrelated components need to read or write this?
  yes → global UI state (purpose-scoped store)
  no  → local state (owned by the one component)
```

## The iron rule: server data is never copied into a global store

Server-fetched data has exactly one source of truth: the server. The moment it is copied into a general-purpose global store (a Redux/Zustand/Context slice named after an API resource), two copies exist and one of them silently goes stale — the store copy does not know when the server value changes, gets invalidated, or gets refetched by another part of the app.

**Detect: the `useEffect` + `setState`-from-fetch pattern.**

```bash
grep -rlE 'useEffect' --include='*.tsx' --include='*.ts' src \
  | xargs grep -lE 'set[A-Z][A-Za-z]*\(.*\b(await|then)\b' 2>/dev/null
```

Reading: a file matching both patterns is a candidate for the smell — a component manually fetching in `useEffect` and pushing the result into local or (worse) global state instead of using a server-cache layer. Not every match is a violation (a component-local fetch for a genuinely one-off, uncached read can be legitimate); confirm the fetched data is not also read by other unrelated components before flagging.

**Detect: a global store slice named after an API resource.**

```bash
grep -rlE "create(Store|Slice)|defineStore" --include='*.ts' --include='*.tsx' src/store src/stores 2>/dev/null \
  | xargs grep -liE '(users?|orders?|products?|posts?|customers?)(Slice|Store)' 2>/dev/null
```

Any match → a store slice named after a backend resource is very likely a server-data mirror; move that data to the project's server-cache layer and keep the store slice (if it survives) to only the UI-only state genuinely related to that resource (e.g. `isUsersPanelOpen`, never `users`).

**SMELL:**

```tsx
const [users, setUsers] = useState<User[]>([]);
useEffect(() => {
  fetchUsers().then(setUsers);
}, []);
// `users` is now a second, unsynchronized copy of server truth
```

**CLEAN:**

```tsx
const { data: users } = useQuery({ queryKey: ["users"], queryFn: fetchUsers });
// server-cache layer owns staleness, refetch, and cache invalidation
```

## URL state — the shareability test

Before placing a piece of UI state in memory, ask: "if a user copies the current URL and opens it in a new tab, should this state be present?" If yes, it is URL state — a selected filter, an open tab, a pagination page, a search query. If no (a hover state, a mid-drag position, an unsaved draft), it is local state.

**Detect: a filter/tab/page value held only in component state with no corresponding URL param.**

```bash
grep -rlE 'useState.*\b(filter|tab|page|sort)\b' --include='*.tsx' src \
  | xargs grep -L 'useSearchParams\|useRouter\|URLSearchParams' 2>/dev/null
```

Grey zone — judge by whether the value genuinely affects what the user sees on load. A file matching (state named like a filter/tab/page, but no URL-param hook nearby) is worth a manual check, not an automatic fix.

**SMELL:**

```tsx
const [tab, setTab] = useState("overview"); // lost on refresh, unshareable
```

**CLEAN:**

```tsx
const [params, setParams] = useSearchParams();
const tab = params.get("tab") ?? "overview"; // shareable, survives refresh
```

## Form state

Keep in-progress form input local to the form (via local state or a form library) until submission. Only the submitted, validated result crosses into server-cache state (as a mutation) or global state (rare — a multi-step wizard's cross-step draft can justify a scoped store, never the app's general-purpose store).

**Detect: a form input writing directly into a global store on every keystroke.**

```bash
grep -rlE 'onChange=\{.*\bset[A-Z][A-Za-z]*\(' --include='*.tsx' src \
  | xargs grep -l "from ['\"].*store['\"]" 2>/dev/null
```

Any match → an `onChange` handler calls a global-store setter directly → confirm the field is genuinely cross-component-visible while being typed (rare); otherwise move it to form-local state and commit to the store only on submit.

## Global-store scope check

A single global store accumulating unrelated keys (`theme`, `cart`, `currentUserDraft`, `notifications`, `selectedRowIds`) is a sign that server-cache and local state have been funneled into it by default rather than by classification.

**Detect: distinct top-level keys in the project's global store definition (approximate — inspect the printed list by hand).**

```bash
grep -oE '^\s*[a-zA-Z_][a-zA-Z0-9_]*:' src/store/index.ts src/store/*.ts 2>/dev/null | sort -u
```

Grey zone — no fixed count threshold. Judge each key against the taxonomy above: a key that is really server-cache or form-local data misplaced in the global store is the actual defect, not the key count itself.

## Incumbent-respect clause

Detect the project's existing state-management library (Redux, Zustand, Jotai, React Query/TanStack Query, Context) and use it for new state of the matching kind. Apply this taxonomy to classify *which* kind new state is; do not introduce a second global-store library into a project that already has one, and do not migrate existing state to a new kind as a side effect of an unrelated feature change.

## Hand-offs

- Whether a piece of state belongs to a server component or a client leaf → `architectures.md` in this skill.
- Which layer (primitive/composed/feature) owns a piece of local state → `components.md` in this skill.
- Per-file type discipline for store slices and reducers → `programming`.
