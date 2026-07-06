# ML Training Discipline

A training run is a claim about what the model can do; the ladder below is the evidence that makes the claim believable before it makes the run fast, large, or novel.

## Table of Contents

- [Hard rules](#hard-rules) — the discipline ladder, the experiment tracking table, when to relax the ladder, the uncommitted-changes-at-launch guard
- [Hand-offs](#hand-offs)

---

## Hard rules

### The discipline ladder (apply in order, every new modeling effort)

**1. Overfit a single batch first.** Before any full run, take one batch — or a handful of examples — and train on it alone until the loss drops to (near) zero, or accuracy reaches (near) 100%. This is the canonical smoke test: if the model cannot memorize a tiny batch, the pipeline itself is broken (wrong loss, a label/feature mismatch, a gradient that never flows), and no amount of full-dataset training will fix that.

Grey zone — no single grep catches this; judge by the loss curve: a single-batch loss that plateaus well above zero after generous training steps means the pipeline is broken, not that the batch is "just hard."

Fast diagnosis when step 1 fails:

| Symptom | Likely cause |
|---|---|
| Loss is `NaN` within the first few steps | Learning rate too high, or an unguarded division/log inside the loss |
| Single-batch loss won't reach zero, even after many steps | A data/label mismatch, a gradient path that never actually reaches some parameters, or the wrong loss function for the task |
| Train loss drops but validation loss does not, on the *full* run | Overfitting — this is a step-6 (eval discipline) concern, not a step-1 one; step 1 only concerns the single-batch memorization check |

**2. Baseline before novelty.** Every modeling effort starts with the cheapest baseline that could plausibly work — a majority-class or mean predictor, a linear model, or a pretrained model with only its head trained (frozen backbone). A novel architecture is judged against that number, in the same report, not against "no result at all."

```bash
ls configs/ | grep -iE 'baseline' || echo "FAIL: no baseline config found — nothing for the novel run to beat"
```

Pass: a baseline config exists (or the report cites a numeric baseline the reader can check). Fail: no baseline present — a "beats prior work" claim has nothing to actually beat.

**3. One variable per experiment.** A single experiment changes exactly one variable from its predecessor; the config diff between two experiments *is* the experiment's identity.

```bash
diff configs/exp-003.yaml configs/exp-004.yaml
```

Pass: the diff shows exactly one semantic change (one hyperparameter, one architectural flag). Fail: multiple unrelated fields changed at once — a metric delta cannot be attributed to any single cause.

**SMELL — a config diff that changes three things at once:**

```diff
- learning_rate: 0.001
- batch_size: 32
- optimizer: adam
+ learning_rate: 0.0005
+ batch_size: 64
+ optimizer: sgd
```

Whichever metric moves, there is no way to say which of the three changes caused it.

**CLEAN — a config diff that changes exactly one thing:**

```diff
- learning_rate: 0.001
+ learning_rate: 0.0005
```

**4. Seed everything; report variance over ≥3 seeds for any claim.**

```bash
matches="$(find src/<pkg>/training configs -type f \( -name "*.py" -o -name "*.yaml" \) -exec grep -nE "seed" {} + 2>/dev/null)"
[ -z "$matches" ] && echo "FAIL: no seed set — run is not reproducible" || echo "$matches"
```

Pass: a seed value is set and recorded in the config. Fail: no seed anywhere — the run cannot be reproduced even with the exact same code and data. Use `find` over a shell glob for the two path patterns — a glob that matches zero files (an empty `configs/` before the first experiment is committed) aborts the whole line before grep runs in some shells, producing a false FAIL even when a seed is already set in `src/`. Any claim of improvement is reported as mean ± spread across at least 3 seeds; a single run's number is an anecdote, not a result.

Grey zone — multi-worker data loading needs each worker's seed derived from the base seed (for example `base_seed + worker_id`), not the same base seed copied verbatim to every worker; copying it verbatim makes every worker draw an identical augmentation/shuffle stream instead of an independent one, which quietly reduces the effective diversity of a "shuffled" epoch.

GPU training rarely reproduces bitwise-identical results across runs even with every seed fixed (non-deterministic cuDNN/cuBLAS kernels are the usual cause); chasing bitwise identity is not the goal — reporting mean ± spread over ≥3 seeds is. Bitwise-exact reproduction is available (`torch.use_deterministic_algorithms(True)` or equivalent) when a specific debugging need requires it, at a real throughput cost.

**5. Checkpointing and resume are tested before a long run launches.** Before a run expected to take longer than the environment's typical uninterrupted window, deliberately kill it at a checkpoint boundary and resume it — confirm loss and metrics continue smoothly rather than restarting from scratch or diverging. Skipping this turns the first real preemption into a fully lost run.

```bash
timeout 60 python scripts/train.py --config configs/exp-004.yaml --out experiments/exp-004/
python scripts/train.py --config configs/exp-004.yaml --out experiments/exp-004/ --resume-from experiments/exp-004/latest.ckpt
```

Pass: the second invocation's loss picks up near where the first left off, not from a fresh initialization. Fail: the resumed run's loss jumps back to its initial value, or the resume flag silently does nothing — either means a real preemption in production would lose all progress.

**6. Eval discipline: a fixed eval set, never tuned on the test split, and a metric that matches the actual product goal.** The test split is read exactly once, at the very end, to report the final number. Pick the metric from what the product actually needs — optimizing accuracy on a severely imbalanced classification task while the product cares about rare-class recall reports a number that looks good and means little; see `references/vision.md`'s class-imbalance playbook for the vision-specific version of this same problem.

```bash
grep -rnE "test" src/<pkg>/training/*.py | grep -viE "eval\.py|final_report|report_metrics"
```

Grey zone — approximate: this flags files referencing "test" outside the expected eval/report modules; confirm by hand whether test data actually enters a hyperparameter search loop (grid search, early-stopping-on-test, manual "peek and adjust") rather than being read only for the final reported number. Early stopping driven by the validation split is standard practice and not a leak; early stopping (or any other hyperparameter decision) driven by the test split is exactly the leak this rule forbids.

### Experiment tracking table

Log all of the following for every run that produces a number anyone will cite:

| Log | Why it matters |
|---|---|
| Config hash / config file path | Identifies the exact hyperparameters used |
| Git SHA | Identifies the exact code that ran |
| Data manifest hash (see `references/datasets.md`) | Identifies the exact data version used |
| Metrics (train/val/test, per epoch or step) | The outcome being claimed |
| Artifacts (checkpoints, plots, confusion matrices) | Makes the result inspectable after the fact, not just a number in a table |

A minimal per-run log entry (JSON, one line per run, appended to an `experiments/log.jsonl`) covers the table above without inventing new infrastructure:

```json
{"run_id": "exp-004", "config": "configs/exp-004.yaml", "git_sha": "a1b2c3d",
 "data_manifest": "9f8e7d6c", "seed": 3, "val_metric": 0.842,
 "checkpoint": "experiments/exp-004/latest.ckpt"}
```

### Grey zone — when to relax the ladder

A throwaway exploratory run (checking whether a feature is even worth pursuing, before any result will be reported or compared) does not need the full ladder — step 1 (the smoke test) still applies, because a broken pipeline wastes time regardless of intent, but steps 2–4 (baseline, one-variable diffing, multi-seed variance) apply once the run's result is going into a report, a comparison table, or a decision. Judge by audience: a number nobody but the author will ever see again can skip the full ladder; a number that will be compared against anything else cannot.

### Uncommitted-changes-at-launch guard

```bash
git status --porcelain | grep -q . && echo "FAIL: uncommitted changes at launch — this run's git SHA won't describe the code that ran"
```

Pass: no output — the working tree is clean, so the recorded git SHA fully describes the code. Fail: uncommitted changes exist — put this exact check as a pre-flight assertion inside the training entrypoint itself, not just as a manual habit before the command; a run that "worked" with uncommitted changes cannot be reproduced later even when it succeeded.

## Hand-offs

- Split-before-fitting and leakage prevention that this ladder assumes is already true of the data (steps 2 and 6 above depend on it) → `references/datasets.md`.
- Vision-specific additions to this ladder (input pipeline, augmentation, error analysis) → `references/vision.md`.
- Serving a trained checkpoint behind an API → the `backend` skill.
- Per-file Python discipline for the training code itself → the `programming` skill.
