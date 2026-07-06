# adr

Author or update one Architecture Decision Record: a self-complete, MECE record of a single expensive-to-reverse, cross-cutting decision and the rationale behind it. Template: `../templates/adr.md`. Canonical location: `docs/decisions/ADR-NNN-{topic}.md`.

Document the **why**, not the what. Code and rules show what the system does; an ADR preserves the context, constraints, trade-offs, and rejected alternatives that explain why the system is shaped this way.

## When to write an ADR

- Choosing a framework, library, or major dependency
- Designing a data model or schema
- Selecting an auth strategy
- Choosing API architecture (`REST` vs `GraphQL` vs `tRPC`, public contract shape, versioning model)
- Choosing build tools, hosting, or infrastructure
- Any cross-cutting decision that would be costly to reverse

## Do not write an ADR for

- Implementation steps or file-level details (belong in the plan)
- Choices that will be revisited within this same work item
- Trivial configuration values with no architectural consequence

**Decision test:** *"Would a future engineer or agent working on an unrelated feature need to know this?"* Yes → ADR. No, it only affects this feature's implementation details → leave it in the plan.

## Authoring steps

1. Find the next ADR number — scan `docs/decisions/` for the highest `ADR-NNN` and add one. The number is a stable topic anchor, never reused or renumbered.
2. Copy `../templates/adr.md` to `docs/decisions/ADR-NNN-{topic}.md`. The `{topic}` slug is kebab-case, lowercase, hyphens only, no date prefix, no issue number. The filename slug is authoritative; a frontmatter `slug` that disagrees with the filename is an error.
3. Fill every section: frontmatter (`slug`/`date`/`author`/`status`/`references`/`refines`), Status, Date, Context (state requirements and pressures as facts, not preferences), Decision (one choice, specific and unambiguous), Alternatives considered (each option with pros, cons, and the specific reason it was **rejected**), Consequences (Enables / Costs–trade-offs / New constraints).
4. Seed `## Changelog` with `- YYYY-MM-DD: initial decision`.
5. Set `status: Accepted` once the decision is committed (`Proposed` only while still under deliberation).

## ADR lifecycle

```
PROPOSED → ACCEPTED → DEPRECATED
```

An ADR describes the current decision for one topic as a self-complete, MECE record. When the decision changes, edit that ADR body **in place** so it contains only the current decision, then add one line to its `## Changelog`: `- YYYY-MM-DD: what changed`. Do not create ADR replacement chains, coverage matrices, or retired-source tracking — git holds the detailed history. Status is only `Proposed | Accepted | Deprecated`.

## Why there is no "supersede"

An ADR is the self-complete, MECE, current decision for one atomic topic. "Supersede" collapses different relationships that must stay separate:

- **Same decision changed** → edit the ADR body in place and add one line to `## Changelog`; git holds the full history. Do not create a new ADR or chain.
- **More specific sub-decision** → create a separate atomic ADR that `refines:` the broader decision. Both remain current.
- **Different decision that builds on another** → create a separate atomic ADR that `references:` the other decision. Both remain current.
- **"Only clause X changed"** → the ADR was probably not atomic. Split it into atomic ADRs, then update the changed decision in place.

If each ADR is atomic, MECE, and self-complete, supersede chains collapse into in-place edits with `## Changelog` plus `references:` / `refines:` links.

## Plan vs ADR — the boundary

This is the most common filing error. They answer different questions.

| | plan (`docs/exec-plan/`) | ADR (`docs/decisions/`) |
|---|---|---|
| Question | *How* to implement this specific work | *Why* this cross-cutting choice — and what alternatives were rejected |
| Scope | One feature / task (work-scoped) | Cross-cutting — constrains all future work |
| Lifespan | Archivable when work ends | Permanent topic anchor; body edited in place to current decision |
| Body | Immutable after finalize; scope change → new slug | Updated in place; each change is one line in the ADR's `## Changelog` |
| Location | `active/{slug}/plan.md` → `archive/{slug}/` | `docs/decisions/ADR-NNN-*.md` |

### Distill rule

When a plan contains an expensive-to-reverse, cross-cutting choice (framework selection, data model, auth strategy, API shape, infrastructure), distill that choice into a new ADR before or at the time the plan is archived. The plan entry is **not** replaced — the ADR lives alongside it in `docs/decisions/`.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The code is self-documenting." | Code documents what exists; ADRs document why this path won and which paths lost. |
| "We'll document it once the API stabilizes." | Writing the ADR is the first test of the design; unclear rationale usually means the design is not stable yet. |
| "Nobody reads docs." | Future agents, future engineers, and you three months from now read the decision trail when changing the system. |
| "ADRs are overhead." | A 10-minute ADR prevents the same two-hour architecture argument six months later. |
| "Comments go stale." | What-comments go stale; why-comments and ADR rationale stay useful because the historical constraint remains true. |

Document known gotchas inline with a pointer back to the decision: `See ADR-NNN for rationale`.

## Red flags

- A plan and an ADR conflated into one file
- ADRs that overlap (not MECE), or a decision change with no `## Changelog` entry
- An ADR carrying implementation steps or file-level detail (that belongs in the plan)
- A supersede chain, coverage matrix, or retired-source list (use in-place edit + `## Changelog` + `references:`/`refines:`)
- A frontmatter `slug` that disagrees with the filename

## Verification

- [ ] The ADR records exactly one cross-cutting, expensive-to-reverse decision
- [ ] Context states facts and pressures; Decision is one unambiguous choice
- [ ] Each alternative carries a concrete reason it was rejected
- [ ] Consequences cover what it enables, what it costs, and new constraints
- [ ] `## Changelog` has a dated bullet; status is `Proposed | Accepted | Deprecated`
- [ ] Cross-ADR links use `references:` / `refines:`, not supersede chains
- [ ] Filename slug matches the frontmatter slug exactly
