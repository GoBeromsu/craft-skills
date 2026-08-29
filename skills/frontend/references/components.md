# Frontend Component Reuse

A reusable component is a stable semantic contract, not JSX moved into a shared folder. Keep business behavior in its owning slice, prefer native/incumbent primitives, and promote only after real consumers demonstrate one reason to change.

## Contents

- [Hierarchy and ownership](#hierarchy-and-ownership)
- [Reusable component API strategy](#reusable-component-api-strategy)
- [Composition choices](#composition-choices)
- [Controlled and uncontrolled state](#controlled-and-uncontrolled-state)
- [Accessibility and semantic contracts](#accessibility-and-semantic-contracts)
- [Public surface and promotion](#public-surface-and-promotion)
- [Framework boundaries](#framework-boundaries)
- [Colocation and verification](#colocation-and-verification)
- [Incumbent-respect clause](#incumbent-respect-clause)
- [Hand-offs](#hand-offs)

## Hierarchy and ownership

| Component kind | Owns | May depend on |
|---|---|---|
| Primitive / design system | Semantic control and finite token-driven variants | Existing design tokens and platform behavior |
| Composed / pattern | Reusable interaction shape without product authority | Primitives and focused shared libraries |
| Feature-bound | Product workflow, route/data integration, analytics | Lower reusable components and owning slice internals |

This component hierarchy does not replace architectural layers. A primitive belongs in an eligible shared/design-system owner; a product-specific composition remains in its route or feature even when it uses primitives.

A lower reusable component never imports routing, authorization, analytics, product fetching, or feature internals. If it must, the component is feature-bound or its contract is wrong.

## Reusable component API strategy

Choose in order:

1. Use the semantic HTML element or incumbent primitive when it already satisfies behavior and accessibility.
2. Add a wrapper only for a stable design/product contract, not merely to shorten JSX.
3. Model behavior with explicit named props and a finite `variant`/`size` vocabulary.
4. Use discriminated unions when modes are mutually exclusive so invalid combinations cannot compile.
5. Keep styling extension narrow: the incumbent `className` pattern and documented CSS custom properties are usually sufficient.
6. Add refs, polymorphism, or imperative handles only for demonstrated focus/measurement/integration consumers.

Prefer:

```tsx
type NoticeProps =
  | { variant: "info"; message: string }
  | { variant: "action"; message: string; actionLabel: string; onAction(): void };
```

Avoid independent booleans that encode contradictory modes:

```tsx
<Notice isInfo isAction isDismissible />
```

Do not make arbitrary `style`, render-hook, or internal DOM props the primary design API. Every escape hatch becomes a supported contract and weakens refactorability.

## Composition choices

| Need | Prefer |
|---|---|
| Static visual composition | `children` or named slots |
| Coordinated subparts sharing component-owned context | Compound components with a small documented context |
| Parent computes data that the caller must render | Render prop |
| Cross-tree product state | An explicit state owner, not child inspection/cloning |

Avoid inspecting or cloning children to infer product behavior; data flow becomes implicit and fragile. Define components at module scope so identity and local state survive parent renders. Declare `lazy()` components at module scope as well.

## Controlled and uncontrolled state

Choose one ownership model first:

- Controlled: caller owns `value`/`open`/`selected` and receives `onValueChange` or equivalent.
- Uncontrolled: component owns state and accepts `defaultValue`/`defaultOpen`.

Support both only when real consumers require both. Document precedence, callback timing, reset behavior, and transitions between modes; do not switch ownership after mount silently. Keep transient hover, focus-visible, draft, and disclosure state local unless another component genuinely coordinates it.

For coordinated components, place one source of truth at the closest common owner. A custom Hook reuses logic; separate callers still receive separate state instances unless they share an external owner.

## Accessibility and semantic contracts

A reusable API includes:

- Correct native role and element before ARIA recreation.
- Accessible name, description, error, and required/disabled semantics.
- Keyboard operation, focus order, focus restoration, and visible focus.
- Stable list identity from data; never random keys or reorderable array indices.
- Reduced-motion, forced-colors, zoom/reflow, and touch target behavior when applicable.
- Events that expose semantic values rather than leaking internal DOM structure.

A visually reusable custom control that loses native keyboard or form behavior is not reusable. Verify semantics in the rendered surface, not only TypeScript types or a story snapshot.

## Public surface and promotion

Treat the third similar consumer as a review trigger, not an automatic extraction.

Promotion requires:

- Multiple real consumers with the same semantics and expected reason to change.
- A legal lower-layer owner and a named maintainer.
- A narrow explicit export surface and no feature-specific knowledge.
- Contract coverage for variants, behavior, accessibility, and current consumers.
- Consumer imports rewritten to the supported entry and obsolete deep paths removed.

Keep two small copies when they represent different contexts. Similar appearance does not prove one domain meaning.

## Framework boundaries

### React and Vite

Assume browser execution after the application is confirmed as an SPA. Keep reusable components pure; derive render values rather than mirroring them in effects. Split heavy optional UI only after a production profile shows meaningful initial cost.

### Next.js App Router

Keep reusable presentation server-compatible by default. Add `'use client'` only to the smallest module requiring state, effects, event handlers, custom Hooks, or browser APIs. Props crossing the server/client boundary must be serializable; keep callbacks inside the client island. A component may need a server-rendered shell plus a small client controller rather than making the whole tree client-only.

Never export server-only fetching/authorization from an entry consumed by client components.

## Colocation and verification

Keep source, contract tests, and stories/examples together using incumbent naming. Stories are examples, not assertions.

Verify applicable branches:

- Semantic element, accessible name, keyboard/focus, disabled/error states.
- Every finite variant and discriminated mode.
- Controlled and uncontrolled ownership, callbacks, reset, and invalid transitions.
- Consumer-visible rendering and layout across relevant viewports/themes.
- Server render and client hydration/serialization where applicable.
- Public entry imports and absence of old deep paths.

Production profiling precedes `memo`, `useMemo`, and `useCallback`. Memoization is an optimization, not a correctness mechanism; remove effect chains and unstable ownership before adding caches.

## Incumbent-respect clause

Use the project's current primitive library, naming, test/story format, and styling API. A flat unowned component directory is missing layering, but reorganizing it is a separate change. Apply the smallest correct owner to new work and record broader drift.

## Hand-offs

- Architectural ranks, slice APIs, and promotion → [`folders.md`](folders.md).
- Server/client and rendering boundaries → [`architectures.md`](architectures.md).
- State classification → [`state.md`](state.md).
- CSS variants, tokens, and delivery → [`css.md`](css.md).
- Type-level API discipline → `programming`; component testing depth → `testing`; untrusted rendering → `security`.
- New token meaning, primitive, or material design decision → `document` and the `docs/design.md` gate in `SKILL.md`.
