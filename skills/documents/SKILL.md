---
name: documents
description: '"write an ADR", "set up docs/", "where does this spec go", "write a README", "write the changelog", "document this API", "how should I comment this", "write a design.md", "set up a design system", "define UI tokens", "/documents" — author and route project documentation: research/references/spec/plan/decision/rule artifacts plus README, API docs, changelog, code comments, and design system tokens.'
version: 1.2.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
compatibility: claude-code, codex
---

# documents

Owns the full project documentation system: the `docs/` folder ontology, the lifecycle of every artifact type, and the routing rules that place each artifact in the right location with the right template.

This skill is a **waypoint**. It carries the ontology, routing, and docs/ layout at decision depth; deep per-format recipes live in nested sub-recipes that you load on demand (see **Children** below).

## Artifact types (MECE)

Every documentation artifact answers exactly one question. Never let one artifact try to answer two.

| Artifact | Question answered | Lifespan | Template | Canonical location |
|----------|------------------|----------|----------|--------------------|
| **research** | *What did I find* — facts, sources, comparisons (pre-decision) | Topic-scoped; superseded as evidence evolves | `templates/research.md` | `docs/research/{slug}.md` |
| **references** | *What does this external source say* — verbatim static archive of a third-party document | Permanent snapshot; never edited after capture | `templates/references.md` | `docs/research/references/{slug}.md` |
| **spec** | *What* is this work and are the requirements clear? | Work-scoped, one-shot | `templates/spec.md` | `docs/exec-plan/active/{slug}/spec.md` |
| **plan** | *How* to implement (steps, files, order) | Work-scoped; body immutable after finalize | `templates/plan.md` | `docs/exec-plan/active/{slug}/plan.md` |
| **decision** | One expensive-to-reverse *cross-cutting* decision | Permanent topic anchor; body edited in place; each change logged as one line in the ADR's ## Changelog | `adr/template.md` | `docs/decisions/ADR-NNN-{topic}.md` |
| **rule** | A standing convention (ongoing constraint, not work-scoped) | Alive as long as the convention holds | `templates/rule.md` | `docs/rules/{topic}.md` |

## Children — load on demand

For a sub-task below, **Read the named sub-recipe before authoring** — it carries the deep format, the steps, and the colocated template. The sub-recipes are progressive-disclosure reference files this waypoint loads on demand; they are not separately discovered commands.

| Sub-task / trigger | Load |
|---|---|
| Write or update an ADR / record a cross-cutting decision | `adr/SKILL.md` (+ `adr/template.md`) |
| Write or update the repository README | `readme/SKILL.md` (+ `readme/template.md`) |
| Document a function/method or REST endpoint (JSDoc, OpenAPI) | `api-docs/SKILL.md` (+ `api-docs/template.md`) |
| Write the project-level CHANGELOG / release notes | `changelog/SKILL.md` (+ `changelog/template.md`) |
| Decide how to comment code (comment-the-why) | `inline-comments/SKILL.md` |
| Write or update a project's design system source of truth (design.md) | `design/SKILL.md` (+ `design/template.md`) |

The remaining ontology artifacts (research, references, spec, plan, rule) are authored directly from `templates/` using the routing below — they have no sub-recipe yet.

## Routing

When an artifact arrives for filing, ask exactly one question — "which question does this answer?" — and route to the matching template and location above. If the answer spans two questions, split into two artifacts.

**References vs research:** A references file is a verbatim static copy of an external document (e.g. a spec page, RFC, or third-party doc converted to markdown). A research file is your own synthesis — findings, comparisons, and options drawn from one or more sources. Never merge them.

**Rule vs ADR:** If a convention encodes a cross-cutting decision, the *why* goes in a decision (ADR) and the *what to do* goes in a rule. The ADR is the frozen choice; the rule is the live operational guide. For ADR depth, load `adr/SKILL.md`.

## Decision pipeline

```
research (facts found)  →  decision/ADR (choice made)  →  plan (implementation built)
```

- Research collects evidence and presents options. It does **not** decide.
- A decision distilled from research is an ADR (load `adr/SKILL.md`).
- How to build that decision is a plan.

When something is hard to route, ask which stage it is at: *Am I still gathering facts (research), committing to a choice (ADR), or sequencing work (plan)?*

## Canonical `docs/` layout

```
docs/
├── research/                     # Fact collection — sources, comparisons (pre-decision)
│   ├── {slug}.md                 #   research artifact
│   └── references/               #   verbatim static archives of external documents
│       └── {slug}.md
├── exec-plan/                    # All work-scoped specs + plans
│   ├── active/{slug}/            #   spec.md + plan.md while work is in progress
│   └── archive/{slug}/           #   same folder, moved here when done/discarded/superseded
├── decisions/                    # Cross-cutting ADRs (ADR-001..N) — permanent, never deleted
│   ├── README.md                 #   ADR index + lifecycle reference
│   └── ADR-NNN-{topic}.md
├── rules/                        # Standing conventions (ongoing constraints, not work-scoped)
│   └── {topic}.md
└── architecture.md               # Living system map — annotated directory tree, component
                                  # boundaries, cross-cutting decisions index, key data/control
                                  # flows. Points to ADRs and rules; does not restate them.
```

Scratch drafts from planning or research passes live **outside** `docs/` (tool-specific scratch workspace) and are not git-canonical. The first act of finalizing a draft is to **move** it into `docs/` under the correct path, then delete the scratch source.

## Lifecycle — spec and plan (exec-plan)

```
spec drafted (scratch)
     │  [first act of planning]  MOVE ──►  docs/exec-plan/active/{slug}/spec.md
     ▼
plan drafted (scratch)
     │  MOVE ──►  docs/exec-plan/active/{slug}/plan.md
     │            FINALIZED on first git commit that includes plan.md
     │            body is immutable from that point
     ▼
work complete / discarded / superseded?
     │  add frontmatter status line(s) to plan.md (or spec.md if no plan was written):
     │    status: done | discarded | superseded-by
     │    superseded-by: {new-slug}     # required when status: superseded-by
     ▼
MOVE entire folder:  active/{slug}/  ──►  archive/{slug}/

     │  plan contained a cross-cutting / expensive-to-reverse decision?
     ▼
DISTILL ──►  docs/decisions/ADR-NNN-{topic}.md   (load adr/SKILL.md)
```

**Lifecycle = folder position.** A plan is active or archived by where its folder lives, not by a status field alone. Move the whole `{slug}/` folder — never split spec and plan.

**Supersede timing:** When creating a superseding plan (plan-B), archive the superseded plan (plan-A) in the same action before beginning execution of plan-B.

**Plan immutability.** A plan is finalized on the first git commit that includes its `plan.md`. From that point the body is immutable. If scope changes, create a new slug and set the old plan's frontmatter to `status: superseded-by` + `superseded-by: {new-slug}`. Only the `status` / `superseded-by` frontmatter lines are mutable post-finalize.

ADR lifecycle, the plan-vs-ADR boundary, the distill rule, and why there is no "supersede" all live in `adr/SKILL.md` — load it when working on a decision.

## Slug naming

Format: `{kebab-description}` — lowercase, hyphens only, no date prefix, no issue numbers. Date and author live in frontmatter, not the folder name.

The folder name is the authoritative slug. A frontmatter `slug` field that disagrees with its folder name is an error.

## `architecture.md` — the system map

`architecture.md` answers "how is this system put together?" for someone who just opened the repo. It is a living map updated as the system changes — not frozen like an ADR.

Include: annotated directory tree (each top-level folder with a one-line purpose and pointer to the governing ADR/rule), component boundaries (what each module owns and how they communicate), cross-cutting decisions index (links to ADRs — do not restate them), and the one or two data/control flows that matter most.

Keep it a map, not a manual. If it starts duplicating an ADR body, replace the duplication with a link.

## Trivial exemptions — no spec/plan required

- Typo, comment, or wording fixes
- Lint- or format-only changes
- Dependency patch-version bumps (`x.y.Z`)
- Behavior-preserving renames

## Red flags

- A research doc that asserts a decision (research presents; it does not decide)
- Scratch drafts treated as canonical (never moved into `docs/`)
- `architecture.md` that restates ADR bodies instead of linking them
- Completed or discarded work still sitting in `active/` with no `status` frontmatter
- A references file containing your own synthesis (that belongs in research)
- Authoring an ADR, README, API doc, or changelog without first loading its sub-recipe

## Verification

- [ ] Each artifact answers exactly one of the six questions (research/references/spec/plan/decision/rule)
- [ ] Cross-cutting decisions are distilled into ADRs, not buried in plans
- [ ] Completed/discarded work moved from `active/` to `archive/` with a `status` line
- [ ] `architecture.md` is a map that links out, not a manual that duplicates
- [ ] References files contain verbatim source content, not your synthesis
- [ ] Slug frontmatter field matches the folder name exactly
- [ ] Deep-format work (ADR, README, API docs, changelog, comments) was authored from its sub-recipe
