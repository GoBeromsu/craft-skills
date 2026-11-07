#!/usr/bin/env python3
"""Validate craft-skills skill-package format against the repository conventions
in `AGENTS.md`.

Each skill package is a single directory `skills/<skill-name>/` containing at
least `SKILL.md`. Package history stays in git. This validator enforces, per package:

  1. Every Agent Skills specification rule (frontmatter syntax and keys,
     `name`, `description` including its length limit, `compatibility`)
     through the official linter `skills_ref.validate` (pinned in
     scripts/governance/requirements.txt); each message is `AGENT_SKILLS_SPEC`.
     No local rule duplicates the linter.
  2. Local: `metadata` is a present mapping (`NO_METADATA`, `BAD_METADATA`) and
     `metadata.version` is semver `MAJOR.MINOR.PATCH` (`NO_VERSION`, `BAD_VERSION`).
  3. Local: SKILL.md contains no `## Change Log` (`CHANGELOG_IN_SKILL`).
  4. Local: no tracked real `.env` file in the package (`TRACKED_ENV`).
  5. Local: no markdown link climbs out of the package with `../`
     (`TRAVERSAL_LINK`; the Hermes tap fetcher aborts on such a path).
  6. Local: Git-visible top-level entries are only the directories `scripts/`,
     `references/`, `assets/`, `templates/`, `agents/` and the files `SKILL.md`,
     `.env.example`, `env.example` (`DISALLOWED_PACKAGE_ENTRY`).
  7. Local: no directory named `tests` anywhere in the package (`TESTS_IN_PACKAGE`).
  8. Local, --diff-base only: a removed package leaves no files
     (`INCOMPLETE_RETIREMENT`) and no live references (`DANGLING_PACKAGE_REFERENCE`).

Only top-level `skills/<name>/SKILL.md` files define packages. Paths the body
mentions are not resolved, and body length or typography is not a format check.

Modes:
  (default)       full scan; reports every violation; exit 1 if any hard error found.
  --diff-base REF select the union of committed, staged, unstaged and untracked
                  package/support changes against one commit, not a revision range.
  --package PATH select an existing skills/<owner> directory; repeatable and
                  additive to --diff-base, never a glob or an escaping path.
  --advisory      report format findings without failing; input/Git errors exit 2.

This validator owns FORMAT only. Secret/real-path leakage is owned by
validate_runtime_hygiene.py — keep the two concerns separate.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = REPO_ROOT / "skills"
TESTS_DIR = REPO_ROOT / "tests"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
CHANGE_LOG_HEADING_RE = re.compile(r"^## +Change Log\b", re.MULTILINE)
REAL_ENV_NAME_RE = re.compile(r"^\.env(?:\..+)?$")

ALLOWED_PACKAGE_DIRS = frozenset({"scripts", "references", "assets", "templates", "agents"})
ALLOWED_PACKAGE_FILES = frozenset({"SKILL.md", ".env.example", "env.example"})

# Repository tools and CI need no skill owner.
# Exact files and directory prefixes; a path is in scope when it equals a
# file or starts with a prefix plus "/".
REPOSITORY_TOOL_FILES = frozenset({
    "AGENTS.md",
    "README.md",
    "scripts/ci-local.sh",
    ".codex/config.yaml",
    ".github/workflows/pr-check.yml",
    ".github/workflows/test-plugin-install.yml",
})
REPOSITORY_TOOL_PREFIXES = (
    "scripts/governance/",
    "tests/governance/",
    ".github/",
    ".codex/",
)


def require_skills_ref():
    """Import the official linter only when format checks run."""
    try:
        import skills_ref
    except ImportError:
        print("skill-format: missing the official linter; run "
              "`python3 -m pip install -r scripts/governance/requirements.txt`", file=sys.stderr)
        raise SystemExit(2)
    return skills_ref


@dataclass
class Finding:
    skill: str
    code: str
    detail: str


def tracked_env_files(skill_dir: Path) -> list[str]:
    rel = skill_dir.relative_to(REPO_ROOT).as_posix()
    return sorted(
        path for path in git_paths("ls-files", "-z", "--", rel)
        if PurePosixPath(path).name != ".env.example"
        and REAL_ENV_NAME_RE.match(PurePosixPath(path).name)
    )


def git_output(*args: str) -> bytes:
    """Read Git without shell parsing or silent input-error fallbacks."""
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        detail = os.fsdecode(getattr(exc, "stderr", b"") or b"").strip()
        raise ValueError(f"Git {' '.join(args)!r} failed: {detail or exc}") from exc


def safe_repo_path(value: str) -> Path:
    path = PurePosixPath(value)
    if (not value or "\0" in value or path.is_absolute()
            or ".." in path.parts or path.as_posix() != value):
        raise ValueError(f"noncanonical repository path: {value!r}")
    candidate = REPO_ROOT / path
    if candidate.relative_to(REPO_ROOT).as_posix() != value:
        raise ValueError(f"noncanonical repository path: {value!r}")
    if not candidate.resolve().is_relative_to(REPO_ROOT.resolve()):
        raise ValueError(f"repository path escapes root: {value!r}")
    return candidate


def git_paths(*args: str) -> set[str]:
    paths = {os.fsdecode(value) for value in git_output(*args).split(b"\0") if value}
    for value in paths:
        safe_repo_path(value)
    return paths


def package_owners(paths: set[str]) -> set[str]:
    return {
        str(PurePosixPath(path).parent)
        for path in paths
        if path.startswith("skills/") and path.endswith("/SKILL.md")
        and PurePosixPath(path).parent.parent.as_posix() == "skills"
    }


def nearest_owner(path: str, owners: set[str]) -> str | None:
    matches = [owner for owner in owners if path == owner or path.startswith(owner + "/")]
    return max(matches, key=len) if matches else None


def current_owners() -> set[str]:
    owners: set[str] = set()
    if not SKILLS_DIR.is_dir():
        return owners
    # A skills/ symlink (or link chain) must stay inside the repo before any listing or read.
    skills_root = SKILLS_DIR.resolve()
    repo_root = REPO_ROOT.resolve()
    if not skills_root.is_relative_to(repo_root):
        raise ValueError(f"skills/ escapes repository root: {skills_root}")
    # rglob does not traverse directory symlinks; reject escaping entries first.
    for entry in SKILLS_DIR.iterdir():
        if entry.is_symlink() and not entry.resolve().is_relative_to(skills_root):
            raise ValueError(f"skill path escapes skills/: {entry.relative_to(REPO_ROOT)}")
    for skill in SKILLS_DIR.glob("*/SKILL.md"):
        if not skill.resolve().is_relative_to(SKILLS_DIR.resolve()):
            raise ValueError(f"SKILL.md escapes skills/: {skill.relative_to(REPO_ROOT)}")
        owners.add(skill.parent.relative_to(REPO_ROOT).as_posix())
    return owners


def explicit_owner(value: str, owners: set[str]) -> str:
    path = PurePosixPath(value)
    candidate = safe_repo_path(value)
    if ("\\" in value or any(char in value for char in "*?[]") or not path.parts
            or path.parts[0] != "skills"):
        raise ValueError(f"invalid --package {value!r}: use a repository-relative skills/ owner")
    normalized = path.as_posix()
    if normalized not in owners:
        raise ValueError(f"--package {value!r} is not an existing SKILL.md owner")
    if not candidate.resolve().is_relative_to(SKILLS_DIR.resolve()):
        raise ValueError(f"--package {value!r} escapes skills/")
    return normalized


def is_repository_tool_path(rel: str) -> bool:
    """CI and repository tools need no skill owner."""
    if rel in REPOSITORY_TOOL_FILES or PurePosixPath(rel).parent == PurePosixPath("tests"):
        return True
    return any(rel == prefix[:-1] or rel.startswith(prefix) for prefix in REPOSITORY_TOOL_PREFIXES)


def _map_package_resource(rel: str) -> str:
    """Map a repo-root test tree onto its skill owner; leave other paths alone."""
    if rel == "tests" or rel.startswith("tests/"):
        return "skills/" + rel[len("tests/"):]
    return rel


def diff_union(base: str, head: str) -> set[str]:
    """Committed, staged, unstaged, and untracked paths. Not a revision range."""
    changed: set[str] = set()
    for args in (
        ("diff", "--name-only", "-z", "--no-renames", base, head),
        ("diff", "--cached", "--name-only", "-z", "--no-renames", head),
        ("diff", "--name-only", "-z", "--no-renames"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
    ):
        changed.update(git_paths(*args))
    return changed


def historical_owners(base: str, head: str) -> set[str]:
    """Owners visible at base, at HEAD, or in the index.

    A deletion commit removes the owner from HEAD and from the index. The
    base tree is the evidence that the removed package had a real owner.
    """
    return package_owners(
        git_paths("ls-tree", "-r", "--name-only", "-z", base)
        | git_paths("ls-tree", "-r", "--name-only", "-z", head)
        | git_paths("ls-files", "--cached", "-z")
    )


def has_package_consumer(text: str, suffix: str, removed: str) -> bool:
    """Recognize reference syntax, not every prose mention of an old owner."""
    reference = re.compile(
        r"(?:^|[\s`'\"(=])(?:\$\{?\w+\}?/)?"
        + re.escape(removed) + r"(?=/|[\s`'\"),#]|$)", re.MULTILINE,
    )
    invocation = re.compile(
        r"(?<![\w/-])/skill:" + re.escape(removed.removeprefix("skills/"))
        + r"(?=$|[\s`'\"),])",
    )
    if suffix == ".py":
        try:
            tree = ast.parse(text)
        except SyntaxError:
            # Malformed source must not hide an otherwise visible consumer.
            return bool(reference.search(text) or invocation.search(text))
        non_consumers: set[int] = set()
        for node in ast.walk(tree):
            # A negative assertion's literal expected value is checker data.
            # Do not skip the actual expression, which can still load a path.
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "assertNotIn" and node.args
                    and isinstance(node.args[0], ast.Constant)):
                non_consumers.add(id(node.args[0]))
            if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)):
                non_consumers.add(id(node.value))
        return any(
            isinstance(node, ast.Constant) and isinstance(node.value, str)
            and id(node) not in non_consumers
            and (reference.search(node.value) or invocation.search(node.value))
            for node in ast.walk(tree)
        )
    if suffix == ".md":
        # Links, inline code, and fenced commands are actionable references.
        # Plain prose (including a retirement narrative) is not a loader.
        for match in re.finditer(
            r"```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`\n]+`|"
            r"\]\(([^)\n]+)\)|^\s*\[[^\]\n]+\]:\s*(\S+)",
            text, re.MULTILINE,
        ):
            value = match.group(1) or match.group(2) or match.group()
            if reference.search(value) or invocation.search(value):
                return True
        return bool(invocation.search(text))
    return bool(reference.search(text) or invocation.search(text))


def select_packages(diff_base: str | None, packages: list[str]) -> tuple[list[Path], list[Finding]]:
    if not REPO_ROOT.is_dir():
        raise ValueError("repository root must be an existing directory")
    git_root = Path(os.fsdecode(git_output("rev-parse", "--show-toplevel").removesuffix(b"\n")))
    if git_root.resolve() != REPO_ROOT.resolve():
        raise ValueError("--root must identify the Git worktree root")
    if diff_base is None and not SKILLS_DIR.is_dir():
        raise ValueError("full or explicit scan requires a skills/ directory")
    owners = current_owners()
    selected = {explicit_owner(value, owners) for value in packages}
    findings: list[Finding] = []
    if diff_base is None:
        return [REPO_ROOT / owner for owner in sorted(selected if packages else owners)], findings
    if not diff_base or diff_base.startswith("-") or ".." in diff_base:
        raise ValueError("--diff-base requires one commit-ish, not a range or option")
    base = git_output("rev-parse", "--verify", "--end-of-options", diff_base + "^{commit}").decode().strip()
    head = git_output("rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    changed = diff_union(base, head)
    previous = historical_owners(base, head)
    tombstones: set[str] = set()
    for rel in sorted(changed):
        mapped = _map_package_resource(rel)
        owner = nearest_owner(mapped, owners)
        old_owner = nearest_owner(mapped, previous)
        if owner:
            selected.add(owner)
        if old_owner and old_owner not in owners:
            tombstones.add(old_owner)
        if owner or old_owner:
            continue
        if is_repository_tool_path(rel):
            print(f"scope: repository-tool {rel!r} (no skill owner required)")
            continue
        if not (REPO_ROOT / rel).exists():
            # A removed unowned file leaves nothing to validate.
            print(f"scope: removed {rel!r} (no skill owner)")
            continue
        if rel.startswith(("skills/", "tests/", "scripts/")):
            raise ValueError(f"unresolved package/support ownership for {rel!r}")
        print(f"scope: excluded {rel!r} (outside package-format ownership)")
    # Check current Git-visible references, not ignored runtime captures or archives.
    reference_paths = (
        git_paths("ls-files", "--cached", "--others", "--exclude-standard", "-z")
        if tombstones else set()
    )
    for removed in sorted(tombstones):
        print(f"scope: tombstone {removed}")
        for rel_root in (removed, "tests/" + removed.removeprefix("skills/")):
            directory = REPO_ROOT / rel_root
            if (directory.is_file() or directory.is_symlink()
                    or any(p.is_file() or p.is_symlink() for p in directory.rglob("*"))):
                findings.append(Finding(removed, "INCOMPLETE_RETIREMENT",
                                        f"SKILL.md was removed but files remain under {rel_root}"))
        for rel in sorted(reference_paths):
            parts = PurePosixPath(rel).parts
            if "archive" in parts or parts[0] in {".git", ".gjc"}:
                continue
            candidate = REPO_ROOT / rel
            if candidate.name == "CHANGELOG.md" or not candidate.is_file():
                continue
            if not candidate.resolve().is_relative_to(REPO_ROOT.resolve()):
                raise ValueError(f"reference file escapes repository: {candidate}")
            try:
                text = candidate.read_text(encoding="utf-8")
            except UnicodeError:
                continue
            if has_package_consumer(text, candidate.suffix, removed):
                mapped = _map_package_resource(rel)
                consumer = nearest_owner(mapped, owners)
                if consumer:
                    selected.add(consumer)
                findings.append(Finding(consumer or rel, "DANGLING_PACKAGE_REFERENCE",
                                        f"{rel} still references removed owner {removed}"))
    return [REPO_ROOT / owner for owner in sorted(selected)], findings


TRAVERSAL_LINK_RE = re.compile(
    r"\]\(\.\./|(?:references|templates|scripts|assets|examples)/(?:[^\s)`\"'<>]*/)?\.\.(?:/|$)"
)  # mirrors the Hermes tap fetcher's traversal abort


def check_traversal_link(name: str, body: str) -> list[Finding]:
    if not TRAVERSAL_LINK_RE.search(body):
        return []
    return [Finding(name, "TRAVERSAL_LINK",
                    "SKILL.md links climb out of the package with `../`; "
                    "the Hermes tap fetcher aborts the install on such a path "
                    "(AGENTS.md)")]


def check_package_entries(name: str, skill_dir: Path) -> list[Finding]:
    """Git-visible top-level entries must be on the package allowlist,
    and no directory anywhere in the package may be named `tests`."""
    rel = skill_dir.relative_to(REPO_ROOT).as_posix()
    entries: dict[str, bool] = {}
    test_dirs: set[str] = set()
    # Names only: entries are never resolved or read.
    listing = git_output("ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", rel)
    for path in (os.fsdecode(value) for value in listing.split(b"\0") if value):
        if not os.path.lexists(REPO_ROOT / path):
            continue  # an uncommitted deletion is no longer a package entry
        inner = path[len(rel) + 1:]
        top, sep, _ = inner.partition("/")
        entries[top] = entries.get(top, False) or bool(sep)
        dirs = inner.split("/")[:-1]
        if "tests" in dirs:
            test_dirs.add("/".join(dirs[:dirs.index("tests") + 1]))
    findings: list[Finding] = [
        Finding(name, "TESTS_IN_PACKAGE",
                f"directory {test_dir + '/'!r} ships tests inside the install bundle; "
                "remove test code from the skill repository (AGENTS.md)")
        for test_dir in sorted(test_dirs)
    ]
    for entry, is_dir in sorted(entries.items()):
        if entry in (ALLOWED_PACKAGE_DIRS if is_dir else ALLOWED_PACKAGE_FILES):
            continue
        if is_dir and entry == "tests":
            continue  # TESTS_IN_PACKAGE owns a top-level tests/ directory
        if not is_dir and REAL_ENV_NAME_RE.match(entry):
            continue  # TRACKED_ENV owns real env files
        kind = "directory" if is_dir else "file"
        findings.append(Finding(name, "DISALLOWED_PACKAGE_ENTRY",
                                f"{kind} {entry!r} is not on the package allowlist "
                                "(AGENTS.md)"))
    return findings


def check_skill(skill_dir: Path) -> list[Finding]:
    skills_ref = require_skills_ref()
    name = skill_dir.name
    findings: list[Finding] = []
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")

    for message in skills_ref.validate(skill_dir):
        findings.append(Finding(name, "AGENT_SKILLS_SPEC", message))
    try:
        props = skills_ref.read_properties(skill_dir)
    except skills_ref.SkillError:
        props = None  # validate() above already reported why the frontmatter is unreadable

    if props is not None:
        metadata = props.metadata
        if metadata is None:
            findings.append(Finding(name, "NO_METADATA", "missing metadata.version block"))
        elif not isinstance(metadata, dict):
            findings.append(Finding(name, "BAD_METADATA", "metadata must be a mapping"))
        else:
            version = metadata.get("version", "")
            if not version:
                findings.append(Finding(name, "NO_VERSION", "missing metadata.version"))
            elif not SEMVER_RE.match(version):
                findings.append(Finding(name, "BAD_VERSION", f"{version!r} is not MAJOR.MINOR.PATCH"))

    if CHANGE_LOG_HEADING_RE.search(text):
        findings.append(Finding(name, "CHANGELOG_IN_SKILL",
                                "package history belongs in git log, not SKILL.md"))

    body = text[text.find("\n---", 3) + 4:] if text.startswith("---") else text

    findings.extend(check_traversal_link(name, body))
    findings.extend(check_package_entries(name, skill_dir))

    for env in tracked_env_files(skill_dir):
        findings.append(Finding(name, "TRACKED_ENV", f"committed real env file: {env}"))

    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate craft-skills skill-package format.")
    ap.add_argument("--diff-base", action="append",
                    help="single base commit, supplied once; union committed/staged/unstaged/untracked changes")
    ap.add_argument("--package", action="append", default=[], help="existing skills/<owner>; repeatable, additive")
    ap.add_argument("--advisory", action="store_true", help="report format findings; input/Git errors still fail")
    ap.add_argument("--root", help="repo root override (default: derived from script path)")
    args = ap.parse_args()
    require_skills_ref()

    global REPO_ROOT, SKILLS_DIR, TESTS_DIR
    if args.root:
        REPO_ROOT = Path(args.root).resolve()
        SKILLS_DIR = REPO_ROOT / "skills"
        TESTS_DIR = REPO_ROOT / "tests"

    try:
        if args.diff_base and len(args.diff_base) != 1:
            raise ValueError("--diff-base may be supplied only once")
        diff_base = args.diff_base[0] if args.diff_base else None
        targets, findings = select_packages(diff_base, args.package)
        for directory in targets:
            print(f"scope: package {directory.relative_to(REPO_ROOT).as_posix()}")
            findings.extend(check_skill(directory))
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"skill-format: input error: {exc}", file=sys.stderr)
        return 2

    for f in findings:
        print(f"  [{f.code}] {f.skill}: {f.detail}")

    if not findings:
        print(f"skill-format: OK — {len(targets)} package(s) validated.")
        return 0

    print(f"skill-format: {len(findings)} error(s) across {len(targets)} package(s).")
    return 0 if args.advisory else 1


if __name__ == "__main__":
    raise SystemExit(main())
