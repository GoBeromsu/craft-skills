# Skill Evaluation Methodology

How to run and interpret the outcome checks the contract's §7 lets the agent choose.
The contract owns evidence selection, official-original ownership, and current/stale/failure update semantics; this reference owns how to run and read the selected checks.
Generated transcripts, scores, campaign receipts, and run outputs are gitignored scratch or retired Git history, not a pass condition.
Do not lock wording or procedure snapshots; preserve real functional, security, and data-integrity fixtures.
Official vendor evaluator harnesses may exist upstream; this library does not copy them or require their generated outputs.
Label every result as **executed** (a real command, run, or observed effect) or **reviewed** (reading a document, contract, or diff); a review never stands in for a run, and an unavailable check is reported as not run.
Evaluate what the task asked for — the requested outcome and the description's trigger fit — without adding a uniform run, case, or provider quota to every skill.
Escalate to optional heavyweight machinery only when actual task risk warrants it.

## Table of Contents

1. [Baseline delta — the value measure](#1-baseline-delta--the-value-measure)
2. [Optional authored scenarios](#2-optional-authored-scenarios)
3. [Routing probes](#3-routing-probes)
4. [Fresh-eyes judge](#4-fresh-eyes-judge)
5. [Read the transcripts, not just the outputs](#5-read-the-transcripts-not-just-the-outputs)
6. [Improve without overfitting](#6-improve-without-overfitting)
7. [When to go heavyweight](#7-when-to-go-heavyweight)

---

## 1. Baseline delta — the value measure

An improvement claim needs a matched comparison, not merely an attractive with-skill output.
Use baseline/candidate arms when comparing designs, changing routing pressure, or claiming better performance.
A format repair or safety regression need not improve an unrelated model benchmark.
Do not impose a positive measured delta, generated score file, or wording snapshot as a universal publication condition.

- **Creating:** the baseline arm runs the prompt with no skill.
- **Updating:** snapshot the current version first (`cp -r` to scratch) and run the baseline arm against the snapshot — otherwise the comparison silently tests new-vs-nothing instead of new-vs-old.
- Run both arms in fresh agent sessions with no authoring context — the author already knows what the skill "meant to say" and cannot observe its ambiguity. Use parallel subagents when the runtime has them; sequential runs otherwise.
- Record cost alongside correctness (tokens, wall time when observable). A skill that wins on quality but doubles cost should say so in its body rather than surprise its callers.
- When comparing a model, reasoning/effort setting, or harness change, use representative tasks and record success, cited evidence, token use, and latency for both arms. Verify the conclusion again in a fresh context; do not promote a configuration from one favorable run.

## 2. Optional authored scenarios

When the agent chooses reusable authored scenarios, they may live under `tests/<name>/evals/` (contract §7).
They are optional inputs, not a required graded corpus, JSON vocabulary, schema, or case count.

- Name the artifacts, decisions, refusals, or effects a correct run produces — not "handles it well".
- Where a check is objective (file exists, format matches, command exits 0, secret stays unexposed, write is atomic), script the real effect rather than eyeballing a wording snapshot; the script outlives the session and re-runs on every update.
- Subjective outputs (writing tone, visual design) take qualitative review instead — do not force assertions onto judgments that need a human eye.
- An assertion that passes in both arms does not prove improvement, but may still guard an important safety invariant or regression; retain it when the contract requires that protection.
- A pass needs cited run evidence. Record unavailable or uncertain evidence as unverified/not-run with a reason, never as passed; a required uncovered behavior still blocks admission. A surface match with empty or wrong content never counts.
- Probe each assertion for gameability — could a wrong-but-plausible output still pass it (a hallucinated document that happens to mention the right name)? If so, sharpen it until only genuine success passes.
- A case whose verdict flips across repeat runs is telling you something: either the scenario is flaky or the skill under-specifies a decision the runs are guessing at.

Presence of scenario files is not a quality gate.
Do not commit generated transcripts or scores as the success artifact.

## 3. Routing probes

When the agent selects relevant routing positives and near-misses (optional; selection policy: contract §7):

- Write queries the way users actually type: concrete file names, column letters, a line of backstory, casual phrasing, the occasional typo. Mix lengths. A polished abstract query ("Extract text from PDF") tests nothing real.
- Positives cover different phrasings of the intent — including ones that never name the skill or its file type — plus cases where a sibling skill competes and this one should win.
- Negatives must be near-misses that share keywords or concepts with the skill but need something else. An obviously irrelevant negative ("write a fibonacci function" against a PDF skill) is a free pass, not a test.
- Account for undertriggering: runtimes consult a skill only when the task plausibly benefits, so a trivial one-step prompt is a poor probe no matter how well the description matches. Make probe tasks substantive enough that consulting the skill is rational.
- Judge trigger-fit with fresh eyes — an agent session that has not seen the authoring conversation, given only the library's name+description lines and the probe prompt.
- After tuning the description against failures, re-judge on prompts that were **not** used for the tuning. A description iterated against one fixed set memorizes that set; held-out prompts are what catch it.

Do not treat a frozen prompt list, exact trigger vocabulary, or procedure order as proof of routing quality by itself.

### Evidence gate for a leading routing directive

The optional `MUST USE <bounded ownership clause>.` form in contract §3 needs behavioral evidence because its lexical shape cannot prove MECE ownership.

1. Choose positives and nearest-sibling negatives that exercise the claimed ownership boundary, not an arbitrary count.
2. Assign stable IDs and freeze prompts, labels, and tuning/unseen partitions before tuning.
3. Record the baseline and prompt-set identities; changes to either require new evidence for the affected comparison.
4. Run matched baseline/candidate cases and record successes, misses, false positives, and actual denominators.
5. Freeze the candidate before consulting unseen verdicts; use an independent read-only judge on the relevant discovery surface.
6. Record the runtime, model or human judge, and surface for each result. Test distinct parser/discovery boundaries where needed, not every model/runtime combination.
7. Demonstrate any claimed improvement and check regressions on the evaluated intents. Keep ordinary prose when stronger routing pressure is not justified.

Uncertain, uncited, or flaky judgments cannot establish the claim; report the limitation rather than inventing a clean score.
A perfect baseline does not justify self-application; the general directive capability may still ship.
The evidence must quote the proposed ownership class and identify its explicit included intents plus excluded or handed-off nearest-sibling intents.
Scenario review also confirms that body prose gained neither directive syntax nor repeated caps-lock rigidity.

## 4. Fresh-eyes judge

Use a capable model or human in a fresh context, independent from the authoring session, as the qualitative judge.
Record the exact runtime, model or human identity, and discovery surface so the verdict proves only the environment that actually produced it.
Keep the judge read-only through enforced tool or permission controls rather than prompt intent alone.
Give it only the artifacts needed for the rubric: do not include the author's rationale or identify which A/B arm is the candidate.
Require cited evidence for the verdict, and treat missing evidence or uncertain judgment as failure rather than letting the authoring session self-judge.
When GJC orchestrates authoring, follow the selected workflow and evidence boundary in [`vendor-gjc.md`](vendor-gjc.md); it does not prescribe a fixed profile or a second provider as the judge.

## 5. Read the transcripts, not just the outputs

Selected run transcripts can carry two signals the final artifacts hide; they remain scratch, not a required deliverable:

- **Repeated work** — when every run hand-writes the same helper or re-derives the same schema, the skill should bundle it once: code into `scripts/`, knowledge into `references/` (contract §5 owns the classification).
- **Wasted detours** — when runs consistently burn effort on an unproductive path, find the skill sentence sending them there and cut it, then re-check the affected outcome. Every line of body must pull its weight.

## 6. Improve without overfitting

The loop iterates on a handful of examples because that is fast — but the skill ships to prompts nobody drafted.
When a run fails:

- Generalize the lesson before encoding it. Ask what class of prompt fails, not what patch makes this one pass.
- Prefer explaining why over adding constraints; a rule the model understands transfers to unseen cases, a bare directive does not. The contract §3 routing clause is an evidence-gated discovery signal, not permission to pile caps-lock rigidity into body prose.
- For a stubborn failure, change the frame — a different metaphor, a different working pattern — rather than adding one more rule per failed run. Reframes are cheap to try and occasionally land something great.
- The memorization check is §3's held-out re-judging: prompts that were not used for the tuning judge the tuned result.
- Stop when required behavior is supported and further improvements are not meaningful; repeated tuning on the same examples can merely overfit them.

## 7. When to go heavyweight

The light loop above is the default and suffices for most packages.
Escalate only when actual task risk warrants it — two versions genuinely compete, a regression would be costly, or a numeric claim needs numbers — using repeated runs with mean/stddev, token/latency aggregation, or blind A/B judging by an independent agent that is not told which output is which.
That machinery is never a publication gate and must not replace functional, security, or data-integrity fixtures.
Where a vendor runtime ships this machinery ready-made, its lens names the official surface and the boundary: use it on that vendor's runtime when the risk justifies it; do not copy the harness into this repository or require its generated outputs as local SSOT.
The methodology here stays the same either way.
