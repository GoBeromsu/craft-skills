"""Inventory parity checker for documented and plugin-listed skills."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CHECKER_NAME = "inventory_parity"
CHECKER_VERSION = "1"
SKILL_KINDS = {"leaf", "thick", "area"}
DOC_FILES = ("README.md", "AGENTS.md")
PLUGIN_DIRS = (".claude-plugin", ".codex-plugin", ".hermes")

_BACKTICK_CELL_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|")
_SKILL_PATH_RE = re.compile(r"\bskills/([a-z0-9][a-z0-9-]*)/SKILL\.md\b")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$", re.MULTILINE)


def _repo_paths(config: dict[str, Any]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for repo in config.get("repos", []):
        if isinstance(repo, dict) and isinstance(repo.get("name"), str) and isinstance(repo.get("path"), str):
            paths[repo["name"]] = Path(repo["path"]).expanduser().resolve()
    return paths


def _strip_comment_lines(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def _load_jsonish(path: Path) -> Any | None:
    try:
        return json.loads(_strip_comment_lines(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return None


def _repo_skill_names(aggregate: dict[str, Any], repo_name: str) -> set[str]:
    names: set[str] = set()
    for package in aggregate.get("packages", []):
        if not isinstance(package, dict):
            continue
        if package.get("owner_repo") != repo_name or package.get("kind") not in SKILL_KINDS:
            continue
        name = package.get("name")
        if isinstance(name, str) and name:
            names.add(name)
        else:
            package_id = package.get("id")
            if isinstance(package_id, str) and package_id.startswith(f"{repo_name}/"):
                names.add(package_id.rsplit("/", 1)[-1])
        children = package.get("children")
        if package.get("kind") == "area" and isinstance(children, list):
            for child in children:
                if isinstance(child, str) and child:
                    names.add(child.rsplit("/", 1)[-1])
    return names


def _declares_no_skills(text: str) -> bool:
    lowered = text.lower()
    return "no skills are currently published" in lowered or "currently intentionally empty" in lowered

def _is_skill_inventory_heading(level: int, title: str) -> bool:
    if level == 1:
        return False
    normalized = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", title.strip().lower())
    return normalized in {"skills", "skill inventory", "published skills", "current skills"}


def _skills_sections(text: str) -> list[str]:
    matches = list(_HEADING_RE.finditer(text))
    sections: list[str] = []
    for index, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2)
        if not _is_skill_inventory_heading(level, title):
            continue
        end = len(text)
        for next_match in matches[index + 1 :]:
            if len(next_match.group(1)) <= level:
                end = next_match.start()
                break
        sections.append(text[match.end() : end])
    return sections


def _extract_doc_skills(path: Path) -> tuple[set[str], bool]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set(), False

    skills: set[str] = set()
    for section in _skills_sections(text):
        for line in section.splitlines():
            match = _BACKTICK_CELL_RE.match(line.strip())
            if match:
                value = match.group(1).strip()
                if value.lower() != "skill":
                    skills.add(value)
    for match in _SKILL_PATH_RE.finditer(text):
        skills.add(match.group(1))
    return skills, _declares_no_skills(text)


def _extract_plugin_skills_from_value(value: Any) -> set[str] | None:
    if not isinstance(value, list):
        return None
    skills: set[str] = set()
    for item in value:
        candidate: str | None = None
        if isinstance(item, str):
            candidate = item
        elif isinstance(item, dict):
            for field in ("name", "id", "path", "directory"):
                field_value = item.get(field)
                if isinstance(field_value, str) and field_value:
                    candidate = field_value
                    break
        if candidate is None:
            continue
        candidate = candidate.strip().strip("/")
        path_match = re.search(r"(?:^|/)skills/([^/]+)(?:/SKILL\.md)?$", candidate)
        if path_match:
            candidate = path_match.group(1)
        elif "/" in candidate:
            candidate = candidate.rsplit("/", 1)[-1]
        if candidate:
            skills.add(candidate)
    return skills


def _extract_plugin_skills(path: Path) -> set[str] | None:
    data = _load_jsonish(path)
    if not isinstance(data, dict):
        return None
    if "skills" in data:
        return _extract_plugin_skills_from_value(data.get("skills"))
    plugin = data.get("plugin")
    if isinstance(plugin, dict) and "skills" in plugin:
        return _extract_plugin_skills_from_value(plugin.get("skills"))
    return None


def _finding(
    severity: str,
    code: str,
    message: str,
    repo_name: str,
    path: Path,
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "checker": CHECKER_NAME,
        "severity": severity,
        "code": code,
        "package_id": None,
        "message": message,
        "path": str(path),
        "details": {"repo": repo_name, **details},
    }


def _compare_inventory(
    findings: list[dict[str, Any]],
    *,
    repo_name: str,
    surface: str,
    path: Path,
    listed: set[str],
    manifest_names: set[str],
    severity: str,
) -> None:
    for missing in sorted(listed - manifest_names):
        findings.append(
            _finding(
                severity,
                f"inventory_parity.{surface}_skill_missing_manifest",
                f"{surface} lists a skill that is absent from skills-manifest.yaml.",
                repo_name,
                path,
                {"skill": missing, "surface": surface},
            )
        )
    for missing in sorted(manifest_names - listed):
        findings.append(
            _finding(
                severity,
                f"inventory_parity.manifest_skill_missing_{surface}",
                f"skills-manifest.yaml lists a skill absent from {surface}.",
                repo_name,
                path,
                {"skill": missing, "surface": surface},
            )
        )


def check(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    repos = _repo_paths(config)
    findings: list[dict[str, Any]] = []

    for repo_name, repo_root in sorted(repos.items()):
        manifest_names = _repo_skill_names(aggregate, repo_name)
        for doc_name in DOC_FILES:
            doc_path = repo_root / doc_name
            if not doc_path.is_file():
                continue
            listed, declares_empty = _extract_doc_skills(doc_path)
            if not listed and not declares_empty:
                continue
            _compare_inventory(
                findings,
                repo_name=repo_name,
                surface=doc_name.lower().replace(".md", ""),
                path=doc_path,
                listed=listed,
                manifest_names=manifest_names,
                severity="advisory",
            )

        for plugin_dir_name in PLUGIN_DIRS:
            plugin_dir = repo_root / plugin_dir_name
            if not plugin_dir.is_dir():
                continue
            for plugin_path in sorted(plugin_dir.glob("*.json")):
                listed = _extract_plugin_skills(plugin_path)
                if listed is None:
                    continue
                _compare_inventory(
                    findings,
                    repo_name=repo_name,
                    surface="plugin_manifest",
                    path=plugin_path,
                    listed=listed,
                    manifest_names=manifest_names,
                    severity="blocking",
                )

    return findings


def run(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    return check(aggregate, config)
