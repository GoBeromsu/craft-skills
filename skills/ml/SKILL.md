---
name: ml
description: Applies ML/DL research engineering discipline — reproducible project layout, leakage-safe dataset construction, and a training-discipline ladder — to classical ML, deep learning, fine-tuning, and vision work. Use when scaffolding a new ML project, asked to "build a dataset" or "데이터셋 구축", running or reviewing a "train a model" experiment, or building a "vision model" pipeline (augmentation, detection, segmentation). Not for per-file Python discipline (typing, TDD loop) — use `programming` — not for building or changing LLM-agent behavior (prompts, tools, agent evals) — use `agents` — and not for GPU/CUDA environment setup or shared-host job launch — use `gpu`.
metadata:
  version: 2.2.0
---

# ml

Run ML/DL research and engineering work under one discipline: reproducibility first, evaluation honesty second, novelty third. A result nobody can rerun is not a result; a number bought by peeking at the test set is not a number; a fancier architecture only counts once a boring baseline is on the board. This skill is an index — shared rules live here, the per-topic iron list lives in `references/`; load the matching reference before touching a project layout, a dataset, or a training run.

## Task gate — run first, every time

Identify the task type before writing dataset, training, or vision code. Rows stack — load every reference whose row matches, not only the first one that fits:

| Task | Read | Notes |
|---|---|---|
| New project or explicitly scoped package/layout migration | `references/project-layout.md` | Use its `uv`/`pyproject.toml`/`src/` recipe as a greenfield default; preserve an established project's lockfile, environment, and layout during feature work. |
| Dataset construction, ingestion, splitting, labeling, or versioning | `references/datasets.md` | Stacks with `training.md` and/or `vision.md` whenever the dataset also feeds a training run or is image/video data. |
| A training run for any model class, including standalone LLM fine-tuning (SFT, LoRA) | `references/training.md` | |
| A vision task (image/video pipeline, augmentation, detection/segmentation) | `references/vision.md` | Load in addition to `training.md` — vision rules layer on top of the general training ladder, not replace it. |
| A run that will execute on a GPU host — CUDA/build selection, VRAM budgeting, shared-machine or HPC launch | Load the `gpu` skill first | `gpu` proves the environment and gates the launch; the references here still own the methodology once the environment is proven. |
| Building or changing agent behavior — prompts, tools, a tool-use loop, agent evals | Stop here | Load the `agents` skill instead; it owns the eval-first law for that work. |

Example: labeling and splitting an image dataset that will then be trained on matches three rows at once — load `datasets.md` + `training.md` + `vision.md` together, not `vision.md` alone.

## Core rules

- **Reproducibility receipt.** Every run that produces a reported number is reproducible from a git SHA, a config file, and a data manifest hash — missing any one means the number should not be cited. `references/training.md` has the full experiment-tracking contract.
- **Split before you fit anything.** Train/validation/test separate before any statistic is computed from the data — scaling, imputation, vocabulary, augmentation parameters. `references/datasets.md` gives the three leakage classes and their detection commands.
- **A baseline exists before a novel approach is judged.** "Better than the majority-class/linear/frozen-pretrained baseline," not "better than nothing." `references/training.md` covers the discipline ladder in full.
- **The test set is touched once** — reported at the end, never inside a tuning loop.

## Requirements

- Python: for a greenfield project, `uv` is a default for dependency locking and running; `pandas`/`polars`, `pandera` (or an equivalent schema checker), and `scikit-learn`/`torch`/`jax` are examples chosen to fit the task. In an established project, use its existing locked environment and installed tooling.
- `git`, `grep`, `find`, `awk`, `sha256sum` (`shasum -a 256` on macOS) for the detection commands in each reference.
- A config format the team already uses for one-run-one-config (examples assume YAML).

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "It's just a quick experiment script, skip the project layout." | A throwaway exploration still needs a smoke test and must respect the incumbent environment and layout; the full baseline, comparison, and variance ladder applies when its result will be reported or used for a decision. |
| "I already know the data is clean, skip split-before-fit." | Leakage is invisible in code, visible only in an eval number that quietly stops meaning anything. |
| "The new architecture is obviously better, no baseline needed." | "Obviously better" without a baseline number is an opinion, not a result. |
| "I peeked at the test metric once, that's not really tuning on it." | One peek biases every decision made afterward, even unconsciously. The test set is touched once, full stop. |
| "This is mostly a fine-tuning job, so `ml` covers it" (even though it calls tools). | If the feature calls tools, reasons over retrieved context, or drives multi-step LLM behavior, route to `agents` regardless of what else it touches. |

## Red flags

- A greenfield project with no locked environment or importable training code, or an unrelated feature that rewrites an established project's packaging.
- A preprocessing/scaling/vocabulary step that runs before the split, or on the concatenation of all three.
- A "novel" result reported with no baseline number in the same table.
- A training run launched with uncommitted changes, so its git SHA doesn't describe the code that ran.
- A claim of improvement from a single seed with no variance reported.
- An augmentation transform present in the validation or eval data loader.

## Boundaries

Not for wrapping a trained model behind a serving API — load `backend` — or for suite-level test-architecture decisions — load `testing`. GPU/CUDA environment, compatibility, and shared-host launch preflight are `gpu`'s domain — a GPU training run loads `gpu` first, then this skill. The `agents` boundary from the task gate is the one worth double-checking on every task: "the model calls a tool" or "the pipeline reasons over retrieved text" is agent work even when it also touches a model file.

## Verification

- [ ] The task gate identified the task type and the matching reference was read before writing code — or the task was recognized as agent work and handed to `agents` instead.
- [ ] The established project's locked environment and layout were preserved, or greenfield code has a locked environment and is importable.
- [ ] Every fitted statistic (scaler, vocabulary, augmentation parameter) is fit on the train split only.
- [ ] A baseline number exists in the same report as any novel-approach number.
- [ ] Each reported result has a reproducibility receipt: the code revision, configuration, data manifest, and recorded outcome identify what ran.
- [ ] The test set was touched exactly once, to report the final number.
- [ ] Claims of improvement report variance over ≥3 seeds, not a single run.
