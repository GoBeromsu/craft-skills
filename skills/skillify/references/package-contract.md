# Package Contract — Decision Guide

When to create each part of a craft-skills skill package, with examples and rationale.

The **normative one-line rules** live in `schemas.md §4`. This file is the explanatory
companion: it answers *why* each part exists and gives concrete examples so authors
make consistent, well-reasoned decisions.

---

## SKILL.md — Always Required

**Rule:** Every skill package requires exactly one `SKILL.md`. No exceptions.

**Rationale:** `SKILL.md` is the entry point Claude Code and Codex load.
Without it, the skill does not exist to any runtime.

**Size budget:** Keep the body under 500 lines / 5000 tokens. When it grows beyond that,
move bulk content to `sections/` (see below) rather than trimming useful material. One
level of indirection is fine; two levels of STOP-Read chaining is a smell.

---

## scripts/ — Deterministic, Repeatable Steps Only

**Rule:** Create `scripts/` when a step in the skill's process must be deterministic and
repeatable — not when it just runs a command you could put in a prose code block.

**Create when:**
- Format validation (e.g., `validate-skill-format.py` — checks frontmatter, CHANGELOG
  presence, no `## Change Log` section; CI-callable with `--diff-base`).
- Data transformation that is called identically every run (e.g., a fan-out script that
  sends a payload to three CLI endpoints and collects structured responses).
- Any step where a wrong result must be caught by exit code, not by reading prose output.

**Do not create when:**
- The "script" is just a one-liner bash command you can inline in the skill body.
- The logic branches on judgment (routing, quality assessment) — that belongs in a prompt,
  not a script; scripts are for verifiable, non-judgment operations.
- The step only ever runs once (setup, migration) — put it in a `## Setup` section of
  `SKILL.md` instead.

**Example:** `skillify/scripts/validate-skill-format.py` is a script because it enforces
a schema contract and CI must call it with a deterministic pass/fail exit code. A prompt
cannot reliably replace it.

---

## references/ — On-Demand Bulk Knowledge

**Rule:** Create `references/` when reference material would bloat `SKILL.md` beyond its
size budget or is loaded only sometimes (not on every skill invocation).

**Create when:**
- A schema or contract document that authors and reviewers consult, but the runtime agent
  does not need on every execution (e.g., `schemas.md`, `topology-and-routing.md`).
- Per-variant documentation that only one branch of the skill's workflow reads
  (e.g., docs for a specific tool or integration).
- Any single reference file that exceeds 300 lines — it gets a table of contents.

**Do not create when:**
- The reference fits inline (under ~50 lines) in `SKILL.md` — keep it there for
  progressive disclosure.
- The material is the skill's *workflow*, not supporting knowledge — that belongs in
  `SKILL.md` directly.

**Example:** `skillify/references/pipeline.md` holds the Writer/Reviewer Task invocation
templates. They are needed by the orchestrator but not by every caller of skillify, so
they live in `references/` rather than in `SKILL.md`.

---

## assets/ — Output Materials

**Rule:** Create `assets/` when the skill's process produces or uses files that are not
code or prose instructions — templates, icons, fonts, static data files.

**Create when:**
- The skill generates documents from a template (e.g., a PR description template,
  a slide deck boilerplate, a report scaffold).
- The skill requires a static data file as input to a script (e.g., a fixture JSON,
  a reference CSV).

**Do not create when:**
- The "asset" is a code snippet that belongs inline in `SKILL.md` or a script.
- The asset is a secret or contains real credentials — those go in `.env` (gitignored).

**Example:** A `document-skills/pptx` skill might keep a `assets/base-template.pptx`
that every generated slide deck starts from.

---

## sections/ + manifest.json — Heavy SKILL.md Decomposition

**Rule:** Use `sections/` + `manifest.json` only when `SKILL.md` genuinely exceeds the
size budget and the excess is structured content that splits cleanly by concern.

**Create when:**
- `SKILL.md` is over 500 lines / 5000 tokens after trimming redundancy.
- The excess breaks into 2–4 named sections that are each loaded only in specific
  branches of the workflow (STOP-Read pattern: "Read sections/foo.md before continuing").
- You want to keep `SKILL.md` as a lightweight skeleton with deliberate STOP-Read
  pointers.

**Structure:**

```
skills/<skill>/
  SKILL.md           # skeleton — one STOP-Read pointer per heavy section
  manifest.json      # lists available sections and their purposes
  sections/
    phase-harvest.md
    phase-prove.md
    phase-cement.md
```

**Do not create when:**
- The skill is under budget — premature decomposition adds navigation overhead.
- You are splitting to avoid reading the skill carefully; trimming beats splitting.

**STOP-Read pointer format** (in `SKILL.md`):

```markdown
> STOP — Read `sections/phase-harvest.md` before proceeding with this phase.
```

---

## RESOLVER.md — Routing Tables

**Rule:** See `schemas.md §5` for the normative when-required table. Summary:

- `skills/RESOLVER.md` (master): always exists.
- `skills/<area>/RESOLVER.md`: required when the area has ≥2 leaf skills.
- Flat skill at `skills/<skill-name>/`: no RESOLVER.

**Create an area RESOLVER when** you have promoted two or more related skills into an
area folder and need to document how to distinguish between them. The RESOLVER is the
disambiguation contract, not a convenience index.

**Do not create when:**
- There is only one skill in the area — add a second before creating the RESOLVER.
- You are tempted to create a whole-repo router — that is the phantom router anti-pattern.
  Claude Code discovers skills from frontmatter directly; a repo-level router is noise.

**Example:** `skills/second-brain/RESOLVER.md` exists because `second-brain/` contains
`terminology`, `roundup`, and siblings. Without it, a bare trigger phrase like
"summarize my notes" is ambiguous between siblings.

---

## agents/ — Sub-Agent Charters

**Rule:** Create `agents/` when the skill's process explicitly spawns sub-agents that
operate in separate lanes with distinct charters.

**Create when:**
- The skill has an **author lane** (produces content) and an **eval lane** (judges it),
  and these must never run in the same active context (no self-approval).
- Each sub-agent has a named, scoped charter that differs meaningfully from the others
  (e.g., `writer.md` drafts only; `reviewer.md` audits only; `grader.md` scores outputs).

**Do not create when:**
- The skill calls a tool or script inline — that does not require a sub-agent charter file.
- The sub-agent's instruction fits in a single Task() prompt argument — no file needed.

**Example:** `skillify/agents/` contains three agents organized along two axes (lane × eval-target):

| Agent | Lane | Eval target |
|-------|------|-------------|
| `writer.md` | Author | Static (produces SKILL.md drafts) |
| `reviewer.md` | Eval | Static (judges skill text and routing coherence; shared rubric for `scripts/consensus.py` multi-model panel) |
| `grader.md` | Eval | Dynamic (grades real run outputs vs tier-gate assertions) |

Each has a distinct charter and a distinct lane; mixing them in one context violates the no-self-approval rule.

**Separation contract:** the author lane runs first and produces a draft. The eval lane runs in a separate turn and sees the draft only, never the harvest context. Never self-approve in the same active context.

**Deferred capability — blind→unblind A/B selection:** comparing competing drafts (`comparator`/`analyzer`) is intentionally deferred until skillify iterates on multiple competing drafts. When added, implement as a single `agents/ab-judge.md` with an internal blind→unblind two-phase protocol. Do not add it before the workflow genuinely produces competing drafts.

**Routing audit split:** `reviewer.md` judges routing coherence (trigger phrase quality, thick-schema field completeness, phantom dispatcher clause detection). Deterministic path-resolution — verifying that each RESOLVER load key exists on disk — belongs to the Layer-1 routing validator script, not to any agent.
