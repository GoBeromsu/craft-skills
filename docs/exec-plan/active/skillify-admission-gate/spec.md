---
slug: skillify-admission-gate
type: spec
status: active
date: 2026-06-16
author: gobeumsu
target-repo: craft-skills
source: relocated from eldercare .omc/specs/deep-interview-skillify-admission-gate.md (deep-interview --quick, ambiguity 4.8%, PASSED)
---

# Deep Interview Spec: skillify Admission Gate

## Metadata
- Interview ID: skillify-admission-gate
- Mode: --quick
- Rounds: 2 (Round 0 topology + Round 1 design)
- Final Ambiguity Score: 4.8%
- Type: brownfield
- Generated: 2026-06-16
- Threshold: 0.05
- Threshold Source: ~/.claude/settings.json
- Target repo: craft-skills (https://github.com/GoBeromsu/craft-skills, local `${CRAFT_SKILLS_REPO_PATH}`) — NOT eldercare
- Status: PASSED

## Clarity Breakdown
| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Goal Clarity | 0.97 | 0.35 | 0.340 |
| Constraint Clarity | 0.95 | 0.25 | 0.238 |
| Success Criteria | 0.93 | 0.25 | 0.233 |
| Context Clarity | 0.95 | 0.15 | 0.143 |
| **Total Clarity** | | | **0.952** |
| **Ambiguity** | | | **0.048** |

## Topology
| Component | Status | Description | Coverage / Deferral Note |
|-----------|--------|-------------|--------------------------|
| `references/checklist.md` | active | Promotion Admission Checklist — the admission rubric (5 drop-questions + result routing) | AC-1..AC-3 |
| `agents/reviewer.md` (generalize) | active | Generalize EXISTING reviewer charter into a checklist-driven impartial judge | AC-4..AC-6 |
| `skillify/SKILL.md` Stage 0 | active | Add "Stage 0: Admission" to Core Process; single clean pass; admission receipt; Tier-1 wiring | AC-7..AC-10 |
| top-level `agents/` dir + `using-our-stack` manifest | deferred | Separate follow-up work item — user-confirmed defer 2026-06-16 |
| eldercare cleanup (promote worktree-workflow + documentation-and-adrs; demote 6 Tier-1 copies to references) | deferred | Separate follow-up work item — user-confirmed defer 2026-06-16 |
| 3-tier model as a craft-skills ADR | deferred | Separate follow-up work item — user-confirmed defer 2026-06-16 |
| eldercare PR #112 (.claude/skills symlink) push | deferred | Already committed on its worktree branch; push is its own closure step, kept out of this work |

## Goal
Add an **admission gate** to craft-skills' `skillify` skill that answers a single question the
current gate never asks: *"Does this candidate even belong in craft-skills?"* — distinct from
the existing Layer-1 (deterministic format) and Layer-2 (multi-model quality/trust consensus)
gates. The gate runs **before Harvest**, judged in a **clean lane by a generalized impartial
reviewer** driven by a checklist, so project-local / upstream-owned / non-portable candidates
are rejected cheaply before any authoring effort is spent.

## Constraints
- Target is the **craft-skills** repo, not eldercare. Delivery follows craft-skills' own worktree
  workflow: branch → commit → PR.
- `skillify` is **protected infrastructure**. Editing `skills/skillify/**` requires explicit
  current-turn user approval + `SKILLIFY_EDIT_TOKEN` set during the edit, then unset.
- Must pass skillify's own gates on the changed package: Layer-1 format scripts
  (`validate-skill-format.py`, `validate-runtime-hygiene.py`) and Layer-2 consensus; bump
  `skillify` `version` (MINOR — new Stage 0 phase, backward-compatible) and append a dated
  `CHANGELOG.md` bullet.
- Body must obey skillify's recipe-completeness law: present-tense imperative only; no
  history / attribution / jargon contamination; MECE parts.
- **Reference-only philosophy** is the spine of the checklist content — the gate must actively
  reject re-authoring anything a mature upstream harness already does (route to a reference
  instead).
- Do NOT create a new `admission.md` agent. Reuse and generalize the EXISTING `agents/reviewer.md`.
- The admission judgment is a **single clean pass**, not multi-model consensus (consensus is
  reserved for the expensive Layer-2 trust layer).

## Non-Goals
- Creating the top-level `agents/` directory or the `using-our-stack` manifest (deferred).
- Eldercare skill promotion/demotion cleanup (deferred).
- Writing the 3-tier-model ADR (deferred).
- Pushing eldercare PR #112 (separate closure).
- Changing Layer-1 or Layer-2 gates themselves (admission is additive, pre-Harvest).

## Acceptance Criteria
- [ ] **AC-1** `skills/skillify/references/checklist.md` exists with 5 numbered **drop-questions**,
      each phrased so the default verdict is REJECT and a ✓ requires active evidence:
      Q1 Reusability (true on a stack/domain-disjoint next project?), Q2 Ownership (mature upstream
      already does it → route to reference, do not re-author), Q3 Convention-not-artifact
      (how/who/which vs one-off script/data/doc), Q4 Portability (harness-agnostic, runs on ≥2
      harnesses with no harness-internal body dependency), Q5 Boundary-purity (hybrid → split
      upstream-reference from our-delta before promoting).
- [ ] **AC-2** Each question states its routed fail-action (project-local / `using-our-stack`
      reference / split-then-resubmit).
- [ ] **AC-3** Checklist defines a result-routing rule that **records where and why** a rejected
      candidate landed, so the same candidate is not re-litigated.
- [ ] **AC-4** `agents/reviewer.md` is generalized to a **checklist-driven impartial judge**:
      it receives a checklist/rubric + candidate + tier defs and renders ✓/✗-per-item + verdict,
      with no stake in the outcome and no self-approval.
- [ ] **AC-5** The generalized reviewer preserves the existing quality-review responsibility
      (post-author, anatomy/trigger-fit/recipe-law) AND serves admission (pre-harvest, scope) —
      differentiated by *which checklist it is given* and *when it is invoked*, not by two
      overlapping charters. MECE is preserved at the checklist level.
- [ ] **AC-6** Reviewer charter explicitly forbids receiving the author's promotion rationale in
      the admission invocation (rationale would contaminate scope judgment).
- [ ] **AC-7** `skills/skillify/SKILL.md` Core Process gains **"Stage 0: Admission"** before
      Harvest/Detect-mode: spawn the generalized reviewer as a fresh subagent (clean context) with
      `checklist.md` + candidate + tier defs; single pass; emit an admission receipt.
- [ ] **AC-8** On REJECT the author has **no veto** — disagreement escalates to the human; the
      author cannot self-approve past the gate.
- [ ] **AC-9** Admission receipt is written to `skills/skillify/evals/admission-<candidate-slug>-<date>.md`
      (skillify package owns it, since a rejected candidate may have no skill directory yet),
      recording per-question ✓/✗ + one-line evidence + verdict ADMIT|REJECT + routed destination.
      On ADMIT the candidate proceeds to Harvest; the receipt is referenced at Tier-1 entry.
- [ ] **AC-10** Tier-1 entry gate adds a precondition: admission receipt exists with verdict ADMIT.
- [ ] **AC-11** skillify `version` bumped (MINOR); `CHANGELOG.md` gains one dated bullet;
      Layer-1 format + runtime-hygiene scripts pass on the diff; Layer-2 consensus receipt produced.
- [ ] **AC-12** Delivered as a craft-skills branch → commit → PR; no edits to `skills/skillify/**`
      without the approval-token break-glass procedure.

## Assumptions Exposed & Resolved
| Assumption | Challenge | Resolution |
|------------|-----------|------------|
| Admission needs its own agent | reviewer.md already exists; 4 charters violates "small asset" | Generalize existing reviewer into checklist-driven judge; no new agent |
| Gate should be as rigorous as Layer-2 | Admission is a cheap binary scope decision | Single clean pass; consensus stays for the trust layer only |
| MECE must be at the agent level | One judge serving two checklists can stay MECE | MECE enforced at the *checklist* level; lane enforced by *invocation timing* |
| Receipt lives in the candidate skill dir | A rejected candidate may have no dir yet | Receipt lives in the skillify package `evals/`, keyed by candidate slug |
| This work also builds agents/ + manifest + ADR + cleanup | Scope creep across repos | Scoped to the 3 admission-gate artifacts; rest deferred to follow-up items |

## Technical Context (brownfield)
- `skillify/SKILL.md` already defines: 3 stages (Harvest → Prove → Cement), Layer-1 (format
  scripts) / Layer-2 (consensus.py multi-model convergence), Tier-1/Tier-2 gates, MECE law,
  recipe-completeness + contamination gates, lane separation ("never self-approve"), and
  protected-infra governance (PreToolUse hook + `SKILLIFY_EDIT_TOKEN`).
- Existing agent charters: `agents/writer.md`, `agents/reviewer.md`, `agents/grader.md`.
- The admission gate slots in as **Stage 0**, upstream of all existing stages; it reuses the
  established lane-separation and receipt-artifact patterns (mirrors `evals/consensus-*.md`).
- 5-key frontmatter contract + per-package `CHANGELOG.md` + semver are enforced by Layer-1.

## Ontology (Key Entities)
| Entity | Type | Fields | Relationships |
|--------|------|--------|---------------|
| Admission Gate | core domain | stage=0, verdict, receipt | precedes Harvest; gates Tier-1 entry |
| Admission Checklist | core domain | 5 drop-questions, routing rules | consumed by generalized Reviewer |
| Generalized Reviewer | core domain | checklist-input, lane, verdict | runs admission (pre-harvest) + quality (post-author) |
| Admission Receipt | supporting | per-question verdict, evidence, routed-destination | written to skillify/evals/ |
| Candidate | external | workflow, slug | judged by Admission Gate |
| Tier (1/2/3) | core domain | reuse, ownership, portability | defines admission criteria |

## Interview Transcript
<details>
<summary>Full Q&A (2 rounds)</summary>

### Round 0 — Topology / Scope
**Q:** Core 3 components confirmed; include boundary items 4–7 (agents/ dir + manifest, eldercare cleanup, 3-tier ADR, #112 push)?
**A:** "admission gate만 (추천)" — scope to the core 3; defer 4–7 as follow-up work items.

### Round 1 — Judge structure + mechanism
**Q1:** Who performs admission judgment (reviewer/writer/grader already exist)?
**A1:** "범용 reviewer로 일반화" — generalize existing reviewer.md into a checklist-driven impartial judge; no new admission.md.
**Q2:** How does the gate judge?
**A2:** "단일 깨끗한 판정 1회" — single clean pass; consensus reserved for Layer-2.

</details>
