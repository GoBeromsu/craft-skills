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
| `frontend` | design-first gate and router shape; rendering-architecture/state/folder rules original synthesis; Next.js App Router colocation folder convention | code-yeongyu/lazycodex (MIT; pattern-only); [Next.js project-structure docs](https://nextjs.org/docs/app/getting-started/project-structure); [bulletproof-react nextjs-app](https://github.com/alan2207/bulletproof-react/tree/master/apps/nextjs-app); [Feature-Sliced Design](https://feature-sliced.design/) (unidirectional-dependency principle only); [velog: 프론트엔드 도메인 아키텍처](https://velog.io/@k-svelte-master/frontend-domain-architecture); [velog: 슬기롭게 폴더 구조 설계하기 (feat. Next.js App routing 방식)](https://velog.io/@heoze/%EC%8A%AC%EA%B8%B0%EB%A1%AD%EA%B2%8C-%ED%8F%B4%EB%8D%94-%EA%B5%AC%EC%A1%B0-%EC%84%A4%EA%B3%84%ED%95%98%EA%B8%B0-FSD-%EA%B0%84%EB%8B%A8%ED%9E%88-%EC%82%B4%ED%8E%B4%EB%B3%B4%EA%B8%B0-feat.-Next.js-App-routing-%EB%B0%A9%EC%8B%9D) | adapted |
| `backend` | architecture-detection rules and persistence rationale | [JNU-SWCU/oss-hub](https://github.com/JNU-SWCU/oss-hub) (ADR-001; operator-supplied) | adapted |
| `api` | contract-first resource, error, and interface conventions | [Pullit API Design Guide](https://pullit-docs-server.vercel.app/index.html#02-api-design); [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills/tree/main/skills/api-and-interface-design) | adapted |
| `ast-grep` | syntax-tree decision test, misconception models, and mutation ladder | [code-yeongyu/lazycodex](https://github.com/code-yeongyu/lazycodex) (MIT; pinned at `9b9f8e8f620e3f797567078734165350e1e46659`) | adapted |
| `cicd` | CI/CD automation and deployment state-transition rules | [addyosmani/agent-skills ci-cd-and-automation](https://github.com/addyosmani/agent-skills/tree/main/skills/ci-cd-and-automation); operator-approved JNU-SWCU/oss-hub init deployment plan (operator-supplied, 2026-07-11) | distilled |
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
| `write-prd` | operator-supplied PRD template | — | original (template supplied by operator) |
| `research` | — | — | original (skill-library redesign) |
| `debug` | — | — | original (skill-library redesign) |
| `aside` | — | — | original (grounded in Aside developer docs, https://docs.aside.com/help/developers) |
| `tailscale` | `tailscale` skill (v1.1.1) — tailnet-health gate, daemon-variant restart paths, OAuth-popup triage, profile/identity drift | [bstack](https://github.com/GoBeromsu/bstack) | derived |

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
