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

**Prompts are an ownership boundary.** Keep each instruction owned in one authoritative place;
state autonomy and approval boundaries explicitly. Prefer lean, direct prompts over repeated
context or generic exhortation.

**Change evidence before inference effort.** Before changing model or effort settings, run
representative evaluations for the actual task. Evaluate task-shaped work with the smallest
useful prompt–tool–check (PTC) loop, rather than optimizing a generic benchmark.

## 3. Runtime plumbing (OpenAI-only)

- `agents/openai.yaml` is OpenAI product metadata, not portable skill instruction. Its
  display, prompt, icon, brand, and declared-tool fields belong only in an OpenAI adapter.
- OpenAI model/API parameters, including effort controls, are Codex/OpenAI concerns. They do
  not belong in universal SKILL.md guidance.
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
- **Prompt tuning.** OpenAI-specific API parameters remain OpenAI-only. The portable rule is
  to improve instructions, task shape, and evidence first.

## 5. Absorbed into core

- Degree-of-freedom matched to fragility → `contract.md` §4.
- Concise progressive disclosure and purpose-driven `scripts/`, `references/`, and `assets/`
  → `contract.md` §5.
- One owner per instruction; explicit autonomy/approval limits; lean prompts → `contract.md`
  §4.
- Representative before/after evaluation and task-shaped prompt–tool–check loops →
  `evaluation.md` §§1–4.
- Description as the compact trigger surface, not a second copy of execution guidance →
  `contract.md` §3.
