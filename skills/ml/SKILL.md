---
name: ml
description: '"build a dataset", "데이터셋 구축", "train a model", "학습 돌려줘", "vision model" — ML/DL research engineering: reproducible project layout, dataset construction and leakage prevention, training discipline, and vision-specific practice, routed through a PHASE 0 task gate. LLM-agent building routes to the `agents` skill instead.'
version: 1.0.0
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
compatibility: claude-code, codex
---

# ml

Run ML/DL work under one discipline: **reproducibility first, evaluation honesty second, novelty third.** A result nobody can rerun is not a result; a number bought by peeking at the test set is not a number; a fancier architecture only counts once a boring baseline is on the board.

## Overview

This skill is an index. Shared rules live here; the per-topic iron list lives in `references/`. Load the matching reference before touching a project layout, a dataset, or a training run. This skill covers classical ML and deep learning research/engineering work — it does not cover building or operating an LLM-powered agent or feature; that discipline belongs to the `agents` skill and is out of scope here by design. Standalone LLM fine-tuning — SFT, LoRA, or evaluating a fine-tuned model against your own data — is training work and belongs here under the training-discipline ladder; only building or changing agent behavior (prompts, tools, agent evals) routes to `agents`.

## When to Use

- Scaffolding a new ML/DL project, or restructuring one that has no package layout, no locked dependencies, or scattered data/notebook conventions.
- Building, splitting, versioning, or labeling a dataset.
- Running or reviewing a training experiment for any model class (classical ML, deep learning, fine-tuning).
- A vision task: image/video input pipelines, augmentation, classification, detection, or segmentation.

**Not for:** building or changing an LLM agent, prompt, tool-use loop, or other LLM-powered feature — load the `agents` skill; that work has its own eval-first law and does not belong here. Not for wrapping a trained model behind a serving API — load `backend`. Not for per-file Python discipline (typing, LOC ceiling, TDD loop) — load `programming`. Not for software test-suite architecture — load `testing`.

## PHASE 0 — task gate (run first, every time)

Do not write dataset, training, or vision code before this gate.

1. Identify the task type from the request. Rows stack — load every reference whose row matches the task, not only the first one that fits:

   | Task | Read | Notes |
   |---|---|---|
   | New project, or an existing one missing `pyproject.toml` / `src/` / a lockfile | `references/project-layout.md` | Always load this one, even alongside another reference below — it is the absolute packaging/layout baseline. |
   | Dataset construction, ingestion, splitting, labeling, or versioning | `references/datasets.md` | Stacks with `training.md` and/or `vision.md` below whenever the dataset also feeds a training run or is image/video data. |
   | A training run for any model class | `references/training.md` | |
   | A vision task (image/video pipeline, augmentation, detection/segmentation) | `references/vision.md` | Load in addition to `training.md` — vision rules layer on top of the general training ladder, they do not replace it. |
   | Building or changing an LLM agent, prompt, tool-use loop, or other LLM-powered feature | **STOP.** Do not proceed in this skill. | Load the `agents` skill instead — eval-first law, prompt/tool design, and context/tracing discipline live there, not here. |

   Example: labeling and splitting an image dataset that will then be trained on matches three rows at once — load `references/datasets.md` + `references/training.md` + `references/vision.md` together, not `vision.md` alone.

2. Confirm the task is not agent work before writing a single line — "the model calls a tool" or "the pipeline reasons over retrieved text" is agent work even when it also touches a model file.
3. Apply the core rules below plus the per-reference iron list.

## Core rules (apply regardless of which reference you load)

- **Reproducibility receipt.** Every run that produces a reported number is reproducible from three things: a git SHA, a config file, and a data manifest hash. Missing any one of them means the number cannot be regenerated and should not be cited. `references/training.md` gives the full experiment-tracking contract.
- **Split before you fit anything.** Train/validation/test are separated before any statistic is computed from the data — scaling, imputation, vocabulary, augmentation parameters, everything. `references/datasets.md` gives the three leakage classes and their detection commands.
- **A baseline exists before a novel approach is judged.** "Better than nothing" is not a comparison; "better than the majority-class/linear/frozen-pretrained baseline" is. `references/training.md` covers the discipline ladder in full.
- **The test set is touched once.** Reported at the end, never inside a tuning loop. Tuning on the test set converts an evaluation into a leaderboard trick.

## Requirements

- Python: `uv` (dependency locking and running), `pandas`/`polars` for tabular work, `pandera` or an equivalent schema-validation library for ingest checks, a training framework matching the task (`scikit-learn`, `torch`, `jax`).
- `git`, `grep`, `find`, `awk`, `sha256sum` (or `shasum -a 256` on macOS) for the detection commands in every reference file.
- A config format the team already uses for one-run-one-config (YAML is the default assumed in examples).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's just a quick experiment script, skip the project layout." | The quick script is the one that gets copy-pasted into the next three experiments. `references/project-layout.md`'s baseline costs nothing with `uv`. |
| "I already know the data is clean, I'll skip the split-before-fit rule." | Leakage is invisible in the code and visible only in an eval number that quietly stops meaning anything. Split first, every time. |
| "The new architecture is obviously better, no need for a baseline number." | "Obviously better" without a baseline number is an opinion, not a result. Put the baseline in the same table. |
| "I peeked at the test metric once, that's not really tuning on it." | One peek is enough to bias every decision made afterward, even unconsciously. The test set is touched once, at the end, full stop. |
| "This is basically an agent feature but it's mostly a fine-tuning job, so ml covers it." | If the feature calls tools, reasons over retrieved context, or drives multi-step LLM behavior, it is agent work regardless of what else it touches — route to `agents`. |
| "Augmentation on the val set can't hurt, it's just more data." | It changes what the eval loader shows the model at eval time, corrupting the very number meant to be trustworthy. `references/vision.md` ships the detection command. |

## Red Flags

- A project with no `pyproject.toml`, no `src/` layout, or no lockfile that is already past its first experiment.
- A preprocessing/scaling/vocabulary step that runs before the train/val/test split, or runs on the concatenation of all three.
- A "novel" result reported with no baseline number in the same table.
- A training run launched with uncommitted changes, so its git SHA does not describe the code that actually ran.
- A claim of improvement from a single seed with no variance reported.
- An augmentation transform present in the validation or eval data loader.
- Agent/tool/prompt code being written or reviewed inside an `ml`-flagged task without a hand-off to `agents`.

## Verification

- [ ] PHASE 0 identified the task type and the matching reference was read before writing code — or the task was recognized as agent work and handed to `agents` instead.
- [ ] The project has `pyproject.toml`, a `src/` layout, and a locked dependency file, or a plan to add them is stated.
- [ ] Every fitted statistic (scaler, vocabulary, augmentation parameter) is fit on the train split only.
- [ ] A baseline number exists in the same report as any novel-approach number.
- [ ] The run that produced the reported number has a git SHA, a config file, and a data manifest hash all pointing at exactly what ran.
- [ ] The test set was touched exactly once, to report the final number.
- [ ] Claims of improvement report variance over ≥3 seeds, not a single run.
