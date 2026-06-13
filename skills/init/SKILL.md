---
name: init
description: '"init this repo", "set up the docs structure", "bootstrap craft conventions", "/init" — scaffold the docs/ ontology folders and wire git-hook enforcement into a target project in one idempotent step.'
version: 1.0.0
allowed-tools: [Bash, Read, Write, Edit, Grep, Glob]
compatibility: claude-code, codex
---

# init

Scaffold a project's docs/ folder ontology and wire git-hook enforcement in one explicit,
idempotent step. Run once after cloning; re-running a fully bootstrapped repo produces only
skip notices with no side effects.

**Scope boundary — three skills, three responsibilities:**

| Responsibility | Owner |
|---|---|
| Scaffold `docs/` folders and seed anchor files | **init** (this skill) |
| Author and maintain content inside `docs/` | `documents` skill |
| Install and manage git-hook enforcement logic | `worktree` skill's installer — init delegates to it |
| Scaffold consumer plugin manifests (`.claude-plugin`, etc.) | **out of scope for init** |

## Core Process

### 1. Detect existing state

Before writing anything, inspect the target repo for each item init manages. Collect the missing
set — all writes in subsequent steps are gated on this set.

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
# README.md at repo root is treated separately — see Step 3.
```

Report each item's status (present / missing) before taking any action.

### 2. Scaffold missing docs/ folders

For each directory in `DOCS_DIRS` that does not exist, create it and add a `.gitkeep` so git
tracks the empty folder. Skip any directory that already exists.

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

### 3. Seed anchor files

Seed each anchor file only when it is absent. Never overwrite an existing file regardless of its
content — report it as present and leave it untouched.

#### docs/decisions/README.md

Init owns this template. Write it verbatim when the file is missing:

```markdown
# ADR Index

Architecture Decision Records capture significant, expensive-to-reverse technical decisions.

## Lifecycle

```
PROPOSED → ACCEPTED → (SUPERSEDED | DEPRECATED)
```

- Never delete an ADR. Write a new ADR that references and supersedes the old one.
- One decision per ADR — non-overlapping, with no gaps across the set.
- Sequential numbering: ADR-001, ADR-002, …

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| (none yet) | | | |
```

#### docs/architecture.md and README.md

These templates are owned by the `documents` skill and live as standalone files in its
`templates/` directory. Do not duplicate them here — read the template **files** directly
(no prose-section extraction):

1. Locate the documents skill's `templates/` directory using Glob. Try each pattern and use
   the first that resolves:
   ```
   ~/.claude/skills/*/skills/documents/templates/
   ~/.claude/plugins/*/*/skills/documents/templates/
   ~/.claude/plugins/*/skills/documents/templates/
   ```
2. For `docs/architecture.md` (only if absent): read `templates/architecture.md` from the
   located directory and write its contents verbatim.
3. For `README.md` at repo root (only if absent): read `templates/readme.md` from the located
   directory and write its contents verbatim.

If the documents skill's `templates/` directory cannot be located, write a one-line placeholder
(`# Architecture` or `# Project Name`) and record this warning:
`"documents templates not found — placeholder written; run documents to fill in templates."`

### 4. Wire enforcement rails

After the docs/ scaffold is complete, invoke each relevant skill's first-run installer. Check
for each installer before invoking it; skip with a recorded notice if the installer is not
present. Do not fail hard on a missing optional installer — record the skip and continue.

#### Worktree / git-guard installer

The worktree skill's git-guard installer wires `core.hooksPath` and registers the `git wt`
alias. Detect and invoke:

```bash
GUARD_SCRIPT="scripts/git-guard/setup-hooks.sh"
if [ -f "$GUARD_SCRIPT" ]; then
  bash "$GUARD_SCRIPT"
  echo "Wired: git-guard (core.hooksPath set)"
else
  echo "Notice: $GUARD_SCRIPT not found — git-guard wiring skipped."
  echo "Add the worktree skill's git-guard scripts and re-run init, or wire manually."
fi
```

For additional skill installers: follow the same detect-then-invoke pattern. Each skill
documents its own first-run installer path and invocation command.

## Idempotency Rules

- Every folder creation is gated on `[ ! -d "$dir" ]`.
- Every file seed is gated on `[ ! -f "$file" ]`.
- Re-running init on an already-bootstrapped repo writes nothing and produces only status
  notices.
- Do not patch or merge into an existing file. If a file is present but appears incomplete,
  report it and stop — the operator decides what to do next.

## Verification

After running init, confirm all of the following:

- [ ] `docs/research/`, `docs/exec-plan/active/`, `docs/exec-plan/archive/`,
  `docs/decisions/`, `docs/rules/` all exist
- [ ] `docs/decisions/README.md` present with the ADR index template
- [ ] `docs/architecture.md` present (seeded from documents skill or placeholder with warning)
- [ ] `README.md` present at repo root (pre-existing or seeded with warning if documents
  skill was not found)
- [ ] git-guard wired: `git config core.hooksPath` returns the hooks directory,
  or a skip notice was recorded
- [ ] No existing file was overwritten — confirmed by reviewing the "Skipped" log lines

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just create the folders by hand — no need for init." | Manual setup diverges across repos and is not auditable. Init is the single explicit, idempotent entry point for scaffold consistency. |
| "README.md exists but looks incomplete — init should patch it." | Init does not patch existing files. The `documents` skill authors and updates content; init only seeds when a file is absent. |
| "I'll also scaffold the .claude-plugin here." | Plugin manifests are consumer-side configuration, not docs/ rails. Init's scope ends at docs/ and git-hook wiring. |
| "The worktree installer failed — I'll skip it silently." | Record every skip explicitly. A missing enforcement rail is a gap the operator must close before conventions are enforced. |
| "I'll embed the architecture.md and README.md templates inline here." | Those templates are owned by the `documents` skill. Duplicating them creates two divergent sources of truth — read them from the documents skill at seed time. |

## Red Flags

- Overwriting an existing file (docs/ or README.md) with a template
- Scaffolding `.claude-plugin` or any consumer plugin manifest (out of scope)
- Embedding the architecture.md or README.md template text in this skill's body
  (templates are owned by the `documents` skill)
- Invoking a skill installer that is absent without recording a skip notice
- Not verifying `git config core.hooksPath` after the git-guard installer runs
- Running init without first checking which items already exist (Step 1 is not optional)
- Treating a skip notice as an error — skips are expected on re-runs
