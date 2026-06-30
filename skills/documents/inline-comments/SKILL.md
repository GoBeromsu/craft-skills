---
name: inline-comments
description: '"how should I comment this code", "write a code comment", "comment the why", "should I add a comment here" — apply the comment-the-why convention for inline code comments. Loaded on demand by the documents waypoint.'
---

# inline-comments

Apply the inline-comment convention: comment the **why**, not the what. This is a standing convention, not an artifact — there is no template, only the rule and its boundaries.

The code already shows *what* it does. A comment earns its place only when it carries context the code cannot: why this approach, why this constraint, why this non-obvious choice.

## When to add a comment

- **The why behind a non-obvious choice** — why this algorithm over the obvious one, why this order matters, why a slower path is taken on purpose.
- **A constraint or gotcha** — an external API quirk, a boundary condition, a workaround for an upstream bug, a value that must stay in sync with something elsewhere.
- **A pointer to the decision** — when the reason is cross-cutting and lives in an ADR, link it: `// See ADR-NNN for rationale`. The comment carries the local "watch out"; the ADR carries the full why.

## When NOT to add a comment

- **Restating the code** — `// increment i` over `i++` is noise that goes stale.
- **Compensating for an unclear name** — if a comment is needed to explain what a variable or function *is*, rename it instead. A good name removes the comment.
- **Dead code or commented-out blocks** — delete them; git remembers.
- **Change narration** — `// changed from X` belongs in the commit message or CHANGELOG, never in the code.

## The test

Before writing a comment, ask: *"Does this tell the reader something the code cannot?"*
- Yes → it is a why-comment; keep it.
- No → either delete it, or fix the code (rename, extract) so the comment is unnecessary.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "More comments make code clearer." | What-comments restate the code and rot when the code changes. Clarity comes from naming and structure; comments are reserved for the why. |
| "I'll comment what this line does." | The line already says what it does. Comment why it does it this way, or say nothing. |
| "I'll leave the old version in a comment, just in case." | Git holds history. Commented-out code is dead weight that misleads readers. Delete it. |
| "A comment is faster than renaming." | A comment explaining what a name means is a renamed-variable waiting to happen. Rename; the comment disappears. |

## Red flags

- A comment that paraphrases the line below it
- A comment explaining what a poorly named variable holds (rename instead)
- Commented-out code left in the file
- A comment narrating a past change ("used to be X")
- A cross-cutting rationale duplicated inline instead of linked to its ADR

## Verification

- [ ] Every comment tells the reader something the code cannot
- [ ] No comment merely restates the code
- [ ] Names carry meaning; comments are not compensating for unclear naming
- [ ] No commented-out code or change-narration comments
- [ ] Cross-cutting rationale links to its ADR rather than duplicating it
