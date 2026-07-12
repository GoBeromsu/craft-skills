---
name: research
description: 'Runs a decision research workflow ending in a docs/research/{slug}.md artifact — scope the question and the decision it feeds, sweep official/primary sources before secondary ones, verify claims in proportion to risk, synthesize source-linked findings with options compared side by side, then state gaps and confidence — never the decision itself. Use when asked to "research this before we decide", "do a deep dive on X", "compare these options", "what does the evidence say", or "조사해줘". Fans out source sweeps when subagents are available, otherwise runs sequentially. Not for filing or template questions (use document) and not for making the call — document authors the ADR once research lands.'
metadata:
  version: 1.1.0
---

# research

Turn an open question into a `docs/research/{slug}.md` artifact a future decision can be made from. Success: findings and their evidence are traceable, options sit side by side, and the file names its own gaps — it commits to nothing itself.

## Phase 1 — Scope

State the question in one sentence and the decision it will inform (which ADR, which upcoming choice). A research pass with no named decision downstream is either premature or belongs in a reference capture instead — confirm the destination decision before sweeping sources.

## Phase 2 — Sweep

Official/primary sources first — vendor docs, specs, source repositories, primary data — then quality secondary sources (well-reviewed write-ups, case studies) only to fill gaps primary sources leave open. A source dense enough that paraphrasing loses precision, or one likely to be cited more than once, gets captured verbatim as `docs/research/references/{slug}.md` (`../document/templates/references.md`) before synthesis starts — re-quoting it from memory later drifts from the original.

## Phase 3 — Verify risk

Classify each finding before synthesis. For a contested code-shaped claim, run the smallest
executable probe that exercises the claim and record the command or scenario with its observed
result. For a consequential non-code claim, counter-search for disconfirming evidence and
corroborate it with an independent source; reconcile any conflict. When the required probe,
counter-search, or corroboration is unavailable or inconclusive, label the finding unresolved
rather than promoting it to a conclusion.

## Phase 4 — Synthesize

Author `docs/research/{slug}.md` from `../document/templates/research.md` — point at the
template, never copy its body into this skill. Every claim links its source inline; findings
and opinion live in separate sections; options that a later decision will choose between are
compared in a table, not narrative-ranked. This phase produces zero decision — recommending
or ranking belongs to the ADR that reads this file later, not to the file itself.

## Phase 5 — Gaps and confidence

Close with what the sweep left unresolved and how confident each finding is (source count,
source authority, recency). An empty "open questions" section is valid when none remain;
state why the evidence is sufficient rather than inventing gaps.

## Fan-out vs. single agent

Default: when the runtime exposes a subagent/Task tool, split Phase 2 across parallel sub-tasks — one per source cluster or comparison dimension — then merge captures before Phase 3. Escape hatch: no subagent support, or the topic is narrow enough that one sweep covers it → run all five phases sequentially in one pass. Either path produces exactly one `docs/research/{slug}.md`; fan-out changes how Phase 2 runs, never the output shape.

## Output

- Synthesis: `docs/research/{slug}.md`, authored from `../document/templates/research.md`.
- Verbatim capture: `docs/research/references/{slug}.md` per repeatedly-cited source, from `../document/templates/references.md`.

Slug matches the filename exactly; `document` owns the `docs/` layout, slug convention, and lifecycle rules for both paths — load it for those, not this skill.

## Boundaries

Not for deciding where an artifact lives, which template applies, or the `docs/` ontology in general — load `document`. Not for making the decision this research feeds: once findings are gathered, hand off to `document`'s ADR flow — this skill never writes a recommendation as if it were a conclusion.

## Verification

- [ ] Phase 1's question and the decision it feeds are both stated before any source is opened.
- [ ] Primary/official sources were swept before secondary ones.
- [ ] Each contested code-shaped claim has its executable probe or an explicit unresolved label.
- [ ] Each consequential non-code claim has counter-search, independent corroboration, or an explicit unresolved label.
- [ ] [Citation rules](#phase-4--synthesize) were applied.
- [ ] Findings and opinion sit in separate sections; options needing a future choice are tabulated, not ranked.
- [ ] A repeatedly-cited source has a verbatim `references/{slug}.md` capture, not a re-paraphrase from memory.
- [ ] The file states gaps and confidence and stops short of a decision.
