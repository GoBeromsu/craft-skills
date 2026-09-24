---
name: skillify
description: Owns the lifecycle of skill packages wherever the user chooses — creating, updating, moving/renaming, retiring them, and absorbing frontier labs' skill-creators into vendor lenses — completing with the package plus its evaluation evidence while official skills stay unmodified. Use when a user says "make a skill", "skillify this workflow", "turn this into a skill", "update this skill", "move this skill", "absorb openai's new skill-creator", or "스킬 만들자", or a recurring correction needs encoding into a governing skill. Not for registering, installing, or publishing a finished package (bstack uses `promote`), one-off project scripts, unharvested field experiments, or rewriting official skills.
metadata:
  version: 7.0.0
---

# skillify

Turns a repeated workflow into a well-formed skill package — required `SKILL.md`, the execution parts it needs, and history under the destination's policy — at the destination the user chooses, and owns that package's lifecycle afterward.
The destination may be this library, another skill library, a project's skill directory, an Obsidian vault, or any other location; where skillify itself is stored does not decide where its output goes.
Success looks like: the package exists at the chosen location, related official skills remain unmodified originals on their official channels, the package holds only uncovered context, the dependencies the task actually uses satisfy [contract §10](references/contract.md#10-external-facts-and-dependencies), and focused functional and safety evidence supporting the stated outcome and failure boundary is handed off with the package ([contract §7](references/contract.md#7-eval-first-authoring-loop)).
The core contract stays vendor-agnostic; runtime plumbing lives in that vendor's lens.

The run is complete when the package exists, required authoring checks pass, and its usable evidence handoff identifies the evaluated content.
Installation into a runtime, registration in a library, branch/PR delivery, merge, and publication are separate effects with their own approvals; none of them is an automatic side effect of authoring ([lifecycle §6](references/lifecycle.md#6-branch--commit--pr)).
bstack registration and publication belong to the bstack `promote` skill, which consumes the evidence handoff and does not repeat authoring or quality evaluation.
State the artifact, location, relevant format, and what happens when the run cannot succeed.
Independent review judges that meaning; no exact heading, phrase, or section order is a format gate ([contract §4](references/contract.md#4-body)).

The result includes:

- The package at the chosen location, with every mentioned package-relative support path present ([contract §12](references/contract.md#12-referenced-paths)).
- Focused functional, security, and data-integrity evidence where the destination keeps tests — repo-root `tests/<name>/` in this library, the destination's own convention elsewhere. Optional reusable scenarios may live there; generated run outputs are not required ([contract §7](references/contract.md#7-eval-first-authoring-loop)).
- A task-bound authoring receipt: target location, requested effects, evaluated scope, base commit where one exists plus the content digest of the evaluated snapshot, chosen verification, actual results labeled as executed or reviewed, independent judgment where needed, [§10](references/contract.md#10-external-facts-and-dependencies) outcomes for the dependencies actually used, trigger findings, and any unverified obligation. This is the evidence a destination gate such as `promote` consumes.
- A dated `CHANGELOG.md` bullet, version bump per the [rubric](references/contract.md#8-version-bump-rubric), and a CHANGELOG at or under 100 lines ([contract §6](references/contract.md#6-changelog)); a destination that keeps history elsewhere applies its own rule.
- A summary naming package, location, mode, evidence obtained, limitations, and which separate effects (install, registration, PR, publication) were not requested or remain pending approval.

When the run cannot succeed, leave no half-built package:

- The entry check fails → stop; return the failed question and the owner that should hold the candidate (project-local script, upstream harness, official vendor skill, or the destination's own gate).
- A related official skill would be copied or rewritten → stop; keep the original and author only the uncovered gap, or report the official owner as the blocker.
- A dependency the task actually uses is stale and cannot be updated and verified within the current approval ([contract §10](references/contract.md#10-external-facts-and-dependencies)) → report it and leave the run incomplete; a runtime the task does not use never blocks it.
- A destination check fails (this library: a Layer-1 validator) → fix the defect; change the check only when it is the authorized target and still has a current consumer or independent safety owner.
- A claimed improvement is not shown → revise the claim or recipe; do not fabricate a delta.
- A near-miss triggers the skill → tighten the sibling boundary and rerun relevant probes.
- Upstream skill-creator guidance conflicts → record the divergence in the vendor lens; never silently import.
- A Git destination has unrelated work or a stale base → follow the [clean-start route](references/lifecycle.md#1-clean-start) without touching that work; a non-Git destination has no such step.
- Required authoring evidence is missing, stale, or inaccessible → retain the draft and hand off an incomplete result identifying the gap. Unverified optional checks or separate, unrequested delivery effects do not block authoring; never report a run, PR, install, or publication that did not happen.

## Entry check

Read context once at entry: the current request and conversation, the user's stated purpose, way of working, and mistakes to avoid, and the project instructions already in effect.
Use the relevant context already available; do not harvest whole conversation or memory stores.
Pull further material only when the task needs it — the selected destination's own policy (a library's contract, a project's skill conventions, a vault's placement, permission, style, and property rules), read for that destination only.
Check whether that destination is private or shared before writing; do not include secrets, account values, or private source text in shared packages, and include personal context in a private package only when authorized and necessary.
A non-vault task needs no vault path; a non-Git destination needs no worktree.
Do not stand up a context service or require a new configuration file.

Then answer three questions.
All yes → proceed.
Any no → keep the candidate project-local, or point at the upstream harness or official vendor skill that already owns it.

1. **Reusable craft?** Useful on another relevant project or repeated workflow; package only context appropriate for the authorized destination.
2. **Owned here?** No mature upstream harness or official vendor skill already performs this workflow. Official originals stay unmodified; the package records only uncovered context.
3. **Vendor-agnostic?** Plain Markdown with `${ENV_VAR}` indirection — no call that only one runtime exposes.

A library destination adds its own admission on top of these questions (this library: root `AGENTS.md`; bstack: `promote`); apply it there rather than copying it into every run.

## Detect mode

```bash
SKILL_DIR="<destination>/<skill-name>"   # this library: skills/<skill-name>
test -f "$SKILL_DIR/SKILL.md" && mode=update || mode=create
```

A request to absorb an upstream skill-creator is comparison and local-gap extraction, not re-hosting product commands or evaluator harnesses — go to the [absorption protocol](references/vendor-absorption.md).

## Upstream-first create/update

Official vendor skills stay unmodified originals on their official channels.
Local packages hold only uncovered context.
Apply [contract §10](references/contract.md#10-external-facts-and-dependencies) on every create or update to the dependencies the task actually uses; installed-but-unused runtimes are unrelated.
The agent chooses probe, update, recovery, and verification inside that contract.
Do not add generic repeated consent for reversible in-scope work.

## Plan and author

Identify recurring work from concrete invocations — code → `scripts/`, knowledge → `references/`, shapes → `templates/`, consumed files → `assets/` (contract §5).
Match freedom to fragility (contract §4).
State the outcome, failure boundary, and verification method before drafting.
Preserve real functional, security, and data-integrity fixtures; do not require generated eval/run outputs ([contract §7](references/contract.md#7-eval-first-authoring-loop), [`evaluation.md`](references/evaluation.md)).
Portable baseline frontmatter: `name`, `description`, `metadata.version`.
Description is third person, what + when, 3–6 trigger phrases, "Not for X" when a sibling overlaps.
Use contract §3's leading `MUST USE` form only with routing evidence.
Full rules: `references/contract.md`.

## Vendor lenses

Each lens owns uncovered runtime differences, source links, and recorded divergences — not copied official manuals.
Portable lessons land in the core owner; plumbing stays in the lens ([absorption protocol](references/vendor-absorption.md)).
A version or help check is not compatibility or deployment proof.

| Lens | Read when | Official source |
|------|-----------|-----------------|
| [`vendor-openai.md`](references/vendor-openai.md) | Codex runtime or OpenAI scaffold-first craft. | [OpenAI model guide](https://developers.openai.com/api/docs/guides/latest-model) |
| [`vendor-anthropic.md`](references/vendor-anthropic.md) | Claude Code / claude.ai, or Anthropic evaluator machinery on that runtime. | [Anthropic prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5) |
| [`vendor-hermes.md`](references/vendor-hermes.md) | Hermes runtime or its experience-capture craft. | [Hermes skill guide](https://github.com/NousResearch/hermes-agent/tree/main/website/docs/user-guide/skills) |
| [`vendor-cursor.md`](references/vendor-cursor.md) | Cursor discovery and packaging. | [Cursor skills docs](https://prod.cursor.com/docs/skills) |
| [`vendor-grok.md`](references/vendor-grok.md) | Grok model guidance; native packaging only when that runtime is selected. | [xAI model guide](https://docs.x.ai/developers/grok-4-6.md) |
| [`vendor-gjc.md`](references/vendor-gjc.md) | GJC selected as the authoring runtime, or packaging this library for GJC plugin discovery and exact invocation; official orca-cli/orchestration stay native originals. Authoring never requires GJC. | [GJC skills doc](https://github.com/Yeachan-Heo/gajae-code/blob/main/docs/skills.md) |

Core recipes do not depend on a vendor's loader or proprietary tool.
Record actual support per selected runtime; do not invent an undocumented command.

## Lifecycle

Choose create, update, move/rename, or retire from [`lifecycle.md`](references/lifecycle.md).
When the destination is a Git repository, use the [clean-start route](references/lifecycle.md#1-clean-start) first.
Harvest field experiments only on request.

## Validate and hand off

Run the checks the destination consumes: this library's [validator playbook](references/runtime-hygiene.md#2-validator-playbook) for packages under `skills/`, the destination's own checks elsewhere.
Keep only checks with a current consumer or independent safety owner.
Hand off the evidence receipt with the package ([contract §7](references/contract.md#7-eval-first-authoring-loop)); label each result as executed or reviewed.
Branch → commit → PR ([lifecycle §6](references/lifecycle.md#6-branch--commit--pr)) runs only for a Git destination when repository delivery is requested and authorized; install, registration, and publication need their own approvals and are not part of authoring.

## Requirements

- `python3` — official source: https://docs.python.org/3/; safe probe: `python3 --version`; support boundary: Python 3.10+ for this library's Layer-1 validators; not needed for a destination that has no such checks.
- `git` — official source: https://git-scm.com/docs; safe probe: `git --version`; needed only for a Git destination and for this library's format validator, which requires a Git worktree in every mode (`--root` identifies its root).
- `gh` — official source: https://cli.github.com/manual/; safe probe: `gh --version`; support boundary: current `gh pr create`, `gh pr checks`, and `gh pr merge` command surfaces, needed only when an authorized PR delivery is requested.
- The `init` skill's tool-preflight reference (`tool-preflight.md` under its references) records mutable CLI probes, support boundaries, and the CHANGELOG verification receipt convention.
- Related official skills and CLI/agent runtimes that the task actually uses follow [contract §10](references/contract.md#10-external-facts-and-dependencies); GJC, vendor CLIs, and a vault path are optional and never a precondition for authoring elsewhere.

## Anti-patterns

- Authoring without a stated outcome and failure boundary → define them, then choose fixtures that exercise them.
- Forking or rewriting an official vendor skill, or copying its command manual into a lens → leave the original unmodified; author only uncovered local context.
- Treating a version or help check as compatibility, update completion, or deployment proof → follow [contract §10](references/contract.md#10-external-facts-and-dependencies).
- Requiring generated eval outputs or a wording-locked corpus → verify observable functional, security, and data-integrity outcomes.
- Asking for generic repeated consent on reversible in-scope work → act inside the existing approval.
- Adding a checker-of-checker or keeping schema without a consumer or safety owner → remove or rewrite it with the root policy.
- A recipe citing a missing support file → add the file or remove the mention.
- Caps-lock to paper over overlapping routing → prove the §3 directive or keep ordinary prose.
- A nested `SKILL.md` → one flat directory.
- Hand-authoring into a destination without reading its policy or choosing evidence → read the selected destination's policy once, state the outcome and failure boundary, then author there with focused verification.
- Treating install, registration, branch/PR, or publication as an automatic authoring side effect → complete at the chosen location with the evidence handoff; each further effect needs its own approval.
- Requiring GJC, a Git worktree, `gh`, or a vault path for a task that does not use them → bind only the dependencies the task actually invokes.
- Importing upstream plumbing into core, or re-hosting a vendor harness as local SSOT → [absorption protocol](references/vendor-absorption.md).
- Memorizing examples in the body → generalize and check unseen prompts ([evaluation.md §6](references/evaluation.md)).
- Inventing a native API when official docs are uncertain → record the unknown.

## Verification

- [ ] Package exists at the chosen location; official skills unmodified; local content is uncovered context; [§10](references/contract.md#10-external-facts-and-dependencies) outcomes recorded for the dependencies actually used
- [ ] Destination checks pass (this library: [Layer-1 validators](references/runtime-hygiene.md#2-validator-playbook) with a current consumer or safety owner)
- [ ] Focused functional, security, and data-integrity fixtures cover requested effects
- [ ] Leading routing directive has bounded edges and discovery evidence when used
- [ ] Destination history policy satisfied (this library: [CHANGELOG](references/contract.md#6-changelog) including the 100-line cap); [secret hygiene](references/runtime-hygiene.md#1-per-skill-secrets-rule)
- [ ] Absorbed upstream recorded as gap extraction ([protocol §6](references/vendor-absorption.md#6-record-and-deliver))
- [ ] Evidence receipt handed off with executed-versus-reviewed labels and content identity; install, registration, PR, and publication listed as not requested or pending their own approval
