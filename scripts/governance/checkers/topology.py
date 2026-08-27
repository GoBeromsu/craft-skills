"""Topology checker for skill manifest package kinds."""

from __future__ import annotations

from pathlib import Path
from typing import Any

CHECKER_NAME = "topology"
CHECKER_VERSION = "2"

TOPOLOGY_KINDS = {"leaf", "thick", "area", "adapter-wrapper", "runtime-hook", "command"}
SKILL_DIRECTORY_KINDS = {"leaf", "thick", "area", "adapter-wrapper"}
FILE_SURFACE_KINDS = {"runtime-hook", "command"}


def _repo_paths(config: dict[str, Any]) -> dict[str, Path]:
    repos = config.get("repos", [])
    paths: dict[str, Path] = {}
    for repo in repos:
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


def _child_skill_dirs(package_dir: Path) -> list[str]:
    if not package_dir.is_dir():
        return []
    children: list[str] = []
    for child in package_dir.iterdir():
        if child.is_dir() and (child / "SKILL.md").is_file():
            children.append(child.name)
    return sorted(children)


def _declared_children(package: dict[str, Any]) -> list[str]:
    children = package.get("children", [])
    if not isinstance(children, list):
        return []
    return sorted(child for child in children if isinstance(child, str))


def _finding(
    package: dict[str, Any],
    severity: str,
    code: str,
    message: str,
    package_path: Path | None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "checker": CHECKER_NAME,
        "severity": severity,
        "code": code,
        "package_id": package.get("id"),
        "message": message,
        "path": str(package_path) if package_path is not None else None,
        "details": details or {},
    }


def _check_declared_child_diff(
    findings: list[dict[str, Any]],
    package: dict[str, Any],
    package_dir: Path,
    declared_children: list[str],
    child_dirs: list[str],
) -> None:
    declared_child_names = {child_id.rsplit("/", 1)[-1] for child_id in declared_children}
    child_dir_names = set(child_dirs)

    missing_children = [child_id for child_id in declared_children if child_id.rsplit("/", 1)[-1] not in child_dir_names]
    if missing_children:
        findings.append(
            _finding(
                package,
                "blocking",
                "topology.declared_child_missing",
                "Declared child package ids do not match child SKILL.md directories.",
                package_dir,
                {"missing_children": missing_children, "child_skill_dirs": child_dirs},
            )
        )

    undeclared_child_dirs = sorted(child_dir_names - declared_child_names)
    if undeclared_child_dirs:
        findings.append(
            _finding(
                package,
                "advisory",
                "topology.child_directory_undeclared",
                "Child SKILL.md directories are not listed in children.",
                package_dir,
                {"undeclared_child_dirs": undeclared_child_dirs, "declared_children": declared_children},
            )
        )


def check(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    repos = _repo_paths(config)
    findings: list[dict[str, Any]] = []

    for package in aggregate.get("packages", []):
        if not isinstance(package, dict):
            continue
        kind = package.get("kind")
        if kind not in TOPOLOGY_KINDS:
            continue

        package_path = _package_path(package, repos)
        if package_path is None:
            findings.append(
                _finding(
                    package,
                    "blocking",
                    "topology.path_unresolved",
                    "Package path cannot be resolved from owner_repo and id.",
                    None,
                )
            )
            continue

        if kind in SKILL_DIRECTORY_KINDS:
            if not package_path.is_dir():
                findings.append(
                    _finding(
                        package,
                        "blocking",
                        "topology.missing_directory",
                        "Declared skill package directory does not exist.",
                        package_path,
                    )
                )
                continue
            if not (package_path / "SKILL.md").is_file():
                findings.append(
                    _finding(
                        package,
                        "blocking",
                        "topology.missing_skill",
                        "Declared skill package lacks SKILL.md.",
                        package_path,
                    )
                )
                continue
        elif not package_path.exists():
            findings.append(
                _finding(
                    package,
                    "blocking",
                    "topology.missing_surface",
                    "Declared command/runtime-hook surface path does not exist.",
                    package_path,
                    {"kind": kind},
                )
            )
            continue

        is_directory = package_path.is_dir()
        has_resolver = is_directory and (package_path / "RESOLVER.md").is_file()
        child_dirs = _child_skill_dirs(package_path) if is_directory else []
        declared_children = _declared_children(package)

        if kind == "area" and not has_resolver:
            findings.append(
                _finding(
                    package,
                    "blocking",
                    "topology.area_missing_resolver",
                    "kind=area requires RESOLVER.md.",
                    package_path,
                    {"child_skill_dirs": child_dirs},
                )
            )
        if kind != "area" and has_resolver:
            findings.append(
                _finding(
                    package,
                    "blocking",
                    "topology.resolver_kind_mismatch",
                    "RESOLVER.md is present but kind is not area.",
                    package_path,
                    {"declared_kind": kind},
                )
            )

        if kind == "leaf" and child_dirs:
            findings.append(
                _finding(
                    package,
                    "blocking",
                    "topology.leaf_has_child_skills",
                    "kind=leaf must not contain child SKILL.md directories.",
                    package_path,
                    {"child_skill_dirs": child_dirs},
                )
            )

        if kind in {"area", "thick"}:
            _check_declared_child_diff(findings, package, package_path, declared_children, child_dirs)
            if kind == "area" and len(declared_children) < 2:
                findings.append(
                    _finding(
                        package,
                        "blocking",
                        "topology.area_children_too_few",
                        "kind=area requires at least two declared children.",
                        package_path,
                        {"declared_children": declared_children},
                    )
                )
            if kind == "thick" and not child_dirs:
                findings.append(
                    _finding(
                        package,
                        "advisory",
                        "topology.thick_without_child_skills",
                        "kind=thick is declared but no child SKILL.md directories were found.",
                        package_path,
                    )
                )

        if kind == "adapter-wrapper":
            if declared_children:
                findings.append(
                    _finding(
                        package,
                        "blocking",
                        "topology.adapter_wrapper_has_children",
                        "kind=adapter-wrapper must not declare children.",
                        package_path,
                        {"declared_children": declared_children},
                    )
                )
            if child_dirs:
                findings.append(
                    _finding(
                        package,
                        "blocking",
                        "topology.adapter_wrapper_has_child_skills",
                        "kind=adapter-wrapper must not contain child SKILL.md directories.",
                        package_path,
                        {"child_skill_dirs": child_dirs},
                    )
                )

        if kind in FILE_SURFACE_KINDS:
            if declared_children:
                findings.append(
                    _finding(
                        package,
                        "blocking",
                        f"topology.{kind.replace('-', '_')}_has_children",
                        f"kind={kind} must not declare children.",
                        package_path,
                        {"declared_children": declared_children},
                    )
                )
            if child_dirs:
                findings.append(
                    _finding(
                        package,
                        "blocking",
                        f"topology.{kind.replace('-', '_')}_has_child_skills",
                        f"kind={kind} must not contain child SKILL.md directories.",
                        package_path,
                        {"child_skill_dirs": child_dirs},
                    )
                )

    return findings


def run(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    return check(aggregate, config)
