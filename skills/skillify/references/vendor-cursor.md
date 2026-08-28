# Cursor Lens

## 1. Source

Official documentation: [Cursor Agent Skills](https://prod.cursor.com/docs/skills).

## 2. Portable core

- A skill is a directory containing `SKILL.md`, with optional `scripts/`, `references/`, and `assets/`; detailed material loads on demand.
- Cursor uses `name` and `description` to identify and select a skill, matching the portable package model.
- Scripts are referenced from `SKILL.md` with paths relative to the skill root.

## 3. Runtime plumbing and divergence

- Native roots are project `.agents/skills/` and `.cursor/skills/`, plus user `~/.agents/skills/` and `~/.cursor/skills/`; Cursor also accepts compatible Claude and Codex roots.
- Cursor walks a skills root recursively and discovers every `SKILL.md`; it also discovers `.agents/skills/` and `.cursor/skills/` inside nested project directories, where those skills are scoped to that subtree.
- The optional `paths`, `disable-model-invocation`, `icon`, and `color` frontmatter fields are Cursor-only plumbing. Do not add them to the portable core.
- User-level roots are local-machine state. Cursor does not copy them to Cloud Agents, remote SSH Agent sessions, or managed workers; use project skills in the repository or bake them into a worker image.

## 4. Absorbed into core

- Optional `scripts/`, `references/`, and `assets/` validate the package-parts decision rule in `contract.md` §5.
- Progressive loading supports keeping `SKILL.md` focused and moving depth to references.
- Recursive discovery is a runtime convenience, not a library topology rule: this library remains one flat package per skill with no nested `SKILL.md`.
- Runtime discovery, scoping, invocation controls, and Custom Mode presentation remain lens-level plumbing so the universal contract stays vendor-neutral.
