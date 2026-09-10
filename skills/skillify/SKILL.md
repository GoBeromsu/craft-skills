---
name: skillify
description: Owns the full lifecycle of craft-skills skill packages — creating, updating, moving/renaming, retiring them, and absorbing frontier labs' skill-creators into vendor lenses — through evidence-proportional authoring and deterministic format validation. Use when a user says things like "make a skill", "skillify this workflow", "turn this into a skill", "update this skill", "move this skill", "absorb openai's new skill-creator", or "스킬 만들자", or when a recurring workflow correction needs to be encoded into a governing skill. Not for one-off project scripts or private field experiments, which stay local until a requested harvest.
metadata:
  version: 5.0.0
---

# skillify

Turns a repeated workflow into a well-formed craft-skills package — required `SKILL.md` + `CHANGELOG.md`, plus the execution parts it needs — and owns that package's lifecycle afterward.
Success looks like: the package passes the relevant deterministic checks, its output contract agrees with the observed behavior and supplied evidence, and its [delivery follows the authorized lifecycle](references/lifecycle.md#6-branch--commit--pr).
The core contract stays vendor-agnostic; what any one runtime needs lives in that vendor's lens.

## Output contract

A formal authoring run leaves a reviewable package under `skills/<name>/` on its own branch; publication and deployment retain their separate approvals:

- `SKILL.md` whose body carries `## Output contract` — the one literal heading the validator checks and the evals grade against, stating the artifact and what the run does when it cannot succeed ([contract §4](references/contract.md#4-body)).
- Relevant script tests and scenario/routing evidence under `tests/<name>/`; when a corpus is supplied, use `verifiable` cases with assertions or `subjective` cases with a rubric ([contract §7](references/contract.md#7-eval-first-authoring-loop)).
- A task-bound authoring receipt identifying the base commit, current content digest, intended effects, chosen verification and its rationale, actual results, independent judgment where needed, and any unverified obligation.
- Every package-relative `scripts/`, `references/`, `templates/`, `assets/`, or `agents/` support path the body mentions exists in the package ([contract §12](references/contract.md#12-referenced-paths)). Refer to tests from repo-root `tests/<name>/`, not from the installed package, and verify their commands in the authoring evidence.
- A dated `CHANGELOG.md` bullet and a version bump per the [rubric](references/contract.md#8-version-bump-rubric); manifest and plugin versions updated when the package is published.
- The summary names the package, mode, evidence actually obtained, limitations, and delivery state; name a PR or release commit only when it exists.

When the run cannot succeed, it leaves no half-built package:

- Admission check fails → stop before authoring; return the failed question and the owner (project-local, upstream harness, or bstack `promote` for SSOT promotion).
- A Layer-1 validator fails → resolve the actual defect rather than hiding it; change the validator only when its own contract is the authorized target.
- A comparison shows no claimed improvement → revise the claim or recipe; do not fabricate a positive delta. A format repair or required safety regression need not improve an unrelated benchmark.
- A near-miss prompt triggers the skill → tighten the sibling boundary and rerun relevant positives, negatives, and unseen prompts.
- Upstream skill-creator guidance conflicts with this contract → record the divergence in the vendor lens; never silently import.
- Dirty tree or stale `main` → use the [clean-start route](references/lifecycle.md#1-clean-start) without stashing or overwriting unrelated work; report publication or effect approval as pending when it has not been granted.

## Admission check

Before authoring anything, answer three questions.
All three "yes" → proceed.
Any "no" → keep the candidate project-local, or point at the upstream harness that already owns it, instead of authoring here.

1. **Reusable craft?** Useful on another relevant project or repeated workflow, without private project data — not a one-off artifact tied to this account or path.
2. **Owned by this library?** No mature upstream harness already performs this workflow.
3. **Vendor-agnostic?** Runs as plain Markdown instructions with `${ENV_VAR}` indirection — no call that only one runtime exposes.

## Detect mode

```bash
SKILL_DIR="skills/<skill-name>"
test -f "$SKILL_DIR/SKILL.md" && mode=update || mode=create
```

A request to absorb an upstream skill-creator is its own mode — go straight to the [absorption protocol](references/vendor-absorption.md).

## Plan the package

When designing package parts, examine concrete invocations sufficient to identify recurring work — repeated code → `scripts/`, re-derived knowledge → `references/`, fixed artifact shapes → `templates/`, output-consumed files → `assets/` (contract §5).
Then match each remaining step's freedom to its fragility (contract §4): prose where judgment rules, an exact script where the step is fragile and order-sensitive.
For mutable external CLI, API, service, or runtime facts, apply the [official-docs-first dependency contract](references/contract.md#10-external-facts-and-dependencies) before encoding or linking the runtime form in the affected package.

## Evidence-proportional authoring

Before drafting the body, state the output contract, relevant failure conditions, and how the requested change can be verified:

1. Draft `## Output contract` first — the artifact and the cannot-succeed cases; every eval case grades against it.
2. For executable changes, add regressions against the real script or API, including relevant errors and external-effect boundaries. For judgment-heavy changes, choose realistic scenarios and an independent qualitative rubric.
3. When routing changes, exercise included requests and overlapping sibling near-misses on the relevant discovery surface. Use a corpus when it makes these checks repeatable, not to satisfy a fixed case count.
4. Run the selected checks and record actual results. Use matched baseline/candidate arms when asserting an improvement or comparing competing designs; record untested environments and missing evidence explicitly.

For a leading routing directive, state explicit inclusion and sibling exclusion edges, preserve the baseline, and freeze evaluation prompts before tuning.
Use unseen prompts to check generalization and record the actual runtime, judge, and discovery surface.
Demonstrate any claimed routing improvement without regressions on the evaluated boundary; do not impose a universal model/runtime matrix or case count.
Keep ordinary prose when evidence does not justify stronger routing pressure, and never describe untested runtime support as verified.

How to run the arms, judge with fresh eyes, read transcripts, and improve without overfitting: [`references/evaluation.md`](references/evaluation.md).
Authored tests and supplied corpora live beside the package at repo root, never inside an install bundle; private transcripts and judge notes stay in gitignored scratch.
Full contract: `references/contract.md §7`.
Include relevant ambiguity, conflict, unknown, and dependency-update cases per [§10](references/contract.md#10-external-facts-and-dependencies); do not create a service or mandatory global benchmark for them.
Reuse task- and content-bound authoring evidence in the destination admission gate rather than running another equivalent committee.
Review a common policy once, then implement its domain batches; do not restart a full GJC workflow for every package.

## Author the package

Use the portable baseline frontmatter: `name`, `description`, and `metadata.version`.
Add spec keys `license`, `compatibility`, or experimental `allowed-tools` only when the package truly requires them; document the runtime support caveat in the relevant vendor lens rather than making them a universal requirement.
Name is kebab-case and equals the directory: verb-first for a skill the user explicitly triggers, a plain noun for a skill that supplies ambient domain context.
The body carries `## Output contract` right after the purpose sentence; the workflow follows it ([contract §4](references/contract.md#4-body)).
Every package path the body cites must ship with the package ([contract §12](references/contract.md#12-referenced-paths)).
Description is third person, states what + when, weaves in 3–6 real trigger phrases, writes against undertriggering, and adds a "Not for X" line when a sibling overlaps.
Default to ordinary prose.
Use contract §3's exact leading `MUST USE <bounded ownership clause>.` form only when relevant routing evidence justifies the stronger directive; lexical validity alone never proves ownership or behavioral quality.
Preserve useful guidance and move optional depth to `references/`; the repository's 500-line ceiling is a local format policy, not a quality score or an upstream compatibility law.
Keep package content MECE: each rule has one owning section or reference, and nearby locations link to it instead of restating it.
Full rules: `references/contract.md`.

## Vendor lenses

Every frontier lab distills how skills are best made for its models into its own skill-creator.
Put portable lessons in the single core owner that governs them; each lens holds only its vendor's distinctive emphases, runtime plumbing, and recorded divergences from this library's contract.

| Lens | Read when | Official source |
|------|-----------|-----------------|
| [`references/vendor-openai.md`](references/vendor-openai.md) | Targeting the Codex runtime, or consulting OpenAI's scaffold-first discipline. | [OpenAI model guide](https://developers.openai.com/api/docs/guides/latest-model) |
| [`references/vendor-anthropic.md`](references/vendor-anthropic.md) | Targeting Claude Code / claude.ai, or driving Anthropic's eval and description-optimization machinery. | [Anthropic prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5) |
| [`references/vendor-hermes.md`](references/vendor-hermes.md) | Targeting the Hermes runtime, or borrowing its experience-capture (`/learn`) flow. | [Hermes skill guide](https://github.com/NousResearch/hermes-agent/tree/main/website/docs/user-guide/skills) |
| [`references/vendor-cursor.md`](references/vendor-cursor.md) | Targeting Cursor, including its skill discovery and packaging conventions. | [Cursor skills docs](https://prod.cursor.com/docs/skills) |
| [`references/vendor-grok.md`](references/vendor-grok.md) | Using Grok model guidance; consult native packaging only for an explicitly selected Grok runtime. | [xAI model guide](https://docs.x.ai/developers/grok-4-6.md) |
| [`references/vendor-gjc.md`](references/vendor-gjc.md) | Using the selected GJC workflow or direct authoring tools while keeping output portable. | [GJC SDK application guide](https://github.com/Yeachan-Heo/gajae-code/blob/main/docs/sdk-app-guide.md) |

Core recipes do not depend on a vendor's loader or proprietary tool; record actual support and verification per selected runtime, including Claude Code, Codex, Hermes, GJC, and OMO.
Model guidance does not require installing that vendor's CLI; keep optional Cursor or Grok-native plumbing separate from the selected deployment scope.
Vendor fields, commands, plugin metadata, and other runtime plumbing stay in the matching lens.
When a lab ships a new or updated skill-creator, run the [absorption protocol](references/vendor-absorption.md): merge only demonstrated portable lessons into their core owner with provenance, keep plumbing in the lens, and record disagreements — never silently import.

## Lifecycle

Choose the package operation from [`references/lifecycle.md`](references/lifecycle.md): create (§2), update and record corrections (§3), move/rename (§4), or retire (§5).
Before editing, use its [clean-start route](references/lifecycle.md#1-clean-start) so unrelated work stays untouched.
Keep native field experiments separate from official packages and let them evolve without immediate canonical edits or version bumps.
Harvest them only on request, distinguishing canonical packages, proposed PR changes, field packages, and reference evidence before assigning owner, privacy, provenance, and admission state.
Do not scan all memory or conversations to harvest one skill, and do not add scheduled harvesting.

## Validate (Layer 1 — deterministic, CI-enforced)

Run the [validator playbook](references/runtime-hygiene.md#2-validator-playbook) for each changed package.

## Deliver

Follow the [branch → commit → PR delivery flow](references/lifecycle.md#6-branch--commit--pr).

## Requirements

- `python3` — official source: https://docs.python.org/3/; safe probe: `python3 --version`; support boundary: Python 3.10+ for Layer-1 validators.
- `git` — official source: https://git-scm.com/docs; safe probe: `git --version`; format validation requires a Git worktree in every mode, and `--root` identifies its root.
- `gh` — official source: https://cli.github.com/manual/; safe probe: `gh --version`; support boundary: current `gh pr create`, `gh pr checks`, and `gh pr merge` command surfaces for the delivery flow.
- The `init` skill's tool-preflight reference (`tool-preflight.md` under its references) records mutable CLI probes, support boundaries, and the CHANGELOG verification receipt convention.
- Dependency trigger — a selected dependency/runtime release or a changed probe/capability requires official-documentation review and affected evals before updating this package. The dependency contract applies to skillify immediately; apply it to another package when that package is next touched or when its own dependency trigger fires. Do not create mass churn or a global inventory.

## Anti-patterns

- Authoring without a checkable output contract and relevant evidence plan → define the outcome and failure boundary, then choose script tests or scenarios that exercise it.
- Adding `## Goal`, `## Non-goals`, or `## Failure modes` sections → each restates an existing owner (purpose sentence, description's "Not for X", `## Output contract`'s cannot-succeed lines, this registry); one contract heading, one anti-pattern registry.
- Rewriting an untouched legacy package to the current contract → apply the contract when that package is next touched; no mass churn.
- Putting runtime plumbing, plugin metadata, or vendor-only commands in the core body → the matching vendor lens owns them.
- A rubric where an assertion would do, or assertions forced onto judgment output → grade `verifiable` cases by assertions and `subjective` cases by rubric.
- A recipe step that cites a script or reference the package does not ship → add the file or remove the mention; the validator fails the package either way.
- A longer, descriptive skill name "for clarity" → the name is a compact handle; discoverability lives in the description's trigger phrases.
- A description written as an abstract capability blurb → weave in real user trigger phrases.
- Caps-lock used to compensate for weak or overlapping routing boundaries → either prove the single leading description directive with bounded sibling edges and frozen trigger delta, or keep ordinary prose; the exception never applies to body prose.
- A nested `SKILL.md` anywhere inside a package → every skill is one flat directory.
- Treating every field correction as a formal package mutation → retain local learning and use the requested harvest plus authorized lifecycle for shared changes.
- Hand-authoring a skill package because the destination repository carries its own frontmatter and routing conventions → run the admission check and the eval-first loop here first, then let that repository's own promotion gate route the well-formed package.
- Duplicated overlapping guidance inside one package → apply `references/contract.md` §9; link to the owner instead of restating the rule.
- An upstream mechanism imported into core without the portability test → classify universal vs plumbing per the absorption protocol; plumbing stays in the lens.
- Patching the body to memorize its eval examples → generalize the lesson and check unseen prompts (`references/evaluation.md §6`).
- A skill that narrates internal reasoning or asks a user to reveal it → request only decisions, constraints, evidence, and deliverables needed to act.

## Verification

- [ ] [Layer-1 validators](references/runtime-hygiene.md#2-validator-playbook) pass, including the `## Output contract`, referenced paths, and eval corpus checks
- [ ] Relevant real script tests and judgment/routing scenarios cover the requested effects; the receipt explains the selection and every unverified obligation
- [ ] Any leading routing directive has bounded inclusion/exclusion and actual discovery evidence, with unseen prompts and matched comparison when improvement is claimed
- [ ] [Version and CHANGELOG requirements](references/contract.md#6-changelog) are met
- [ ] [Secret hygiene](references/runtime-hygiene.md#1-per-skill-secrets-rule) is met
- [ ] Any absorbed upstream is fully recorded — lens sections 1–5, CHANGELOG `Provenance:`, `skills/PROVENANCE.md` row, manifest `absorbed_from` ([protocol §6](references/vendor-absorption.md#6-record-and-deliver))
- [ ] [Branch → commit → PR delivery](references/lifecycle.md#6-branch--commit--pr) is complete
