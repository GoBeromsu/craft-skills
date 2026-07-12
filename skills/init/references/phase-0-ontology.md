# Phase 0 — docs/ Ontology Scaffold

> **Graft.** This is the one layer carried onto the cartography base engine: the craft-owned
> `docs/` folder/file scaffold, non-destructive and idempotent. GitHub-governance / audit machinery
> and ADR authoring requirements are intentionally **not** part of this graft.

Phase 0 lays the documentation scaffold. On the **bootstrap path** (fresh repo) this is the
substantive work; on the **cartography path** (mature repo) it mostly reports "already present" and
skips. It runs **before** Phases 1–4, and the `docs/` scaffold it seeds is **excluded** from the
Phase 2 cartography scope (no self-mapping).

## Table of Contents

- [Idempotency contract](#idempotency-contract-applies-to-every-step-below)
- [1. Detect existing state](#1-detect-existing-state)
- [2. Scaffold missing docs/ folders](#2-scaffold-missing-docs-folders)
- [3. Seed anchor files](#3-seed-anchor-files)
- [4. Development Flow managed block](#4-development-flow-managed-block-convention-only)
- [Phase 0 verification](#phase-0-verification)

---

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

### docs/decisions/README.md — explicit-only index, written verbatim when missing

```markdown
# Decision Index

This directory is the destination for decision records only when the user explicitly asks for ADRs
or durable decision documentation. `init` creates no ADR files and requires no ADR lifecycle.

## Explicit Records

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| (none yet) | | | |
```

### docs/architecture.md — scaffold anchor, written verbatim when missing

```markdown
# Architecture

Project architecture notes live here when explicitly authored.
```

Do not create or modify root `README.md`. Do not create ADR files, ADR templates, ADR lifecycle
rules, or decision-record prose. If the operator explicitly asks to author an ADR or a substantive
architecture document, hand off to the `document` skill and use these paths only as destinations.

## 4. Development Flow managed block (convention-only)

Install or refresh **one** managed block in the target repo's `AGENTS.md` (or the repo's chosen
managed agent guide — record the path). Preserve all content outside the block. The block is owned by
init and may be **replaced** on re-run.

**Migration rule:** if a repo carries a legacy block that claims hard git-guard/governance rails,
**replace** it with the convention-only block below and record the managed-block action in the
[completion report](../SKILL.md#completion-report). Do not leave stale hard-rail claims.

```markdown
<!-- BEGIN CRAFT-SKILLS INIT DEVELOPMENT FLOW -->
## Development Flow Recipe

Use an issue-driven loop for all repository work:

1. Open or select one GitHub issue describing the change.
2. Never commit directly on `main`. Use a worktree when you need isolation: `git wt <name>` creates (or reuses) a named worktree off the default branch. Reuse a small fixed pool (e.g. `lane-1`~`lane-3`) rather than making a new one per issue.
3. Plan first for non-trivial work: write the intended change, affected files, verification, and rollback note before editing.
4. Fan out into small PRs when a change spans unrelated domains, mixes assets with logic, or needs independent review lanes.
5. Attach review evidence to each PR: tests or checks run, screenshots/transcripts for user-facing behavior, and the issue or planning links that justify the change.
6. Merge only after review. If the user explicitly asks to record a durable decision, hand off to the `document` skill and use `docs/decisions/` as the destination.

Conventions agents must follow:

- Keep each change scoped to its issue. When work — planning, a requirements interview, or implementation — surfaces an out-of-scope problem (a new topic, unrelated bug, or follow-up idea beyond the current issue), open a new GitHub issue for it with one Type label instead of expanding the current change.
- Plan before editing non-trivial code.
- Prefer fan-out PRs over broad mixed-purpose PRs.
- Include review evidence before requesting/performing review.
- Do not merge before review.
- Do not create or require ADRs unless the user explicitly asks for ADRs.
<!-- END CRAFT-SKILLS INIT DEVELOPMENT FLOW -->
```

The block is an agent recipe, not an orchestrator — it tells agents how to run the loop. It must
**not** claim that init opens issues, creates worktrees, fans out PRs, performs reviews, merges, or
writes ADRs automatically or requires ADRs as a default artifact. init ships **no** hard-rail
enforcement of its own; git-guard is the `git` skill's concern and self-installs there on first use
(see the diagnostic notice in SKILL.md).

## Phase 0 verification

- [ ] `docs/research/`, `docs/exec-plan/active/`, `docs/exec-plan/archive/`, `docs/decisions/`,
      `docs/rules/` all exist.
- [ ] `docs/decisions/README.md` present as an explicit-only decision index.
- [ ] `docs/architecture.md` present as a scaffold anchor.
- [ ] Development Flow managed block present in `AGENTS.md` / chosen guide; surrounding content
      preserved; any legacy hard-rail block replaced-and-logged.
- [ ] No existing file overwritten — confirmed via the "Skipped (exists)" notices.
