# Frontend CSS Architecture and Optimization

Read this reference for stylesheet organization, styling-system choice, design tokens, theming, responsive behavior, fonts/assets, CSS delivery, or performance. Logic-only component work does not need it. Preserve the incumbent system unless migration is separately approved.

## Contents

- [Incumbent-first decision](#incumbent-first-decision)
- [Ownership layers](#ownership-layers)
- [Tokens and theming](#tokens-and-theming)
- [Scoping and cascade](#scoping-and-cascade)
- [Choosing a styling strategy](#choosing-a-styling-strategy)
- [React and Vite delivery](#react-and-vite-delivery)
- [Next.js delivery](#nextjs-delivery)
- [Optimization sequence](#optimization-sequence)
- [Verification](#verification)
- [Design-document hand-off](#design-document-hand-off)

## Incumbent-first decision

Inventory before advice:

- Global stylesheet entrypoints and reset/normalization.
- CSS Modules, utility framework, CSS-in-JS, extracted CSS-in-TS, Sass/Less, or other preprocessors.
- Design-token authority and generated outputs.
- Component library and supported styling escape hatches.
- PostCSS/framework plugins, asset/font handling, and build configuration.
- Exact installed versions and matching official capability evidence from [`../SKILL.md#requirements`](../SKILL.md#requirements).

Continue one coherent incumbent system. A mixture introduced by migration is not a stable architecture; document its migration boundary and do not add a third system.

For greenfield web work, start with native CSS and locally scoped CSS Modules when the framework supports them. Add utility CSS, preprocessing, or CSS-in-JS only for a demonstrated authoring/runtime requirement.

## Ownership layers

| Owner | CSS responsibility |
|---|---|
| Framework shell | Reset, font faces, root tokens, theme selection, document defaults, global-style import |
| Shared primitive | Token-driven component styles and finite variants |
| Composed/feature UI | Locally scoped interaction and layout styles |
| Route/page | Route-private composition and styles used only there |

Routes may own private scoped styles. They must not patch another slice's internals, redefine shared tokens, or add broad global selectors. Keep responsive/container rules with the component whose layout changes.

## Tokens and theming

Use one canonical token source. Do not maintain independently editable JSON, Tailwind theme values, CSS variables, and TypeScript constants.

At useful scale, separate:

1. Primitives: palette, spacing, typography scales.
2. Semantic roles: `--text-muted`, `--surface-danger`, `--focus-ring`.
3. Component contracts only when a component truly owns a stable token surface.

Use semantic CSS custom properties as the browser runtime representation where practical. They participate in the cascade and support theme scoping without rerendering React. Shared components consume semantic/component roles, not raw palette values.

Use `@property` only when typed syntax, an initial value, controlled inheritance, or animation is useful. Adopt a design-token interchange format only when design-tool or multi-platform exchange is a real requirement; one web app can keep a simpler canonical CSS source.

For Tailwind versions supporting theme variables, expose a token through the utility theme only when utilities are part of the public contract. Keep ordinary application runtime values as normal CSS custom properties.

## Scoping and cascade

- Prefer local class scope and shallow selectors.
- Use semantic variants rather than arbitrary styling props.
- Expose only documented custom properties or class hooks.
- Avoid IDs for styling and do not repair architecture with `!important` escalation.
- Place vendor CSS in a lower-priority cascade layer when the incumbent architecture uses layers.
- Declare the complete intended layer order before partial migration; unlayered and layered rules have different precedence.
- Use `:where()` when low specificity is deliberately required.
- Distinguish source `@import` compiled by tooling from emitted network `@import`, which can create render-blocking request chains.

CSS Modules scope class and animation names; they do not isolate inherited values, custom properties, element selectors, or the cascade. Keep selectors disciplined even when names are generated.

## Choosing a styling strategy

| Strategy | Choose when | Watch |
|---|---|---|
| Native CSS + CSS Modules | Default cross-framework custom styling; local scope and platform features are enough | Inheritance/cascade still cross module boundaries. |
| Utility CSS | Already incumbent, or the team explicitly wants constrained utility composition | Static source detection; do not build class names from fragments. |
| Extracted CSS-in-TS | Typed build-time tokens/variants justify compilation | Tool/plugin/version coupling and generated output. |
| Runtime CSS-in-JS | Dynamic rule/selector generation cannot be represented by classes or custom properties | Client/runtime cost, streaming/registry support, hydration correctness. |
| Sass/Less | Incumbent code depends on preprocessor capabilities | Prefer native platform features for new greenfield work when they suffice. |

Tailwind-style scanners require complete class tokens visible to the configured source detector. Map variants to complete static strings instead of interpolation such as `bg-${color}-600`; avoid broad safelists that hide ownership and inflate output.

## React and Vite delivery

- Import global CSS once from the application shell.
- Colocate module styles with components/routes.
- Keep CSS code splitting enabled unless a measured deployment constraint requires one stylesheet.
- Verify the installed Vite version's emitted CSS behavior for async chunks; do not assume current docs match an older lockfile.
- Lazy-load only heavy/deferred UI. Confirm both JavaScript and associated CSS leave the initial route.
- Prefer direct imports on hot paths; large barrels can force extra module discovery/transforms.
- Audit expensive community plugins before rewriting application code.
- Do not add critical-CSS tooling by default. First remove unused/global CSS, preserve route splitting, and measure production FCP/LCP and cache behavior.

Vite does not provide application SSR merely because it builds assets. Choose an SSR-capable framework or deliberate Vite SSR architecture when server rendering is a real requirement.

## Next.js delivery

- Import truly global CSS at the framework-supported root layout/entry.
- Use CSS Modules or the incumbent local strategy for component and route-private styles.
- Keep import order intentional because production CSS ordering follows the module graph and framework chunking behavior.
- Prefer Server Components for static transformations and presentation; keep runtime styling/interactivity below the smallest client boundary.
- Use runtime CSS-in-JS only with a library and streaming registry supported by the installed Next version.
- Rely on route/server-component splitting first; use dynamic client imports for heavy deferred interactions only after measurement.
- Leave experimental CSS chunking or inlining controls at defaults unless matching-version evidence and a measured route problem justify a pinned experiment.
- Use the incumbent framework image/font/script facilities only after verifying their installed-version contract.

## Optimization sequence

1. Capture a production baseline: initial/route CSS and JS bytes, requests, applicable Coverage states, LCP resource, INP/long tasks, CLS, accessibility, and visual states.
2. Remove unreachable, duplicated, and obsolete rules after exercising hover, focus, error, modal, responsive, authenticated, and post-navigation states.
3. Reduce global reach and specificity; restore local ownership before changing chunk configuration.
4. Verify route/dynamic CSS delivery and request waterfalls.
5. Optimize fonts, images, and third-party styles/scripts using incumbent framework capabilities.
6. Apply containment, `content-visibility`, animation, preload, critical CSS, or manual chunking only to a measured bottleneck.
7. Re-run the same collection method and interpret the delta against project thresholds.

Critical CSS is conditional: inlining can remove a request but duplicates bytes, delays remaining HTML, and loses independent caching when overused. Preloading everything creates priority contention. Smaller output is not a win when interaction, accessibility, visual stability, or cacheability regresses.

## Verification

Record source, baseline, candidate, delta, project threshold/budget, and interpretation.

| Surface | Checks |
|---|---|
| Cascade | Computed styles, order, specificity/layer behavior, no cross-slice leakage |
| Responsive | Relevant viewports, container behavior, zoom/reflow, touch targets |
| Preferences | Forced colors, reduced motion, dark/high-contrast themes where supported |
| Visual | Loading/error/empty/disabled/focus/hover/modal states after final edit |
| Delivery | Initial and route CSS bytes, requests, cache/chunk behavior, unused coverage after representative interactions |
| User metrics | LCP, INP, CLS and accessibility against project thresholds |

Do not use universal byte budgets. Derive budgets from product users, route frequency, device/network distribution, and the current baseline. For documentation-only evaluation, verify that this collection contract is prescribed and mark real runtime numbers N/A.

## Design-document hand-off

This reference owns CSS implementation placement, delivery, and measurement. `document` and the `docs/design.md` gate own token meaning, design-system decisions, and material visual intent. Link to that owner rather than duplicating its document template or lifecycle.

Sources for conceptual guidance: [MDN custom properties](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties), [MDN cascade layers](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics/Cascade_layers), [Vite CSS features](https://vite.dev/guide/features.html#css), [Next.js CSS](https://nextjs.org/docs/app/getting-started/css), [Tailwind source detection](https://tailwindcss.com/docs/detecting-classes-in-source-files), and [web.dev performance](https://web.dev/learn/performance/).
