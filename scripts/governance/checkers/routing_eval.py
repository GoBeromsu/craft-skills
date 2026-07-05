"""Deterministic routing smoke checker for skill trigger phrases."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CHECKER_NAME = "routing_eval"
CHECKER_VERSION = "1"

_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "into",
    "my",
    "of",
    "or",
    "please",
    "the",
    "this",
    "to",
}


def _repo_paths(config: dict[str, Any]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for repo in config.get("repos", []):
        if isinstance(repo, dict) and isinstance(repo.get("name"), str) and isinstance(repo.get("path"), str):
            paths[repo["name"]] = Path(repo["path"]).expanduser().resolve()
    return paths


def _package_dir(package: dict[str, Any], repos: dict[str, Path]) -> Path | None:
    owner_repo = package.get("owner_repo")
    package_id = package.get("id")
    if not isinstance(owner_repo, str) or not isinstance(package_id, str):
        return None
    repo_root = repos.get(owner_repo)
    if repo_root is None:
        return None

    prefix = f"{owner_repo}/"
    if not package_id.startswith(prefix):
        return None
    relative_id = package_id[len(prefix) :]

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
    return None


def _strip_comment_lines(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def _load_cases(craft_repo: Path) -> tuple[list[dict[str, Any]], Path, str | None]:
    cases_path = craft_repo / "docs" / "governance" / "routing-eval-cases.yaml"
    if not cases_path.is_file():
        return [], cases_path, "missing"
    try:
        data = json.loads(_strip_comment_lines(cases_path.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return [], cases_path, "invalid_json_compatible_yaml"
    cases = data.get("cases") if isinstance(data, dict) else None
    if not isinstance(cases, list):
        return [], cases_path, "invalid_cases"
    return [case for case in cases if isinstance(case, dict)], cases_path, None


def _frontmatter_fields(skill_path: Path) -> dict[str, str]:
    if not skill_path.is_file():
        return {}
    lines = skill_path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    frontmatter: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        frontmatter.append(line)

    fields: dict[str, str] = {}
    idx = 0
    while idx < len(frontmatter):
        line = frontmatter[idx]
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            idx += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        if key not in {"name", "description"}:
            idx += 1
            continue
        if value in {">", ">-", "|", "|-"}:
            collected: list[str] = []
            idx += 1
            while idx < len(frontmatter) and (frontmatter[idx].startswith(" ") or frontmatter[idx].startswith("\t") or not frontmatter[idx].strip()):
                collected.append(frontmatter[idx].strip())
                idx += 1
            fields[key] = " ".join(collected).strip()
            continue
        fields[key] = value.strip().strip('"').strip("'")
        idx += 1
    return fields


def _tokens(text: str) -> set[str]:
    return {token for token in (match.group(0).lower() for match in _TOKEN_RE.finditer(text)) if len(token) > 1 and token not in _STOPWORDS}


def _score(trigger: str, fields: dict[str, str]) -> dict[str, Any]:
    trigger_tokens = _tokens(trigger)
    skill_tokens = _tokens(" ".join(value for value in fields.values() if isinstance(value, str)))
    overlap = sorted(trigger_tokens & skill_tokens)
    return {
        "score": len(overlap),
        "overlap": overlap,
        "trigger_tokens": sorted(trigger_tokens),
    }


def _finding(
    code: str,
    severity: str,
    message: str,
    package_id: str | None,
    path: Path | None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "checker": CHECKER_NAME,
        "severity": severity,
        "code": code,
        "package": package_id,
        "package_id": package_id,
        "message": message,
        "path": str(path) if path is not None else None,
        "details": details or {},
    }


def check(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    repos = _repo_paths(config)
    craft_repo = repos.get("craft-skills")
    if craft_repo is None:
        return [
            _finding(
                "routing_eval.craft_repo_missing",
                "blocking",
                "craft-skills repo path is required to load routing-eval cases.",
                None,
                None,
            )
        ]

    cases, cases_path, cases_error = _load_cases(craft_repo)
    if cases_error is not None:
        return [
            _finding(
                f"routing_eval.cases_{cases_error}",
                "blocking",
                "routing-eval-cases.yaml must be present and JSON-compatible YAML.",
                None,
                cases_path,
            )
        ]

    packages = {package.get("id"): package for package in aggregate.get("packages", []) if isinstance(package, dict)}
    findings: list[dict[str, Any]] = []

    for index, case in enumerate(cases):
        trigger = case.get("trigger")
        expected_id = case.get("expected_package")
        forbidden_neighbors = case.get("forbidden_neighbors", [])
        if not isinstance(trigger, str) or not isinstance(expected_id, str) or not isinstance(forbidden_neighbors, list):
            findings.append(
                _finding(
                    "routing_eval.invalid_case",
                    "blocking",
                    "Routing eval case must declare trigger, expected_package, and forbidden_neighbors.",
                    expected_id if isinstance(expected_id, str) else None,
                    cases_path,
                    {"case_index": index},
                )
            )
            continue

        expected_package = packages.get(expected_id)
        if expected_package is None:
            findings.append(
                _finding(
                    "routing_eval.expected_package_missing",
                    "blocking",
                    "Expected package id from routing-eval case is absent from aggregate.",
                    expected_id,
                    cases_path,
                    {"case_index": index, "trigger": trigger},
                )
            )
            continue

        expected_dir = _package_dir(expected_package, repos)
        expected_skill = expected_dir / "SKILL.md" if expected_dir is not None else None
        expected_fields = _frontmatter_fields(expected_skill) if expected_skill is not None else {}
        expected_score = _score(trigger, expected_fields)
        if expected_score["score"] == 0:
            findings.append(
                _finding(
                    "routing_eval.expected_trigger_missing",
                    "blocking",
                    "Trigger tokens do not overlap the expected skill name/description frontmatter.",
                    expected_id,
                    expected_skill,
                    {"case_index": index, "trigger": trigger, **expected_score},
                )
            )
            continue

        neighbor_scores: list[dict[str, Any]] = []
        for neighbor_id in forbidden_neighbors:
            if not isinstance(neighbor_id, str):
                continue
            neighbor_package = packages.get(neighbor_id)
            if neighbor_package is None:
                findings.append(
                    _finding(
                        "routing_eval.forbidden_neighbor_missing",
                        "blocking",
                        "Forbidden neighbor id from routing-eval case is absent from aggregate.",
                        expected_id,
                        cases_path,
                        {"case_index": index, "trigger": trigger, "neighbor": neighbor_id},
                    )
                )
                continue
            neighbor_dir = _package_dir(neighbor_package, repos)
            neighbor_skill = neighbor_dir / "SKILL.md" if neighbor_dir is not None else None
            neighbor_score = _score(trigger, _frontmatter_fields(neighbor_skill) if neighbor_skill is not None else {})
            neighbor_scores.append({"package": neighbor_id, "path": str(neighbor_skill) if neighbor_skill else None, **neighbor_score})
            if neighbor_score["score"] > expected_score["score"]:
                findings.append(
                    _finding(
                        "routing_eval.forbidden_neighbor_stronger",
                        "blocking",
                        "Forbidden neighbor frontmatter matches the trigger more strongly than the expected skill.",
                        expected_id,
                        expected_skill,
                        {
                            "case_index": index,
                            "trigger": trigger,
                            "expected": expected_score,
                            "neighbor": neighbor_scores[-1],
                        },
                    )
                )

    return findings


def run(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    return check(aggregate, config)
