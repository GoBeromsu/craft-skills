# Rendered verification handoff

Rendered verification belongs to browser/testing mechanics. Design supplies expected states and observations; capture producers emit the checker v1 manifest without claiming usability or WCAG conformance.

## Capture matrix

For each affected task, record state (default, hover, active, focus-visible, disabled, loading, plus empty/error for data-bearing primitives), viewport class and exact dimensions, input (keyboard/pointer), zoom/reflow condition, reduced-motion setting, route/data state, and artifact identity. Compare only captures with the same viewport dimensions, device scale, browser/engine, zoom, locale, fonts, input, state, and deterministic data. Record any difference threshold and its unit; a diff number is an observation limit, never a quality score or proof of fitness.

Capture focus after keyboard navigation and identify the control with normalized accessibility-node `id`; `control_ref` is that id, never a locator. Capture records join an expectation on exact control_ref and viewport_id, with `state: focus-visible`, `input: keyboard`, and a verified artifact. Locators `{kind,value}` are stable anchors only.

For zoom/reflow, record zoom percentage, viewport CSS pixels, horizontal-scroll observation, and affected state. For motion, capture normal and reduced-motion conditions, recording OS/browser setting and wait policy. Do not infer animation behavior from a still image. Artifact records use a root-contained relative path, kind, SHA-256, producer/version/run metadata, and source state metadata. Re-capture when route, data, viewport, input mode, browser version, fonts, or motion setting changes.

A complete coverage declaration means only the named checker fact for the explicitly supplied ownership root is enumerated. Missing nodes, missing artifact verification, unsupported roles, dynamic behavior, visual contrast, target size, pixels, intent, and task success remain insufficient or require a manual audit. Browser launch, screenshots, diff mechanics, and accessibility-tree extraction are intentionally external to this package.
