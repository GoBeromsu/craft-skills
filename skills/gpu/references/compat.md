# CUDA Compatibility Chain & Install Selection

How to choose every CUDA-coupled package version from probed facts, and how to run a
source build without breaking the chain or the host.

## Table of Contents

1. [The chain](#1-the-chain)
2. [Per-architecture minimums](#2-per-architecture-minimums)
3. [Selection procedure](#3-selection-procedure)
4. [Source builds](#4-source-builds)
5. [Attention backends](#5-attention-backends)
6. [Allocator and device-map settings](#6-allocator-and-device-map-settings)
7. [The container escape hatch](#7-the-container-escape-hatch)

---

## 1. The chain

Four links, checked in order; a break anywhere surfaces as "no kernel image is available",
`torch.cuda.is_available() == False`, or a build failure:

```
GPU compute capability (sm_XX)
  ∈ torch's compiled arch list        # torch.cuda.get_arch_list()
torch's CUDA runtime (torch.version.cuda)
  ≤ driver's CUDA ceiling             # nvidia-smi header "CUDA Version"
local nvcc toolkit version
  == torch's CUDA runtime             # only when building any extension from source
```

The prebuilt-wheel case needs only the first two links — a torch cuXXX wheel bundles its
own runtime, so no local toolkit is required to *run*. The moment anything is compiled
(flash-attn, llama.cpp, a custom op), the third link becomes mandatory: a torch built for
one CUDA version and an `nvcc` from another blocks the build or produces broken kernels.

A new GPU generation breaks the first link silently: the wheel installs fine, imports
fine, and fails only at kernel launch. That is why the probe precedes the install choice.

## 2. Per-architecture minimums

| Architecture | sm | Minimum stack |
|---|---|---|
| Blackwell (RTX 50xx, RTX PRO 6000) | sm_120 | CUDA ≥ 12.8 (torch wheel cu128+); driver ≥ 570 with the **open kernel module** — the proprietary module does not support Blackwell |
| Hopper (H100) | sm_90 | CUDA ≥ 11.8; source builds need `sm_90` in the arch flags |
| Ampere (A100, RTX 30xx) | sm_80/86 | CUDA ≥ 11.0 |

The pattern generalizes: each new architecture has a minimum CUDA version, and stable
wheels lag it. When the probe shows a compute capability newer than the newest wheel's
arch list, the answer is the matching cuXXX wheel index (or nightly) — not a downgrade,
not a driver reinstall.

## 3. Selection procedure

1. Probe (SKILL.md block): compute capability, driver ceiling, existing torch state.
2. **Read the support surfaces before touching pip.** In order: the official install
   selector / release-notes compatibility matrix (new CUDA versions and new
   architectures ship as *experimental* before *stable* — know which tier you are
   adopting); the package README's supported-architecture list, which is gated per
   major version; and the issue tracker searched for this GPU's sm. A build system
   accepting an arch flag is not support — default arch lists routinely include
   architectures the kernels are not yet validated on, and the failure surfaces later
   as a segfaulting compile or a broken runtime, never as an install error.
3. Pick the torch wheel: newest build whose CUDA runtime ≤ driver ceiling **and** whose
   arch list contains the GPU's sm. Verify after install:
   ```bash
   python3 -c "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_arch_list(), torch.cuda.get_device_capability())"
   ```
4. Smoke-test before installing anything on top:
   ```bash
   python3 -c "import torch; x=torch.randn(1024,1024,device='cuda'); torch.cuda.synchronize(); print('cuda-ok', (x@x).sum().item())"
   ```
5. Only then layer dependents (flash-attn, bitsandbytes, llama.cpp) — for each, confirm
   a prebuilt wheel exists for this **exact** combination before any source build is
   considered. Wheels are keyed on every axis at once — package version × CUDA × torch
   version × C++ ABI × python × platform — and a miss on any one axis silently drops
   the install into a source build. A missing wheel for a new architecture is a signal
   to re-read step 2, not to brute-force a compile.
6. Record `python -m torch.utils.collect_env` with the run's records — the canonical
   environment fingerprint that upstream maintainers require in bug reports, and the
   answer to every later "what changed" question.

## 4. Source builds

A source build is a launch — on a shared host it also passes the shared-host gate
(`references/shared-hosts.md`).

- **RAM cap first.** Each parallel `nvcc` job on a heavy kernel library costs several GB
  of host RAM (flash-attn's own build system budgets ~5 GB per compile thread).
  `MAX_JOBS = free_RAM_GB / 6`, rounded down, minimum 1. An uncapped build on a 32 GB
  host freezes it — SSH and all — in under two minutes.
- **Toolkit match.** `nvcc --version` must equal `torch.version.cuda` before starting; fix
  the mismatch by aligning torch to the toolkit (or vice versa), never by hoping.
- **Arch flags explicit.** Target the probed sm directly — e.g. `FLASH_ATTN_CUDA_ARCHS=120`
  for flash-attn, `CMAKE_CUDA_ARCHITECTURES=120` for llama.cpp — so the build neither
  misses the GPU nor wastes hours compiling every architecture.
- **Shape of a safe build command:**
  ```bash
  nice -n 10 env MAX_JOBS=2 FLASH_ATTN_CUDA_ARCHS=<sm> \
    pip install --no-build-isolation flash-attn
  ```
  (`--no-build-isolation` so the build sees the real torch, not an isolated stale one.)

## 5. Attention backends

- flash-attn releases trail new architectures, and its generations are themselves
  architecture-gated (one generation can be Hopper-only while another covers
  Ampere/Ada/Hopper) — a new architecture typically reaches torch's built-in SDPA one
  or more releases before it reaches flash-attn, so check the README's support list and
  the issue tracker for this sm (§3 step 2) before planning around the flash path. On an
  unsupported sm the failure is a model-load error, not a slow path. Gate it:
  ```python
  try:
      import flash_attn  # noqa: F401
      attn = "flash_attention_2"
  except ImportError:
      attn = "sdpa"
  model = AutoModelForCausalLM.from_pretrained(name, attn_implementation=attn, ...)
  ```
  SDPA is the universal fallback — slower, but correct on every architecture torch
  supports; a measured SDPA number beats an unmeasured flash-attn promise.
- Any speedup claim for the flash path is unmeasured until benchmarked on this GPU —
  plan capacity from the measured fallback, treat the flash build as an upside.

## 6. Allocator and device-map settings

- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` — reclaims multi-GB fragmentation on
  long runs with large, variable-length batches; free to enable, measurable win.
- Pin the device map (`device_map={"": 0}` or explicit) and assert after load that no
  module landed on CPU. `device_map="auto"` under VRAM pressure spills to CPU silently:
  the run "works" while being an order of magnitude slower and its measured VRAM peak
  becomes a lie.

## 7. The container escape hatch

The default is wheel selection on the host (§3). Switch to the GPU vendor's monthly ML
container when the machine is a brand-new architecture, or when the chain has fought
back twice — wheel misses, ABI mismatches, a failed source build. The container ships a
pre-matched, pinned CUDA/framework/kernel-library stack, including a pip constraints
file that stops later installs from silently replacing the matched versions, and
collapses the whole compatibility chain into a single image tag. Record that tag with
the run like any other version pin; upgrading the container is a deliberate change, not
a side effect.
