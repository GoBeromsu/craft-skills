#!/usr/bin/env python3
"""Validate craft-skills skill-package format against the authoring contract
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
 10. SKILL.md body carries a literal `## Output contract` heading (contract §4).  The
     section must also state the cannot-succeed behavior, but that is judged by review,
     not by scanning for a keyword.
 11. Every package-relative support path the body mentions (`scripts/`, `references/`,
     `templates/`, `assets/`, `agents/`) exists in the package, and no markdown link
     climbs out of the package with `../` (contract §12). Repository-root
     `tests/<name>/` paths are not package-local support paths.
 12. Supplied eval corpora at repo-root `tests/<name>/evals/` have typed cases
     and prompts. Corpus presence and case counts do not establish adequacy:
     the authoring evidence and independent review own that judgment.

Modes:
  (default)       full scan; reports every violation; exit 1 if any hard error found.
  --diff-base REF select the union of committed, staged, unstaged and untracked
                  package/support changes against one commit, not a revision range.
  --package PATH select an existing skills/<owner> directory; repeatable and
                  additive to --diff-base, never a glob or an escaping path.
  --advisory      report format findings without failing; input/Git errors exit 2.

Warnings (description-length shape) never affect the exit code, in any mode.
This validator owns FORMAT only. Secret/real-path leakage is owned by
validate-runtime-hygiene.py — keep the two concerns separate.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = REPO_ROOT / "skills"
TESTS_DIR = REPO_ROOT / "tests"


def corpus_dir(skill_dir: Path) -> Path:
    """Eval corpus lives at repo-root tests/<name>/evals/, never inside the package."""
    return TESTS_DIR / skill_dir.name / "evals"

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
ALL_CAPS_DIRECTIVE_LOOKALIKE = re.compile(r"^MUST(?![A-Za-z0-9])")
CONTRACT_SECTION = "Output contract"
PACKAGE_PATH_DIRS = ("scripts", "references", "templates", "assets", "tests", "agents")
PACKAGE_PATH_RE = re.compile(
    r"(?:\$SKILL_DIR/|\$\{SKILL_DIR\}/|(?<![A-Za-z0-9_./-]))(?:" + "|".join(PACKAGE_PATH_DIRS) + r")/[A-Za-z0-9_./-]*[A-Za-z0-9_]"
)
GRADING_KINDS = {"verifiable", "subjective"}


@dataclass
class Finding:
    skill: str
    code: str
    detail: str
    severity: str = "error"  # "error" | "warning"


def parse_scalar(value: str) -> object:
    """Parse the YAML scalar forms needed to distinguish strings from types."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1]
        return [parse_scalar(item) for item in inner.split(",") if item.strip()]
    if value.startswith("{") and value.endswith("}"):
        return {}
    if re.fullmatch(r"[>|][+-]?", value):
        return None
    comment = re.search(r"[ \t]+#", value)
    if comment is not None:
        value = value[:comment.start()].rstrip()
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
        if ALL_CAPS_DIRECTIVE_LOOKALIKE.search(description):
            return "BAD_MUST_USE_LOOKALIKE", (
                "leading all-caps MUST/USE lookalikes are reserved; use the exact "
                "'MUST USE <clause>. <remainder>' grammar or ordinary sentence case"
            )
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
    clause = description[len(PREFIX):delimiter_index]
    remainder = description[delimiter_index + len(DELIMITER):]
    if (
        not clause
        or not remainder
        or clause != clause.strip()
        or remainder != remainder.strip()
    ):
        return "BAD_MUST_USE_CLAUSE", (
            "MUST USE directive needs canonical nonempty clause and remainder spacing around '. '"
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
    return sorted(
        path for path in git_paths("ls-files", "-z", "--", rel)
        if PurePosixPath(path).name != ".env.example" and REAL_ENV_RE.search(path)
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
    }


def nearest_owner(path: str, owners: set[str]) -> str | None:
    matches = [owner for owner in owners if path == owner or path.startswith(owner + "/")]
    return max(matches, key=len) if matches else None


def current_owners() -> set[str]:
    owners: set[str] = set()
    for skill in SKILLS_DIR.rglob("SKILL.md"):
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
    changed: set[str] = set()
    for args in (
        ("diff", "--name-only", "-z", "--no-renames", base, head),
        ("diff", "--cached", "--name-only", "-z", "--no-renames", head),
        ("diff", "--name-only", "-z", "--no-renames"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
    ):
        changed.update(git_paths(*args))
    previous = package_owners(
        git_paths("ls-tree", "-r", "--name-only", "-z", base)
        | git_paths("ls-tree", "-r", "--name-only", "-z", head)
        | git_paths("ls-files", "--cached", "-z")
    )
    tombstones: set[str] = set()
    for rel in sorted(changed):
        mapped = "skills/" + rel[len("tests/"):] if rel.startswith("tests/") else rel
        owner = nearest_owner(mapped, owners)
        old_owner = nearest_owner(mapped, previous)
        if owner:
            selected.add(owner)
        if old_owner and old_owner not in owners:
            tombstones.add(old_owner)
        if owner or old_owner:
            continue
        # These shared surfaces invoke or document skillify's format contract.
        if (rel in {"AGENTS.md", "skills/PROVENANCE.md", ".github/workflows/pr-check.yml",
                    ".github/workflows/test-plugin-install.yml"}
                or rel.startswith(("scripts/governance/", "tests/governance/"))):
            if "skills/skillify" not in owners:
                raise ValueError(f"shared format owner skills/skillify is missing for {rel!r}")
            selected.add("skills/skillify")
        elif rel.startswith(("skills/", "tests/", "scripts/")):
            raise ValueError(f"unresolved package/support ownership for {rel!r}")
        else:
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
        reference = re.compile(
            r"(?:^|[\s`'\"(=])(?:\$\{?\w+\}?/)?"
            + re.escape(removed) + r"(?=/|[\s`'\"),#]|$)", re.MULTILINE,
        )
        for rel in sorted(reference_paths):
            if PurePosixPath(rel).parts[0] in {".git", ".gjc", "archive"}:
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
            if reference.search(text):
                mapped = "skills/" + rel[len("tests/"):] if rel.startswith("tests/") else rel
                consumer = nearest_owner(mapped, owners)
                if consumer:
                    selected.add(consumer)
                findings.append(Finding(consumer or rel, "DANGLING_PACKAGE_REFERENCE",
                                        f"{rel} still references removed owner {removed}"))
    return [REPO_ROOT / owner for owner in sorted(selected)], findings


def check_contract_sections(name: str, body: str) -> list[Finding]:
    match = re.search(rf"^## +{re.escape(CONTRACT_SECTION)}\s*$(.*?)(?=^## |\Z)", body, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if match is None:
        return [Finding(name, "MISSING_CONTRACT_SECTION",
                        f"SKILL.md body lacks `## {CONTRACT_SECTION}` (contract §4)")]
    # The section must state the cannot-succeed behavior, but that is an authoring
    # obligation judged by scenarios and review.  A keyword scan only proved that a
    # word was present, so it is not enforced here.
    return []


TRAVERSAL_LINK_RE = re.compile(
    r"\]\(\.\./|(?:references|templates|scripts|assets|examples)/(?:[^\s)`\"'<>]*/)?\.\.(?:/|$)"
)  # mirrors the Hermes tap fetcher's traversal abort


def check_referenced_paths(name: str, skill_dir: Path, body: str) -> list[Finding]:
    findings: list[Finding] = []
    if TRAVERSAL_LINK_RE.search(body):
        findings.append(Finding(name, "TRAVERSAL_LINK",
                                "SKILL.md links climb out of the package with `../`; "
                                "the Hermes tap fetcher aborts the install on such a path (contract §12)"))
    seen: set[str] = set()
    for match in PACKAGE_PATH_RE.finditer(body):
        rel = re.sub(r"^\$\{?SKILL_DIR\}?/", "", match.group(0)).rstrip(".")
        if rel in seen or "<" in rel or "*" in rel or rel.endswith("/"):
            continue
        if rel == "tests" or rel.startswith("tests/"):
            continue  # repo-root tests/<name>/ is never a package path
        seen.add(rel)
        if rel.split("/", 1)[0] not in PACKAGE_PATH_DIRS:
            continue
        if not (skill_dir / rel).exists():
            findings.append(Finding(name, "MISSING_REFERENCED_PATH",
                                    f"SKILL.md mentions `{rel}` but the package does not ship it (contract §12)"))
    return findings


def _load_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def check_eval_corpus(name: str, skill_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    evals_path = corpus_dir(skill_dir) / "evals.json"
    triggers_path = corpus_dir(skill_dir) / "triggers.json"

    if evals_path.exists():
        data = _load_json(evals_path)
        if isinstance(data, dict) and "skill" in data and data["skill"] != name:
            findings.append(Finding(name, "BAD_EVAL_CORPUS", "eval corpus `skill` does not match its owner"))
        cases = data.get("cases") if isinstance(data, dict) else None
        if not isinstance(cases, list):
            findings.append(Finding(name, "BAD_EVAL_CORPUS", "tests/evals/evals.json must be an object with a `cases` list"))
        else:
            seen_ids: set[str] = set()
            for i, case in enumerate(cases):
                label = case.get("id", f"#{i}") if isinstance(case, dict) else f"#{i}"
                if not isinstance(case, dict):
                    findings.append(Finding(name, "BAD_EVAL_CORPUS", f"case {label} is not an object"))
                    continue
                for key in ("id", "prompt", "expected_behavior", "grading"):
                    if not isinstance(case.get(key), str) or not case[key].strip():
                        findings.append(Finding(name, "BAD_EVAL_CORPUS", f"case {label} lacks non-empty `{key}`"))
                case_id = case.get("id")
                if isinstance(case_id, str):
                    if case_id in seen_ids:
                        findings.append(Finding(name, "BAD_EVAL_CORPUS", f"duplicate case id {case_id!r}"))
                    seen_ids.add(case_id)
                grading = case.get("grading")
                if not isinstance(grading, str) or grading not in GRADING_KINDS:
                    findings.append(Finding(name, "BAD_EVAL_CORPUS",
                                            f"case {label} grading must be one of {sorted(GRADING_KINDS)}"))
                else:
                    key = "assertions" if grading == "verifiable" else "rubric"
                    values = case.get(key)
                    if (not isinstance(values, list) or not values
                            or not all(isinstance(value, str) and value.strip() for value in values)):
                        findings.append(Finding(name, "BAD_EVAL_CORPUS",
                                                f"{grading} case {label} needs non-empty `{key}` string list"))

    if triggers_path.exists():
        data = _load_json(triggers_path)
        if not isinstance(data, dict):
            findings.append(Finding(name, "BAD_EVAL_CORPUS", "tests/evals/triggers.json must be an object"))
        else:
            if "skill" in data and data["skill"] != name:
                findings.append(Finding(name, "BAD_EVAL_CORPUS", "trigger corpus `skill` does not match its owner"))
            for key in ("should_trigger", "should_not_trigger"):
                items = data.get(key)
                if not isinstance(items, list) \
                        or not all(isinstance(x, str) and x.strip() for x in items):
                    findings.append(Finding(name, "BAD_EVAL_CORPUS",
                                            f"tests/evals/triggers.json `{key}` must be a list of non-empty prompts"))
    return findings


def check_skill(skill_dir: Path) -> list[Finding]:
    name = skill_dir.name
    findings: list[Finding] = []
    if skill_dir.parent != SKILLS_DIR:
        findings.append(Finding(name, "NESTED_SKILL_MD", "craft packages must be flat under skills/"))
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

    findings.extend(check_contract_sections(name, body))
    findings.extend(check_referenced_paths(name, skill_dir, body))
    findings.extend(check_eval_corpus(name, skill_dir))

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
    ap.add_argument("--diff-base", action="append",
                    help="single base commit, supplied once; union committed/staged/unstaged/untracked changes")
    ap.add_argument("--package", action="append", default=[], help="existing skills/<owner>; repeatable, additive")
    ap.add_argument("--advisory", action="store_true", help="report format findings; input/Git errors still fail")
    ap.add_argument("--root", help="repo root override (default: derived from script path)")
    args = ap.parse_args()

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
