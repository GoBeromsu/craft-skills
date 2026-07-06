---
status: done
---

# Plan — skill-library redesign to vendor-official authoring standards

Date: 2026-07-06
Driver: adversarial review of the whole library (including skillify itself and AGENTS.md)
against current official Anthropic and OpenAI skill-authoring guidance, plus the naming
convention the operator wants (verb names for explicitly-triggered skills).

## Sources of authority

- Anthropic: platform.claude.com Agent Skills overview + best-practices; code.claude.com/docs/en/skills;
  anthropic.com/engineering "Equipping agents for the real world with Agent Skills"; anthropics/skills
  skill-creator; code.claude.com best-practices (CLAUDE.md guidance).
- OpenAI: developers.openai.com/codex/skills, /guides/agents-md, /learn/best-practices,
  /plugins/build; GPT-5 / 5.2 / 5.5 prompting guides; agents.md spec; openai/model_spec.
- Open standard: agentskills.io specification + eval guide.
- Exemplars the operator rates highly: Yeachan-Heo/gajae-code, code-yeongyu/lazycodex `plugins/omo/skills`.

## Verdict on the current library (what's wrong)

1. **Descriptions violate both vendors' guidance.** Current frontmatter descriptions are bare
   quoted-trigger lists (e.g. skillify: `'"make a skill", "스킬 만들자", …'`). Official guidance:
   third person, states *what the skill does* and *when to use it*, key use case front-loaded,
   clear scope boundaries. skillify codified the anti-pattern ("real user trigger phrases, not
   capability blurbs") and imposed it on every skill — the fix must start there.
2. **The invented 5-key frontmatter law diverges from the spec.** Only `name` + `description`
   are required anywhere (Codex requires exactly those; Claude Code recommends only
   `description`). `version` as a top-level key is read by no runtime — the open standard puts
   it in `metadata`. `allowed-tools` is experimental and unneeded by these skills;
   `compatibility` is explicitly "most skills do not need" territory.
3. **skillify is process-maximalist against both vendors' direction.** Admission receipts,
   writer/reviewer/grader charters, a 3-CLI consensus convergence loop with rebuttal rounds,
   tier gates, MECE law prose, three contamination gates. GPT-5.5 guidance: describe outcome and
   success criteria, avoid step-by-step process unless the path matters; contradictory/overlapping
   rule layers are actively damaging. Anthropic: "Claude is already very smart. Only add context
   Claude doesn't already have." The official authoring loop is eval-first and empirical, not
   consensus-bureaucratic.
4. **Naming.** Anthropic explicitly lists `documents` as a bad (overly generic) name. The
   operator's rule, matching the omo convention: explicitly-triggered skills carry verb names
   (`start-work`, `review-work`, `remove-ai-slops`); domain-context skills may stay nouns
   (`frontend`, `programming`, `lsp`, `rules`).
5. **CHANGELOGs break their own one-line law.** The convention (`one compact line, why → what`)
   exists in skillify §Change history, but real entries run to 90+ words with provenance clauses.
6. **Temporal evals were tracked in git.** Fixed 2026-07-06: `skills/*/evals/` gitignored;
   receipts stay local. skillify's tier gates still *mandate* committed receipts — removed in
   the rebuild.
7. **AGENTS.md fails both vendors' litmus.** "Would removing this cause mistakes?" — the full
   folder tree (file-by-file description of the codebase) and the per-skill table duplicate what
   any agent reads from disk. "Short, accurate beats long, vague." It also documents a skillify
   protection hook that is not installed (no `.claude/hooks/`, no `.claude/settings.json`).
8. **Invented topology (thick skills, areas, RESOLVER) has no upstream counterpart** and is
   internally broken (issue #28: schemas.md mandates a master `skills/RESOLVER.md` that does not
   exist). Official model: one skill = one directory with SKILL.md + optional `references/`,
   `scripts/`, `assets/`, kept one level deep.

## Target contracts

### Frontmatter (vendor-agnostic, open-standard)

```yaml
---
name: <kebab-case, = directory name>
description: <third person; what it does + when to use it; key use case first;
  real trigger phrases woven in; scope boundaries ("not for …") when neighbors overlap>
metadata:
  version: <semver>
---
```

Nothing else. Semver discipline survives in `metadata.version`; `CHANGELOG.md` per package stays
(local convention, no upstream conflict).

### Naming

- Explicitly-triggered workflow skills: verb-first (`refactor`, `init`, `skillify`, `hookify`,
  `research`, `debug`, `document`, `write-report`).
- Domain-context skills: noun allowed (`frontend`, `backend`, `programming`, `ml`, `agents`,
  `git`, `security`, `testing`).
- Kebab-case, ≤2 tokens, no `-skill`/`-tool` suffixes; name must equal directory.

### Body

- Target ≤150 lines for leaf skills; hard ceiling 500 (official). Every line is a recurring
  token cost once loaded.
- Lead with outcome + success criteria; give steps only where the exact path matters
  (degrees-of-freedom calibration: prose for judgment, scripts for fragile/deterministic ops).
- One default per decision with a named escape hatch; no option buffets.
- References exactly one level deep; reference files >100 lines carry a ToC; domain-partitioned.
- No time-sensitive content, consistent terminology, forward-slash paths, `${ENV_VAR}`
  placeholders, no ALL-CAPS rigidity walls (explain why briefly instead).
- No sub-SKILL.md files. Former sub-recipes become `references/*.md` + `templates/*.md`.

### CHANGELOG

`- YYYY-MM-DD — [vX.Y.Z: ]<why> → <what>.` — one line, ≤ ~160 chars. One-time reformat of all
existing files under the sanctioned reformat exception; never edit bullets afterwards.

### Evals (temporal, gitignored)

Official eval-first loop replaces the consensus gate: ~3 scenarios in `evals/evals.json`
(agentskills.io format: prompt / expected_output / assertions-added-later), without-skill
baseline, iterate to pass; description tuning via ~8 should-trigger + ~8 near-miss
should-NOT-trigger prompts. Receipts and run artifacts stay local.

## Rename / topology map

| Current | Target | Why |
|---|---|---|
| `documents` (+5 sub-recipe SKILL.mds) | `document`, sub-recipes flattened to `references/` + `templates/` | verb; "documents" is an official bad-name example; kills invented thick-skill topology |
| `technical-report` | `write-report` | operator explicitly triggers it; verb-first omo style |
| `git/worktree/SKILL.md` | `git/references/worktree.md` | sub-recipe → plain reference |
| all others | keep | verbs already (`init`, `refactor`, `hookify`, `skillify`) or sanctioned domain nouns |
| — (new) | `research` | operator's literal example; deep-research workflow feeding `docs/research/` |
| — (new) | `debug` | hypothesis-driven debugging discipline; core to the full-stack + ML researcher loop |

## skillify v4 (rebuild spec)

Keep: lifecycle ownership (create/update/rename/deprecate), branch→PR delivery, Layer-1 format
validator (rewritten to the new contract), runtime-hygiene validator, per-skill `.env` secrets
rule, one-line CHANGELOG law, admission *question* (does this belong in craft-skills — reusable,
owned here, vendor-agnostic?) as a short inline check.

Drop: admission receipts + reviewer-subagent mandate, writer/reviewer/grader charter mandate,
Layer-2 consensus as a required gate (`scripts/consensus.py` survives as an optional deep-check),
tier-gate checklists, MECE/contamination-gate prose (fold into ~5 body-contract bullets),
areas/RESOLVER/thick-skill taxonomy (closes #28), `evals/` as committed artifacts.

Add: the eval-first authoring loop; the description contract with trigger-tuning; the naming
contract above. `references/schemas.md` collapses into one `references/contract.md`.

## AGENTS.md rewrite

≤ ~80 lines: what the repo is + non-goals, install matrix (Claude Code plugin, Codex
`.agents/skills`, Hermes external_dirs, generic), pointer to skillify as the authoring contract,
env-var table, repo rails (issue routing, PR conventions, governance harness command). Remove
folder tree, per-skill table, uninstalled-hook governance section.

## Execution waves

- **Wave 0 (mechanical, single lane):** renames + flattening + repo-wide reference fix; commit.
- **Wave 1 (parallel Sonnet executors via Workflow):** one executor per package (14 rewrites +
  `research` + `debug` new), each delivering frontmatter/description/body/CHANGELOG per contract;
  per-package adversarial verify agents check contract compliance.
  skillify rebuild reviewed personally by the planner. Issues #31 + #27 fold into `document`'s
  work order; #29 folds into `git`+`hookify` (single owner for hooksPath install logic).
- **Wave 2:** repo surfaces — skills-manifest.yaml regeneration, routing-eval-cases.yaml rename
  fixes, AGENTS.md, README, plugin.json/marketplace.json, install.sh, PROVENANCE.md.
- **Wave 3:** verification — Layer-1 validators, pytest, governance harness, fresh-eyes review
  fan-out; then work-log doc (`docs/research/2026-07-06-skill-library-redesign.md`), commit, push.

## Deferred (out-of-scope discoveries → issues)

- LSP / code-graph tooling the operator likes in omo: runtime tooling (plugin/MCP), not a
  portable prose skill; candidate reference material for `programming`/`refactor`. → new issue.
- Governance harness right-sizing (manifest duplicates frontmatter; inventory-parity checker
  fights drift the manifest itself creates). Landed 2026-07-06 from PR #30 as-is; revisit after
  the redesign settles. → new issue.
