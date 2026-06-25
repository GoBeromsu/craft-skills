---
name: documents
description: '"write an ADR", "set up docs/", "where does this spec go", "/documents" — author and route project documentation: research/references/spec/plan/decision/rule artifacts into the docs/ ontology.'
version: 1.0.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
compatibility: claude-code, codex
---

# documents

Owns the full project documentation system: the `docs/` folder ontology, the lifecycle of every artifact type, and the routing rules that place each artifact in the right location with the right template.
This guidance is derived and thickened from the addyosmani/agent-skills `documentation-and-adrs` SSOT, adapted to this repository's self-complete ADR model.

## Artifact types (MECE)

Every documentation artifact answers exactly one question. Never let one artifact try to answer two.

| Artifact | Question answered | Lifespan | Template | Canonical location |
|----------|------------------|----------|----------|--------------------|
| **research** | *What did I find* — facts, sources, comparisons (pre-decision) | Topic-scoped; superseded as evidence evolves | `templates/research.md` | `docs/research/{slug}.md` |
| **references** | *What does this external source say* — verbatim static archive of a third-party document | Permanent snapshot; never edited after capture | `templates/references.md` | `docs/research/references/{slug}.md` |
| **spec** | *What* is this work and are the requirements clear? | Work-scoped, one-shot | `templates/spec.md` | `docs/exec-plan/active/{slug}/spec.md` |
| **plan** | *How* to implement (steps, files, order) | Work-scoped; body immutable after finalize | `templates/plan.md` | `docs/exec-plan/active/{slug}/plan.md` |
| **decision** | One expensive-to-reverse *cross-cutting* decision | Permanent topic anchor; body edited in place to the current decision; each change logged as one line in the ADR's ## Changelog (git holds full history) | `templates/decision.md` | `docs/decisions/ADR-NNN-{topic}.md` |
| **rule** | A standing convention (ongoing constraint, not work-scoped) | Alive as long as the convention holds | `templates/rule.md` | `docs/rules/{topic}.md` |

## Routing

When an artifact arrives for filing, ask exactly one question — "which question does this answer?" — and route to the matching template and location above. If the answer spans two questions, split into two artifacts.

**References vs research:** A references file is a verbatim static copy of an external document (e.g. a spec page, RFC, or third-party doc converted to markdown). A research file is your own synthesis — findings, comparisons, and options drawn from one or more sources. Never merge them.

**Rule vs ADR:** If a convention encodes a cross-cutting decision, the *why* goes in a decision (ADR) and the *what to do* goes in a rule. The ADR is the frozen choice; the rule is the live operational guide.

## Decision pipeline

```
research (facts found)  →  decision/ADR (choice made)  →  plan (implementation built)
```

- Research collects evidence and presents options. It does **not** decide.
- A decision distilled from research is an ADR.
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

## Lifecycle

### Spec and plan (exec-plan)

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
DISTILL ──►  docs/decisions/ADR-NNN-{topic}.md
```

**Lifecycle = folder position.** A plan is active or archived by where its folder lives, not by a status field alone. Move the whole `{slug}/` folder — never split spec and plan.

**Supersede timing:** When creating a superseding plan (plan-B), archive the superseded plan (plan-A) in the same action before beginning execution of plan-B.

### Plan immutability

A plan is finalized on the first git commit that includes its `plan.md`. From that point the body is immutable. If scope changes, create a new slug and set the old plan's frontmatter to `status: superseded-by` + `superseded-by: {new-slug}`. Only the `status` / `superseded-by` frontmatter lines are mutable post-finalize.

### ADR lifecycle

```
PROPOSED → ACCEPTED → DEPRECATED
```

An ADR describes the current decision for one topic as a self-complete, MECE record. When the decision changes, edit that ADR body in place so it contains only the current decision, then add one line to its `## Changelog`: `- YYYY-MM-DD: what changed`. Do not create ADR replacement chains, coverage matrices, or retired-source tracking; git holds the detailed history. The ADR number is a stable topic anchor.
Document the **why**, not the what. Code and rules show what the system does; ADRs preserve the context, constraints, trade-offs, and rejected alternatives that explain why the system is shaped this way.

### Why there is no "supersede"

An ADR is the self-complete, MECE, current decision for one atomic topic. "Supersede" collapses different relationships that must stay separate:

- Same decision changed → edit the ADR body in place and add one line to `## Changelog`; git holds the full history. Do not create a new ADR or chain.
- More specific sub-decision → create a separate atomic ADR that `Refines:` the broader decision. Both remain current.
- Different decision that builds on another → create a separate atomic ADR that `References:` the other decision. Both remain current.
- "Only clause X changed" → the ADR was probably not atomic. Split it into atomic ADRs, then update the changed decision in place.

If each ADR is atomic, MECE, and self-complete, supersede chains collapse into in-place edits with `## Changelog` plus `References:` / `Refines:` links. ADR status is only `Proposed | Accepted | Deprecated`.

## Plan vs ADR — boundary

This is the most common filing error. They answer different questions.

| | plan (`docs/exec-plan/`) | ADR (`docs/decisions/`) |
|---|---|---|
| Question | *How* to implement this specific work | *Why* this cross-cutting choice — and what alternatives were rejected |
| Scope | One feature / task (work-scoped) | Cross-cutting — constrains all future work |
| Lifespan | Archivable when work ends | Permanent topic anchor; body edited in place to current decision |
| Body | Immutable after finalize; scope change → new slug | Updated in place; each change is one line in the ADR's ## Changelog (git holds detail) |
| Location | `active/{slug}/plan.md` → `archive/{slug}/` | `docs/decisions/ADR-NNN-*.md` |

### Distill rule

When a plan contains an expensive-to-reverse, cross-cutting choice (framework selection, data model, auth strategy, API shape, infrastructure), distill that choice into a new ADR before or at the time the plan is archived. The plan entry is **not** replaced — the ADR lives alongside it in `docs/decisions/`.

Decision test: *"Would a future engineer or agent working on an unrelated feature need to know this?"*
- Yes → write an ADR.
- No, it only affects this feature's implementation details → leave it in the plan.

### When to write an ADR
- Choosing a framework, library, or major dependency
- Designing a data model or schema
- Selecting an auth strategy
- Choosing API architecture (`REST` vs `GraphQL` vs `tRPC`, public contract shape, versioning model)
- Choosing build tools, hosting, or infrastructure
- Any cross-cutting decision that would be costly to reverse

### Do not write an ADR for

- Implementation steps or file-level details (belong in the plan)
- Choices that will be revisited within this same work item
- Trivial configuration values with no architectural consequence

### Common rationalizations
| Rationalization | Reality |
|---|---|
| "The code is self-documenting." | Code documents what exists; ADRs document why this path won and which paths lost. |
| "We'll document it once the API stabilizes." | Writing the ADR is the first test of the design; unclear rationale usually means the design is not stable yet. |
| "Nobody reads docs." | Future agents, future engineers, and you three months from now read the decision trail when changing the system. |
| "ADRs are overhead." | A 10-minute ADR prevents the same two-hour architecture argument six months later. |
| "Comments go stale." | What-comments go stale; why-comments and ADR rationale stay useful because the historical constraint remains true. |

Document known gotchas inline with a pointer back to the decision: `See ADR-NNN for rationale`.

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
- A plan and an ADR conflated into one file
- ADRs that overlap (not MECE), or a decision change with no ## Changelog entry
- Scratch drafts treated as canonical (never moved into `docs/`)
- `architecture.md` that restates ADR bodies instead of linking them
- Completed or discarded work still sitting in `active/` with no `status` frontmatter
- A references file containing your own synthesis (that belongs in research)

## Verification

- [ ] Each artifact answers exactly one of the six questions (research/references/spec/plan/decision/rule)
- [ ] Cross-cutting decisions are distilled into ADRs, not buried in plans
- [ ] Completed/discarded work moved from `active/` to `archive/` with a `status` line
- [ ] ADRs are MECE (one decision each); changed decisions are edited in place with a ## Changelog one-line entry and cross-ADR links use `References:` / `Refines:`
- [ ] `architecture.md` is a map that links out, not a manual that duplicates
- [ ] References files contain verbatim source content, not your synthesis
- [ ] Slug frontmatter field matches the folder name exactly
