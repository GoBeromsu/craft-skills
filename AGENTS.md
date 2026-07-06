# craft-skills — Agent Operating Guide

Engineering and research work-craft skills for Claude Code, Codex, and Hermes. Kept strictly
separate from `bstack` (personal / life / second-brain automation) so the two domains never
share context.

---

## 1. Folder Tree

```
craft-skills/
├── .claude-plugin/
│   ├── marketplace.json         # Claude Code marketplace registry
│   └── plugin.json              # Plugin metadata (name, version, author, license)
├── .claude/
│   └── CLAUDE.md                # Thin deferral → AGENTS.md (Claude Code reads this)
├── .codex/
│   └── config.yaml              # Codex CLI project config (AGENTS.md read natively)
├── .hermes/
│   └── README.md                # Hermes mount instructions (skills.external_dirs)
├── skills/                      ← Claude Code plugin mount + Hermes external_dirs target
│   ├── document/                # Documentation waypoint — docs/ ontology, routing, nested sub-recipes
│   │   ├── SKILL.md             #   waypoint: ontology + routing + docs/ layout + Children index
│   │   ├── references/          #   flattened sub-recipes: adr.md, readme.md, changelog.md, inline-comments.md, design.md
│   │   └── templates/           #   research/references/spec/plan/rule/architecture + adr/readme/changelog/design skeletons
│   ├── init/                    # Dual-entry: docs/ ontology bootstrap + hierarchical AGENTS.md cartography
│   │   ├── SKILL.md             #   triage: classify runtime → Phase 0 graft → orchestrate phases 1-4
│   │   ├── references/          #   phase-0-ontology (graft) + phase-1..4 (init-deep cartography engine)
│   │   └── CHANGELOG.md
│   ├── skillify/                # Vendored skill-authoring promotion gate (self-governing)
│   │   └── SKILL.md
│   ├── hookify/                 # Convention → local deterministic enforcement (runtime hook/lint/pre-commit) + starter guards
│   │   └── SKILL.md
│   ├── programming/             # Correctness-first Python/TypeScript engineering discipline + language references
│   │   └── SKILL.md
│   ├── frontend/                # Rendering-architecture-gated frontend engineering — SPA/SSR-RSC/SSG/islands rules + reuse/state/folder references
│   │   └── SKILL.md
│   ├── backend/                 # Architecture-gated backend engineering — layered/vertical-slice/hexagonal + API/folder references
│   │   └── SKILL.md
│   ├── ml/                      # ML/DL research engineering — layout/datasets/training/vision references
│   │   └── SKILL.md
│   ├── agents/                  # LLM-agent engineering — eval-first law, prompts-as-code, context/tracing references
│   │   └── SKILL.md
│   ├── testing/                 # Suite-level test architecture — structure/integration/e2e references
│   │   └── SKILL.md
│   ├── refactor/                # Behavior-preserving restructuring — smell/move catalogs + scripts/detect-smells.sh
│   │   └── SKILL.md
│   ├── git/                     # Version-control craft — atomic commits, conventions, history surgery
│   │   ├── SKILL.md
│   │   └── references/worktree.md  #   sub-recipe: git wt workflow + git-guard rails (propose-first install)
│   ├── security/                # Defensive security triage — web/API/LLM/secrets detection references
│   │   └── SKILL.md
│   ├── write-report/            # Canonical technical-report engine — YAML-frame TOC + structure/source validators
│   │   └── SKILL.md
│   └── PROVENANCE.md            # Cross-skill lineage registry — source skill per skill
├── install.sh                   # POSIX-sh multi-runtime convenience installer
├── AGENTS.md                    # ← this file (single source of truth for all runtimes)
└── README.md                    # Project overview + install matrix
```

---

## 2. Skills

One imperative sentence per skill. Load the skill's `SKILL.md` for the full recipe.

| Skill | What it does |
|-------|-------------|
| `document` | Waypoint that routes project documentation through the `docs/` ontology (research→ADR→plan pipeline) and loads nested sub-recipes on demand for ADRs, README, the project changelog, the comment-the-why convention, and the project design.md. |
| `init` | Dual-entry: bootstrap a project's `docs/` ontology + ADR rails (Phase 0 graft), then generate a complexity-scored hierarchical `AGENTS.md` knowledge base (Phases 1–4, init-deep cartography engine in `references/`), with a single-agent fallback for non-fan-out runtimes. |
| `skillify` | Create, update, move, or promote a craft-skills skill through the vendored two-layer promotion gate. |
| `hookify` | Turn a convention or SE best-practice into local deterministic enforcement (Claude Code / Codex runtime hook → lint → pre-commit), shipping a starter guard and red-proving it fires. |
| `programming` | Write/review Python and TypeScript with correctness-first discipline, loading the shared workflow plus per-language references before editing code. |
| `frontend` | Route frontend work through a PHASE 0 rendering-architecture gate (SPA / SSR-RSC / SSG / islands), then apply architecture-specific rules, component-reuse layers, state placement, and folder conventions — gated on the project's design.md. |
| `backend` | Route backend work through an architecture-detection gate (layered / vertical-slice / hexagonal), then apply dependency-direction rules, the API design contract law, and per-framework folder conventions. |
| `ml` | Run ML/DL research engineering through a task gate — reproducible `pyproject` + `src/` layout, leakage-safe dataset construction, the training-discipline ladder, and vision-specific practice. |
| `agents` | Build and change LLM agents under the eval-first law — prompts-as-code, tool design, and context/tracing discipline, handing tool-permission and consumption enforcement to `security`. |
| `testing` | Architect test suites — taxonomy with resource-based sizing, a placement decision tree, the prove-it bug-fix law, and structure/integration/e2e conventions each with a detection command. |
| `refactor` | Restructure code behavior-preservingly — when-to-refactor triggers, a characterization-test protocol for legacy code, a 17-smell detection catalog, a 12-move catalog, and `scripts/detect-smells.sh`. |
| `git` | Commit and rewrite history safely — atomic-commit split protocol, incumbent repo-style detection, commit/branch/PR conventions, and non-interactive-safe history surgery; the `worktree` sub-recipe runs the `git wt` worktree workflow with git-guard rails. |
| `security` | Triage defensive security across web, API, and LLM surfaces — trust-boundary mapping, per-class detection commands, reachability × severity triage, and secrets/dependency hygiene. |
| `write-report` | Scaffold a per-project `technical-report.yaml` frame through a depth-ordered interview, then author/review canonical section markdown against it under code-enforced structure and source-coverage gates. |

---

## 3. Multi-Runtime Model

Skills are plain Markdown. Any agent that can ingest instruction files can use them. Each
runtime loads this repository differently — the table below is the authoritative install
matrix. See `README.md` for the user-facing install commands.

| Runtime | How skills are loaded | Config entry point |
|---------|----------------------|--------------------|
| **Claude Code** | Marketplace plugin — `/plugin marketplace add GoBeromsu/craft-skills` then `/plugin install craft-skills@craft-skills`. Claude Code resolves `skills/` from `.claude-plugin/plugin.json`. | `.claude/CLAUDE.md` (defers here) |
| **Codex** | Clone the repo; Codex reads `AGENTS.md` natively for skill context. Per-project hook registration is optional via `.codex/config.yaml`. | `.codex/config.yaml` |
| **Hermes** | Mount `skills/` via `skills.external_dirs` in `${HERMES_HOME}/config.yaml`. Full instructions in `.hermes/README.md`. | `.hermes/README.md` |
| **Generic agents** (Cursor, Gemini, Copilot, etc.) | Point the agent's instruction-file import at `skills/<name>/SKILL.md` — each file is a self-contained Markdown recipe. | None required |

**Single source of truth — do not duplicate into per-runtime files.**  
`.claude/CLAUDE.md` and `.codex/config.yaml` contain no substantive content beyond a pointer
or minimal config. All operating conventions live here.

---

## 4. Skill Authoring Conventions

Skills live at `skills/<name>/SKILL.md`. Every `SKILL.md` opens with a YAML frontmatter
block using exactly these **5 keys**:

```yaml
---
name: <matches dir; ≤64 chars; lowercase/digits/hyphen; no leading/trailing/consecutive hyphen>
description: <real user trigger phrase + what it does; ≤1024 chars>
version: <3-part semver MAJOR.MINOR.PATCH>
allowed-tools: [Bash, Read, Edit, Grep]      # Claude Code tool names
compatibility: claude-code, codex, hermes    # intended runtimes; ≤500 chars
---
```

- `description` must be trigger-dense — real phrases a user types, not a capability blurb.
- **Thick skills carry nested sub-recipes.** A skill may be flat (default — one discovered
  `SKILL.md`) or a thick skill: a parent waypoint `SKILL.md` plus nested
  `skills/<skill>/<child>/SKILL.md` sub-recipes the parent `Read`s on demand (e.g. `documents/`
  with `adr/`, `readme/`, …). A sub-recipe carries only `name` + `description` (the
  agentskills.io minimum) and an optional colocated `template.md`; it shares its parent
  package's `version` and `CHANGELOG.md` and is **not** a separately discovered command (no
  `plugin.json` `skills` manifest entry, no RESOLVER). This is distinct from an *area*
  (≥2 sibling skills + RESOLVER). See `skills/skillify/references/schemas.md` §1.6 / §2.
- External binary requirements (`git`, `python3`, `tmux`, …) go in a `## Requirements` body
  section, not in frontmatter.
- Use `${ENV_VAR}` placeholders throughout. Never hardcode absolute paths.
- Keep `references/` sub-directories for sub-procedures and reference docs; the main `SKILL.md`
  stays at triage/decision depth.
- Recipe body is present-tense imperative operating instructions only. History belongs in
  `CHANGELOG.md`, not in `SKILL.md`.
- For skill authoring workflow, load the `skillify` skill.

### Version-bump criteria

| Bump | When | Confirmation required |
|------|------|-----------------------|
| `MAJOR` | Trigger phrase removed/renamed, `allowed-tools` gains entries callers must permission, or output format breaks downstream consumers | Yes |
| `MINOR` | New phase, flag, routing branch, or user-visible behavioral addition (backward-compatible) | Yes |
| `PATCH` | Bug fix, prose correction, checklist/dependency bump — no interface change | No |

### Provenance

Record where a skill came from — never in `SKILL.md` (body or frontmatter): the recipe is
present-tense imperative only, and naming a source there fails skillify's attribution gate.

- **Per-change credit → `CHANGELOG.md`.** On the bullet for the change that introduces or re-sources
  a skill, append a `Provenance:` clause:
  `- YYYY-MM-DD — <why; what changed>; Provenance: <what> adapted from <source> @ <repo/ref>.`
- **At-a-glance lineage → `skills/PROVENANCE.md`.** One row per skill mapping it to its source
  skill(s) and relationship (`derived` / `adapted` / `vendored` / `original`). This is the current
  snapshot; it links back to the dated `CHANGELOG.md` detail, never restating it.

This keeps the three surfaces MECE: `SKILL.md` is the recipe, `CHANGELOG.md` is the dated per-change
credit, and `skills/PROVENANCE.md` is the current cross-skill lineage view.

---

## 5. skillify Protection Governance

`skills/skillify/` is protected infrastructure. skillify owns skill CRUD (create, update, move,
promote, retire) for the entire craft-skills library. Arbitrary modification or deletion is
forbidden without explicit user permission.

When `.claude/hooks/protect-skillify.sh` is in place, `Write`, `Edit`, and `Bash(rm / mv / …)`
operations targeting `skills/skillify/**` are blocked by default across all runtimes.

### Lifting the deny for one operation

1. Grant explicit approval in the current turn.
2. Set the approval token in the shell running the agent:
   ```bash
   export SKILLIFY_EDIT_TOKEN="user-approved-$(openssl rand -hex 16)"
   ```
3. Protection is lifted while `SKILLIFY_EDIT_TOKEN` is set. Unset it immediately after:
   ```bash
   unset SKILLIFY_EDIT_TOKEN
   ```

### Hook locations (active once the script is authored)

| Runtime | Hook location |
|---------|--------------|
| Claude Code | `.claude/settings.json` PreToolUse → `.claude/hooks/protect-skillify.sh` |
| Codex | `.codex/config.yaml` `pre_tool_call` → `.claude/hooks/protect-skillify.sh` |
| Hermes | Merge block (see `.hermes/README.md`) into `${HERMES_HOME}/config.yaml` |

---

## 6. Env-Var Contract

Use `${ENV_VAR}` placeholders in all skill content. Never hardcode `/Users/<name>/…` literal paths.

| Variable | Meaning | Example placeholder |
|----------|---------|---------------------|
| `CRAFT_SKILLS_REPO_PATH` | Absolute path to this repo root — used by Hermes `external_dirs` mount. | `/path/to/craft-skills` |
| `CRAFT_WT_REMOTE_HOST` | Tailscale hostname for remote worktree exec (git skill's worktree sub-recipe; optional). | `m1-pro` |

---

## 7. What Hermes Loads

Hermes mounts `${CRAFT_SKILLS_REPO_PATH}/skills` via `skills.external_dirs`. Only files under
`skills/` are discoverable by Hermes. After any skill move or restructure, verify with
`hermes skills list` that updated skills are visible.

See `.hermes/README.md` for the exact config snippet and deployment steps.

---

## 8. Scope Discipline & Issue Routing

All repository work follows the issue-driven loop (`init` installs the canonical Development
Flow recipe into a project's `AGENTS.md`). One standing rail applies to this repo too:

- **Out-of-scope discoveries route to a new issue immediately.** When work — including a
  `deep-interview`/requirements session, planning, or implementation — surfaces a problem
  beyond the topic you started with, do not expand the current change to absorb it. Open a
  new GitHub issue capturing it (with exactly one Type label: `feat`, `fix`, `chore`, `docs`,
  `refactor`, or `test`), then keep the current work scoped to its original issue.
