# Hermes Lens (Hermes Agent)

Local context for targeting Hermes or consulting its skill-authoring craft.
Official Hermes skills stay unmodified on their official channels; this file records uncovered library boundaries, source links, and divergences — not copied product instructions or a re-hosted evaluator harness.
Consult current official docs and installed loader/help when a runtime form is unknown; apply [contract §10](contract.md#10-external-facts-and-dependencies) on create/update.
A version or help check is not compatibility or deployment proof.
Model prompting, tap installation, plugin registration, and actual effective loading are separate contracts.

## 1. Source

Official surfaces to consult first:

- [Hermes skills guide](https://github.com/NousResearch/hermes-agent/tree/main/website/docs/user-guide/skills)
- [Skill-creation guide](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/creating-skills.md)
- [Plugin developer guide](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/plugins/index.md)
- Installed Hermes loader/help

Historical comparison snapshot (not a local SSOT): [Hermes Agent repository](https://github.com/NousResearch/hermes-agent) as retrieved 2026-08-28.
Coordinator-verified working-host facts at authoring time were Hermes `v0.21.3` / upstream release `v2026.9.14`; those are not multi-runtime compatibility evidence and must be re-probed per [contract §10](contract.md#10-external-facts-and-dependencies).

## 2. Portable lesson

**Keep field learning separate from formal promotion.**
Preserve a useful correction in its identifiable native field context without automatically changing the official package.
Harvest requested packages and narrowly linked provenance through the current authoring/admission boundary.
Preserve unique work and dependencies before an authorized retirement; do not require a compatibility stub or broadly ingest memory and conversations.

**Use the attention budget, not only parser limits.**
Always-loaded discovery text must be short enough to route well.
Keep procedural detail in the loaded skill body and its on-demand resources, rather than making the index carry it.

**Keep instructions checkable.**
Co-locate an important rule with its caveat, example, and verification when that context is necessary.
Delete stale sediment and no-op prose instead of preserving it for appearance.

**Skills are procedural; memory is declarative.**
A skill contains reusable how-to knowledge loaded on demand.
Compact facts needed on every turn belong to memory or another runtime-owned context mechanism.

## 3. Runtime plumbing (Hermes-only)

- Hermes tap, plugin, scanner, and install commands belong to current official Hermes docs and installed help. Do not copy a command sheet into portable `SKILL.md`.
- A tap unit, a plugin hook, and a registered plugin skill have different consumers. Inspect actual namespace/discovery behavior, recursive contents, and frontmatter support before choosing or equating them. A missing scanner dependency or incompatible private API is unverified, not a `safe` result.
- Hermes rich metadata, including `metadata.hermes.*`, tool/environment requirements, templated bodies, and scheduling-oriented fields, are lens-only product capabilities. Verify the installed setup/config consumers from official docs; keep secret values out of source or receipts. Runtime acceptance does not override the destination's narrower frontmatter policy.
- Hermes-managed authoring, approval, hub, and smoke-test surfaces are runtime operations, not universal commands. This lens invents no cross-runtime command from them.
- Do not copy Hermes evaluator or smoke-test harnesses, or require their generated outputs, in this repository.

If a native Hermes surface is uncertain, leave it unknown rather than inventing a command.

## 4. Divergences from this library

- **Official originals.** Hermes product usage stays on official channels. This library does not fork, patch, or republish those skills.
- **Discovery and metadata.** Hermes may use plugin namespaces and rich metadata to select or hide skills. This library's core remains plain Agent Skills-compatible Markdown and does not depend on Hermes names, metadata, plugins, or precedence.
- **Description budget.** Hermes's own index may impose a much shorter house limit than this library's portable trigger-description guidance. Each limit serves its runtime's routing surface and is not averaged into a false universal rule.
- **Dynamic and scheduled bodies.** Runtime interpolation, load-time execution, and schedule-oriented fields are not portable skill behavior; this library keeps static Markdown instructions and externalizes automation.
- **Field versus official.** Native local experimentation is not official-cache editing or automatic canonical promotion.
- **Headless operation.** Inspect actual host capabilities and required credentials. A headless gateway does not prove that an app-backed CLI is unavailable, and support documentation does not prove a new package was loaded.

## 5. Absorbed into core

- Preserve field corrections and unique work; use requested, evidence-bound formal promotion → `lifecycle.md` §§3 and 5.
- Attention-budget distinction and concise trigger text → `contract.md` §3.
- Remove stale/no-op prose; pair important rules with completion evidence → `contract.md` §4.
- Reusable procedural craft rather than project-local declarative facts → the admission check in `SKILL.md`.
- Declared inputs (config plus required environment) → confirms the declared-inputs rule in `runtime-hygiene.md`.
