# Hermes Lens (Hermes Agent)

## 1. Source

Retrieved 2026-08-28:

- [Hermes Agent repository](https://github.com/NousResearch/hermes-agent), including its
  [skill-creation guide](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/creating-skills.md),
  [skills guide](https://github.com/NousResearch/hermes-agent/tree/main/website/docs/user-guide/skills),
  and in-repository skill-authoring guidance.

## 2. Portable lesson

**Capture reusable procedural craft, then curate conservatively.** Record a correction after
it is learned; retire or archive stale guidance deliberately rather than silently deleting it.
Protect human-authored material during maintenance.

**Use the attention budget, not only parser limits.** Always-loaded discovery text must be
short enough to route well. Keep procedural detail in the loaded skill body and its on-demand
resources, rather than making the index carry it.

**Keep instructions checkable.** Co-locate an important rule with its caveat, example, and
verification when that context is necessary. Delete stale sediment and no-op prose instead of
preserving it for appearance.

**Skills are procedural; memory is declarative.** A skill contains reusable how-to knowledge
loaded on demand. Compact facts needed on every turn belong to memory or another runtime-owned
context mechanism.

## 3. Runtime plumbing (Hermes-only)

- Hermes plugin installation and namespaced discovery are runtime plumbing. A plugin can expose
  packages under a namespace and resolve names according to its own precedence rules; portable
  core instructions must not require that discovery behavior.
- Hermes rich metadata, including `metadata.hermes.*`, tool/environment requirements, templated
  bodies, and scheduling-oriented fields, are lens-only product capabilities. For script inputs,
  `metadata.hermes.config` declares non-secret settings such as paths and top-level
  `required_environment_variables` declares secrets. They do not extend the portable skill
  contract.
- Hermes-managed authoring, approval, hub, and smoke-test surfaces are runtime operations, not
  universal commands. This lens intentionally defines no cross-runtime command from them.

## 4. Divergences from this library

- **Discovery and metadata.** Hermes may use plugin namespaces and rich metadata to select or
  hide skills. This library's core remains plain Agent Skills-compatible Markdown and does not
  depend on Hermes names, metadata, plugins, or precedence.
- **Description budget.** Hermes's own index may impose a much shorter house limit than this
  library's portable trigger-description guidance. Each limit serves its runtime's routing
  surface and is not averaged into a false universal rule.
- **Dynamic and scheduled bodies.** Runtime interpolation, load-time execution, and
  schedule-oriented fields are not portable skill behavior; this library keeps static Markdown
  instructions and externalizes automation.

## 5. Absorbed into core

- Record corrections; archive or deprecate conservatively; protect human-authored work →
  `lifecycle.md` §§3 and 5.
- Attention-budget distinction and concise trigger text → `contract.md` §3.
- Remove stale/no-op prose; pair important rules with completion evidence →
  `contract.md` §4.
- Reusable procedural craft rather than project-local declarative facts → the admission check
  in `SKILL.md`.
- Declared inputs (config plus required environment) → confirms the declared-inputs rule in
  `runtime-hygiene.md`; Hermes injects declared config into context on load and passes declared
  secrets into sandboxes.
