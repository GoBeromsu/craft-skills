# Obsidian Visualization

Build a note-grounded diagram by writing the target file directly: an Excalidraw drawing and a JSON Canvas graph are both just files with a documented shape, not runtime objects that need a plugin API to construct.
Generate the file with a small deterministic script, validate it, open it to confirm it renders, and only then hand it back.
Reach for the plugin's live-editing API ([`ea-workbench.md`](ea-workbench.md)) only for the narrow exception in [§6](#6-exception-live-edits-through-the-plugin).

## Table of contents

1. [Choose the format](#1-choose-the-format)
2. [Excalidraw file anatomy](#2-excalidraw-file-anatomy)
3. [Excalidraw element essentials](#3-excalidraw-element-essentials)
4. [JSON Canvas file anatomy](#4-json-canvas-file-anatomy)
5. [Procedure](#5-procedure)
6. [Exception: live edits through the plugin](#6-exception-live-edits-through-the-plugin)
7. [Content choices](#7-content-choices)
8. [Safety rules](#8-safety-rules)
9. [Result](#9-result)

## 1. Choose the format

| Nodes are... | Use |
| --- | --- |
| Existing vault notes/files to navigate — a map, an MOC, a dependency map of notes | **Canvas** (`.canvas`) |
| Free-form shapes with no backing note — architecture/data-flow diagrams, styled status cards, tables, labeled arrows | **Excalidraw** (`.excalidraw.md`) |

Mermaid stays [`mermaid.md`](mermaid.md)'s job for a diagram fenced inline inside a note.
Do not substitute one format for another against what the user asked for; Canvas versus Excalidraw is a real choice with the rule above, not a fallback.

## 2. Excalidraw file anatomy

An `.excalidraw.md` file is Markdown, top to bottom:

```
---
excalidraw-plugin: parsed
<any other frontmatter the vault wants>
---
<optional plaintext description>

# Excalidraw Data

## Text Elements
<text of element 1> ^<elementId1>

<text of element 2> ^<elementId2>

%%
## Drawing
```json
{"type":"excalidraw","version":2,"source":"https://github.com/zsviczian/obsidian-excalidraw-plugin","elements":[...],"appState":{"gridSize":null,"viewBackgroundColor":"#ffffff"},"files":{}}
```
%%
```

The `## Text Elements` section is a human-readable index (one blank line between entries); the plugin reads the actual scene from the fenced `json` block.
Always emit plain `json`, never hand-edit or hand-produce `compressed-json` — it is a compression codec output, not something to author by hand.

## 3. Excalidraw element essentials

Build elements with [`scripts/excalidraw_scene.py`](../scripts/excalidraw_scene.py) (stdlib only: `Scene.rect`, `.text`, `.box`, `.arrow`, `.write`, and a standalone `check()`) rather than re-deriving these fields by hand:

- **Rectangle / text / arrow / frame** each need `id`, `type`, `x`, `y`, `width`, `height`, plus the style fields (`strokeColor`, `backgroundColor`, `roundness`, ...) — see the script's `_base()` for the full set.
- **Bound text** (a label centered in its box): the text element carries `containerId: <rectId>`, and the container's `boundElements` includes `{"type":"text","id":<textId>}`. Missing either half renders wrong or breaks on reload.
- **Arrow bindings**: `startBinding`/`endBinding` are `{elementId, focus, gap}` on the arrow, mirrored as `{"type":"arrow","id":<arrowId>}` in both endpoints' `boundElements`. `points` are relative to the arrow's own `x, y` (first point is always `[0, 0]`).
- **Links**: set `link` to a pinned commit URL or a `[[Wikilink]]`; resolve a wikilink target against the vault before writing it (a plausible-looking note name is not a resolved one).
- **Groups**: `groupIds: [<groupId>]` on every element that should move/select together (e.g. a card's rect + extra badges beyond the one bound text `.box()` already handles).
- **Text sizing**: estimate width per character before wrapping — Hangul/CJK ≈ 1.0× `fontSize`, Latin ≈ 0.6× `fontSize`, `lineHeight` 1.25. `excalidraw_scene.py`'s `wrap()`/`dims()` already do this; reuse them instead of guessing widths inline.

## 4. JSON Canvas file anatomy

A `.canvas` file is `{"nodes": [...], "edges": [...]}` — defer node/edge schema, colors, and ID conventions to the native `json-canvas` skill; this package adds only the choice rule (§1) and the checks in §5 that are vault-specific (file nodes must resolve).

## 5. Procedure

Same loop for both formats:

1. **Gather evidence** for whatever the diagram claims (source files at a pinned commit, note contents, measured values) — see [§7](#7-content-choices).
2. **Write a small deterministic generator script.** Compute layout from measured text/content, don't eyeball coordinates. For Excalidraw, build on `excalidraw_scene.py`; for Canvas, a direct ~10-line dict-and-`json.dump` script is enough — it's too small to need a helper.
3. **Write a new file** (never overwrite an existing drawing — [§8](#8-safety-rules)).
4. **Automated checks**, before opening anything:
   - Excalidraw: `Scene.check()` — unique ids, every arrow binding and text `containerId` resolves and is mirrored, no two filled rectangles overlap.
   - Canvas: unique ids, every edge's `fromNode`/`toNode` resolves, no two nodes overlap, and every `file` node's path exists in the vault (the native `json-canvas` skill's own checklist doesn't know about the vault, so this package owns that one check).
5. **Rendered QA.** Open the file through the official Obsidian CLI (native `obsidian-cli` skill owns the exact command surface) and confirm the view type loads with the expected element/node count. For Excalidraw, also export a PNG through the plugin — `ea.createPNG(path, scale, {withBackground:true}, null, "light", padding)`, write the returned bytes with Node `fs` to a temp file — and *look at the image*: overlaps, clipping, illegible text, wrong hierarchy. Fix the generator and regenerate; don't hand-patch the output file.
   CLI gotcha: `obsidian eval` only returns synchronous values. For the async `createPNG` call, assign the result to a `window.__x` variable in one eval and poll for it with a second eval.

## 6. Exception: live edits through the plugin

Use the ExcalidrawAutomate workbench instead of steps 2–3 above only when the task genuinely needs it:

- Interactive edits inside a drawing the user has open right now (not a batch regeneration).
- Embedding images/files that must go through the plugin's file store.

See [`ea-workbench.md`](ea-workbench.md) for plugin/API admission, the workbench build helpers, persistence, the async completion guard, and reload+render QA for that path.
Do not reach for the workbench just because a diagram is "complex" — direct file authoring handles any element count; a 300+ element, multi-section diagram is normal-sized for this workflow.

## 7. Content choices

Honor the user's chosen source of truth: when a repo is authoritative, pin the reviewed commit and link source cards to files at that commit; label mounted/router declarations separately from inspected internals; keep vault notes as background unless the user makes them authoritative, and don't equate a hub concept with an edge-local module just because the names look related.
Use a reference image for visual language only — never to infer services, protocols, or measured values.

Pick the views the task and evidence actually support; don't default to a linear overview when the request is architectural:

| View | Needs |
| --- | --- |
| Runtime/pipeline | Real data shapes, branches, and verified stage ownership. |
| Sequence | Lifelines, calls/returns, `loop`/`opt`/`alt`, explicit async boundaries — no invented round-trip. |
| Data contracts | Actual field names, optionality, producers/consumers, source links. |
| Compose/deployment | Declared services/ports/volumes — label as declared, not observed running state. |
| Observability | Actual logs/metrics/events; label any illustrative timeline as such. |

## 8. Safety rules

- A new visualization request → a new file. Do not rewrite an existing drawing unless the user asked for that drawing specifically.
- If asked to edit an existing drawing: back it up first, diff element ids and bindings before/after, and use the exception path in [§6](#6-exception-live-edits-through-the-plugin) or a targeted `check()`-validated patch — never a full-scene replacement without that diff.
- Never hand-edit `compressed-json`, a host path, a vault name, an account identifier, or a secret into a shipped example.

## 9. Result

Report the vault-relative path, chosen format and why, source-of-truth evidence, `check()`/checklist result, and the rendered-QA outcome (element/node count confirmed, PNG inspected for Excalidraw).
A failed check, an unresolved link, or an uninspected render is a partial result — report it as a blocker, not a success.
