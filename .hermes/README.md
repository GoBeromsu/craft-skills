# craft-skills — Hermes Integration

This directory documents how to mount craft-skills into a Hermes Agent installation.
No hook scripts live here yet; a `hooks/` subdirectory will be added once
`.claude/hooks/protect-skillify.sh` is authored.

---

## Mount via skills.external_dirs

Hermes loads skills from an external directory by adding an entry to
`${HERMES_HOME}/config.yaml`. Add the block below, then restart the gateway.

```yaml
# In ${HERMES_HOME}/config.yaml — merge under the existing skills: key,
# or add the full block if none exists yet.
skills:
  external_dirs:
    - /path/to/craft-skills/skills   # replace with your actual clone path
                                     # or use ${CRAFT_SKILLS_REPO_PATH}/skills
                                     # NOTE: Hermes expands ~ but NOT ${VARS} in
                                     # config.yaml paths — use a literal absolute path.
```

**Steps:**

1. Clone this repo to a stable location (suggested: `~/dev/GoBeromsu/craft-skills`).
2. Set `CRAFT_SKILLS_REPO_PATH` in your shell profile:
   ```bash
   export CRAFT_SKILLS_REPO_PATH="$HOME/dev/GoBeromsu/craft-skills"
   ```
3. Merge the `skills.external_dirs` block above into `${HERMES_HOME}/config.yaml`
   using the literal clone path (not a `${VAR}` expansion).
4. Restart the gateway:
   ```bash
   hermes gateway restart
   ```
5. Verify skills are visible:
   ```bash
   hermes skills list | grep -E 'document|git|init|skillify|write-prd'
   ```

**ASSUMPTION NOTE:** The `skills.external_dirs` key name and config.yaml merge behaviour
are based on the Hermes Agent documented interface. If your installed Hermes version uses
a different key (e.g. `external_skill_dirs`), check with `hermes --help | grep -i external`
and adjust accordingly.

---

## Future: skillify Write-Protection Hook

Once `.claude/hooks/protect-skillify.sh` is authored and made executable (`+x`), a
Hermes `pre_tool_call` hook can be wired to block unauthorized writes to
`skills/skillify/**`. The hook block to merge into `${HERMES_HOME}/config.yaml` will
look like:

```yaml
# Future hook block — do not activate until protect-skillify.sh exists
# hooks:
#   pre_tool_call:
#     - matcher: "terminal|write_file|patch|Bash|Write|Edit"
#       command: "~/dev/GoBeromsu/craft-skills/.claude/hooks/protect-skillify.sh"
#       timeout: 10
```

**Key contract notes (verified from Hermes source):**

- Event key is `pre_tool_call` (not `pre_tool_use` — that is Claude Code's key).
- Hermes dispatches via `shlex.split(os.path.expanduser(command))` with `shell=False`,
  so a leading `~` expands to `$HOME` but `${VARS}` do not — use a literal `~/...` path.
- Deny protocol: stdout `{"decision":"block","reason":"..."}` + exit non-zero.
- A hook does not fire until allowlisted. For a headless launchd gateway, set
  `hooks_auto_accept: true` in `config.yaml` (or `HERMES_ACCEPT_HOOKS=1`) before restart.
  The `--accept-hooks` flag is `hermes gateway run` (foreground) only.

Create this file (`protect-skillify-hermes.yaml`) in `.hermes/hooks/` once the script
is ready, mirroring the pattern documented in the bstack reference repo.
