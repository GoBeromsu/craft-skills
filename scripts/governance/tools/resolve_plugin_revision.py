#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


class PluginRevisionError(Exception):
    pass


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )


def resolve_revision(root: Path, manifest: str, expected_version: str) -> str:
    history = _git(root, "log", "--format=%H", "--", manifest)
    if history.returncode:
        raise PluginRevisionError(history.stderr.strip() or "git log failed")

    for revision in history.stdout.splitlines():
        snapshot = _git(root, "show", f"{revision}:{manifest}")
        if snapshot.returncode:
            continue
        try:
            payload = json.loads(snapshot.stdout)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("version") == expected_version:
            return revision

    raise PluginRevisionError(f"no revision contains {manifest} at version {expected_version}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()
    try:
        revision = resolve_revision(Path.cwd(), args.manifest, args.expected_version)
    except PluginRevisionError as error:
        print(f"resolve_plugin_revision: {error}")
        return 1
    print(revision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
