# GPU Failure Triage

Map the symptom to its structural cause before changing anything; every branch here has
been mis-fixed in the wild by reinstalling at random or rebooting away the evidence.

## Table of Contents

1. [Triage table](#1-triage-table)
2. [OOM](#2-oom)
3. [Xid faults and wedged GPUs](#3-xid-faults-and-wedged-gpus)
4. [Fail-closed deployment rules](#4-fail-closed-deployment-rules)

---

## 1. Triage table

| Symptom | Structural cause | Fix |
|---|---|---|
| `no kernel image is available for execution on the device` | GPU's sm missing from torch's compiled arch list (new architecture, old wheel) | Install the build whose arch list contains the sm (`references/compat.md` §3); never a driver downgrade |
| `torch.cuda.is_available()` is False, `nvidia-smi` works | CPU-only wheel, or torch CUDA runtime > driver ceiling | Compare `torch.version.cuda` to the driver's CUDA ceiling; reinstall the matching wheel |
| `torch.cuda.is_available()` is False, `nvidia-smi` also broken | Driver/kernel-module problem, not a Python problem | Fix the driver layer first (correct module variant for the architecture); no pip command can help |
| Extension build fails or dies mid-compile | `nvcc` ≠ torch CUDA version, or host RAM exhausted by parallel jobs | Align toolkit and torch; cap `MAX_JOBS` (`references/compat.md` §4) |
| Model load fails naming an attention backend | Backend hard-coded for an architecture that doesn't support it | Explicit `attn_implementation="sdpa"`; add the guard (`references/compat.md` §5) |
| Run is "working" but ~10× slower than expected | Silent CPU spill via `device_map="auto"`, or a power/thermal cap | Assert the device map; read `clocks_throttle_reasons.active` — a power cap is a board spec, not a bug |
| `CUDA error: unspecified launch failure`, Xid messages in syslog | Fault cascade — see §3 | Stop the workload; passive triage first |

## 2. OOM

`torch.cuda.OutOfMemoryError` is a budgeting failure; fix the budget, not the symptom
order:

1. Read the error's own arithmetic (tried / free / reserved-but-unallocated). A large
   reserved-vs-allocated gap is fragmentation →
   `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` first, it is free.
2. Re-measure the real peak at micro scale (`torch.cuda.max_memory_allocated()` **and**
   `nvidia-smi`) — the two diverge, and the SMI number is what the card actually runs
   out of.
3. Then trade in order of cost: gradient checkpointing → batch/sequence reduction →
   precision/quantization → a bigger card. Do not "fix" OOM with `device_map="auto"`
   spill — that converts an honest failure into a silent 10× slowdown.
4. Host-RAM OOM (the process is killed, or the whole host freezes with SSH dead) is a
   different failure: dataloader workers or a parallel build ate system RAM. Budget per
   `references/shared-hosts.md` §4.

## 3. Xid faults and wedged GPUs

Xid errors in `dmesg`/journal are the GPU's own fault log. The **first** Xid is the
evidence; everything after is cascade (context-switch timeouts, GSP/firmware recovery
failures, finally "GPU Reset Required" and a hung `nvidia-smi`).

- **Stop feeding it.** Once Xids appear, further CUDA work — including diagnostic
  workloads — creates new faults and buries the first one. Triage passively from logs.
- **Capture before changing state.** Prior-boot journal, the full Xid sequence with
  timestamps, driver/kernel versions, and what workload ran. A reboot or driver
  downgrade that "makes it work" without captured evidence proves nothing about the
  cause and guarantees a repeat.
- **Watch the disk.** A fault cascade can spam syslog at hundreds-of-GB scale and fill
  the root filesystem — check `df -h` during any incident, rotate or cap logs.
- **Keep hypotheses separate.** A first-fault "illegal instruction" can be a software
  stack defect *or* hardware/power instability executing a valid command wrongly; a
  passing smoke test after a driver change does not decide between them. Say "not
  isolated" rather than declaring the first fix that survives a smoke test the root
  cause.
- **Read the memory counters.** `nvidia-smi -q` ECC sections (volatile vs aggregate,
  correctable vs uncorrectable), retired pages, and row-remap status separate a
  software-triggered fault from failing hardware: a climbing uncorrectable count on one
  GPU is an RMA conversation, not a software bug. After any incident, the health gate
  (`dcgmi diag`, `references/shared-hosts.md` §7) belongs in the checklist before the
  node takes real work again.

## 4. Fail-closed deployment rules

For any unattended service that touches CUDA — distilled from a real cascade whose blast
radius was widened by every one of these being missing:

- One guarded entrypoint: the CUDA/driver startup check must run on every launch path;
  an alternative entrypoint that skips the guard is a defect.
- Fatal CUDA errors exit the process. The supervisor restarts with a fresh context; the
  code never catches a device assert / launch failure as a generic exception and
  continues on a corrupted context.
- An out-of-process watchdog reads the GPU's fault stream (Xid via dmesg/journal or DCGM)
  and can stop admitting work — in-process code cannot observe its own GPU dying.
- Preserve first-failure evidence: input identifiers and stage boundaries logged (with
  explicit `torch.cuda.synchronize()` markers where async hides the faulting op), so the
  failing input is recoverable after a crash.
- Retention outlives triage: if logs rotate away before anyone reads them, the incident
  is unlearnable.
