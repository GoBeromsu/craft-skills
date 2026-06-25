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
│   ├── documents/               # Project documentation system — docs/ ontology, templates, routing
│   │   └── SKILL.md
│   ├── worktree/                # git wt workflow, git-guard self-install, optional remote exec
│   │   └── SKILL.md
│   ├── init/                    # Project bootstrap / rail-laying
│   │   └── SKILL.md
│   ├── skillify/                # Vendored skill-authoring promotion gate (self-governing)
│   │   └── SKILL.md
│   └── technical-report/        # Canonical technical-report engine — YAML-frame TOC + structure/source validators
│       └── SKILL.md
├── install.sh                   # POSIX-sh multi-runtime convenience installer
├── AGENTS.md                    # ← this file (single source of truth for all runtimes)
└── README.md                    # Project overview + install matrix
```

---

## 2. Skills

One imperative sentence per skill. Load the skill's `SKILL.md` for the full recipe.

| Skill | What it does |
|-------|-------------|
| `documents` | Author and route project documentation artifacts (research, spec, plan, ADR, rule) through the `docs/` ontology using the research→ADR→plan decision pipeline. |
| `worktree` | Run the `git wt <issue#>` dedicated-worktree workflow, self-install git-guard on first use, and optionally exec on a remote Tailscale host via tmux. |
| `init` | Bootstrap a project's `docs/` scaffold, wire standing conventions, and invoke each skill's self-installer in one explicit, one-time pass. |
| `skillify` | Create, update, move, or promote a craft-skills skill through the vendored two-layer promotion gate. |
| `technical-report` | Scaffold a per-project `technical-report.yaml` frame through a depth-ordered interview, then author/review canonical section markdown against it under code-enforced structure and source-coverage gates. |

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
| `CRAFT_WT_REMOTE_HOST` | Tailscale hostname for remote worktree exec (worktree skill; optional). | `m1-pro` |

---

## 7. What Hermes Loads

Hermes mounts `${CRAFT_SKILLS_REPO_PATH}/skills` via `skills.external_dirs`. Only files under
`skills/` are discoverable by Hermes. After any skill move or restructure, verify with
`hermes skills list` that updated skills are visible.

See `.hermes/README.md` for the exact config snippet and deployment steps.
