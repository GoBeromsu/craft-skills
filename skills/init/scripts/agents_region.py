#!/usr/bin/env python3
"""Replace one marker-delimited region of an AGENTS file, byte-exactly.

This is the only part of the AGENTS lifecycle that is not judgment: deciding
where instructions belong and what they say is prose work for the agent, but
editing a delimited span without disturbing a single surrounding byte is
fragile string surgery that is done wrong by hand. Everything else -- scoring,
placement, deletion authority -- deliberately stays out of this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

BEGIN = "<!-- init:managed id={id} sha256={sha256} -->"
END = "<!-- /init:managed id={id} -->"


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def envelope(managed_id: str, payload: bytes) -> bytes:
    """Wrap a payload so its own hash makes later drift detectable."""
    if not payload.endswith(b"\n"):
        raise ValueError("payload must end with LF")
    text = payload.decode("utf-8")
    return (
        BEGIN.format(id=managed_id, sha256=_digest(payload))
        + "\n"
        + text
        + END.format(id=managed_id)
        + "\n"
    ).encode("utf-8")


def _read(path: Path) -> tuple[bytes, int] | None:
    """Read a regular file without ever following a symlink."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise ValueError(f"{path} is not a safe regular file: {error}") from error
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"{path} is not a regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks), stat.S_IMODE(info.st_mode)
    finally:
        os.close(descriptor)


def region_span(data: bytes, managed_id: str) -> tuple[int, int]:
    """Locate exactly one self-consistent managed region, or refuse the file.

    The hash recorded in the opening marker is what makes a hand edit inside the
    region detectable. Verifying it here is what keeps 'never silently overwrite
    existing content' true for bytes a person added between the markers.
    """
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("managed file must be UTF-8") from error
    end = END.format(id=managed_id)
    opener = f"<!-- init:managed id={managed_id} sha256="
    start = text.find(opener)
    if start < 0:
        raise ValueError("managed region is absent")
    if text.find(opener, start + 1) >= 0:
        raise ValueError("managed region is ambiguous")
    head = text.find("\n", start)
    finish = text.find(end, head) if head >= 0 else -1
    if head < 0 or finish < 0:
        raise ValueError("managed region is unterminated")
    recorded = text[start + len(opener) : head].removesuffix(" -->")
    if len(recorded) != 64 or any(character not in "0123456789abcdef" for character in recorded):
        raise ValueError("managed region marker has no valid payload hash")
    if _digest(text[head + 1 : finish].encode("utf-8")) != recorded:
        raise ValueError("managed region was edited by hand; resolve it before rewriting")
    finish += len(end)
    if finish < len(text) and text[finish] == "\n":
        finish += 1
    return len(text[:start].encode("utf-8")), len(text[:finish].encode("utf-8"))


def apply_region(path: Path, managed_id: str, payload: bytes) -> dict[str, object]:
    """Install the payload as the file's managed region, preserving the rest."""
    block = envelope(managed_id, payload)
    observed = _read(path)
    if observed is None:
        merged, mode = block, 0o644
    else:
        current, mode = observed
        try:
            start, finish = region_span(current, managed_id)
        except ValueError as error:
            if str(error) != "managed region is absent":
                raise
            # Never silently swallow incumbent instructions: append the region
            # after existing content instead of replacing the file.
            separator = b"" if not current or current.endswith(b"\n\n") else (b"\n" if current.endswith(b"\n") else b"\n\n")
            merged = current + separator + block
        else:
            merged = current[:start] + block + current[finish:]
        if merged == current:
            return {"path": str(path), "changed": False, "mode": mode, "sha256": _digest(current)}
    temporary = path.with_name(f".{path.name}.init-region.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        offset = 0
        while offset < len(merged):
            written = os.write(descriptor, merged[offset:])
            if written <= 0:
                raise OSError("write made no progress")
            offset += written
        os.fchmod(descriptor, mode)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    return {"path": str(path), "changed": True, "mode": mode, "sha256": _digest(merged)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write one managed AGENTS region in place.")
    parser.add_argument("path", help="AGENTS file to update")
    parser.add_argument("--id", required=True, help="managed region id")
    parser.add_argument("--payload-file", required=True, help="payload file, or - for stdin")
    args = parser.parse_args(argv)
    try:
        if "/" in args.id or any(character.isspace() for character in args.id) or ">" in args.id or not args.id:
            raise ValueError("managed id must be non-empty with no whitespace, '/' or '>'")
        payload = sys.stdin.buffer.read() if args.payload_file == "-" else Path(args.payload_file).read_bytes()
        result = apply_region(Path(args.path), args.id, payload)
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
