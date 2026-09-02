---
name: init
description: Maps a repository into a maintained hierarchical AGENTS.md knowledge base. Use when asked to "init this repo" for AGENTS, deep-init a codebase, generate or update AGENTS.md, map repository conventions, audit existing AGENTS coverage, or report stale managed AGENTS regions. Not for package-manager or plugin initialization, docs scaffolding or authoring (use `document`), or git-hook installation (use `git`).
metadata:
  version: 4.1.1
---

# init

Map a repository into a maintained hierarchical `AGENTS.md` knowledge base with evidence-backed placements and preserved incumbent instructions.

## Output contract

Return the written or read-only audit result with the affected `AGENTS.md` paths, evidence sources, managed-region status, and unavailable paths.
If paths are unreadable, scope evidence is ambiguous, or a managed region was hand-edited, stop and report the condition without overwriting incumbent content.

Placement and content are judgment, so they live in this file as prose.
Only one step is fragile enough to be executable: editing a marker-delimited region without disturbing surrounding bytes.

## Invocation

| Request | Meaning |
|---|---|
| `init`, or `init map` | Map the repository: inventory, choose placements, write managed regions. |
| `init audit` | Report current state read-only. Never write. |
| `init report-stale` | Name managed regions no longer backed by a placement. Never delete. |

Bare `init` means map. Do not ask which mode was intended, and do not treat bare `init` as a selector.
`audit` and `report-stale` require their explicit words.

## Map

Work top down and stop as soon as the repository is described.

1. **Inventory.** Read the tree without following symlinks. Note first-party directories, their file types, declared entry points, and configuration files. Skip `.git`, `node_modules`, `vendor`, `dist`, `build`, `__pycache__`, and comparable vendored or generated trees.
2. **Preflight mutable tools.** Before recording a tool-dependent instruction, follow [tool preflight](references/tool-preflight.md) and keep unavailable or unsupported command surfaces explicit.
3. **Place the root.** A root `AGENTS.md` always exists.
4. **Place a child only on evidence.** Add a nested `AGENTS.md` when a directory owns its own build or dependency configuration, presents a distinct entry boundary, and holds enough code that root guidance would be wrong there. Prefer fewer files. A directory that merely holds many files is not a scope.
5. **Write content that a newcomer could not infer.** Commands actually declared in that scope, entry points, local conventions, and constraints. Cite the file each claim comes from. Never invent a command; if no command is declared, say so.
6. **Do not repeat the parent.** A child file adds only what differs from the instruction chain above it.
7. **Install each payload** as a managed region using the script below.

Keep a root file within roughly 50-150 lines and a child file within roughly 30-80.
When evidence exceeds that, summarize and state the omitted count rather than truncating silently.

## Audit

Report, without writing anything: which `AGENTS.md` files exist, which managed regions are present and internally consistent, which scopes look uncovered, and which paths could not be read.
State loading behavior as unknown unless a runtime probe actually demonstrated it.
Never infer loading from directory placement or from a successful map.

## Report stale

Name any managed region whose scope no longer warrants a placement, then stop.
`init` has no deletion authority: removing a file or a region is the user's decision, and hand-editing is fine because the region markers make ownership visible.

## The one script

```sh
python3 skills/init/scripts/agents_region.py <path> --id <region-id> --payload-file <file|->
```

It replaces exactly one `<!-- init:managed id=... -->` region, or appends one when the file has none, and preserves every other byte plus the file mode.
It refuses symlinks, non-regular files, non-UTF-8 content, and files holding two regions with the same id.
The hash in each opening marker is checked before any rewrite, so a region someone edited by hand is refused rather than overwritten; resolve that edit first, either by keeping the human text outside the markers or by folding it into the payload.
Exit `0` on success with a JSON receipt, `2` on refusal with a JSON error.
Rerunning it with the same payload is a byte-identical no-op.

Use one stable id per scope, for example `init-root` or `init-<directory>`.

## Safety and canonicality

Before working on a path, read every `AGENTS.md` from the repository root through that path's directory in order; the nearest instruction wins on conflict.
This reading rule is instruction, not proof of how a runtime loads files.

Existing content is never silently adopted, overwritten, or deleted.
This holds inside the markers too: a hand-edited region is reported, not rewritten.
When a file already holds substantive instructions, keep them: the script appends rather than replacing, and consolidating them into managed content requires the user's agreement.
When a `CLAUDE.md` holds anything other than the exact adapter bytes, migrate its content into `AGENTS.md` with the user's agreement before installing the adapter.

## Boundaries

| Responsibility | Owner |
|---|---|
| AGENTS placement, content, canonicality, audit, and stale reporting | **init** |
| Documentation scaffolding, README, ADRs, and substantive docs content | `document` |
| Git hooks and enforcement rails | `git` |
| Package, plugin, or ecosystem initialization | Outside init |

## Requirements

- `python3` — official source: <https://docs.python.org/3/>; safe probe: `python3 --version`; support boundary: Python 3.10+ for the region script and its test module.
- Dependency trigger — a selected Python release or a changed probe result requires official-documentation review and rerunning `python3 -m unittest discover -s skills/init/tests -p 'test_*.py'` before trusting this recipe.
- [Tool preflight](references/tool-preflight.md) records mutable CLI probes, support boundaries, incompatibilities, and CHANGELOG verification receipts.

## Anti-patterns

- Asking whether bare `init` meant map → bare `init` is map.
- Deleting a file or region because it looks stale → report it and let the user decide.
- Overwriting incumbent instructions to install managed content → preserve them and ask.
- Writing a nested `AGENTS.md` because a directory has many files → require configuration, an entry boundary, and real weight.
- Restating parent guidance in a child file → keep only the local difference.
- Claiming a command that no configuration declares → cite the source file or omit it.
- Editing a managed region with ad-hoc string replacement → use the script.
- Reporting loader behavior as known without a probe → say unknown.
