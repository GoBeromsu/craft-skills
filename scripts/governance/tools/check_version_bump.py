#!/usr/bin/env python3
"""Require changed skill packages to have a semver bump and changelog entry."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_DATE_BULLET = re.compile(r"^- \d{4}-\d{2}-\d{2}\b")
_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
_ROOT_PLUGIN_MANIFESTS = (
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
)


class VersionCheckError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class SemVer:
    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...]

    def __lt__(self, other: "SemVer") -> bool:
        core = (self.major, self.minor, self.patch)
        other_core = (other.major, other.minor, other.patch)
        if core != other_core:
            return core < other_core
        if not self.prerelease:
            return False
        if not other.prerelease:
            return True
        for left, right in zip(self.prerelease, other.prerelease):
            if left == right:
                continue
            left_numeric = left.isdigit()
            right_numeric = right.isdigit()
            if left_numeric and right_numeric:
                return int(left) < int(right)
            if left_numeric != right_numeric:
                return left_numeric
            return left < right
        return len(self.prerelease) < len(other.prerelease)


def _parse_semver(value: str) -> SemVer | None:
    match = _SEMVER.fullmatch(value.strip())
    if not match:
        return None
    prerelease = tuple(match.group(4).split(".")) if match.group(4) else ()
    return SemVer(int(match.group(1)), int(match.group(2)), int(match.group(3)), prerelease)


def _run_git(root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode:
        raise VersionCheckError(process.stderr.strip() or f"git {' '.join(args)} failed")
    return process.stdout


def _base_commit(root: Path, diff_base: str) -> str:
    if "..." in diff_base:
        left, right = diff_base.split("...", 1)
        if not left or not right:
            raise VersionCheckError(f"invalid symmetric diff range {diff_base!r}")
        return _run_git(root, "merge-base", left, right).strip()
    return _run_git(root, "rev-parse", diff_base).strip()


def _changed_packages(root: Path, diff_base: str) -> set[str]:
    changed = _run_git(root, "diff", "--name-only", diff_base)
    packages: set[str] = set()
    for path in changed.splitlines():
        parts = Path(path).parts
        if len(parts) >= 3 and parts[0] == "skills":
            packages.add(parts[1])
    return packages


def _root_plugin_manifest_changed(root: Path, diff_base: str) -> bool:
    changed = set(_run_git(root, "diff", "--name-only", diff_base).splitlines())
    return any(relative in changed for relative in _ROOT_PLUGIN_MANIFESTS)


def _git_show(root: Path, revision: str, path: str) -> str | None:
    process = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode:
        return None
    return process.stdout


def _version_from_skill(text: str) -> str | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        frontmatter_end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return None
    metadata_indent: int | None = None
    for line in lines[1:frontmatter_end]:
        metadata_match = re.match(r"^(\s*)metadata\s*:\s*$", line)
        if metadata_match:
            metadata_indent = len(metadata_match.group(1))
            continue
        version_match = re.match(r"^(\s*)version\s*:\s*([^#\s]+)\s*(?:#.*)?$", line)
        if version_match and metadata_indent is not None and len(version_match.group(1)) > metadata_indent:
            return version_match.group(2).strip('"\'')
    return None


def _version_from_plugin(text: str | None) -> str | None:
    if text is None:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    version = payload.get("version") if isinstance(payload, dict) else None
    return version if isinstance(version, str) else None


def _root_plugin_violations(root: Path, base: str) -> list[str]:
    violations: list[str] = []
    current_versions: dict[str, str] = {}
    base_versions: dict[str, str] = {}
    for relative in _ROOT_PLUGIN_MANIFESTS:
        current_path = root / relative
        current_text = current_path.read_text(encoding="utf-8") if current_path.exists() else None
        current_version = _version_from_plugin(current_text)
        base_version = _version_from_plugin(_git_show(root, base, relative))
        if current_version is None or _parse_semver(current_version) is None:
            violations.append(f"{relative}: root plugin version is not valid semver")
        else:
            current_versions[relative] = current_version
        if base_version is None or _parse_semver(base_version) is None:
            violations.append(f"{relative}: base root plugin version is not valid semver")
        else:
            base_versions[relative] = base_version

    if len(set(current_versions.values())) > 1:
        violations.append("root plugin versions must match")
    for relative in _ROOT_PLUGIN_MANIFESTS:
        current = _parse_semver(current_versions[relative]) if relative in current_versions else None
        previous = _parse_semver(base_versions[relative]) if relative in base_versions else None
        if current is not None and previous is not None and not previous < current:
            violations.append(f"{relative}: root plugin version must increase")
    return violations


def _dated_bullets(text: str) -> set[str]:
    return {line for line in text.splitlines() if _DATE_BULLET.match(line)}


def _without_version(text: str) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    try:
        frontmatter_end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return text
    metadata_indent: int | None = None
    kept: list[str] = []
    for index, line in enumerate(lines):
        if index <= frontmatter_end:
            metadata_match = re.match(r"^(\s*)metadata\s*:\s*$", line)
            if metadata_match:
                metadata_indent = len(metadata_match.group(1))
            version_match = re.match(r"^(\s*)version\s*:", line)
            if version_match and metadata_indent is not None and len(version_match.group(1)) > metadata_indent:
                continue
        kept.append(line)
    return "".join(kept)


def _has_substantive_change(root: Path, base: str, package: str) -> bool:
    changed = _run_git(root, "diff", "--name-only", base, "--", f"skills/{package}")
    for relative in changed.splitlines():
        path = Path(relative)
        if path.name == "CHANGELOG.md":
            continue
        if path.name != "SKILL.md":
            return True
        base_text = _git_show(root, base, relative)
        current_path = root / relative
        current_text = current_path.read_text(encoding="utf-8") if current_path.exists() else None
        if base_text is None or current_text is None or _without_version(base_text) != _without_version(current_text):
            return True
    return False


def check(root: Path, diff_base: str) -> tuple[list[str], list[str]]:
    base = _base_commit(root, diff_base)
    violations: list[str] = []
    notes: list[str] = []
    changed_packages = _changed_packages(root, diff_base)
    if changed_packages or _root_plugin_manifest_changed(root, diff_base):
        violations.extend(_root_plugin_violations(root, base))
    for package in sorted(changed_packages):
        skill_path = root / "skills" / package / "SKILL.md"
        current_skill = skill_path.read_text(encoding="utf-8") if skill_path.exists() else None
        base_skill = _git_show(root, base, f"skills/{package}/SKILL.md")
        if current_skill is None:
            violations.append(f"{package}: SKILL.md is missing")
            continue

        new_version = _version_from_skill(current_skill)
        new_semver = _parse_semver(new_version) if new_version else None
        if new_semver is None:
            violations.append(f"{package}: metadata.version is not valid semver")

        changelog_path = root / "skills" / package / "CHANGELOG.md"
        current_changelog = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
        base_changelog = _git_show(root, base, f"skills/{package}/CHANGELOG.md") or ""
        if not _dated_bullets(current_changelog) - _dated_bullets(base_changelog):
            violations.append(f"{package}: CHANGELOG.md must gain a dated bullet")

        if base_skill is None:
            notes.append(f"{package}: new package (no base SKILL.md)")
            continue

        old_version = _version_from_skill(base_skill)
        old_semver = _parse_semver(old_version) if old_version else None
        if old_semver is None:
            violations.append(f"{package}: base metadata.version is not valid semver")
        elif new_semver is not None and not old_semver < new_semver:
            violations.append(f"{package}: metadata.version must increase ({old_version} -> {new_version})")
        if old_semver is not None and new_semver is not None and old_semver < new_semver:
            if not _has_substantive_change(root, base, package):
                violations.append(f"{package}: version bump has no package content change")
    return violations, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diff-base", default="origin/main...HEAD", help="git diff range or base ref")
    args = parser.parse_args()
    try:
        violations, notes = check(Path.cwd(), args.diff_base)
    except VersionCheckError as error:
        print(f"check_version_bump: {error}")
        return 1
    for note in notes:
        print(f"check_version_bump: note: {note}")
    if violations:
        for violation in violations:
            print(f"check_version_bump: {violation}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
