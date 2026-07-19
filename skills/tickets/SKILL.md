---
name: tickets
description: 'Executes a team work ticket delivered as a GitHub issue: pulls it with `gh issue view`, treats its 최소 요구, 완료 조건, and 절대 금지 sections as the entire scope contract, defers to the target repo''s own AGENTS.md for every branch/commit/PR/security rule, and proves each completion criterion with real evidence before a PR opens. Use when someone hands over a ticket number and says something like "oss-hub 티켓 #12 진행해줘", "pick up issue #7", "work the next open ticket", or "implement this GitHub issue for me". Not for authoring or scoping the ticket itself — that is the issue author''s job; not for branch/commit/PR mechanics — that is `git` and the repo''s own AGENTS.md.'
metadata:
  version: 1.0.0
---

# tickets

Turns a GitHub-issue work ticket into a scoped, verified pull request without expanding the ticket's scope or duplicating the host repo's own conventions.
Success looks like: the PR closes exactly what the ticket's contract asks for, every completion-criterion line item is demonstrated before the PR opens, and no file outside the ticket's forbidden boundary is touched.

## Workflow

1. Collect the ticket: `gh issue view <number>` (add `--repo <owner>/<repo>` when not already inside that repo's clone).
2. Parse the contract — three sections are the sole source of truth for scope, in order of what they gate:
   - 최소 요구 (기능) — the minimum functional requirement; implement no more and no less.
   - 완료 조건 (기능 검증) — the checklist that must be demonstrated, not merely asserted, before the PR opens.
   - 절대 금지 (이 티켓의 경계) — files and behaviors this ticket must not touch.
   When a 선행 의존성 (preceding dependency) section names an unmet dependency, stop and report it instead of starting partial work.
3. Before writing any code, read the target repo's AGENTS.md (root and any nested AGENTS.md files) for branch naming, commit style, PR flow, and security rules — this skill never restates those, so drift between the skill and the repo's real rules cannot happen.
4. Implement only what the minimum-requirement section calls for; treat schema changes or adjacent features as belonging to their own designated ticket even when fixing them now would be convenient.
5. Respect the forbidden-boundary section literally — zero edits to any file or area it names.
6. Work through the completion-condition checklist one item at a time, driving the real behavior (run the test, exercise the screen or flow) before checking it off; do not open the PR on an unverified checklist.
7. Open the PR following the repo's own AGENTS.md flow. On a public repo, run its hygiene/secret-check script first if one exists, and keep commit messages, the PR body, and any comments free of secrets, real names, and personal paths.
8. Once the PR is open, move the ticket's project-board card to "In Review".

## Escape hatches

- A named preceding dependency is unmet → report exactly which one and stop; do not begin partial implementation.
- The contract is silent or ambiguous on a point the implementation needs → ask the user rather than inferring from unrelated docs, code comments, or a similar past ticket; the ticket body is self-contained by design.

## Requirements

- `gh` — issue view, PR creation, and project-board card moves.
- `git` — branch and commit mechanics, per the target repo's own AGENTS.md and the `git` skill.

## Anti-patterns

- Adding an "improvement" the minimum-requirement section never named → leave it out of this PR; file or point to a separate ticket instead.
- Inferring a missing requirement from external documentation, code comments, or memory of a similar ticket → the ticket body is the only source; ask when it is silent.
- Checking off a completion-criterion item without having driven the behavior it describes → run the test or the flow first, then check the box.
- Restating branch/commit/PR conventions inside this skill → that duplication drifts from the repo's real rules; always read the repo's own AGENTS.md instead.

## Verification

- [ ] Ticket's 최소 요구, 완료 조건, and 절대 금지 sections read before any code change.
- [ ] Preceding dependency, if named, checked; an unmet one is reported without starting work.
- [ ] The target repo's AGENTS.md (root and nested) read before the first edit.
- [ ] No file outside the forbidden-boundary section touched.
- [ ] Every completion-criterion item demonstrated with real evidence, not asserted.
- [ ] PR opened per the repo's own flow; project-board card moved to In Review.
- [ ] Public repo: commit/PR/comment text carries no secret, real name, or personal path; the repo's own check script ran first when one exists.
