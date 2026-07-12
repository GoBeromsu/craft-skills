"""Deterministic routing smoke checker for skill trigger phrases."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CHECKER_NAME = "routing_eval"
CHECKER_VERSION = "1"
_CASESETS_CONFIG_KEY = "routing_eval_casesets"
_COVERAGE_CONFIG_KEY = "routing_eval_coverage_path"
_DEFAULT_CASESETS = ["docs/governance/routing-eval-cases.yaml"]
_DEFAULT_COVERAGE_PATH = "docs/governance/routing-eval-coverage.json"
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


def _resolve_craft_path(craft_repo: Path, configured_path: str) -> Path:
    path = Path(configured_path)
    return path if path.is_absolute() else craft_repo / path


def _load_cases(craft_repo: Path, casesets: list[Any]) -> tuple[list[tuple[Any, Path]], Path | None, str | None]:
    loaded_cases: list[tuple[Any, Path]] = []
    for configured_path in casesets:
        if not isinstance(configured_path, str) or not configured_path:
            return [], None, "invalid_caseset_path"
        cases_path = _resolve_craft_path(craft_repo, configured_path)
        if not cases_path.is_file():
            return [], cases_path, "missing"
        try:
            data = json.loads(_strip_comment_lines(cases_path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            return [], cases_path, "invalid_json_compatible_yaml"
        cases = data.get("cases") if isinstance(data, dict) else None
        if not isinstance(cases, list):
            return [], cases_path, "invalid_cases"
        loaded_cases.extend((case, cases_path) for case in cases)
    return loaded_cases, None, None


def _load_coverage(craft_repo: Path, config: dict[str, Any]) -> tuple[set[str] | None, Path, str | None]:
    configured_path = config.get(_COVERAGE_CONFIG_KEY, _DEFAULT_COVERAGE_PATH)
    if not isinstance(configured_path, str) or not configured_path:
        return None, craft_repo / _DEFAULT_COVERAGE_PATH, "invalid_path"
    coverage_path = _resolve_craft_path(craft_repo, configured_path)
    if not coverage_path.is_file():
        return None, coverage_path, "missing"
    try:
        data = json.loads(_strip_comment_lines(coverage_path.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return None, coverage_path, "invalid_json"
    declared = data.get("expected_craft_packages") if isinstance(data, dict) and data.get("schemaVersion") == 1 else None
    if not isinstance(declared, list) or not all(isinstance(name, str) and name for name in declared):
        return None, coverage_path, "invalid_schema"
    return set(declared), coverage_path, None


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


def _case_is_valid(case: Any) -> bool:
    if not isinstance(case, dict):
        return False
    trigger = case.get("trigger")
    expected_id = case.get("expected_package")
    forbidden_neighbors = case.get("forbidden_neighbors")
    return (
        isinstance(trigger, str)
        and bool(trigger)
        and isinstance(expected_id, str)
        and bool(expected_id)
        and isinstance(forbidden_neighbors, list)
        and all(isinstance(neighbor, str) and neighbor for neighbor in forbidden_neighbors)
    )


def _craft_package_name(package_id: str) -> str | None:
    prefix = "craft-skills/"
    return package_id[len(prefix) :] if package_id.startswith(prefix) and package_id[len(prefix) :] else None


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

    casesets = config.get(_CASESETS_CONFIG_KEY, _DEFAULT_CASESETS)
    if not isinstance(casesets, list):
        return [
            _finding(
                "routing_eval.cases_invalid_casesets",
                "blocking",
                "routing-eval casesets must be a list of paths.",
                None,
                None,
            )
        ]
    cases, cases_path, cases_error = _load_cases(craft_repo, casesets)
    if cases_error is not None:
        return [
            _finding(
                f"routing_eval.cases_{cases_error}",
                "blocking",
                "Routing-eval casesets must be present and JSON-compatible YAML.",
                None,
                cases_path,
            )
        ]

    packages = {package.get("id"): package for package in aggregate.get("packages", []) if isinstance(package, dict)}
    active_repos = set(repos)
    findings: list[dict[str, Any]] = []
    craft_expected_packages: set[str] = set()

    for index, (case, source_path) in enumerate(cases):
        expected_id = case.get("expected_package") if isinstance(case, dict) else None
        if not _case_is_valid(case):
            findings.append(
                _finding(
                    "routing_eval.invalid_case",
                    "blocking",
                    "Routing eval case must declare non-empty trigger, expected_package, and string forbidden_neighbors.",
                    expected_id if isinstance(expected_id, str) else None,
                    source_path,
                    {"case_index": index},
                )
            )
            continue

        trigger = case["trigger"]
        expected_id = case["expected_package"]
        forbidden_neighbors = case["forbidden_neighbors"]
        craft_name = _craft_package_name(expected_id)
        if craft_name is not None:
            craft_expected_packages.add(craft_name)

        expected_package = packages.get(expected_id)
        if not isinstance(expected_package, dict) or expected_package.get("owner_repo") not in active_repos:
            findings.append(
                _finding(
                    "routing_eval.expected_package_missing",
                    "blocking",
                    "Expected package id from routing-eval case is absent from active repositories' aggregate.",
                    expected_id,
                    source_path,
                    {"case_index": index, "trigger": trigger},
                )
            )
            continue

        expected_dir = _package_dir(expected_package, repos)
        expected_skill = expected_dir / "SKILL.md" if expected_dir is not None else None
        expected_score = _score(trigger, _frontmatter_fields(expected_skill) if expected_skill is not None else {})
        if expected_score["score"] == 0:
            findings.append(
                _finding(
                    "routing_eval.expected_trigger_missing",
                    "advisory",
                    "Trigger tokens do not overlap the expected skill name/description frontmatter.",
                    expected_id,
                    expected_skill,
                    {"case_index": index, "trigger": trigger, **expected_score},
                )
            )
            continue

        for neighbor_id in forbidden_neighbors:
            neighbor_owner, _, _ = neighbor_id.partition("/")
            if config.get("profile", "portable") == "portable" and neighbor_owner not in active_repos:
                continue
            neighbor_package = packages.get(neighbor_id)
            if not isinstance(neighbor_package, dict) or neighbor_package.get("owner_repo") not in active_repos:
                findings.append(
                    _finding(
                        "routing_eval.forbidden_neighbor_missing",
                        "advisory",
                        "Forbidden neighbor id from routing-eval case is absent from active repositories' aggregate.",
                        expected_id,
                        source_path,
                        {"case_index": index, "trigger": trigger, "neighbor": neighbor_id},
                    )
                )
                continue
            neighbor_dir = _package_dir(neighbor_package, repos)
            neighbor_skill = neighbor_dir / "SKILL.md" if neighbor_dir is not None else None
            neighbor_score = _score(trigger, _frontmatter_fields(neighbor_skill) if neighbor_skill is not None else {})
            details = {
                "case_index": index,
                "trigger": trigger,
                "expected": expected_score,
                "neighbor": {"package": neighbor_id, "path": str(neighbor_skill) if neighbor_skill else None, **neighbor_score},
            }
            if neighbor_score["score"] > expected_score["score"]:
                findings.append(
                    _finding(
                        "routing_eval.forbidden_neighbor_stronger",
                        "advisory",
                        "Forbidden neighbor frontmatter matches the trigger more strongly than the expected skill.",
                        expected_id,
                        expected_skill,
                        details,
                    )
                )
            elif neighbor_score["score"] == expected_score["score"]:
                findings.append(
                    _finding(
                        "routing_eval.forbidden_neighbor_tie",
                        "advisory",
                        "Forbidden neighbor frontmatter ties the expected skill's trigger match.",
                        expected_id,
                        expected_skill,
                        details,
                    )
                )

    declared_coverage, coverage_path, coverage_error = _load_coverage(craft_repo, config)
    if coverage_error is not None:
        findings.append(
            _finding(
                "routing_eval.coverage_invalid",
                "blocking",
                "Routing-eval coverage declaration must be present and valid JSON.",
                None,
                coverage_path,
                {"error": coverage_error},
            )
        )
    elif declared_coverage != craft_expected_packages:
        findings.append(
            _finding(
                "routing_eval.coverage_mismatch",
                "blocking",
                "Declared craft package coverage does not match routing-eval casesets.",
                None,
                coverage_path,
                {
                    "declared": sorted(declared_coverage),
                    "cases": sorted(craft_expected_packages),
                    "missing_from_declaration": sorted(craft_expected_packages - declared_coverage),
                    "missing_from_cases": sorted(declared_coverage - craft_expected_packages),
                },
            )
        )
    return findings


def run(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    return check(aggregate, config)
