# Provenance

Cross-skill lineage registry: the source skill(s) each craft-skills skill derives from.

This table is the **current at-a-glance snapshot**. The dated, per-change detail — *what* was
adapted and *when* — lives in each skill's `CHANGELOG.md` `Provenance:` clause; this registry links
back to it the way `architecture.md` links to ADRs without restating them.

Provenance never lives in `SKILL.md` (body or frontmatter): the recipe is present-tense imperative
only, and naming a source there fails skillify's attribution gate.

## Registry

| skill | origin | upstream repo / ref | relationship |
|---|---|---|---|
| `documents` | `documentation-and-adrs` SSOT | addyosmani/agent-skills | derived |
| `programming` | `programming` skill; ponytail; gajae-code agent discipline | code-yeongyu/lazycodex, DietrichGebert/ponytail (MIT) | adapted |
| `worktree` | git-guard scripts (6) | eldercare-fall-ai | vendored |
| `skillify` | two-layer discipline; skill-anatomy format SSOT; compact-name style | gstack (Garry Tan), addyosmani/agent-skills, code-yeongyu/lazycodex | adapted |
| `hookify` | hook patterns/philosophy; Claude Code hooks model; git `core.hooksPath` convention | Yeachan-Heo/oh-my-claudecode, Claude Code hooks docs | adapted |
| `init` | — | — | original |
| `technical-report` | — | — | original (promoted from a project-local skill) |

## Relationship vocabulary

- **derived** — built directly on the source's model, then thickened/adapted for this repo.
- **adapted** — specific principles or rules lifted and dissolved into this skill's recipe.
- **vendored** — concrete files (scripts, hooks) copied in and maintained here.
- **original** — no external source skill; authored for this repo.

## Recording rule

When a skill is created or materially re-sourced:

1. Add or update its row above (the current snapshot).
2. Add a dated `Provenance:` clause to that skill's `CHANGELOG.md` bullet (the per-change detail):
   `- YYYY-MM-DD — <why; what changed>; Provenance: <what> adapted from <source> @ <repo/ref>.`
3. Never put the attribution in `SKILL.md` — body or frontmatter.
