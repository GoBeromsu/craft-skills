# craft-skills

Work-craft Claude Code skills (research + engineering) by Beomsu Koh.

A personal marketplace of task-oriented skills for software and research work — kept separate from
[`bstack`](https://github.com/GoBeromsu/bstack) (personal / life / second-brain automation) so the
two domains never bleed into each other's context.

---

## Skills

| Skill | Purpose |
|-------|---------|
| `document` | Project documentation system — `docs/` folder ontology (research / spec / plan / ADR / rule), the research→ADR→plan decision pipeline, routing for what belongs where, and sub-recipes for ADRs, README, changelog, comments, and the project design.md. |
| `init` | Dual-entry bootstrap + cartography — scaffolds the `docs/` ontology + ADR rails (Phase 0), then generates a complexity-scored hierarchical `AGENTS.md` knowledge base (Phases 1–4, ported from init-deep) in one pass. |
| `skillify` | Vendored skill-authoring promotion gate — create, update, move, or promote craft-skills skills through a two-layer review gate. |
| `hookify` | Turn a convention or engineering best-practice into local deterministic enforcement — choose the earliest reliable hook/lint/pre-commit surface, ship a starter guard, and red-prove it fires. |
| `programming` | Correctness-first Python and TypeScript engineering discipline — routes code edits through shared workflow rules plus language-specific references before writing. |
| `frontend` | Rendering-architecture-gated frontend engineering — SPA / SSR-RSC / SSG / islands absolute rules, component-reuse layers, state placement, and folder conventions, gated on the project's design.md. |
| `backend` | Architecture-gated backend engineering — layered / vertical-slice / hexagonal detection gate, dependency-direction rules, API design contract law, and per-framework folder conventions. |
| `ml` | ML/DL research engineering — reproducible `pyproject` + `src/` layout, leakage-safe dataset construction, the training-discipline ladder, and vision-specific practice. |
| `agents` | LLM-agent engineering — eval-first shipping law, prompts-as-code, tool design, and context/tracing discipline for building and changing agent behavior. |
| `testing` | Suite-level test architecture — taxonomy with resource-based sizing, placement decision tree, prove-it bug-fix law, and structure/integration/e2e conventions with detection commands. |
| `refactor` | Behavior-preserving restructuring — when-to-refactor triggers, characterization-test protocol for legacy code, 17-smell + 12-move catalogs, and a one-pass `detect-smells.sh`. |
| `git` | Version-control craft — atomic-commit split protocol, incumbent repo-style detection, commit/branch/PR conventions, and non-interactive-safe history surgery; includes the `git wt` worktree-workflow sub-recipe with git-guard rails. |
| `security` | Defensive security triage across web, API, and LLM surfaces — trust-boundary mapping, per-class detection commands, severity triage, and secrets/dependency hygiene. |
| `write-report` | Build and enforce a project's canonical technical report — Scaffold mode interviews depth-by-depth to fill a per-project `technical-report.yaml` frame; Author/Validate mode writes/reviews section markdown against it and gates structure + source coverage with two validators. |

---

## Install Matrix

### Claude Code

Install via the marketplace (interactive, inside Claude Code):

```
/plugin marketplace add GoBeromsu/craft-skills
/plugin install craft-skills@craft-skills
```

Then invoke any skill by name, e.g. `document`, `init`, `skillify`, `programming`, `frontend`, `backend`, `ml`, `agents`, `testing`, `refactor`, `git`, `security`, `hookify`, `write-report`.

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

The Codex plugin root is the repository root, so the tracked `skills/` tree is
packaged directly.

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
   hermes skills list | grep -E 'document|init|skillify|programming|frontend|backend|ml|agents|testing|refactor|git|security|hookify|write-report'
   ```

See `.hermes/README.md` for full deployment details and the future skillify protection hook.

---

### Generic / Other Agents (Cursor, Gemini, Copilot, etc.)

Skills are plain Markdown — any agent that can ingest instruction files can use them.
Point the agent's instruction-file import at the skill you want:

```
skills/document/SKILL.md
skills/init/SKILL.md
skills/skillify/SKILL.md
skills/programming/SKILL.md
skills/frontend/SKILL.md
skills/backend/SKILL.md
skills/ml/SKILL.md
skills/agents/SKILL.md
skills/testing/SKILL.md
skills/refactor/SKILL.md
skills/git/SKILL.md
skills/security/SKILL.md
skills/hookify/SKILL.md
skills/write-report/SKILL.md
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
