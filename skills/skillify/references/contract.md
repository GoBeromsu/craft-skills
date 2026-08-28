# Skill Authoring Contract

The permanent, self-contained authoring contract for every `SKILL.md` in this library.
`SKILL.md` links here for the full rules; this file is the canonical source authors and reviewers check a package against.

## Table of Contents

1. [Frontmatter](#1-frontmatter)
2. [Naming](#2-naming)
3. [Description](#3-description)
4. [Body](#4-body)
5. [Package parts](#5-package-parts)
6. [CHANGELOG](#6-changelog)
7. [Eval-first authoring loop](#7-eval-first-authoring-loop)
8. [Version-bump rubric](#8-version-bump-rubric)
9. [MECE ownership](#9-mece-ownership)
10. [External facts and dependencies](#10-external-facts-and-dependencies)
11. [Core portability](#11-core-portability)

---

## 1. Frontmatter

Every package requires a root `SKILL.md`.
Use this portable baseline:

```yaml
---
name: <kebab-case, equal to the directory name>
description: <see §3>
metadata:
  version: <MAJOR.MINOR.PATCH>
---
```

`version` is never a top-level key.
The Agent Skills spec also permits `license`, `compatibility`, and experimental `allowed-tools`.
Add one of those optional keys only when the package cannot meet its support boundary without it, and record the affected-runtime support caveat in that runtime's vendor lens.
Do not add vendor-specific fields to the portable baseline.

## 2. Naming

- **Verb-first** for a skill the user explicitly triggers by naming the action it performs (`refactor`, `init`, `skillify`, `hookify`, `write-report`).
- **Plain noun** for a skill that supplies ambient domain context rather than being invoked by a verb (`programming`, `frontend`, `backend`, `ml`, `agents`, `git`, `security`, `testing`).
- Kebab-case, matches the directory exactly, no more than two tokens, no `-skill` / `-tool` / `-helper` suffix (the package is already a skill).

## 3. Description

Shape:

```
<Third-person sentence: what it does>. Use when <concrete situations, with 3-6 real
trigger phrases woven in naturally>. Not for <nearest-neighbor boundary — use Y>.
```

- Third person ("Routes…", "Scaffolds…", "Owns…"), never "I" / "You".
- Both *what* the skill does and *when* to use it are present; the primary use case leads the sentence.
- Trigger phrases are real things a user types, embedded in prose — never a bare quoted list, never keyword stuffing.
- Add a "Not for X — use Y" boundary sentence whenever a sibling skill's domain overlaps.
- Write against undertriggering: runtimes consult a skill only when its description names the situation at hand, and they err toward not consulting. Name the concrete situations that need the skill — including ones where the user never says the skill's name — rather than merely permitting use. The boundary sentence keeps this assertiveness precise: trigger phrases widen recall, "Not for X" guards the near-misses.
- The description is the only triggering surface — the body loads after the decision, so "when to use" prose in the body is dead weight there.
- 300–700 characters is the target shape; 1024 is the hard ceiling. The validator warns (non-blocking) under 200 or over 700 chars, and hard-fails only outside 1..1024.
- At most one Korean trigger phrase, and only if that is genuinely how the operator invokes the skill in practice.

## 4. Body

- 150 lines is the target for a leaf skill; 500 lines is the hard ceiling the validator enforces. When the draft runs long, move depth to `references/*.md` — don't trim useful material, relocate it.
- Structure: title → 1–2 sentence purpose with success criteria → the workflow/decision content → boundaries/hand-offs. Cut preamble and restated-obvious practice — an agent is already competent; only add context it doesn't already have.
- Outcome over process: state the goal and constraints. Give numbered steps only where the exact sequence matters (a fragile or deterministic operation) — prose for judgment calls, scripts for mechanics.
- Keep instructions lean and single-owned: state the action, its autonomy boundary, and any required approval at the owner; link from every other location. Report progress through observable evidence and decisions, not private chain-of-thought, and never ask a user to reveal or transcribe internal reasoning.
- Delegate independent lanes when the runtime supports delegation; keep dependent decisions with their owner and specify the hand-off evidence.
- Match freedom to fragility. High freedom (prose heuristics) where many routes are valid and context decides; medium freedom (a preferred pattern with parameters) where one way is better but variation is fine; low freedom (an exact script, few knobs) where the operation is fragile and order-sensitive. A narrow bridge gets guardrails; an open field gets a compass — the wrong choice either straitjackets judgment or lets a fragile step wobble.
- One default per decision, with one named escape hatch. No option menus.
- No ALL-CAPS rigidity walls and no "MUST/NEVER/LAW" shouting — where strict adherence matters, one short clause of why is enough. A single sparing **bold** is fine.
- Break lines only where a sentence ends — one sentence per line in paragraphs, one item per line in lists; never hard-wrap mid-sentence at a column width. Markdown renders both identically, but sentence-boundary lines read and diff cleaner. Deterministic enforcement: `scripts/reflow-sentences.py <files>` exits 1 on violations; `--fix` reflows a wrapped file in place.
- References sit exactly one level deep (`references/*.md`); any reference over 100 lines opens with a table of contents. Templates live in `templates/`, scripts in `scripts/`. No nested `SKILL.md` anywhere inside a package — including `agents/` — every skill is one flat directory.
- Present-tense imperative throughout; no history, no provenance credit, no vendor lock (no Claude-only frontmatter or `/plugin` instructions in the body). Use `${ENV_VAR}` placeholders, forward-slash paths, and no time-sensitive language ("new", "recently", bare dates).
- Preserve the skill's distinctive craft — detection commands, decision tables, hard-won laws survive, compressed rather than deleted. If genuinely valuable content doesn't fit in the body, move it to `references/`; don't cut it.
- A table the body already earns (a routing table, a gate) stays a table.
- `## Anti-patterns` is the single registry for recorded unwanted behaviors — one line per entry, shaped `- <unwanted behavior> → <what to do instead>.`, accumulated from real operator corrections (see the lifecycle's record-a-correction flow), not invented upfront. It subsumes `## Red Flags` and `## Common Rationalizations`; a package carries at most this one such section.
- Document external-binary requirements (`git`, `python3`, …) in a short `## Requirements` section only if the skill actually shells out to them.

## 5. Package parts

A package is one directory with required root `SKILL.md` and `CHANGELOG.md`, plus only the execution parts its concrete invocations need.

Plan the parts from concrete examples before authoring: walk 2–3 real invocations of the workflow and ask what a fresh run would redo each time.
Code every run would rewrite → `scripts/`.
Knowledge every run would re-derive (schemas, flag meanings, domain rules) → `references/`.
A fixed artifact shape every run would re-type → `templates/`.
Files the output consumes without reading (boilerplate, fonts, images) → `assets/`.
What remains — the judgment and sequencing — is the `SKILL.md` body.

| Part | Create when |
|------|-------------|
| `references/` | Bulk knowledge consulted on demand, not on every invocation. |
| `scripts/` | A step must be deterministic and repeatable — CI can call it for a pass/fail exit code. Not for one-off setup or judgment-driven branching. |
| `templates/` | The skill emits a canonical artifact with a fixed shape. |
| `assets/` | The output consumes files without loading them into context — boilerplate trees, fonts, images copied or filled into results. They are not background reference material. |
| `agents/` | A bounded subagent role needs a charter or runtime metadata. Each file defines that role's scope, inputs, outputs, and hand-off; it is never a child skill and never contains `SKILL.md`. |
| `tests/` | Any `scripts/` file ships with a matching test module. |
| `evals/` | Local scratch for the eval-first loop (§7) — **gitignored, never committed**. |
| `.env` / `.env.example` | Any credential, token, or host-specific value. Commit only `.env.example` with placeholders. |

An additional directory needs a concrete execution purpose not covered by these parts; document that purpose in the package rather than using it for grouping.
No routing-index file, no grouping subfolders, no nested per-child `SKILL.md`.
Hermes, Claude Code, Codex, Cursor, and Grok-native share each package's `SKILL.md` as the portable core; put runtime-specific discovery and plumbing in their respective lenses.

## 6. CHANGELOG

Every package owns a `CHANGELOG.md`.
One line per entry:

```
- YYYY-MM-DD — [vX.Y.Z: ]<why it changed> → <what it became>.
```

Lead with the trigger, not the artifact — full detail lives in git history, the bullet is the summary.
Link any referenced skill or file with `[text](path)`.
Newest last; append, never rewrite a past bullet (a one-time reformat to this convention is the only sanctioned exception, already spent for this library).
`## Change Log` inside `SKILL.md` is forbidden — history lives only in `CHANGELOG.md`.

When a change derives from operator-supplied source material — a doc, repo, article, or conversation handed over during authoring — record it in two places: append a `Provenance:` clause to that bullet that names what was taken and links a public source as `[name](url)` — e.g. `Provenance: reuse rung from [ponytail](https://github.com/DietrichGebert/ponytail)`; a local source uses its plain path — and land any substantive excerpt worth re-consulting as a `references/*.md` file (rewritten to reference-style voice, §4) rather than leaving it only in chat history.
The cross-skill lineage snapshot lives in `skills/PROVENANCE.md`; update its row when a package's primary source changes.

## 7. Eval-first authoring loop

Replaces any committee review or manual sign-off process as the quality gate.
Before authoring a package, draft (in the local, gitignored `evals/` directory):

- `evals/evals.json` — about 3 realistic scenarios: `{"skill": "<name>", "cases": [{"prompt": "<realistic user request>", "expected_behavior": "<what a correct run does>"}]}`.
- `evals/triggers.json` — 8 should-trigger prompts plus 8 near-miss should-NOT-trigger prompts drawn from sibling skills' domains.

Run each scenario without the skill, then with the drafted `SKILL.md`; the skill's value is the delta between the two arms, not the with-skill output alone.
Iterate the body until behavior matches `expected_behavior`.
Run the 16 trigger prompts against the drafted `description`; any near-miss that would plausibly match tightens the "Not for X" boundary sentence (§3).
How to run the arms, judge with fresh eyes, read transcripts, and iterate without overfitting: `references/evaluation.md`.
These artifacts are temporal working notes, not a package part — never commit them.

## 8. Version-bump rubric

```
MAJOR  A trigger phrase is removed/renamed, or output format breaks a downstream consumer.
MINOR  A backward-compatible capability is added — new phase, flag, or behavior.
PATCH  A bug fix, prose correction, or dependency bump with no interface change.
```

Ask: "does a caller already using this skill need to change anything?" → MAJOR or MINOR.
"Does the caller gain a new opt-in capability?" → MINOR.
"Fix or clarification with no interface effect?" → PATCH.

## 9. MECE ownership

Inside one skill package, each rule has exactly one owner: the body for always-read routing or gates, a reference for deep topic rules, a script for deterministic checks, and `CHANGELOG.md` for history.
If another section needs the same rule, link to the owner instead of restating it.
Overlapping warning sections (`Red Flags`, `Common Rationalizations`, repeated anti-pattern tables) are an anti-pattern; keep one `## Anti-patterns` registry in `SKILL.md` and let references link back or add topic-specific rules only when they do not duplicate the package-level entry.

## 10. External facts and dependencies

This section owns authoring rules and package-local maintenance for mutable facts about external CLIs, APIs, services, and runtimes.
It excludes conceptual guidance, writing guidance, and procedures that are purely local.

When a fact is unknown, ambiguous, or version-dependent, consult the official primary documentation first.
Encode the resulting runtime form in the affected package, or link to the exact official source when reproducing it would be brittle or excessive.
When sources conflict, disclose the conflict where the fact is used; prefer a more-specific repository-local contract or reproducible evidence matching the target version and platform over general or stale documentation.
Leave an unresolved fact unknown rather than inventing a value, behavior, or command.

For every mutable CLI, API, service, or runtime requirement, the affected package records its name, official source URL, installed-version probe, support boundary, and release or update trigger in its `## Requirements` section or a linked reference.
The probe is an exact safe command or API query that reports the installed or selected version; the boundary says which version range, platform, or capability the recipe supports.
For a selected dependency/runtime release or a changed probe/capability, that trigger requires official-documentation review and affected evals, then update the recipe if its runtime form changed, bump the package version, and append its CHANGELOG entry.
Keep this maintenance beside the dependent package; do not build a global dependency inventory, background daemon, or separate update framework.
This contract applies to skillify immediately and to every other package when it is next touched or its own dependency trigger fires; do not create mass churn to retrofit untouched packages.

Exercise applicable ambiguity, conflict, and unknown cases through the existing eval-first loop (§7), including the expected disclosure or unknown outcome.
Do not create a fact inventory or validator for this contract.

## 11. Core portability

Universal `SKILL.md` recipes must work without alteration on Hermes, Claude Code, Codex, Cursor, and Grok-native runtimes.
They may require standard tools only when the package documents them; they must not require one vendor's CLI, plugin command, frontmatter field, or proprietary tool.
Put runtime-specific fields, installation commands, plugin metadata, and plumbing in that runtime's vendor lens.
If a workflow cannot meet this law, make its boundary and supported runtime explicit in the relevant lens rather than presenting it as universal core guidance.
