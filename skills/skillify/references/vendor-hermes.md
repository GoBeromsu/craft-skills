# Hermes Lens (Hermes Agent)

## 1. Source

Retrieved 2026-08-28:

- [Hermes Agent repository](https://github.com/NousResearch/hermes-agent), including its [skill-creation guide](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/creating-skills.md), [skills guide](https://github.com/NousResearch/hermes-agent/tree/main/website/docs/user-guide/skills), and in-repository skill-authoring guidance.

For native packaging, consult the official [plugin developer guide](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/plugins/index.md) and the installed loader/help.
Model prompting, tap installation, plugin registration, and actual effective loading are separate contracts.

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

- Hermes distribution is runtime plumbing: this library ships through a custom tap (`hermes skills tap add GoBeromsu/craft-skills`, one install unit per package), which copies the whole unit and scans every file with the skills guard — only a `safe` verdict installs without `--force`, so prose and scripts stay scanner-clean. Portable core instructions must not depend on Hermes discovery, naming, or precedence behavior.
- A tap unit, a plugin hook, and a registered plugin skill have different consumers. Inspect actual namespace/discovery behavior, recursive contents, and frontmatter support before choosing or equating them. A missing scanner dependency or incompatible private API is unverified, not a `safe` result.
- Hermes rich metadata, including `metadata.hermes.*`, tool/environment requirements, templated bodies, and scheduling-oriented fields, are lens-only product capabilities. For script inputs, `metadata.hermes.config` declares non-secret settings such as paths and top-level `required_environment_variables` declares secrets, as consumed by `tools/skills_tool_setup.py`. Verify the installed setup/config consumers and keep secret values out of source or receipts. Runtime acceptance does not override the destination's narrower frontmatter policy.
- Hermes-managed authoring, approval, hub, and smoke-test surfaces are runtime operations, not universal commands. This lens intentionally defines no cross-runtime command from them.

## 4. Divergences from this library

- **Discovery and metadata.** Hermes may use plugin namespaces and rich metadata to select or hide skills. This library's core remains plain Agent Skills-compatible Markdown and does not depend on Hermes names, metadata, plugins, or precedence.
- **Description budget.** Hermes's own index may impose a much shorter house limit than this library's portable trigger-description guidance. Each limit serves its runtime's routing surface and is not averaged into a false universal rule.
- **Dynamic and scheduled bodies.** Runtime interpolation, load-time execution, and schedule-oriented fields are not portable skill behavior; this library keeps static Markdown instructions and externalizes automation.
- **Field versus official.** Native local experimentation is not official-cache editing or automatic canonical promotion. Record source class and content provenance rather than inferring authorship from a missing package name.
- **Headless operation.** Inspect actual host capabilities and required credentials. A headless gateway does not prove that an app-backed CLI is unavailable, and support documentation does not prove a new package was loaded.

## 5. Absorbed into core

- Preserve field corrections and unique work; use requested, evidence-bound formal promotion → `lifecycle.md` §§3 and 5.
- Attention-budget distinction and concise trigger text → `contract.md` §3.
- Remove stale/no-op prose; pair important rules with completion evidence → `contract.md` §4.
- Reusable procedural craft rather than project-local declarative facts → the admission check in `SKILL.md`.
- Declared inputs (config plus required environment) → confirms the declared-inputs rule in `runtime-hygiene.md`; Hermes injects declared config into context on load and passes declared secrets into sandboxes.
