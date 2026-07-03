# craft-skills

Work-craft Claude Code skills (research + engineering) by Beomsu Koh.

A personal marketplace of task-oriented skills for software and research work — kept separate from
[`bstack`](https://github.com/GoBeromsu/bstack) (personal / life / second-brain automation) so the
two domains never bleed into each other's context.

---

## Skills

| Skill | Purpose |
|-------|---------|
| `documents` | Project documentation system — `docs/` folder ontology (research / spec / plan / ADR / rule), the research→ADR→plan decision pipeline, and routing for what belongs where. |
| `worktree` | `git wt <issue#>` dedicated-worktree workflow, git-guard self-install, and optional remote execution via Tailscale + tmux. |
| `init` | Dual-entry bootstrap + cartography — scaffolds the `docs/` ontology + ADR rails (Phase 0), then generates a complexity-scored hierarchical `AGENTS.md` knowledge base (Phases 1–4, ported from init-deep) in one pass. |
| `skillify` | Vendored skill-authoring promotion gate — create, update, move, or promote craft-skills skills through a two-layer review gate. |
| `technical-report` | Build and enforce a project's canonical technical report — Scaffold mode interviews depth-by-depth to fill a per-project `technical-report.yaml` frame; Author/Validate mode writes/reviews section markdown against it and gates structure + source coverage with two validators. |

---

## Install Matrix

### Claude Code

Install via the marketplace (interactive, inside Claude Code):

```
/plugin marketplace add GoBeromsu/craft-skills
/plugin install craft-skills@craft-skills
```

Then invoke any skill by name, e.g. `documents`, `worktree`, `init`, `skillify`.

---

### Codex

Install via the Codex plugin marketplace:

```bash
codex plugin marketplace add GoBeromsu/craft-skills
codex plugin add craft-skills@craft-skills
```

For local validation while developing this repository:

```bash
codex plugin marketplace add ./
codex plugin list --marketplace craft-skills --available --json
codex plugin add craft-skills@craft-skills --json
```

The Codex plugin exposes the tracked `skills/` tree through
`plugins/craft-skills/skills -> ../../skills`.

---

### Hermes

Mount `skills/` via `skills.external_dirs` in your Hermes config:

1. Clone the repo:
   ```bash
   git clone https://github.com/GoBeromsu/craft-skills.git ~/dev/GoBeromsu/craft-skills
   ```
2. Add the mount to `${HERMES_HOME}/config.yaml`:
   ```yaml
   skills:
     external_dirs:
       - /Users/<you>/dev/GoBeromsu/craft-skills/skills
   ```
   Use a literal absolute path — Hermes expands `~` but not `${VARS}` in config paths.
3. Restart the gateway:
   ```bash
   hermes gateway restart
   ```
4. Verify:
   ```bash
   hermes skills list | grep -E 'documents|worktree|init|skillify'
   ```

See `.hermes/README.md` for full deployment details and the future skillify protection hook.

---

### Generic / Other Agents (Cursor, Gemini, Copilot, etc.)

Skills are plain Markdown — any agent that can ingest instruction files can use them.
Point the agent's instruction-file import at the skill you want:

```
skills/documents/SKILL.md
skills/worktree/SKILL.md
skills/init/SKILL.md
skills/skillify/SKILL.md
```

No runtime-specific config required.

---

### Convenience Installer

For Codex and Hermes, a POSIX-sh installer is provided:

```bash
./install.sh codex    # clone the repo to ~/dev/GoBeromsu/craft-skills
./install.sh hermes   # print the config snippet to paste into ${HERMES_HOME}/config.yaml
./install.sh claude   # print the Claude Code marketplace commands
./install.sh all      # run all three
```

The script is idempotent and safe to re-run.

---

## Validation

```bash
claude plugin validate .
codex plugin marketplace add ./
codex plugin list --marketplace craft-skills --available --json
codex plugin add craft-skills@craft-skills --json
```

## License

MIT
