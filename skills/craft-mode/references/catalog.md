# Source catalog

This catalog maps every direct skill and every principle in pstack, pinned at cursor/plugins@6b0300214a09fd6029cfb7077043125758cd1fd2, to its place in this library.
Each row has three labels.
**Origin** is where the source came from.
**Current craft owner** is the package that already covered the topic before the import, or `none`.
**Craft destination** is where the source now lives.

**Kind** says how to reach it:

- **command**: a package you invoke by name.
- **reference**: a file read on demand by its owner or by craft-mode; it has no command of its own.
- **dropped**: no portable substance exists, so no file or command offers it.

Cross-package paths name the owning skill and its file.
Resolve them through that skill's discovery location.

## Contents

- [Direct skills](#direct-skills)
- [pstack automations](#pstack-automations)
- [Principles](#principles)
- [Unsupported boundaries](#unsupported-boundaries)
- [Composition edges](#composition-edges)

## Direct skills

| Upstream skill | Origin | Current craft owner | Craft destination | Kind | Notes |
|---|---|---|---|---|---|
| `poteto-mode` | pstack | none | `craft-mode` | command | Playbook router and working style; no persistent mode. |
| `poteto-help` | pstack | none | `craft-help` | command | Router help for craft-mode. |
| `how` | pstack | none | `how` | command | Spawns read-only subagents: one explainer for a simple question, parallel explorers then an explainer for a complex one. |
| `why` | pstack | none | `why` | command | May compose how. |
| `recall` | pstack | none | `recall` | command | Mines the active workspace's recent transcripts with parallel subagents; reads another project's only when asked. |
| `blast-radius` | pstack | none | `blast-radius` | command | Proves the safety fact by running real code. |
| `architect` | pstack | none | `architect` | command | Grounds through how and why; explores with arena. |
| `arena` | pstack | none | `arena` | command | Parallel candidates on two model families, a judge from another family, then pick, graft, and verify. |
| `swarm` | pstack | none | `swarm` | command | Fans bounded subagents out over slices or a race and drains one report. |
| `interrogate` | pstack | none | `interrogate` | command | Uses whatever reviewers the runtime offers; no fixed model list. |
| `automate-me` | pstack | none | `automate-me` | command | Mines the active workspace's transcripts and asks the user, then drafts one personal mode skill and lands it through a PR. |
| `setup-pstack` | pstack | none | `craft-mode/references/setup.md` | dropped | Model and budget configuration dropped by owner decision; the file documents native discovery only. |
| `reflect` | pstack | none | `reflect` | command | Three parallel reviewers read the active transcript or a session digest; edits wait for user approval, backlog items file automatically. |
| `correct` | pstack | none | `correct` | command | Fixes each repeated mistake class at the highest level that works, one commit per class, and proves each check fails on a real past mistake. |
| `teach` | pstack | none | `teach` | command | Composes how and why. |
| `tdd` | pstack | `programming` (now `principle-programming`), red-green TDD | `tdd` | command | Failing-first regression test when practical; otherwise the closest executable check, reported as such. |
| `benchmark-checklist` | pstack | none | `benchmark-checklist` | command | Applies `principle-testing/references/explain-the-number.md`. |
| `no-comments` | pstack | `programming` shortcut comments and `document` inline comments | `principle-programming/references/comments.md` | reference | Spawns one comment-review subagent with `principle-programming/references/comment-sicko.md` and acts on accepted findings. |
| `typescript-best-practices` | pstack | `programming` (now `principle-programming`) TypeScript reference | `principle-programming/references/typescript.md` and `principle-programming/references/typescript/patterns.md` | reference | Absorbed whole; upstream wins on conflicts. |
| `figure-it-out` | pstack | none | `figure-it-out` | command | Designs an auditable playbook when none fits. |
| `show-me-your-work` | pstack | none | `show-me-your-work` | command | Local decision log by default. |
| `create-verification-skill` | pstack | `testing` (now `principle-testing`) e2e guidance | `principle-testing/references/verification-skills.md` | reference | Writes a project-local `.agents/skills/verify-<app>/` skill with a feature map. |
| `maintain-verification-skill` | pstack | `testing` (now `principle-testing`) e2e guidance | `principle-testing/references/verification-skills.md` | reference | Read-only source subagents per feature, a live pass, then one PR of proven corrections or a clean or blocked report. |
| `unslop` | pstack | none | `unslop` | command | Always applies to prose; code and fixed machine formats are excluded. |
| `bro` | pstack | none | `bro` | command | Short plain-language restatement on request. |
| `technical-writing` | pstack | `document` | `document/references/technical-writing.md` | reference | Read by document for prose work. |

## pstack automations

| Upstream pack | Origin | Current craft owner | Craft destination | Kind | Notes |
|---|---|---|---|---|---|
| `automations/benny` | pstack | `issue-triage`, `craft-mode` | `issue-triage/references/intake.md`, `issue-triage/references/routing.example.md`; `craft-mode/references/reproduce-and-fix.md`, `verify-existing-fix.md`, `control-adapter.md` | reference | Dissolved: issue-triage intake triages, classifies, dedupes, and returns one verdict; the craft-mode Bug fix playbook reproduces confirmed bug or performance reports through those references, verifies an existing fix or attempts a bounded fix with before/after proof. Slack source mechanics become the report's source issue/thread or pasted text; scheduling and automation templates are dropped. |

## Principles

Every principle file holds the upstream body verbatim, with frontmatter dropped and sibling links rewritten.
craft-mode's SKILL.md indexes all of them.

| Upstream principle | Group | Origin | Current craft owner | Craft destination | Kind |
|---|---|---|---|---|---|
| `principle-laziness-protocol` | core | pstack | `programming` and `refactor` | `principle-programming/references/laziness-protocol.md` | reference |
| `principle-foundational-thinking` | core | pstack | none | `principle-architecture/references/foundational-thinking.md` | reference |
| `principle-redesign-from-first-principles` | core | pstack | none | `principle-architecture/references/redesign-from-first-principles.md` | reference |
| `principle-attack-the-premise` | core | pstack | none | `debug/references/attack-the-premise.md` | reference |
| `principle-subtract-before-you-add` | core | pstack | `programming` and `refactor` | `refactor/references/subtract-before-you-add.md` | reference |
| `principle-minimize-reader-load` | core | pstack | none | `principle-programming/references/minimize-reader-load.md` | reference |
| `principle-outcome-oriented-execution` | core | pstack | none | `principle-architecture/references/outcome-oriented-execution.md` | reference |
| `principle-experience-first` | core | pstack | none | `principle-frontend/references/experience-first.md` | reference |
| `principle-exhaust-the-design-space` | core | pstack | none | `principle-architecture/references/exhaust-the-design-space.md` | reference |
| `principle-build-the-lever` | core | pstack | none | `principle-programming/references/build-the-lever.md` | reference |
| `principle-model-the-domain` | architecture | pstack | none | `principle-programming/references/model-the-domain.md` | reference |
| `principle-boundary-discipline` | architecture | pstack | `programming` | `principle-backend/references/boundary-discipline.md` | reference |
| `principle-type-system-discipline` | architecture | pstack | none | `principle-programming/references/type-system-discipline.md` | reference |
| `principle-make-operations-idempotent` | architecture | pstack | none | `principle-backend/references/make-operations-idempotent.md` | reference |
| `principle-migrate-callers-then-delete-legacy-apis` | architecture | pstack | none | `principle-architecture/references/migrate-callers-then-delete-legacy-apis.md` | reference |
| `principle-separate-before-serializing-shared-state` | architecture | pstack | none | `principle-architecture/references/separate-before-serializing-shared-state.md` | reference |
| `principle-prove-it-works` | verification | pstack | `testing` | `principle-testing/references/prove-it-works.md` | reference |
| `principle-fix-root-causes` | verification | pstack | `debug` | `debug/references/fix-root-causes.md` | reference |
| `principle-sequence-verifiable-units` | verification | pstack | none | `principle-testing/references/sequence-verifiable-units.md` | reference |
| `principle-test-behavior-not-implementation` | verification | pstack | `testing` | `principle-testing/references/test-behavior-not-implementation.md` | reference |
| `principle-explain-the-number` | verification | pstack | none | `principle-testing/references/explain-the-number.md` | reference |
| `principle-guard-the-context-window` | delegation | pstack | none | `craft-mode/references/guard-the-context-window.md` | reference |
| `principle-never-block-on-the-human` | delegation | pstack | none | `craft-mode/references/never-block-on-the-human.md` | reference |
| `principle-encode-lessons-in-structure` | meta | pstack | none | `correct/references/encode-lessons-in-structure.md` | reference |

## Unsupported boundaries

`setup-pstack` configured per-role models and budgets for Cursor; the owner dropped that outcome.
No package pins a model or a budget.

Skills added upstream after the previous pin are not imported: `ketchup` (#539), `ketchup-video` (#797), `sharpen` (#615), `statechart` (#741), `in-your-own-words` (#602), and `create-formal-verification-skill` / `maintain-formal-verification-skill` (#709, #716).

Elsewhere, Cursor-only parts are removed and the portable outcome stays: Custom Mode persistence, fixed model tables, Cursor transcript paths, and Cursor's built-in skill authoring.

## Composition edges

The 23 playbooks live in `playbooks/`, one upstream file each, and own their workflow and principle edges.
These direct-skill edges are required:

- `teach` composes `how` and `why`.
- `architect` grounds through `how` and `why` and explores alternatives with `arena`.
- `benchmark-checklist` applies `principle-testing/references/explain-the-number.md`.
- `correct` applies `correct/references/encode-lessons-in-structure.md`.
