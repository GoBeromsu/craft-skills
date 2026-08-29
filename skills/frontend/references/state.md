# Frontend State Placement

State has one authoritative owner. Classify a value before choosing a Hook, URL parameter, provider, store, query cache, or server boundary; duplicated representations drift.

## Contents

- [Five state kinds](#five-state-kinds)
- [Classification flow](#classification-flow)
- [State ownership in slices](#state-ownership-in-slices)
- [Server-cache state](#server-cache-state)
- [URL state](#url-state)
- [Form and local state](#form-and-local-state)
- [Global UI state](#global-ui-state)
- [React and Vite placement](#react-and-vite-placement)
- [Next.js placement](#nextjs-placement)
- [Derived state and hydration](#derived-state-and-hydration)
- [Verification](#verification)
- [Incumbent-respect clause](#incumbent-respect-clause)
- [Hand-offs](#hand-offs)

## Five state kinds

| Kind | Authoritative owner | Examples |
|---|---|---|
| Server-cache | Backend plus incumbent server/query cache | Products, user profile, orders |
| URL | Route/query parameters | Filter, tab, search, pagination |
| Form | Form instance until submit | Draft fields, validation errors |
| Global UI | Small purpose-scoped client owner | Theme, active modal, sidebar state |
| Local | Closest component owning the interaction | Hover, disclosure, transient selection |

Do not classify a value by the library already used to hold it. A Redux/Zustand/Context key can still be misplaced server, URL, form, or local state.

## Classification flow

```text
Does the value come from backend authority?
  yes → server-cache state
  no  ↓
Should a copied URL reproduce it?
  yes → URL state
  no  ↓
Is it unsubmitted form input or form validation?
  yes → form state
  no  ↓
Do unrelated branches genuinely coordinate it?
  yes → purpose-scoped global UI state
  no  → local state at the closest owner
```

Then ask whether the value is computable from existing props/state. If yes, derive it during render instead of storing another state variable.

## State ownership in slices

- Route adapters own URL parsing/serialization and pass typed values downward or expose a narrow route/feature API.
- A feature owns local/form state for its user capability.
- An Entity can expose stable client-side domain behavior or server-cache access, but it does not mirror the backend database into a global store.
- Cache infrastructure lives in the incumbent lower-level integration; feature/entity APIs expose domain-specific query/mutation operations.
- Shared primitives own only interaction state needed to implement their semantic contract.

State exports obey the dependency rules in [`folders.md`](folders.md). A public entry narrows a legal dependency; it does not authorize a peer/upward import.

## Server-cache state

Server data has backend authority. Do not copy it into component or global UI state through an effect merely to make it easier to read.

Prefer the incumbent framework/server/query-cache representation. After a mutation, update or invalidate through that same owner. A one-off client fetch can be valid, but it still needs one staleness/error/retry owner rather than an additional store copy.

Smell:

```tsx
const [users, setUsers] = useState<User[]>([]);
useEffect(() => { fetchUsers().then(setUsers); }, []);
```

Prefer a framework server read or incumbent query API whose cache owns freshness. Do not add a query library when the framework/incumbent stack already meets the requirement.

## URL state

Use the shareability test: should refresh, a copied link, and back/forward navigation reproduce this value? If yes, encode it once in route/query parameters.

- Parse and validate external URL input.
- Choose canonical defaults and omit redundant parameters when appropriate.
- Avoid keeping a synchronized memory copy.
- Preserve navigation semantics: replace for transient refinements only when history should not grow; push when the user expects a navigable state.

## Form and local state

Keep unsubmitted input inside the form. Submit the validated result through the owning mutation boundary. A multi-step draft can justify a form-scoped provider/store; it does not justify an application-wide general store.

Keep transient interaction state at the closest component. Lift it only to the closest common owner when siblings coordinate. A custom Hook reuses behavior, not one shared state instance.

## Global UI state

Use a small purpose-scoped owner only when unrelated branches coordinate client-only state with no URL/backend authority. Name the scope (`theme`, `commandPalette`, `notifications`) instead of accumulating one application store.

Providers should be as deep as practical. A high provider can enlarge render and, in Next.js, client-module boundaries. Do not introduce a second store library for one new scope.

## React and Vite placement

For a confirmed browser SPA:

- Use the incumbent router for URL state.
- Use the incumbent query/cache mechanism for server data.
- Keep form and local state inside the owning feature/component.
- Persist to browser storage only when the product requires persistence; version/validate the stored shape and handle unavailable storage.
- Measure render behavior before adding selectors or memoization.

Vite does not decide state ownership. Build tooling and state architecture are separate contracts.

## Next.js placement

For an incumbent App Router project, verify behavior against the installed Next version:

- Prefer server reads in Server Components when data does not require browser-interactive fetching.
- Keep authorization and secrets in server-only modules and send minimal serializable data to client leaves.
- Use client caches only for genuinely client-interactive/live data or an established incumbent cache contract.
- Keep non-serializable/browser state below `'use client'`.
- Do not copy a server-rendered snapshot into a global client store by effect.
- Do not read `window`, storage, media queries, or browser-only values during server render. Initialize deterministically, then synchronize through the smallest client boundary when necessary.
- Do not encode cache/revalidation APIs from branch-head docs without matching-version evidence from `SKILL.md` Requirements.

## Derived state and hydration

Remove these duplication patterns:

- State that can be calculated from props or existing state.
- Effects that mirror props into state or run event-specific behavior.
- URL values duplicated in component/global state.
- Server snapshots copied into client stores.
- Several booleans representing one finite status; use one explicit status union.
- Browser persistence read during server render, producing server/client markup differences.

Handle user events in event handlers. Use effects only to synchronize with an external system. Reset conceptual identity with an appropriate key or owner boundary rather than cascaded reset effects.

## Verification

Exercise the behavior belonging to the state kind:

| Kind | Checks |
|---|---|
| Server-cache | Loading/error/empty, mutation invalidation, stale/refetch behavior, authorization boundary |
| URL | Refresh, copied link, back/forward, invalid/missing parameters |
| Form | Validation, submit, reset, error recovery, multi-step persistence if required |
| Global UI | Isolation between scopes, provider placement, persistence if required |
| Local | Remount/reset identity, sibling coordination, no unrelated rerenders where measured |
| Next boundary | Serialization, hydration warnings, server-only/client import safety |

Use real production behavior for performance claims. A documentation-only evaluation verifies the prescribed collection method and marks runtime numbers N/A.

## Incumbent-respect clause

Use the incumbent router, form, query/cache, and store mechanisms for the matching state kind. Apply this taxonomy to new work; do not migrate existing state or add a second library as a side effect. Record misclassified legacy state for a separately scoped correction.

## Hand-offs

- Server/client rendering boundary → [`architectures.md`](architectures.md).
- Slice and public API ownership → [`folders.md`](folders.md).
- Controlled/uncontrolled component APIs → [`components.md`](components.md).
- Persisted theme/token styling → [`css.md`](css.md).
- Store/reducer type discipline → `programming`.
