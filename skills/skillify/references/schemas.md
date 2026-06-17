# Skill Package Contract Schemas

> This file is the canonical CONTRACT SCHEMA SSOT for craft-skills skill packages.
> `skillify` authors and reviewers operate against this document.

## Table of Contents

1. [craft-skills Deltas](#1-craft-skills-deltas)
2. [5-Key Frontmatter Schema](#2-5-key-frontmatter-schema)
3. [Anatomy Section Flow](#3-anatomy-section-flow)
4. [Package-Part Conditions](#4-package-part-conditions)
5. [RESOLVER Thick Schema](#5-resolver-thick-schema)
6. [Version-Bump Rubric](#6-version-bump-rubric)

---

## 1. craft-skills Deltas

These rules override the upstream guide where they conflict.

1. **Frontmatter carries 5 keys.** craft-skills `SKILL.md` frontmatter requires `name`, `description`,
   `version` (semver), `allowed-tools` (Claude Code tool names), and `compatibility` (intended
   runtimes). Bump `version` on every behavioral change.

2. **Per-package `CHANGELOG.md`, not a vault stub.** Each skill package owns a `CHANGELOG.md`
   with `YYYY-MM-DD — why; what changed` bullets. There is no separate `{skill-name}.md` stub
   and no `## Change Log` section inside `SKILL.md`.

3. **`references/` and `scripts/` live INSIDE the skill directory**
   (`skills/<area>/<skill>/references/`), not at the repo root. This diverges from the upstream
   "references at project root" rule because craft-skills is a multi-skill plugin library.

4. **Secrets live in a per-skill `.env`.** Access paths, API keys, tokens, and host-specific
   values go in `skills/<area>/<skill>/.env` (gitignored). Commit only `<skill>/.env.example`
   with placeholder values. Never hardcode real values in `SKILL.md`, references, scripts,
   tests, or evals.

5. **Recipe-law: present-tense imperative only.** Skill recipes are operating instructions.
   Never narrate the skill's own evolution inside `SKILL.md` or any reference file
   ("used to", "we migrated", "이전에는", "previously"). History belongs in `CHANGELOG.md` only.
   Bake corrections imperatively — not as "we used to do X".

   **Imperative distillation procedure.** A skill carries semantic memory (timeless rules),
   never episodic memory (what this skill used to be). When a historical correction is
   discovered, apply the three-way split:

   ① **Corrected behavior (rule)** → a present-tense imperative step in `## Steps` /
     Core Process. Example: "Author flat-first."
   ② **Failure it prevents (why)** — only if it has anti-regression value → a present-tense
     invariant row in `## Common Rationalizations` or a bullet in `## Red Flags`.
     Example: `"It's fine to nest now" | "Flat-first — one skill is not an area."` NOT a
     past-event sentence.
   ③ **The event, date, or narrative itself** → `CHANGELOG.md` (or dropped entirely).

   Transformation pattern: `"was X, changed to Y"` (story) → `"do Y"` in Core Process +
   `"X is wrong because Z"` in Rationalizations (invariant). Same information; only tense
   and location change. The Rationalizations/Red Flags tables are the sanctioned landing
   zone for the imperative residue of a correction — the lesson is relocated, not lost.

   **Contamination test (one line):** "Could a reader who never knew this skill's past
   understand and execute this sentence as-is?" Any reference to a former skill name, a
   migration event, or temporal markers ("previously", "used to", "이전에는", "we changed")
   fails — rewrite via the three-way split above.

   **External attribution is provenance, not recipe.** The *source* of a rule — who or what
   inspired it ("inspired by X", "adopted from `<tool>`", "`<repo>`-style") — carries no
   operating value to a reader executing the recipe. Keep the *function* as a present-tense
   imperative invariant in the body; record the *credit* in `CHANGELOG.md`. Dissolve borrowed
   philosophy into the recipe; do not sign it. Contamination test for this class: "Does this
   sentence name a person, tool, or repo as the origin of a rule?" If yes, strip the name from
   the body and move the credit to `CHANGELOG.md`.

   **Jargon/unexplained terminology is a contamination.** A term of art used without definition
   — or an abstract/cultural blurb standing in for a concrete technical concept — is not
   self-contained operating instruction. A reader executing the recipe may not share the
   author's context. Resolution is two-part: (1) **body** — define the term inline at its first
   use (present-tense, self-contained) OR replace the abstract phrasing with a concrete
   technical equivalent; never leave a meta-explanation ("we call it X because…") in the body;
   (2) **CHANGELOG.md** — record the specific clarification decision and provenance (which
   term, what it replaced, why). Contamination test for this class: "Can a reader who does not
   share the author's context execute this sentence without guessing what the term means?" If
   no, define it inline or replace it; move the clarification rationale to `CHANGELOG.md`.

---

## 2. 5-Key Frontmatter Schema

```yaml
---
name: <matches dir; ≤64; lowercase/digits/hyphen; no leading/trailing/consecutive hyphen>
description: <real user trigger phrase + what it does; ≤1024>
version: <3-part semver MAJOR.MINOR.PATCH>
allowed-tools: [Bash, Read, Edit, Grep]
compatibility: claude-code, codex
---
```

### Field Rules

| Field | Constraint |
|-------|------------|
| `name` | Lowercase letters, digits, hyphens only. Must match the package directory name exactly. No leading hyphen, no trailing hyphen, no consecutive hyphens. ≤64 characters. |
| `description` | Opens with the real user trigger phrase (the exact phrasing a user types), then states what the skill does. ≤1024 characters. No embedded workflow steps — the description is injected into the system prompt, so steps in it are followed instead of the full skill. |
| `version` | Three-part semver `MAJOR.MINOR.PATCH`. Bump on every behavioral change. See §6 for the rubric. |
| `allowed-tools` | YAML list of Claude Code **tool names** (e.g., `Bash`, `Read`, `Edit`, `Grep`, `Task`). Declares the tools the skill may invoke. Not shell binary names. |
| `compatibility` | Comma-separated list of intended runtimes. Valid values: `claude-code`, `codex`. ≤500 characters. |

**External binaries** (`gh`, `python3`, etc.) are **NOT** in frontmatter.
Document them in the `SKILL.md` body under `## Requirements` as prose. Frontmatter declares
agent-layer tool permissions; runtime prerequisites are prose in the skill body.

### Name style

The `name` is a compact handle, not a sentence — discoverability lives in `description` (the trigger phrases), so the name stays terse and stable.

- Name the **one concept** the skill owns, in the fewest tokens that stay unambiguous. Prefer a single word (`programming`, `refactor`, `documents`); a verb for an action skill, a noun for a domain skill.
- Cap at **two tokens**. A third is justified only when the concept genuinely needs it (`remove-ai-slops`). Hyphens join the words of one concept; they never decorate.
- Banned: a `-skill` / `-tool` / `-helper` / `-workflow` suffix (the package is already a skill), a `how-to-` / `auto-` / `my-` prefix, a verb-plus-object phrase that reads as a sentence (`generate-the-report`), and a name that merely restates the description.

---

## 3. Anatomy Section Flow

### Recommended Section Pattern

```markdown
# Skill Title

## Overview
One-two sentences: what this skill does and why it matters.

## When to Use
- Bullet list of triggering conditions (symptoms, task types).
- When NOT to use (exclusions).

## [Core Process / The Workflow / Steps]
Numbered steps or phases. ASCII flowcharts at decision points.
Code examples where they clarify behavior.

## Requirements
External binaries, env vars, prerequisites not captured in frontmatter.
(craft-skills addition — not in upstream template.)

## Common Rationalizations
| Rationalization | Reality |
|---|---|
| Excuse agents use to skip a step | Why the excuse is wrong |

## Red Flags
- Behavioral patterns indicating the skill is being violated.

## Verification
After completing the skill's process, confirm:
- [ ] Each exit criterion (each requires verifiable evidence).
```

The frontmatter contract above is required. The section layout is a recommended pattern, not
a rigid template. Equivalent headings (`How It Works`, `Workflow`, `Process`) are acceptable
when they serve the same purpose clearly.

### Section Purposes

**Overview** — the elevator pitch. Answers: what does this skill do, and why should an agent
follow it?

**When to Use** — helps agents decide if this skill applies. Include both positive triggers
and negative exclusions.

**Core Process** — the heart of the skill. Step-by-step, specific, actionable.
"Run `npm test` and verify all tests pass" beats "make sure the tests work."

**Requirements** (craft-skills addition) — lists external binaries, env vars, and runtime
prerequisites. External binaries belong here, not in frontmatter.

**Common Rationalizations** — the most distinctive feature of well-crafted skills. Every
skip-worthy step gets an excuse paired with a factual rebuttal. Prevents the agent from
rationalizing its way around the process.

**Red Flags** — observable signs the skill is being violated. Useful during code review and
self-monitoring.

**Verification** — exit criteria. Every checkbox is verifiable with evidence (test output,
build result, screenshot, etc.).

### Writing Principles

1. **Process over knowledge.** Skills are workflows, not reference docs. Steps, not facts.
2. **Specific over general.** "Run `npm test`" beats "verify the tests".
3. **Evidence over assumption.** Every verification checkbox requires proof.
4. **Anti-rationalization.** Every skip-worthy step needs a counter-argument in the
   rationalizations table.
5. **Progressive disclosure.** `SKILL.md` is the entry point. Supporting files are loaded
   only when needed.
6. **Token-conscious.** Every section must justify its inclusion. If removing it would not
   change agent behavior, remove it.

---

## 4. Package-Part Conditions

The table below is **normative** — one line per part, stating exactly when to create it.
For the explanatory decision guide with concrete examples and rationale, see
`package-contract.md`.

| Part | Create when |
|------|-------------|
| `SKILL.md` | Always (required). Keep body < 500 lines / < 5000 tokens with refs one level deep. |
| `scripts/` | A step must be deterministic and repeatable (format checks, transforms, fan-out). Prefer a script over a prompt for anything verifiable. |
| `references/` | Bulk knowledge loaded on demand (schemas, per-variant docs). A reference file > 300 lines gets a table of contents. |
| `assets/` | Files used in the skill's output (templates, icons, fonts). |
| `sections/` + `manifest.json` | Heavy SKILL.md: keep a small skeleton, move bulk sections to `sections/<x>.md` behind a STOP-Read pointer in the manifest. |
| `RESOLVER.md` | See §5. Master always. Area with ≥2 leaf skills always. Flat skill: none. |
| `agents/` | The skill spawns sub-agents with distinct charters. This is a real, defined package part — skills that spawn sub-agents MUST declare them here (one `.md` file per charter). **`agents/` is a skillify-package surface** holding this package's writer/reviewer/grader charters (skill-creator convention); it is NOT a global requirement imposed on every craft-skills skill. skillify carries exactly three: `writer.md` (author/static — defines the writer lane charter), `reviewer.md` (eval/static — defines the reviewer lane charter; shared rubric for the `scripts/consensus.py` multi-model panel, absorbs routing judgment), `grader.md` (eval/dynamic — defines the grader charter; grades real run outputs vs assertions). Blind→unblind A/B comparison (`comparator`/`analyzer`) is intentionally deferred; see Deferred Capabilities note below. **Role prompts live in `agents/` (skill-creator convention), not `prompts/`.** This is a deliberate choice: `agents/` signals sub-agent lane charters scoped to the skill package; a separate `prompts/` directory is not used and must not be created. |
| `CHANGELOG.md` | Always, alongside any versioned SKILL.md. Append one dated bullet per change (`YYYY-MM-DD — why; what changed`); never edit prior bullets. |
| `evals/` | Runtime log scratch only — **gitignored, never committed**. When a Layer-2 consensus run executes, `scripts/consensus.py` writes its receipts here (`evals/consensus-<skill>-<date>.md`, `evals/<provider>-r<N>.md`) as a local record of that run. These are transient logs, not a package surface: the convergence verdict that gates a change is captured in the PR/CHANGELOG, not in committed receipt files. |

### Deferred Capabilities

**Blind→unblind A/B draft selection** (`comparator`/`analyzer`) is intentionally deferred until skillify iterates on competing drafts. When added, it should be a single `agents/ab-judge.md` with an internal blind→unblind two-phase protocol (blind phase scores both drafts without knowing provenance; unblind phase reveals authorship before final selection). Do not add this file until the workflow genuinely produces multiple competing drafts.

**Load-key path-resolution** is a Layer-1 script check, not an agent judgment. The routing validator script (`scripts/validate-skill-format.py` or a dedicated routing validator) owns filesystem existence checks for all RESOLVER load keys. `agents/reviewer.md` judges routing coherence (trigger phrase quality, field completeness, phantom dispatcher clause detection) but does not perform filesystem stat calls.

---

## 5. RESOLVER Thick Schema

### When a RESOLVER.md Is Required

| Scope | Requirement |
|-------|-------------|
| `skills/RESOLVER.md` (master) | Always exists. Routes all areas and flat skills. |
| `skills/<area>/RESOLVER.md` (area) | Required when the area folder contains ≥2 leaf skills. |
| Flat skill at `skills/<skill-name>/` | None. A flat skill carries no RESOLVER. |

**No phantom router rule.** Do not create a whole-repo shared-tool pseudo-router.
`skills/RESOLVER.md` is a reference routing table only — never a loadable skill.
A root-level dispatcher that routes the entire repo as a single mega-skill must not exist.
Claude Code discovers individual skills from `skills/<name>/SKILL.md` frontmatter directly;
a synthetic whole-repo router adds no value and must be removed.

### Header Dispatcher Line (required on every RESOLVER.md)

Every `RESOLVER.md` opens with a `dispatcher for:` header line naming the scope:

```
dispatcher for: <area-name | master>
```

Examples:

```
dispatcher for: master
dispatcher for: skillify
dispatcher for: second-brain
```

### Per-Area Boundary-Charter Prose Block (required)

After the header line and before the routing table, each area RESOLVER includes a
boundary-charter prose block defining what the area owns and what it hands off:

```markdown
## Boundary Charter

**<Area> owns:** <one sentence — what this area is solely responsible for>.
**<Area> does NOT own:** <one sentence — adjacent concerns explicitly excluded>.
**Hand-off:** <which area or flat skill handles the excluded concern>.
```

Example:

```markdown
## Boundary Charter

**skillify owns:** the full lifecycle of craft-skills skill packages — create, update, move/rename,
deprecate — and the gates that make a package trustworthy.
**skillify does NOT own:** personal note creation, prompt/template authoring, or unrelated plugin configuration.
**Hand-off:** note or template operations → the operator's note-taking workflow; plugin config → project settings.
```

### Routing Entry Schema (7 fields per entry)

| Field | Meaning |
|-------|---------|
| **Trigger intent** | The real user phrase or context that routes here. Written as a user would actually type it. Not an abstract capability blurb. |
| **Skill / Area** | The leaf skill key or area folder this entry dispatches to. |
| **Load key** | The concrete path that resolves at runtime (must exist on disk). Nested skills use qualified keys: `<area>/<skill>`. |
| **Boundary** | What this skill does NOT own — the MECE charter edge. One sentence. |
| **Sibling delta** | How this skill differs from its nearest sibling routing entry. Disambiguation sentence to prevent mis-routing. |
| **Compatibility** | Which runtimes this routing entry is valid in: `claude-code`, `codex`. |
| **Notes** | Edge cases, deprecations, cross-area handoffs. Omit value if none. |

### RESOLVER Table Format

```markdown
dispatcher for: <scope>

## Boundary Charter
...

## Routing Table

| Trigger intent | Skill / Area | Load key | Boundary | Sibling delta | Compatibility | Notes |
|----------------|-------------|----------|----------|---------------|---------------|-------|
| "make a skill", "skillify this workflow" | skillify | skillify | Does not own personal note creation or prompt authoring | skillify owns skill CRUD; other workflows own note/template CRUD | claude-code, codex | |
```

### Validation Rules

- Every load key resolves to an existing directory on disk at eval time.
- Every trigger intent is a real user phrase, not a capability blurb.
- No routing entry points to a non-existent skill directory (orphan check).
- **Layer split:** path-existence checks (does each load key resolve on disk?) are owned by the Layer-1 routing validator script (`scripts/validate-skill-format.py` or a dedicated routing validator). Routing judgment (are trigger phrases real? are thick-schema fields coherent? are there phantom dispatcher clauses?) is owned by `agents/reviewer.md` in the eval lane.

---

## 6. Version-Bump Rubric

```
MAJOR  Skill's contract changes incompatibly: a trigger phrase removed/renamed,
       allowed-tools gains entries callers must now permission, or output format
       breaks downstream consumers.
       Requires explicit user confirmation before bumping. Reset MINOR/PATCH → 0.

MINOR  Backward-compatible capability added: new phase, flag, routing branch, specialist
       dispatch, or any user-visible behavioral addition.
       Requires explicit user confirmation before bumping. Reset PATCH → 0.

PATCH  Bug fix, prose correction, checklist or dependency bump, quality-gate tuning —
       no interface change, no new behavior visible to callers.
       Ship without prompting the user.
```

**Decision heuristic:** ask "does a caller already using this skill need to change anything?"
If yes → MAJOR or MINOR. "Does the caller gain a new opt-in capability?" If yes → MINOR.
"Is it a fix or a clarification with no interface effect?" → PATCH.
