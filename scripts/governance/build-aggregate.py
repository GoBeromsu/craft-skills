#!/usr/bin/env python3
"""Build the generated skill-manifest aggregate from repository manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from schema import validate_aggregate

GENERATOR_VERSION = "1"
MANIFEST_NAME = "skills-manifest.yaml"
HEADER_BY_VISIBILITY = {
    "all": "# PRIVATE-LOCAL artifact: generated from workspace manifests; do not publish or hand-edit.\n",
    "public": "# PUBLIC artifact: generated from workspace manifests with visibility:private packages excluded.\n",
}
VISIBILITY_CHOICES = tuple(HEADER_BY_VISIBILITY)


def _strip_comment_lines(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def _load_jsonish_yaml(path: Path) -> Any:
    try:
        return json.loads(_strip_comment_lines(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: expected JSON-compatible YAML: {exc}") from exc


def _load_repos_config(path: Path) -> list[dict[str, str]]:
    data = _load_jsonish_yaml(path)
    repos = data.get("repos") if isinstance(data, dict) else None
    if not isinstance(repos, list):
        raise SystemExit(f"{path}: expected top-level repos array")
    normalized: list[dict[str, str]] = []
    for index, repo in enumerate(repos):
        if not isinstance(repo, dict):
            raise SystemExit(f"{path}: repos[{index}] must be an object")
        name = repo.get("name")
        repo_path = repo.get("path")
        if not isinstance(name, str) or not name:
            raise SystemExit(f"{path}: repos[{index}].name must be a non-empty string")
        if not isinstance(repo_path, str) or not repo_path:
            raise SystemExit(f"{path}: repos[{index}].path must be a non-empty string")
        normalized.append({"name": name, "path": repo_path})
    return normalized


def _load_manifest(repo: dict[str, str]) -> tuple[Path, dict[str, Any]]:
    manifest_path = Path(repo["path"]).expanduser().resolve() / MANIFEST_NAME
    if not manifest_path.exists():
        raise SystemExit(f"missing manifest for {repo['name']}: {manifest_path}")
    data = _load_jsonish_yaml(manifest_path)
    if not isinstance(data, dict):
        raise SystemExit(f"{manifest_path}: manifest must be an object")
    if data.get("schema_version") != 1:
        raise SystemExit(f"{manifest_path}: schema_version must be 1")
    packages = data.get("packages")
    if not isinstance(packages, list):
        raise SystemExit(f"{manifest_path}: packages must be an array")
    return manifest_path, data


def build(config_path: Path, *, visibility: str = "all") -> dict[str, Any]:
    repos = sorted(_load_repos_config(config_path), key=lambda repo: repo["name"])
    source_manifests: list[str] = []
    packages: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    if visibility not in VISIBILITY_CHOICES:
        raise SystemExit(f"unsupported visibility: {visibility}")

    for repo in repos:
        manifest_path, manifest = _load_manifest(repo)
        source_manifests.append(f"{repo['name']}/{MANIFEST_NAME}")
        for package in manifest["packages"]:
            if not isinstance(package, dict):
                raise SystemExit(f"{manifest_path}: every package must be an object")
            package_id = package.get("id")
            if not isinstance(package_id, str) or not package_id:
                raise SystemExit(f"{manifest_path}: every package needs a non-empty id")
            if package_id in seen_ids:
                raise SystemExit(f"duplicate package id: {package_id}")
            seen_ids.add(package_id)
            if package.get("schema_version") != 1:
                raise SystemExit(f"{manifest_path}: package {package_id} schema_version must be 1")
            if visibility == "public" and package.get("visibility") == "private":
                continue
            packages.append(dict(package))

    return {
        "generated": True,
        "schema_version": 1,
        "generator": {
            "name": "craft-skills/scripts/governance/build-aggregate.py; GENERATED DO NOT EDIT",
            "version": GENERATOR_VERSION,
        },
        "source_manifests": sorted(source_manifests),
        "packages": sorted(packages, key=lambda package: package["id"]),
    }


def render(aggregate: dict[str, Any], *, visibility: str = "all") -> str:
    if visibility not in VISIBILITY_CHOICES:
        raise SystemExit(f"unsupported visibility: {visibility}")
    return HEADER_BY_VISIBILITY[visibility] + json.dumps(aggregate, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="JSON-compatible repos.yaml path")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="aggregate JSON output path",
    )
    parser.add_argument(
        "--visibility",
        choices=VISIBILITY_CHOICES,
        default="all",
        help="aggregate visibility filter; public excludes visibility:private packages",
    )
    args = parser.parse_args()

    output = args.output
    if output is None:
        output = Path("governance/generated/aggregate-public.json" if args.visibility == "public" else "governance/generated/aggregate.json")

    aggregate = build(args.config, visibility=args.visibility)
    schema_findings = validate_aggregate(aggregate, source="generated aggregate")
    if schema_findings:
        first = schema_findings[0]
        raise SystemExit(f"generated aggregate failed schema validation: {first['code']}: {first['message']}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(aggregate, visibility=args.visibility), encoding="utf-8")
    print(f"wrote {output} ({len(aggregate['packages'])} packages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
