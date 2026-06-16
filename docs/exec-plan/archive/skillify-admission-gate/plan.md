---
slug: skillify-admission-gate
type: plan
status: done
date: 2026-06-16
author: gobeumsu
spec: ./spec.md
---

# Plan: skillify Admission Gate (Stage 0)

## Requirements Summary
Add a pre-Harvest **Stage 0: Admission** gate to the protected `skillify` skill so candidates
that are project-local, upstream-owned, or non-portable are rejected before any authoring cost.
Judgment is a single clean pass by the **generalized reviewer** driven by a new `checklist.md`.
Definition of done = AC-1..AC-12 in `spec.md`.

## Decision Drivers
1. Reference-only philosophy — never re-author what a mature upstream harness already owns.
2. Small-asset discipline — generalize the existing reviewer, do not add a 4th agent charter.
3. Cheap binary scope decision — single clean pass, not multi-model consensus (that is Layer-2).
4. MECE — one judge, two checklists, differentiated by invocation timing; no overlapping charters.
5. Protected-infra governance — branch → commit → PR; Layer-1 + Layer-2 gates on the diff.

## Implementation Steps
1. **`references/checklist.md`** (AC-1..3) — 5 numbered drop-questions, default verdict REJECT,
   ✓ requires active evidence; each carries a routed fail-action; a result-routing rule records
   where/why a rejected candidate landed so it is not re-litigated.
2. **`agents/reviewer.md`** (AC-4..6) — generalize into a checklist-driven impartial judge with
   two modes (Admission pre-harvest / Quality post-author) selected by the supplied rubric +
   invocation timing; admission invocation excludes the author's promotion rationale; no
   self-approval; REJECT escalates to the human.
3. **`references/pipeline.md`** — add `§ Admission Task` invocation template (SKILL.md references
   invocation templates by name only; MECE keeps the template out of SKILL.md).
4. **`SKILL.md`** (AC-7..11) — add Stage 0: Admission to Core Process before Harvest/Detect-mode;
   spawn the generalized reviewer as a fresh clean subagent, single pass, emit receipt to
   `evals/admission-<candidate-slug>-<date>.md`; REJECT → human, author has no veto; add Tier-1
   entry-gate precondition (admission receipt verdict=ADMIT); bump `version` 3.0.4 → 3.1.0;
   append a dated `CHANGELOG.md` bullet.

## Verification Steps
- Layer-1: `validate-skill-format.py` + `validate-runtime-hygiene.py --diff-base origin/main...HEAD` pass.
- Layer-2: `consensus.py --skill skills/skillify` produces a receipt; read convergence verdict.
- AC checklist: each AC-1..AC-12 satisfied; recipe-law (no history/attribution/jargon) clean; MECE preserved.

## Risks and Mitigations
- **Risk:** receipt files (`evals/`) get committed. **Mitigation:** stage files selectively; never `git add evals/`.
- **Risk:** generalized reviewer overlaps grader's dynamic-eval lane. **Mitigation:** admission/quality are static-eval judgment against a checklist; grader stays the post-run artifact-vs-assertion grader — distinct rubric + distinct timing.
- **Risk:** unrelated untracked `skills/distil/` bleeds into the commit. **Mitigation:** explicit per-file staging.

## Distill candidates (ADR follow-ups, deferred)
- 3-tier skill model (harness-reference / convention-own / project-local) — flagged in spec as a deferred craft-skills ADR.
