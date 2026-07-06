# craft-skills — Agent Operating Guide

Engineering and research work-craft skills for any coding agent — Claude Code, Codex, Hermes,
or a generic instruction-following agent. This is the operator's own accumulated craft, kept
vendor-agnostic on purpose: every skill is a plain Markdown recipe, portable across runtimes
with no lock-in to one tool's frontmatter or plugin format. Kept strictly separate from
`bstack` (personal / life / second-brain automation) so the two domains never share context.

## Layout

A package is one flat directory: `skills/<name>/SKILL.md` plus whichever of `references/`,
`templates/`, `scripts/`, `tests/`, and `CHANGELOG.md` it needs. No nested `SKILL.md` files —
every skill is one level deep. `evals/` directories are local, gitignored scratch for the
eval-first authoring loop; they are never committed.

The 17 packages (alphabetical): `agents`, `backend`, `debug`, `distil`, `document`, `frontend`,
`git`, `hookify`, `init`, `ml`, `programming`, `refactor`, `research`, `security`, `skillify`,
`testing`, `write-report`.

The authoring contract — frontmatter shape, naming, description rules, body limits, CHANGELOG
format, and the eval-first loop — lives at `skills/skillify/references/contract.md`. All skill
create/update/move/retire work routes through the `skillify` skill; nothing here duplicates
that contract.

## Install matrix

| Runtime | How skills are loaded |
|---------|------------------------|
| **Claude Code** | Marketplace plugin — `/plugin marketplace add GoBeromsu/craft-skills` then `/plugin install craft-skills@craft-skills`. |
| **Codex** | Reads `AGENTS.md` natively; skills are also discoverable by cloning this repo into `.agents/skills`. |
| **Hermes** | Mount `skills/` via `skills.external_dirs` — see `.hermes/README.md`. |
| **Generic agents** (Cursor, Gemini, Copilot, etc.) | Point the instruction-file import at `skills/<name>/SKILL.md`; each file is self-contained. |

## Environment variables

| Variable | Meaning |
|----------|---------|
| `CRAFT_SKILLS_REPO_PATH` | Absolute path to this repo root — used by Hermes's `external_dirs` mount. |
| `CRAFT_WT_REMOTE_HOST` | Tailscale hostname for remote worktree exec (the worktree recipe now lives in the `git` skill's `references/worktree.md`; optional). |

## Rails

- Skill changes ship as branch → PR through the `skillify` skill. Edits under `skills/skillify/`
  additionally require explicit operator approval in the current session — no enforcement hook
  is installed for this; it is a human/agent judgment gate only.
- Out-of-scope discoveries route immediately to a new GitHub issue with exactly one `type: X`
  label, rather than expanding the current change to absorb them.
- CHANGELOG bullets are one compact line: `- YYYY-MM-DD — [vX.Y.Z: ]why → what.`
- Provenance is two-tier: per-change credit lives in the package's own `CHANGELOG.md`; the
  current cross-skill lineage snapshot lives in `skills/PROVENANCE.md`.
- Governance harness: `python3 scripts/governance/harness.py --config <repos.json>` where
  `repos.json` is `{"repos":[{"name":"craft-skills","path":"<repo root>"}]}`.
