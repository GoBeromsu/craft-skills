# Shared GPU Hosts & HPC Launch Discipline

Launching on a machine other people depend on — a lab workstation, a login node, a
cluster. The failure this prevents is not a bad experiment; it is taking the host down
for everyone on it.

## Table of Contents

1. [Full preflight](#1-full-preflight)
2. [Occupancy predicate](#2-occupancy-predicate)
3. [Progressive scaling](#3-progressive-scaling)
4. [Footprint budgeting](#4-footprint-budgeting)
5. [Co-tenant etiquette](#5-co-tenant-etiquette)
6. [Cluster specifics](#6-cluster-specifics)

---

## 1. Full preflight

Extends the SKILL.md probe; still read-only until the occupancy verdict:

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv
nvcc --version 2>/dev/null || echo "no local toolkit"
df -h "$HOME" /tmp; free -h; nproc
python3 -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.get_arch_list())"
```

Record the outputs. Disk and host RAM matter as much as VRAM: model caches are tens of
GB, and source builds and dataloader workers consume host RAM, not GPU memory.

## 2. Occupancy predicate

Allocate nothing on the GPU until this returns a "Free" verdict:

```bash
for i in 1 2 3; do
  nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
  sleep 3
done
nvidia-smi --query-compute-apps=pid,used_memory,process_name --format=csv
```

"Free" = all three samples under the thresholds (defaults: util ≤ 25 %, memory ≤ 2 GiB)
**and** the compute-apps list is empty. Any other verdict → do not allocate; coordinate
with whoever owns the running process instead. Build the same predicate into the job
itself (a subprocess check before model load, aborting if occupied) so an unattended or
scheduled launch cannot land on top of someone else's run.

## 3. Progressive scaling

Never jump from zero to the full run:

1. **Smoke** (< 10 min, minimal resources): one CUDA matmul, then one model forward /
   one training step. Proves the stack and the data path.
2. **Micro-bench** (< 30 min): a handful of steps at real batch/sequence settings.
   Measure step time (median over ≥ 20 steady steps), VRAM peak (both
   `torch.cuda.max_memory_allocated()` and the `nvidia-smi` peak), and host RAM.
   Optionally log thermals to catch power/thermal caps:
   ```bash
   nvidia-smi --query-gpu=timestamp,temperature.gpu,power.draw,power.limit,clocks.sm,pstate,clocks_throttle_reasons.active --format=csv -l 2 > thermal.csv
   ```
3. **Full run**: requested resources and wall-clock projected from the micro-bench
   numbers (steps × measured step time, plus a checkpoint/conversion overhead margin),
   not from intuition. Checkpointing verified before the long run starts, so a mid-run
   failure costs a segment, not the run.

## 4. Footprint budgeting

Budget all four, not just VRAM:

- **VRAM** — measured at micro-bench, extrapolated with headroom; a worked anchor: a 14B
  model in bf16 with LoRA, 16k sequence, batch 1, gradient checkpointing peaks near
  70 GiB allocated / 85 GiB reserved — a 96 GB card fits it, a 48 GB card does not.
- **Host RAM** — dataloader workers × per-worker footprint + `pin_memory` staging + any
  build. Cap `num_workers` against `free -h`, not against CPU count.
- **Disk** — model cache + checkpoints + logs against `df -h`. Runaway logging can fill a
  root filesystem during a single incident; cap or rotate logs on long runs.
- **Wall-clock** — on a shared host, a run has a time budget agreed with co-tenants, and
  a ledger of actual GPU time spent keeps the agreement honest.

## 5. Co-tenant etiquette

- Announce before heavy use: what, when, expected duration, and how to reach you.
  Overnight windows are coordinated across timezones, not assumed.
- The occupancy predicate runs before *every* allocation, not once per day.
- Source builds count as heavy use — RAM-capped (`references/compat.md` §4), `nice`d,
  and announced, because their blast radius is the whole host, not the GPU.
- If your job takes the host down anyway: tell the co-tenants immediately what ran, what
  the blast radius is (data at risk or not), and what you changed so it cannot recur.

## 6. Cluster specifics

- Request resources from measured numbers: over-request buys queue time, under-request
  buys an OOM kill. Profile at micro scale, then request measured + margin.
- Interactive-session default memory is typically tiny (single-digit GB) — set `--mem`
  explicitly or the first real allocation dies.
- Home quotas break caches mid-run: point `HF_HOME` (or symlink the cache directory) at
  scratch storage before the first download.
- Post-mortem a finished or killed job against its request
  (`sacct -j <jobid> --format=JobID,MaxRSS,Elapsed,State`) and feed the numbers into the
  next request.
