---
name: write-prd
description: Authors product requirements documents by filling a provided or packaged PRD template from product context, with One Pager, scope, metrics, rollout, open issues, and history kept coherent. Use when asked to "write a PRD", "fill this PRD template", "turn this product idea into a PRD", "complete the product requirements document", or "PRD 작성해줘". Not for ADRs, READMEs, changelogs, or docs-ontology artifacts (use `document`), or one-off technical reports (use `write-report`).
metadata:
  version: 1.0.0
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

- **New draft** — start from the selected template and fill every section that can be
  supported by the available context.
- **Complete draft** — preserve existing filled content, replace placeholders where context
  supports a concrete answer, and turn remaining placeholders into Open Issues.
- **Review draft** — check the PRD for missing problem framing, weak scope boundaries,
  unmeasurable metrics, hidden decisions, and stale placeholders; patch the draft when the
  user asked for completion rather than a review-only response.

## Fill Order

1. **Document information** — fill title, author/team roles, PM epic, state, approver, and
   sign-off. Unknown role assignments become Open Issues; do not invent names.
2. **One Pager** — write Overview, Problem, Objectives, Constraints, Persona, and Use Cases
   before feature details. Keep Objectives to the few outcomes that would prove the work
   mattered.
3. **Scope** — split Features In and Features Out with explicit reasons. Each included
   feature maps to at least one objective or use case; each excluded feature names the
   future review point or reason it is out of scope.
4. **Design and technical considerations** — reference existing links when present. If a
   design, API, data, security, infrastructure, or AI consideration is unresolved, record it
   as an Open Issue with an owner role.
5. **Success metrics** — prefer numbers, ratios, time limits, adoption counts, conversion
   rates, error rates, or pilot criteria. When no baseline exists, define how the baseline
   will be captured rather than writing vague improvement language.
6. **GTM and phasing** — state the customer-facing value, release channel, rollout stage,
   feature status, owner, date, and blocker notes at the smallest useful level of detail.
7. **Open Issues, Q&A, Decision Log, Change History** — move uncertainty here instead of
   hiding it in prose. Record the first draft as `v0.1` in Change History unless the user
   provides a different version.
8. **Checklist** — mark only sections that have concrete PRD content as done.

## Output Rules

- Keep the template's section order and table shapes unless the user explicitly supplies a
  different template.
- In the final PRD, remove instructional text such as "what to fill" prompts and example
  blocks unless the user asks for a teaching template. The deliverable is the filled PRD,
  not the blank template.
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
- Features Out is specific enough to prevent MVP scope creep.
- Metrics are measurable, or the PRD states how they will be measured.
- Design and technical unknowns are not buried in prose.
- Open Issues have an owner role, due date or review point, and status.
- Change History and Decision Log are present when the PRD is meant to be shared or reviewed.

## Files

- `templates/prd.template.md` — default PRD frame with One Pager, PRD body, checklist,
  Decision Log, and Change History.
