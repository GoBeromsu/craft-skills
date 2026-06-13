#!/usr/bin/env python3
"""Validate craft-skills skill-package format.

Each skill package (`skills/<area>/<skill>/`) must be well-formed per the canonical
schema (`skills/skillify/references/schemas.md`):

  1. SKILL.md frontmatter has `name`, `description`, `version`, `allowed-tools`,
     and `compatibility` (5-key shape).
  2. `name` equals the package directory name.
  3. `description` is non-empty and <= 1024 characters.
  4. `version` is semver `MAJOR.MINOR.PATCH`.
  5. `allowed-tools` is present and is a YAML list (sequence).
  6. `compatibility` is present, non-empty, and <= 500 characters.
  7. SKILL.md body contains no `## Change Log` (history lives in CHANGELOG.md).
  8. CHANGELOG.md exists beside SKILL.md with >= 1 dated bullet `- YYYY-MM-DD ...`.
  9. No tracked real `.env` file in the package (only `.env.example` may be committed).

Modes:
  (default)       full scan; reports every violation; exit 1 if any are found.
  --diff-base REF only enforce packages whose own SKILL.md or CHANGELOG.md changed
                  vs REF (PR mode).  Diff-base scope rule: a package is "changed"
                  ONLY when its own ``<pkgdir>/SKILL.md`` or ``<pkgdir>/CHANGELOG.md``
                  appears in the git diff name-list.  Changes to sibling files
                  (RESOLVER.md, references/*, scripts/*, etc.) do NOT pull the
                  package into enforcement scope — routing changes are covered by
                  validate-routing.py.  A parent area's SKILL.md does not match a
                  child leaf, and a child's change does not match the parent area —
                  each file is matched against its own immediate parent directory.
                  Legacy packages stay green until their own SKILL.md/CHANGELOG.md
                  is next touched.
  --advisory      print violations but always exit 0 (use for a non-blocking report).

This validator owns FORMAT only. Secret/real-path leakage is owned by
validate-runtime-hygiene.py — keep the two concerns separate.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = REPO_ROOT / "skills"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
CHANGELOG_BULLET_RE = re.compile(r"^- \d{4}-\d{2}-\d{2}\b")
CHANGE_LOG_HEADING_RE = re.compile(r"^## +Change Log\b", re.MULTILINE)
REAL_ENV_RE = re.compile(r"(^|/)\.env(\.[A-Za-z0-9_-]+)?$")


@dataclass
class Finding:
    skill: str
    code: str
    detail: str


def parse_frontmatter(text: str) -> "dict[str, str | list[str]] | None":
    """Minimal YAML-frontmatter reader (no external deps). Scalar keys and list values.

    Supports inline list syntax: ``key: [a, b, c]``
    Supports block list syntax::

        key:
          - a
          - b
    """
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end].strip("\n")
    fields: "dict[str, str | list[str]]" = {}
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line or line[0] in " \t#":
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip("'\"")
        # Inline list: key: [item1, item2, ...]
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            fields[key] = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
            i += 1
        # Block list: key:<newline>  - item
        elif val == "":
            items: list[str] = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                stripped = next_line.lstrip()
                if stripped.startswith("- "):
                    items.append(stripped[2:].strip().strip("'\""))
                    j += 1
                elif next_line and next_line[0] not in " \t":
                    break
                else:
                    break
            if items:
                fields[key] = items
                i = j
            else:
                fields[key] = val
                i += 1
        else:
            fields[key] = val
            i += 1
    return fields


def tracked_env_files(skill_dir: Path) -> list[str]:
    rel = skill_dir.relative_to(REPO_ROOT).as_posix()
    try:
        out = subprocess.run(
            ["git", "ls-files", rel],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    hits = []
    for f in out.splitlines():
        name = f.rsplit("/", 1)[-1]
        if name == ".env.example":
            continue
        if REAL_ENV_RE.search(f):
            hits.append(f)
    return hits


def changed_skill_dirs(diff_base: str) -> set[Path] | None:
    """Return skill-package directories whose own SKILL.md or CHANGELOG.md changed.

    Diff-base scope rule: a package is "changed" ONLY when its own
    ``<pkgdir>/SKILL.md`` or ``<pkgdir>/CHANGELOG.md`` appears in the diff
    name-list.  Changes to sibling files (RESOLVER.md, references/*, scripts/*)
    do NOT trigger enforcement — those are owned by validate-routing.py.
    """
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", diff_base],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"ERROR: could not compute diff against {diff_base!r}: {exc}", file=sys.stderr)
        return None
    dirs: set[Path] = set()
    for rel in out.splitlines():
        p = REPO_ROOT / rel
        # Only the package whose *own* SKILL.md or CHANGELOG.md changed is in scope.
        # Any other sibling file change (RESOLVER.md, references/*, …) is ignored.
        if p.name not in ("SKILL.md", "CHANGELOG.md"):
            continue
        pkg_dir = p.parent
        # Must be under skills/ (not the skills/ root itself).
        if SKILLS_DIR not in pkg_dir.parents:
            continue
        if (pkg_dir / "SKILL.md").exists():
            dirs.add(pkg_dir)
    return dirs


def check_skill(skill_dir: Path) -> list[Finding]:
    name = skill_dir.name
    findings: list[Finding] = []
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")

    fm = parse_frontmatter(text)
    if fm is None:
        return [Finding(name, "NO_FRONTMATTER", "SKILL.md has no YAML frontmatter")]

    if fm.get("name") != name:
        findings.append(Finding(name, "NAME_MISMATCH",
                                f"frontmatter name {fm.get('name')!r} != dir {name!r}"))
    desc = fm.get("description", "")
    if not desc:
        findings.append(Finding(name, "NO_DESCRIPTION", "missing description"))
    elif len(desc) > 1024:
        findings.append(Finding(name, "DESCRIPTION_TOO_LONG", f"{len(desc)} > 1024 chars"))
    version = fm.get("version", "")
    if not version:
        findings.append(Finding(name, "NO_VERSION", "missing version"))
    elif not isinstance(version, str) or not SEMVER_RE.match(version):
        findings.append(Finding(name, "BAD_VERSION", f"{version!r} is not MAJOR.MINOR.PATCH"))

    allowed_tools = fm.get("allowed-tools")
    if allowed_tools is None:
        findings.append(Finding(name, "NO_ALLOWED_TOOLS", "missing allowed-tools"))
    elif not isinstance(allowed_tools, list):
        findings.append(Finding(name, "BAD_ALLOWED_TOOLS",
                                "allowed-tools must be a YAML list (sequence), "
                                f"got {allowed_tools!r}"))

    compat = fm.get("compatibility")
    if not compat:
        findings.append(Finding(name, "NO_COMPATIBILITY", "missing compatibility"))
    else:
        compat_str = ", ".join(compat) if isinstance(compat, list) else str(compat)
        if len(compat_str) > 500:
            findings.append(Finding(name, "BAD_COMPATIBILITY",
                                    f"compatibility is {len(compat_str)} chars, max 500"))

    if CHANGE_LOG_HEADING_RE.search(text):
        findings.append(Finding(name, "CHANGELOG_IN_SKILL",
                                "## Change Log belongs in CHANGELOG.md, not SKILL.md"))

    changelog = skill_dir / "CHANGELOG.md"
    if not changelog.exists():
        findings.append(Finding(name, "NO_CHANGELOG", "missing CHANGELOG.md beside SKILL.md"))
    else:
        cl = changelog.read_text(encoding="utf-8")
        if not any(CHANGELOG_BULLET_RE.match(line) for line in cl.splitlines()):
            findings.append(Finding(name, "CHANGELOG_NO_DATED_BULLET",
                                    "CHANGELOG.md has no '- YYYY-MM-DD ...' bullet"))

    for env in tracked_env_files(skill_dir):
        findings.append(Finding(name, "TRACKED_ENV", f"committed real env file: {env}"))

    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate craft-skills skill-package format.")
    ap.add_argument("--diff-base", help="only enforce packages changed vs this git ref")
    ap.add_argument("--advisory", action="store_true", help="report but always exit 0")
    ap.add_argument("--root", help="repo root override (default: derived from script path)")
    args = ap.parse_args()

    global REPO_ROOT, SKILLS_DIR
    if args.root:
        REPO_ROOT = Path(args.root).resolve()
        SKILLS_DIR = REPO_ROOT / "skills"

    all_skill_dirs = sorted({p.parent for p in SKILLS_DIR.rglob("SKILL.md")})

    if args.diff_base:
        scope = changed_skill_dirs(args.diff_base)
        if scope is None:
            return 2
        targets = [d for d in all_skill_dirs if d in scope]
        if not targets:
            print("skill-format: no changed skill packages to validate.")
            return 0
    else:
        targets = all_skill_dirs

    findings: list[Finding] = []
    for d in targets:
        findings.extend(check_skill(d))

    if not findings:
        print(f"skill-format: OK — {len(targets)} package(s) validated.")
        return 0

    for f in findings:
        print(f"  [{f.code}] {f.skill}: {f.detail}")
    print(f"skill-format: {len(findings)} violation(s) across {len(targets)} package(s).")
    return 0 if args.advisory else 1


if __name__ == "__main__":
    raise SystemExit(main())
