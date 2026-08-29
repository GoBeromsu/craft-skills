# Bad-UX audit guide

Audit observable interaction and design consequences, not taste, motive, legality, or comprehensive conformance.
Use one primary family per finding so prioritization remains actionable.

## Evidence record

Record each finding with:

- observation: concrete source or rendered fact, without a conclusion hidden inside it.
- evidence_domain: `source`, `rendered`, `research`, or `reported`.
- evidence: path, capture, participant result, or reproducible location.
- affected_user, task, state, viewport, and input: the scope of the observed consequence.
- primary_family: one family from this reference.
- secondary_tags: optional contextual frameworks, not extra primary classifications.
- consequence: blocking, harmful/error-prone, costly/confusing, or minor friction to the user’s task.
- severity: priority assigned from that consequence, not from visual dislike or an automated score.
- confidence: high, medium, or low based on evidence quality and representativeness.
- recommendation: a bounded improvement that preserves known constraints.
- verification: evidence that would confirm or revise the recommendation.
- limitation: what the evidence cannot establish.

Severity describes the consequence if the observation is true.
Confidence describes how strongly the evidence supports it; low confidence requires narrower language or more evidence.

## Primary families

| Family | Record when evidence shows | Guard against |
|---|---|---|
| Feedback and system status | A meaningful action, progress, result, or failure lacks timely understandable feedback. | Do not require feedback for imperceptible or intentionally deferred work without task evidence. |
| Mental-model match and signifiers | Labels, controls, or visible consequences conflict with a supported user model or leave an available action unclear. | Do not substitute the reviewer’s personal model for user/context evidence. |
| User control, prevention, and recovery | Users cannot safely cancel, undo, prevent a foreseeable error, or recover with understandable guidance. | Do not label an irreversible consequence defective when the task necessarily requires it and consequences are clear. |
| Choice and cognitive load | Choice structure or required recall plausibly impedes a defined task. | Do not remove needed choices or explanation merely to reduce screen density. |
| Target acquisition and motor access | Target placement, size, spacing, or interaction demand impedes the observed input method. | Do not infer touch failure from a desktop screenshot or prescribe one universal size. |
| Perceptual organization and hierarchy | Grouping, prominence, or reading sequence obscures task-relevant relationships. | Do not treat a different visual style as a hierarchy defect without task evidence. |
| Consistency and standards | Similar actions/states behave or appear differently without a contextual reason, or an incumbent/platform convention is broken. | Do not enforce convention where a deliberate, explained domain distinction exists. |
| Accessibility and adaptability | Evidence shows a barrier in keyboard, focus, non-color distinction, zoom/reflow, motion, or assistive-technology experience. | Do not claim WCAG failure or complete accessibility coverage from a local observation. |
| Flow fitness and human-centered value | The observed flow adds avoidable work or fails a defined user need/context. | Do not infer the intended task, value, or user population without research or product evidence. |
| State and responsive resilience | A meaningful empty, error, loading, disabled, focus, viewport, or input state loses clarity or usable continuity. | Do not infer unobserved states from the default view. |

## Agency, consent, disclosure, and trust observations

Record forced action, asymmetric accept/decline presentation, preselection, obstructed reversal, hidden material disclosure, or a mismatch between stated action and visible consequence as an observable user-control/recovery finding.
Use consistency or status as a secondary tag when it adds context.
Record a missing visible disclosure only when established requirements say it should be present.
Do not infer manipulation, intent, consent validity, fraud, privacy compliance, legal sufficiency, or security posture.
Hand those conclusions to legal, privacy, or security owners with the evidence record.
A visually symmetric choice without further evidence is a near miss, not a trust finding.

## False-positive guards

Do not report a defect when evidence is limited to unsupported source syntax, an unverified screenshot, a hypothetical state, a personal preference, or a framework name without a task consequence.
Do not collapse observation and recommendation: state the observed fact first, then the inference, then the change.
Do not remove explanatory copy to improve minimalism unless hierarchy, action labels, signifiers, recognition, and progressive disclosure become stronger; never replace meaning with mystery icons.
Do not use audit output to certify usability, accessibility, privacy, security, consent, or legal compliance.
