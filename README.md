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
| `api` | Define contract-first public HTTP APIs with stable resource URLs, DTO-only success payloads, pagination, and diagnosable sanitized failures. |
| `aside` | Drive the Aside AI browser (CLI, MCP server, or automation REPL) to do real work inside logged-in, authenticated web apps that a plain fetch or static extractor can't reach. |
| `ast-grep` | Search and replace code by syntax-tree shape with ast-grep, validating parseable patterns and inspecting a dry-run before mutation. |
| `backend` | Route backend engineering through an architecture-detection gate (layered / vertical-slice / hexagonal), then apply dependency-direction rules, persistence choices, and per-framework folder conventions. |
| `cicd` | Design inexpensive, reliable PR validation and reversible Jenkins Compose deployment pipelines with deployment-server-owned image builds. |
| `debug` | Diagnose a failing program under a hypothesis-driven loop — reproduce before theorizing, log fact separately from inference, and confirm the mechanism with instrumentation before any fix lands. |
| `defuddle` | Extract clean Markdown or metadata JSON from web articles and docs with the Defuddle CLI — strips nav/ads/boilerplate and falls back to a headless browser for JS-heavy pages. |
| `distil` | Distil transferable rules and conventions from an external source — a repo, an article, an AGENTS.md, or a third-party skill — into the library under the authoring contract, with provenance recorded. |
| `document` | Route documentation into the `docs/` ontology while keeping ADR authoring explicit-only unless the user asks to record a decision. |
| `frontend` | Gate frontend engineering on a rendering-architecture decision (SPA / SSR-RSC / SSG / islands) before UI code is written, then apply component-reuse, state-placement, and folder rules. |
| `git` | Guide version-control craft — ground-truth and incumbent-style detection, the atomic-commit split protocol, commit/branch/PR conventions, and non-interactive-safe history surgery, including the `git wt` worktree workflow. |
| `hookify` | Turn a convention or best practice into local, deterministic enforcement so a violation is blocked before it happens, not corrected after. |
| `init` | Bootstrap the craft-owned `docs/` scaffold on a fresh repo, then generate a complexity-scored hierarchical `AGENTS.md` knowledge base on a mature one, in one triaged run. |
| `ml` | Apply ML/DL research-engineering discipline — reproducible project layout, leakage-safe dataset construction, and a training-discipline ladder — to classical ML, deep learning, fine-tuning, and vision work. |
| `obsidian-bases` | Author and debug Obsidian Bases (`.base` files and `base` blocks) — filters, formulas, views, and `groupBy`/`sort` design for a readable dataset. |
| `obsidian-canvas` | Create and edit Obsidian JSON Canvas (`.canvas`) files — nodes, edges, groups, and connections per the JSON Canvas 1.0 spec, with edge-integrity validation. |
| `obsidian-cli` | Operate an Obsidian vault through the `obsidian-cli` binary — note reads/writes/search with write-then-readback verification and a destructive-op guard. |
| `obsidian-clipper` | Author selector-verified Obsidian Web Clipper JSON templates that map clipped fields to vault frontmatter. |
| `obsidian-doctor` | Diagnose and repair broken Obsidian plugins and Templater templates against an accumulating registry, driving Obsidian via obsidian-cli. |
| `obsidian-markdown` | Write Obsidian Flavored Markdown (wikilinks, embeds, callouts, properties) following a compact note house style. |
| `obsidian-mermaid` | Author Mermaid diagrams that render in Obsidian's pinned Mermaid 11.4.1, avoiding label-escaping and unsupported-diagram-type pitfalls. |
| `programming` | Apply correctness-first, type-strict engineering discipline when writing or editing Python or TypeScript. |
| `refactor` | Restructure code without changing what it does, each move backed by a detection command and threshold, gated behind a characterization-test protocol for untested legacy code. |
| `research` | Run a decision-depth research workflow ending in a `docs/research/{slug}.md` artifact — sweep primary sources, synthesize with a citation on every claim, and state gaps and confidence, never the decision itself. |
| `security` | Find and fix vulnerabilities across web, API, and LLM surfaces, mapping every trust boundary first and triaging by production reachability and severity second. |
| `skillify` | Own the full lifecycle of craft-skills packages — create, update, move, retire — through an eval-first authoring loop and deterministic format validation. |
| `testing` | Architect and audit the test suite — classify each test by taxonomy and resource-based size, place it via a decision tree, and enforce the prove-it law that every bug fix ships with a failing-then-passing test. |
| `write-prd` | Author decision-ready product requirements documents from a provided or packaged template, keeping scope, metrics, rollout, and open issues coherent. |
| `write-report` | Scaffold and author a project's one-off canonical technical report against a single YAML frame whose depth is the enforced table of contents. |

---

## Install Matrix

### Claude Code

Claude marketplace commands:

```
/plugin marketplace add GoBeromsu/craft-skills
/plugin install craft-skills@craft-skills
```

Then invoke any of the 30 skills above by name, e.g. `api`, `aside`, `ast-grep`, `defuddle`, `obsidian-markdown`,
`init`, `skillify`, `programming`, `research`, `write-prd`, `debug`.

---

### Codex

**Codex canonical channel:** install the plugin defined by `.codex-plugin/plugin.json`:

```bash
codex plugin marketplace add ./
codex plugin add craft-skills@craft-skills --json
```

**Codex auxiliary clone path:** `.agents/skills/craft-skills` from the user project's root:

```bash
git clone https://github.com/GoBeromsu/craft-skills.git .agents/skills/craft-skills
```

The clone is optional discovery context; its skills have the nested layout
`.agents/skills/craft-skills/skills/<name>/SKILL.md`.

---

### Hermes

**Hermes mount path:** `~/dev/GoBeromsu/craft-skills/skills`, via `skills.external_dirs` in your Hermes config:

1. Clone the repo:
   ```bash
   git clone https://github.com/GoBeromsu/craft-skills.git ~/dev/GoBeromsu/craft-skills
   ```
2. Add the mount to `${HERMES_HOME}/config.yaml`:
   ```yaml
   skills:
     external_dirs:
       - ~/dev/GoBeromsu/craft-skills/skills
   ```
   Use a literal absolute path — Hermes expands `~` but not `${VARS}` in config paths.
3. Restart the gateway:
   ```bash
   hermes gateway restart
   ```
4. Verify:
   ```bash
hermes skills list | grep -E 'agents|api|aside|ast-grep|backend|cicd|debug|defuddle|distil|document|frontend|git|hookify|init|ml|obsidian-bases|obsidian-canvas|obsidian-cli|obsidian-clipper|obsidian-doctor|obsidian-markdown|obsidian-mermaid|programming|refactor|research|security|skillify|testing|write-prd|write-report'
   ```

See `.hermes/README.md` for full deployment details.

---

### Generic / Other Agents (Cursor, Gemini, Copilot, etc.)

Skills are plain Markdown — any agent that can ingest instruction files can use them.
Point the agent's instruction-file import at the skill you want:

```
skills/api/SKILL.md
skills/aside/SKILL.md
skills/agents/SKILL.md
skills/backend/SKILL.md
skills/cicd/SKILL.md
skills/ast-grep/SKILL.md
skills/debug/SKILL.md
skills/defuddle/SKILL.md
skills/distil/SKILL.md
skills/document/SKILL.md
skills/frontend/SKILL.md
skills/git/SKILL.md
skills/hookify/SKILL.md
skills/init/SKILL.md
skills/ml/SKILL.md
skills/obsidian-bases/SKILL.md
skills/obsidian-canvas/SKILL.md
skills/obsidian-cli/SKILL.md
skills/obsidian-clipper/SKILL.md
skills/obsidian-doctor/SKILL.md
skills/obsidian-markdown/SKILL.md
skills/obsidian-mermaid/SKILL.md
skills/programming/SKILL.md
skills/refactor/SKILL.md
skills/research/SKILL.md
skills/security/SKILL.md
skills/skillify/SKILL.md
skills/testing/SKILL.md
skills/write-prd/SKILL.md
skills/write-report/SKILL.md
```

No runtime-specific config required.

---

### Convenience Installer

For Codex and Hermes, a POSIX-sh installer is provided:

```bash
./install.sh codex    # print the Codex plugin commands
./install.sh codex --clone /path/to/project  # optionally clone discovery context
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
