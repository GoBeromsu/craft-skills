---
slug: skill-authoring-standards
date: 2026-07-06
author: agent
topic: Evidence base for the 2026-07-06 skill-library redesign to vendor-official authoring standards
status: active
---

# Skill-Authoring Standards: Vendor Guidance, Open Spec, and Exemplar Conventions

## Summary

This surveys what the open agent-skills standard, official Anthropic/OpenAI guidance, and two
hand-authored exemplar skill libraries actually require or recommend for skill frontmatter,
descriptions, body structure, and AGENTS.md-style context files. It is the evidence base behind
the 2026-07-06 skill-library redesign; the decisions themselves live in
`docs/exec-plan/active/skill-library-redesign/plan.md`, not here. Headline finding: only `name`
and `description` are ever required at the frontmatter level anywhere — everything richer
(version, allowed-tools, compatibility, argument-hint, provenance fields) is vendor-specific
tooling or self-invented convention. Both vendors converge on "third-person, what+when"
descriptions and short, outcome-oriented bodies, but diverge from the strongest hand-authored
exemplar (omo/lazycodex) on trigger-phrase style and observed body length.

## Background

craft-skills' prior conventions (5-key frontmatter, bare quoted-trigger-list descriptions,
thick-skill topology, a consensus-gated skillify pipeline) were adversarially reviewed against
current vendor guidance, producing the redesign plan. This research backs that review with three
sources: (1) a web-research pass on OpenAI/Codex's AGENTS.md and Agent Skills docs plus GPT-5.x
prompting guides; (2) a structural analysis of two exemplar repos (gajae-code, lazycodex/omo);
(3) `contract.md`, the distilled authoring contract for the redesign, whose clauses cite
Anthropic's official skill-authoring guidance (platform.claude.com Agent Skills overview,
code.claude.com skills docs, the anthropic.com/engineering Agent Skills post, CLAUDE.md
best-practices).

**Gap**: the raw Anthropic research report was produced earlier in this session but never
persisted to a file. Its claims survive only as citations inside `contract.md` — findings below
tagged "(second-hand)" trace only that far, unlike the OpenAI/exemplar findings, which trace to
fetched URLs or direct repo inspection.

## Findings

### (a) Open standard vs. vendor-specific additions

- Codex Agent Skills frontmatter requires only `name` + `description`. — [developers.openai.com/codex/skills](https://developers.openai.com/codex/skills)
- Codex's *plugin* manifest (`plugin.json`, a tier above a skill) requires `name` + `version` + `description` — a different artifact from a skill's own frontmatter. — [developers.openai.com/codex/plugins/build](https://developers.openai.com/codex/plugins/build)
- lazycodex/omo's 24 hand-authored skills use only `name` + `description` (occasionally an optional `metadata.short-description`); none carries `version`, `allowed-tools`, or `compatibility`. — research-exemplars.md
- gajae-code's bundled skills add `argument-hint`, `pipeline`, `handoff-policy`, `handoff`, `level`, even an in-frontmatter `source:` line — none of it spec-mandated. — research-exemplars.md
- Anthropic (via contract.md, second-hand): only `description` is strictly required at the Claude Code layer; `version`/`allowed-tools`/`compatibility` are read by no runtime found; the open standard nests version-like metadata under a `metadata` key.

### (b) Description and trigger-phrase design

- Codex: 8,000-char description cap; "front-load the key use case and trigger words"; "establish clear scope boundaries and avoid overlap with other skills." — [developers.openai.com/codex/skills](https://developers.openai.com/codex/skills)
- omo/lazycodex: `"MUST USE for/when X"` opener, compressed scope summary, then a literal `Triggers: "phrase1", "phrase2", ...` list, sometimes a `"NOT for X, use Y"` carve-out; 400–900 chars, optimized purely for router-matching, not readability. — research-exemplars.md
- Contract (§2, second-hand): third-person voice, what + when both present, key use case first; 3–6 trigger phrases **woven into prose** (explicitly not a bare list); a "Not for X — use Y" boundary when a sibling overlaps; 300–700 chars target, ≤1024 hard cap.
- Tension: the contract rules out a bare `Triggers:` list as an anti-pattern, while that exact form is omo's core mechanism. Both agree on front-loading and scope boundaries; they disagree on prose-embedded vs. verbatim-listed triggers.

### (c) Body authoring: size, structure, degrees of freedom, eval-first loop

- Codex: "Keep each skill focused on one job"; "Prefer instructions over scripts unless you need deterministic behavior or external tooling"; imperative steps with explicit inputs/outputs; test prompts against descriptions. — [developers.openai.com/codex/skills](https://developers.openai.com/codex/skills)
- Codex's trigger for creating a skill at all: "If you keep reusing the same prompt or correcting the same workflow, it should probably become a skill." — [developers.openai.com/codex/learn/best-practices](https://developers.openai.com/codex/learn/best-practices)
- GPT-5.5 guidance (generalized beyond skills): describe "the expected outcome, success criteria, allowed side effects, evidence rules, and output shape" rather than prescribing steps; "avoid step-by-step process guidance unless the exact path matters." — [developers.openai.com/api/docs/guides/latest-model](https://developers.openai.com/api/docs/guides/latest-model)
- Observed exemplar practice diverges from that ideal: omo/lazycodex bodies run ~100–800 lines (median ~200–270), written as imperative procedure with decision tables, `## PHASE 0`-style gate headers, bold "STOP"/"DO NOT X BEFORE Y" directives. Every skill also carries a first-class `agents/` subdirectory (sub-agent delegation config) — undocumented by either vendor. — research-exemplars.md
- Contract (§3, second-hand): ≤150-line target, 500-line hard ceiling; outcome over process, steps only where sequence matters; one default per decision plus one named escape hatch; no ALL-CAPS; references one level deep, ToC past 100 lines.
- Eval-first loop: contract §5 specifies a gitignored `evals/evals.json` (~3 scenarios) + `evals/triggers.json` (8 should-trigger + 8 near-miss prompts) to tune the description boundary. agentskills.io is cited as authority for this pattern, but its schema was not independently captured in either scratch report — treat as unverified.
- Gap: omo's observed median (~200–270 lines) sits above the contract's 150-line target, though both fit the shared 500-line ceiling. Flagged here, not resolved — resolution is a plan.md decision.

### (d) AGENTS.md / context-file guidance

- agents.md spec: "just standard Markdown... no required fields"; recommended sections: overview, build/test commands, code style, testing instructions, security considerations, commit/PR guidelines, deployment steps. READMEs stay human-facing; AGENTS.md carries agent-specific detail. — [agents.md](https://agents.md)
- "A short, accurate AGENTS.md is more useful than a long file full of vague rules." — [developers.openai.com/codex/learn/best-practices](https://developers.openai.com/codex/learn/best-practices)
- Codex merge mechanics: nearest-directory file wins (appears later in the merged prompt, overrides); 32 KiB size cap; empty files silently skipped, over-cap files silently dropped. — [developers.openai.com/codex/guides/agents-md](https://developers.openai.com/codex/guides/agents-md)
- Anti-patterns: "Overloading the prompt with durable rules instead of moving them into AGENTS.md"; "Not letting the agent see its work by not giving details on build/test commands"; "Giving Codex full permission before understanding the workflow." — same source
- Directional, non-official: one third-party study found LLM-generated AGENTS.md files "slightly reduced task success while increasing cost by 23%," vs. "+4%" for human-written files — widely cited in community summaries, not an OpenAI claim; treat as caution only.
- Contract's litmus (via contract.md/plan.md, second-hand): "would removing this cause mistakes?" as the bar for keeping a CLAUDE.md/AGENTS.md line — not independently re-verified against a raw Anthropic source in this pass.

### (e) Naming conventions

- Official Codex position: **no** documented naming convention (verb-first, kebab-case, etc.) for skills or custom prompts — left to the author. The only hard rule found anywhere is kebab-case for a plugin's `name` in `plugin.json`. — [developers.openai.com/codex/custom-prompts](https://developers.openai.com/codex/custom-prompts), [developers.openai.com/codex/plugins/build](https://developers.openai.com/codex/plugins/build)
- Anthropic (via plan.md's verdict, second-hand): cites "documents" specifically as an official example of an overly generic bad name — not independently re-verified against a raw source here.
- omo/lazycodex's actual practice is a mixed, trigger-oriented scheme, not a grammatical rule: domain nouns (`frontend`, `rules`, `lsp`), a tool name (`ast-grep`), verb+object actions (`review-work`, `start-work`), product-namespaced actions (`lcx-report-bug`, `lcx-doctor`). Unifying principle: "the name matches what a user would actually type or say." — research-exemplars.md
- gajae-code mirrors this with its own `gjc-` prefix for meta/maintenance skills — a shared-but-undocumented convention across both repos. — research-exemplars.md

### (f) LSP / code-graph integration models (deferred)

- Both repos wire in LSP and code-graph tooling via two different models: LSP gets a full MCP-server backend plus a two-skill split (`lsp` for usage, `lsp-setup` for install/verify, with a per-language reference tree and real verification scripts); code-graph is exposed only as an MCP wrapper around a third-party npm package, invoked via a session-start hook with **no SKILL.md at all**. — research-exemplars.md §8
- Evidence only, not a design brief: adopting this pattern is out of scope for the redesign this document backs. Tracked separately as GitHub issue #33.

## Comparison

| Dimension | Open standard / Codex | omo/lazycodex (exemplar) | Anthropic-derived contract (second-hand) |
|---|---|---|---|
| Required frontmatter | `name` + `description` only | `name` + `description` (+ optional `metadata.short-description`) | `description` strictly required; `name`/`metadata.version` kept by convention |
| Description style | Front-loaded triggers, clear scope boundary | `MUST USE for/when...` + bare `Triggers:` list + `NOT for X` carve-out | What+when prose, triggers woven in (no bare list), `Not for X — use Y` |
| Body length | No hard number; "keep focused on one job" | ~100–800 lines, median ~200–270 | ≤150-line target, 500-line hard ceiling |
| Naming rule | None documented; kebab-case only for plugin `name` | Whatever a user would type/say; mixed nouns/verbs/prefixes | Verb-first for explicitly-triggered skills (plan.md decision, not restated here) |

## Open questions

- Is the bare `Triggers:` list genuinely an Anthropic anti-pattern, or a stricter read than the source warrants? The contract disallows it; omo's exemplar uses it as its core mechanism. Neither raw report resolves this.
- What does the agentskills.io eval guide actually specify for `evals/evals.json` / `triggers.json` shape? Cited as authority but not independently captured by either scratch report.
- Is the "LLM-generated AGENTS.md reduces success" study methodologically sound, or a repeated community claim? Treated here as directional only.
- Every "Anthropic guidance" claim here is second-hand via `contract.md`'s citations — the original Anthropic research pass was never persisted to a re-verifiable file. A follow-up pass re-fetching platform.claude.com / code.claude.com / anthropic.com/engineering directly would close this gap.
- LSP/code-graph adoption is deferred to GitHub issue #33 and unresolved here.

## References

- [agents.md](https://agents.md) — the open AGENTS.md spec
- [developers.openai.com/codex/guides/agents-md](https://developers.openai.com/codex/guides/agents-md) — Codex AGENTS.md discovery/merge mechanics
- [developers.openai.com/codex/learn/best-practices](https://developers.openai.com/codex/learn/best-practices) — Codex best practices (AGENTS.md, skills, anti-patterns)
- [developers.openai.com/codex/skills](https://developers.openai.com/codex/skills) — Agent Skills format/spec
- [developers.openai.com/codex/custom-prompts](https://developers.openai.com/codex/custom-prompts) — deprecated custom-prompts format
- [developers.openai.com/codex/plugins/build](https://developers.openai.com/codex/plugins/build) — plugin manifest format
- [developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide) — Codex-specific GPT-5 system-prompt guidance
- [developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide) — GPT-5.2 prompting guide
- [github.com/openai/openai-cookbook gpt-5_prompting_guide.ipynb](https://github.com/openai/openai-cookbook/blob/main/examples/gpt-5/gpt-5_prompting_guide.ipynb) — original GPT-5 prompting guide
- [developers.openai.com/api/docs/guides/latest-model](https://developers.openai.com/api/docs/guides/latest-model) — "Using GPT-5.5" guide
- [github.com/openai/model_spec/blob/main/model_spec.md](https://github.com/openai/model_spec/blob/main/model_spec.md) — instruction hierarchy / chain of command
- Structural analysis of `Yeachan-Heo/gajae-code` and `code-yeongyu/lazycodex` (shallow clones inspected directly; per-file evidence in research-exemplars.md) — no stable public URLs beyond the repos themselves
- `contract.md` — distilled craft-skills authoring contract; source of all Anthropic-attributed and consensus-decision claims here (second-hand for Anthropic-sourced clauses; see Background)
