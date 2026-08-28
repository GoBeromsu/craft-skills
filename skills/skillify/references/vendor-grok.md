# Grok Lens

## 1. Source

Official documentation: [Grok Skills, Plugins & Marketplaces](https://docs.x.ai/build/features/skills-plugins-marketplaces).

## 2. Portable core

- Skills are reusable folders of Markdown instructions, scripts, and resources.
- `SKILL.md` frontmatter can identify a skill with `name` and describe its trigger with `description`.
- Enabled plugins can contribute a `skills/` directory, while the skill package itself remains portable.

## 3. Runtime plumbing and divergence

- Grok discovers project skills from `./.grok/skills/` while walking upward to the repository root, user skills from `~/.grok/skills/`, enabled plugin `skills/` directories, and extra `[skills] paths` in `~/.grok/config.toml`.
- Plugin roots are project `./.grok/plugins/`, user `~/.grok/plugins/`, marketplace installs under `~/.grok/plugins/marketplaces/`, extra `[plugins] paths` in `~/.grok/config.toml`, and CLI `--plugin-dir` paths.
- User-invocable skills become slash commands such as `/<skill-name>`.
- The `when-to-use`/`when_to_use`, `paths`, `argument-hint`, `user-invocable`, and `disable-model-invocation` fields are Grok-only plumbing. Do not add them to the portable core.
- `allowed-tools` is non-enforcing: it neither grants nor restricts tools. It is therefore not a portable capability or security declaration.
- Grok reads Claude Code marketplaces, plugins, skills, MCPs, agents, hooks, and instruction files without configuration; this compatibility is runtime behavior, not a reason to duplicate Claude-specific package metadata.

## 4. Absorbed into core

- The explicit distinction between reusable instructions and runtime-owned discovery/configuration reinforces the portable-core boundary.
- Slash invocation is an adapter feature; portable skill prose states the workflow rather than a runtime command.
- `paths` may improve a Grok runtime's surfacing, but its vendor semantics stay outside the universal contract.
- Grok's Claude compatibility validates interoperable `SKILL.md` packages without making Claude fields part of the common schema.
