---
name: design
description: Owns canonical DESIGN.md artifacts and evidence-first UX/UI judgment for coherent product design roots. Use when requests ask to define interface direction; choose type, color, spacing, or motion; audit a user journey; establish design tokens or state specifications; redesign information hierarchy; review mental models; evaluate rendered states; prioritize bad UX; improve an interaction; or turn accessibility and usability findings into an improvement plan. Not for frontend rendering and architecture or generic documentation — use frontend or document; live-page operation and automated evidence collection remain mechanics-owned.
metadata:
  version: 1.0.0
---

# Design

Create durable design decisions that help identified users complete a defined task in a stated context.
Succeed when the ownership root has one current `DESIGN.md`, recommendations distinguish evidence from inference, and implementation receives decisions that can be verified in relevant rendered states.

## Routing

| Request | Owner and response |
|---|---|
| Material choice changes perception, understanding, decision-making, task completion, accessibility experience, or reusable visual/interaction language | Use this skill for bounded design judgment. |
| Rendering, framework/component architecture, state placement, folders, API boundaries, or faithful implementation of established decisions | Keep `frontend` autonomous. |
| Navigation, interaction automation, screenshots, accessibility snapshots, computed styles, or visual diffs | Hand mechanics to browser/testing; request normalized evidence. |
| General documentation or information architecture without design judgment | Use `document`. |

Treat the repository root as one ownership root only when its deployables deliberately share one design system.
For divergent deployable apps, use each app root independently.
Do not create parent/child inheritance, a workspace index, or multiple `DESIGN.md` files for one coherent root.

## Workflow

1. Establish the ownership root, product, users, task, context, incumbent system, constraints, and decision to make.
2. Gather source observations and rendered observations separately, naming state, viewport, input mode, and evidence limitations.
3. Inspect the existing `DESIGN.md` before changing direction; preserve unknown content during migration and resolve contradictory roots with the product owner.
4. Create or update the root `DESIGN.md` from [the canonical template](templates/DESIGN.md), retaining its named literal tokens, eleven H2 headings, and exact primitive/debt grammar.
5. Apply the durable frameworks and their limits in [frameworks](references/frameworks.md); use them to frame a decision, not to claim universal compliance.
6. Audit concrete interaction evidence with [bad-UX guidance](references/bad-ux.md), select one primary family, and prioritize by user/task consequence and confidence.
7. State a recommendation, alternatives rejected when material, expected states, accepted debt, and re-verification evidence.
8. When Python is available, run the optional [bounded checker](references/checker.md) against the selected ownership root; report omitted checks as not requested, malformed evidence as invalid, missing or ambiguous evidence as insufficient, and error diagnostics as observed bounded violations. A performed pass means only no listed violation in declared scope; keep screenshots and manual rendered judgment separate.
9. Hand tokens, primitives, state expectations, and acceptance evidence to `frontend`; hand capture mechanics to browser/testing.

## Artifact lifecycle

Keep one root artifact in uppercase `DESIGN.md`.
Record product intent, principles, tokens, type, layout, primitives, interaction, motion, accessibility expectations, verification, and dated accepted debt in the template’s order.
Treat colors, elevation/depth, and shapes as token decisions; explain their intended perceptual role where it affects use.
Describe component primitives with all required states, `data_bearing`, same-state references, and a `non_color_cue` for every state.
Add selected, read-only, warning, success, permission-limited, offline, or destructive-confirmation states when the product semantics expose them; the required baseline is a floor, not a complete state inventory.
Record unknown legacy content under its nearest appropriate canonical section rather than dropping it.
Retire a lowercase legacy path only after a preservation ledger confirms every semantic item is preserved, transformed, merged as an equivalent duplicate, or removed with owner approval.
Update `DESIGN.md` in the same change as a material token, primitive, state, or interaction decision.
During a material audit, compare the implemented primitive inventory with the artifact and record or remove every orphan instead of trusting a stale catalog.

## Requirements

- The Markdown workflow has no external dependency. The optional checker requires Python 3.9 or later, uses only the standard library, and is probed with `python3 --version`; official source: [Python documentation](https://docs.python.org/3/). Recheck the documented support boundary, checker tests, and package evals when the selected Python major changes.

## Evidence and judgment

Label each claim as an observation, inference, recommendation, or limitation.
Do not infer intent, task fitness, aesthetic quality, usability, accessibility conformance, or legal compliance from source or screenshots alone.
When rendered evidence is available, cover the affected task’s meaningful states, viewport classes, keyboard/pointer input, focus treatment, reduced-motion behavior, and zoom/reflow where relevant.
When evidence is unavailable or ambiguous, report what is missing and request a rendered/manual audit rather than guessing a defect or pass.

Prioritize a finding by the consequence to the affected user completing the task: blocking, harmful/error-prone, costly/confusing, or minor friction.
Record confidence separately from severity; low confidence narrows the recommendation or requests evidence.
For agency, consent, disclosure, or trust concerns, record observable asymmetry or missing visible information without assigning motive; hand legal, privacy, and security conclusions to their owners.

## Handoffs

Give `frontend` the design decision, target user/task/context, token or primitive/state specification, non-color cue, responsive/accessibility expectation, accepted debt, and verification evidence.
Ask browser/testing for captures or normalized accessibility evidence; do not prescribe their tooling.
Escalate normative accessibility conformance to accessibility engineering and legal/privacy/security obligations to the applicable domain owner.

## Anti-patterns

- Removing explanatory copy to make an interface cleaner → strengthen hierarchy, action labels, signifiers, recognition, and progressive disclosure first; never replace meaning with mystery icons.
- Treating design as a gate for ordinary frontend implementation → invoke design only for material UX/UI judgment and return implementation ownership to frontend.
- Calling source code or a screenshot proof of user success or conformance → record its domain and limitation, then obtain relevant rendered/manual evidence.
- Shipping stock framework values or one-off literals outside the named token system → register the deliberate design decision or replace it with an incumbent token.
- Assigning multiple primary families to one audit finding → choose the dominant user/task consequence and use secondary tags only for context.
- Calling an observable consent asymmetry deceptive or illegal → record the interaction and hand intent, legal, privacy, and security conclusions to their owners.
