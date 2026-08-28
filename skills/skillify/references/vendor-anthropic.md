# Anthropic Lens (Claude Code / claude.ai)

## 1. Source

Retrieved 2026-08-28:

- [`anthropics/skills` at `3b3fad96af16a10759d930941b4520ba0c40edae`](https://github.com/anthropics/skills/tree/3b3fad96af16a10759d930941b4520ba0c40edae), especially `skills/skill-creator`, its evaluation and benchmark scripts, and `agents/grader.md`, `agents/comparator.md`, and `agents/analyzer.md`.
- [Prompting Claude Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5).

## 2. Portable lesson

**Quality is measured behavior.** Compare a skill run with an appropriate baseline on realistic
tasks. Use held-out cases where practical; a structural pass alone cannot establish usefulness.

**Separate grading, comparison, and diagnosis.** A grader checks evidence against explicit
expectations, a blind comparator assesses competing outputs without knowing their arm, and an
analyzer distinguishes a skill defect from an eval defect. This division reduces self-confirming
evaluation.

**Give brief, strong instructions.** State the task, constraints, and completion evidence
plainly. Ground progress reports in observed work, not assurances. Keep the scope to the
simplest complete solution.

**Design long work as a bounded execution.** For long-running work, preserve useful intermediate evidence and delegate independent bounded slices only when the runtime supports it.
Verify the result from a fresh context.
Do not ask a model to transcribe private reasoning; request inspectable outputs, decisions, and evidence instead.

## 3. Runtime plumbing (Claude-only)

- The pinned Anthropic package's runner, stream handling, throwaway command injection, and
  packaging format depend on Claude Code. They are implementation details of that runtime, not
  a portable evaluation protocol.
- Claude adaptive-thinking controls, refusal behavior, fallback behavior, and send-to-user mechanics are Claude-specific. They stay out of universal SKILL.md instructions.
- Fable-only API behavior stays in this lens and never enters universal SKILL.md instructions.
- The source package's improvement loop may use interactive Claude sessions. This library does
  not import a casual-prose style or a user-interrupt loop as a universal operating pattern.

## 4. Divergences from this library

- **Eval artifacts.** Anthropic persists schema'd benchmark and history artifacts alongside a
  skill. This library keeps `evals/` as gitignored local scratch (`contract.md` §7), while
  retaining the measurement discipline.
- **Executor coupling.** Anthropic's scripts assume its CLI and session protocol; this library
  defines runner-agnostic evaluation outcomes in [`evaluation.md`](evaluation.md).
- **Frontmatter.** Anthropic-specific compatibility and tool fields are not part of the
  portable frontmatter contract.
- **Interaction model.** Evidence-grounded progress, simplest-complete scope, supported delegation, fresh-context verification, and inspectable conclusions are portable. Adaptive thinking, refusal/fallback tuning, and send-to-user mechanics are not.

## 5. Absorbed into core

- Evidence-grounded progress → `contract.md` §4.
- Implement only what the requested outcome requires; no speculative features, refactors, or abstractions. Do not add fallbacks or validation for impossible internal states; validate system boundaries. Keep complete end-to-end behavior. → `contract.md` §4.
- Delegation only when the runtime supports it → `contract.md` §4.
- Fresh-context verification → `evaluation.md` §1.
- Inspectable conclusions and evidence rather than reasoning-transcription requests → `contract.md` §4.
