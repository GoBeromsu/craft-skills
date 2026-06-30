# Phase 3 — Generate AGENTS.md

> **Ported from init-deep §"Phase 3: Generate AGENTS.md".**
> Port-completeness checklist (all must remain present):
> - [x] **Existence rule** — `Edit` an existing file, `Write` a new one; never `Write` over an existing file.
> - [x] **Root template** with the full section set (OVERVIEW / STRUCTURE / WHERE TO LOOK / CODE
>       MAP / CONVENTIONS / ANTI-PATTERNS / UNIQUE STYLES / COMMANDS / NOTES).
> - [x] **Provenance stamp** format (`Generated` / `Commit` / `Branch`).
> - [x] Subdir template + the parallel/sequential generation rule with the 30–80 line budget.
> - [x] Root quality gate (50–150 lines, no generic advice).
> - [x] **GRAFT addition:** the `## DOCS & DECISIONS` section cross-linking the docs/ ontology + ADR index.

Phase 3 writes the files. Root first (full treatment), then the scored subdirs.

## File-writing rule (critical)

If `AGENTS.md` already exists at the target path → use **`Edit`**. If it does not exist → use
**`Write`**. **Never** `Write` over an existing file; always confirm existence first via the Phase 1
discovery results or a `Read`. On the agent-spawn path subdirs are generated in parallel; on the
single-agent path they are generated sequentially — the existence rule is identical either way.

## Root AGENTS.md (full treatment)

Fill the provenance stamp from git (`{TIMESTAMP}` = ISO date, `{SHORT_SHA}` = `git rev-parse
--short HEAD`, `{BRANCH}` = `git rev-parse --abbrev-ref HEAD`). If the repo has no commits yet
(fresh bootstrap), write `uncommitted` for SHA/branch rather than failing.

```markdown
# PROJECT KNOWLEDGE BASE

**Generated:** {TIMESTAMP}
**Commit:** {SHORT_SHA}
**Branch:** {BRANCH}

## OVERVIEW
{1-2 sentences: what + core stack}

## STRUCTURE
\`\`\`
{root}/
├── {dir}/    # {non-obvious purpose only}
└── {entry}
\`\`\`

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|

## CODE MAP
{From LSP/codegraph — skip only if neither exists or project <10 files. If centrality was
unmeasured, say so here.}

| Symbol | Type | Location | Refs | Role |
|--------|------|----------|------|------|

## CONVENTIONS
{ONLY deviations from standard}

## ANTI-PATTERNS (THIS PROJECT)
{Explicitly forbidden here}

## UNIQUE STYLES
{Project-specific}

## COMMANDS
\`\`\`bash
{dev/test/build}
\`\`\`

## DOCS & DECISIONS
{GRAFT — only when Phase 0 seeded or found a docs/ ontology in this repo. See format below.}

## NOTES
{Gotchas}
```

**Root quality gate:** 50–150 lines, no generic advice, no obvious info.

### The `## DOCS & DECISIONS` section (graft — links code map ↔ ontology)

This is the one additive section that bonds the ported cartography engine to the kept docs/ ontology
graft (Phase 0). Emit it in the **root** AGENTS.md only, and only when a `docs/` ontology exists in
the repo (Phase 0 seeded it, or it was already present). Keep it to links — never restate ADR or
architecture bodies:

```markdown
## DOCS & DECISIONS

- Architecture map: [`docs/architecture.md`](docs/architecture.md)
- Decisions (ADRs): [`docs/decisions/`](docs/decisions/) — index in [`docs/decisions/README.md`](docs/decisions/README.md)
- Active plans: [`docs/exec-plan/active/`](docs/exec-plan/active/) · Research: [`docs/research/`](docs/research/) · Rules: [`docs/rules/`](docs/rules/)
```

If no `docs/` ontology exists (cartography-only run on a repo that never bootstrapped), omit the
section entirely and note its absence in the report.

## Subdirectory AGENTS.md

For every location in `AGENTS_LOCATIONS` except root, generate a tight child file. On agent-spawn
runtimes launch these as parallel writing tasks; on single-agent runtimes write them one at a time.
Each child uses a **self-contained** generation brief:

- **30–80 lines max.**
- **NEVER repeat parent content** (dedup-vs-parent is enforced again in phase-4).
- Sections: OVERVIEW (1 line), STRUCTURE (only if >5 subdirs), WHERE TO LOOK, CONVENTIONS (only if
  different from parent), ANTI-PATTERNS.

Wait for all child writes to complete before moving to Phase 4.
