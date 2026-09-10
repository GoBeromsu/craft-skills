# ML Training Discipline

Match the evidence to the modeling claim before making a run faster, larger, or more novel. Preserve exploratory results with their limitations instead of manufacturing certainty or blocking them on arbitrary counts.

## Table of Contents

- [Hard rules](#hard-rules) — smoke tests, baselines, attribution, uncertainty, recovery, evaluation, and reproducibility
- [Hand-offs](#hand-offs)

## Hard rules

### The discipline ladder

**1. Smoke-test a small, understood input before a full run.** Verify data/label alignment, finite loss, intended trainable parameters, gradient flow, and meaningful updates. When the objective and model can memorize the selected examples, overfit a tiny batch as a diagnostic; define the expected target before interpreting the curve.

A nonzero loss is not by itself proof of a broken pipeline. Contradictory labels for identical inputs, regularization, frozen capacity, stochastic objectives, and irreducible uncertainty can impose a valid nonzero floor. For example, a deterministic binary classifier given the same input with both labels has minimum mean cross-entropy `log(2)`, not zero. Check the objective's feasible target before demanding memorization.

| Symptom | Investigation |
|---|---|
| Loss becomes `NaN` or infinite | Check numerical stability, input values, learning rate, and unsafe operations |
| A representable tiny example does not improve | Check labels, objective, trainable parameters, gradients, and optimizer updates |
| A constrained objective plateaus above zero | Compare with its expected floor and constraints; do not label it broken from the loss alone |
| Full-run train loss improves while validation does not | Investigate generalization, leakage, distribution shift, and overfitting rather than rerunning the memorization check blindly |

**2. Establish a baseline before claiming an improvement.** Choose the cheapest credible baseline for the task: a majority/mean predictor, linear model, frozen pretrained model, or an already measured comparable system. Compare actual outcomes on the same evaluation boundary. A file named `baseline` proves neither a run nor its result. An exploratory run may remain exploratory; an unmeasured baseline means the improvement claim remains unverified.

**3. Match experimental design to attribution.** Change one factor at a time for a simple causal comparison. Planned factorial designs and multi-change candidates are valid, but record their full configuration and distinguish a combined-system comparison from evidence about an individual factor.

```bash
diff configs/exp-003.yaml configs/exp-004.yaml
```

Inspect the semantic changes rather than counting diff lines. A learning-rate, batch-size, and optimizer change can support a claim about the combined candidate against a matched baseline; without suitable controls or experimental design it cannot identify which change caused the outcome. Record the hypothesis and controls before selecting a favorable explanation.

**4. Record randomness and qualify uncertainty.** Record applicable framework, data-loader, sampling, and evaluator seeds plus relevant deterministic settings. Inspect their actual use: finding the word `seed` in a source file is not execution evidence. Use framework-supported independent worker streams rather than accidentally repeating identical augmentation/shuffle streams.

Choose repeats and uncertainty estimates for the task variability, decision stakes, and available budget. Report the actual sample count and method; do not impose a universal seed floor or claim statistical stability merely because a count was reached. A single stochastic run can be reported as preliminary, without invented variance or an unsupported robust-improvement claim. Repeating a deterministic calculation with different unused seed labels adds no evidence.

Seeds alone do not guarantee bitwise identity across hardware, library versions, or nondeterministic kernels. Record those limits. Enable a framework's documented deterministic mode when the debugging need justifies its performance cost, not as an assumed universal default.

**5. Test checkpoint recovery before committing to a long run.** For runs longer than the expected uninterrupted window, use a bounded short trial and the project's supported interruption/resume mechanism. Verify the recovered checkpoint identity, step, model/optimizer/scheduler state and applicable RNG/data-loader state. Check that training genuinely continues; a success exit or a similar-looking loss alone is insufficient.

Use the project's installed help and configuration for the actual invocation. Do not invent a resume flag or interrupt an unrelated live job to demonstrate recovery. Preserve a failed recovery as a launch blocker for the long run, not as a passing smoke test.

**6. Keep evaluation independent of tuning and aligned with the product goal.** Use validation data for model selection, early stopping, and other tuning. Reserve the test set for a frozen final comparison; do not use test feedback to select the next candidate while calling it untouched hold-out evidence. Replaying a frozen final evaluation for verification is not a new independent test set: disclose reuse and do not retune from its results.

Pick the metric from the actual task. Accuracy can conceal rare-class failure in an imbalanced classifier; use the relevant recall, precision, calibration, or other product measure. Inspect the data/control flow rather than treating a grep match for `test` as proof of leakage. See `references/vision.md` for vision-specific checks.

For preference or RL post-training, version the reward function, extraction/parser logic, and any reward model. Test known-good, malformed, and adversarial completions so extraction errors or reward exploits do not masquerade as task success. Evaluate the resulting candidate against a matched baseline with a held-out end-task metric; training reward, formatting compliance, or one loss direction alone does not prove quality. Reward counts, dispersion thresholds, and loss behavior depend on the task and trainer. Keep framework APIs and attention-backend selection with matching official documentation and the `gpu` environment checks.

### Experiment tracking table

Keep the following in the project's existing run receipt for a result that will be cited or compared; do not create a new tracking service merely to satisfy this table.

| Log | Why it matters |
|---|---|
| Configuration identity and preserved artifact | Identifies actual hyperparameters, not just a mutable filename |
| Git base/revision plus frozen current-content identity | Identifies the code that ran, including relevant dirty or untracked inputs |
| Data manifest hash (see `references/datasets.md`) | Identifies the data version and split |
| Metrics and their evaluation boundary | Identifies the measured outcome, split, and uncertainty limits |
| Artifacts and their identities | Preserves checkpoints, plots, predictions, and other inspectable evidence |
| Actual invocation and relevant environment | Distinguishes recorded execution from an intended command |

For reported generative-model evaluations, also preserve the model/checkpoint ID and revision, prompt/template revision, evaluation task or suite and version, few-shot/decoding/evaluator settings, and hardware. If a hosted model or evaluator revision is unavailable, record that limitation instead of inventing an immutable identifier. These details qualify a reported evaluation; they do not require model downloads or full evaluations for unrelated exploratory or documentation work.

Illustrative JSONL shape (one record per physical line; placeholders are not observed identities):

```json
{"run_id":"exp-004","config":"configs/exp-004.yaml","config_digest":"<recorded-digest>","git_sha":"<recorded-base-commit>","source_snapshot":"experiments/exp-004/source.tar","source_digest":"<recorded-digest>","data_manifest":"<recorded-digest>","seed":3,"val_metric":0.842,"uncertainty":"single exploratory run; variance not estimated","checkpoint":"experiments/exp-004/latest.ckpt","invocation":"<actual invocation>","environment":"<recorded environment identity>"}
```

For a reported generative evaluation, extend that record with the applicable fields rather than replacing its existing provenance:

```json
{"model_or_checkpoint_id":"<evaluated model>","model_revision":"<observed revision or unavailable>","prompt_template_revision":"<recorded revision>","evaluation_task_or_suite":"<task identifier>","evaluation_suite_version":"<recorded version>","few_shot":0,"decoding_settings":{"temperature":0},"evaluator_settings":"<recorded settings>","hardware":"<observed hardware or unavailable>"}
```

### Exploratory runs

A throwaway exploration still needs a credible smoke test and must respect the incumbent environment and launch authority. Apply baseline, attribution, uncertainty, and receipt requirements when using its result for a comparison or decision. Preserve limited observations as limited observations; never convert a missing measurement into a fabricated value or a universal failure of the experiment.

### Freeze source identity before launch

A Git SHA alone does not identify dirty or relevant untracked inputs. Preserve the exact code/configuration snapshot used by the run, record its digest and base commit, and verify that the launched inputs match it. Include all relevant committed, staged, unstaged, and untracked execution inputs; record dependency, data, and model identities separately. Do not include secrets in a shareable snapshot.

A clean checkout can use an immutable revision when it fully identifies the execution inputs. A dirty checkout is acceptable with a complete, preserved current-content snapshot; never force a commit, stash, branch switch, or discard as a substitute. If the inputs cannot be frozen or change after capture, stop the comparable/long-run launch until its identity is resolved. Exploratory output without this evidence remains explicitly non-reproducible, not a verified comparison.

## Hand-offs

- Dataset splitting, fitted-statistic leakage, and manifests → `references/datasets.md`.
- Vision-specific input pipelines, augmentation, and error analysis → `references/vision.md`.
- Serving a trained checkpoint behind an API → the `backend` skill.
- Per-file Python discipline → the `programming` skill.
- Framework/CUDA compatibility and shared-host launch safety → the `gpu` skill.
