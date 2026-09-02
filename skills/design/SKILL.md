---
name: design
description: Owns canonical DESIGN.md artifacts and evidence-first UX/UI judgment for coherent product design roots. Use when requests ask to define interface direction; choose type, color, spacing, or motion; audit a user journey; establish design tokens or state specifications; redesign information hierarchy; review mental models; evaluate rendered states; prioritize bad UX; improve an interaction; or turn accessibility and usability findings into an improvement plan. Not for frontend rendering and architecture or generic documentation — use frontend or document; live-page operation and automated evidence collection remain mechanics-owned.
metadata:
  version: 1.1.0
---

## Goal

Review a PR or rendered user journey against seven named UX principles so an identified operator can complete one primary action without an evidenced interaction failure.
Succeed when the review names each failed principle from a rendered screen or interaction, records reproducible evidence, and recommends the smallest correction.

## Output contract

Deliver the completed [UX review template](templates/ux-review.md) as the review artifact.
Include `primary_operator`, `primary_action`, `evidence`, `screens_checked[]`, `violated_principles[]`, and `recommendation`.
Treat a verdict without screenshot or interaction evidence as a static review rather than a completed interaction review.
List every checked screen when no principle is violated.

## Routing

| Request | Owner and response |
|---|---|
| Material choice changes perception, understanding, decision-making, task completion, accessibility experience, or reusable visual or interaction language | Use this skill for bounded design judgment. |
| Rendering, framework or component architecture, state placement, folders, API boundaries, or faithful implementation of established decisions | Keep `frontend` autonomous. |
| Navigation, interaction automation, screenshots, accessibility snapshots, computed styles, or visual diffs | Use the `browser` skill to capture evidence, then return to this skill for judgment. |
| General documentation or information architecture without design judgment | Use `document`. |

Treat the repository root as one ownership root only when its deployables deliberately share one design system.
Use each app root independently when deployable apps diverge.
Do not create parent or child inheritance, a workspace index, or multiple `DESIGN.md` files for one coherent root.

## UX review

1. Identify the primary operator and the one primary action that completes the task.
2. Walk [the seven UX review principles](references/ux-principles.md) and perform each applicable click-and-observe check.
3. Capture screenshots or interaction transcripts through the craft `browser` skill for web surfaces.
4. Fill [the UX review template](templates/ux-review.md) with each checked screen, every violated principle, its screen evidence, reproducible steps, the smallest fix, and a recommendation.
5. Return a static review with `evidence: none` and lower confidence when browser access or rendered evidence is unavailable.

## Artifact lifecycle

Keep one root artifact in uppercase `DESIGN.md`.
Record product intent, principles, tokens, type, layout, primitives, interaction, motion, accessibility expectations, verification, and dated accepted debt in [the canonical template](templates/DESIGN.md).
Treat colors, elevation or depth, and shapes as token decisions and explain their intended perceptual role where it affects use.
Describe component primitives with all required states, `data_bearing`, same-state references, and a `non_color_cue` for every state.
Add selected, read-only, warning, success, permission-limited, offline, or destructive-confirmation states when product semantics expose them.
Record unknown legacy content under its nearest appropriate canonical section rather than dropping it.
Retire a lowercase legacy path only after a preservation ledger confirms every semantic item is preserved, transformed, merged as an equivalent duplicate, or removed with owner approval.
Update `DESIGN.md` in the same change as a material token, primitive, state, or interaction decision.
Compare the implemented primitive inventory with the artifact during a material audit and record or remove every orphan.

## Evidence and judgment

Label each claim as an observation, inference, recommendation, or limitation.
Gather source observations and rendered observations separately and name state, viewport, input mode, and evidence limitations.
Apply [frameworks](references/frameworks.md) to frame a decision rather than claim universal compliance.
Audit concrete interaction evidence with [bad-UX guidance](references/bad-ux.md), select one primary family, and prioritize it by user and task consequence.
Prioritize a finding as blocking, harmful or error-prone, costly or confusing, or minor friction.
Record confidence separately from severity and narrow a low-confidence recommendation to the available evidence.
Record observable asymmetry or missing visible information for agency, consent, disclosure, or trust concerns without assigning motive.

## Requirements

Use Python 3.9 or later only when running the optional bounded checker described in [checker guidance](references/checker.md).
Probe the installed interpreter with `python3 --version` before running the checker.
Run the checker against the selected ownership root when Python is available and report omitted checks as not requested, malformed evidence as invalid, missing or ambiguous evidence as insufficient, and diagnostics as observed bounded violations.
Keep screenshots and manual rendered judgment separate from a checker pass.

## Handoffs

Give `frontend` the design decision, target user, task, context, token or primitive or state specification, non-color cue, responsive or accessibility expectation, accepted debt, and verification evidence.
Give `browser` the target route, role, interaction, and capture request without prescribing its mechanics.
Escalate normative accessibility conformance to accessibility engineering and legal, privacy, or security obligations to their applicable owner.

## Anti-patterns

- Judge a UX change from the PR description alone → inspect the affected screen and interaction before reaching a verdict.
- Name a principle without a screen → attach a screenshot path or interaction transcript reference and reproducible steps.
- Recommend a redesign when one check fails → make the smallest fix that makes the failed check pass.
- Remove explanatory copy to make an interface cleaner → strengthen hierarchy, action labels, signifiers, recognition, and progressive disclosure first.
- Treat design as a gate for ordinary frontend implementation → invoke design only for material UX or UI judgment and return implementation ownership to frontend.
- Call source code or a screenshot proof of user success or conformance → record its domain and limitation and obtain relevant rendered or manual evidence.
- Ship stock framework values or one-off literals outside the named token system → register the deliberate design decision or replace it with an incumbent token.
- Assign multiple primary families to one audit finding → choose the dominant user and task consequence and use secondary tags only for context.
- Call an observable consent asymmetry deceptive or illegal → record the interaction and hand intent, legal, privacy, and security conclusions to their owners.

## Non-goals

Do not implement frontend components, rendering, architecture, or state management, because `frontend` owns implementation.
Do not write or revise product copy, because the product or copywriting owner owns wording.
Do not operate a live page or automate evidence collection without the `browser` skill.
Do not claim accessibility, legal, privacy, or security conformance from this review.

## Failure modes

Ask which role performs the task before judging when the primary operator is ambiguous.
Deliver a static review with `evidence: none` and lower confidence when browser access, screenshots, or interaction transcripts are unavailable.
Report missing routes, credentials, or environments as evidence limitations and avoid guessing a pass or failure.
Return the checked screens and partial findings when only part of the journey is reachable.
