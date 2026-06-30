# Phase 0 — docs/ Ontology + ADR Graft

> **Graft (kept from craft-skills' original `init` v1.x).** This is the one layer carried onto the
> init-deep base engine: the `docs/` ontology scaffold + ADR index, non-destructive and idempotent.
> The original init's GitHub-governance / audit machinery is intentionally **not** ported.

Phase 0 lays the documentation rails. On the **bootstrap path** (fresh repo) this is the substantive
work; on the **cartography path** (mature repo) it mostly reports "already present" and skips. It
runs **before** Phases 1–4, and the `docs/` scaffold it seeds is **excluded** from the Phase 2
cartography scope (no self-mapping).

## Idempotency contract (applies to every step below)

- Every folder creation is gated on `[ ! -d "$dir" ]`.
- Every file seed is gated on `[ ! -f "$file" ]`.
- **Never overwrite an existing file** regardless of content — report it present, leave it untouched.
- Do not patch or merge into an existing file. If a file is present but looks incomplete, report it
  and stop — the operator decides. (The one exception is the Development Flow managed block in
  step 4, which is owned by init and may be replaced.)
- Re-running on an already-bootstrapped repo writes nothing and emits only status notices.

## 1. Detect existing state

Before writing anything, inspect the target repo for each managed item and collect the missing set.
All subsequent writes are gated on this set. Report each item present/missing first.

```bash
DOCS_DIRS=(
  docs/research
  docs/exec-plan/active
  docs/exec-plan/archive
  docs/decisions
  docs/rules
)

ANCHOR_FILES=(
  docs/decisions/README.md
  docs/architecture.md
)
# README.md at repo root is treated separately — see step 3.
```

Also detect whether the repo has an `AGENTS.md` operating guide (preferred managed-block target) or
another standardized agent instruction document.

## 2. Scaffold missing docs/ folders

For each directory in `DOCS_DIRS` that does not exist, create it and add a `.gitkeep`. Skip any that
already exist.

```bash
for dir in "${DOCS_DIRS[@]}"; do
  if [ ! -d "$dir" ]; then
    mkdir -p "$dir"
    touch "$dir/.gitkeep"
    echo "Created: $dir"
  else
    echo "Skipped (exists): $dir"
  fi
done
```

## 3. Seed anchor files

Seed each anchor only when absent.

### docs/decisions/README.md — owned by init, written verbatim when missing

```markdown
# ADR Index

Architecture Decision Records capture significant, expensive-to-reverse technical decisions.

## Lifecycle

\`\`\`
PROPOSED → ACCEPTED → (SUPERSEDED | DEPRECATED)
\`\`\`

- Never delete an ADR. Write a new ADR that references and supersedes the old one.
- One decision per ADR — non-overlapping, with no gaps across the set.
- Sequential numbering: ADR-001, ADR-002, …

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| (none yet) | | | |
```

### docs/architecture.md and README.md — owned by the `documents` skill

These templates live as standalone files inside the thick `documents` skill's sub-recipes. Do **not**
duplicate them here — read the template **files** directly (no prose-section extraction):

1. Locate the documents skill's root directory with Glob. Try each pattern; use the first that resolves:
   ```
   ~/.claude/skills/*/skills/documents/
   ~/.claude/plugins/*/*/skills/documents/
   ~/.claude/plugins/*/skills/documents/
   ~/.claude/plugins/cache/*/*/*/skills/documents/
   ```
2. For `docs/architecture.md` (only if absent): read **`templates/architecture.md`** from the located
   directory and write its contents verbatim.
3. For `README.md` at repo root (only if absent): read **`readme/template.md`** from the located
   directory and write its contents verbatim.
4. The ADR body template (when the operator later authors an actual decision) lives at
   **`adr/template.md`** in the same directory — point them there; init does not seed individual ADRs.

If the documents skill's directory cannot be located, write a one-line placeholder (`# Architecture`
or `# Project Name`) and record this warning:
`"documents templates not found — placeholder written; run documents to fill in templates."`

## 4. Development Flow managed block (convention-only)

Install or refresh **one** managed block in the target repo's `AGENTS.md` (or the repo's chosen
managed agent guide — record the path). Preserve all content outside the block. The block is owned by
init and may be **replaced** on re-run.

**Migration rule (init 2.0):** if a repo carries the **1.x** block — which claimed hard
git-guard/governance rails — **replace** it with the convention-only block below and **log the
replacement** in the final report (phase-4 observability). Do not leave stale hard-rail claims.

```markdown
<!-- BEGIN CRAFT-SKILLS INIT DEVELOPMENT FLOW -->
## Development Flow Recipe

Use an issue-driven loop for all repository work:

1. Open or select one GitHub issue describing the change.
2. Never commit directly on `main`. Use a worktree when you need isolation: `git wt <name>` creates (or reuses) a named worktree off the default branch. Reuse a small fixed pool (e.g. `lane-1`~`lane-3`) rather than making a new one per issue.
3. Plan first for non-trivial work: write the intended change, affected files, verification, and rollback note before editing.
4. Fan out into small PRs when a change spans unrelated domains, mixes assets with logic, or needs independent review lanes.
5. Attach review evidence to each PR: tests or checks run, screenshots/transcripts for user-facing behavior, and the issue/ADR links that justify the change.
6. Merge only after review. After merge, distill durable decisions into ADRs: PR note → ADR candidate → accepted ADR → superseding ADR when the decision changes.

Conventions agents must follow:

- Keep each change scoped to its issue. When work — planning, a requirements interview, or implementation — surfaces an out-of-scope problem (a new topic, unrelated bug, or follow-up idea beyond the current issue), open a new GitHub issue for it with one Type label instead of expanding the current change.
- Plan before editing non-trivial code.
- Prefer fan-out PRs over broad mixed-purpose PRs.
- Include review evidence before requesting/performing review.
- Do not merge before review.
- Distill lasting architecture or process decisions into ADRs.
<!-- END CRAFT-SKILLS INIT DEVELOPMENT FLOW -->
```

The block is an agent recipe, not an orchestrator — it tells agents how to run the loop. It must
**not** claim that init opens issues, creates worktrees, fans out PRs, performs reviews, merges, or
writes ADRs automatically. init 2.0 ships **no** hard-rail enforcement of its own; git-guard is the
`worktree` skill's concern and self-installs there on first use (see the diagnostic notice in
SKILL.md).

## Phase 0 verification

- [ ] `docs/research/`, `docs/exec-plan/active/`, `docs/exec-plan/archive/`, `docs/decisions/`,
      `docs/rules/` all exist.
- [ ] `docs/decisions/README.md` present with the ADR index template.
- [ ] `docs/architecture.md` present (seeded from documents skill or placeholder + warning).
- [ ] `README.md` present at repo root (pre-existing or seeded; warning if documents skill not found).
- [ ] Development Flow managed block present in `AGENTS.md` / chosen guide; surrounding content
      preserved; any 1.x block replaced-and-logged.
- [ ] No existing file overwritten — confirmed via the "Skipped (exists)" notices.
