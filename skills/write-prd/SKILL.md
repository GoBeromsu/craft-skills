---
name: write-prd
description: Authors product requirements documents by filling a provided or packaged PRD template from product context, with One Pager, scope, metrics, rollout, open issues, and history kept coherent. Use when asked to "write a PRD", "fill this PRD template", "turn this product idea into a PRD", "complete the product requirements document", or "PRD 작성해줘". Not for ADRs, READMEs, changelogs, or docs-ontology artifacts (use `document`), or one-off technical reports (use `write-report`).
metadata:
  version: 1.1.0
---

# write-prd

Fill a PRD template into a decision-ready product requirements document. Success means the
document explains why the product work matters, who it serves, what is in and out of scope,
how success is measured, what remains unknown, and what the delivery phases are.

## Inputs

Use the richest available source, in this order:

1. A user-supplied PRD template or partially filled PRD.
2. Product notes, meeting notes, tickets, designs, user research, or implementation context.
3. `templates/prd.template.md` as the default frame when no template is supplied.

If the user provides only a rough idea, write a best-effort draft and mark unresolved facts
as Open Issues. Ask one concise question only when the product, user, or intended outcome is
so unclear that any PRD would be misleading.

## Modes

- **New draft** — start from the selected template and fill the sections required by its
  structure and the approved scope that available context supports.
- **Complete draft** — preserve existing filled content, replace placeholders where context
  supports a concrete answer, and turn remaining placeholders into Open Issues.
- **Review draft** — check the PRD for missing problem framing, weak scope boundaries,
  unmeasurable metrics, hidden decisions, and stale placeholders; patch the draft when the
  user asked for completion rather than a review-only response.

## Review signals

Let a user-provided template and approved scope determine section order, depth, and required
content. For the packaged template, review these signals rather than imposing a fill sequence:

- **Document information** identifies the draft and its accountable roles without invented names.
- **One Pager** frames the problem, intended outcomes, constraints, users, and use cases before
  scope details claim resolution.
- **Scope** makes included work traceable to an objective or use case; record exclusions and
  review points when the selected template or approved scope calls for them.
- **Design and technical considerations** link existing decisions and turn unresolved design,
  API, data, security, infrastructure, or AI questions into owned Open Issues.
- **Success metrics** use measurable thresholds or a baseline-capture method instead of vague
  improvement language.
- **GTM and phasing** state customer value, release path, status, ownership, timing, and blockers
  at the smallest useful level of detail.
- **Open Issues, Q&A, Decision Log, and Change History** expose uncertainty and material
  decisions rather than hiding them in prose.
- **Checklist** marks only sections with concrete PRD content.

## Authoring Principles

Use the packaged template as the artifact frame, not as reader-facing instruction. Internal
authoring guidance belongs in this skill:

- Let a user-provided template and approved scope determine the required sections and their
  order; use the packaged template as the default frame, not a mandatory sequence.
- Write the number of Objectives needed to express distinct approved outcomes; consolidate
  overlap rather than applying a fixed cap.
- Treat a PRD as a decision document, not a feature list: it must explain why the work
  matters, who uses it, what success means, and what will not be built.
- Where scope exclusions are part of the selected template or approved scope, make them specific
  enough to prevent creep and state the reason plus a review point.
- Write Success Metrics with numbers wherever possible: time, ratio, count, usage,
  conversion, error rate, pilot threshold, or an explicit baseline-capture method.
- Move unknowns to Open Issues with an owner role and due date or review point instead of
  inventing answers.

## Output Rules

- Preserve the selected template's section order and table shapes; a user-provided template and
  approved scope override the packaged default.
- In the final PRD, remove instructional text such as "what to fill" prompts, example
  blocks, writing-order guides, and beginner principles unless the user asks for a teaching
  template. The deliverable is the filled PRD, not the blank template or the skill's
  authoring notes.
- Write in the language of the selected template or the user's request. For a Korean PRD
  template, write Korean prose while preserving product, metric, and system names that are
  normally English.
- Prefer concrete scope and evidence over polished but unsupported claims.
- Use `TBD` only in document metadata. In body sections, unresolved facts belong in Open
  Issues with `Open` status.
- Do not present product decisions as final when the source material only implies them.
  Phrase them as assumptions or Open Issues.
- If writing into a repository, save the PRD at the user's requested path; otherwise return
  a single Markdown PRD.

## Quality Check

Before finishing, verify:

- The Problem explains the user pain and business/operational cost before naming features.
- Objectives, Features In, Success Metrics, and Feature Timeline are mutually consistent.
- Features Out is specific enough to prevent MVP scope creep when the selected template or approved scope includes it.
- Metrics are measurable, or the PRD states how they will be measured.
- Design and technical unknowns are not buried in prose.
- Open Issues have an owner role, due date or review point, and status.
- Change History and Decision Log are present when the PRD is meant to be shared or reviewed.

## Anti-patterns

- Leaving authoring guidance as PRD template sections → encode the guidance in this skill
  and keep the template to the artifact sections a reader should see.

## Files

- `templates/prd.template.md` — default PRD frame with One Pager, PRD body, checklist,
  Decision Log, and Change History.
