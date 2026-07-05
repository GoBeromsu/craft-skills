---
name: init
description: '"init this repo", "deep init", "set up the docs structure", "bootstrap craft conventions", "generate AGENTS.md", "map this codebase", "/init" — dual-entry skill: scaffold the docs/ ontology + ADR rails (bootstrap), then generate a complexity-scored hierarchical AGENTS.md knowledge base (cartography) in one pass.'
version: 2.1.0
allowed-tools: [Bash, Read, Write, Edit, Grep, Glob, Task]
compatibility: claude-code, codex, hermes
---

# init

`init` is a **dual-entry** skill built on init-deep's cartography engine with craft-skills'
docs/ ontology + ADR scaffold grafted on as Phase 0:

- **Bootstrap path** — "init this repo", fresh/shallow repo: Phase 0 substantively seeds the
  `docs/` ontology + ADR rails; Phases 1–4 scale to the (shallow) codebase and degrade to a
  root-only map.
- **Cartography path** — "deep init", "generate AGENTS.md", "map this codebase", mature repo:
  Phase 0 mostly skips (already present); Phases 1–4 do the heavy hierarchical AGENTS.md generation.

Both paths run the same five phases in order. This file is **triage only** — it routes; the
procedures live in `references/phase-*.md`. Read each phase file when you reach it.

## Requirements

- `git`, POSIX `sh`, standard coreutils (`find`, `awk`, `sed`, `wc`).
- **Optional:** `ast-grep` (`sg`) for symbol/reference inventory when no LSP/codegraph is available
  (fallback is `grep`/`find`). LSP and codegraph tooling are optional; absent → explore/`grep`
  fallback with centrality marked "unmeasured".

## Flags (cartography engine)

```
init                 # Update mode: bootstrap if needed, then modify existing + create new AGENTS.md where warranted
init --create-new    # Read existing AGENTS.md → remove all → regenerate from scratch
init --max-depth=N   # Limit directory depth for cartography (default: 3)
```

## Triage — route the run

### Step A. Classify runtime (agent-spawn capability)

Branch once, up front; every phase honors this classification:

- **Agent-spawn runtime** — Claude Code (`Task`) or Codex (`multi_agent_v1`): Phase 1 fans out
  concurrent explore agents with dynamic scaling; Phase 3 generates subdir files in parallel.
- **Single-agent runtime** — Hermes / generic: **no fan-out.** Run Phase 1 investigations
  **sequentially** in the main session via `Bash` + `Grep` + `Glob` (+ `ast-grep` if present), and
  generate Phase 3 files one at a time. This is a first-class documented path, not a stub.

LSP/codegraph are optional in **both** branches; absent → explore/`grep`/`ast-grep` fallback,
centrality "unmeasured".

### Step B. git-guard diagnostic notice (one line, non-blocking)

init 2.0 does **not** install enforcement rails. git-guard belongs to the `worktree` skill and
self-installs there on first use. So a missing guard is visible — not silently assumed — emit one
line at start:

```bash
echo "git-guard: core.hooksPath = $(git config core.hooksPath 2>/dev/null || echo '<unset — the git skill worktree sub-recipe proposes install on first use>')"
```

### Step C. Track all phases, then run them in order

Track the five phases (e.g. with TodoWrite on Claude Code) and mark each `in_progress → completed`
in real time. Run strictly in order — each phase's output feeds the next:

| Phase | File | What it does |
|-------|------|--------------|
| **0 — Ontology graft** | `references/phase-0-ontology.md` | Scaffold `docs/` ontology + ADR index + architecture/README seeds (idempotent, non-destructive). Replace-and-log any 1.x managed block. |
| **1 — Discovery** | `references/phase-1-discovery.md` | Concurrent (or sequential) explore + bash structure + LSP/codegraph code map + read existing; dynamic agent scaling. |
| **2 — Scoring** | `references/phase-2-scoring.md` | Weighted complexity matrix → `AGENTS_LOCATIONS` (root always; >15 create; 8–15 if distinct; <8 skip). |
| **3 — Generate** | `references/phase-3-generate.md` | Root AGENTS.md (full treatment + provenance stamp + `## DOCS & DECISIONS` graft link), then scored subdirs. Existence rule: `Edit` if present, `Write` if new. |
| **4 — Review** | `references/phase-4-review.md` | Dedup-vs-parent, line budgets (root 50–150, subdir 30–80), telegraphic gate, and the final observability report. |

### Step D. Cartography scope guard

Phases 1–4 map **code** directories. Exclude the `docs/` ontology that Phase 0 just seeded — never
map the documentation scaffold back onto itself.

## Scope boundary — three skills, three responsibilities

| Responsibility | Owner |
|---|---|
| Scaffold `docs/` ontology + ADR rails (Phase 0) and generate the hierarchical AGENTS.md map (Phases 1–4) | **init** (this skill) |
| Author and maintain content inside `docs/` (ADRs, README, architecture, …) | `documents` skill |
| Install and manage git-hook enforcement (git-guard) | `worktree` skill's installer — init only emits the diagnostic notice |
| Scaffold consumer plugin manifests (`.claude-plugin`, etc.) | **out of scope for init** |

## Idempotency & safety rails

- Phase 0 is fully idempotent — re-running a bootstrapped repo writes nothing, only status notices.
- Phase 3 never `Write`s over an existing `AGENTS.md` — `Edit` existing, `Write` new.
- The Development Flow managed block is the **only** existing content init may replace, and it logs
  the replacement.
- Every run ends with the Phase 4 observability report (path taken, centrality measured/unmeasured,
  files created/updated, managed-block action) — no silent or degraded run.

## Red flags

- Inlining the scoring matrix, generation templates, or phase procedures into this file (they live
  in `references/` — this file stays at triage depth).
- Overwriting an existing file (`docs/`, `README.md`, or an `AGENTS.md`) with a template.
- Assuming `Task`/fan-out on a single-agent runtime instead of the sequential path.
- Emitting a confident centrality number when neither LSP nor codegraph was available.
- Leaving a 1.x hard-rail managed block in place, or claiming init installs governance/enforcement.
- Skipping the final report, or finishing without stating the path taken and managed-block action.
