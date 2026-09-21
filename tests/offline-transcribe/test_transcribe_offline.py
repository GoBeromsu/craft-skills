#!/usr/bin/env python3
"""Filesystem and integrity behavior for offline-transcribe."""
from __future__ import annotations

import importlib.util
import io
import json
import math
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[2] / "skills/offline-transcribe/scripts/transcribe_offline.py"
LAUNCHER = SCRIPT.with_suffix(".sh")
SPEC = importlib.util.spec_from_file_location("transcribe_offline", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

STEM = "강의.part.01"
AUDIO = f"{STEM}.wav"
OPTIONS = {"language": None, "word_timestamps": False, "condition_on_previous_text": True}
OFFLINE_ENV = {
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
}


def _model_dir(root: Path, name: str = "model") -> Path:
    path = root / name
    path.mkdir()
    (path / "config.json").write_text('{"n_mels": 80}\n', encoding="utf-8")
    (path / "weights.npz").write_bytes(b"npz-bytes")
    return path


def _audio(root: Path, name: str = AUDIO) -> Path:
    path = root / name
    path.write_bytes(b"RIFF-fake")
    return path


def _backend(text: str = "hello", start: float = 0.0, end: float = 1.0):
    def run(_audio_path: Path, _model_dir: Path, _options: dict) -> dict:
        return {
            "text": text,
            "language": "en",
            "segments": [{"start": start, "end": end, "text": text}],
        }
    return run


def _duration(_path: Path) -> float:
    return 1.0


def _pcm(samples: int):
    class Fake:
        def flatten(self):
            return self

        def astype(self, _dtype):
            return self

        def __truediv__(self, _other):
            return self

    def decode(_path: Path):
        return Fake(), float(samples) / float(mod.SAMPLE_RATE)

    return decode


def _bundle(out: Path) -> Path:
    return out / STEM


def _output(out: Path, ext: str) -> Path:
    return _bundle(out) / (f"{STEM}.receipt.json" if ext == "receipt.json" else f"{STEM}.{ext}")


class OfflineTranscribeTest(unittest.TestCase):
    def setUp(self) -> None:
        offline_env = mock.patch.dict(os.environ, OFFLINE_ENV)
        offline_env.start()
        self.addCleanup(offline_env.stop)
        self._native_rename = mod._native_exclusive_directory_rename
        mod._native_exclusive_directory_rename = self._commit_staging

    def tearDown(self) -> None:
        mod._native_exclusive_directory_rename = self._native_rename

    @staticmethod
    def _commit_staging(
        parent: Path,
        staging_name: str,
        destination_name: str,
        _staging_dir: Path,
    ) -> None:
        os.rename(parent / staging_name, parent / destination_name)

    def test_unicode_internal_dot_stem_and_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.mkdir()
            model = _model_dir(root)
            audio = _audio(root)
            first = mod.transcribe_item(
                audio, model, out, OPTIONS, backend=_backend(), duration_fn=_duration,
            )
            self.assertEqual(first["status"], "complete")
            self.assertEqual(first["outputs"]["json"], str(_output(out, "json")))
            self.assertFalse((out / f"{STEM}.json").exists())
            for ext in ("json", "srt", "vtt", "txt", "tsv", "md", "receipt.json"):
                path = _output(out, ext)
                self.assertTrue(path.is_file(), path)
                self.assertFalse(path.is_symlink())
            payload = json.loads(_output(out, "json").read_text(encoding="utf-8"))
            self.assertEqual(payload["duration_seconds"], 1.0)
            self.assertTrue(payload["raw_asr"])
            self.assertIn("controller_sha256", payload["backend"])
            reused = mod.transcribe_item(
                audio, model, out, OPTIONS, backend=_backend("CHANGED"), duration_fn=_duration,
            )
            self.assertEqual(reused["status"], "reused")
            self.assertEqual(json.loads(_output(out, "json").read_text(encoding="utf-8"))["text"], "hello")

    def test_nonfinite_and_out_of_range_timestamps_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.mkdir()
            model = _model_dir(root)
            audio = _audio(root)
            with self.assertRaises(mod.ItemError):
                mod.transcribe_item(
                    audio, model, out, OPTIONS, backend=_backend(end=float("nan")), duration_fn=_duration,
                )
            with self.assertRaises(mod.ItemError):
                mod.transcribe_item(
                    audio, model, out, OPTIONS, backend=_backend(end=9.0), duration_fn=_duration,
                )
            self.assertEqual(list(out.iterdir()), [])

    def test_negative_duration_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.mkdir()
            with self.assertRaises(mod.ItemError):
                mod.transcribe_item(
                    _audio(root), _model_dir(root), out, OPTIONS,
                    backend=_backend(), duration_fn=lambda _p: -1.0,
                )

    def test_decoded_pcm_duration_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.mkdir()
            model = _model_dir(root)
            seen = {}
            audio = _audio(root)
            decoded_waveform, decoded_duration = _pcm(8000)(audio)

            def infer(waveform, _model, _options):
                seen["waveform"] = waveform
                return _backend(end=0.5)(audio, model, OPTIONS)

            result = mod.transcribe_item(
                audio, model, out, OPTIONS,
                decode_fn=lambda _path: (decoded_waveform, decoded_duration), infer_fn=infer,
            )
            self.assertEqual(result["status"], "complete")
            payload = json.loads(_output(out, "json").read_text(encoding="utf-8"))
            self.assertEqual(payload["duration_seconds"], 0.5)
            self.assertIs(seen["waveform"], decoded_waveform)

    def test_repetition_is_flagged_not_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.mkdir()

            def repeating(_a, _m, _o):
                return {
                    "text": "hi hi hi",
                    "language": "en",
                    "segments": [
                        {"start": 0.0, "end": 0.2, "text": "hi"},
                        {"start": 0.2, "end": 0.4, "text": "hi"},
                        {"start": 0.4, "end": 1.0, "text": "hi"},
                    ],
                }

            result = mod.transcribe_item(
                _audio(root), _model_dir(root), out, OPTIONS,
                backend=repeating, duration_fn=_duration,
            )
            self.assertIn("suspicious_repetition", result["warnings"])
            payload = json.loads(_output(out, "json").read_text(encoding="utf-8"))
            self.assertEqual([seg["text"] for seg in payload["segments"]], ["hi", "hi", "hi"])

    def test_writer_failure_is_all_or_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.mkdir()
            original = mod.write_markdown

            def boom(*_args, **_kwargs):
                raise RuntimeError("writer boom")

            mod.write_markdown = boom
            try:
                with self.assertRaises(mod.ItemError):
                    mod.transcribe_item(
                        _audio(root), _model_dir(root), out, OPTIONS,
                        backend=_backend(), duration_fn=_duration,
                    )
            finally:
                mod.write_markdown = original
            self.assertEqual(list(out.iterdir()), [])

    def test_callback_before_commit_observes_complete_staging_and_no_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.mkdir()
            seen = {}

            def callback(parent, staging_name, destination_name, staging_dir):
                destination = parent / destination_name
                self.assertFalse(destination.exists())
                self.assertFalse(destination.is_symlink())
                self.assertEqual(staging_dir, parent / staging_name)
                self.assertEqual(
                    {path.name for path in staging_dir.iterdir()},
                    {
                        f"{STEM}.json",
                        f"{STEM}.srt",
                        f"{STEM}.vtt",
                        f"{STEM}.txt",
                        f"{STEM}.tsv",
                        f"{STEM}.md",
                        f"{STEM}.receipt.json",
                    },
                )
                seen["called"] = True
                seen["count"] = seen.get("count", 0) + 1
                os.rename(staging_dir, destination)

            original = mod._native_exclusive_directory_rename
            mod._native_exclusive_directory_rename = callback
            try:
                result = mod.transcribe_item(
                    _audio(root), _model_dir(root), out, OPTIONS,
                    backend=_backend(), duration_fn=_duration,
                )
            finally:
                mod._native_exclusive_directory_rename = original
            self.assertTrue(seen["called"])
            self.assertEqual(seen["count"], 1)
            self.assertEqual(result["status"], "complete")
            self.assertTrue(_bundle(out).is_dir())

    def test_failed_commit_publishes_nothing_without_destination_unlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.mkdir()
            sentinel = root / "user.txt"
            sentinel.write_text("keep-me\n", encoding="utf-8")

            def fail(*_args):
                raise mod.ItemError("native commit failed")

            original = mod._native_exclusive_directory_rename
            mod._native_exclusive_directory_rename = fail
            try:
                with self.assertRaises(mod.ItemError):
                    mod.transcribe_item(
                        _audio(root), _model_dir(root), out, OPTIONS,
                        backend=_backend(), duration_fn=_duration,
                    )
            finally:
                mod._native_exclusive_directory_rename = original
            self.assertFalse(_bundle(out).exists())
            self.assertFalse(_bundle(out).is_symlink())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep-me\n")

    def test_collision_at_commit_preserves_empty_directory_file_and_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = _model_dir(root)
            audio = _audio(root)
            for kind in ("directory", "file", "symlink"):
                out = root / f"out-{kind}"
                out.mkdir()
                target = root / f"{kind}-target"
                if kind == "symlink":
                    target.write_text("keep-target\n", encoding="utf-8")

                def collide(parent, _staging_name, destination_name, _staging_dir):
                    destination = parent / destination_name
                    if kind == "directory":
                        destination.mkdir()
                    elif kind == "file":
                        destination.write_text("keep-file\n", encoding="utf-8")
                    else:
                        destination.symlink_to(target)
                    raise mod.ItemError("refusing to overwrite existing bundle")

                original = mod._native_exclusive_directory_rename
                mod._native_exclusive_directory_rename = collide
                try:
                    with self.assertRaises(mod.ItemError):
                        mod.transcribe_item(
                            audio, model, out, OPTIONS,
                            backend=_backend(), duration_fn=_duration,
                        )
                finally:
                    mod._native_exclusive_directory_rename = original
                destination = out / STEM
                self.assertTrue(destination.is_symlink() if kind == "symlink" else destination.exists())
                if kind == "directory":
                    self.assertEqual(list(destination.iterdir()), [])
                elif kind == "file":
                    self.assertEqual(destination.read_text(encoding="utf-8"), "keep-file\n")
                else:
                    self.assertEqual(target.read_text(encoding="utf-8"), "keep-target\n")

    def test_occupied_bundle_symlink_is_not_followed_for_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = _model_dir(root)
            audio = _audio(root)
            out = root / "out"
            out.mkdir()
            target = root / "target-bundle"
            target.mkdir()
            marker = target / "marker.txt"
            marker.write_text("do-not-follow\n", encoding="utf-8")
            (out / STEM).symlink_to(target, target_is_directory=True)
            with self.assertRaises(mod.ItemError):
                mod.transcribe_item(
                    audio, model, out, OPTIONS, backend=_backend(), duration_fn=_duration,
                )
            self.assertEqual(marker.read_text(encoding="utf-8"), "do-not-follow\n")

    def test_changed_input_model_options_backend_and_output_invalidate_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.mkdir()
            model = _model_dir(root)
            audio = _audio(root)
            first = mod.transcribe_item(audio, model, out, OPTIONS, backend=_backend(), duration_fn=_duration)
            self.assertEqual(first["status"], "complete")
            audio.write_bytes(b"changed-bytes")
            with self.assertRaises(mod.ItemError):
                mod.transcribe_item(audio, model, out, OPTIONS, backend=_backend(), duration_fn=_duration)
            audio.write_bytes(b"RIFF-fake")
            (model / "weights.npz").write_bytes(b"npz-changed")
            with self.assertRaises(mod.ItemError):
                mod.transcribe_item(audio, model, out, OPTIONS, backend=_backend(), duration_fn=_duration)
            (model / "weights.npz").write_bytes(b"npz-bytes")
            with self.assertRaises(mod.ItemError):
                mod.transcribe_item(
                    audio, model, out,
                    {"language": "ko", "word_timestamps": False, "condition_on_previous_text": True},
                    backend=_backend(), duration_fn=_duration,
                )
            receipt = json.loads(_output(out, "receipt.json").read_text(encoding="utf-8"))
            receipt["backend"]["controller_sha256"] = "deadbeef"
            _output(out, "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaises(mod.ItemError):
                mod.transcribe_item(audio, model, out, OPTIONS, backend=_backend(), duration_fn=_duration)
            original = json.loads(_output(out, "json").read_text(encoding="utf-8"))
            original["text"] = "tampered"
            _output(out, "json").write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaises(mod.ItemError):
                mod.transcribe_item(audio, model, out, OPTIONS, backend=_backend(), duration_fn=_duration)

    def test_unrelated_model_sentinel_is_not_fingerprinted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.mkdir()
            model = _model_dir(root)
            sentinel = model / "secret.bin"
            sentinel.write_bytes(b"do-not-read")
            opened = []
            original = Path.read_bytes

            def tracked(self, *args, **kwargs):
                opened.append(str(self))
                return original(self, *args, **kwargs)

            Path.read_bytes = tracked
            try:
                mod.transcribe_item(
                    _audio(root), model, out, OPTIONS, backend=_backend(), duration_fn=_duration,
                )
            finally:
                Path.read_bytes = original
            self.assertFalse(any(path.endswith("secret.bin") for path in opened))
            (model / "secret.bin").write_bytes(b"changed-secret")
            reused = mod.transcribe_item(
                _audio(root), model, out, OPTIONS, backend=_backend(), duration_fn=_duration,
            )
            self.assertEqual(reused["status"], "reused")

    def test_missing_upstream_model_files_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model"
            model.mkdir()
            (model / "weights.bin").write_bytes(b"not-upstream")
            with self.assertRaises(mod.ItemError):
                mod.model_material(model)

    def test_interrupted_receipt_is_not_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.mkdir()
            model = _model_dir(root)
            audio = _audio(root)
            mod.transcribe_item(audio, model, out, OPTIONS, backend=_backend(), duration_fn=_duration)
            receipt = json.loads(_output(out, "receipt.json").read_text(encoding="utf-8"))
            receipt["status"] = "partial"
            _output(out, "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaises(mod.ItemError):
                mod.transcribe_item(audio, model, out, OPTIONS, backend=_backend(), duration_fn=_duration)

    def test_mixed_batch_preserves_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            good = _audio(root, AUDIO)
            missing = root / "no-such.wav"
            receipt = mod.run_batch(
                [good, missing],
                _model_dir(root),
                out,
                OPTIONS,
                backend=_backend(),
                duration_fn=_duration,
            )
            self.assertEqual(receipt["status"], "failed")
            self.assertEqual(receipt["failed"], 1)
            self.assertEqual(receipt["items"][0]["status"], "complete")
            self.assertEqual(receipt["items"][1]["status"], "failed")
            self.assertTrue(_output(out, "json").is_file())

    def test_batch_json_sentinel_and_symlink_are_not_touched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = _model_dir(root)
            audio = _audio(root)
            out = root / "out"
            out.mkdir()
            sentinel = out / "offline-transcribe.batch.json"
            sentinel.write_text("keep-sentinel\n", encoding="utf-8")
            result = mod.run_batch(
                [audio], model, out, OPTIONS, backend=_backend(), duration_fn=_duration,
            )
            self.assertEqual(result["status"], "complete")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep-sentinel\n")

            out2 = root / "out2"
            out2.mkdir()
            target = root / "batch-target"
            target.write_text("keep-target\n", encoding="utf-8")
            batch_link = out2 / "offline-transcribe.batch.json"
            batch_link.symlink_to(target)
            result = mod.run_batch(
                [audio], model, out2, OPTIONS, backend=_backend(), duration_fn=_duration,
            )
            self.assertEqual(result["status"], "complete")
            self.assertTrue(batch_link.is_symlink())
            self.assertEqual(target.read_text(encoding="utf-8"), "keep-target\n")

    def test_url_and_missing_model_are_usage_errors(self) -> None:
        with self.assertRaises(mod.UsageError):
            mod.require_local_path("https://example.com/a.wav", kind="input")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(mod.UsageError):
                mod.require_model_dir(str(Path(tmp) / "missing-model"))

    def test_strict_json_rejects_nan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            with self.assertRaises(ValueError):
                mod.write_strict_json(path, {"n": math.nan})
            self.assertFalse(path.exists())


class LauncherTest(unittest.TestCase):
    def _launch(self, arguments: list[str], exit_code: int):
        with tempfile.TemporaryDirectory(prefix="offline launcher 공간 ") as tmp:
            root = Path(tmp)
            fake_python = root / "python3"
            probe = (
                "import json, os, sys\n"
                "print(json.dumps({\n"
                "    'args': sys.argv[1:],\n"
                "    'credentials_present': [name for name in "
                "('HF_TOKEN', 'HUGGING_FACE_HUB_TOKEN') if name in os.environ],\n"
                f"    'flags': {{name: os.getenv(name) for name in {tuple(OFFLINE_ENV)!r}}},\n"
                "}, ensure_ascii=False))\n"
                "sys.exit(0 if sys.argv[1:] == ['--inspect-parent'] "
                "else int(os.getenv('SYNTHETIC_EXIT')))\n"
            )
            fake_python.write_text(
                "#!/bin/sh\n"
                f"exec {shlex.quote(sys.executable)} -c {shlex.quote(probe)} \"$@\"\n",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            # A complete synthetic environment: never pass host credentials.
            environment = {
                "PATH": f"{root}:/usr/bin:/bin",
                "HF_TOKEN": "synthetic-hf-token",
                "HUGGING_FACE_HUB_TOKEN": "synthetic-hub-token",
                "SYNTHETIC_EXIT": str(exit_code),
                **{name: "caller-value" for name in OFFLINE_ENV},
            }
            result = subprocess.run(
                [
                    "/bin/sh", "-c",
                    '"$@"\nchild_status=$?\npython3 --inspect-parent\nexit "$child_status"',
                    "synthetic-parent", str(LAUNCHER), *arguments,
                ],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.stderr, "")
            child, parent = [json.loads(line) for line in result.stdout.splitlines()]
            return result.returncode, child, parent

    def test_launcher_removes_credentials_before_python_and_scopes_flags(self) -> None:
        status, child, parent = self._launch([], 0)
        self.assertEqual(status, 0)
        self.assertEqual(child["credentials_present"], [])
        self.assertEqual(child["flags"], OFFLINE_ENV)
        self.assertEqual(
            parent["credentials_present"], ["HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"],
        )
        self.assertEqual(parent["flags"], {name: "caller-value" for name in OFFLINE_ENV})

    def test_launcher_forwards_exact_arguments_and_exit_status(self) -> None:
        arguments = [
            "--input", "강의.part.01 file.wav", "", "--output-dir",
            "literal * $HOME ; $(false) ' \"\nsecond line", "--", "-leading-dash",
        ]
        for exit_code in (0, 2, 37):
            with self.subTest(exit_code=exit_code):
                status, child, _parent = self._launch(arguments, exit_code)
                self.assertEqual(status, exit_code)
                self.assertEqual(child["args"], [str(SCRIPT), *arguments])


class OfflineContextTest(unittest.TestCase):
    def test_missing_or_wrong_flag_stops_batch_before_inference_or_output(self) -> None:
        for name in OFFLINE_ENV:
            for value in (None, "0", "true", ""):
                with self.subTest(flag=name, value=value):
                    environment = dict(OFFLINE_ENV)
                    if value is None:
                        del environment[name]
                    else:
                        environment[name] = value
                    with tempfile.TemporaryDirectory() as tmp:
                        root = Path(tmp)
                        output = root / "out"
                        backend = mock.Mock(side_effect=AssertionError("inference ran"))
                        with mock.patch.dict(os.environ, environment, clear=True):
                            with mock.patch.object(mod, "snapshot_identities") as identity:
                                with self.assertRaisesRegex(mod.UsageError, "transcribe_offline.sh"):
                                    mod.run_batch(
                                        [root / AUDIO], root / "model", output, OPTIONS,
                                        backend=backend,
                                    )
                                identity.assert_not_called()
                        backend.assert_not_called()
                        self.assertFalse(output.exists())

    def test_missing_context_blocks_direct_sdk_entrypoints(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("builtins.__import__", side_effect=AssertionError("SDK import ran")):
                with self.assertRaisesRegex(mod.UsageError, "required offline context"):
                    mod.backend_identity()
                with self.assertRaisesRegex(mod.UsageError, "required offline context"):
                    mod.infer_mlx(object(), Path("/missing-model"), OPTIONS)
                with self.assertRaisesRegex(mod.UsageError, "required offline context"):
                    mod.transcribe_item(
                        Path("/missing-audio"), Path("/missing-model"), Path("/unused"), OPTIONS,
                    )

    def test_main_reports_missing_context_as_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = _model_dir(root)
            audio = _audio(root)
            output = root / "out"
            error = io.StringIO()
            with mock.patch.dict(os.environ, {}, clear=True), redirect_stderr(error):
                status = mod.main([
                    "--input", str(audio), "--model-dir", str(model),
                    "--output-dir", str(output),
                ])
            self.assertEqual(status, 2)
            payload = json.loads(error.getvalue())
            self.assertEqual(payload["status"], "usage_error")
            self.assertIn("transcribe_offline.sh", payload["error"])
            self.assertFalse(output.exists())


class NativePublicationTest(unittest.TestCase):
    @staticmethod
    def _publication_set(
        root: Path,
    ) -> tuple[Path, dict[str, Path], dict[str, Path]]:
        output = root / "out"
        output.mkdir()
        staging_dir = output / ".staging"
        staging_dir.mkdir()
        destination_bundle = output / STEM
        extensions = ("json", "srt", "vtt", "txt", "tsv", "md", "receipt.json")
        staging = {
            ext: staging_dir
            / (f"{STEM}.receipt.json" if ext == "receipt.json" else f"{STEM}.{ext}")
            for ext in extensions
        }
        destinations = {
            ext: destination_bundle
            / (f"{STEM}.receipt.json" if ext == "receipt.json" else f"{STEM}.{ext}")
            for ext in extensions
        }
        for ext, path in staging.items():
            path.write_text(f"staged-{ext}\n", encoding="utf-8")
        return output, staging, destinations

    def test_native_publication_commits_one_complete_bundle(self) -> None:
        with tempfile.TemporaryDirectory(prefix="offline-transcribe-native-") as tmp:
            root = Path(tmp)
            output, staging, destinations = self._publication_set(root)
            staging_dir = next(iter(staging.values())).parent
            destination_bundle = output / STEM
            if sys.platform != "darwin":
                with self.assertRaisesRegex(
                    mod.ItemError,
                    "exclusive directory publication is unsupported on this platform",
                ):
                    mod.publish_complete_set(staging, destinations)
                self.assertTrue(staging_dir.is_dir())
                self.assertFalse(destination_bundle.exists())
                return

            mod.publish_complete_set(staging, destinations)

            self.assertTrue(destination_bundle.is_dir())
            self.assertFalse(destination_bundle.is_symlink())
            self.assertFalse(staging_dir.exists())
            self.assertEqual(
                {entry.name for entry in destination_bundle.iterdir()},
                {path.name for path in destinations.values()},
            )
            for ext, path in destinations.items():
                self.assertEqual(path.read_text(encoding="utf-8"), f"staged-{ext}\n")

    def test_native_eexist_preserves_existing_empty_directory_file_and_symlink(self) -> None:
        for kind in ("directory", "file", "symlink"):
            with self.subTest(kind=kind):
                with tempfile.TemporaryDirectory(prefix="offline-transcribe-native-") as tmp:
                    root = Path(tmp)
                    output, staging, destinations = self._publication_set(root)
                    staging_dir = next(iter(staging.values())).parent
                    destination_bundle = output / STEM
                    if sys.platform != "darwin":
                        with self.assertRaisesRegex(
                            mod.ItemError,
                            "exclusive directory publication is unsupported on this platform",
                        ):
                            mod.publish_complete_set(staging, destinations)
                        self.assertTrue(staging_dir.is_dir())
                        self.assertFalse(destination_bundle.exists())
                        continue

                    target = root / f"{kind}-target"
                    if kind == "symlink":
                        target.write_text("existing-target\n", encoding="utf-8")

                    real_native = mod._native_exclusive_directory_rename

                    def inject_collision(
                        parent: Path,
                        _staging_name: str,
                        destination_name: str,
                        _staging_dir: Path,
                        collision_kind: str = kind,
                        collision_target: Path = target,
                    ) -> None:
                        destination = parent / destination_name
                        if collision_kind == "directory":
                            destination.mkdir()
                        elif collision_kind == "file":
                            destination.write_text("existing-file\n", encoding="utf-8")
                        else:
                            destination.symlink_to(collision_target)
                        real_native(parent, _staging_name, destination_name, _staging_dir)

                    mod._native_exclusive_directory_rename = inject_collision
                    try:
                        with self.assertRaisesRegex(
                            mod.ItemError, "refusing to overwrite existing bundle"
                        ):
                            mod.publish_complete_set(staging, destinations)
                    finally:
                        mod._native_exclusive_directory_rename = real_native

                    self.assertTrue(staging_dir.is_dir())
                    self.assertEqual(
                        {entry.name for entry in staging_dir.iterdir()},
                        {path.name for path in staging.values()},
                    )
                    if kind == "directory":
                        self.assertTrue(destination_bundle.is_dir())
                        self.assertFalse(destination_bundle.is_symlink())
                        self.assertEqual(list(destination_bundle.iterdir()), [])
                    elif kind == "file":
                        self.assertTrue(destination_bundle.is_file())
                        self.assertFalse(destination_bundle.is_symlink())
                        self.assertEqual(
                            destination_bundle.read_text(encoding="utf-8"),
                            "existing-file\n",
                        )
                    else:
                        self.assertTrue(destination_bundle.is_symlink())
                        self.assertEqual(
                            destination_bundle.read_text(encoding="utf-8"),
                            "existing-target\n",
                        )
                        self.assertEqual(
                            target.read_text(encoding="utf-8"),
                            "existing-target\n",
                        )


if __name__ == "__main__":
    unittest.main()
