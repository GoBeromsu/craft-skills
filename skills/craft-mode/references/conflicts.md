# Owner decisions

Preserve upstream principle bodies unchanged.
Apply these owner decisions at the existing craft rule owners instead of editing a principle to remove the disagreement.
The decision paragraphs below retain the plan's wording.
File lists identify the affected owners; the listed edits are applied in this branch.

## (a) Shortcut comments

(a) `no-comments` wins over the `craft:` shortcut-comment convention, which is removed from `programming` (its `craft:` comment lines and recorded-mistake line) and from `refactor`'s boy-scout line; a shortcut's ceiling goes to a follow-up note, type, test or lint instead, per `no-comments` step 5.

Affected files:

- `principle-programming/SKILL.md`, the renamed programming owner.
- `refactor/SKILL.md`.
- `principle-programming/references/comments.md`, which owns the no-comments procedure and step 5.

## (b) Package history

(b) Skills and plugins carry no CHANGELOG. History, source credit, and lineage stay in commit messages and git log.

Affected files:

- Repository `AGENTS.md`, the package-history convention.

## (c) Validated TypeScript assertions

(c) TypeScript: judged not a real conflict (both forbid casting unvalidated data and both put parsing at the boundary with the repository's schema library first); the upstream wording governs: `as` only right after validation, exhaustiveness via inline `const _exhaustive: never`. The current iron-list item banning every `as` and the `assertNever` example are replaced by the upstream text.

Affected files:

- `principle-programming/SKILL.md`, the iron list and no-excuse audit.
- `principle-programming/references/typescript.md`.
- `principle-programming/references/typescript/patterns.md`.
- `principle-programming/references/type-system-discipline.md` and `principle-backend/references/boundary-discipline.md`, preserved principle text.

## (d) Declared phase boundaries

(d) `outcome-oriented-execution` always follows the upstream text: for any planned change that declares where temporary breakage is acceptable, intermediate breakage is allowed and verification happens at the declared phase boundaries; `programming`'s "one logical, independently reversible unit" rule and `refactor`'s separate-commit rule each gain one line deferring to the principle in that case.

Affected files:

- `principle-architecture/references/outcome-oriented-execution.md`, preserved principle text.
- `principle-programming/SKILL.md`, the independently reversible unit rule.
- `refactor/SKILL.md`, the separate-commit step and checklist.
- `craft-mode/references/playbooks/refactoring.md`, the refactoring route.

## (e) Inline-comment scope

(e) Comment Sicko's keep-list governs code comments: a comment stays only when it is a legal or license header; non-obvious behavior forced by an external dependency, platform, vendor, or protocol we cannot reshape; `// prettier-ignore` or a lint suppression whose rule is faulty, pedantic, or style-only; a doc comment that defines a public API contract; or an issue or RFC link that explains a constraint code cannot express. ADR-pointer comments are deleted. Decided by the owner on 2026-10-07; this replaces the version the orchestrator adopted by default earlier that day, which also kept ADR pointers.

Affected files:

- `document/references/inline-comments.md`, the rewritten convention.
- `principle-programming/references/comment-sicko.md`, preserved upstream text; the keep-list.
- `principle-programming/references/comments.md`, preserved principle text; the review procedure both files point to.

## (f) Commits and PRs

(f) Upstream wording governs commits and PRs: skills and playbooks commit and open PRs as written.

Affected files:

- `craft-mode/references/playbooks/`, including `opening-a-pr.md`, `babysit.md`, `shipping.md`, `autopilot-full.md`, `autopilot-stack.md` and `multi-phase-plan.md`.
- `correct/SKILL.md`, one commit per mistake class.
- `automate-me/SKILL.md`, commit and open a PR.
- `principle-testing/references/verification-skills.md`, one PR of proven corrections.

## (g) Transcripts

(g) Upstream wording governs transcripts: read the active workspace's transcripts, never other workspaces'.

Affected files:

- `recall/SKILL.md`; its upstream step 2 reads another project's transcripts only when the user asks, and stays as written.
- `reflect/SKILL.md` and `automate-me/SKILL.md`.
- `craft-mode/references/playbooks/session-pickup.md`, `eval.md`, `worktree-cleanup.md` and `orchestrate.md`.
- `craft-mode/references/runtimes.md`, the per-runtime transcript directory.

## (h) Autonomy

(h) craft-mode's upstream Autonomy and Subagents sections govern: delegate in the background by default, take external actions such as team chat, tickets and evals without asking, run wake loops in long-running playbooks, and let reflect file backlog items.

Affected files:

- `craft-mode/SKILL.md`, the Autonomy and Subagents sections and the description.
- `craft-mode/references/never-block-on-the-human.md` and `craft-mode/references/guard-the-context-window.md`, preserved principle text.
- `craft-mode/references/playbooks/autonomous-run.md`, `orchestrate.md` and `babysit.md`, the wake loops.
- `reflect/SKILL.md`, backlog filing.

## (i) Regression tests

(i) The tdd skill's upstream rule governs regression tests: prefer no new test over a bad test, and use the closest executable check when a test is impractical.

Affected files:

- `tdd/SKILL.md`, preserved upstream text.
- `principle-programming/SKILL.md`, the reproducible-defect rule, which defers to tdd.
- `principle-testing/SKILL.md`, whose `no-test` decision and safe fail-before demonstration already agree.

## (j) Runtimes without workers

(j) Packages write nothing for runtimes without workers; bodies assume subagents.

Affected files:

- `craft-mode/SKILL.md`, the description.
- `craft-mode/references/catalog.md`, the `swarm` row.
- Repository `README.md`, the craft-mode row.

## (k) craft-help wording

(k) craft-help keeps poteto-help's wording verbatim for the two sentences about skills loading only when the user types them or craft-mode runs them, and for the `principle-*` directories note; only names and links change.

Affected files:

- `craft-help/SKILL.md`, the Get set up loading sentence, the note under the skill table, the principles paragraph and the fix-table row; the `/setup-pstack` sentence has no craft equivalent and is dropped.

## (l) Model roles

(l) Where pstack assigned a model per role, the port restores the role distinction as one plain-language sentence instead of the earlier "two different model families" generalization: the fastest, cheapest setting for high-volume reading and code-writing roles, the most capable setting for synthesis and judgment, and a capable model from a different family where a step needs cross-family review; bodies name no models or effort levels, the agent picks the actual model in its runtime, pinning is optional per runtime, and a runtime with one model needs nothing extra.

Affected files:

- `how/SKILL.md`, `why/SKILL.md`, `reflect/SKILL.md`, `swarm/SKILL.md`, `interrogate/SKILL.md`, `arena/SKILL.md` and `architect/SKILL.md`, at each upstream model assignment.
- `craft-mode/SKILL.md`, the Subagents defaults, and `craft-mode/references/playbooks/` `bug-fix.md`, `feature.md`, `hillclimb.md`, `perf-issue.md`, `refactoring.md` and `multi-phase-plan.md`.
- `craft-mode/references/runtimes.md`, the Models row.

## (m) Dangling references to unimported skills

(m) Upstream text that calls a skill this library does not import is inlined at the call site instead of linking a missing package: the `ketchup` catch-up runs in the **bro** skill's voice, and interrogate's `in-your-own-words` step keeps the local base wording; orch is deleted along with upstream's removal of it.

Affected files:

- `craft-mode/references/playbooks/autopilot-full.md`, the hourly tick and the Reply catch-up.
- `interrogate/SKILL.md`, the intent sentence.
- `craft-mode/references/playbooks/orchestrate.md` and the removed `craft-mode/scripts/orch/`.

## (o) Forge CLI wording

(o) Upstream's mentions of its named forge CLI take the existing local "alternative forge CLI" rewrite; `scripts/worktree-audit.sh` keeps the `origin` command it calls and rewrites only its comment.

Affected files:

- `craft-mode/references/playbooks/shipping.md`.
- `craft-mode/references/playbooks/autopilot-full.md`.
- `craft-mode/references/playbooks/autopilot-stack.md`, which keeps its local wording.
- `craft-mode/references/playbooks/opening-a-pr.md` and `babysit.md`, the forge readiness and stack commands.
