# ExcalidrawAutomate Workbench (Exception Path)

Use this only for the two cases [`visualize.md`§6](visualize.md#6-exception-live-edits-through-the-plugin) names: interactive edits inside a drawing the user has open right now, or embedding files that must go through the plugin's file store.
Every other Excalidraw request writes the file directly per `visualize.md`.

## Table of contents

1. [Plugin admission](#1-plugin-admission)
2. [Acquire the workbench](#2-acquire-the-workbench)
3. [Persist the edit](#3-persist-the-edit)
4. [Async completion guard](#4-async-completion-guard)
5. [Reload and render QA](#5-reload-and-render-qa)

## 1. Plugin admission

Probe the plugin and API before planning any call — package discovery or skill-loader state is not an installation check:

```javascript
JSON.stringify({
  plugin: Boolean(app.plugins.getPlugin("obsidian-excalidraw-plugin")),
  api: typeof ExcalidrawAutomate !== "undefined",
  version: app.plugins.getPlugin("obsidian-excalidraw-plugin")?.manifest?.version ?? null,
});
```

Probe the actual methods the task will call, not just plugin presence.
If the plugin or API is absent, report the missing layer and stop — do not fall back to guessing a command or installing/enabling the plugin without separate authority for that effect.
Primary sources: the [plugin repo](https://github.com/zsviczian/obsidian-excalidraw-plugin), its [manifest](https://github.com/zsviczian/obsidian-excalidraw-plugin/blob/master/manifest.json), and the [ExcalidrawAutomate type surface](https://github.com/zsviczian/obsidian-excalidraw-plugin/blob/master/docs/API/ExcalidrawAutomate.d.ts).

## 2. Acquire the workbench

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

Stop when the file, leaf, scene, or a required method is missing.
Snapshot original element ids, geometry, text, links, and frame/group/arrow bindings before an additive edit so step 5 can prove nothing else moved.
Build with `ea.addFrame`, `ea.addRect`, `ea.addText`, `ea.addArrow`, `ea.connectObjects`, `ea.addToGroup`; set `ea.style.roundness = null` before an orthogonal multi-point arrow (rounded routes can bow outside the frame), then restore it.

## 3. Persist the edit

```javascript
ea.setView(leaf.view);
const applied = await ea.addElementsToView(false, true, true);
if (!applied) throw new Error("ExcalidrawAutomate did not apply the scene");
```

For editing an existing element: `ea.copyViewElementsToEAforEditing([existing])`, mutate `ea.getElement(existing.id)`, commit through the same `addElementsToView` call.
Never use `deleteViewElements` as a stand-in for an additive update, and never treat a live scene update as saved — a live scene can look correct while the file on disk still holds the old one; the reload in step 5 is what proves it persisted.

## 4. Async completion guard

The CLI's `eval` only returns synchronous values, so a caller driving this from the official Obsidian CLI needs its own pending/result handshake with a nonce it controls — never inferred from whatever the last poll happened to return:

```javascript
function createVisualizationRequest() {
  return {expectedNonce: crypto.randomUUID(), launchAttempted: false};
}

function publishVisualizationResult(expectedNonce, terminal) {
  const pending = window.__obsidianVisualizePending;
  if (!pending || pending.nonce !== expectedNonce) return;
  window.__obsidianVisualizeResult = {nonce: expectedNonce, ...terminal};
}

function launchVisualization(request, operation) {
  if (!request?.expectedNonce) throw new Error("A caller-known visualization nonce is required");
  if (request.launchAttempted) throw new Error("This visualization request was already launched");
  request.launchAttempted = true;
  const {expectedNonce} = request;
  window.__obsidianVisualizePending = {nonce: expectedNonce, status: "pending"};
  window.__obsidianVisualizeResult = {nonce: expectedNonce, status: "pending"};
  Promise.resolve().then(operation).then(
    (value) => publishVisualizationResult(expectedNonce, {status: "fulfilled", value}),
    (error) => publishVisualizationResult(expectedNonce, {
      status: "rejected",
      error: error instanceof Error ? (error.stack ?? error.message) : String(error),
    }),
  );
}

function pollVisualization(expectedNonce) {
  const pending = window.__obsidianVisualizePending;
  const result = window.__obsidianVisualizeResult;
  if (!pending || pending.nonce !== expectedNonce) return {status: "not-started-or-stale", expectedNonce};
  if (!result || result.nonce !== expectedNonce) return {status: "pending", nonce: expectedNonce};
  return result.status === "fulfilled" || result.status === "rejected" ? result : {status: "pending", nonce: expectedNonce};
}
```

Create the request and keep `expectedNonce` before launching; pass the same value to every later poll.
A blank or not-executed launch, or an older fulfilled result under a different nonce, both surface as `not-started-or-stale` from `pollVisualization` — never accept that as this request's result.
A rejected result, a timeout, or a mismatched identity is a precise incomplete outcome; report it.
A retry needs a new caller-generated nonce and fresh authorization for another mutation — never replay silently.

## 5. Reload and render QA

Reload independently after the apply finishes: `await ExcalidrawAutomate.getSceneFromFile(file)`.
For an additive edit, prove every original id and its snapshotted geometry/text/links/memberships/bindings are unchanged, then separately verify the new elements — unique ids, valid `frameId` targets, group membership, arrow binding targets, wikilink resolution.

Render each changed frame from the *reloaded* scene, never the unsaved workbench: fresh EA instance, copy the frame's elements into `elementsDict`, set theme/background, `await ea.createPNG(undefined, 1, {withBackground: true, withTheme: true}, undefined, "light")`.
Write the bytes to a temp PNG and look at it — overlaps, clipping, illegible cards, bad hierarchy, wrong semantics.
Fix, persist, reload, re-render until clean, then focus with `leaf.view.zoomToElements(false, elementsForFrame)` or `zoomToFit(false)` (don't call the unverified `excalidrawAPI.scrollToContent`).
