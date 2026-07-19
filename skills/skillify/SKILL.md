---
name: skillify
description: Owns the full lifecycle of craft-skills skill packages — creating, updating, moving/renaming, retiring them, and absorbing frontier labs' skill-creators into vendor lenses — through an eval-first authoring loop and deterministic format validation. Use when a user says things like "make a skill", "skillify this workflow", "turn this into a skill", "update this skill", "move this skill", "absorb openai's new skill-creator", or "스킬 만들자", or when a recurring workflow correction needs to be encoded into a governing skill instead of staying in chat memory. Not for one-off project scripts or prompts with no reuse intent — those stay local to the originating project.
metadata:
  version: 4.4.0
---

# skillify

Turns a repeated workflow into a well-formed craft-skills package — `SKILL.md` + `CHANGELOG.md`, plus whatever `references/`, `scripts/`, `templates/`, `assets/`, or `tests/` it needs — and owns that package's lifecycle afterward.
Success looks like: the package passes both Layer-1 validators, its description triggers correctly and only on the intended prompts, and its [delivery follows the lifecycle flow](references/lifecycle.md#6-branch--commit--pr).
The core contract stays vendor-agnostic; what any one runtime needs lives in that vendor's lens.

## Admission check

Before authoring anything, answer three questions.
All three "yes" → proceed.
Any "no" → keep the candidate project-local, or point at the upstream harness that already owns it, instead of authoring here.

1. **Reusable craft?** True and useful on a next project whose stack is unrelated to the one it came from — not a one-off artifact bound to this project's paths or data.
2. **Owned by this library?** No mature upstream harness already performs this workflow.
3. **Vendor-agnostic?** Runs as plain Markdown instructions with `${ENV_VAR}` indirection — no call that only one runtime exposes.

## Detect mode

```bash
SKILL_DIR="skills/<skill-name>"
test -f "$SKILL_DIR/SKILL.md" && mode=update || mode=create
```

A request to absorb an upstream skill-creator is its own mode — go straight to the [absorption protocol](references/vendor-absorption.md).

## Plan the package

Before writing anything, walk 2–3 concrete invocations of the workflow and classify what a fresh run would redo each time into package parts — repeated code → `scripts/`, re-derived knowledge → `references/`, fixed artifact shapes → `templates/`, output-consumed files → `assets/` (the planning walk and parts table: `references/contract.md` §5).
Then match each remaining step's freedom to its fragility (contract §4): prose where judgment rules, an exact script where the step is fragile and order-sensitive.

## Eval-first authoring loop (the quality gate)

Before writing `SKILL.md`, draft the eval scenarios that will judge it — evals are the quality bar, not a manual sign-off round:

1. Draft `evals/evals.json` — about 3 realistic scenarios (prompt + expected behavior).
2. Draft `evals/triggers.json` — 8 should-trigger + 8 near-miss should-NOT-trigger prompts pulled from sibling skills' domains.
3. Run each scenario without the skill, then with the drafted body — the skill's value is the delta between the arms. Iterate until behavior matches. Run the 16 trigger prompts against the drafted description; tighten the "Not for X" boundary sentence wherever a near-miss would plausibly match.

How to run the arms, judge with fresh eyes, read transcripts, and improve without overfitting: [`references/evaluation.md`](references/evaluation.md).
`evals/` is local scratch — gitignored, never committed.
Full contract: `references/contract.md §7`.

## Author the package

Frontmatter is exactly `name`, `description`, `metadata.version` — nothing else.
Name is kebab-case and equals the directory: verb-first for a skill the user explicitly triggers, a plain noun for a skill that supplies ambient domain context.
Description is third person, states what + when, weaves in 3–6 real trigger phrases, writes against undertriggering, and adds a "Not for X" line when a sibling overlaps.
Body targets 150 lines, hard-caps at 500; move depth to `references/*.md`.
Keep package content MECE: each rule has one owning section or reference, and nearby locations link to it instead of restating it.
Full rules: `references/contract.md`.

## Vendor lenses

Every frontier lab distills how skills are best made for its models into its own skill-creator.
The universal lessons are already merged into this package's core files; each lens holds one vendor's distinctive emphases, runtime plumbing, and recorded divergences from this library's contract.

| Lens | Read when |
|------|-----------|
| [`references/vendor-openai.md`](references/vendor-openai.md) | Targeting the Codex runtime, or consulting OpenAI's scaffold-first discipline. |
| [`references/vendor-anthropic.md`](references/vendor-anthropic.md) | Targeting Claude Code / claude.ai, or driving Anthropic's eval and description-optimization machinery. |
| [`references/vendor-hermes.md`](references/vendor-hermes.md) | Targeting the Hermes runtime, or borrowing its experience-capture (`/learn`) flow. |

When a lab ships a new or updated skill-creator, run the [absorption protocol](references/vendor-absorption.md): universal lessons merge into core with provenance, plumbing stays in the lens, and disagreements are recorded — never silently imported.

## Lifecycle

Choose the package operation from [`references/lifecycle.md`](references/lifecycle.md): create (§2), update and record corrections (§3), move/rename (§4), or retire (§5).
Before editing, use its [clean-start route](references/lifecycle.md#1-clean-start) so unrelated work stays untouched.

## Validate (Layer 1 — deterministic, CI-enforced)

Run the [validator playbook](references/runtime-hygiene.md#2-validator-playbook) for each changed package.

## Deliver

Follow the [branch → commit → PR delivery flow](references/lifecycle.md#6-branch--commit--pr).

## Requirements

- `python3` — both Layer-1 validators
- `gh` — PR creation and branch flow

## Anti-patterns

- Authoring before `evals/evals.json` + `evals/triggers.json` exist → evals judge behavior and trigger-fit first; tests lock in behavior only once proven.
- A longer, descriptive skill name "for clarity" → the name is a compact handle; discoverability lives in the description's trigger phrases.
- A description written as an abstract capability blurb → weave in real user trigger phrases.
- A nested `SKILL.md` anywhere inside a package → every skill is one flat directory.
- An operator correction left in chat memory → record it via the three-way split before the session ends (`references/lifecycle.md §3`).
- Duplicated overlapping guidance inside one package → apply `references/contract.md` §9; link to the owner instead of restating the rule.
- An upstream mechanism imported into core without the portability test → classify universal vs plumbing per the absorption protocol; plumbing stays in the lens.
- Patching the body until the three eval examples pass → generalize the lesson instead; held-out prompts judge the result (`references/evaluation.md §5`).

## Verification

- [ ] [Layer-1 validators](references/runtime-hygiene.md#2-validator-playbook) pass
- [ ] `evals/` scenarios ran clean and the 16 trigger prompts route correctly
- [ ] [Version and CHANGELOG requirements](references/contract.md#6-changelog) are met
- [ ] [Secret hygiene](references/runtime-hygiene.md#1-per-skill-secrets-rule) is met
- [ ] Any absorbed upstream is fully recorded — lens sections 1–5, CHANGELOG `Provenance:`, `skills/PROVENANCE.md` row, manifest `absorbed_from` ([protocol §6](references/vendor-absorption.md#6-record-and-deliver))
- [ ] [Branch → commit → PR delivery](references/lifecycle.md#6-branch--commit--pr) is complete
