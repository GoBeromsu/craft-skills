#!/usr/bin/env python3
"""Require changed skill packages to have a semver bump and changelog entry."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

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


def _git_output(root: Path, *args: str) -> bytes:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        detail = os.fsdecode(getattr(exc, "stderr", b"") or b"").strip()
        raise VersionCheckError(f"git {' '.join(args)!r} failed: {detail or exc}") from exc


def _git_worktree_root(root: Path) -> Path:
    reported = os.fsdecode(_git_output(root, "rev-parse", "--show-toplevel").removesuffix(b"\n"))
    git_root = Path(reported)
    if git_root.resolve() != root.resolve():
        raise VersionCheckError("requested root must identify the Git worktree root")
    return git_root


def _verify_commit(root: Path, diff_base: str) -> str:
    if not diff_base or diff_base.startswith("-") or ".." in diff_base:
        raise VersionCheckError("--diff-base requires one commit-ish, not a range or option")
    return _git_output(
        root, "rev-parse", "--verify", "--end-of-options", diff_base + "^{commit}",
    ).decode().strip()


def _changed_relpaths(root: Path, base: str) -> set[str]:
    changed: set[str] = set()
    head = _git_output(root, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    for args in (
        ("diff", "--name-only", "-z", "--no-renames", base, head),
        ("diff", "--cached", "--name-only", "-z", "--no-renames", head),
        ("diff", "--name-only", "-z", "--no-renames"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
    ):
        for raw in _git_output(root, *args).split(b"\0"):
            if not raw:
                continue
            value = os.fsdecode(raw)
            path = PurePosixPath(value)
            if (not value or "\0" in value or path.is_absolute()
                    or ".." in path.parts or path.as_posix() != value):
                raise VersionCheckError(f"noncanonical repository path: {value!r}")
            changed.add(value)
    return changed


def _package_from_path(relative: str) -> str | None:
    parts = PurePosixPath(relative).parts
    if len(parts) >= 3 and parts[0] == "skills":
        if parts[2] == "tests":
            return None
        return parts[1]
    return None


def _changed_packages(changed: set[str]) -> set[str]:
    packages: set[str] = set()
    for relative in changed:
        package = _package_from_path(relative)
        if package:
            packages.add(package)
    return packages


def _root_plugin_manifest_changed(changed: set[str]) -> bool:
    return any(relative in changed for relative in _ROOT_PLUGIN_MANIFESTS)


def _git_show(root: Path, revision: str, path: str) -> str | None:
    process = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if process.returncode:
        return None
    try:
        return process.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VersionCheckError(f"unreadable git object {revision}:{path}: {exc}") from exc


def _contained_live_path(root: Path, path: Path) -> Path | None:
    """Resolve and contain a live path before any content read."""
    try:
        if not path.exists() and not path.is_symlink():
            return None
        resolved = path.resolve()
        if not resolved.is_relative_to(root.resolve()):
            raise VersionCheckError(f"path escapes root: {path}")
        if not resolved.exists():
            return None
        return resolved
    except OSError as exc:
        raise VersionCheckError(f"unreadable path {path}: {exc}") from exc


def _read_text(root: Path, path: Path) -> str | None:
    contained = _contained_live_path(root, path)
    if contained is None:
        return None
    try:
        return contained.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise VersionCheckError(f"unreadable path {path}: {exc}") from exc


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
        current_text = _read_text(root, root / relative)
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


def _has_substantive_change(root: Path, base: str, package: str, changed: set[str]) -> bool:
    prefix = f"skills/{package}/"
    for relative in changed:
        if relative != f"skills/{package}" and not relative.startswith(prefix):
            continue
        path = PurePosixPath(relative)
        if path.name == "CHANGELOG.md":
            continue
        if path.name != "SKILL.md":
            return True
        base_text = _git_show(root, base, relative)
        current_text = _read_text(root, root / relative)
        if base_text is None or current_text is None or _without_version(base_text) != _without_version(current_text):
            return True
    return False


def _former_skill_owner(root: Path, base: str, package: str) -> bool:
    return _git_show(root, base, f"skills/{package}/SKILL.md") is not None


def check(root: Path, diff_base: str) -> tuple[list[str], list[str]]:
    root = root.resolve()
    if not root.is_dir():
        raise VersionCheckError("repository root must be an existing directory")
    _git_worktree_root(root)
    base = _verify_commit(root, diff_base)
    changed = _changed_relpaths(root, base)
    violations: list[str] = []
    notes: list[str] = []
    changed_packages = _changed_packages(changed)
    if changed_packages or _root_plugin_manifest_changed(changed):
        violations.extend(_root_plugin_violations(root, base))
    for package in sorted(changed_packages):
        skill_path = root / "skills" / package / "SKILL.md"
        current_skill = _read_text(root, skill_path)
        base_skill = _git_show(root, base, f"skills/{package}/SKILL.md")
        if current_skill is None:
            if base_skill is None:
                violations.append(f"{package}: missing SKILL.md with no Git-established former owner")
                continue
            remnants = [
                relative for relative in changed
                if relative == f"skills/{package}" or relative.startswith(f"skills/{package}/")
            ]
            live = skill_path.parent
            if live.exists() and any(live.rglob("*")):
                violations.append(f"{package}: retired package still has remnant files")
                continue
            if remnants and all(
                not (root / relative).exists()
                for relative in remnants
            ) and not live.exists():
                notes.append(f"{package}: retired package with Git-established former owner")
                continue
            violations.append(f"{package}: incomplete retirement")
            continue

        new_version = _version_from_skill(current_skill)
        new_semver = _parse_semver(new_version) if new_version else None
        if new_semver is None:
            violations.append(f"{package}: metadata.version is not valid semver")

        changelog_path = root / "skills" / package / "CHANGELOG.md"
        current_changelog = _read_text(root, changelog_path) or ""
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
            if not _has_substantive_change(root, base, package, changed):
                violations.append(f"{package}: version bump has no package content change")
    return violations, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--diff-base",
        default="HEAD",
        help="single verified commit; unions committed/staged/unstaged/untracked package changes",
    )
    args = parser.parse_args()
    try:
        violations, notes = check(Path.cwd(), args.diff_base)
    except VersionCheckError as error:
        print(f"check_version_bump: {error}")
        return 2
    for note in notes:
        print(f"check_version_bump: note: {note}")
    if violations:
        for violation in violations:
            print(f"check_version_bump: {violation}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
