# Apple Silicon (MPS)

The two laws hold on an M-series Mac — probe before install, budget before launch — but
the chain is different: no CUDA, no separate VRAM, one unified memory pool shared with
the OS and every open app.

## The probe

```bash
sysctl -n machdep.cpu.brand_string hw.memsize
system_profiler SPDisplaysDataType | grep -E "Chipset|Cores"
python3 -c "import torch; print(torch.__version__, torch.backends.mps.is_available(), torch.backends.mps.is_built())"
```

## The chain, translated

- The device is `"mps"`, backed by Metal. None of the CUDA chain applies: no
  `nvidia-smi`, no `nvcc`, no cuXXX wheel variants — the plain macOS arm64 torch wheel
  ships the MPS backend.
- `is_built()` False → wrong wheel (x86 python under Rosetta is the usual cause);
  `is_available()` False while `is_built()` is True → the macOS version is too old for
  the backend.
- CUDA-only packages have no wheel here at all: flash-attn, bitsandbytes' CUDA kernels,
  TensorRT. Attention is SDPA; quantization needs an MPS/Metal-native path (or MLX,
  Apple's own framework). A requirements file copied from a CUDA host must be
  re-derived, not force-installed — the missing-wheel signal means "does not exist on
  this platform", not "build it from source".

## Unified memory changes the budget law

- There is no VRAM number to size against: the model, the OS, and every open app share
  one pool. Budget against actually-free memory, and expect an over-ask to degrade the
  whole machine through swap pressure rather than fail with a clean OOM.
- torch caps MPS allocations at a fraction of total memory
  (`PYTORCH_MPS_HIGH_WATERMARK_RATIO`; `0.0` removes the cap). Raising it trades a
  clean allocation error for machine-wide swap death — change it consciously, if at all.
- The co-tenants are your own applications: close the heavy ones before a micro-bench,
  or the measured numbers lie.

## Operator coverage

- An op not implemented for MPS raises by default; `PYTORCH_ENABLE_MPS_FALLBACK=1`
  makes it fall back to CPU **silently, per-op** — the run "works" with hidden
  device-to-CPU round-trips, the MPS analog of `device_map="auto"` spill. Enable it
  consciously and re-measure; never leave it as a permanent default.
- float64 is unsupported on MPS — code that needs it runs on CPU or not at all.

## What transfers unchanged

Smoke-before-scale, micro-bench-then-extrapolate, and warmup-plus-synchronize timing
all apply — the synchronize call is `torch.mps.synchronize()`. Treat a Mac result as a
correctness and prototyping result: a performance claim about a CUDA deployment target
is only measurable on the CUDA target.
