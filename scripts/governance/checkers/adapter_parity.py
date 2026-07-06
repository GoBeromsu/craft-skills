"""Adapter parity checker for OMS adapter-wrapper manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CHECKER_NAME = "adapter_parity"
CHECKER_VERSION = "1"
OMS_REPO = "oh-my-secondbrain"
RUNTIME_HOSTS = {"claude-code", "codex", "hermes"}
PLUGIN_RELATIVE = {
    "claude-code": Path(".claude-plugin") / "plugin.json",
    "codex": Path(".codex-plugin") / "plugin.json",
}


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


def _normalize_adapters(package: dict[str, Any]) -> list[dict[str, Any]]:
    adapters = package.get("adapters")
    if isinstance(adapters, dict):
        values = adapters.values()
    elif isinstance(adapters, list):
        values = adapters
    else:
        return []
    return [adapter for adapter in values if isinstance(adapter, dict)]


def _relative_adapter_parts(package: dict[str, Any]) -> tuple[str, str] | None:
    package_id = package.get("id")
    if not isinstance(package_id, str):
        return None
    prefix = f"{OMS_REPO}/adapters/"
    if not package_id.startswith(prefix):
        return None
    parts = package_id[len(prefix) :].split("/", 1)
    if len(parts) != 2 or parts[0] not in RUNTIME_HOSTS or not parts[1]:
        return None
    return parts[0], parts[1]


def _skill_dirs(adapter_root: Path) -> set[str]:
    skills_root = adapter_root / "skills"
    if not skills_root.is_dir():
        return set()
    return {child.name for child in skills_root.iterdir() if child.is_dir() and (child / "SKILL.md").is_file()}


def _load_plugin_skills(plugin_path: Path) -> set[str] | None:
    if not plugin_path.is_file():
        return None
    try:
        data = json.loads(plugin_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    skills = data.get("skills")
    if isinstance(skills, str):
        # A directory value means every child skill directory is exposed by convention.
        return {"*"}
    if not isinstance(skills, list):
        return set()
    exposed: set[str] = set()
    for entry in skills:
        if not isinstance(entry, str):
            continue
        normalized = entry.strip().rstrip("/")
        if not normalized:
            continue
        exposed.add(Path(normalized).name)
    return exposed


def _package_key(package: dict[str, Any]) -> str | None:
    package_id = package.get("id")
    return package_id if isinstance(package_id, str) else None


def _finding(
    code: str,
    package: dict[str, Any] | None,
    severity: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    package_id = _package_key(package or {})
    return {
        "checker": CHECKER_NAME,
        "code": code,
        "package": package_id,
        "package_id": package_id,
        "severity": severity,
        "message": message,
        "details": details or {},
    }


def _exemption_reason(package: dict[str, Any], code: str, runtime: str, skill: str) -> str | None:
    containers = [package.get("adapter_parity_exemptions"), package.get("exemptions")]
    for adapter in _normalize_adapters(package):
        containers.append(adapter.get("adapter_parity_exemptions"))
        containers.append(adapter.get("exemptions"))

    for container in containers:
        entries: list[Any]
        if isinstance(container, dict):
            entries = list(container.values())
        elif isinstance(container, list):
            entries = container
        else:
            continue
        for entry in entries:
            if isinstance(entry, str):
                if entry in {skill, f"{runtime}/{skill}", code}:
                    return entry
                continue
            if not isinstance(entry, dict):
                continue
            entry_code = entry.get("code")
            entry_runtime = entry.get("runtime")
            entry_skill = entry.get("skill") or entry.get("name") or entry.get("directory")
            if entry_code not in (None, code):
                continue
            if entry_runtime not in (None, runtime):
                continue
            if entry_skill not in (None, skill):
                continue
            reason = entry.get("reason")
            return reason if isinstance(reason, str) and reason else "declared exemption"
    return None


def _declared_wrapper_index(aggregate: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    declared: dict[tuple[str, str], dict[str, Any]] = {}
    for package in aggregate.get("packages", []):
        if not isinstance(package, dict):
            continue
        if package.get("owner_repo") != OMS_REPO or package.get("kind") != "adapter-wrapper":
            continue
        parts = _relative_adapter_parts(package)
        if parts is not None:
            declared[parts] = package
    return declared
def _adapter_skill_path(runtime: str, skill: str) -> str:
    return f"{OMS_REPO}/adapters/{runtime}/skills/{skill}"


def _plugin_path(runtime: str) -> str:
    return f"{OMS_REPO}/adapters/{runtime}/{PLUGIN_RELATIVE[runtime]}"



def check(aggregate: dict[str, Any], repos: dict[str, Any]) -> list[dict[str, Any]]:
    repo_paths = _repo_paths(repos)
    oms_root = repo_paths.get(OMS_REPO)
    findings: list[dict[str, Any]] = []
    if oms_root is None:
        return [
            _finding(
                "adapter_parity.repo_unresolved",
                None,
                "blocking",
                "oh-my-secondbrain repo path cannot be resolved from governance config.",
                {"repo": OMS_REPO},
            )
        ]

    declared = _declared_wrapper_index(aggregate)
    actual_by_runtime = {runtime: _skill_dirs(oms_root / "adapters" / runtime) for runtime in RUNTIME_HOSTS}
    plugin_by_runtime = {
        runtime: _load_plugin_skills(oms_root / "adapters" / runtime / relpath)
        for runtime, relpath in PLUGIN_RELATIVE.items()
    }

    for (runtime, skill), package in sorted(declared.items()):
        if _profile_value(package, "adapter_parity") == "skip":
            continue
        adapter_declarations = [adapter for adapter in _normalize_adapters(package) if adapter.get("runtime") == runtime]
        if not adapter_declarations:
            findings.append(
                _finding(
                    "adapter_parity.runtime_not_declared",
                    package,
                    "blocking",
                    "Adapter-wrapper id names a runtime that is not declared in adapters[].",
                    {"runtime": runtime, "skill": skill, "declared_adapters": _normalize_adapters(package)},
                )
            )
            continue

        active_declarations = [adapter for adapter in adapter_declarations if adapter.get("status") != "omitted"]
        if not active_declarations:
            if skill in actual_by_runtime.get(runtime, set()):
                findings.append(
                    _finding(
                        "adapter_parity.omitted_but_present",
                        package,
                        "advisory",
                        "Adapter is declared omitted but an adapter skill directory exists.",
                        {"runtime": runtime, "skill": skill, "path": _adapter_skill_path(runtime, skill)},
                    )
                )
            continue

        if skill not in actual_by_runtime.get(runtime, set()):
            findings.append(
                _finding(
                    "adapter_parity.missing_skill_directory",
                    package,
                    "blocking",
                    "Declared adapter-wrapper is missing its adapters/<host>/skills/<skill>/SKILL.md directory.",
                    {"runtime": runtime, "skill": skill, "expected_path": _adapter_skill_path(runtime, skill)},
                )
            )
            continue

        plugin_skills = plugin_by_runtime.get(runtime)
        if plugin_skills is not None and "*" not in plugin_skills and skill not in plugin_skills:
            exemption = _exemption_reason(package, "adapter_parity.plugin_skill_missing", runtime, skill)
            if exemption is None:
                findings.append(
                    _finding(
                        "adapter_parity.plugin_skill_missing",
                        package,
                        "advisory",
                        "Adapter skill directory exists and manifest declares exposure, but plugin.json skills does not expose it.",
                        {
                            "runtime": runtime,
                            "skill": skill,
                            "plugin_path": _plugin_path(runtime),
                            "plugin_skills": sorted(plugin_skills),
                        },
                    )
                )

    for runtime, actual_skills in sorted(actual_by_runtime.items()):
        for skill in sorted(actual_skills):
            if (runtime, skill) not in declared:
                findings.append(
                    _finding(
                        "adapter_parity.unmanifested_skill_directory",
                        None,
                        "blocking",
                        "Adapter skill directory exists without a matching adapter-wrapper package in the aggregate.",
                        {"runtime": runtime, "skill": skill, "path": _adapter_skill_path(runtime, skill)},
                    )
                )

    for runtime, plugin_skills in sorted(plugin_by_runtime.items()):
        if plugin_skills is None or "*" in plugin_skills:
            continue
        for skill in sorted(plugin_skills):
            if skill not in actual_by_runtime.get(runtime, set()):
                findings.append(
                    _finding(
                        "adapter_parity.plugin_skill_directory_missing",
                        None,
                        "blocking",
                        "plugin.json exposes an adapter skill directory that does not exist.",
                        {"runtime": runtime, "skill": skill, "plugin_path": _plugin_path(runtime)},
                    )
                )
            elif (runtime, skill) not in declared:
                findings.append(
                    _finding(
                        "adapter_parity.plugin_skill_unmanifested",
                        None,
                        "blocking",
                        "plugin.json exposes an adapter skill that lacks a matching adapter-wrapper package in the aggregate.",
                        {"runtime": runtime, "skill": skill, "plugin_path": _plugin_path(runtime)},
                    )
                )

    return findings


def run(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    return check(aggregate, config)
