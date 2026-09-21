---
name: obsidian
description: Routes native Obsidian skills and local app/plugin coordination. Use for vault note create/edit/cleanup (“옵시디언 노트 정리”; not filing/taxonomy), `.base` or embedded base blocks with `groupBy`/`sort`/`limit` and Dataview-to-Bases, `.canvas` mind maps, Obsidian Mermaid, `obsidian visualize` Excalidraw architecture diagrams, official `obsidian` CLI note read/create/move/write plus `backlinks`/`unresolved` audits, readback verification, `Vault not found`, and `obsidian` versus `obsidian-cli`, Web Clipper templates (YouTube/GitHub) with variables/filters, “플러그인 고쳐줘”, silent plugin failures, API skew, Templater `ReferenceError`/`<%`, or headless `ob` Sync (“headless sync 점검”, “obsidian sync status”, “볼트 동기화 복구”, “pull-only로 맞춰줘”, daemon restart). Not for web extraction, CommonMark, Dataview queries, React Flow, non-Obsidian Mermaid/Excalidraw, outside-vault files, core app bugs, desktop Sync/Dropbox replication, or filing/provenance.
metadata:
  version: 2.1.0
---
# Obsidian

Compose the native format and CLI skills with local app, plugin, renderer, and Sync coordination so the requested artifact follows the real runtime behavior while preserving unrelated vault content.

## Output contract

Return the verified artifact or runtime state, selected sub-recipe, readback evidence, and every unavailable prerequisite.
If the vault is unresolved, the runtime or command surface is unavailable or unsupported, or readback evidence is missing, stop and report the condition without inventing an operation.

## Requirements

Use only the tools required by the selected sub-recipe:

- `${OBSIDIAN_VAULT_PATH}` for an exact vault root when filesystem readback is required.
- The native skill packages `obsidian-markdown`, `obsidian-bases`, `json-canvas`, and `obsidian-cli`, discovered by package identity through the active runtime's skill loader. Their official originals own format, schema, and command details; this package does not copy or replace them. The `obsidian-cli` name is a skill identity, not a promise about an executable named `obsidian-cli`.
- An active local Excalidraw plugin and ExcalidrawAutomate API for [`obsidian visualize`](references/visualize.md); plugin installation, enablement, settings changes, and cross-machine execution remain separate effects.
- `ob` from `obsidian-headless` for the headless Sync pairing and daemon sub-recipe.
- A real browser when Web Clipper selectors must be tested against a page.
- Runtime and release maintenance: record the relevant [Obsidian Help](https://help.obsidian.md/), [Obsidian developer documentation](https://docs.obsidian.md/), and official app, CLI, plugin API, or Sync release source. Use an installed app or CLI version probe only when current official documentation supports that exact probe; otherwise observe the version in the app and record it as unknown to automation. When probe or release evidence shows an app, CLI, plugin API, or Sync runtime form changed, recheck official documentation, rerun affected package evaluations, update the recipe if needed, then bump this package's version and append its CHANGELOG.

Never hardcode a host path, vault name, account identifier, remote host, or credential.

## Route the request

| Intent | Load |
|---|---|
| Write, edit, or reformat note prose; wikilinks, embeds, callouts, properties, tags, dates, people links, or house style | Discover `obsidian-markdown`; use [the local target-vault boundary](references/markdown.md) only for authorization and destination readback |
| Create, debug, or optimize a `.base` file or `base` code block | Discover `obsidian-bases`; use [the local Bases coordination](references/bases.md) only for app/rendering evidence |
| Create or edit a `.canvas` JSON Canvas graph | Discover `json-canvas`; use [the local Markdown target boundary](references/markdown.md#non-markdown-targets-and-destination-readback) for links and embeds |
| Author or repair Mermaid that must render in Obsidian | [`references/mermaid.md`](references/mermaid.md) |
| Create or extend a note-grounded Excalidraw architecture or other visualization through the local plugin API | [`references/visualize.md`](references/visualize.md) |
| Read, create, search, move, mutate, or link-audit vault notes | Discover `obsidian-cli`; this package contributes only target-vault authority and readback boundaries |
| Build or debug an Obsidian Web Clipper JSON template | [`references/clipper.md`](references/clipper.md) |
| Diagnose a plugin, Templater template, plugin API, or plugin-driven script | [`references/doctor.md`](references/doctor.md) |
| Bootstrap, pair, operate, or recover the headless `ob` Sync client | [`references/sync.md`](references/sync.md) |
| Read Sync state for a vault the desktop app already syncs | Discover `obsidian-cli`; keep Sync lifecycle and supervisor evidence in [`references/sync.md`](references/sync.md) |

Load more than one sub-recipe only when responsibilities genuinely compose.
For example, a vault mutation composes the applicable native Obsidian mutation surface with native `obsidian-markdown` and `markdown.md` for target-vault authority and destination readback.
A Mermaid fence inside a note composes native `obsidian-markdown` with `mermaid.md` for renderer compatibility.
Linking or embedding a Canvas in a note uses [Markdown link targeting and readback](references/markdown.md#non-markdown-targets-and-destination-readback), native `json-canvas`, and the existing Canvas renderer guidance in [`references/markdown-embeds.md`](references/markdown-embeds.md#embed-canvas).
An Excalidraw visualization uses `visualize.md` for local API admission, evidence-grounded scene construction, plugin-managed persistence, and rendered QA; use `markdown.md` only when the task also changes a note that links or embeds the drawing.

## Shared operating contract

1. **Resolve the exact artifact.** Identify the vault, note-relative path, `.base`/`.canvas` file, plugin id, template, or Sync pairing before changing it.
2. **Read before writing.** Preserve unrelated content, metadata, IDs, edge references, and source URLs.
3. **Apply the matching native package and local boundary.** Do not substitute generic Markdown, JSON, shell file editing, or browser assumptions for Obsidian-specific behavior.
4. **Use the least destructive applicable native surface.** Use the native `obsidian-cli` surface when a vault-aware CLI operation is the selected owner, or preserve an independently authorized native Obsidian mutation surface for another effect; never bypass the selected owner with raw writes or an unrelated third-party CLI. Treat delete, unlink, reset, mirror, cleanup, and bulk replacement as destructive operations requiring explicit scope and approval.
5. **Read back the result.** Verify the exact file or runtime state after every mutation. A successful exit code without materialized output is not completion.
6. **Report evidence.** Name the verified artifact and check performed; disclose any unavailable runtime or UI check as unverified.
7. **Ground mutable runtime facts.** For Obsidian app, CLI, plugin API, or Sync behavior, consult official documentation first. Disclose conflicts; a more-specific vault-local contract or reproducible evidence for the matching app/plugin version and platform may override general or stale documentation. If unresolved, keep it unknown and stop or use the sub-recipe's safe fallback — never invent a command or capability.

## Boundaries

This package owns uncovered app, plugin, renderer, and Sync coordination plus target-vault authorization and native-surface readback.
A discovered native skill owns its format, field/type, schema, and command details; the target-vault/OMS owner or personal policy owns authorization, template selection, placement, provenance, and house style.
A personal knowledge-management skill may own what a note means, where it belongs, required provenance, and which template frame applies; compose that policy with this package rather than duplicating it here.
Before a note write, resolve the actual target-vault policy and its native owner, the exact note and authorized change, required provenance, and protected content.
Reusable mechanics, a writable tool, or a folder classification do not grant write authority.
Reuse existing task-bound authority when it covers that note and effect; do not demand redundant consent.
When authority or the native capability is absent or ambiguous, keep the operation read-only and report the specific gap rather than bypassing the owner or editing user profiles to manufacture permission.
Static public-page extraction belongs to an extractor such as `defuddle`, not Web Clipper or browser automation.
Generic Mermaid outside Obsidian does not inherit Obsidian’s bundled-renderer compatibility baseline.
Generic file synchronization, Git conflicts, and backup systems are outside the headless Obsidian Sync sub-recipe.

## Anti-patterns

- Loading every reference for every request → load only the selected sub-recipe and any explicitly composing neighbor.
- Editing a vault note with raw shell text tools → use the selected native CLI or OMS surface and exact readback.
- Rewriting a native format or command catalog locally → load the matching official package by identity and report a capability gap when it is unavailable.
- Conflating the `obsidian-cli` skill identity with a binary, or treating a third-party `obsidian-cli` executable as the official surface → use the executable and runtime documented by the discovered native skill, or report the unsupported surface.
- Declaring a tool unavailable after one failed probe → confirm with a second, different probe before reporting a degraded path.
- Treating `.base`, `.canvas`, Mermaid, and Markdown as one syntax → route by artifact type; each has a separate parser and invariant set.
- Replacing a requested Excalidraw visualization with Mermaid, JSON Canvas, a pasted screenshot, or compressed drawing-data edits → use `visualize.md` and verify the persisted scene plus rendered frames.
- Trusting a Web Clipper selector without testing the real page → inspect the page and verify every selector before shipping JSON.
- Editing plugin state files or bundled plugin code directly → follow `doctor.md` and use the plugin/runtime’s supported mutation surface.
- Enabling bidirectional or continuous headless Sync before a one-shot pull-only verification → follow `sync.md`’s staged promotion gate.
- Letting this reusable package decide a personal vault’s taxonomy or filing zone → load the personal policy owner for those decisions.

## Verification

- [ ] The request was routed to the correct native package and local coordination reference.
- [ ] The exact target and applicable runtime prerequisites were verified.
- [ ] Unrelated content and metadata were preserved.
- [ ] Destructive operations had explicit approved scope or were skipped.
- [ ] The changed artifact or runtime state was read back exactly.
- [ ] Any composed sub-recipes had distinct responsibilities.
- [ ] Any CLI claim names which binary produced it, and a tool reported unavailable was probed at least twice.
