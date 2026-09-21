# Grok Lens

Local context for Grok model guidance and, when explicitly selected, the Grok-native runtime.
Official xAI skills and Grok CLI distribution stay unmodified on their official channels; this file records uncovered library boundaries and source links, not copied product instructions.
Supporting the model through another agent does not require a Grok CLI or add a deployment target.
Consult current official docs when a runtime form is unknown; apply [contract §10](contract.md#10-external-facts-and-dependencies) on create/update.
A version or help check is not compatibility or deployment proof.

## 1. Source

Official surfaces to consult first:

- [Grok 4.6 model guidance](https://docs.x.ai/developers/grok-4-6.md) for the selected model and API
- [Grok Skills, Plugins & Marketplaces](https://docs.x.ai/build/features/skills-plugins-marketplaces) only for the separate Grok-native runtime
- Installed Grok CLI help when a native Grok operation is explicitly requested

A coordinator-verified working-host fact at authoring time was Grok CLI stable `1.0.34`; that is not multi-runtime compatibility evidence and must be re-probed per [contract §10](contract.md#10-external-facts-and-dependencies).

## 2. Portable lesson

Skills are reusable folders of Markdown instructions, scripts, and resources.
`SKILL.md` frontmatter can identify a skill with `name` and describe its trigger with `description`.
Enabled plugins can contribute a `skills/` directory, while the skill package itself remains portable.
Keep model-specific parameters and runtime-specific packaging separate; record actual evidence instead of requiring a preferred Grok judge or a fixed multi-model quorum.

## 3. Runtime plumbing (Grok-native only)

Apply discovery facts only to the documented Grok-native runtime after verifying its installed version and help for an explicitly requested native operation.
Do not infer paths, permission semantics, or marketplace capabilities from the model name alone.
Exact current roots, config keys, and slash-command forms belong to official Grok docs and installed help — do not copy a command sheet here.

- The `when-to-use`/`when_to_use`, `paths`, `argument-hint`, `user-invocable`, and `disable-model-invocation` fields are Grok-only plumbing. Do not add them to the portable core.
- `allowed-tools` is non-enforcing on this runtime: it neither grants nor restricts tools. It is therefore not a portable capability or security declaration.
- Documented Claude compatibility, if present, is runtime behavior, not a reason to duplicate Claude-specific package metadata and not proof that this package is installed or effectively loaded.

If a native Grok surface is uncertain, leave it unknown rather than inventing a command.

## 4. Divergences from this library

- **Official originals.** xAI product usage stays on official channels. This library does not fork, patch, or republish those skills.
- **Discovery.** Grok-native roots and marketplace installs are adapter facts. Portable skill prose states the workflow rather than a runtime slash command.
- **Evidence.** Upstream evaluation suggestions are not universal corpus counts or generated-run gates (`contract.md` §7).
- **Compatibility claims.** A listed Claude-compatible loader is not deployment proof.

## 5. Absorbed into core

- Reusable instructions versus runtime-owned discovery/configuration → `contract.md` §11.
- Slash invocation as adapter, not portable prose → `contract.md` §4.
- Vendor `paths` and invocation fields stay outside the universal contract → `contract.md` §1.
