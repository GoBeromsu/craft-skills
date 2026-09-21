# Obsidian Excalidraw Visualization

Build or extend a note-grounded visualization through an active local Excalidraw plugin and its ExcalidrawAutomate API.
Use this route for architecture and other linked visual explanations that need real Obsidian elements, persisted scene evidence, and rendered QA rather than Mermaid, JSON Canvas, a pasted screenshot, or direct edits to compressed `.excalidraw.md` data.

## Table of Contents

1. [Runtime admission](#runtime-admission)
2. [Authority and evidence](#authority-and-evidence)
3. [Choose the views](#choose-the-views)
4. [Build in an EA workbench](#build-in-an-ea-workbench)
5. [Links](#links)
6. [Persist safely](#persist-safely)
7. [Reload and render QA](#reload-and-render-qa)
8. [Result](#result)

## Runtime admission

Resolve the exact vault, drawing path, requested effect, and local vault policy before mutation.
Read the vault's authoring, provenance, protected-content, and nested `AGENTS.md` rules; they own placement, metadata, and Git policy.
Reuse the single canonical authorized drawing.
For an additive request, preserve its frontmatter and every existing scene element; for a new drawing, apply the metadata required by the target vault and plugin policy.
For a new drawing, use the active plugin's verified create/open surface to create that one authorized artifact and open its Excalidraw leaf before acquiring the workbench.
Do not synthesize compressed `.excalidraw.md` data or guess a command name; if the local plugin cannot produce the target file and matching leaf through an observed supported surface, report that blocker and stop.

Verify all three local runtime layers instead of treating a plugin ID in a list as installation proof:

1. Confirm the plugin directory contains its installed `manifest.json` and `main.js` through a read-only probe.
2. In the running target vault, inspect `app.plugins.getPlugin("obsidian-excalidraw-plugin")` and its `manifest.version`.
3. Confirm `typeof ExcalidrawAutomate !== "undefined"`, `typeof ExcalidrawAutomate.getAPI === "function"`, and the methods used by the planned script.

Use this read-only in-app query as the version/API probe:

```javascript
JSON.stringify({
  plugin: Boolean(app.plugins.getPlugin("obsidian-excalidraw-plugin")),
  api: typeof ExcalidrawAutomate !== "undefined",
  version: app.plugins.getPlugin("obsidian-excalidraw-plugin")?.manifest?.version ?? null,
});
```

Use the official [Excalidraw plugin repository](https://github.com/zsviczian/obsidian-excalidraw-plugin), [manifest](https://github.com/zsviczian/obsidian-excalidraw-plugin/blob/master/manifest.json), and [ExcalidrawAutomate type surface](https://github.com/zsviczian/obsidian-excalidraw-plugin/blob/master/docs/API/ExcalidrawAutomate.d.ts) as primary API sources.
The calls below are field-verified with Excalidraw 2.27.3; on another version, capability-probe every used call and recheck the official type surface rather than assuming compatibility.
Treat a changed stable plugin release, a changed method signature, or a failed capability probe as the update trigger for this reference.
Do not install or enable the plugin, switch machines, or change plugin/app settings without authority for that separate effect.
If the local plugin or API is absent, report the missing layer and observed version/path evidence, perform only source and layout preparation, and do not claim that a drawing was saved or rendered.
Use [`doctor.md`](doctor.md) only when the request also authorizes plugin diagnosis or repair.

## Authority and evidence

Honor the user's selected source of truth.
When a repository is authoritative, pin the reviewed commit, inspect implementation and real callsites, and link source cards to files at that commit.
Label mounted or router declarations separately from inspected internals, and distinguish source defaults from observed deployed behavior.
Treat vault notes as background unless the user makes them authoritative.
Read every note used for meaning; do not equate a central hub concept with an edge-local module because their names look related.

Use a reference image for visual language only.
Do not infer services, instrumentation, protocols, providers, latency, measured values, payload fields, or runtime behavior from its appearance.
Attach CPU/GPU ownership to the particular verified stage and provider; evidence for one adapter never labels every ML stage.
Keep uncertain or uninspected behavior visibly unknown.

## Choose the views

Start architecture work with system or container boundaries and logically nested modules, not a linear overview.
Represent a browser SPA as a logical client even when a backend container serves its static files; distinguish where it is served from where it runs.
Add only the complementary frames the task and sources support:

| View | Required evidence and semantics |
|---|---|
| Runtime or ML pipeline | Actual data shapes, branches, stage/provider ownership, and verified CPU/GPU placement. |
| Sequence | Lifelines, calls and returns, `loop`/`opt`/`alt`, and explicit asynchronous boundaries. Do not add a camera acknowledgment or per-frame status round-trip unless source proves it. |
| Data contracts | Actual field names, optionality, producers, consumers, and source links. Missing model score is absent/unknown, not normal or zero. |
| Compose or deployment | Declared services, prerequisites, ports, volumes, and dependencies; do not present a declaration as observed running state. |
| Observability | Actual logs, metrics, events, and inspection channels. Label any synthetic debug timeline as illustrative and never present invented values as observations. |

Keep event probability, event admission, local acceptance, and upstream receipt as distinct states.
Place complementary frames to the right of or below the retained layout unless the target policy specifies another expansion direction.

## Build in an EA workbench

Author the script outside compressed drawing data and syntax-check it before execution.
Acquire a detached workbench and persisted baseline before drawing:

```javascript
async function loadDrawing(drawingPath) {
  const ea = ExcalidrawAutomate.getAPI();
  ea.reset();
  const file = app.vault.getAbstractFileByPath(drawingPath);
  const leaf = app.workspace.getLeavesOfType("excalidraw")
    .find((candidate) => candidate.view.file?.path === drawingPath);
  if (!file || !leaf) throw new Error(`Open the Excalidraw file first: ${drawingPath}`);
  const before = await ExcalidrawAutomate.getSceneFromFile(file);
  return {ea, file, leaf, before};
}
```

Stop when the file, Excalidraw leaf, scene, or any required method is absent.
Snapshot original element IDs plus geometry, text, links, frame/group membership, and arrow bindings before an additive edit.
Build helpers around `ea.addFrame`, `ea.addRect`, `ea.addText`, `ea.addArrow`, `ea.connectObjects`, and `ea.addToGroup` so every card records its frame, readable text bounds, optional source/term link, and connector policy.
Assign each child with `ea.getElement(id).frameId = frameId`, then validate that every referenced frame and element ID exists before apply.
Use explicit text width and font sizing; summarize evidence instead of pasting giant source excerpts.
Keep source-linked cards readable and reject overlaps or clipping before persistence.

Use `ea.style.roundness = null` for orthogonal multi-point arrows because rounded routes can bow outside their frame.
Restore the desired card roundness afterward.
Use straight arrows where they remain unambiguous and `ea.connectObjects(a, "right", b, "left", {padding: 9})` for simple bound connections.

## Links

Keep pinned GitHub source badges visually distinct from project-note navigation.
A source badge uses an HTTPS URL pinned to the reviewed commit, not a moving branch.
A domain term receives a wikilink only when its actual note exists and has the required kind.
Resolve each candidate in drawing context with `app.metadataCache.getFirstLinkpathDest(name, drawingPath)`, inspect the returned file and metadata when kind matters, and reject unresolved or wrong-kind targets.
Do not fabricate note names, create a terminology encyclopedia automatically, or link a merely similar concept.
Set a validated target with `ea.getElement(id).link = "[[Existing Note]]"` or the pinned HTTPS URL.

## Persist safely

For additive elements, target the open view and let the plugin manage persistence:

```javascript
ea.setView(leaf.view);
const applied = await ea.addElementsToView(false, true, true);
if (!applied) throw new Error("ExcalidrawAutomate did not apply the scene");
```

For an authorized edit to an existing element, call `ea.copyViewElementsToEAforEditing([existing])`, mutate `ea.getElement(existing.id)`, and commit through the same `addElementsToView` path.
Do not use `deleteViewElements` as an additive update.
Use full-scene replacement only when explicitly authorized and after preservation plus rollback review.
Do not rely on direct `leaf.view.excalidrawAPI.updateScene()` followed by an immediate save; a live scene can look correct while the file still contains the old scene.

Discover the native `obsidian-cli` skill for the supported command surface when invoking a script through the official Obsidian CLI; this reference owns the asynchronous completion guard.
Use the selected CLI's `eval` command in this order:

```bash
node --check "${DRAWING_SCRIPT}"
obsidian vault="${VAULT_NAME}" eval code="eval(require('fs').readFileSync('${DRAWING_SCRIPT}','utf8'))"
obsidian vault="${VAULT_NAME}" eval code='JSON.stringify(window.__obsidianVisualizeResult ?? null)'
```

Name the script's complete asynchronous entry point `runVisualization` or substitute its actual function name below.
Initialize a run-scoped pending result before the first asynchronous operation and only let that run publish its terminal state:

```javascript
function runWithVisualizeStatus(operation) {
  const runId = (window.__obsidianVisualizeRunSeq ?? 0) + 1;
  window.__obsidianVisualizeRunSeq = runId;
  window.__obsidianVisualizeResult = {runId, status: "pending"};

  Promise.resolve()
    .then(operation)
    .then((value) => {
      if (window.__obsidianVisualizeRunSeq === runId) {
        window.__obsidianVisualizeResult = {runId, status: "fulfilled", value};
      }
    })
    .catch((error) => {
      if (window.__obsidianVisualizeRunSeq === runId) {
        window.__obsidianVisualizeResult = {
          runId,
          status: "rejected",
          error: error instanceof Error ? (error.stack ?? error.message) : String(error),
        };
      }
    });
  return runId;
}

runWithVisualizeStatus(runVisualization);
```

An async `eval` may return no output before work finishes.
Query the result in a subsequent `eval`, record the current `runId`, and continue polling until that same run reaches `fulfilled` or `rejected`; never accept a terminal result from an earlier run.
Do not race persistence, export, or readback after blank CLI output.

## Reload and render QA

Independently reload the file with `await ExcalidrawAutomate.getSceneFromFile(file)` after the apply finishes.
For additive work, prove that all original IDs remain and the snapshotted geometry, text, links, memberships, and bindings are unchanged; separately verify each new frame and element.
Check unique IDs, valid `frameId` targets, group membership, arrow binding targets, frame containment, and every wikilink resolution.

Render each added or changed frame from the reloaded scene, never from the unsaved workbench.
For each frame, reset a fresh EA instance, copy the frame plus elements whose `frameId` matches into `elementsDict`, set canvas theme/background, and call `await ea.createPNG(undefined, 1, {withBackground: true, withTheme: true}, undefined, "light")`.
Write the blob bytes to a temporary PNG and inspect the image visually for overlaps, clipping, illegible source cards, bad hierarchy, arrow curves, and incorrect semantics.
Fix defects, persist again, reload again, and repeat the affected exports.

After QA, focus the relevant frame with `leaf.view.zoomToElements(false, elementsForFrame)` or the view's available `zoomToFit(false)`.
Do not call an unverified `excalidrawAPI.scrollToContent` method.
Do not rebuild unrelated indexes or change plugin configuration.

## Result

Return the vault-relative artifact link, selected source-of-truth commit or note evidence, created or changed frames, persisted-scene checks, link resolution counts, rendered-frame inspection result, and focused frame.
Separate verified facts from unavailable checks.
An absent API, unresolved link, failed persistence reload, preservation mismatch, or uninspected render is a precise partial-result blocker, never a generic success claim.
