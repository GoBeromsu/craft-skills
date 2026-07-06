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
| `document` | `documentation-and-adrs` SSOT; design.md section contract (`design/` sub-recipe) | addyosmani/agent-skills; code-yeongyu/lazycodex (MIT) | derived |
| `distil` | operator's own WIP draft (absorbed 2026-07-06) | — | original |
| `programming` | `programming` skill; ponytail ladder + never-cut list + root-cause rule; gajae-code agent discipline; TS clean-code + smell catalog | [code-yeongyu/lazycodex](https://github.com/code-yeongyu/lazycodex), [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) (MIT), [labs42io/clean-code-typescript](https://github.com/labs42io/clean-code-typescript) (MIT) | adapted |
| `frontend` | design-first gate and router shape; rendering-architecture/state/folder rules original synthesis | code-yeongyu/lazycodex (MIT; pattern-only) | adapted |
| `backend` | API observed-behavior + one-version rules; architecture-detection rules original synthesis | addyosmani/agent-skills | adapted |
| `ml` | training-discipline ladder; layout/dataset rules original synthesis | "A Recipe for Training Neural Networks" (A. Karpathy) | adapted |
| `agents` | — (hardening hand-off boundaries align with OWASP Top 10 for LLM Applications) | — | original |
| `testing` | resource-based test sizes; prove-it bug-fix law; DAMP-over-DRY | addyosmani/agent-skills | adapted |
| `refactor` | smell-detection catalog format; 12-move refactoring catalog; naming/function/comment smell entries | [code-yeongyu/lazycodex](https://github.com/code-yeongyu/lazycodex) (MIT); Martin Fowler, *Refactoring* (2nd ed.); [labs42io/clean-code-typescript](https://github.com/labs42io/clean-code-typescript) (MIT) | adapted |
| `git` | ground-truth command block; repo-style detection; `references/worktree.md` git-guard scripts (6) | code-yeongyu/lazycodex (MIT) `git-master`; eldercare-fall-ai | adapted (scripts vendored) |
| `security` | threat-model-first workflow; dependency-audit triage; LLM hardening rules | addyosmani/agent-skills; OWASP Top 10 for LLM Applications | adapted |
| `skillify` | two-layer discipline; skill-anatomy format SSOT; compact-name style | gstack (Garry Tan), addyosmani/agent-skills, code-yeongyu/lazycodex | adapted |
| `hookify` | hook patterns/philosophy; Claude Code hooks model; git `core.hooksPath` convention | Yeachan-Heo/oh-my-claudecode, Claude Code hooks docs | adapted |
| `init` | — | — | original |
| `write-report` | — | — | original (promoted from a project-local skill) |
| `research` | — | — | original (skill-library redesign) |
| `debug` | — | — | original (skill-library redesign) |

## Relationship vocabulary

- **derived** — built directly on the source's model, then thickened/adapted for this repo.
- **adapted** — specific principles or rules lifted and dissolved into this skill's recipe.
- **vendored** — concrete files (scripts, hooks) copied in and maintained here.
- **original** — no external source skill; authored for this repo.

## Recording rule

When a skill is created or materially re-sourced:

1. Add or update its row above (the current snapshot).
2. Add a dated `Provenance:` clause to that skill's `CHANGELOG.md` bullet (the per-change detail):
   `- YYYY-MM-DD — <why> → <what>. Provenance: <what was taken> from [name](url).` (a local source uses its plain path)
3. Never put the attribution in `SKILL.md` — body or frontmatter.
