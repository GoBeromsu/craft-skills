#!/usr/bin/env python3
"""Block drift among skill inventory surfaces."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(re.sub(r"(?m)^\s*#.*\n?", "", text))


def _skill_dirs(root: Path) -> set[str]:
    skills = root / "skills"
    if not skills.is_dir():
        raise ValueError("missing skills directory")
    return {
        child.name
        for child in skills.iterdir()
        if child.is_dir() and (child / "SKILL.md").is_file()
    }


def _agents_names(root: Path) -> set[str]:
    text = (root / "AGENTS.md").read_text(encoding="utf-8")
    match = re.search(r"The \d+ packages \(alphabetical\):\s*(.+?)\.", text, re.DOTALL)
    if not match:
        raise ValueError("AGENTS.md lacks the 'The N packages (alphabetical)' sentence")
    return set(re.findall(r"`([a-z0-9-]+)`", match.group(1)))


def _manifest_names(root: Path) -> set[str]:
    manifest = _load_json(root / "skills-manifest.yaml")
    return {package["name"] for package in manifest["packages"]}


def _coverage_names(root: Path) -> set[str]:
    coverage = _load_json(root / "docs/governance/routing-eval-coverage.json")
    return set(coverage["expected_craft_packages"])


def _routing_names(root: Path) -> set[str]:
    routing = _load_json(root / "docs/governance/routing-eval-cases.yaml")
    prefix = "craft-skills/"
    return {
        case["expected_package"][len(prefix) :]
        for case in routing["cases"]
        if case.get("expected_package", "").startswith(prefix)
    }


def _plugin_counts(root: Path, package_count: int) -> list[str]:
    errors: list[str] = []
    for relative_path in (".codex-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        path = root / relative_path
        payload = _load_json(path)
        text = json.dumps(payload, ensure_ascii=False)
        counts = [
            int(value)
            for value in re.findall(r"\b(?:across|packages)\s+(\d+)\s+(?:packages|reusable)\b", text)
        ]
        if not counts:
            errors.append(f"{relative_path}: missing package-count string")
        elif any(count != package_count for count in counts):
            errors.append(
                f"{relative_path}: package-count strings {counts} do not match {package_count}"
            )
    return errors


def _compare(reference_name: str, reference: set[str], actual_name: str, actual: set[str]) -> list[str]:
    if actual == reference:
        return []
    missing = ", ".join(sorted(reference - actual)) or "none"
    unexpected = ", ".join(sorted(actual - reference)) or "none"
    return [f"{actual_name}: missing [{missing}]; unexpected [{unexpected}] against {reference_name}"]


def check_inventory_surfaces(root: Path) -> list[str]:
    """Return per-surface inventory drift diagnostics, or an empty list."""
    extractors = {
        "skills/*/ directories": _skill_dirs,
        "AGENTS.md list": _agents_names,
        "skills-manifest.yaml names": _manifest_names,
        "routing-eval-coverage.json names": _coverage_names,
        "routing case craft-owned expected set": _routing_names,
    }
    inventories: dict[str, set[str]] = {}
    errors: list[str] = []

    for name, extractor in extractors.items():
        try:
            inventories[name] = extractor(root)
        except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"{name}: cannot read inventory ({error})")

    reference_name = "skills/*/ directories"
    reference = inventories.get(reference_name)
    if reference is not None:
        for name, actual in inventories.items():
            if name != reference_name:
                errors.extend(_compare(reference_name, reference, name, actual))
        errors.extend(_plugin_counts(root, len(reference)))
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
    errors = check_inventory_surfaces(args.root.resolve())
    if errors:
        print("Inventory surfaces check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Inventory surfaces check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
