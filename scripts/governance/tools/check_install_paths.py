#!/usr/bin/env python3
"""Check that documented runtime install channels and paths agree."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SURFACES = {
    "README.md": Path("README.md"),
    "AGENTS.md": Path("AGENTS.md"),
    "install.sh": Path("install.sh"),
    ".hermes/README.md": Path(".hermes/README.md"),
}
_REQUIRED = {
    "claude": ("README.md", "AGENTS.md", "install.sh"),
    "codex_plugin": ("README.md", "AGENTS.md", "install.sh"),
    "codex_clone": ("README.md", "AGENTS.md", "install.sh"),
    "hermes": ("README.md", "AGENTS.md", "install.sh", ".hermes/README.md"),
}


def _one(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1) if match else None


def _normalize_assignment_path(value: str) -> str:
    value = value.strip()
    for prefix in ("${PWD}/", "$PWD/"):
        if value.startswith(prefix):
            return value[len(prefix) :]
    for prefix in ("${HOME}/", "$HOME/"):
        if value.startswith(prefix):
            return "~/" + value[len(prefix) :]
    return value


def _assignment(name: str, text: str) -> str | None:
    match = re.search(
        rf"^\s*{name}=(?:\"([^\"]*)\"|'([^']*)'|([^\s#]+))\s*(?:#.*)?$",
        text,
        flags=re.MULTILINE,
    )
    if not match:
        return None
    return _normalize_assignment_path(next(value for value in match.groups() if value is not None))


def _declared_paths(text: str, surface: str) -> dict[str, str]:
    """Extract documented values, using install.sh executable assignments."""
    declarations: dict[str, str] = {}

    marketplace = _one(r"/plugin\s+marketplace\s+add\s+([A-Za-z0-9._/-]+)", text)
    plugin = _one(r"/plugin\s+install\s+([A-Za-z0-9@._/-]+)", text)
    if marketplace or plugin:
        if marketplace and plugin:
            declarations["claude"] = f"{marketplace};{plugin}"
        else:
            declarations["claude"] = "<incomplete Claude marketplace command>"

    if re.search(r"\.codex-plugin/plugin\.json", text):
        declarations["codex_plugin"] = ".codex-plugin/plugin.json"

    if surface == "install.sh":
        clone_path = _assignment("CLONE_DIR", text)
        hermes_path = _assignment("SKILLS_PATH", text)
    else:
        clone_path = _one(
            r"Codex auxiliary clone path:\**\s*[`\"']?([A-Za-z0-9._/-]+)", text
        )
        hermes_path = _one(
            r"Hermes mount path:\**\s*[`\"']?([~A-Za-z0-9._/-]+)", text
        )

    if clone_path:
        declarations["codex_clone"] = clone_path.rstrip(".")
    if hermes_path:
        declarations["hermes"] = hermes_path.rstrip(".")
    return declarations


def check_install_paths(root: Path) -> list[str]:
    declarations: dict[str, dict[str, str]] = {key: {} for key in _REQUIRED}
    errors: list[str] = []

    for surface, relative_path in _SURFACES.items():
        path = root / relative_path
        if not path.is_file():
            errors.append(f"missing install surface: {relative_path}")
            continue
        for key, value in _declared_paths(path.read_text(encoding="utf-8"), surface).items():
            declarations[key][surface] = value

    for key, required_surfaces in _REQUIRED.items():
        values = declarations[key]
        for surface in required_surfaces:
            if surface not in values:
                errors.append(f"{key}: missing declaration in {surface}")
        distinct = sorted(set(values.values()))
        if len(distinct) > 1:
            rendered = ", ".join(f"{surface}={value}" for surface, value in sorted(values.items()))
            errors.append(f"{key}: inconsistent declarations: {rendered}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="repository root to inspect",
    )
    args = parser.parse_args()
    errors = check_install_paths(args.root.resolve())
    if errors:
        print("Install path consistency check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Install path consistency check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
