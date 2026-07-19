# Skill Evaluation Methodology

How to run and judge the eval-first artifacts the contract's §7 requires.
The contract owns *what* the gate is (which files, how many cases); this reference owns *how* to run the loop so its verdicts mean something.

## Table of Contents

1. [Baseline delta — the value measure](#1-baseline-delta--the-value-measure)
2. [Scenario evals](#2-scenario-evals)
3. [Trigger evals](#3-trigger-evals)
4. [Read the transcripts, not just the outputs](#4-read-the-transcripts-not-just-the-outputs)
5. [Improve without overfitting](#5-improve-without-overfitting)
6. [When to go heavyweight](#6-when-to-go-heavyweight)

---

## 1. Baseline delta — the value measure

A skill's measured value is the delta between a with-skill run and a without-skill run on the same prompt — never the with-skill output looking good in isolation.
A capable agent completes many tasks respectably with no skill at all; the skill earns its context cost only where the delta shows up.

- **Creating:** the baseline arm runs the prompt with no skill.
- **Updating:** snapshot the current version first (`cp -r` to scratch) and run the baseline arm against the snapshot — otherwise the comparison silently tests new-vs-nothing instead of new-vs-old.
- Run both arms in fresh agent sessions with no authoring context — the author already knows what the skill "meant to say" and cannot observe its ambiguity. Use parallel subagents when the runtime has them; sequential runs otherwise.
- Record cost alongside correctness (tokens, wall time when observable). A skill that wins on quality but doubles cost should say so in its body rather than surprise its callers.

## 2. Scenario evals

For the `evals/evals.json` cases (shape and count: contract §7):

- Make each `expected_behavior` concrete enough to verify — name the artifacts, decisions, or refusals a correct run produces, not "handles it well".
- Where a check is objective (file exists, format matches, command exits 0), script it rather than eyeballing it; the script outlives the session and re-runs on every update.
- Subjective outputs (writing tone, visual design) take qualitative review instead — do not force assertions onto judgments that need a human eye.
- An assertion that passes in **both** arms discriminates nothing about the skill — sharpen it or drop it.
- Put the burden of proof on the expectation: a pass needs cited evidence from the run, an uncertain verdict grades as fail, and a surface match (right filename, empty or wrong content) never counts.
- Probe each assertion for gameability — could a wrong-but-plausible output still pass it (a hallucinated document that happens to mention the right name)? If so, sharpen it until only genuine success passes.
- A case whose verdict flips across repeat runs is telling you something: either the eval is flaky or the skill under-specifies a decision the runs are guessing at.

## 3. Trigger evals

For the `evals/triggers.json` prompts (counts: contract §7):

- Write queries the way users actually type: concrete file names, column letters, a line of backstory, casual phrasing, the occasional typo. Mix lengths. A polished abstract query ("Extract text from PDF") tests nothing real.
- Should-trigger prompts cover different phrasings of the intent — including ones that never name the skill or its file type — plus cases where a sibling skill competes and this one should win.
- Should-NOT-trigger prompts must be near-misses that share keywords or concepts with the skill but need something else. An obviously irrelevant negative ("write a fibonacci function" against a PDF skill) is a free pass, not a test.
- Account for undertriggering: runtimes consult a skill only when the task plausibly benefits, so a trivial one-step prompt is a poor probe no matter how well the description matches. Make probe tasks substantive enough that consulting the skill is rational.
- Judge trigger-fit with fresh eyes — an agent session that has not seen the authoring conversation, given only the library's name+description lines and the probe prompt.
- After tuning the description against failures, re-judge on prompts that were **not** used for the tuning. A description iterated against one fixed set memorizes that set; held-out prompts are what catch it.

## 4. Read the transcripts, not just the outputs

The run transcripts carry two signals the final artifacts hide:

- **Repeated work** — when every run hand-writes the same helper or re-derives the same schema, the skill should bundle it once: code into `scripts/`, knowledge into `references/` (contract §5 owns the classification).
- **Wasted detours** — when runs consistently burn effort on an unproductive path, find the skill sentence sending them there and cut it, then re-run. Every line of body must pull its weight; removal is an experiment that costs one eval cycle.

## 5. Improve without overfitting

The loop iterates on a handful of examples because that is fast — but the skill ships to prompts nobody drafted.
When a run fails:

- Generalize the lesson before encoding it. Ask what class of prompt fails, not what patch makes this one pass.
- Prefer explaining why over adding constraints; a rule the model understands transfers to unseen cases, a bare directive does not. Piling on caps-lock rigidity is the signature of overfitting (style rules: contract §4).
- For a stubborn failure, change the frame — a different metaphor, a different working pattern — rather than adding one more rule per failed run. Reframes are cheap to try and occasionally land something great.
- The memorization check is §3's held-out re-judging: prompts that were not used for the tuning judge the tuned result.
- Stop when feedback comes back clean or improvements stop being meaningful; more loops on the same three examples past that point only overfit them.

## 6. When to go heavyweight

The light loop above is the default and suffices for most packages.
Escalate to benchmark machinery — repeated runs with mean/stddev, token/latency aggregation, blind A/B judging by an independent agent that is not told which output is which — only when two versions genuinely compete, a regression would be costly, or a claim ("44% better") needs numbers behind it.
Where a vendor runtime ships this machinery ready-made, its lens file says what exists and how to drive it — today `vendor-anthropic.md` is the one that documents such a harness; the methodology here stays the same either way.
