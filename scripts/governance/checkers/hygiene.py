"""Private-data hygiene checker for public and mixed skill surfaces."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Iterable

CHECKER_NAME = "hygiene"
CHECKER_VERSION = "1"
PUBLIC_VISIBILITIES = {"public", "mixed"}
MANIFEST_REPOS = {"craft-skills", "agent-skills", "oh-my-secondbrain"}
TOKEN_FALSE_POSITIVE_MARKERS = (
    "${",
    "<",
    "PLACEHOLDER",
    "placeholder",
    "EXAMPLE",
    "example",
    "DUMMY",
    "dummy",
    "REDACTED",
    "redacted",
)

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("absolute_user_path", re.compile(r"/Users/[^\s`'\"),]+")),
    ("personal_name", re.compile(r"\bbeomsu\b", re.IGNORECASE)),
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    (
        "token_literal",
        re.compile(
            r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|glpat-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|AIza[0-9A-Za-z_-]{20,}|[A-Za-z0-9_]*(?:TOKEN|SECRET|API_KEY|PASSWORD)[A-Za-z0-9_]*\s*[:=]\s*['\"][^'\"]{8,}['\"])",
            re.IGNORECASE,
        ),
    ),
    ("env_file_reference", re.compile(r"(?<![A-Za-z0-9_])\.env(?:\.[A-Za-z0-9_-]+)?(?![A-Za-z0-9_])")),
)


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


def _package_key(package: dict[str, Any] | None) -> str | None:
    if not isinstance(package, dict):
        return None
    package_id = package.get("id")
    return package_id if isinstance(package_id, str) else None


def _finding(
    code: str,
    package: dict[str, Any] | None,
    message: str,
    details: dict[str, Any] | None = None,
    *,
    severity: str = "blocking",
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


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + len("\n---\n") :]


def _safe_fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _is_token_false_positive(value: str) -> bool:
    return any(marker in value for marker in TOKEN_FALSE_POSITIVE_MARKERS)


def _display_path(path: Path, repo_paths: dict[str, Path]) -> str:
    resolved = path.resolve()
    for repo_name, repo_root in sorted(repo_paths.items()):
        try:
            relative = resolved.relative_to(repo_root.resolve())
        except ValueError:
            continue
        return f"{repo_name}/{relative.as_posix()}"
    return path.name


def _scan_text(text: str, *, path: str, package: dict[str, Any] | None) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern_name, pattern in PATTERNS:
            for match in pattern.finditer(line):
                value = match.group(0)
                if pattern_name == "token_literal" and _is_token_false_positive(value):
                    continue
                severity = "advisory" if pattern_name == "env_file_reference" else "blocking"
                findings.append(
                    _finding(
                        f"hygiene.{pattern_name}",
                        package,
                        "Public or mixed package content contains private-data hygiene risk.",
                        {
                            "path": path,
                            "line": line_number,
                            "pattern": pattern_name,
                            "match_sha256_12": _safe_fingerprint(value),
                        },
                        severity=severity,
                    )
                )
    return findings


def _manifest_paths(repo_paths: dict[str, Path]) -> Iterable[tuple[str, Path]]:
    for repo_name in sorted(MANIFEST_REPOS):
        repo_root = repo_paths.get(repo_name)
        if repo_root is None:
            continue
        manifest_path = repo_root / "skills-manifest.yaml"
        if manifest_path.is_file():
            yield repo_name, manifest_path


def check(aggregate: dict[str, Any], repos: dict[str, Any]) -> list[dict[str, Any]]:
    repo_paths = _repo_paths(repos)
    findings: list[dict[str, Any]] = []
    scanned_package_skill_paths: set[tuple[str | None, Path]] = set()

    for package in aggregate.get("packages", []):
        if not isinstance(package, dict):
            continue
        if package.get("visibility") not in PUBLIC_VISIBILITIES:
            continue
        if package.get("owner_repo") == "bstack" and package.get("visibility") == "private":
            continue
        if _profile_value(package, "private_data_hygiene") == "skip":
            continue
        package_dir = _package_dir(package, repo_paths)
        if package_dir is None:
            continue
        skill_path = package_dir / "SKILL.md"
        package_id = _package_key(package)
        key = (package_id, skill_path)
        if key in scanned_package_skill_paths or not skill_path.is_file():
            continue
        scanned_package_skill_paths.add(key)
        try:
            body = _strip_frontmatter(skill_path.read_text(encoding="utf-8"))
        except OSError:
            continue
        findings.extend(_scan_text(body, path=_display_path(skill_path, repo_paths), package=package))

    for repo_name, manifest_path in _manifest_paths(repo_paths):
        try:
            text = manifest_path.read_text(encoding="utf-8")
        except OSError:
            continue
        findings.extend(
            _scan_text(
                text,
                path=_display_path(manifest_path, repo_paths),
                package={"id": f"{repo_name}/skills-manifest.yaml"},
            )
        )

    return findings


def run(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    return check(aggregate, config)
