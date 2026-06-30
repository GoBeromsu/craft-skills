---
name: init
description: '"init this repo", "set up the docs structure", "bootstrap craft conventions", "/init" — scaffold the docs/ ontology folders and wire git-hook enforcement into a target project in one idempotent step.'
version: 1.1.0
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
| Resolve GitHub governance config and install/verify issue label taxonomy | **init** scripts under `skills/init/scripts/` |
| Install and verify GitHub governance rails (labels, issue template, auto-label workflow, PR check workflow) | **init** owns installer/verifier wiring; scripts consume the shared resolved config |

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

Report each item's status (present / missing) before taking any action. Also detect whether the target repo has an `AGENTS.md` operating guide (preferred recipe target) or another managed agent instruction document that the operator has standardized on.

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

These templates are owned by the `documents` skill and live as standalone files: the
architecture template under its `templates/` directory, and the README template inside the
`readme/` sub-recipe. Do not duplicate them here — read the template **files** directly
(no prose-section extraction):

1. Locate the documents skill's root directory using Glob. Try each pattern and use
   the first that resolves:
   ```
   ~/.claude/skills/*/skills/documents/
   ~/.claude/plugins/*/*/skills/documents/
   ~/.claude/plugins/*/skills/documents/
   ```
2. For `docs/architecture.md` (only if absent): read `templates/architecture.md` from the
   located directory and write its contents verbatim.
3. For `README.md` at repo root (only if absent): read `readme/template.md` from the located
   directory and write its contents verbatim.

If the documents skill's directory cannot be located, write a one-line placeholder
(`# Architecture` or `# Project Name`) and record this warning:
`"documents templates not found — placeholder written; run documents to fill in templates."`

#### Development Flow recipe managed block

Install or refresh one managed block in the target repo's `AGENTS.md` when that file exists. If the repo uses another agent instruction document as its managed operating guide, use that document instead and record the path. Preserve all existing content outside the managed block. The block is owned by init and may be replaced on re-run; do not rewrite unrelated prose.

```markdown
<!-- BEGIN CRAFT-SKILLS INIT DEVELOPMENT FLOW -->
## Development Flow Recipe

Use an issue-driven loop for all repository work:

1. Open or select one GitHub issue with exactly one Type label (`feat`, `fix`, `chore`, `docs`, `refactor`, or `test`, unless this repo overrides the taxonomy in `.github/issue-driven-governance.yml`).
2. Create a dedicated worktree with `git wt <issue-number>` and do all implementation there. Never commit directly on `main`.
3. Plan first for non-trivial work: write the intended change, affected files, verification, and rollback note before editing.
4. Fan out into small PRs when a change spans unrelated domains, exceeds the logic-churn threshold, mixes assets with logic, or needs independent review lanes.
5. Attach review evidence to each PR: tests or checks run, screenshots/transcripts for user-facing behavior, and the issue/ADR links that justify the change.
6. Merge only after review. After merge, distill durable decisions into ADRs: PR note → ADR candidate → accepted ADR → superseding ADR when the decision changes.

Hard rails fail with a non-zero exit code when enforcement is installed:

- Direct commits to `main` are blocked by git-guard.
- PR logic churn above the resolved threshold fails unless the explicit size override label is reviewer-approved.
- Asset-only or generated-only changes must stay out of logic churn and use the resolved non-logic path rules.
- PR base branches must match the resolved allowed base list.
- Every issue must carry exactly one Type label; the auto-label workflow refuses unknown or missing Type selections.

Conventions agents must follow even when a hard rail cannot see them:

- Plan before editing non-trivial code.
- Prefer fan-out PRs over broad mixed-purpose PRs.
- Include review evidence before requesting/performing review.
- Do not merge before review.
- Distill lasting architecture or process decisions into ADRs.
<!-- END CRAFT-SKILLS INIT DEVELOPMENT FLOW -->
```

The managed block is an agent recipe, not an orchestrator. It tells agents how to run the loop; it must not claim that init opens issues, creates worktrees, fans out PRs, performs reviews, merges, or writes ADRs automatically.

### 4. Wire enforcement rails

After the docs/ scaffold is complete, invoke each relevant skill's first-run installer. Check
for each installer before invoking it; skip with a recorded notice if the installer is not
present. Do not fail hard on a missing optional installer — record the skip and continue.

#### Worktree / git-guard installer

git-guard ships **by default** with init. Init does not wait for the guard scripts to already
exist in the target repo — it invokes the worktree skill's bundled `install.sh`, which copies the
guard scripts into `scripts/git-guard/`, copies the shipped hooks into `.githooks/`, and wires
`core.hooksPath` + the `git wt` alias. The installer is idempotent and never clobbers existing
files, so re-running is safe.

Locate the worktree skill's `install.sh` using Glob (same lookup style as the documents
templates). Try each pattern and use the first that resolves:

```
~/.claude/skills/*/skills/worktree/scripts/install.sh
~/.claude/plugins/*/*/skills/worktree/scripts/install.sh
~/.claude/plugins/*/skills/worktree/scripts/install.sh
~/.claude/plugins/cache/*/*/*/skills/worktree/scripts/install.sh
```

Then invoke it from the target repo root:

```bash
WT_INSTALL="<path resolved above>"
if [ -f "$WT_INSTALL" ]; then
  sh "$WT_INSTALL"
  echo "Wired: git-guard (scripts + hooks scaffolded, core.hooksPath set)"
else
  echo "Notice: worktree install.sh not found — git-guard wiring skipped."
  echo "Install/enable the worktree skill and re-run init, or wire manually."
fi
```

Always confirm `git config core.hooksPath` returns `.githooks` afterward.

#### GitHub governance rails

Init owns GitHub governance rails for issue labels, the issue Type template, fail-closed auto-labeling, and PR size/base checks. These scripts consume the single resolved config from `skills/init/scripts/governance_config.py` and must be run from the target repository root.

Preview the exact mutation plan before applying anything:

```bash
python ${CRAFT_SKILLS_REPO_PATH}/skills/init/scripts/install_github_governance.py --repo-root . --dry-run
```

Apply the installer only after reviewing the change plan:

```bash
python ${CRAFT_SKILLS_REPO_PATH}/skills/init/scripts/install_github_governance.py --repo-root .
```

Verify without mutation:

```bash
python ${CRAFT_SKILLS_REPO_PATH}/skills/init/scripts/verify_github_governance.py --repo-root . --check
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
- [ ] git-guard scaffolded by default: `scripts/git-guard/` and `.githooks/pre-commit` /
  `.githooks/pre-push` exist, and `git config core.hooksPath` returns `.githooks`
  (or a skip notice was recorded because the worktree installer could not be located)
- [ ] GitHub governance install preview was reviewed with `install_github_governance.py --dry-run`
- [ ] GitHub governance rails were applied with `install_github_governance.py` or an explicit skip was recorded
- [ ] GitHub governance verifier passed with `verify_github_governance.py --check`
- [ ] Development Flow recipe managed block is present in `AGENTS.md` or the chosen managed agent guide, with existing content preserved
- [ ] No existing file was overwritten — confirmed by reviewing the "Skipped" log lines

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just create the folders by hand — no need for init." | Manual setup diverges across repos and is not auditable. Init is the single explicit, idempotent entry point for scaffold consistency. |
| "README.md exists but looks incomplete — init should patch it." | Init does not patch existing files. The `documents` skill authors and updates content; init only seeds when a file is absent. |
| "I'll also scaffold the .claude-plugin here." | Plugin manifests are consumer-side configuration, not docs/ rails. Init's scope ends at docs/ and git-hook wiring. |
| "git-guard only installs if its scripts are already in the repo." | No. init scaffolds git-guard **by default** via the worktree skill's `install.sh` — it copies the scripts and hooks in, then wires them. A fresh clone gets enforcement without a manual pre-step. |
| "The worktree installer failed — I'll skip it silently." | Record every skip explicitly. A missing enforcement rail is a gap the operator must close before conventions are enforced. |
| "The GitHub governance installer is optional docs polish." | It is an init-owned enforcement rail. Preview with `--dry-run`, apply intentionally, then verify with `--check`. |
| "The Development Flow block can be pasted wherever." | Keep it in one managed block, preserve surrounding content, and replace only the block on re-run. |
| "I'll embed the architecture.md and README.md templates inline here." | Those templates are owned by the `documents` skill. Duplicating them creates two divergent sources of truth — read them from the documents skill at seed time. |

## Red Flags

- Overwriting an existing file (docs/ or README.md) with a template
- Scaffolding `.claude-plugin` or any consumer plugin manifest (out of scope)
- Embedding the architecture.md or README.md template text in this skill's body
  (templates are owned by the `documents` skill)
- Invoking a skill installer that is absent without recording a skip notice
- Not verifying `git config core.hooksPath` after the git-guard installer runs
- Running GitHub governance installation without first reviewing `--dry-run` output
- Treating `verify_github_governance.py --check` as mutating or optional after install
- Duplicating the Development Flow recipe outside the managed block or deleting existing target guide content
- Running init without first checking which items already exist (Step 1 is not optional)
- Treating a skip notice as an error — skips are expected on re-runs
