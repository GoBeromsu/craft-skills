#!/usr/bin/env python3
"""Transcribe local media with a prefetched local Whisper model. No network fetch."""
from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterable

CAPTION_FORMATS = ("txt", "vtt", "srt", "tsv")
OWNED_EXTENSIONS = ("json", "srt", "vtt", "txt", "tsv", "md", "receipt.json")
PROTOCOL_WHITELIST = "file,crypto,data"
SAMPLE_RATE = 16000
TIMESTAMP_EPS = 1e-3
CONTROLLER = Path(__file__).resolve()

BackendFn = Callable[[Path, Path, dict[str, Any]], dict[str, Any]]
DurationFn = Callable[[Path], float]
DecodeFn = Callable[[Path], tuple[Any, float]]
InferFn = Callable[[Any, Path, dict[str, Any]], dict[str, Any]]


class ItemError(Exception):
    pass


class UsageError(Exception):
    pass


def require_offline_context() -> None:
    if (
        os.getenv("HF_HUB_OFFLINE") != "1"
        or os.getenv("TRANSFORMERS_OFFLINE") != "1"
        or os.getenv("HF_HUB_DISABLE_TELEMETRY") != "1"
        or os.getenv("HF_HUB_DISABLE_IMPLICIT_TOKEN") != "1"
    ):
        raise UsageError(
            "required offline context is missing; invoke transcribe_offline.sh "
            "with a prepared Python environment"
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def contained_regular_file(root: Path, name: str) -> Path:
    if "/" in name or name in {".", ".."}:
        raise ItemError("invalid model filename")
    path = root / name
    if path.is_symlink():
        raise ItemError("model file must not be a symlink")
    try:
        resolved = path.resolve()
    except OSError as exc:
        raise ItemError("unreadable model file") from exc
    if not resolved.is_relative_to(root.resolve()):
        raise ItemError("model file escapes model directory")
    if not resolved.is_file() or resolved.is_symlink():
        raise ItemError("model file is missing")
    return resolved


def model_material(directory: Path) -> dict[str, str]:
    root = directory.resolve()
    config = contained_regular_file(root, "config.json")
    safetensors = root / "weights.safetensors"
    npz = root / "weights.npz"
    if safetensors.exists() or safetensors.is_symlink():
        weights = contained_regular_file(root, "weights.safetensors")
        weights_name = "weights.safetensors"
    elif npz.exists() or npz.is_symlink():
        weights = contained_regular_file(root, "weights.npz")
        weights_name = "weights.npz"
    else:
        raise ItemError("model directory is missing weights.safetensors or weights.npz")
    return {
        "config.json": sha256_file(config),
        weights_name: sha256_file(weights),
    }


def output_name_for(input_path: Path) -> str:
    return input_path.name


def owned_paths(output_dir: Path, input_path: Path) -> dict[str, Path]:
    name = output_name_for(input_path)
    base = Path(name)
    stem = base.with_suffix("").name
    bundle = output_dir / stem
    return {
        ext: bundle / (f"{stem}.receipt.json" if ext == "receipt.json" else f"{stem}.{ext}")
        for ext in OWNED_EXTENSIONS
    }


def require_local_path(value: str, *, kind: str) -> Path:
    if "://" in value:
        raise UsageError(f"{kind} must be a local path, not a URL")
    path = Path(value)
    if not path.is_absolute():
        path = path.resolve()
    else:
        path = Path(os.path.realpath(path))
    return path


def require_model_dir(value: str) -> Path:
    if "://" in value:
        raise UsageError("model directory must be a local path, not a URL")
    path = Path(value)
    if not path.is_absolute():
        path = Path.cwd() / path
    if path.is_symlink():
        raise UsageError("model directory must not be a symlink")
    if not path.is_dir():
        raise UsageError("model directory must be an existing local directory")
    return path.resolve()


def module_version(name: str) -> str:
    try:
        module = __import__(name)
    except Exception:
        return "unavailable"
    version = getattr(module, "__version__", None)
    if isinstance(version, str) and version:
        return version
    try:
        from importlib.metadata import version as dist_version
        return dist_version(name)
    except Exception:
        return "unknown"


def backend_identity() -> dict[str, str]:
    require_offline_context()
    whisper_version = module_version("mlx_whisper")
    if whisper_version in {"unavailable", "unknown"}:
        try:
            from mlx_whisper._version import __version__ as whisper_alt
            if isinstance(whisper_alt, str) and whisper_alt:
                whisper_version = whisper_alt
        except Exception:
            pass
    return {
        "name": "mlx_whisper",
        "mlx_whisper": whisper_version,
        "mlx": module_version("mlx"),
        "controller_sha256": sha256_file(CONTROLLER),
    }


def snapshot_identities(input_path: Path, model_dir: Path, options: dict[str, Any]) -> dict[str, Any]:
    return {
        "input": {"path": str(input_path), "sha256": sha256_file(input_path)},
        "model_dir": {"path": str(model_dir), "material": model_material(model_dir)},
        "backend": backend_identity(),
        "options": options,
    }


def identities_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    for key in ("input", "model_dir", "backend", "options"):
        if left.get(key) != right.get(key):
            return False
    return True


def decode_audio(path: Path) -> tuple[Any, float]:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise ItemError("ffmpeg is not on PATH")
    command = [
        ffmpeg,
        "-nostdin",
        "-protocol_whitelist", PROTOCOL_WHITELIST,
        "-i", str(path),
        "-threads", "0",
        "-f", "s16le",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        "-ar", str(SAMPLE_RATE),
        "-",
    ]
    try:
        proc = subprocess.run(command, capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise ItemError("ffmpeg decode failed") from exc
    import numpy as np
    import mlx.core as mx
    pcm = np.frombuffer(proc.stdout, np.int16)
    duration = 0.0 if pcm.size == 0 else float(pcm.size) / float(SAMPLE_RATE)
    if not math.isfinite(duration) or duration < 0:
        raise ItemError("decoded audio duration is not finite and nonnegative")
    waveform = mx.array(pcm).flatten().astype(mx.float32) / 32768.0
    return waveform, duration


def infer_mlx(waveform: Any, model_dir: Path, options: dict[str, Any]) -> dict[str, Any]:
    require_offline_context()
    model_material(model_dir)
    from mlx_whisper.transcribe import transcribe
    return transcribe(
        waveform,
        path_or_hf_repo=str(model_dir),
        verbose=False,
        language=options.get("language"),
        word_timestamps=bool(options.get("word_timestamps")),
        condition_on_previous_text=bool(options.get("condition_on_previous_text")),
    )


def require_finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ItemError(f"{label} is not a number")
    number = float(value)
    if not math.isfinite(number):
        raise ItemError(f"{label} is not finite")
    return number


def validate_result(result: dict[str, Any], duration: float) -> list[str]:
    if duration < 0 or not math.isfinite(duration):
        raise ItemError("media duration is not finite and nonnegative")
    segments = result.get("segments")
    if not isinstance(segments, list):
        raise ItemError("backend result is missing a segments list")
    warnings: list[str] = []
    texts: list[str] = []
    last_end = 0.0
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise ItemError(f"segment {index} is not an object")
        start = require_finite(segment.get("start"), f"segment {index} start")
        end = require_finite(segment.get("end"), f"segment {index} end")
        if start < 0 or end < 0:
            raise ItemError(f"segment {index} has a negative timestamp")
        if start > end:
            raise ItemError(f"segment {index} starts after it ends")
        if end - duration > TIMESTAMP_EPS:
            raise ItemError(f"segment {index} ends after measured media duration")
        text = segment.get("text")
        if not isinstance(text, str):
            raise ItemError(f"segment {index} text is not a string")
        texts.append(text.strip())
        last_end = max(last_end, end)
    if last_end + 0.5 < duration:
        warnings.append("coverage_gap")
    stripped = [text for text in texts if text]
    if len(stripped) >= 3 and len(set(stripped)) == 1:
        warnings.append("suspicious_repetition")
    else:
        repeats = 0
        for previous, current in zip(stripped, stripped[1:]):
            if previous and previous == current:
                repeats += 1
        if repeats >= 2:
            warnings.append("suspicious_repetition")
    return warnings


def write_strict_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_strict_json(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ItemError("JSON readback is not an object")
    json.dumps(payload, allow_nan=False)
    return payload


def write_markdown(path: Path, title: str, duration: float, result: dict[str, Any]) -> None:
    lines = [
        f"# {title}",
        "",
        f"duration_seconds: {duration}",
        f"language: {result.get('language') or ''}",
        "",
    ]
    for segment in result["segments"]:
        start = require_finite(segment["start"], "markdown start")
        end = require_finite(segment["end"], "markdown end")
        lines.append(f"[{start:.3f} → {end:.3f}] {str(segment.get('text', '')).strip()}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_captions(tmpdir: Path, input_name: str, result: dict[str, Any]) -> None:
    try:
        from mlx_whisper.writers import get_writer
    except ImportError as exc:
        raise ItemError("mlx_whisper is required to write caption formats") from exc
    for fmt in CAPTION_FORMATS:
        get_writer(fmt, str(tmpdir))(result, input_name)


RENAME_EXCL = 0x4


def _native_exclusive_directory_rename(
    parent: Path,
    staging_name: str,
    destination_name: str,
    staging_dir: Path,
) -> None:
    """Publish one staged directory with macOS's exclusive rename primitive."""
    if sys.platform != "darwin":
        raise ItemError("exclusive directory publication is unsupported on this platform")
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        renameatx_np = libc.renameatx_np
    except (AttributeError, OSError) as exc:
        raise ItemError("renameatx_np is unavailable") from exc
    renameatx_np.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameatx_np.restype = ctypes.c_int
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        parent_fd = os.open(str(parent), flags)
    except OSError as exc:
        raise ItemError("could not bind output directory") from exc
    try:
        try:
            parent_stat = os.fstat(parent_fd)
            staging_stat = os.stat(staging_dir, follow_symlinks=False)
        except OSError as exc:
            raise ItemError("could not verify publication filesystem") from exc
        if parent_stat.st_dev != staging_stat.st_dev:
            raise ItemError("staging and output directories are on different filesystems")
        ctypes.set_errno(0)
        result = renameatx_np(
            parent_fd,
            os.fsencode(staging_name),
            parent_fd,
            os.fsencode(destination_name),
            RENAME_EXCL,
        )
        if result != 0:
            error_number = ctypes.get_errno()
            if error_number == errno.EEXIST:
                raise ItemError("refusing to overwrite existing bundle")
            detail = os.strerror(error_number) if error_number else "unknown error"
            raise ItemError(f"exclusive bundle publication failed: {detail}")
    finally:
        os.close(parent_fd)


def publish_complete_set(staging: dict[str, Path], destinations: dict[str, Path]) -> None:
    """Atomically publish a complete staged bundle directory."""
    expected = set(OWNED_EXTENSIONS)
    if set(staging) != expected or set(destinations) != expected:
        raise ItemError("publication produced an incomplete set")
    staging_dir = next(iter(staging.values())).parent
    destination_bundle = next(iter(destinations.values())).parent
    parent = destination_bundle.parent
    if staging_dir.parent != parent:
        raise ItemError("staging directory must share the output parent")
    if staging_dir.is_symlink() or not staging_dir.is_dir():
        raise ItemError("staging directory is not a local directory")
    if destination_bundle.name == "" or destination_bundle.name in {".", ".."}:
        raise ItemError("invalid destination bundle")
    for ext in OWNED_EXTENSIONS:
        source = staging[ext]
        destination = destinations[ext]
        if source.parent != staging_dir or destination.parent != destination_bundle:
            raise ItemError("publication paths are not contained in their bundles")
        if source.name != destination.name or source.is_symlink() or not source.is_file():
            raise ItemError("publication staging is incomplete")
    try:
        names = {entry.name for entry in staging_dir.iterdir()}
    except OSError as exc:
        raise ItemError("could not inspect publication staging") from exc
    if names != {source.name for source in staging.values()}:
        raise ItemError("publication staging contains an unexpected file")
    _native_exclusive_directory_rename(
        parent,
        staging_dir.name,
        destination_bundle.name,
        staging_dir,
    )


def load_receipt(path: Path) -> dict[str, Any] | None:
    if path.is_symlink() or not path.is_file():
        return None
    try:
        return load_strict_json(path)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, ItemError, TypeError, ValueError):
        return None


def matching_complete_set(
    paths: dict[str, Path],
    receipt: dict[str, Any],
    expected: dict[str, Any],
) -> bool:
    bundle = paths["receipt.json"].parent
    if bundle.is_symlink() or not bundle.is_dir():
        return False
    if receipt.get("status") != "complete":
        return False
    if not identities_match(receipt, expected):
        return False
    outputs = receipt.get("outputs")
    if not isinstance(outputs, dict):
        return False
    for ext, path in paths.items():
        if ext == "receipt.json":
            continue
        if path.is_symlink() or not path.is_file():
            return False
        digest = outputs.get(ext)
        if digest != sha256_file(path):
            return False
    return True


def transcribe_item(
    input_path: Path,
    model_dir: Path,
    output_dir: Path,
    options: dict[str, Any],
    *,
    backend: BackendFn | None = None,
    duration_fn: DurationFn | None = None,
    decode_fn: DecodeFn | None = None,
    infer_fn: InferFn | None = None,
) -> dict[str, Any]:
    require_offline_context()
    if not input_path.is_file() or input_path.is_symlink():
        raise ItemError("input is not a local regular file")
    paths = owned_paths(output_dir, input_path)
    bundle = paths["receipt.json"].parent
    if bundle.is_symlink():
        raise ItemError("occupied bundle symlink is not a reusable output")
    expected = snapshot_identities(input_path, model_dir, options)
    if bundle.exists():
        if not bundle.is_dir():
            raise ItemError("occupied bundle is not a directory")
        receipt = load_receipt(paths["receipt.json"])
        if receipt and matching_complete_set(paths, receipt, expected):
            return {"input": str(input_path), "status": "reused", "outputs": {k: str(v) for k, v in paths.items()}}
        raise ItemError("incomplete, changed, or unrelated outputs already occupy the destination")
    try:
        if backend is not None:
            duration = (duration_fn or (lambda _path: 0.0))(input_path)
            result = backend(input_path, model_dir, options)
        else:
            waveform, duration = (decode_fn or decode_audio)(input_path)
            result = (infer_fn or infer_mlx)(waveform, model_dir, options)
    except ItemError:
        raise
    except Exception as exc:
        raise ItemError("transcription failed") from exc
    if not isinstance(result, dict):
        raise ItemError("backend did not return an object")
    warnings = validate_result(result, duration)
    payload = {
        "text": result.get("text") if isinstance(result.get("text"), str) else "",
        "language": result.get("language") if isinstance(result.get("language"), str) else "",
        "duration_seconds": duration,
        "segments": result["segments"],
        "warnings": warnings,
        "backend": expected["backend"],
        "raw_asr": True,
    }
    require_finite(payload["duration_seconds"], "duration_seconds")
    if not identities_match(expected, snapshot_identities(input_path, model_dir, options)):
        raise ItemError("input or model identity changed while processing")
    tmpdir = Path(tempfile.mkdtemp(prefix=".offline-transcribe-staging-", dir=str(output_dir)))
    try:
        write_captions(tmpdir, output_name_for(input_path), result)
        title = Path(output_name_for(input_path)).with_suffix("").name
        write_strict_json(tmpdir / f"{title}.json", payload)
        load_strict_json(tmpdir / f"{title}.json")
        write_markdown(tmpdir / f"{title}.md", title, duration, result)
        staging = {
            ext: tmpdir / f"{title}.{ext}"
            for ext in ("json", "srt", "vtt", "txt", "tsv", "md")
        }
        missing = [ext for ext, path in staging.items() if not path.is_file()]
        if missing:
            raise ItemError("caption or integrity writer produced an incomplete set")
        output_digests = {ext: sha256_file(path) for ext, path in staging.items()}
        receipt_payload = {
            "status": "complete",
            **expected,
            "duration_seconds": duration,
            "warnings": warnings,
            "outputs": output_digests,
        }
        receipt_path = tmpdir / f"{title}.receipt.json"
        write_strict_json(receipt_path, receipt_payload)
        load_strict_json(receipt_path)
        staging["receipt.json"] = receipt_path
        publish_complete_set(staging, paths)
    except ItemError:
        raise
    except Exception as exc:
        raise ItemError("publication failed") from exc
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return {
        "input": str(input_path),
        "status": "complete",
        "warnings": warnings,
        "outputs": {k: str(v) for k, v in paths.items()},
    }


def collect_inputs(values: list[str], lists: list[str]) -> list[Path]:
    raw: list[str] = list(values)
    for list_path in lists:
        path = require_local_path(list_path, kind="input list")
        if not path.is_file():
            raise UsageError("input list is not a file")
        raw.extend(
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    if not raw:
        raise UsageError("at least one --input or --input-list path is required")
    return [require_local_path(item, kind="input") for item in raw]


def run_batch(
    inputs: Iterable[Path],
    model_dir: Path,
    output_dir: Path,
    options: dict[str, Any],
    *,
    backend: BackendFn | None = None,
    duration_fn: DurationFn | None = None,
    decode_fn: DecodeFn | None = None,
    infer_fn: InferFn | None = None,
) -> dict[str, Any]:
    require_offline_context()
    output_dir.mkdir(parents=True, exist_ok=True)
    items = []
    failures = 0
    for path in inputs:
        try:
            items.append(
                transcribe_item(
                    path,
                    model_dir,
                    output_dir,
                    options,
                    backend=backend,
                    duration_fn=duration_fn,
                    decode_fn=decode_fn,
                    infer_fn=infer_fn,
                )
            )
        except ItemError as exc:
            failures += 1
            items.append({"input": str(path), "status": "failed", "error": str(exc)})
        except Exception:
            failures += 1
            items.append({"input": str(path), "status": "failed", "error": "transcription failed"})
    receipt = {
        "status": "failed" if failures else "complete",
        "failed": failures,
        "items": items,
    }
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline local-file transcription")
    parser.add_argument("--input", action="append", default=[], help="local media file")
    parser.add_argument("--input-list", action="append", default=[], help="file of local media paths")
    parser.add_argument("--model-dir", required=True, help="already-prefetched local model directory")
    parser.add_argument("--output-dir", required=True, help="directory for transcripts")
    parser.add_argument("--language", default=None)
    parser.add_argument("--word-timestamps", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        inputs = collect_inputs(args.input, args.input_list)
        model_dir = require_model_dir(args.model_dir)
        output_dir = require_local_path(args.output_dir, kind="output directory")
        options = {
            "language": args.language,
            "word_timestamps": bool(args.word_timestamps),
            "condition_on_previous_text": True,
        }
        receipt = run_batch(inputs, model_dir, output_dir, options)
    except UsageError as exc:
        print(json.dumps({"status": "usage_error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, allow_nan=False))
    return 1 if receipt["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
