# craft-skills — Hermes Integration

Hermes v0.18.2 installs craft-skills from the repository root. The root plugin
loads as a zero-registration bridge; recursive skill discovery comes from the
plugin-owned `skills/` directory through `skills.external_dirs`.

## Install

```bash
hermes plugins install GoBeromsu/craft-skills --enable
```

The install target is `${HERMES_HOME}/plugins/craft-skills`. The `.hermes`
subdirectory contains integration guidance only, so it is not a plugin install
target.

## Discover Skills

**Hermes mount path:** `plugins/craft-skills/skills`.

Add the profile-relative plugin skill path to `${HERMES_HOME}/config.yaml`:

```yaml
skills:
  external_dirs:
    - plugins/craft-skills/skills
```

Hermes resolves relative entries against the active `HERMES_HOME` and scans the
directory recursively for `SKILL.md`. The bridge preserves the repository's
flat 30-package tree and registers no plugin skills, hooks, tools, middleware,
or commands.

When both bstack and craft-skills are installed, bstack owns the first bare
`skillify` lookup. Keep its path first:

```yaml
skills:
  external_dirs:
    - plugins/bstack/skills
    - plugins/craft-skills/skills
```

Restart Hermes after changing the profile configuration, then verify discovery:

```bash
hermes gateway restart
hermes skills list | grep -E 'agents|api|skillify|write-report'
hermes plugins list --user --json
```
