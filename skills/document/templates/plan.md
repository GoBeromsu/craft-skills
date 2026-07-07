---
slug: {kebab-description}         # must match the folder name exactly
date: YYYY-MM-DD
author: {name or agent}
spec: {slug of the corresponding spec, or "none"}
status: active                     # active | done | discarded | superseded-by: {new-slug}
superseded-by:                     # fill only when status: superseded-by
---

# Plan: {Feature or Task Title}

<!--
PURPOSE: Sequence the implementation — HOW to build what the spec requires.
This file answers "how?" — concrete steps, files to change, and order.
Do not create a separate ADR from this plan unless the user explicitly asks to
record a decision.

IMMUTABILITY: This file is finalized on the first git commit that includes it.
From that point the body below is immutable. Only the frontmatter `status` and
`superseded-by` lines may change post-finalize.
-->

## Approach

<!-- One paragraph: the core strategy. Why this approach over obvious alternatives. -->

## Steps

<!-- Ordered, actionable steps. Each step should be completable independently.
     Use checkboxes so progress is trackable. -->

- [ ] 1. {Step description — specific file or command}
- [ ] 2.
- [ ] 3.

## Files affected

<!-- List every file that will be created, modified, or deleted. -->

| File | Change type | Notes |
|------|-------------|-------|
| `{path}` | create / modify / delete | |

## Risks and mitigations

<!-- Identify what could go wrong and how to handle it. -->

| Risk | Mitigation |
|------|------------|
| | |

## Verification

<!-- How to confirm the implementation is correct. -->

- [ ]
- [ ]

## Decision notes

<!--
Optional: note implementation trade-offs that matter while executing this plan.
If the user explicitly asked to record a decision, link the ADR here; otherwise
keep trade-offs in this plan.
-->

- {Decision note or ADR link, if explicitly requested}
