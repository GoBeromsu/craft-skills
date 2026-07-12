---
name: document
description: Routes repository documentation into a six-type ontology and authors canonical artifacts. Use when asked to "record this decision", "where does this spec go", "update the README", "draft the project CHANGELOG", "comment-the-why", or "write a design.md". Not for repository docs scaffolding (use init), conducting research (use research), technical reports (use write-report), or API-surface comments.
metadata:
  version: 3.1.0
---

# document

Author and file project documentation so every artifact lands at exactly one canonical location with the right template. Success: a reader or agent can always answer "where does this go?" without guessing.

## Requirements

- POSIX `find`, `sed`, `grep` (BSD or GNU) — the root-doc-sprawl check below.

## Artifact types (MECE)

Every documentation artifact answers exactly one question; never let one artifact try to answer two.

| Artifact | Question answered | Lifespan | Template | Canonical location |
|----------|------------------|----------|----------|--------------------|
| **research** | *What did I find* — facts, sources, comparisons (pre-decision) | Topic-scoped; superseded as evidence evolves | `templates/research.md` | `docs/research/{slug}.md` |
| **references** | *What does this external source say* — verbatim static archive of a third-party document | Permanent snapshot; never edited after capture | `templates/references.md` | `docs/research/references/{slug}.md` |
| **spec** | *What* is this work and are the requirements clear? | Work-scoped, one-shot | `templates/spec.md` | `docs/exec-plan/active/{slug}/spec.md` |
| **plan** | *How* to implement (steps, files, order) | Work-scoped; body immutable only after explicit finalization | `templates/plan.md` | `docs/exec-plan/active/{slug}/plan.md` |
| **decision** | One expensive-to-reverse *cross-cutting* decision | Permanent topic anchor; edited in place, each change logged in the ADR's `## Changelog` | `templates/adr.md` | `docs/decisions/ADR-NNN-{topic}.md` |
| **rule** | A standing convention (ongoing constraint, not work-scoped) | Alive as long as the convention holds | `templates/rule.md` | `docs/rules/{topic}.md` |

## Routing

Pick the primary question a task answers and route by that row — the ontology table above for the six ontology artifacts, or the table below for repo-level artifacts and standing conventions. Create a `decision` artifact only when the user explicitly asks to record a decision or write an ADR; otherwise keep research, specs, plans, and rules in their own lanes and note decision candidates inside that artifact.

| Task | Read | Author with |
|------|------|--------------|
| Record a cross-cutting decision / write an ADR | `references/adr.md` | `templates/adr.md` |
| Write or update the repository README | `references/readme.md` | `templates/readme.md` |
| Write the project-level CHANGELOG / release notes | `references/changelog.md` | `templates/changelog.md` |
| Decide how to comment code (comment-the-why) | `references/inline-comments.md` | — |
| Write or update `design.md` / design tokens | `references/design.md` | `templates/design.md` |
| Map the system (`architecture.md`) | see architecture.md section below | `templates/architecture.md` |
| File research, a spec, a plan, a rule, or an archived source | ontology table above | matching `templates/*.md` |

No documentation task should dead-end here — every repo-level artifact and every ontology artifact has an exit row.

**References vs research:** a references file is a verbatim static copy of an external document; a research file is your own synthesis. Never merge them.

**Rule vs ADR:** the *what to do* goes in a rule. Load `references/adr.md` only when the user explicitly asks for an ADR or decision record.

### Root-doc-sprawl check

Loose `.md` files accumulate at the repo root instead of filing into the ontology above. Count them, excluding the conventional set:

```bash
find . -maxdepth 1 -name '*.md' | sed 's|^\./||' | grep -viE '^(readme|agents|claude|changelog|contributing|license|code_of_conduct)\.md$' | wc -l
```

More than 3 is a signal to investigate the loose documents and propose their canonical `docs/` paths before adding more. Do not move existing documents without an explicit request.

## Decision boundaries

```
research (facts found)  |  decision/ADR (explicit record request)  |  plan (implementation built)
```

Research collects evidence and presents options; it does not decide. A plan sequences implementation; it may mention trade-offs without spawning a decision record. An ADR is an explicit destination, not an automatic distillation step. When routing is unclear, ask which artifact the user wants: evidence, a recorded decision, or implementation sequencing.

## `docs/` layout

```
docs/
├── research/                     # Fact collection — sources, comparisons (pre-decision)
│   ├── {slug}.md
│   └── references/               #   verbatim static archives of external documents
│       └── {slug}.md
├── exec-plan/
│   ├── active/{slug}/             #   spec.md + plan.md while work is in progress
│   └── archive/{slug}/            #   same folder, moved here when done/discarded/superseded
├── decisions/                     # Cross-cutting ADRs — permanent, never deleted
│   ├── README.md                  #   ADR index + lifecycle reference
│   └── ADR-NNN-{topic}.md
├── rules/
│   └── {topic}.md
└── architecture.md                # Living system map — see architecture.md section below
```

Scratch drafts live outside `docs/` and are not git-canonical. Finalizing a draft means **moving** it into `docs/` at the correct path, then deleting the scratch source.

## Lifecycle — spec and plan

```
spec drafted (scratch) → MOVE → docs/exec-plan/active/{slug}/spec.md
plan drafted (scratch) → MOVE → docs/exec-plan/active/{slug}/plan.md
                                  FINALIZE only when the user explicitly adopts the immutable-plan contract
work done / discarded / superseded → add status: done|discarded|superseded (+ superseded-by: {slug} when applicable) → MOVE active/{slug}/ → archive/{slug}/
user explicitly requested a decision record → create/update docs/decisions/ADR-NNN-{topic}.md (references/adr.md)
```

**Lifecycle = folder position.** A plan is active or archived by where its folder lives, never by a status field alone; move the whole `{slug}/` folder, never split spec and plan.

**Supersede timing:** when creating a superseding plan-B, archive plan-A in the same action, before beginning plan-B's execution.

**Finalized-plan contract:** a working plan remains editable after commits. Set `finalized: true` only when the user explicitly adopts its body as immutable; from then, a scope change gets a new slug and the old plan's frontmatter is updated to `status: superseded` + `superseded-by: {new-slug}`. Only the finalization and lifecycle frontmatter changes after finalization.

## Slug naming

Format: `{kebab-description}` — lowercase, hyphens only, no date prefix, no issue number. The folder (or filename) is the authoritative slug; a frontmatter `slug` that disagrees with it is an error.

## `architecture.md`

Answers "how is this system put together?" for someone who just opened the repo: an annotated directory tree, component boundaries, a cross-cutting-decisions index (links to ADRs, not restatements), and the one or two data/control flows that matter most.

Update it whenever a change moves a component boundary or a new cross-cutting decision lands — not on every commit. Staleness signal: its directory tree or ADR index no longer matches reality. Keep it a map: if a section starts duplicating an ADR body, replace the duplication with a link.

## Trivial exemptions — no spec/plan required

- Typo, comment, or wording fixes
- Lint- or format-only changes
- Dependency patch-version bumps (`x.y.Z`)
- Behavior-preserving renames

## Anti-patterns

- Implicitly creating or scheduling an ADR because research, a plan, or a durable choice mentions a decision → keep the original artifact in its lane and create an ADR only when the user explicitly asks to record one.

## Verification

- [ ] Each artifact answers exactly one question (an ontology row or a routing-table row) — none dead-ended
- [ ] Any ADR was created only from an explicit ADR / decision-record request
- [ ] Completed/discarded work moved `active/` → `archive/` with a `status` line
- [ ] `architecture.md` reflects the latest component boundaries and decisions, or was flagged stale
- [ ] References files hold verbatim source content, not synthesis
- [ ] Slug matches its folder/filename exactly
- [ ] Root-doc-sprawl check run when loose root docs are suspected; any relocation was proposed and explicitly requested before moving files
