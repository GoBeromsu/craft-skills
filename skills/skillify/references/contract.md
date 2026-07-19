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

---

## 1. Frontmatter

Exactly this shape — nothing else:

```yaml
---
name: <kebab-case, equal to the directory name>
description: <see §3>
metadata:
  version: <MAJOR.MINOR.PATCH>
---
```

`version` as a top-level key, `allowed-tools`, and `compatibility` are forbidden.
Only `name`, `description`, and `metadata` (holding `version`) are read by any runtime this library targets; `scripts/validate-skill-format.py` rejects any other top-level key.

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
- Match freedom to fragility. High freedom (prose heuristics) where many routes are valid and context decides; medium freedom (a preferred pattern with parameters) where one way is better but variation is fine; low freedom (an exact script, few knobs) where the operation is fragile and order-sensitive. A narrow bridge gets guardrails; an open field gets a compass — the wrong choice either straitjackets judgment or lets a fragile step wobble.
- One default per decision, with one named escape hatch. No option menus.
- No ALL-CAPS rigidity walls and no "MUST/NEVER/LAW" shouting — where strict adherence matters, one short clause of why is enough. A single sparing **bold** is fine.
- Break lines only where a sentence ends — one sentence per line in paragraphs, one item per line in lists; never hard-wrap mid-sentence at a column width. Markdown renders both identically, but sentence-boundary lines read and diff cleaner. Deterministic enforcement: `scripts/reflow-sentences.py <files>` exits 1 on violations; `--fix` reflows a wrapped file in place.
- References sit exactly one level deep (`references/*.md`); any reference over 100 lines opens with a table of contents. Templates live in `templates/`, scripts in `scripts/`. No nested `SKILL.md` anywhere inside a package — every skill is one flat directory.
- Present-tense imperative throughout; no history, no provenance credit, no vendor lock (no Claude-only frontmatter or `/plugin` instructions in the body). Use `${ENV_VAR}` placeholders, forward-slash paths, and no time-sensitive language ("new", "recently", bare dates).
- Preserve the skill's distinctive craft — detection commands, decision tables, hard-won laws survive, compressed rather than deleted. If genuinely valuable content doesn't fit in the body, move it to `references/`; don't cut it.
- A table the body already earns (a routing table, a gate) stays a table.
- `## Anti-patterns` is the single registry for recorded unwanted behaviors — one line per entry, shaped `- <unwanted behavior> → <what to do instead>.`, accumulated from real operator corrections (see the lifecycle's record-a-correction flow), not invented upfront. It subsumes `## Red Flags` and `## Common Rationalizations`; a package carries at most this one such section.
- Document external-binary requirements (`git`, `python3`, …) in a short `## Requirements` section only if the skill actually shells out to them.

## 5. Package parts

A package is one directory: `SKILL.md` + `CHANGELOG.md`, plus whichever of these it needs.

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
| `assets/` | The output consumes files it never loads into context — boilerplate trees, fonts, images copied or filled into results. |
| `tests/` | Any `scripts/` file ships with a matching test module. |
| `evals/` | Local scratch for the eval-first loop (§7) — **gitignored, never committed**. |
| `.env` / `.env.example` | Any credential, token, or host-specific value. Commit only `.env.example` with placeholders. |

No routing-index file, no grouping subfolders, no nested per-child `SKILL.md`.
Claude Code and Codex discover a skill from its own directory's `SKILL.md` frontmatter directly.

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
