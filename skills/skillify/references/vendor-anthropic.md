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

**Design long work as a bounded execution.** For long-running work, preserve useful intermediate
evidence and delegate independent bounded slices when the runtime supports it. Do not ask a
model to expose private reasoning; request inspectable outputs, decisions, and evidence instead.

## 3. Runtime plumbing (Claude-only)

- The pinned Anthropic package's runner, stream handling, throwaway command injection, and
  packaging format depend on Claude Code. They are implementation details of that runtime, not
  a portable evaluation protocol.
- Claude adaptive-thinking controls, refusal behavior, and runtime fallback behavior are
  Claude-specific. They stay out of universal SKILL.md instructions.
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
- **Interaction model.** Strong instructions and evidence-grounded progress are portable;
  adaptive thinking, refusal/fallback tuning, and interruption mechanics are not.

## 5. Absorbed into core

- Baseline comparison, fresh sessions, snapshots, and representative held-out evaluation →
  `evaluation.md` §§1 and 5.
- Evidence-first grading; blind comparison; analyzer separation of skill versus eval defects →
  `evaluation.md` §2.
- Realistic queries, near-miss negatives, and trigger evaluation → `evaluation.md` §3 and
  `contract.md` §3.
- Brief strong instructions, evidence-grounded progress, bounded delegation, and
  simplest-complete scope → `contract.md` §4.
- Inspectable conclusions and evidence rather than reasoning-extraction requests →
  `contract.md` §4.
