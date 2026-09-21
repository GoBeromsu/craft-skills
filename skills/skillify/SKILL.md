---
name: skillify
description: Owns the full lifecycle of craft-skills skill packages — creating, updating, moving/renaming, retiring them, and absorbing frontier labs' skill-creators into vendor lenses — through upstream-first lightweight authoring that leaves official skills unmodified. Use when a user says things like "make a skill", "skillify this workflow", "turn this into a skill", "update this skill", "move this skill", "absorb openai's new skill-creator", or "스킬 만들자", or when a recurring workflow correction needs to be encoded into a governing skill. Not for one-off project scripts or private field experiments, which stay local until a requested harvest, and not for rewriting official vendor skills.
metadata:
  version: 6.0.0
---

# skillify

Turns a repeated workflow into a well-formed craft-skills package — required `SKILL.md` + `CHANGELOG.md`, plus the execution parts it needs — and owns that package's lifecycle afterward.
Success looks like: related official skills remain unmodified originals on their official channels, the local package holds only uncovered context, related working-host dependencies satisfy [contract §10](references/contract.md#10-external-facts-and-dependencies), focused functional and safety evidence supports the stated outcome and failure boundary, and [delivery follows the authorized lifecycle](references/lifecycle.md#6-branch--commit--pr).
The core contract stays vendor-agnostic; runtime plumbing lives in that vendor's lens.

A formal authoring run leaves a reviewable package under `skills/<name>/` on its own branch; publication and deployment retain their separate approvals.
State the artifact, location, relevant format, and what happens when the run cannot succeed.
Independent review judges that meaning; no exact heading, phrase, or section order is a format gate ([contract §4](references/contract.md#4-body)).

The package includes:

- Focused functional, security, and data-integrity evidence under `tests/<name>/`. Optional reusable scenarios may live there; generated run outputs are not required ([contract §7](references/contract.md#7-eval-first-authoring-loop)).
- A task-bound authoring receipt: base commit, content digest, intended effects, chosen verification, actual results, independent judgment where needed, [§10](references/contract.md#10-external-facts-and-dependencies) current/stale/failure outcomes, and any unverified obligation.
- Every mentioned package-relative support path present in the package ([contract §12](references/contract.md#12-referenced-paths)). Refer to tests from repo-root `tests/<name>/`.
- A dated `CHANGELOG.md` bullet, version bump per the [rubric](references/contract.md#8-version-bump-rubric), and a CHANGELOG at or under 100 lines ([contract §6](references/contract.md#6-changelog)).
- A summary naming package, mode, evidence obtained, limitations, and delivery state.

When the run cannot succeed, leave no half-built package:

- Admission fails → stop; return the failed question and owner (project-local, upstream harness, official vendor skill, or bstack `promote`).
- A related official skill would be copied or rewritten → stop; keep the original and author only the uncovered gap, or report the official owner as the blocker.
- [Contract §10](references/contract.md#10-external-facts-and-dependencies) current/stale/update-failure outcomes are unmet → incomplete.
- A Layer-1 validator fails → fix the defect; change the validator only when it is the authorized target and still has a current consumer or independent safety owner.
- A claimed improvement is not shown → revise the claim or recipe; do not fabricate a delta.
- A near-miss triggers the skill → tighten the sibling boundary and rerun relevant probes.
- Upstream skill-creator guidance conflicts → record the divergence in the vendor lens; never silently import.
- Dirty tree or stale `main` → [clean-start](references/lifecycle.md#1-clean-start); report pending publication approval when it has not been granted.

## Admission check

Before authoring, answer three questions.
All yes → proceed.
Any no → keep the candidate project-local, or point at the upstream harness or official vendor skill that already owns it.

1. **Reusable craft?** Useful on another relevant project or repeated workflow, without private project data.
2. **Owned by this library?** No mature upstream harness or official vendor skill already performs this workflow. Official originals stay unmodified; this library records only uncovered local context.
3. **Vendor-agnostic?** Plain Markdown with `${ENV_VAR}` indirection — no call that only one runtime exposes.

## Detect mode

```bash
SKILL_DIR="skills/<skill-name>"
test -f "$SKILL_DIR/SKILL.md" && mode=update || mode=create
```

A request to absorb an upstream skill-creator is comparison and local-gap extraction, not re-hosting product commands or evaluator harnesses — go to the [absorption protocol](references/vendor-absorption.md).

## Upstream-first create/update

Official vendor skills stay unmodified originals on their official channels.
Local packages hold only uncovered context.
Apply [contract §10](references/contract.md#10-external-facts-and-dependencies) on every create or update.
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
| [`vendor-gjc.md`](references/vendor-gjc.md) | Selected GJC workflow or direct authoring tools; official orca-cli/orchestration stay native originals. | [GJC SDK application guide](https://github.com/Yeachan-Heo/gajae-code/blob/main/docs/sdk-app-guide.md) |

Core recipes do not depend on a vendor's loader or proprietary tool.
Record actual support per selected runtime; do not invent an undocumented command.

## Lifecycle

Choose create, update, move/rename, or retire from [`lifecycle.md`](references/lifecycle.md).
Use the [clean-start route](references/lifecycle.md#1-clean-start) first.
Harvest field experiments only on request.

## Validate and deliver

Run the [validator playbook](references/runtime-hygiene.md#2-validator-playbook).
Keep only checks with a current consumer or independent safety owner.
Follow [branch → commit → PR](references/lifecycle.md#6-branch--commit--pr). Delivery is not install or live publication.

## Requirements

- `python3` — official source: https://docs.python.org/3/; safe probe: `python3 --version`; support boundary: Python 3.10+ for Layer-1 validators.
- `git` — official source: https://git-scm.com/docs; safe probe: `git --version`; format validation requires a Git worktree in every mode, and `--root` identifies its root.
- `gh` — official source: https://cli.github.com/manual/; safe probe: `gh --version`; support boundary: current `gh pr create`, `gh pr checks`, and `gh pr merge` command surfaces for the delivery flow.
- The `init` skill's tool-preflight reference (`tool-preflight.md` under its references) records mutable CLI probes, support boundaries, and the CHANGELOG verification receipt convention.
- Related official skills and CLI/agent runtimes follow [contract §10](references/contract.md#10-external-facts-and-dependencies).

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
- Hand-authoring into a destination's private conventions → run admission and focused verification here first.
- Importing upstream plumbing into core, or re-hosting a vendor harness as local SSOT → [absorption protocol](references/vendor-absorption.md).
- Memorizing examples in the body → generalize and check unseen prompts ([evaluation.md §6](references/evaluation.md)).
- Inventing a native API when official docs are uncertain → record the unknown.

## Verification

- [ ] Official skills unmodified; local content is uncovered context; [§10](references/contract.md#10-external-facts-and-dependencies) current/stale/failure outcomes recorded
- [ ] [Layer-1 validators](references/runtime-hygiene.md#2-validator-playbook) with a current consumer or safety owner pass
- [ ] Focused functional, security, and data-integrity fixtures cover requested effects
- [ ] Leading routing directive has bounded edges and discovery evidence when used
- [ ] [CHANGELOG](references/contract.md#6-changelog) including the 100-line cap; [secret hygiene](references/runtime-hygiene.md#1-per-skill-secrets-rule)
- [ ] Absorbed upstream recorded as gap extraction ([protocol §6](references/vendor-absorption.md#6-record-and-deliver)); [delivery](references/lifecycle.md#6-branch--commit--pr) complete
