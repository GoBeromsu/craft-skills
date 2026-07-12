"""Provenance and license checker for skill manifests."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

CHECKER_NAME = "provenance"
CHECKER_VERSION = "1"


def _repo_paths(config: dict[str, Any]) -> dict[str, Path]:
    repos = config.get("repos", [])
    paths: dict[str, Path] = {}
    for repo in repos:
        if isinstance(repo, dict) and isinstance(repo.get("name"), str) and isinstance(repo.get("path"), str):
            paths[repo["name"]] = Path(repo["path"]).expanduser().resolve()
    return paths


def _profile_value(package: dict[str, Any], key: str) -> str | None:
    profile = package.get("validation_profile")
    if isinstance(profile, dict) and isinstance(profile.get(key), str):
        return profile[key]
    return None


def _severity_for_profile(package: dict[str, Any], key: str) -> str | None:
    value = _profile_value(package, key)
    if value == "skip":
        return None
    if value == "warn":
        return "advisory"
    return "blocking"


def _package_key(package: dict[str, Any]) -> str | None:
    package_id = package.get("id")
    return package_id if isinstance(package_id, str) else None


def _finding(
    code: str,
    package: dict[str, Any],
    severity: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    package_id = _package_key(package)
    return {
        "checker": CHECKER_NAME,
        "code": code,
        "package": package_id,
        "package_id": package_id,
        "severity": severity,
        "message": message,
        "details": details or {},
    }


def _migration_map_paths(repo_paths: dict[str, Path]) -> list[tuple[str, Path]]:
    paths: list[tuple[str, Path]] = []
    for repo_name, repo_root in repo_paths.items():
        if not repo_root.is_dir():
            continue
        for name in ("MIGRATION.map", "MIGRATION.map.yaml", "MIGRATION.map.json"):
            path = repo_root / name
            if path.is_file():
                paths.append((repo_name, path))
    return sorted(paths)


def _migration_ids_from_text(text: str) -> set[str]:
    valid: set[str] = set()
    for match in re.finditer(r"(?m)^\s*-?\s*id:\s*([^\s#]+)\s*$", text):
        legacy_id = match.group(1).strip().strip('"\'')
        if legacy_id:
            valid.update({legacy_id, f"agent-skills:{legacy_id}", f"agent-skills/{legacy_id}"})
    for match in re.finditer(r"(?m)^\s*target_id:\s*([^\s#]+)\s*$", text):
        target_id = match.group(1).strip().strip('"\'')
        if target_id:
            valid.add(target_id)
            if "/skills/" in target_id:
                valid.add(target_id.replace("/skills/", "/", 1))
    return valid


def _migration_ids(repo_paths: dict[str, Path]) -> tuple[set[str], list[str]]:
    valid: set[str] = set()
    sources: list[str] = []
    for repo_name, path in _migration_map_paths(repo_paths):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        valid.update(_migration_ids_from_text(text))
        sources.append(f"{repo_name}/{path.name}")
    return valid, sources


def _valid_absorbed_refs(aggregate: dict[str, Any], repo_paths: dict[str, Path]) -> tuple[set[str], list[str]]:
    package_ids = {
        package.get("id")
        for package in aggregate.get("packages", [])
        if isinstance(package, dict) and isinstance(package.get("id"), str)
    }
    migration_ids, sources = _migration_ids(repo_paths)
    return set(package_ids) | migration_ids, sources


def check(aggregate: dict[str, Any], repos: dict[str, Any]) -> list[dict[str, Any]]:
    repo_paths = _repo_paths(repos)
    valid_absorbed_refs, migration_sources = _valid_absorbed_refs(aggregate, repo_paths)
    findings: list[dict[str, Any]] = []

    for package in aggregate.get("packages", []):
        if not isinstance(package, dict):
            continue
        provenance = package.get("provenance")
        if not isinstance(provenance, dict):
            if package.get("owner_repo") == "craft-skills":
                findings.append(
                    _finding(
                        "provenance.craft_missing_provenance",
                        package,
                        "advisory",
                        "craft-skills package lacks a provenance object.",
                    )
                )
            continue

        severity = _severity_for_profile(package, "provenance_license")
        if severity is not None:
            upstream = provenance.get("upstream")
            license_value = provenance.get("license")
            if isinstance(upstream, str) and upstream and not (isinstance(license_value, str) and license_value.strip()):
                findings.append(
                    _finding(
                        "provenance.upstream_license_missing",
                        package,
                        severity,
                        "Package provenance declares an upstream but does not declare a license.",
                        {"upstream": upstream},
                    )
                )

        absorbed_from = provenance.get("absorbed_from")
        if isinstance(absorbed_from, list):
            unknown_refs = [ref for ref in absorbed_from if isinstance(ref, str) and ref not in valid_absorbed_refs]
            external_refs = [
                ref
                for ref in unknown_refs
                if repos.get("profile") == "portable" and ref.partition("/")[0] not in repo_paths
            ]
            if external_refs:
                findings.append(
                    _finding(
                        "provenance.absorbed_from_unresolved",
                        package,
                        "advisory",
                        "provenance.absorbed_from references an unavailable external repository in the portable profile.",
                        {"unknown_refs": sorted(external_refs), "migration_sources": migration_sources},
                    )
                )
            unknown_refs = [ref for ref in unknown_refs if ref not in external_refs]
            if unknown_refs:
                findings.append(
                    _finding(
                        "provenance.absorbed_from_unresolved",
                        package,
                        "blocking",
                        "provenance.absorbed_from references must exist in the aggregate or a MIGRATION.map entry.",
                        {"unknown_refs": sorted(unknown_refs), "migration_sources": migration_sources},
                    )
                )

    return findings


def run(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    return check(aggregate, config)
