"""Deprecation and archive-safety checker for skill manifests."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

CHECKER_NAME = "deprecation"
CHECKER_VERSION = "1"
DEPRECATED_LIFECYCLES = {"deprecated", "archived"}
ARCHIVE_PARTS = {"archive", "archived"}


def _repo_paths(config: dict[str, Any]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for repo in config.get("repos", []):
        if isinstance(repo, dict) and isinstance(repo.get("name"), str) and isinstance(repo.get("path"), str):
            paths[repo["name"]] = Path(repo["path"]).expanduser().resolve()
    return paths


def _relative_id(package: dict[str, Any]) -> tuple[str, str] | None:
    owner_repo = package.get("owner_repo")
    package_id = package.get("id")
    if not isinstance(owner_repo, str) or not isinstance(package_id, str):
        return None
    prefix = f"{owner_repo}/"
    if not package_id.startswith(prefix):
        return None
    return owner_repo, package_id[len(prefix) :]


def _package_path(package: dict[str, Any], repos: dict[str, Path]) -> Path | None:
    relative = _relative_id(package)
    if relative is None:
        return None
    owner_repo, relative_id = relative
    repo_root = repos.get(owner_repo)
    if repo_root is None:
        return None
    if owner_repo in {"craft-skills", "bstack"}:
        return repo_root / "skills" / relative_id
    if owner_repo == "oh-my-secondbrain":
        if relative_id.startswith("core/"):
            return repo_root / "core" / "skills" / relative_id[len("core/") :]
        if relative_id.startswith("adapters/"):
            parts = relative_id.split("/", 2)
            if len(parts) == 3:
                _, runtime, adapter_name = parts
                return repo_root / "adapters" / runtime / "skills" / adapter_name
    if owner_repo == "agent-skills":
        return repo_root / "skills" / relative_id
    return repo_root / relative_id


def _archive_reference(value: str) -> bool:
    parts = [part for part in re.split(r'[/:""]', value.lower()) if part]
    return any(part in ARCHIVE_PARTS for part in parts)


def _has_tombstone(package: dict[str, Any]) -> bool:
    for field in ("tombstone", "deprecation"):
        value = package.get(field)
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, dict):
            for text_field in ("reason", "description", "tombstone", "note"):
                text = value.get(text_field)
                if isinstance(text, str) and text.strip():
                    return True
    return False


def _replacement_values(package: dict[str, Any]) -> list[str]:
    value = package.get("replaced_by")
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _target_package_candidates(target_id: str, repos: dict[str, Path]) -> set[str]:
    candidates = {target_id}
    parts = target_id.split("/", 2)
    if len(parts) >= 3 and parts[0] in repos and parts[1] == "skills":
        candidates.add(f"{parts[0]}/{parts[2]}")
    return candidates


def _target_path(target_id: str, repos: dict[str, Path]) -> Path | None:
    parts = target_id.split("/", 1)
    if len(parts) != 2:
        return None
    repo_root = repos.get(parts[0])
    if repo_root is None:
        return None
    return repo_root / parts[1]


def _parse_migration_entries(path: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return entries

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        start_match = re.match(r"^-\s+id:\s*(.+?)\s*$", stripped)
        if start_match:
            if current is not None:
                entries.append(current)
            current = {"id": _clean_scalar(start_match.group(1))}
            continue
        if current is None:
            continue
        field_match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.+?)\s*$", stripped)
        if field_match:
            field, value = field_match.groups()
            if field in {"disposition", "target_id", "confidence"}:
                current[field] = _clean_scalar(value)
    if current is not None:
        entries.append(current)
    return entries


def _clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _migration_maps(repos: dict[str, Path]) -> list[Path]:
    paths: list[Path] = []
    for repo_root in repos.values():
        if not repo_root.is_dir():
            continue
        paths.extend(sorted(repo_root.rglob("MIGRATION.map.yaml")))
    return paths


def _finding(
    package: dict[str, Any] | None,
    severity: str,
    code: str,
    message: str,
    path: Path | None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "checker": CHECKER_NAME,
        "severity": severity,
        "code": code,
        "package_id": package.get("id") if isinstance(package, dict) else None,
        "message": message,
        "path": str(path) if path is not None else None,
        "details": details or {},
    }


def check(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    repos = _repo_paths(config)
    packages = [package for package in aggregate.get("packages", []) if isinstance(package, dict)]
    package_ids = {package["id"] for package in packages if isinstance(package.get("id"), str)}
    package_by_id = {package["id"]: package for package in packages if isinstance(package.get("id"), str)}
    findings: list[dict[str, Any]] = []

    for package in packages:
        lifecycle = package.get("lifecycle")
        package_path = _package_path(package, repos)
        replacements = _replacement_values(package)

        if lifecycle in DEPRECATED_LIFECYCLES:
            if not replacements and not _has_tombstone(package):
                findings.append(
                    _finding(
                        package,
                        "blocking",
                        "deprecation.missing_replacement_or_tombstone",
                        "Deprecated/archived packages require replaced_by or a tombstone explanation.",
                        package_path,
                        {"lifecycle": lifecycle},
                    )
                )
            for replacement in replacements:
                if replacement not in package_ids:
                    findings.append(
                        _finding(
                            package,
                            "blocking",
                            "deprecation.replacement_missing",
                            "replaced_by points to a package id absent from the aggregate.",
                            package_path,
                            {"replaced_by": replacement},
                        )
                    )
        elif lifecycle == "active":
            package_id = package.get("id")
            archive_refs: list[str] = []
            if isinstance(package_id, str) and _archive_reference(package_id):
                archive_refs.append(package_id)
            if package_path is not None and any(part.lower() in ARCHIVE_PARTS for part in package_path.parts):
                archive_refs.append(str(package_path))
            provenance = package.get("provenance")
            if isinstance(provenance, dict):
                upstream = provenance.get("upstream")
                if isinstance(upstream, str) and _archive_reference(upstream):
                    archive_refs.append(upstream)
            if archive_refs:
                findings.append(
                    _finding(
                        package,
                        "blocking",
                        "deprecation.active_points_to_archive",
                        "Active package points at an archive-only path.",
                        package_path,
                        {"archive_references": sorted(set(archive_refs))},
                    )
                )

    for map_path in _migration_maps(repos):
        for entry in _parse_migration_entries(map_path):
            if entry.get("disposition") != "deprecated":
                continue
            target_id = entry.get("target_id")
            if not target_id:
                findings.append(
                    _finding(
                        None,
                        "blocking",
                        "deprecation.migration_deprecated_missing_target",
                        "MIGRATION.map.yaml deprecated entry lacks target_id.",
                        map_path,
                        {"legacy_id": entry.get("id")},
                    )
                )
                continue

            target_candidates = _target_package_candidates(target_id, repos)
            matched_package = next((package_by_id[candidate] for candidate in target_candidates if candidate in package_by_id), None)
            target_path = _target_path(target_id, repos)
            if matched_package is not None:
                matched_lifecycle = matched_package.get("lifecycle")
                if matched_lifecycle == "active":
                    findings.append(
                        _finding(
                            matched_package,
                            "blocking",
                            "deprecation.migration_deprecated_targets_active_package",
                            "MIGRATION.map.yaml deprecated entry points at an active package.",
                            _package_path(matched_package, repos),
                            {"legacy_id": entry.get("id"), "target_id": target_id, "migration_map": str(map_path)},
                        )
                    )
                continue
            if target_path is None or not target_path.exists():
                findings.append(
                    _finding(
                        None,
                        "blocking",
                        "deprecation.migration_deprecated_target_dangling",
                        "MIGRATION.map.yaml deprecated entry points to no manifest package or archive path.",
                        target_path or map_path,
                        {"legacy_id": entry.get("id"), "target_id": target_id, "migration_map": str(map_path)},
                    )
                )

    return findings


def run(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    return check(aggregate, config)
