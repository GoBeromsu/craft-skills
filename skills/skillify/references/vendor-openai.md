# OpenAI Lens (Codex / OpenAI)

Local context for targeting Codex or consulting OpenAI skill-creator craft.
Official OpenAI skills and Codex distribution stay unmodified on their official channels; this file records uncovered library boundaries, source links, and divergences — not copied product instructions or a re-hosted evaluator harness.
Consult current official docs when a runtime form is unknown; apply [contract §10](contract.md#10-external-facts-and-dependencies) on create/update.

## 1. Source

Official surfaces to consult first:

- [OpenAI latest-model guide](https://developers.openai.com/api/docs/guides/latest-model)
- Current Codex / OpenAI plugin and skills documentation on their official channels
- [`openai/plugins`](https://github.com/openai/plugins), the current OpenAI distribution source at last comparison (`6d99ee149c9fe3c7a55b96cab062cadc1ad36a9d`)

Historical comparison snapshot (deprecated as a distribution source, not a local SSOT): [`openai/skills` at `49f948faa9258a0c61caceaf225e179651397431`](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431), especially the historical `skills/.system/skill-creator` package.
Latest comparison: `openai/skills` `main` still resolves to `49f948f` and `skills/.system/skill-creator` last changed at `4ab6e0f` (`SKILL.md` sha256 `a17383bf…`), so the comparison is a verified no-op; §4–§5 hold the full keep/amend/decline disposition.
A coordinator-verified working-host fact at authoring time was Codex `0.155.1`; that is not multi-runtime compatibility evidence and must be re-probed per [contract §10](contract.md#10-external-facts-and-dependencies).
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
Do not add generic repeated consent for reversible in-scope work.

**Change evidence before model or effort.**
Before changing model or effort settings, run representative checks for the actual task.
Use task-shaped deterministic processing for repeatable, order-sensitive work rather than optimizing a generic benchmark or copying an upstream eval harness.

## 3. Runtime plumbing (OpenAI-only)

- `agents/openai.yaml` is OpenAI product metadata, not portable skill instruction. Its display, prompt, icon, brand, and declared-tool fields belong only in an OpenAI adapter.
- Model-specific effort and tool/API controls belong to the selected OpenAI API contract, not universal SKILL.md guidance.
- Verify each API-specific processing mechanism against its actual provider documentation instead of promoting a vendor feature name into a portable requirement.
- The historical creator package demonstrates the `scripts/`, `references/`, and `assets/` layout and its recommended `agents/openai.yaml` adapter. Its repository status does not make that adapter a universal package requirement.
- `openai/plugins` is the distribution path; do not infer a distribution command from this lens. Follow the current runtime's documented installation surface.
- Do not copy OpenAI evaluator scripts or require their generated outputs in this repository.

## 4. Divergences from this library

- **Official originals.** OpenAI product usage stays on official channels. This library does not fork, patch, or republish those skills.
- **Distribution.** This library keeps runtime-neutral source packages; OpenAI distribution metadata is isolated in a lens or adapter. The deprecated `openai/skills` checkout is never treated as the current OpenAI distribution mechanism.
- **Frontmatter and product fields.** `agents/openai.yaml` and any OpenAI-only fields are not admitted into the portable contract.
- **Prompt tuning.** Model-specific parameters and API mechanics remain in their runtime boundary. Improve instructions, task shape, and evidence first.
- **Evidence policy.** Upstream evaluation suggestions are not universal corpus counts, wording-locked harnesses, or proof that every supported runtime was tested. Local acceptance follows the actual requested behavior and effect (`contract.md` §7).
- **Package history.** The OpenAI creator forbids `CHANGELOG.md`, `README.md`, and other auxiliary files inside a skill; this library keeps a per-package `CHANGELOG.md` as the single history owner (`contract.md` §6) and ships no README. A destination that forbids the file keeps history in its own store.
- **Declined mechanisms.** `init_skill.py`, `quick_validate.py`, and `generate_openai_yaml.py` scaffolds are Codex product tooling; this library's format validator and package-parts table own the same checks portably. Tool-namespaced names (`gh-address-comments`) are not adopted; §2 naming keeps one or two tokens.
- **Kept as confirmations.** Concise-is-key and "only add what the model lacks", degrees of freedom, three-level progressive disclosure with one-level-deep references and a table of contents past 100 lines, concrete-example planning, running added scripts, and iterating on real usage are all already core.

## 5. Absorbed into core

- Lean portable prompts → `contract.md` §4.
- Explicit action and approval boundaries → `contract.md` §4.
- Representative model/effort evaluation → `evaluation.md` §7.
- Task-shaped deterministic processing → `contract.md` §5.
