# Phase 4 — Review & Deduplicate

## Per-file review

For each generated `AGENTS.md`:

- Remove generic advice (anything that would apply to *any* project).
- Remove content duplicated from the parent file (**dedup-vs-parent**).
- Trim to the size budget: **root 50–150 lines, subdir 30–80 lines.**
- Verify telegraphic style — terse, scannable, no prose padding.

## Quality anti-patterns (reject on sight)

- **Unjustified fan-out** — select agent coverage from unresolved high-risk questions, not repository size alone (Phase 1).
- **Sequential when fan-out was available** — on agent-spawn runtimes, explore + LSP + codegraph run
  concurrently. (Sequential is correct *only* on single-agent runtimes.)
- **Ignoring existing** — always read existing AGENTS.md first, even under `--create-new`.
- **Over-documenting** — not every directory needs an `AGENTS.md`; respect the Phase 2 cutoffs.
- **Redundancy** — a child never repeats its parent.
- **Generic content** — remove anything true of all projects.
- **Verbose style** — telegraphic or die.

## Completion-report inputs

Provide the cartography values required by the [completion report](../SKILL.md#completion-report):
runtime path, centrality measurement status, directories analyzed, created/updated `AGENTS.md`
files, and managed-block action. Name unavailable evidence explicitly.
