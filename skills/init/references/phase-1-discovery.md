# Phase 1 — Discovery + Analysis

This is the **cartography** engine's first phase. It builds the raw material — structure, code
map, existing knowledge, project-specific conventions — that Phase 2 scores. Phase 0 (the docs/
ontology graft) runs before this; on a mature repo Phase 0 mostly skips and the run is dominated
by Phases 1–4.

## Table of Contents

- [Runtime branch: how discovery fans out](#runtime-branch-how-discovery-fans-out)
- [Concurrent explore fan-out](#concurrent-explore-fan-out-agent-spawn-runtimes)
- [Main-session analysis](#main-session-analysis-always-runs-both-branches)
- [Collect + merge](#collect--merge)

---

## Runtime branch: how discovery fans out

SKILL.md has already classified the runtime. Honor that classification here:

- **Agent-spawn runtimes** (Claude Code `Task`, Codex `multi_agent_v1`): fire the explore agents
  **concurrently in the background** and do the main-session bash/LSP/codegraph analysis while they
  run, then collect their results.
- **Single-agent runtimes** (Hermes, generic): there is no fan-out. Run the same investigations
  **sequentially in the main session** using `Bash` + `Grep` + `Glob` (and `ast-grep`/`sg` if
  present). Cover every explore role's question yourself, in order. This path is slower but
  produces the same merged findings.

The report (see phase-4) must state which path was taken.

## Concurrent explore fan-out (agent-spawn runtimes)

Fire these immediately — they run async while the main session works. Each agent role is a
**self-contained prompt**; do not assume any harness-specific tool name inside it. Where a code
graph or LSP is available, instruct the agent to ground its claims in that data rather than guessing
from directory conventions.

Standing roles (fire all at once, collect later):

1. **Project structure** — map the real layout; report deviations from standard patterns.
2. **Entry points** — find main/index files, trace what they reach; report non-standard organization.
3. **Conventions** — find config files (`.eslintrc`, `pyproject.toml`, `.editorconfig`, …); report
   project-specific rules.
4. **Anti-patterns** — find `DO NOT` / `NEVER` / `ALWAYS` / `DEPRECATED` comments; list forbidden patterns.
5. **Build/CI** — find `.github/workflows`, `Makefile`, task runners; report non-standard patterns.
6. **Test patterns** — find test configs/structure and what the core modules cover; report unique conventions.

### Dynamic agent spawning

After the bash structural pass below, spawn **additional** explore agents scaled to project size.
This table is load-bearing — static agent counts are an anti-pattern:

| Factor | Threshold | Additional agents |
|--------|-----------|-------------------|
| **Total files** | >100 | +1 per 100 files |
| **Total lines** | >10k | +1 per 10k lines |
| **Directory depth** | ≥4 | +2 for deep exploration |
| **Large files (>500 lines)** | >10 files | +1 for complexity hotspots |
| **Monorepo** | detected | +1 per package/workspace |
| **Multiple languages** | >1 | +1 per language |

Example: 500 files, 50k lines, depth 6, 15 large files → +5 +5 +2 +1 = **13 additional agents**
(large-file analysis, deep-module exploration, shared-utility scan, …).

On single-agent runtimes there are no extra agents — instead, the main session spends
**proportionally more passes** on the same hotspots the table would have fanned out to (large
files, deep modules, each workspace, each language).

## Main-session analysis (always runs, both branches)

### 1. Bash structural analysis

```bash
# Directory depth histogram
find . -type d -not -path '*/\.*' -not -path '*/node_modules/*' -not -path '*/venv/*' \
  -not -path '*/dist/*' -not -path '*/build/*' | awk -F/ '{print NF-1}' | sort -n | uniq -c

# Files per directory (top 30)
find . -type f -not -path '*/\.*' -not -path '*/node_modules/*' \
  | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -30

# Code concentration by extension
find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" \
  -o -name "*.go" -o -name "*.rs" \) -not -path '*/node_modules/*' \
  | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -20

# Existing AGENTS.md / CLAUDE.md
find . -type f \( -name "AGENTS.md" -o -name "CLAUDE.md" \) -not -path '*/node_modules/*' 2>/dev/null
```

Also measure the scale inputs the dynamic-agent table consumes:

```bash
total_files=$(find . -type f -not -path '*/node_modules/*' -not -path '*/.git/*' | wc -l)
total_lines=$(find . -type f \( -name "*.ts" -o -name "*.py" -o -name "*.go" \) \
  -not -path '*/node_modules/*' -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
large_files=$(find . -type f \( -name "*.ts" -o -name "*.py" \) -not -path '*/node_modules/*' \
  -exec wc -l {} + 2>/dev/null | awk '$1 > 500 {count++} END {print count+0}')
max_depth=$(find . -type d -not -path '*/node_modules/*' -not -path '*/.git/*' \
  | awk -F/ '{print NF}' | sort -rn | head -1)
```

### 2. Read existing AGENTS.md

For each existing `AGENTS.md` / `CLAUDE.md` found, read it and extract key insights, conventions,
and anti-patterns into an `EXISTING_AGENTS` map. This feeds the update-vs-create decision in Phase 3.

If `--create-new`: **read all existing first** (preserve their context), *then* delete them, *then*
regenerate from scratch. Never delete before reading.

### 3. Code map — drive LSP and codegraph (do not skip)

This is the highest-signal source for the CODE MAP and for the Symbol/Export/Reference rows in the
Phase 2 scoring matrix. LSP and codegraph are **complementary peers**, not alternatives — run both
when present, alongside the explore agents.

- **LSP** (check status first; names may appear with or without an `lsp_` prefix):
  - document-scope symbols on each entry point → file outline.
  - workspace-scope symbols by kind (class/interface/function) → symbol inventory.
  - find-references on top exports → reference centrality.
- **codegraph** (when the `codegraph_*` family exists — a first-class peer, not a last resort):
  - explore → overview; callers/callees/impact → centrality + blast radius for the matrix;
    search/files → symbol/file inventory.

**Fallback:** only if NEITHER LSP nor codegraph exists, use the explore agents + `ast-grep` (`sg`)
for the symbol/reference inventory, and **mark centrality "unmeasured" in the CODE MAP** (and in the
final report). Never silently emit a confident centrality number you could not measure.

## Collect + merge

On agent-spawn runtimes, collect every background explore result after the main-session analysis
finishes. Then **merge** all four streams — bash structure + LSP/codegraph code map + existing
AGENTS.md insights + explore findings — into one project model. That merged model is the input to
Phase 2.
