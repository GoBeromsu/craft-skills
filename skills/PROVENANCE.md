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
| `frontend` | design-first gate and router shape; framework-shell, slice/public-API, component/state, CSS, and measurement rules | code-yeongyu/lazycodex (MIT; pattern-only); [React](https://react.dev/); [Next.js](https://nextjs.org/docs); [Vite](https://vite.dev/guide/); [FSD](https://fsd.how/docs/); [MDN CSS](https://developer.mozilla.org/en-US/docs/Web/CSS/); [web.dev performance](https://web.dev/learn/performance/) | adapted |
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
| `skillify` | two-layer discipline; skill-anatomy format SSOT; compact-name style; vendor lenses + absorption protocol (degrees-of-freedom, reusable-parts planning, baseline-delta evals, experience-capture flow) | [Agent Skills specification](https://agentskills.io/specification) ([agentskills/agentskills](https://github.com/agentskills/agentskills/tree/69ef37e9424c0a7ea9dd2293b559e43ec8176379) at `69ef37e9424c0a7ea9dd2293b559e43ec8176379`); [anthropics/skills](https://github.com/anthropics/skills/tree/3b3fad96af16a10759d930941b4520ba0c40edae) `skill-creator` at `3b3fad96af16a10759d930941b4520ba0c40edae`; deprecated [openai/skills](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431) creator at `49f948faa9258a0c61caceaf225e179651397431`; current [openai/plugins](https://github.com/openai/plugins/tree/6d99ee149c9fe3c7a55b96cab062cadc1ad36a9d) at `6d99ee149c9fe3c7a55b96cab062cadc1ad36a9d`; [OpenAI latest-model / Sol prompting](https://developers.openai.com/api/docs/guides/latest-model); [Claude Fable prompting](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5); [Cursor Agent Skills](https://prod.cursor.com/docs/skills); [Grok Skills, Plugins & Marketplaces](https://docs.x.ai/build/features/skills-plugins-marketplaces); NousResearch/hermes-agent; gstack (Garry Tan); addyosmani/agent-skills; code-yeongyu/lazycodex | adapted |
| `hookify` | hook patterns/philosophy; Claude Code hooks model; git `core.hooksPath` convention | Yeachan-Heo/oh-my-claudecode, Claude Code hooks docs | adapted |
| `init` | — | — | original |
| `write-report` | — | — | original (promoted from a project-local skill) |
| `write-prd` | operator-supplied PRD template | — | original (template supplied by operator) |
| `research` | — | — | original (skill-library redesign) |
| `debug` | — | — | original (skill-library redesign) |
| `browser` | craft `aside` lineage; browser router and Aside, agent-browser, and vendor-neutral existing-session references (Claude in Chrome is a Claude Code-specific subsection) | [Aside developer docs](https://docs.aside.com/help/developers); [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser); [bstack](https://github.com/GoBeromsu/bstack) `skills/browser/*` at `d3e291c802e35f940047f93be6b4838a0d1269df` | moved and adapted |
| `obsidian` | thick package consolidating Markdown, Bases, Canvas, Mermaid, CLI, Clipper, doctor, and headless Sync sub-recipes | [bstack](https://github.com/GoBeromsu/bstack) `obsidian/*` at `3e0672c` | moved and adapted |
| `vmware` | operator VM lifecycle and VNC automation workflow | — | original |
| `tailscale` | `tailscale` skill (v1.1.1) — tailnet-health gate, daemon-variant restart paths, OAuth-popup triage, profile/identity drift | [bstack](https://github.com/GoBeromsu/bstack) | derived |
| `gpu` | operator incident evidence — RTX 6000 probe preflight/occupancy predicate/settings delta, a shared-host RAM-freeze post-mortem, an edge-GPU Xid incident report, HPC progressive-scaling notes; support-matrix/build/benchmark discipline from vendor and maintainer sources | [Dao-AILab/flash-attention](https://github.com/Dao-AILab/flash-attention); [pytorch RELEASE.md](https://github.com/pytorch/pytorch/blob/main/RELEASE.md); [NVIDIA DCGM diagnostics](https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/dcgm-diagnostics.html); [NVIDIA GTC 2019 S9956](https://developer.download.nvidia.com/video/gputechconf/gtc/2019/presentation/s9956-best-practices-when-benchmarking-cuda-applications_V2.pdf); [stas00/ml-engineering](https://github.com/stas00/ml-engineering) | adapted |

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
