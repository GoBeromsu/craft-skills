# OpenAI Lens (Codex / OpenAI)

## 1. Source

Retrieved 2026-08-28:

- [`openai/skills` at `49f948faa9258a0c61caceaf225e179651397431`](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431), especially the historical `skills/.system/skill-creator` package. This repository remains a useful creator-pattern source, but is **deprecated as a distribution source**.
- [`openai/plugins` at `6d99ee149c9fe3c7a55b96cab062cadc1ad36a9d`](https://github.com/openai/plugins/tree/6d99ee149c9fe3c7a55b96cab062cadc1ad36a9d), the current OpenAI distribution source.
- [OpenAI latest-model guide](https://developers.openai.com/api/docs/guides/latest-model).

Use the selected model's current guide for Astra-specific controls; model guidance and the Codex runtime's native distribution are separate contracts.

## 2. Portable lesson

**Match instruction freedom to task fragility.**
Give a robust task an outcome and room to choose; give a brittle task a prescribed sequence and verification.
This degree-of-freedom rule prevents both unnecessary micromanagement and ambiguous critical workflows.

**Make progressive disclosure deliberate.**
Keep a concise trigger description and a compact SKILL.md; place material used only while executing in `scripts/`, `references/`, or `assets/`.
Bundle a script when repeatable deterministic work would otherwise be recreated.
Put detailed reference material behind an explicit need, not in the default reading path.

**Prompts set action boundaries.**
Keep each instruction owned in one authoritative place.
Use lean, direct portable prompts, and state which actions proceed autonomously and which require approval rather than leaving that boundary to inference.

**Change evidence before model or effort.**
Before changing model or effort settings, run representative evaluations for the actual task.
Use task-shaped deterministic processing for repeatable, order-sensitive work rather than optimizing a generic benchmark.

## 3. Runtime plumbing (OpenAI-only)

- `agents/openai.yaml` is OpenAI product metadata, not portable skill instruction. Its display, prompt, icon, brand, and declared-tool fields belong only in an OpenAI adapter.
- Model-specific effort and tool/API controls belong to the selected OpenAI API contract, not universal SKILL.md guidance.
- Verify each API-specific processing mechanism against its actual provider documentation instead of promoting a vendor feature name into a portable requirement.
- The historical creator package demonstrates the `scripts/`, `references/`, and `assets/` layout and its recommended `agents/openai.yaml` adapter. Its repository status does not make that adapter a universal package requirement.
- `openai/plugins` is the distribution path; do not infer a distribution command from this lens. Follow the current runtime's documented installation surface.

## 4. Divergences from this library

- **Distribution.** This library keeps runtime-neutral source packages; OpenAI distribution metadata is isolated in a lens or adapter. The deprecated `openai/skills` checkout is never treated as the current OpenAI distribution mechanism.
- **Frontmatter and product fields.** `agents/openai.yaml` and any OpenAI-only fields are not admitted into the portable contract.
- **Prompt tuning.** Model-specific parameters and API mechanics remain in their runtime boundary. Improve instructions, task shape, and evidence first.
- **Evidence policy.** Upstream evaluation suggestions are not universal corpus counts or proof that every supported runtime was tested. Local acceptance follows the actual requested behavior and effect.

## 5. Absorbed into core

- Lean portable prompts → `contract.md` §4.
- Explicit action and approval boundaries → `contract.md` §4.
- Representative model/effort evaluation → `evaluation.md` §7.
- Task-shaped deterministic processing → `contract.md` §5.
