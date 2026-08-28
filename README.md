# craft-skills

Work-craft Agent Skills for research and engineering by Beomsu Koh.

Own your craft, vendor-neutral: all 27 packages use the plain Agent Skills `SKILL.md` layout.
The portable core contains no runtime-specific behavior; Claude Code, Codex, Hermes, Cursor,
and Grok-native integration lives in runtime lenses and generated instruction-file adapters.
This is a task-oriented library for software and research work — kept separate from
[`bstack`](https://github.com/GoBeromsu/bstack)
(personal / life / second-brain automation) so the two domains never bleed into each other's
context.

---

## Skills

| Skill | Purpose |
|-------|---------|
| `agents` | Build and change LLM-agent systems — prompts, tool schemas, context/tracing wiring — under an eval-first discipline that proves a behavior change against a versioned eval set before shipping. |
| `api` | Define contract-first public HTTP APIs with stable resource URLs, DTO-only success payloads, pagination, and diagnosable sanitized failures. |
| `browser` | Route browser work to Aside first, except when an explicit tool or an existing authenticated browser session is required; enforce safety preflight, recovery, and cleanup. |
| `ast-grep` | Search and replace code by syntax-tree shape with ast-grep, validating parseable patterns and inspecting a dry-run before mutation. |
| `backend` | Route backend engineering through an architecture-detection gate (layered / vertical-slice / hexagonal), then apply dependency-direction rules, persistence choices, and per-framework folder conventions. |
| `cicd` | Design inexpensive, reliable PR validation and reversible Jenkins Compose deployment pipelines with deployment-server-owned image builds. |
| `debug` | Diagnose a failing program under a hypothesis-driven loop — reproduce before theorizing, log fact separately from inference, and confirm the mechanism with instrumentation before any fix lands. |
| `defuddle` | Extract clean Markdown or metadata JSON from web articles and docs with the Defuddle CLI — strips nav/ads/boilerplate and falls back to a headless browser for JS-heavy pages. |
| `distil` | Distil transferable rules and conventions from an external source — a repo, an article, an AGENTS.md, or a third-party skill — into the library under the authoring contract, with provenance recorded. |
| `document` | Route documentation into the `docs/` ontology while keeping ADR authoring explicit-only unless the user asks to record a decision. |
| `frontend` | Gate frontend engineering on a rendering-architecture decision (SPA / SSR-RSC / SSG / islands) before UI code is written, then apply component-reuse, state-placement, and folder rules. |
| `git` | Guide version-control craft — ground-truth and incumbent-style detection, the atomic-commit split protocol, commit/branch/PR conventions, and non-interactive-safe history surgery, including the `git wt` worktree workflow. |
| `gpu` | Apply GPU environment and resource discipline — probe the hardware before choosing any install, budget the host before launching any job — to CUDA/PyTorch setup, attention-backend builds, and GPU job launches. |
| `guardrails` | Turn a convention into local, deterministic enforcement — runtime hooks, linter and formatter configuration, and pre-commit guards — so a violation is blocked before it happens, not corrected after. |
| `init` | Bootstrap the craft-owned `docs/` scaffold on a fresh repo, then generate a complexity-scored hierarchical `AGENTS.md` knowledge base on a mature one, in one triaged run. |
| `ml` | Apply ML/DL research-engineering discipline — reproducible project layout, leakage-safe dataset construction, and a training-discipline ladder — to classical ML, deep learning, fine-tuning, and vision work. |
| `obsidian` | Route reusable Obsidian Markdown, Bases, Canvas, Mermaid, CLI, Web Clipper, plugin-doctor, and headless Sync work through one thick skill with selectively loaded sub-recipes. |
| `programming` | Apply correctness-first, type-strict engineering discipline when writing or editing Python or TypeScript. |
| `refactor` | Restructure code without changing what it does, each move backed by a detection command and threshold, gated behind a characterization-test protocol for untested legacy code. |
| `research` | Run a decision-depth research workflow ending in a `docs/research/{slug}.md` artifact — sweep primary sources, synthesize with a citation on every claim, and state gaps and confidence, never the decision itself. |
| `security` | Find and fix vulnerabilities across web, API, and LLM surfaces, mapping every trust boundary first and triaging by production reachability and severity second. |
| `skillify` | Own the full lifecycle of craft-skills packages — create, update, move, retire — through an eval-first authoring loop and deterministic format validation. |
| `tailscale` | Verify and repair the Tailscale tailnet that carries cross-host work — SSH, remote process inspection, `scp` — before a dependent workflow runs, triaging failures as network-layer versus service-layer across macOS daemon variants. |
| `testing` | Architect and audit the test suite — classify each test by taxonomy and resource-based size, place it via a decision tree, and enforce the prove-it law that every bug fix ships with a failing-then-passing test. |
| `vmware` | Operate VMware Fusion guests through VM lifecycle checks and VNC-backed input automation. |
| `write-prd` | Author decision-ready product requirements documents from a provided or packaged template, keeping scope, metrics, rollout, and open issues coherent. |
| `write-report` | Scaffold and author a project's one-off canonical technical report against a single YAML frame whose depth is the enforced table of contents. |

---

## Install and discovery

| Runtime | Vendor-native install or documented discovery path |
|---|---|
| Claude Code | Marketplace package |
| Codex | Plugin marketplace package; plain Agent Skills clone is auxiliary development context |
| Hermes | Standalone Hermes plugin |
| Cursor | Project or user skills in `.cursor/skills`; plain Agent Skills discovery also supports `.agents/skills` |
| Grok-native | Skills in `.grok/skills` or a configured plugin path |
| Plain Agent Skills | One `SKILL.md` directory per skill under `.agents/skills` |

### Claude Code — marketplace

Use the Claude Code marketplace channel:

```
/plugin marketplace add GoBeromsu/craft-skills
/plugin install craft-skills@craft-skills
```

Then invoke any of the 27 skills above by name, e.g. `api`, `ast-grep`, `defuddle`, `document`,
`init`, `skillify`, `programming`, `research`, `write-prd`, `debug`.

---

### Codex — plugin or plain Agent Skills

The observed Codex plugin marketplace channel is:

```bash
codex plugin marketplace add GoBeromsu/craft-skills
codex plugin add craft-skills@craft-skills --json
```

Marketplace package metadata is tracked in `.codex-plugin/plugin.json`.

For plain Agent Skills development context, clone into a project-root `.agents/skills` directory:

```bash
git clone https://github.com/GoBeromsu/craft-skills.git .agents/skills/craft-skills
```

The clone is optional development context; its skills have the nested layout
`.agents/skills/craft-skills/skills/<name>/SKILL.md`.

---

### Hermes — plugin

Install the repository root as a standalone plugin:

1. Install and enable the plugin:
   ```bash
   hermes plugins install GoBeromsu/craft-skills --enable
   ```
2. Restart the gateway:
   ```bash
   hermes gateway restart
   ```
3. Verify the namespaced plugin skills:
   ```bash
hermes plugins list --plain --no-bundled
# In a Hermes session: skill_view(name='craft-skills:write-prd')
   ```

Namespacing preserves any existing bare-name owner such as bstack's `skillify`.
Install from the repository root because the `.hermes` subdirectory is intentionally rejected.

See `.hermes/README.md` for full deployment details.

---

### Cursor — documented skills directories

Cursor discovers project skills in `.cursor/skills/<name>/SKILL.md`; its Agent Skills
compatibility also recognizes `.agents/skills/<name>/SKILL.md`. Copy or link the individual
plain skill directories there using the deployment mechanism appropriate for the project.
No Cursor plugin manifest or CLI command is provided by this repository.

### Grok-native — documented skills or plugin configuration

Grok-native discovers plain skills at `.grok/skills/<name>/SKILL.md`, or through its configured
plugin path. Use the vendor's configured plugin mechanism for the latter; this repository does
not invent a Grok plugin manifest or command.

### Plain Agent Skills layout

Each package is a self-contained `skills/<name>/SKILL.md`. For a generic Agent Skills runtime,
place the desired package directory at `.agents/skills/<name>/SKILL.md`. The portable core is
the same file used by every runtime; lenses hold runtime-specific guidance.

### Operational deployment verification

For the approved `m1-pro` deployment, verify the discovered skill directories and runtime
behavior only through the approved Tailscale/Orca SSH route. This is operational verification
guidance, not a vendor install command.

---

### Convenience Installer

The repository's convenience installer prints the observed Claude Code, Codex, and Hermes
channels:

```bash
./install.sh codex    # print the Codex plugin commands
./install.sh codex --clone /path/to/project  # optionally clone development context
./install.sh hermes   # print the Hermes plugin command and profile-relative config snippet
./install.sh claude   # print the Claude Code marketplace commands
./install.sh all      # run all three
```

The script is idempotent and safe to re-run.

---

## Validation

`scripts/ci-local.sh` mirrors every required CI gate locally (pr-size, both Layer-1 validators, distribution-version, harness-portable, marketplace validation) and is the merge gate whenever GitHub Actions cannot run:

```bash
bash scripts/ci-local.sh
```

Enable the tracked git hooks once per clone — pre-commit runs the fast Layer-1 pair, pre-push runs the full mirror:

```bash
git config core.hooksPath .githooks
```

`SKIP_LOCAL_CI=1` bypasses a hook once; `SKIP_MARKETPLACES=1` skips the claude/codex CLI job.
Individual checks can still be run directly (`claude plugin validate .`, `python3 skills/skillify/scripts/validate-skill-format.py`).

Codex reads the tracked plugin tree directly. Hermes integration is covered by the isolated
plugin install/load contract test under `scripts/governance/tests/`.

## License

MIT
