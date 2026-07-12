#!/usr/bin/env python3
"""Validate portable skill package basics without runtime dependencies."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_ABSOLUTE_HOST_PATH = re.compile(r"(?<![A-Za-z0-9])/(?:Users|home)/[^\s`\"']+")


def write_artifact(status: str, reason: str, checks: list[str]) -> None:
    output_dir = Path(os.environ.get("SMOKE_OUT", "/tmp/craft-smokes"))
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = output_dir / "generic.json"
    artifact.write_text(
        json.dumps(
            {
                "runtime": "generic",
                "status": status,
                "reason": reason,
                "checks": checks,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def frontmatter(skill_path: Path) -> dict[str, str]:
    lines = skill_path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("missing opening frontmatter delimiter")
    try:
        closing = lines.index("---", 1)
    except ValueError as error:
        raise ValueError("missing closing frontmatter delimiter") from error

    fields: dict[str, str] = {}
    in_metadata = False
    for line in lines[1:closing]:
        if line.startswith("metadata:"):
            in_metadata = True
            continue
        if line and not line.startswith((" ", "\t")):
            in_metadata = False
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.+)$", line)
        if match:
            fields[match.group(1)] = match.group(2).strip()
        elif in_metadata:
            match = re.match(r"^\s+([A-Za-z][A-Za-z0-9_-]*):\s*(.+)$", line)
            if match and match.group(1) == "version":
                fields["metadata.version"] = match.group(2).strip()
    return fields


def validate(root: Path) -> list[str]:
    failures: list[str] = []
    skill_files = sorted(root.glob("skills/*/SKILL.md"))
    if not skill_files:
        return ["no skills/*/SKILL.md files found"]

    for skill_path in skill_files:
        package = skill_path.parent.name
        try:
            fields = frontmatter(skill_path)
        except ValueError as error:
            failures.append(f"{package}: {error}")
            continue
        for required in ("name", "description", "metadata.version"):
            if not fields.get(required):
                failures.append(f"{package}: missing frontmatter {required}")
        if fields.get("name") and fields["name"] != package:
            failures.append(f"{package}: frontmatter name is {fields['name']!r}")
        match = _ABSOLUTE_HOST_PATH.search(skill_path.read_text(encoding="utf-8"))
        if match:
            failures.append(f"{package}: contains absolute host path {match.group(0)!r}")
    return failures


def main() -> int:
    root = _ROOT
    if len(sys.argv) == 3 and sys.argv[1] == "--root":
        root = Path(sys.argv[2]).resolve()
    elif len(sys.argv) != 1:
        print("usage: smoke-generic.py [--root REPOSITORY_ROOT]", file=sys.stderr)
        return 2

    failures = validate(root)
    checks = ["frontmatter", "name_matches_directory", "self_contained"]
    if failures:
        write_artifact("failed", "; ".join(failures), checks)
        print("Generic smoke failed:", *failures, sep="\n- ")
        return 1
    write_artifact("passed", "all skill packages are portable", checks)
    print("Generic smoke passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
