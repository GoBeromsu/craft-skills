# Anthropic Lens (Claude Code / claude.ai)

Local context for targeting Claude Code or consulting Anthropic skill-creator craft.
Official Anthropic skills and Claude Code distribution stay unmodified on their official channels; this file records uncovered library boundaries, source links, and divergences — not copied product instructions or a re-hosted evaluator harness.
Consult current official docs when a runtime form is unknown; apply [contract §10](contract.md#10-external-facts-and-dependencies) on create/update.

## 1. Source

Official surfaces to consult first:

- [Prompting Claude Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5)
- Anthropic's current skills distribution and Claude Code documentation on their official channels

Historical comparison snapshot (not a local SSOT, not a distribution source): [`anthropics/skills` at `3b3fad96af16a10759d930941b4520ba0c40edae`](https://github.com/anthropics/skills/tree/3b3fad96af16a10759d930941b4520ba0c40edae), especially `skills/skill-creator` and its runtime-owned evaluation scripts.
A coordinator-verified working-host fact at authoring time was Claude Code stable `2.1.267`; that is not multi-runtime compatibility evidence and must be re-probed per [contract §10](contract.md#10-external-facts-and-dependencies).

## 2. Portable lesson

**Quality needs relevant behavioral evidence.**
Use a matched comparison when claiming improvement or choosing competing designs, and unseen cases where practical.
Preserve meaningful safety and script regressions even when both arms pass them; a structural pass alone cannot establish usefulness.

**Separate grading, comparison, and diagnosis when the task actually needs them.**
A grader checks evidence against explicit expectations, a blind comparator assesses competing outputs without knowing their arm, and an analyzer distinguishes a skill defect from an eval defect.
This division reduces self-confirming evaluation.
It is optional local method, not a requirement to copy Anthropic's scripts or persist generated harness outputs.

**Give brief, strong instructions.**
State the task, constraints, and completion evidence plainly.
Ground progress reports in observed work, not assurances.
Keep the scope to the simplest complete solution.

**Design long work as a bounded execution.**
For long-running work, preserve useful intermediate evidence and delegate independent bounded slices only when the runtime supports it.
Verify the result from a fresh context.
Do not ask a model to transcribe private reasoning; request inspectable outputs, decisions, and evidence instead.

## 3. Runtime plumbing (Claude-only)

- Claude Code install, plugin, session, stream, and packaging commands belong to current official Claude Code docs. Do not copy them into portable `SKILL.md`.
- Anthropic's runner, throwaway command injection, and generated benchmark artifacts are implementation details of that runtime, not this library's evaluation protocol.
- Claude adaptive-thinking controls, refusal behavior, fallback behavior, and send-to-user mechanics stay out of universal SKILL.md instructions.
- Fable-only API behavior stays in this lens.
- Use Anthropic's richer evaluator machinery only on that vendor's runtime when actual task risk warrants numbers; do not re-host those scripts or require their generated outputs here.

## 4. Divergences from this library

- **Official originals.** Anthropic product usage stays on official channels. This library does not fork, patch, or republish those skills.
- **Eval artifacts.** Anthropic may persist schema'd benchmark and history artifacts alongside a skill. This library commits optional reusable scenarios under repo-root `tests/<name>/evals/` only when useful, keeps generated transcripts in gitignored scratch, and does not treat corpus presence or harness scores as a pass condition (`contract.md` §7).
- **Executor coupling.** Anthropic's scripts assume its CLI and session protocol; this library defines runner-agnostic outcomes in [`evaluation.md`](evaluation.md).
- **Evaluation scale.** Treat source examples and benchmark machinery as recommendations suited to their task, not fixed case counts, provider quotas, or a mandatory full runtime matrix.
- **Frontmatter.** Anthropic-specific compatibility and tool fields are not part of the portable frontmatter contract.
- **Interaction model.** Evidence-grounded progress, simplest-complete scope, supported delegation, fresh-context verification, and inspectable conclusions are portable. Adaptive thinking, refusal/fallback tuning, and send-to-user mechanics are not.

## 5. Absorbed into core

- Evidence-grounded progress → `contract.md` §4.
- Implement only what the requested outcome requires; no speculative features, refactors, or abstractions. Do not add fallbacks or validation for impossible internal states; validate system boundaries. Keep complete end-to-end behavior. → `contract.md` §4.
- Delegation only when the runtime supports it → `contract.md` §4.
- Fresh-context verification → `evaluation.md` §1.
- Inspectable conclusions and evidence rather than reasoning-transcription requests → `contract.md` §4.
