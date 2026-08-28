# OpenAI Lens (Codex / OpenAI)

## 1. Source

Retrieved 2026-08-28:

- [`openai/skills` at `49f948faa9258a0c61caceaf225e179651397431`](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431), especially the historical `skills/.system/skill-creator` package. This repository remains a useful creator-pattern source, but is **deprecated as a distribution source**.
- [`openai/plugins` at `6d99ee149c9fe3c7a55b96cab062cadc1ad36a9d`](https://github.com/openai/plugins/tree/6d99ee149c9fe3c7a55b96cab062cadc1ad36a9d), the current OpenAI distribution source.
- [OpenAI latest-model guide](https://developers.openai.com/api/docs/guides/latest-model).

## 2. Portable lesson

**Match instruction freedom to task fragility.** Give a robust task an outcome and room to
choose; give a brittle task a prescribed sequence and verification. This degree-of-freedom
rule prevents both unnecessary micromanagement and ambiguous critical workflows.

**Make progressive disclosure deliberate.** Keep a concise trigger description and a compact
SKILL.md; place material used only while executing in `scripts/`, `references/`, or `assets/`.
Bundle a script when repeatable deterministic work would otherwise be recreated. Put detailed
reference material behind an explicit need, not in the default reading path.

**Prompts set action boundaries.** Keep each instruction owned in one authoritative place.
Use lean, direct portable prompts, and state which actions proceed autonomously and which require approval rather than leaving that boundary to inference.

**Change evidence before model or effort.** Before changing model or effort settings, run representative evaluations for the actual task.
Use task-shaped deterministic processing for repeatable, order-sensitive work rather than optimizing a generic benchmark.

## 3. Runtime plumbing (OpenAI-only)

- `agents/openai.yaml` is OpenAI product metadata, not portable skill instruction. Its
  display, prompt, icon, brand, and declared-tool fields belong only in an OpenAI adapter.
- GPT-5.6 parameters, including OpenAI-documented effort controls, are OpenAI API concerns. They do not belong in universal SKILL.md guidance.
- Programmatic Tool Calling is an OpenAI API pattern, not a portable processing requirement. Its API-specific mechanics stay in this lens.
- The historical creator package demonstrates the `scripts/`, `references/`, and `assets/`
  layout and its recommended `agents/openai.yaml` adapter. Its repository status does not make
  that adapter a universal package requirement.
- `openai/plugins` is the distribution path; do not infer a distribution command from this
  lens. Follow the current runtime's documented installation surface.

## 4. Divergences from this library

- **Distribution.** This library keeps runtime-neutral source packages; OpenAI distribution
  metadata is isolated in a lens or adapter. The deprecated `openai/skills` checkout is never
  treated as the current OpenAI distribution mechanism.
- **Frontmatter and product fields.** `agents/openai.yaml` and any OpenAI-only fields are not
  admitted into the portable contract.
- **Prompt tuning.** GPT-5.6 parameters and Programmatic Tool Calling API mechanics remain OpenAI-only. The portable rule is to improve instructions, task shape, and evidence first.

## 5. Absorbed into core

- Lean portable prompts → `contract.md` §4.
- Explicit action and approval boundaries → `contract.md` §4.
- Representative model/effort evaluation → `evaluation.md` §7.
- Task-shaped deterministic processing → `contract.md` §5.
