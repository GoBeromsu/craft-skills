# Promotion Admission Checklist

The admission rubric for **Stage 0: Admission**. The generalized reviewer (`agents/reviewer.md`)
applies this checklist to a candidate workflow **before Harvest**, in a clean lane, to answer one
question: *does this candidate belong in craft-skills at all?*

**Default verdict is REJECT.** Every question starts failed. A ✓ requires active evidence the
reviewer can name — not the absence of a reason to reject. A candidate is **ADMITTED only when all
five questions carry a ✓**; any ✗ yields REJECT routed to the destination named by the first
failing question.

## Tier definitions

The candidate is admissible only as **Tier 2**. The other two tiers route out.

| Tier | What it is | Where it belongs |
|------|-----------|------------------|
| **Tier 1 — harness** | A mature upstream workflow another maintainer already owns and evolves (interview, test-drive, review). | Referenced from craft-skills, never re-authored. |
| **Tier 2 — convention** | A portable, harness-agnostic decision rule the team owns — *the* admissible class. | Owned in `craft-skills/skills/`. |
| **Tier 3 — project-specific** | A workflow bound to one project's stack, data, or paths. | Stays in that project's repository. |

## The five drop-questions

### Q1 — Reusability
**✓ requires:** the candidate is true and useful on a *next* project whose stack and domain are
disjoint from the one it came from. **Evidence:** name one concrete disjoint project where it
applies unchanged.
**Fail-action → project-local.** A workflow that only pays off on its originating project is Tier 3
— keep it in that project's repository.

### Q2 — Ownership
**✓ requires:** no mature upstream harness already performs this workflow. **Evidence:** name the
upstream candidates checked and state why each falls short.
**Fail-action → `using-our-stack` reference.** When an upstream already owns the workflow, record a
thin reference entry — a pointer in the curation manifest naming the upstream harness that owns it —
instead of re-authoring the workflow here. (The candidate is Tier 1: referenced, not owned.)

### Q3 — Convention-not-artifact
**✓ requires:** the candidate encodes a *how / who / which* decision rule — a repeatable convention
— rather than a one-off script, dataset, or document. **Evidence:** state the decision the
convention makes for the next reader.
**Fail-action → project-local.** A single concrete artifact with no decision rule to generalize is
Tier 3 — it travels with its project, not the skill library.

### Q4 — Portability
**✓ requires:** the body runs on ≥2 harnesses with no dependency on any single harness's internals —
plain-markdown instructions, `${ENV_VAR}` indirection, and no call that only one harness exposes.
**Evidence:** name the two harnesses it runs on and confirm no harness-internal call in the body.
**Fail-action → project-local.** A body wired to one harness's internals is not portable; keep it
local until the dependency is removed, or split it (Q5).

### Q5 — Boundary-purity
**✓ requires:** the candidate is a *pure* Tier 2 convention — a single concern with one owner — not
a hybrid that fuses an upstream-owned part with a team-delta part. **Evidence:** confirm the one
concern and its one owner.
**Fail-action → split-then-resubmit.** When the candidate is hybrid, separate the upstream-reference
part (route per Q2) from the team-delta part, then resubmit only the team-delta part to admission.

## Verdict

- **ADMIT** — all five questions ✓. The candidate proceeds to Harvest.
- **REJECT** — any ✗. Record the routed destination of the first failing question.

## Result-routing rule

Every REJECT records where the candidate landed and why, so the same candidate is not re-litigated:

| Field | Content |
|-------|---------|
| Candidate slug | The candidate's kebab identifier. |
| Failing question(s) | Each ✗ question by number. |
| Evidence | The one-line reason each failed. |
| Routed destination | `project-local` · `using-our-stack` reference · `split-then-resubmit`. |

| Routed destination | Meaning |
|--------------------|---------|
| `project-local` | Stays in the originating project's repository (Tier 3); not promoted. |
| `using-our-stack` reference | A thin pointer to the upstream harness that owns the workflow (Tier 1); recorded as a reference target, not re-authored. |
| `split-then-resubmit` | The team-delta part is separated from the upstream part; only the team-delta part re-enters admission. |

The admission receipt (`evals/admission-<candidate-slug>-<date>.md`) is the durable record. A
candidate already carrying a REJECT receipt for an unchanged reason is not re-judged — point at the
existing receipt. Re-admission requires a material change to the candidate (a new evidence answer to
the failing question), recorded as a fresh receipt.
