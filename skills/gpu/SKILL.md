---
name: gpu
description: Applies GPU environment and resource discipline — probe the hardware before choosing any install, budget the host before launching any job — to CUDA/PyTorch setup, attention-backend builds, and GPU job launches. Use when setting up CUDA or PyTorch on a new GPU machine, asked to "install flash attention", debugging "torch.cuda.is_available() returns False", "CUDA out of memory", or "no kernel image is available", sizing VRAM, running a training/inference job on a shared GPU host or HPC, or working on Apple Silicon (MPS, M-series). Not for training methodology, datasets, or evaluation discipline — use `ml` — and not for serving a model behind an API — use `backend`.
metadata:
  version: 1.1.0
---

# gpu

Run GPU work under two laws. **Probe before install:** the CUDA stack is a strict compatibility chain, and every install chosen from memory of a previous GPU generation is a latent failure — a new architecture invalidates the wheel, the toolkit, and the attention backend at once. **Budget before launch:** a job or build launched without measuring the host's free resources can take the whole machine down, and on a shared host that outage lands on other people. Success criteria: no package version chosen before the hardware was probed, and no job or source build started before its resource footprint was checked against what the host actually has free.

## Task gate — run first, every time

Rows stack — load every reference whose row matches:

| Task | Read |
|---|---|
| Installing or upgrading anything CUDA-coupled — torch, flash-attn, llama.cpp, TensorRT, a driver | `references/compat.md` |
| Launching anything on a shared or remote GPU host — a training run, a benchmark, a source build | `references/shared-hosts.md` |
| A CUDA error, an OOM, a hung `nvidia-smi`, or any GPU misbehavior | `references/triage.md` |
| Work on an Apple Silicon Mac (MPS) — install, run, or port from a CUDA host | `references/apple-silicon.md` |
| Training methodology, dataset construction, evaluation discipline | Stop here — load the `ml` skill; this skill only proves the environment it runs on |

## The probe

Run before any install decision or job launch on a machine whose state is not already known from this session. Read-only — allocates nothing on the GPU:

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv
nvcc --version 2>/dev/null || cat /usr/local/cuda/version.json 2>/dev/null || echo "no local CUDA toolkit"
df -h "$HOME" /tmp; free -h; nproc
python3 -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.get_arch_list())" 2>/dev/null
```

Four facts come out: the GPU's compute capability, the driver's CUDA ceiling, the host's free RAM/disk/cores, and what the current torch build actually supports. Every decision below consumes these facts; none of them may be assumed. On Apple Silicon there is no `nvidia-smi` — run the MPS probe in `references/apple-silicon.md` instead; the same kinds of facts come out.

## Core rules

- **The compatibility chain is strict.** GPU compute capability ∈ torch's compiled arch list; torch's CUDA runtime ≤ the driver's CUDA ceiling; local `nvcc` matches torch's CUDA version for any source build. One link broken → "no kernel image", import failures, or a build that dies hours in. `references/compat.md` has the chain, per-architecture minimums, and the selection procedure.
- **Support is a matrix you read, not a flag you try.** Before installing on a new architecture: the official compatibility matrix (new-architecture support ships *experimental* before *stable*), the package's supported-architecture list, the wheel index for the exact version combination, and the issue tracker for this GPU's sm. A build system accepting an arch flag proves nothing — validation status is published, not probed. `references/compat.md` §3 sequences the checks.
- **A source build is a host-RAM job, not a GPU job.** Parallel `nvcc` compiles of a heavy kernel library consume host RAM at gigabytes per job; an uncapped build can freeze the whole machine, SSH included. Cap `MAX_JOBS` from free host RAM, run it under `nice`, and treat the build itself as a launch that needs the shared-host gate — `references/compat.md` §4 owns the cap formula and the safe build command.
- **Occupancy predicate before any GPU allocation on a shared host.** Sample utilization and memory several times and confirm no other compute process exists; only a "Free" verdict permits allocation. `references/shared-hosts.md` owns the predicate and thresholds.
- **Smoke before scale.** One CUDA matmul proves the stack; a short micro-bench measures real VRAM peak and step time; only then commit to the full run, with the full run's footprint extrapolated from measured numbers rather than guessed.
- **Fatal CUDA errors are fatal.** A CUDA launch failure or device assert corrupts the context — exit the process and start clean. Catching it as a generic per-item exception and continuing turns one fault into a cascade and destroys the evidence of the first failure.
- **Attention backends are architecture-gated.** Never hard-code `flash_attention_2`; guard it behind a support check with an explicit SDPA fallback, because on an unsupported architecture the failure is a model-load error, not a graceful degradation.

## Requirements

- `nvidia-smi` (driver installed) for every probe on an NVIDIA host; on Apple Silicon the probe uses `sysctl` and `torch.backends.mps` instead (`references/apple-silicon.md`). `python3` with the project's torch for stack checks.
- `nvcc` only when a source build is actually planned — its absence is a probe finding, not an error.

## Anti-patterns

- Installing torch/CUDA from memory of the previous GPU generation → probe compute capability and driver ceiling first; pick the build whose arch list contains this GPU.
- Launching a source build with default `MAX_JOBS` on a shared or small-RAM host → cap `MAX_JOBS` from free host RAM (`references/compat.md` §4), `nice` it, and warn co-tenants first.
- Catching a fatal CUDA error per-item and continuing the loop → exit the process, restart with a fresh context, preserve the failing input.
- Hard-coding `flash_attention_2` because the last machine supported it → gate on a support check with an SDPA fallback.
- `device_map="auto"` on a VRAM-tight host → silent CPU spill masks the real footprint; pin the device map and assert it after load.
- Running diagnostic CUDA workloads on a GPU already throwing Xid errors → passive triage from system logs first; a wedged GPU turns probes into new faults.
- Rebooting or downgrading a driver before capturing prior-boot logs → the evidence of the first fault is gone; capture, then change state.
- Treating "the build accepted my arch flag" as evidence of support → validation status lives in the release-notes matrix and the issue tracker; read them before installing (`references/compat.md` §3).
- Carrying CUDA instincts to Apple Silicon — expecting `nvidia-smi`, flash-attn, or a separate VRAM pool → the two laws hold but the chain differs; load `references/apple-silicon.md`.

## Boundaries

This skill proves the environment; it does not judge the experiment. Training discipline, dataset handling, and evaluation honesty belong to `ml` — a fine-tuning run loads both, `gpu` first. Per-file Python discipline is `programming`; serving a trained model is `backend`.

## Verification

- [ ] The probe ran before any install was chosen or any job launched, and its four facts appear in the decision (not assumed).
- [ ] Every CUDA-coupled package version was selected against the compatibility chain and the published support matrix, not copied from another machine.
- [ ] Any source build had an explicit `MAX_JOBS` derived from free host RAM.
- [ ] On a shared host: occupancy verdict recorded before allocation, and the full run's footprint extrapolated from a measured micro-bench.
- [ ] No code path catches a fatal CUDA error and continues; attention backend is guarded with a fallback.
