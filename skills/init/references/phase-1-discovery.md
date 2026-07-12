# Phase 1 — Discovery + Analysis

This is the **cartography** engine's first phase. It builds the raw material — structure, code
map, existing knowledge, project-specific conventions — that Phase 2 scores. It runs for the
cartography outcome, after Phase 0 only when the request also included the docs scaffold.

## Table of Contents

- [Runtime branch: how discovery fans out](#runtime-branch-how-discovery-fans-out)
- [Risk-scaled explore selection](#risk-scaled-explore-selection-agent-spawn-runtimes)
- [Main-session analysis](#main-session-analysis-always-runs-both-branches)
- [Collect + merge](#collect--merge)

---

## Runtime branch: how discovery fans out

SKILL.md has already classified the runtime. Honor that classification here:

- **Agent-spawn runtimes** (Claude Code `Task`, Codex `multi_agent_v1`): complete the structural
  pass, then run the selected explore agents **concurrently in the background** while the
  main-session LSP/codegraph analysis continues, then collect their results.
- **Single-agent runtimes** (Hermes, generic): there is no fan-out. Run the same investigations
  **sequentially in the main session** using `Bash` + `Grep` + `Glob` (and `ast-grep`/`sg` if
  present). Cover the same selected investigations yourself, in order. This path is slower but
  produces the same merged findings.

Record the runtime path for the completion report.

## Risk-scaled explore selection (agent-spawn runtimes)

After the structural pass, start the selected agents concurrently while the main session continues.
Each agent role is a
**self-contained prompt**; do not assume any harness-specific tool name inside it. Where a code
graph or LSP is available, instruct the agent to ground its claims in that data rather than guessing
from directory conventions.

Select explore roles after the structural pass from the unresolved questions with the highest
decision impact. Give one agent a self-contained question; combine roles when existing evidence
already answers it, and add an agent when ambiguity or blast radius would otherwise leave a claim
weakly grounded.

Useful role prompts include:

1. **Project structure** — map the real layout; report deviations from standard patterns.
2. **Entry points** — find main/index files, trace what they reach; report non-standard organization.
3. **Conventions** — find config files (`.eslintrc`, `pyproject.toml`, `.editorconfig`, …); report
   project-specific rules.
4. **Anti-patterns** — find `DO NOT` / `NEVER` / `ALWAYS` / `DEPRECATED` comments; list forbidden patterns.
5. **Build/CI** — find `.github/workflows`, `Makefile`, task runners; report non-standard patterns.
6. **Test patterns** — find test configs/structure and what the core modules cover; report unique conventions.

Increase coverage for independent unknowns, cross-package boundaries, unfamiliar languages or
generated code, security or migration-sensitive paths, and high-centrality modules. Do not add
agents merely because a repository has more files, lines, depth, or workspaces. Stop adding agents
when each high-risk conclusion has direct evidence or corroboration; on single-agent runtimes,
prioritize those same questions in sequential passes.

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
for the symbol/reference inventory, and mark centrality "unmeasured" in the CODE MAP so the
[completion report](../SKILL.md#completion-report) can state the limitation.

## Collect + merge

On agent-spawn runtimes, collect every background explore result after the main-session analysis
finishes. Then merge the bash structure, LSP/codegraph code map, existing `AGENTS.md` insights, and
explore findings into one project model. That merged model is the input to Phase 2.
