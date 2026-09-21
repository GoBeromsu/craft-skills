# Cursor Lens

Local context for targeting Cursor skill discovery and packaging.
Official Cursor skills stay unmodified on their official channels; this file records uncovered library boundaries and source links, not copied product instructions.
Consult current official docs when a runtime form is unknown; apply [contract §10](contract.md#10-external-facts-and-dependencies) on create/update.
A version or help check is not compatibility or deployment proof.

## 1. Source

Official surfaces to consult first:

- [Cursor Agent Skills](https://prod.cursor.com/docs/skills)
- Current Cursor documentation on its official channel

Do not invent Cursor CLI flags or Cloud Agent APIs that official docs do not currently name.

## 2. Portable lesson

A skill is a directory containing `SKILL.md`, with optional `scripts/`, `references/`, and `assets/`; detailed material loads on demand.
Cursor uses `name` and `description` to identify and select a skill, matching the portable package model.
Scripts are referenced from `SKILL.md` with paths relative to the skill root.

## 3. Runtime plumbing (Cursor-only)

Exact current roots, recursive-walk rules, and Cloud/SSH scoping belong to official Cursor docs and installed help — do not copy a command sheet here.

- Native project and user skill roots, plus any compatible Claude/Codex roots Cursor currently accepts, are adapter facts. Verify them from current docs before an explicitly requested Cursor-native operation.
- The optional `paths`, `disable-model-invocation`, `icon`, and `color` frontmatter fields are Cursor-only plumbing. Do not add them to the portable core.
- User-level roots are local-machine state. Do not assume they copy to Cloud Agents, remote SSH Agent sessions, or managed workers unless current official docs say so; prefer project skills in the repository when that is the documented portable path.

If a native Cursor surface is uncertain, leave it unknown rather than inventing a command.

## 4. Divergences from this library

- **Official originals.** Cursor product usage stays on official channels. This library does not fork, patch, or republish those skills.
- **Topology.** Recursive discovery is a runtime convenience, not a library topology rule: this library remains one flat package per skill with no nested `SKILL.md`.
- **Frontmatter.** Cursor presentation and invocation-control fields stay lens-only so the universal contract remains vendor-neutral.
- **Evidence.** Cursor-specific eval or UI checks are not generated-run gates for this library (`contract.md` §7).

## 5. Absorbed into core

- Optional `scripts/`, `references/`, and `assets/` validate the package-parts decision rule in `contract.md` §5.
- Progressive loading supports keeping `SKILL.md` focused and moving depth to references.
- Recursive discovery is not a nested-`SKILL.md` license → `contract.md` §4.
- Runtime discovery, scoping, invocation controls, and Custom Mode presentation remain lens-level plumbing → `contract.md` §11.
