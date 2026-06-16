---
name: skillify
description: '"make a skill", "스킬 만들자", "skillify this workflow", "turn this into a skill", "update this skill", "fix this skill", "edit this skill", "move this skill", "/skillify"'
version: 3.2.0
allowed-tools: [Bash, Read, Edit, Write, Grep, Glob]
compatibility: claude-code, codex
---

# skillify

The **craft-skills promotion gate**: turn a workflow into a trusted, resolvable, well-formed skill package. The canonical package schema is `references/schemas.md`; every skill authored here conforms to it.

## Overview

A craft-skills skill package is `SKILL.md` + `CHANGELOG.md`, plus optional `references/`, `scripts/`, `tests/`, `evals/`, `agents/` (role-prompt charters — writer.md, reviewer.md, grader.md — for skills that spawn sub-agents; `agents/` is **optional for craft-skills skills in general**, but **mandatory for skillify itself**: skillify spawns these three charters by name from `references/pipeline.md`, so they are required for this package and are not a global requirement imposed on every other skill), and a gitignored `.env` (commit only `.env.example`). skillify owns the full lifecycle — create, update, move/rename, deprecate — and the two-layer gate that makes a package trustworthy.

## When to Use

- "make a skill", "스킬 만들자", "skillify this workflow", "turn this into a skill", "/skillify"
- "update this skill", "fix this skill", "edit this skill", "move this skill"
- Turning a repeated workflow into a resolvable, tested skill package
- Promoting a bundled/local skill copy into the repo's single source of truth
- Reviewing a session and encoding a durable workflow correction into the governing skill

**NOT for:** prompts under `70. Collections/02 Prompt/` · templates under `90. Settings/02 Templates/` · one-off scripts with no reuse intent.

## Core Process

### Stage 0: Admission — does this candidate belong here?

Run **before** Harvest. Admission is a scope gate, not a quality gate: it answers whether a candidate
workflow belongs in craft-skills at all, so a project-local, upstream-owned, or non-portable
candidate is rejected before any authoring cost is spent. It is distinct from Layer 1 (format) and
Layer 2 (trust) and runs upstream of both.

Spawn the reviewer agent as a **fresh subagent in a clean context** (`§ Admission Task` in
`references/pipeline.md`), handing it `references/checklist.md` + the candidate + the tier
definitions. The judgment is a **single clean pass** — never the Layer-2 consensus loop; consensus is
reserved for the trust layer. The reviewer is not given the author's promotion rationale: scope is
judged on the candidate's own evidence.

The reviewer applies the five drop-questions (Q1 Reusability, Q2 Ownership, Q3 Convention-not-artifact,
Q4 Portability, Q5 Boundary-purity), each defaulting to ✗, and writes an **admission receipt** to
`skills/skillify/evals/admission-<candidate-slug>-<date>.md` — the **skillify package owns the receipt**,
because a rejected candidate may have no skill directory of its own yet — recording per-question ✓/✗ +
one-line evidence + verdict + routed destination.

```
ADMIT  (all five ✓)  →  proceed to Harvest
REJECT (any ✗)       →  record routed destination (project-local / using-our-stack reference /
                        split-then-resubmit); STOP. The author has no veto — disagreement
                        escalates to the human, never back to the author for self-approval.
```

A candidate already carrying a REJECT receipt for an unchanged reason is not re-judged — point at the
existing receipt. Re-admission requires a material change recorded as a fresh receipt.

### The 3 stages: Harvest → Prove → Cement

```
Harvest 수확  →  Prove 입증  →  Cement 결정화
```

- **Harvest:** Capture the raw workflow — repeated patterns, runtime learnings, operational edges — into a `SKILL.md` draft via the writer agent. Do not optimize yet.
- **Prove:** Validate behavior empirically across ≥2–3 model families before writing tests. Tests lock in behavior; tests over unproven behavior lock in mediocrity.
- **Cement:** Lock proven behavior with tests, routing registration, and consensus eval receipts.

### Detect mode

```bash
SKILL_DIR="skills/<skill-name>"          # flat (default), or skills/<area>/<skill-name>
test -f "$SKILL_DIR/SKILL.md" && mode=update || mode=create
```

- **Create:** clear **Stage 0: Admission** first (a new candidate has no prior receipt), then scaffold the package, author via the writer agent, register routing, seed `CHANGELOG.md`, validate (Layer 1 → Layer 2), PR.
- **Update:** patch `SKILL.md`/references, bump `version`, append a `CHANGELOG.md` bullet, validate, PR.
- **Move/rename:** move the whole directory and update every routing surface — see `references/topology-and-routing.md`.
- **Deprecate/delete:** mark deprecation in the **body**, never in frontmatter — the 5-key frontmatter is fixed and admits no `status` key. Add a `## Deprecated` section at the top of `SKILL.md` pointing to the replacement skill, and annotate or remove the routing entry; bump **MAJOR** (a trigger phrase is leaving the contract); append a `CHANGELOG.md` bullet; PR. Prefer a deprecated stub over physical deletion whenever another skill takes over. Delete the directory only after confirming no routing entry and no scheduled job still references the skill.

**Stage 0 gates `create` only.** A new candidate must pass admission before any authoring. `update`, `move/rename`, and `deprecate` operate on a skill already admitted — they reference the existing admission receipt rather than re-run the gate. Re-admission is required only when an update **materially changes scope** (a new trigger phrase, a broadened domain, or a merge with another skill alters what was originally admitted); that re-judgment is recorded as a fresh receipt.

Before any change, start clean: run `git status` first and stash or set aside any unrelated uncommitted work — never discard user-owned changes to reach a clean tree — then `git fetch origin --prune`, switch to `main`, `git pull --ff-only origin main`, and branch. Do not stack edits on a dirty branch.

### Abort / roll back an in-flight promotion

When a promotion is abandoned — Layer 2 never converges after the max rounds, the workflow proves too narrow, or the user cancels — unwind it cleanly instead of leaving half-registered state. Abort is a **user-confirmed** decision: confirm the abandonment before any destructive step (branch delete, PR close); never unilaterally discard work.

- **No PR yet:** once the user confirms, delete the working branch (`git branch -D <branch>`); the scaffolded directory dies with it.
- **PR opened:** close the PR and delete the branch — nothing merges to `main`.
- **Routing already touched:** remove any routing entry added for the abandoned skill so no load key (the routing identifier — the `name` field — by which a skill is discovered and resolved) points at a directory that will not exist.
- **Scaffold to keep for later:** leave it **unregistered** — no routing entry, kept on its branch — rather than a registered-but-broken skill or a sixth frontmatter key. An unrouted directory is never loaded.

An abandoned promotion records nothing in `main` — the branch is the only artifact, and it is gone.

### Author via the Writer → Reviewer pipeline

The writer agent (`agents/writer.md`) drafts the package against `references/schemas.md`. The reviewer agent (`agents/reviewer.md`) is a checklist-driven impartial judge with two modes selected by which rubric it is handed and when it is invoked: in **admission** mode (Stage 0, fed `references/checklist.md`) it judges scope; in **quality** mode (post-author, the anatomy axes) it audits judgment quality — trigger-fit, anatomy intent, compliance with the recipe-completeness law (present-tense imperative, no history/attribution/jargon), and routing coherence — in a **separate lane** from the writer. The grader agent (`agents/grader.md`) grades tier-gate assertions against actual run outputs. Format compliance is a **script gate, not a prompt** — see Layer 1 below.

**Lane rule:** author lane and eval lane never run in the same active context. Never self-approve.

### MECE structure

A skill's internal parts are **MECE** — Mutually Exclusive, Collectively Exhaustive. This is the umbrella that the recipe-completeness law and lane separation both serve.

- **Mutually Exclusive:** every part owns exactly one responsibility, with no overlap. Format is a Layer-1 script, never the reviewer's job; history lives in `CHANGELOG.md`, never `SKILL.md`; provenance is a credit, not a recipe step; the writer drafts, the reviewer judges, the grader scores — never the same lane. Two parts doing the same job is a defect; collapse or re-split until each concern has exactly one owner.
- **Collectively Exhaustive:** the parts together cover the whole recipe with no gaps — this is the recipe-completeness law below.

When a section overlaps another, or a responsibility has no clear home, the package is not MECE — split or merge until the set is both non-overlapping and complete.

### Recipe-completeness law

A skill is a **complete recipe**: the body is present-tense imperative operating instructions only. Never narrate the skill's own evolution, and never name an external person, tool, or repo as the source of a rule — both history and provenance belong in `CHANGELOG.md`, not the recipe.

Apply three contamination gates to every body sentence you write:
- **History gate:** "Could a reader who never knew this skill's past understand and execute this sentence as-is?" Temporal markers ("previously", "used to", "이전에는", "we changed") fail.
- **Attribution gate:** "Does this sentence name a person, tool, or repo as the origin of a rule?" ("inspired by X", "adopted from `<tool>`", "`<repo>`-style") fails.
- **Jargon gate:** "Can a reader who does not share the author's context execute this sentence without guessing what the term means?" An undefined term of art or an abstract/cultural blurb standing in for a concrete technical concept fails.

When a sentence fails either gate, relocate it via the three-way split — corrected behavior → an imperative step in Core Process; the failure it prevents → a `## Common Rationalizations` row or `## Red Flags` bullet; the event, date, or credit → `CHANGELOG.md`. The full distillation procedure is owned by `references/schemas.md §1`. We dissolve borrowed philosophy into the recipe; we do not sign it.

### Run the gate

#### Layer 1 — Deterministic format (first verification action)

Layer 1 is the first VERIFICATION action: it runs after the operational branch/commit/PR setup and before Layer 2. It is CI-enforceable, deterministic, and has no judgment component.

```bash
# Package format: 5-key frontmatter, name==dir, semver version, CHANGELOG presence, no ## Change Log.
python3 skills/skillify/scripts/validate-skill-format.py --diff-base origin/main...HEAD

# Secret / real-path leakage on newly changed lines.
python3 skills/skillify/scripts/validate-runtime-hygiene.py --diff-base origin/main...HEAD
```

Both run in CI in `--diff-base` mode: only skills changed in the PR are enforced. Run `validate-skill-format.py --advisory` for a full non-blocking inventory of legacy gaps. **CI runs Layer 1 only — never Layer 2.**

#### Layer 2 — Multi-model consensus convergence loop (local, orchestrator-independent)

After Layer 1 passes, run `scripts/consensus.py`. This script is **vendored and orchestrator-independent** — it calls the `codex`, `gemini`, and `claude` CLIs directly via subprocess, with no dependency on any agent-orchestration runtime.

**Convergence loop:**

```
1. consensus.py fans out the skill to codex, gemini, claude (role-scoped prompts)
2. Each returns APPROVE / REVISE + findings
3. All APPROVE?  ── YES ──▶  CONVERGED → write evals/consensus-<skill>-<date>.md → gate passes
        │
       NO
        ▼
4. Models REBUT each other via a SEPARATE second invocation:
   ```bash
   python3 skills/skillify/scripts/consensus.py --skill <dir> --round 2 --prior evals/consensus-<skill>-<date>.md
   ```
   The rebuttal round is a fresh invocation — consensus.py does not auto-rebut within a single run; on divergence it writes a receipt and stops for human review.
5. Unresolved conflict → SUBMIT disagreement to the user
6. User responds → revise the skill → back to step 1
   (After 3 rebuttal rounds with no convergence, STOP looping and escalate to the
    user for an explicit override decision — see "User override" below.)
        └────────── loop until all converge, or user overrides after round 3 ────────┘
```

The final call on each surfaced conflict is the **user's** (human-in-the-loop). The loop does not auto-merge on disagreement, and it does not loop unbounded — 3 rounds without convergence is the escalation trigger, not a hard failure.

**Invocation:**

```bash
python3 skills/skillify/scripts/consensus.py \
  --skill skills/<skill-name> \
  [--round N] \
  [--prior skills/<skill-name>/evals/consensus-<skill>-<prev-date>.md] \
  [--providers codex,gemini,claude] \
  [--diff-base origin/main...HEAD]
```

**Diff-scoped review (`--diff-base`, recommended for updates).** Without it the panel reviews the *whole* `SKILL.md` every round, so a small sound edit keeps getting blocked by the file's pre-existing prose — the panel flip-flops and never converges. With `--diff-base` set (mirroring Layer-1's `origin/main...HEAD` contract) the panel judges **only the lines this change adds or modifies**; the full file still ships as context. Use it for **update** mode (the change must be committed first, exactly as Layer-1 requires). Omit it for **create** mode, where every line is new and whole-file review is correct. An empty or unresolvable diff falls back to whole-file review with a warning.

**Artifacts:**
- `skills/<skill>/evals/<provider>-r<N>.md` — per-model verdict for round N
- `skills/<skill>/evals/consensus-<skill>-<date>.md` — synthesized receipt; `scope:` line records `diff (<base>)` or `whole-file`; `status: CONVERGED` when all live models APPROVE

**Script resilience (graceful degradation):** a missing or unauthenticated CLI is recorded in the receipt and skipped — the script never hard-crashes on a missing provider and always writes the receipt. A run with fewer than all requested models is flagged `status: degraded`. Headless-safe for subagents.

**Reading the receipt:** script resilience and gate passage are two different layers. A `degraded` status (fewer than all requested models ran) is a script outcome, not a gate verdict — the script finishing without error never means the gate passed. The pass condition itself lives in **Tier gates** below; this section only produces and interprets the receipt. CI runs Layer 1 only — never Layer 2.

**User override procedure.** When convergence is structurally unreachable — a residual conflict survives round 3, or only one provider is ever available — the user may override. Record the override *in the eval receipt*: set `status: user-override`, add a `rationale:` line stating why consensus was not achievable, and name the operator who issued it. An override is the user's call alone, never self-issued by the agent, and is invalid with zero live providers — at least one model must have actually rendered a verdict.

### Tier gates

```
Tier 1 (entry — register routing):
  [ ] Admission receipt skills/skillify/evals/admission-<candidate-slug>-<date>.md exists with verdict ADMIT
      (create: Stage 0 cleared before any authoring — a non-admitted candidate never reaches Tier 1.
       update/move/deprecate of an already-admitted skill cite the existing receipt; a fresh one is
       required only when an update materially changes the admitted scope)
  [ ] SKILL.md conforms to references/schemas.md (5-key frontmatter + sections)
  [ ] CHANGELOG.md seeded with a dated bullet
  [ ] Layer 1 scripts pass (validate-skill-format.py + validate-runtime-hygiene.py)
  [ ] Routing entry added (see Placement & Routing)
  [ ] E2E smoke — one real run, side effect confirmed

Tier 2 (trust):
  [ ] Layer-2 consensus receipt evals/consensus-<skill>-<date>.md —
      status: CONVERGED (all live models APPROVE, ≥2 live model families),
      or status: user-override with a rationale  [precedes tests]
  [ ] Unit tests for deterministic scripts → tests/
  [ ] Integration test end-to-end with a real fixture → tests/
  [ ] LLM evals for judgment scenarios → evals/
  [ ] Routing eval — trigger phrase naturally selects this skill when invoked in Claude Code
```

## Placement & Routing — flat-first

Default to a **flat** package at `skills/<skill-name>/`. Promote into an area folder only when a cohesive cluster of ≥2–3 sibling skills clearly shares an owner. Do not invent an area for a solo or boundary-ambiguous domain — that creates fake dispatcher clauses and routing ambiguity.

In craft-skills, skills are discovered by Claude Code from the `description` field in `SKILL.md` frontmatter — there is no RESOLVER.md requirement for flat skills. A flat skill at `skills/<skill-name>/` needs only a well-formed `description` trigger phrase. Area folders with ≥2 sibling skills use a RESOLVER.md for disambiguation (full schema: `references/schemas.md §5`). Full move mechanics and routing rules: `references/topology-and-routing.md`.

Leaf descriptions are written as **real user trigger phrases**, not capability blurbs.

## Requirements

- `python3` — Layer-1 validators and `scripts/consensus.py`
- `gh` — PR creation and branch flow
- `codex`, `gemini`, `claude` — Layer-2 consensus CLIs (all three optional; missing providers degrade gracefully and are recorded in the receipt)

## Secrets — per-skill `.env`

Every access path, API key, OAuth token, and host-specific value lives in a **per-skill** `.env` at `$SKILL_DIR/.env` (gitignored). Commit only `$SKILL_DIR/.env.example` with placeholder values; document required variable names in `SKILL.md`. Never hardcode real values in `SKILL.md`, references, scripts, tests, evals, or examples. PR sequence, diff-mode guard, and the break-glass path for an already-committed secret: `references/runtime-hygiene-pr-playbook.md` and `references/secret-env-history-rewrite.md`.

## Change history — per-package CHANGELOG

Every skill package owns a `CHANGELOG.md`. Every change appends one bullet:

```
- YYYY-MM-DD — why; what changed
```

Newest last; never reorder or edit existing bullets. History lives **only** in `CHANGELOG.md` — `SKILL.md` must not contain a `## Change Log` section. Bump `version` (semver) on each change. Version-bump rubric: `references/schemas.md §6`.

## Governance

**This protection applies to the skillify package itself (`skills/skillify/**`), not to the skills it manages.** Editing skillify's own body, references, agents, or scripts requires explicit current-turn operator approval, enforced by PreToolUse hooks across Claude Code and Codex — no arbitrary modify or delete. Ordinary skill lifecycle work skillify performs *on other skills* (create, update, move, deprecate under `skills/<other>/**`) follows the normal branch → commit → PR flow and does **not** need this break-glass approval.

Every skill change is delivered as branch → commit → PR unless the operator explicitly requests local-only. A patched file is not the deliverable; reviewable repo state is. Mechanics: `references/skill-pr-branch-hygiene.md`.

A user workflow correction is a first-class skill signal: encode it in the governing skill body, not only in memory. Prefer patching a class-level umbrella (with detail in `references/`) over creating a narrow one-session skill.

Changes touching authority boundaries need explicit scoped current-turn approval before staging: `references/protected-routing-pr-approval.md`.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's a small edit, skip the branch/PR." | The deliverable is reviewable repo state. A patched file with no PR is not done (unless the operator explicitly requests local-only). |
| "I'll add the CHANGELOG bullet later." | Layer-1 CI fails a changed package with no dated bullet. Add it in the same commit. |
| "This domain feels like an area, I'll nest it now." | Flat-first. One skill is not an area. Premature hierarchy creates fake dispatcher clauses. |
| "I'll write the tests first to lock it down." | Consensus eval precedes tests. Tests over unproven behavior lock in mediocrity. |
| "The reviewer prompt checks the format." | Format is a Layer-1 script gate. The reviewer judges quality only; `validate-skill-format.py` judges format. |
| "I'll put the API key inline for now." | Secrets live in the per-skill `.env`. A committed secret means history rewrite + rotation. |
| "I'll note what this skill used to do for context." | A recipe is present-tense only. Relocate the lesson to a Rationalization/Red-Flag row and the event to CHANGELOG.md. |
| "I'll credit the source that inspired this rule, for context." | Attribution is provenance, not recipe. Keep the principle imperative; move the credit to CHANGELOG.md. A reader executing the recipe never needs to know who it came from. |
| "This term is well-known — no need to define it." | An unexplained term of art is a contamination. Define it inline at first use (present-tense, self-contained), or replace the abstract phrasing with a concrete technical equivalent. Move the clarification rationale to CHANGELOG.md. The reader of the skill may not share your context. |
| "My own review is enough — Layer-2 consensus is optional." | Single-model judgment is not robust. The convergence loop surfaces blind spots no one reviewer catches; the Tier-2 gate requires a consensus receipt. |

## Red Flags

- Authoring a skill without reading `references/schemas.md` first
- A `## Change Log` section inside `SKILL.md` (history belongs in `CHANGELOG.md`)
- Writing tests before the Layer-2 consensus receipt exists
- A leaf description that is an abstract capability blurb, not a user trigger phrase
- Nesting a solo/ambiguous skill into an area folder
- A real path/secret/`.env` value committed into any package file
- Stopping at "I patched the file" without branch + PR
- A sentence in `SKILL.md` that narrates the skill's own history, migration, or prior name
- A body sentence naming an external person, tool, or repo as the source of a rule ("inspired by …", "`<tool>`-style", "adopted from …") — credit belongs in `CHANGELOG.md`
- An undefined term of art, abstract/cultural blurb, or "we call it X because…" meta-note in the body — define inline at first use or replace with concrete technical phrasing; move the clarification rationale to `CHANGELOG.md`
- Two package parts or sections owning the same responsibility (not mutually exclusive), or a concern with no home (not collectively exhaustive) — the skill is not MECE
- Running Layer-2 consensus from CI (Layer 2 is local only; CI runs Layer 1 only)
- Tool skill drafted without reading the upstream README first

## Verification

- [ ] `validate-skill-format.py --diff-base origin/main...HEAD` passes (Layer 1)
- [ ] `validate-runtime-hygiene.py --diff-base origin/main...HEAD` passes (Layer 1)
- [ ] Package conforms to `references/schemas.md`; no `## Change Log` in `SKILL.md`
- [ ] `CHANGELOG.md` has a new dated bullet; `version` bumped
- [ ] Placement is flat unless a real cluster justifies an area
- [ ] Routing entry uses real load keys and user trigger phrases (thick schema: `references/schemas.md §5`)
- [ ] Secrets only in per-skill `.env`; `.env.example` committed with placeholders
- [ ] Layer-2 consensus receipt `evals/consensus-<skill>-<date>.md` with `status: CONVERGED` (Tier-2 required)
- [ ] E2E smoke: one real run, side effect confirmed
- [ ] Branch → commit → PR opened (unless explicitly local-only)
