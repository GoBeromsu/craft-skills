# Writer / Reviewer Pipeline

Authoritative source for the subagent invocation templates referenced from `SKILL.md`.
Update the templates here; `SKILL.md` references these sections by name only.

**Model alignment:** a craft-skills skill package is `SKILL.md` + `CHANGELOG.md` (+ optional
`references/`, `scripts/`, `tests/`, `evals/`, `.env.example`). There is **no** unrelated
note/template stub and **no** `## Change Log` section inside `SKILL.md`. The change history lives in the
package's `CHANGELOG.md`. The canonical format is `references/schemas.md`.

## § Admission Task

Stage 0. Runs before Harvest, as a fresh subagent in a clean context. Single pass — never the
multi-model consensus loop. The reviewer agent runs in `admission` mode and is **not** given the
author's promotion rationale.

```
Task(
  subagent_type = "oh-my-claudecode:code-reviewer",
  model         = "sonnet",
  prompt        = """
    PERSONA OVERRIDE: You are the skillify reviewer agent in ADMISSION mode. Suppress all default
    code-review heuristics (style, complexity, test coverage). Read your charter and the admission
    rubric and execute them verbatim:
      skills/skillify/agents/reviewer.md          — the impartial-judge charter (admission mode)
      skills/skillify/references/checklist.md      — the five drop-questions, fail-actions, routing

    Judge SCOPE ONLY: does this candidate belong in craft-skills? Default every drop-question to ✗;
    mark ✓ only with named evidence. Do NOT read or request the author's promotion rationale — you
    judge the candidate on its own evidence. Do NOT check format (that is a Layer-1 script's job).

    Candidate slug:        {candidate_slug}
    Candidate workflow:    {candidate_description_or_path}
    Tier definitions:      skills/skillify/references/checklist.md

    Output: write the admission receipt (the Admission output block defined in reviewer.md —
    per-question ✓/✗ + one-line evidence + routed destination + ADMIT|REJECT verdict) to
    skills/skillify/evals/admission-{candidate_slug}-{date}.md. No prose outside the receipt.
  """
)
```

On REJECT the author has no veto; surface the receipt and escalate to the human. On ADMIT the
candidate proceeds to the Writer Task below.

## § Writer Task

```
Task(
  subagent_type = "oh-my-claudecode:executor",
  model         = "sonnet",
  prompt        = """
    You are a skill author. Produce a compliant SKILL.md and a CHANGELOG.md bullet for
    one craft-skills skill package.

    MANDATORY before writing, read in full:
      skills/skillify/agents/writer.md      — the complete authoring process and lane contract
      skills/skillify/references/schemas.md  — the canonical SSOT for frontmatter, anatomy,
                                               recipe-law, secret hygiene, and version bumps
      AGENTS.md                              — boundary charters + routing law

    Mode: {create | update}
    Target SKILL.md:   {SKILL_DIR}/SKILL.md
    Target CHANGELOG:  {SKILL_DIR}/CHANGELOG.md
    Change reason (update mode): {change_reason}
    Reviewer feedback (second pass only): {reviewer_rationale}

    This template owns the invocation only, never the content rules. Take every frontmatter,
    section-flow, secret-hygiene, and version-bump rule from writer.md and schemas.md as read
    at run time — do not rely on any schema or section list reproduced from memory.

    Output: write the complete SKILL.md to {SKILL_DIR}/SKILL.md and the updated
    CHANGELOG.md to {SKILL_DIR}/CHANGELOG.md.
  """
)
```

## § Reviewer Task

```
Task(
  subagent_type = "oh-my-claudecode:code-reviewer",
  model         = "sonnet",
  prompt        = """
    PERSONA OVERRIDE: You are the skillify reviewer agent. Suppress all default code-review
    heuristics (style, complexity, test coverage). Read your charter and execute it verbatim:
      skills/skillify/agents/reviewer.md

    The reviewer judges QUALITY ONLY — trigger-fit, anatomy intent, judgment/recipe-law
    compliance, and routing coherence. Format is a Layer-1 script gate
    (scripts/validate-skill-format.py), never the reviewer's job — do not re-check frontmatter
    key counts, section presence, or CHANGELOG regex here. Those belong to the script.

    SKILL.md path:    {SKILL_DIR}/SKILL.md
    CHANGELOG path:   {SKILL_DIR}/CHANGELOG.md
    Reviewer charter: skills/skillify/agents/reviewer.md
    Contract SSOT:    skills/skillify/references/schemas.md (reference, not a re-check list)

    Response format (strict — no other content):
    verdict: approve | request_changes
    rationale: <one paragraph, max 150 words, referencing only reviewer.md's evaluation axes>
  """
)
```

## § Grader Task

```
Task(
  subagent_type = "oh-my-claudecode:code-reviewer",
  model         = "sonnet",
  prompt        = """
    PERSONA OVERRIDE: You are the skillify grader agent (eval/dynamic lane). Read your charter
    and execute it verbatim:
      skills/skillify/agents/grader.md

    Grade each tier-gate assertion against the ACTUAL run artifacts, not the transcript's
    claims. Then critique the assertions themselves. This is the dynamic eval lane — do not
    rewrite the skill and do not check format (that is the Layer-1 script's job).

    Assertions:      {assertions}
    Transcript path: {transcript_path}
    Outputs dir:     {outputs_dir}
    Skill dir:       {skill_dir}
    Grader charter:  skills/skillify/agents/grader.md

    Output: write the JSON grading object defined in grader.md to {outputs_dir}/../grading.json
    (per-assertion fields: text, passed, evidence). No prose outside the JSON.
  """
)
```

## § Verdict parsing + error-handling

```
Parse reviewer response for "verdict: approve" or "verdict: request_changes".
- verdict: approve         → commit current draft (SKILL.md + CHANGELOG.md). Done.
- verdict: request_changes → re-invoke Writer Task ONCE with reviewer_rationale as feedback.
                             Commit second draft unconditionally (no further review).
- neither string found     → log `WARN: unparseable reviewer verdict — treating as approve`.
                             Commit current draft.
```

## § Timeout contract

```
Each Task() invocation has a timeout of 90 seconds.
- Writer Task timeout   → abort, surface error, do NOT commit a partial file.
                          Log `WARN: Task timeout after 90s — writer aborted`.
- Reviewer Task timeout → treat as approve; commit writer's draft.
                          Log `WARN: Task timeout after 90s — reviewer skipped`.
- Grader Task timeout   → record an ungraded receipt; do NOT mark tier-gate assertions passed.
                          Log `WARN: Task timeout after 90s — grader skipped, assertions ungraded`.
```

## § Post-commit verification gate

```bash
# SKILL.md must NOT contain a Change Log section (history lives in CHANGELOG.md).
grep -q '^## Change Log' "$SKILL_DIR/SKILL.md" \
  && echo "WARN: found ## Change Log in SKILL.md — history belongs in CHANGELOG.md"

# CHANGELOG.md must carry at least one dated bullet.
grep -Eq '^- [0-9]{4}-[0-9]{2}-[0-9]{2} — ' "$SKILL_DIR/CHANGELOG.md" \
  || echo "WARN: CHANGELOG.md missing a dated 'YYYY-MM-DD — why; what' bullet"

# No tracked real .env in the package (only .env.example is committed).
git ls-files "$SKILL_DIR" | grep -E '/\.env(\.[A-Za-z0-9_-]+)?$' | grep -v '\.env\.example$' \
  && echo "WARN: tracked real .env in package — must be gitignored"
```
Run after every commit. On any warning, surface to user and continue (do not abort).
