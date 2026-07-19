# craft-skills — Hermes Integration

Hermes installs craft-skills from the repository root. The root plugin registers
every package as a read-only namespaced plugin skill.

## Install

```bash
hermes plugins install GoBeromsu/craft-skills --enable
```

The install target is `${HERMES_HOME}/plugins/craft-skills`. The `.hermes`
subdirectory contains integration guidance only, so it is not a plugin install
target.

## Discover Skills

The initializer scans the plugin-owned `skills/` directory and registers all 31
packages under the `craft-skills:` namespace. It does not add hooks, tools,
middleware, commands, or bare-name collisions. For example, use
`skill_view(name='craft-skills:write-prd')`.

Restart Hermes after changing the profile configuration, then verify discovery:

```bash
hermes gateway restart
hermes plugins list --plain --no-bundled
```
