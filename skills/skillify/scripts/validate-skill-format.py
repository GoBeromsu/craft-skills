#!/usr/bin/env python3
"""Validate craft-skills skill-package format against the v4 authoring contract
(`skills/skillify/references/contract.md`).

Each skill package is a single directory `skills/<skill-name>/` containing at
least `SKILL.md` + `CHANGELOG.md`. This validator enforces, per package:

  1. SKILL.md frontmatter has required `name`, `description`, `metadata` and
     may additionally contain Agent Skills' optional `license`,
     `compatibility`, and `allowed-tools` keys. `allowed-tools` is an
     experimental, implementation-dependent declaration, not a portable
     enforcement mechanism.
  2. `name` equals the package directory name, is kebab-case, and is <= 64
     characters.
  3. `description` is 1..1024 characters (hard bounds); a shape warning
     (non-blocking) fires under 200 or over 700 characters. Its optional
     routing directive is checked for parsed shape only, never semantic proof.
  4. `metadata.version` is present and is semver `MAJOR.MINOR.PATCH`.
  5. SKILL.md body (everything after the frontmatter block) is <= 500 lines.
  6. No SKILL.md is nested anywhere inside the package below the top-level one
     (every skill is one flat directory).
  7. SKILL.md body contains no `## Change Log` (history lives in CHANGELOG.md).
  8. CHANGELOG.md exists beside SKILL.md with >= 1 dated bullet `- YYYY-MM-DD ...`.
  9. No tracked real `.env` file in the package (only `.env.example` may be committed).

Modes:
  (default)       full scan; reports every violation; exit 1 if any hard error found.
  --diff-base REF only enforce packages whose own SKILL.md or CHANGELOG.md changed
                  vs REF (PR mode). A package is "changed" ONLY when its own
                  ``skills/<skill>/SKILL.md`` or ``skills/<skill>/CHANGELOG.md``
                  appears in the git diff name-list. Changes to sibling files
                  (references/*, scripts/*, etc.) do NOT pull the package into
                  enforcement scope. Legacy packages stay green until their own
                  SKILL.md/CHANGELOG.md is next touched.
  --advisory      print violations but always exit 0 (use for a non-blocking report).

Warnings (description-length shape) never affect the exit code, in any mode.
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
KEBAB_CASE_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CHANGELOG_BULLET_RE = re.compile(r"^- \d{4}-\d{2}-\d{2}\b")
CHANGE_LOG_HEADING_RE = re.compile(r"^## +Change Log\b", re.MULTILINE)
REAL_ENV_RE = re.compile(r"(^|/)\.env(\.[A-Za-z0-9_-]+)?$")

ALLOWED_TOP_KEYS = {
    "name",
    "description",
    "metadata",
    "license",
    "compatibility",
    "allowed-tools",
}
BODY_LINE_LIMIT = 500
DESCRIPTION_MIN_WARN = 200
DESCRIPTION_MAX_WARN = 700
DESCRIPTION_HARD_MAX = 1024
NAME_MAX_LENGTH = 64
PREFIX = "MUST USE "
DELIMITER = ". "
ANY_TOKEN = re.compile(r"(?<![A-Za-z0-9_])ANY(?![A-Za-z0-9_])")


@dataclass
class Finding:
    skill: str
    code: str
    detail: str
    severity: str = "error"  # "error" | "warning"


def parse_scalar(value: str) -> object:
    """Parse the YAML scalar forms needed to distinguish strings from types."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1]
        return [parse_scalar(item) for item in inner.split(",") if item.strip()]
    if value.startswith("{") and value.endswith("}"):
        return {}
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if re.fullmatch(r"[-+]?\d+", value):
        return int(value)
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][-+]?\d+)?", value):
        return float(value)
    return value


def validate_description_directive(description: str) -> tuple[str, str] | None:
    """Return one routing-directive shape finding, without semantic inference."""
    prefix_count = description.count(PREFIX)
    if prefix_count > 1:
        return "MULTIPLE_MUST_USE", "description has multiple exact 'MUST USE ' prefixes"
    if prefix_count == 0:
        if ANY_TOKEN.search(description):
            return "MISPLACED_DIRECTIVE_ANY", (
                "standalone uppercase ANY requires a valid MUST USE directive"
            )
        return None
    if not description.startswith(PREFIX):
        return "MISPLACED_MUST_USE", "exact 'MUST USE ' prefix must start at character 0"

    delimiter_index = description.find(DELIMITER, len(PREFIX))
    if delimiter_index == -1:
        return "BAD_MUST_USE_CLAUSE", (
            "MUST USE directive needs a nonempty clause and remainder separated by '. '"
        )
    clause = description[len(PREFIX):delimiter_index].strip()
    remainder = description[delimiter_index + len(DELIMITER):].strip()
    if not clause or not remainder:
        return "BAD_MUST_USE_CLAUSE", (
            "MUST USE directive needs a nonempty clause and remainder separated by '. '"
        )
    if ANY_TOKEN.search(remainder):
        return "MISPLACED_DIRECTIVE_ANY", (
            "standalone uppercase ANY is allowed only in the directive clause"
        )
    if len(ANY_TOKEN.findall(clause)) > 1:
        return "DIRECTIVE_ANY_LIMIT", (
            "MUST USE directive clause may contain at most one standalone uppercase ANY"
        )
    return None


def parse_frontmatter(text: str) -> "dict[str, object] | None":
    """Minimal YAML-frontmatter reader (no external deps).

    Supports scalar values, inline lists (``key: [a, b]``), block lists
    (``key:`` then ``  - item``), and one level of nested mapping
    (``metadata:`` then ``  version: 1.0.0``).
    """
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end].strip("\n")
    fields: "dict[str, object]" = {}
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
        val = val.strip()
        if val != "":
            fields[key] = parse_scalar(val)
            i += 1
            continue
        # Empty scalar: look ahead for an indented block (list or mapping).
        block_lines: list[str] = []
        j = i + 1
        while j < len(lines):
            nxt = lines[j]
            if nxt and nxt[0] not in " \t":
                break
            block_lines.append(nxt)
            j += 1
        list_items = [parse_scalar(ln.lstrip()[2:]) for ln in block_lines if ln.lstrip().startswith("- ")]
        if list_items and len(list_items) == len([b for b in block_lines if b.strip()]):
            fields[key] = list_items
        elif block_lines:
            nested: dict[str, object] = {}
            base_indent = min(len(ln) - len(ln.lstrip()) for ln in block_lines if ln.strip())
            for index, ln in enumerate(block_lines):
                if not ln.strip() or len(ln) - len(ln.lstrip()) != base_indent:
                    continue
                stripped = ln.strip()
                if ":" not in stripped:
                    continue
                nkey, _, nval = stripped.partition(":")
                nval = nval.strip()
                if nval:
                    nested[nkey.strip()] = parse_scalar(nval)
                    continue
                children = [
                    child for child in block_lines[index + 1:]
                    if child.strip() and len(child) - len(child.lstrip()) > base_indent
                ]
                if children and children[0].lstrip().startswith("- "):
                    nested[nkey.strip()] = [
                        parse_scalar(child.lstrip()[2:])
                        for child in children
                        if child.lstrip().startswith("- ")
                    ]
                elif children:
                    nested[nkey.strip()] = {}
                else:
                    nested[nkey.strip()] = ""
            fields[key] = nested
        else:
            fields[key] = val
        i = j
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
    """Return top-level skill-package directories whose own SKILL.md or
    CHANGELOG.md changed vs diff_base."""
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
        if p.name not in ("SKILL.md", "CHANGELOG.md"):
            continue
        pkg_dir = p.parent
        if pkg_dir.parent != SKILLS_DIR:
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

    extra_keys = set(fm.keys()) - ALLOWED_TOP_KEYS
    for key in sorted(extra_keys):
        findings.append(Finding(name, "FORBIDDEN_KEY",
                                f"frontmatter key {key!r} is not allowed; only "
                                "name/description/metadata and optional "
                                "license/compatibility/allowed-tools are"))

    fm_name = fm.get("name")
    if fm_name != name:
        findings.append(Finding(name, "NAME_MISMATCH",
                                f"frontmatter name {fm_name!r} != dir {name!r}"))
    elif not KEBAB_CASE_RE.match(str(fm_name)):
        findings.append(Finding(name, "NAME_NOT_KEBAB_CASE",
                                f"{fm_name!r} is not kebab-case"))
    elif len(fm_name) > NAME_MAX_LENGTH:
        findings.append(Finding(name, "NAME_TOO_LONG",
                                f"{len(fm_name)} > {NAME_MAX_LENGTH} chars"))

    desc = fm.get("description", "")
    if not desc:
        findings.append(Finding(name, "NO_DESCRIPTION", "missing description"))
    elif len(str(desc)) > DESCRIPTION_HARD_MAX:
        findings.append(Finding(name, "DESCRIPTION_TOO_LONG",
                                f"{len(str(desc))} > {DESCRIPTION_HARD_MAX} chars"))
    elif len(str(desc)) < DESCRIPTION_MIN_WARN:
        findings.append(Finding(name, "DESCRIPTION_SHORT",
                                f"{len(str(desc))} < {DESCRIPTION_MIN_WARN} chars (shape warning)",
                                severity="warning"))
    elif len(str(desc)) > DESCRIPTION_MAX_WARN:
        findings.append(Finding(name, "DESCRIPTION_LONG",
                                f"{len(str(desc))} > {DESCRIPTION_MAX_WARN} chars (shape warning)",
                                severity="warning"))

    if isinstance(desc, str) and desc:
        directive_finding = validate_description_directive(desc)
        if directive_finding is not None:
            code, detail = directive_finding
            findings.append(Finding(name, code, detail))

    metadata = fm.get("metadata")
    if not isinstance(metadata, dict):
        findings.append(Finding(name, "NO_METADATA", "missing metadata.version block"))
    else:
        for key, value in metadata.items():
            if not isinstance(key, str) or not isinstance(value, str):
                findings.append(Finding(
                    name,
                    "BAD_METADATA",
                    "metadata must be a string-to-string map",
                ))
                break
        version = metadata.get("version", "")
        if not version:
            findings.append(Finding(name, "NO_VERSION", "missing metadata.version"))
        elif not isinstance(version, str) or not SEMVER_RE.match(version):
            findings.append(Finding(name, "BAD_VERSION", f"{version!r} is not MAJOR.MINOR.PATCH"))

    if "license" in fm and (not isinstance(fm["license"], str) or not fm["license"].strip()):
        findings.append(Finding(name, "BAD_LICENSE",
                                "license must be a non-empty string"))

    if "compatibility" in fm:
        compatibility = fm["compatibility"]
        if (not isinstance(compatibility, str)
                or not 1 <= len(compatibility) <= 500):
            findings.append(Finding(name, "BAD_COMPATIBILITY",
                                    "compatibility must be a string of 1..500 characters"))

    if ("allowed-tools" in fm
            and (not isinstance(fm["allowed-tools"], str) or not fm["allowed-tools"].strip())):
        findings.append(Finding(
            name,
            "BAD_ALLOWED_TOOLS",
            "allowed-tools must be a non-empty string; its semantics are experimental "
            "and implementation-dependent",
        ))

    if CHANGE_LOG_HEADING_RE.search(text):
        findings.append(Finding(name, "CHANGELOG_IN_SKILL",
                                "## Change Log belongs in CHANGELOG.md, not SKILL.md"))

    body = text[text.find("\n---", 3) + 4:]
    body_lines = len(body.splitlines())
    if body_lines > BODY_LINE_LIMIT:
        findings.append(Finding(name, "BODY_TOO_LONG",
                                f"body is {body_lines} lines > {BODY_LINE_LIMIT} hard ceiling"))

    for nested in sorted(skill_dir.rglob("SKILL.md")):
        if nested != skill_md:
            findings.append(Finding(name, "NESTED_SKILL_MD",
                                    f"nested SKILL.md not allowed: {nested.relative_to(skill_dir)}"))

    for env in tracked_env_files(skill_dir):
        findings.append(Finding(name, "TRACKED_ENV", f"committed real env file: {env}"))

    changelog = skill_dir / "CHANGELOG.md"
    if not changelog.exists():
        findings.append(Finding(name, "NO_CHANGELOG", "missing CHANGELOG.md beside SKILL.md"))
    else:
        cl = changelog.read_text(encoding="utf-8")
        if not any(CHANGELOG_BULLET_RE.match(line) for line in cl.splitlines()):
            findings.append(Finding(name, "CHANGELOG_NO_DATED_BULLET",
                                    "CHANGELOG.md has no '- YYYY-MM-DD ...' bullet"))

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

    all_skill_dirs = sorted(
        p for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists()
    ) if SKILLS_DIR.exists() else []

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

    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]

    for f in warnings:
        print(f"  [{f.code}] {f.skill}: {f.detail}")
    for f in errors:
        print(f"  [{f.code}] {f.skill}: {f.detail}")

    if not findings:
        print(f"skill-format: OK — {len(targets)} package(s) validated.")
        return 0

    print(f"skill-format: {len(errors)} error(s), {len(warnings)} warning(s) "
          f"across {len(targets)} package(s).")
    return 0 if (args.advisory or not errors) else 1


if __name__ == "__main__":
    raise SystemExit(main())
