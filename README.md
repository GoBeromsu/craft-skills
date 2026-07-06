# craft-skills

Work-craft Claude Code skills (research + engineering) by Beomsu Koh.

Own your craft, vendor-agnostic: every skill here is a plain Markdown recipe with no lock-in
to one tool's plugin format, so the same file works across Claude Code, Codex, Hermes, or any
other instruction-following agent. A personal marketplace of task-oriented skills for software
and research work — kept separate from [`bstack`](https://github.com/GoBeromsu/bstack)
(personal / life / second-brain automation) so the two domains never bleed into each other's
context.

---

## Skills

| Skill | Purpose |
|-------|---------|
| `agents` | Build and change LLM-agent systems — prompts, tool schemas, context/tracing wiring — under an eval-first discipline that proves a behavior change against a versioned eval set before shipping. |
| `backend` | Route backend engineering through an architecture-detection gate (layered / vertical-slice / hexagonal), then apply dependency-direction rules, an API design contract, and per-framework folder conventions. |
| `debug` | Diagnose a failing program under a hypothesis-driven loop — reproduce before theorizing, log fact separately from inference, and confirm the mechanism with instrumentation before any fix lands. |
| `document` | Route any documentation task into a six-type `docs/` ontology (research, references, spec, plan, decision, rule) and author repo-level artifacts against their canonical templates. |
| `frontend` | Gate frontend engineering on a rendering-architecture decision (SPA / SSR-RSC / SSG / islands) before UI code is written, then apply component-reuse, state-placement, and folder rules. |
| `git` | Guide version-control craft — ground-truth and incumbent-style detection, the atomic-commit split protocol, commit/branch/PR conventions, and non-interactive-safe history surgery, including the `git wt` worktree workflow. |
| `hookify` | Turn a convention or best practice into local, deterministic enforcement so a violation is blocked before it happens, not corrected after. |
| `init` | Bootstrap a repo's `docs/` ontology and ADR rails on a fresh repo, then generate a complexity-scored hierarchical `AGENTS.md` knowledge base on a mature one, in one triaged run. |
| `ml` | Apply ML/DL research-engineering discipline — reproducible project layout, leakage-safe dataset construction, and a training-discipline ladder — to classical ML, deep learning, fine-tuning, and vision work. |
| `programming` | Apply correctness-first, type-strict engineering discipline when writing or editing Python or TypeScript. |
| `refactor` | Restructure code without changing what it does, each move backed by a detection command and threshold, gated behind a characterization-test protocol for untested legacy code. |
| `research` | Run a decision-depth research workflow ending in a `docs/research/{slug}.md` artifact — sweep primary sources, synthesize with a citation on every claim, and state gaps and confidence, never the decision itself. |
| `security` | Find and fix vulnerabilities across web, API, and LLM surfaces, mapping every trust boundary first and triaging by production reachability and severity second. |
| `skillify` | Own the full lifecycle of craft-skills packages — create, update, move, retire — through an eval-first authoring loop and deterministic format validation. |
| `testing` | Architect and audit the test suite — classify each test by taxonomy and resource-based size, place it via a decision tree, and enforce the prove-it law that every bug fix ships with a failing-then-passing test. |
| `write-report` | Scaffold and author a project's one-off canonical technical report against a single YAML frame whose depth is the enforced table of contents. |

---

## Install Matrix

### Claude Code

Install via the marketplace (interactive, inside Claude Code):

```
/plugin marketplace add GoBeromsu/craft-skills
/plugin install craft-skills@craft-skills
```

Then invoke any of the 16 skills above by name, e.g. `document`, `init`, `skillify`,
`programming`, `research`, `debug`.

---

### Codex

Codex reads `AGENTS.md` natively — no plugin install step is required. Skills are also
discoverable by cloning this repo into `.agents/skills`:

```bash
git clone https://github.com/GoBeromsu/craft-skills.git .agents/skills/craft-skills
```

Reference `AGENTS.md` from your own project's `AGENTS.md` to pull in the skill context.

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
   hermes skills list | grep -E 'agents|backend|debug|document|frontend|git|hookify|init|ml|programming|refactor|research|security|skillify|testing|write-report'
   ```

See `.hermes/README.md` for full deployment details.

---

### Generic / Other Agents (Cursor, Gemini, Copilot, etc.)

Skills are plain Markdown — any agent that can ingest instruction files can use them.
Point the agent's instruction-file import at the skill you want:

```
skills/agents/SKILL.md
skills/backend/SKILL.md
skills/debug/SKILL.md
skills/document/SKILL.md
skills/frontend/SKILL.md
skills/git/SKILL.md
skills/hookify/SKILL.md
skills/init/SKILL.md
skills/ml/SKILL.md
skills/programming/SKILL.md
skills/refactor/SKILL.md
skills/research/SKILL.md
skills/security/SKILL.md
skills/skillify/SKILL.md
skills/testing/SKILL.md
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
python3 skills/skillify/scripts/validate-skill-format.py
```

Codex and Hermes need no separate validation step — both read `AGENTS.md` / `SKILL.md`
directly from the tracked tree.

## License

MIT
