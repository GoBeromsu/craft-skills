---
name: init
description: Bootstraps a repository's craft docs scaffold or generates a complexity-scored, hierarchical AGENTS.md knowledge base for a mature one. Use when initializing repo docs folders ("init this repo", "bootstrap craft conventions"), deep-initing a codebase ("deep init", "generate AGENTS.md", "map this codebase"), or setting up the docs structure; uses a sequential cartography path on runtimes without agent fan-out. Not for authoring docs content, ADRs, README, or architecture decisions (use the `document` skill) or installing git-guard hooks (use the `git` skill).
metadata:
  version: 3.1.0
---

# init

`init` selects an outcome, not a fixed phase ceremony. **Bootstrap** creates the craft-owned
`docs/` scaffold; **cartography** generates or updates a hierarchical `AGENTS.md` map.

Both outcomes share only these prerequisites: inspect the requested outcome and existing files
without overwriting them, then emit the git-guard diagnostic below. A docs-only request runs
Phase 0 and stops. A cartography request runs Phases 1–4; run Phase 0 first only when the caller
also asks for the docs scaffold. Do not turn a bootstrap request into codebase mapping.

This file routes; the procedures live in `references/phase-*.md` — read the selected procedure
when you reach it.

## Requirements

- `git`, POSIX `sh`, standard coreutils (`find`, `awk`, `sed`, `wc`).
- Optional: `ast-grep` (`sg`) for symbol/reference inventory when no LSP/codegraph is available
  (fallback is `grep`/`find`). LSP and codegraph tooling are optional; absent → explore/`grep`
  fallback with centrality marked "unmeasured".

## Flags (cartography engine)

```
init                 # Select the requested bootstrap or cartography outcome; update existing AGENTS.md only for cartography
init --create-new    # Read existing AGENTS.md → remove all → regenerate from scratch
init --max-depth=N   # Limit directory depth for cartography (default: 3)
```

## Route the run

### 1. Choose the requested outcome

| Request outcome | Procedure |
|---|---|
| Craft docs scaffold only | Run Phase 0 — Ontology graft. |
| Hierarchical `AGENTS.md` map | Run Phases 1–4 — Cartography. |
| Both scaffold and map | Run Phase 0, then Phases 1–4. |

### 2. Shared prerequisite — git-guard diagnostic notice

init installs no enforcement rails of its own — git-guard belongs to the `git` skill and
self-installs there on first `git wt` use. A missing guard should stay visible, not silently
assumed; emit one line at start:

```bash
echo "git-guard: core.hooksPath = $(git config core.hooksPath 2>/dev/null || echo '<unset — the git skill installs it on first git wt use>')"
```

### Cartography runtime branch

Classify the runtime before Phases 1–4:

- **Agent-spawn runtime** — Claude Code (`Task`) or Codex (`multi_agent_v1`): Phase 1 fans out
  concurrent exploration scaled to uncertainty and risk; Phase 3 can generate subdir files in
  parallel.
- **Single-agent runtime** — Hermes / generic: run Phase 1 investigations sequentially via
  `Bash` + `Grep` + `Glob` (+ `ast-grep` if present), then generate Phase 3 files one at a time.

LSP/codegraph are optional in both branches; absent → explore/`grep`/`ast-grep` fallback,
centrality "unmeasured".

### Cartography phases

Run these in order because each feeds the next:

| Phase | File | What it does |
|-------|------|--------------|
| **1 — Discovery** | `references/phase-1-discovery.md` | Explore + structure + LSP/codegraph code map + existing files; scale investigation to uncertainty and risk. |
| **2 — Scoring** | `references/phase-2-scoring.md` | Weighted complexity matrix → `AGENTS_LOCATIONS` (root always; >15 create; 8-15 if distinct; <8 skip). |
| **3 — Generate** | `references/phase-3-generate.md` | Root AGENTS.md (full treatment + provenance stamp + `## DOCS & DECISIONS` graft link), then scored subdirs. Existence rule: `Edit` if present, `Write` if new. |
| **4 — Review** | `references/phase-4-review.md` | Dedup-vs-parent and line-budget review. |

### Cartography scope guard

Phases 1–4 map **code** directories. Exclude the `docs/` ontology that Phase 0 seeded — never
map the documentation scaffold back onto itself.

## Completion report

End every run with one explicit outcome report: selected branch; docs scaffold action; files
created or updated; and, for cartography, runtime path, centrality measured/unmeasured, directories
analyzed, and managed-block action. Mark inapplicable fields `n/a` and name any unavailable evidence
rather than omitting it.

## Boundaries

| Responsibility | Owner |
|---|---|
| Scaffold craft-owned `docs/` folders/files (Phase 0) and generate the hierarchical AGENTS.md map (Phases 1-4) | **init** (this skill) |
| Author root README content or substantive content inside `docs/` (ADRs, architecture decisions, …) | `document` skill |
| Install and manage git-hook enforcement (git-guard) | `git` skill — init only emits the diagnostic notice |
| Scaffold consumer plugin manifests (`.claude-plugin`, etc.) | out of scope for init |

## Idempotency & Safety Rails

- Phase 0 is fully idempotent — re-running a bootstrapped repo writes nothing, only status notices.
- Phase 3 never `Write`s over an existing `AGENTS.md` — `Edit` existing, `Write` new.
- The Development Flow managed block is the **only** existing content init may replace, and it logs
  the replacement.

## Anti-patterns

- Inlining the scoring matrix, generation templates, or phase procedures into this file → keep
  them in `references/`; this file stays at triage depth.
- Overwriting an existing docs anchor or `AGENTS.md` with a template →
  `Edit` existing files, `Write` only new ones.
- Assuming `Task`/fan-out on a single-agent runtime → run the sequential single-agent path
  (`Bash` + `Grep` + `Glob`, one file at a time) instead.
- Emitting a confident centrality number when neither LSP nor codegraph was available → mark
  centrality "unmeasured" instead.
- Leaving a legacy hard-rail managed block in place → replace it and log the replacement — the
  only existing content init may overwrite.
- Claiming init installs governance/enforcement → git-guard installation belongs to the `git`
  skill; init only emits the diagnostic notice.
- Creating or requiring ADRs when the user did not explicitly ask for ADRs → keep
  `docs/decisions/README.md` as an empty destination/index and hand off decision-record authoring
  to `document`.
