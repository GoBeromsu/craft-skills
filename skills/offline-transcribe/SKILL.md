---
name: offline-transcribe
description: Transcribes already-local audio or video with an already-prefetched local Whisper model and writes a finite JSON transcript plus SRT, VTT, TXT, TSV, and timestamped Markdown. Use when a user says "transcribe this wav offline", "local mlx whisper", "no upload transcript", "강의.part.01.wav 로컬 전사", or "write srt next to this file without fetching a model". Not for OpenAI cloud transcription, URL/download acquisition, diarization, vault writes, or publishing.
metadata:
  version: 1.0.0
---

# offline-transcribe

Run local-only ASR on explicit files with an explicit local model directory and output directory.
Raw ASR stays in the published files; later human corrections are a separate artifact.

On success, each input publishes one exclusive `강의.part.01/` bundle containing `강의.part.01.json`, `강의.part.01.srt`, `강의.part.01.vtt`, `강의.part.01.txt`, `강의.part.01.tsv`, `강의.part.01.md`, and `강의.part.01.receipt.json` from `강의.part.01.wav` using the full original basename with mlx_whisper's public writer.
No flat output aliases are created or read.
JSON is finite-only. Duration is decoded PCM sample count at 16 kHz, never container/video duration, elapsed runtime, or last spoken timestamp.
If decoding, a writer, a timestamp check, or native exclusive directory publication fails, that item fails without publishing a new bundle. Existing destination content stays untouched. Publication is one macOS `renameatx_np(..., RENAME_EXCL)` commit from same-filesystem staging; no destination rollback or unlink is attempted.
A matching digest-bound complete set is reused only when input, consumed model files, options, and actual backend/controller identity still match; mere file existence is not.

When an input, model directory, or option is missing, remote, or incomplete, stop that item or the batch with an honest status. Do not fetch models, follow URLs, or overwrite unrelated files.

## Invoke

```bash
sh skills/offline-transcribe/scripts/transcribe_offline.sh \
  --input "강의.part.01.wav" \
  --model-dir /path/to/prefetched-whisper \
  --output-dir /path/to/out
```

`--input` may be repeated. `--input-list` reads extra local paths, one per line.
Prepare dependencies and the local model separately before invoking the launcher.
Activate the caller's prepared virtual environment or use a prepared uv environment whose `PATH` selects its `python3`; the launcher uses that interpreter without installing anything.
The launcher removes `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` from the child environment before Python starts and sets `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `HF_HUB_DISABLE_TELEMETRY=1`, and `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` for that process only.
It forwards arguments and the interpreter's exit status without changing the caller's environment.
The Python implementation checks those non-secret flag values before SDK use and fails with a usage error when context is missing; use the launcher rather than invoking the implementation directly.
Prefetch is owned by official Hugging Face tooling with `token=False`; this script never downloads.

## Boundaries

- Serial inference only. No URL inputs, Hub repo IDs, diarization, vault writes, or publish.
- Reject a missing or non-directory local model before `load_model` so it cannot become a Hub id.
- Decode with ffmpeg `protocol_whitelist=file,crypto,data` so a local playlist cannot pull remote media.
- Treat process flags and the decoder protocol whitelist as specific controls, not a universal filesystem or network sandbox; SDK cache and token files are not audited by this package.
- Do not treat last-segment time as media completeness.
- Flag suspicious repetition; do not invent coverage or rewrite speech.
- Reject out-of-range ASR timestamps rather than silently clamping them. A `coverage_gap` warning can reflect trailing silence and does not prove missing speech.
- Occupied bundle files, empty directories, and symlinks at the bundle name are conflicts, not reuse; the bundle symlink is never followed.
- Exclusive bundle publication is supported only on macOS filesystems that provide `renameatx_np`; unsupported platforms or filesystems fail closed.
- The batch result is returned and printed as JSON; it is not written to a fixed `offline-transcribe.batch.json` path. Each completed input owns its durable receipt inside its bundle. Exit 1 if any item failed, 2 on usage error.

## Requirements

- POSIX `sh`, `env` with `-u`, `dirname`, and a prepared `python3` on `PATH` with local `mlx-whisper`, `mlx`, and `numpy`; `ffmpeg` must also be on `PATH`.
- Related official skills and CLI/agent runtimes follow the `skillify` skill's contract §10.
- Cloud OpenAI transcribe remains the vendor skill under its official name; do not shadow it.
