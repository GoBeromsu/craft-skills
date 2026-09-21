#!/usr/bin/env python3
"""Validate that craft-skills skill packages do not commit runtime-specific values.

Default mode scans tracked files. CI can use --diff-base with one verified
commit to scan changed lines of tracked files plus full untracked files, so
the guard blocks new leaks without turning legacy cleanup into a single huge
migration. Git, path, and containment helpers come from validate-skill-format.py.
"""
from __future__ import annotations

import argparse
import ast
import os
import subprocess
import importlib.machinery
import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

_FORMAT_PATH = Path(__file__).resolve().parent / "validate-skill-format.py"
_SPEC = importlib.util.spec_from_file_location("skillify_format_validator", _FORMAT_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load format validator helpers from {_FORMAT_PATH}")
fmt = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = fmt
_SOURCE = importlib.machinery.SourceFileLoader(_SPEC.name, str(_FORMAT_PATH)).get_source(_SPEC.name)
if _SOURCE is None:
    raise RuntimeError(f"cannot read format validator source from {_FORMAT_PATH}")
exec(compile(_SOURCE, str(_FORMAT_PATH), "exec", dont_inherit=True), fmt.__dict__)

TEXT_EXTENSIONS = {
    ".bash",
    ".env",
    ".example",
    ".gitignore",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

SKIP_PARTS = {".git", "node_modules", "__pycache__"}
DOC_EXAMPLE_ALLOWLIST = {"skills/skillify/references/runtime-hygiene.md"}
PLACEHOLDER_MARKERS = ("<", ">", "YOUR_", "REDACTED", "PLACEHOLDER", "EXAMPLE", "DUMMY", "XXXX")
LOOKUP_VALUE_RE = re.compile(r"[()\[\]{}]")


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    code: str
    detail: str


@dataclass(frozen=True)
class Rule:
    code: str
    pattern: re.Pattern[str]
    detail: str


SECRET_RULES = [
    Rule("SECRET_PRIVATE_KEY", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"), "private key block marker"),
    Rule("SECRET_AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    Rule("SECRET_GITHUB_TOKEN", re.compile(r"\b(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,}\b"), "GitHub token"),
    Rule("SECRET_SLACK_TOKEN", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"), "Slack token"),
    Rule("SECRET_OPENAI_KEY", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b"), "OpenAI-style API key"),
    Rule("SECRET_ANTHROPIC_KEY", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{32,}\b"), "Anthropic API key"),
]

SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret|token|password|client[_-]?secret)\b['\"]?\s*[:=]\s*(['\"]?)([^'\"\s#`<>]{16,})"
)

RUNTIME_RULES = [
    Rule("RUNTIME_HOME_PATH", re.compile(r"(?<![A-Za-z0-9_<>])/(?:Users|home)/[A-Za-z0-9._-]+/[^\s`'\")\]}]+"), "host-specific home path"),
    Rule("RUNTIME_ABS_VOLUME_PATH", re.compile(r"(?<![A-Za-z0-9_<>])/(?:Volumes|opt|var|etc)/[^\s`'\")\]}]+"), "host-specific absolute path"),
]


def bind_root(root: Path) -> Path:
    resolved = root.resolve()
    fmt.REPO_ROOT = resolved
    fmt.SKILLS_DIR = resolved / "skills"
    fmt.TESTS_DIR = resolved / "tests"
    return resolved


def is_real_env(rel: str) -> bool:
    name = PurePosixPath(rel).name
    return name != ".env.example" and bool(fmt.REAL_ENV_NAME_RE.match(name))


def is_text_candidate(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in SKIP_PARTS for part in rel.parts):
        return False
    return path.suffix in TEXT_EXTENSIONS or path.name in {"SKILL.md", ".gitignore"}


def should_scan_contents(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    return is_text_candidate(path, root) or is_real_env(rel)


def is_placeholder(text: str) -> bool:
    upper = text.upper()
    return any(marker in upper for marker in PLACEHOLDER_MARKERS)


def line_uses_env_indirection(line: str) -> bool:
    return bool(
        re.search(r"\$\{?[A-Z][A-Z0-9_]{2,}\}?", line)
        or re.search(r"os\.environ(?:\.get)?\(", line)
        or re.search(r"process\.env\.[A-Z][A-Z0-9_]+", line)
        or re.search(r"env\(['\"][A-Z][A-Z0-9_]+", line)
    )


def is_python_lookup(rel: Path, line: str, match: re.Match[str]) -> bool:
    """Accept only a name/attribute at the matched source span in Python code."""
    if rel.suffix != ".py" or match.group(2):
        return False
    source = line.lstrip()
    indent = len(line) - len(source)
    start = len(line[indent:match.start(3)].encode("utf-8"))
    end = len(line[indent:match.end(3)].encode("utf-8"))
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return False
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Name, ast.Attribute)):
            continue
        if (
            not isinstance(node.ctx, ast.Load)
            or node.lineno != 1
            or node.end_lineno != 1
            or node.col_offset != start
            or node.end_col_offset != end
        ):
            continue
        while isinstance(node, ast.Attribute):
            node = node.value
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            return True
    return False


def scan_line(rel: Path, lineno: int, line: str, *, doc_example: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    if not line.strip():
        return findings

    for rule in SECRET_RULES:
        for match in rule.pattern.finditer(line):
            matched = match.group(0)
            if is_placeholder(matched):
                continue
            findings.append(Finding(rel, lineno, rule.code, rule.detail))

    for match in SECRET_ASSIGNMENT_RE.finditer(line):
        quote, value = match.group(2), match.group(3)
        if is_placeholder(value) or is_placeholder(match.group(0)):
            continue
        if not quote and LOOKUP_VALUE_RE.search(value):
            continue
        if is_python_lookup(rel, line, match):
            continue
        findings.append(Finding(rel, lineno, "SECRET_ASSIGNMENT", "secret-like assignment"))

    if doc_example:
        return findings

    for rule in RUNTIME_RULES:
        for match in rule.pattern.finditer(line):
            matched = match.group(0)
            if is_placeholder(matched):
                continue
            findings.append(Finding(rel, lineno, rule.code, rule.detail))
    return findings


def _env_finding(rel: Path) -> Finding | None:
    rel_s = rel.as_posix()
    if is_real_env(rel_s):
        return Finding(rel, 0, "RUNTIME_ENV_FILE", "tracked real env file; commit only .env.example placeholders")
    return None


def contained_live_path(root: Path, rel: str) -> Path:
    """Return the live path only after containment. Never read contents here."""
    candidate = fmt.safe_repo_path(rel)
    if candidate.is_symlink() or candidate.exists():
        try:
            resolved = candidate.resolve()
        except OSError as exc:
            raise ValueError(f"unreadable path: {rel}: {exc}") from exc
        if not resolved.is_relative_to(root.resolve()):
            raise ValueError(f"repository path escapes root: {rel}")
    return candidate


def read_text_strict(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"unreadable path: {path}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"unreadable path: {path}: {exc}") from exc


def scan_file(path: Path, root: Path) -> list[Finding]:
    rel = path.relative_to(root)
    findings: list[Finding] = []
    env_hit = _env_finding(rel)
    if env_hit is not None:
        findings.append(env_hit)
    if not should_scan_contents(path, root):
        return findings
    text = read_text_strict(path)
    doc_example = rel.as_posix() in DOC_EXAMPLE_ALLOWLIST
    for lineno, line in enumerate(text.splitlines(), start=1):
        findings.extend(scan_line(rel, lineno, line, doc_example=doc_example))
    return findings


def verify_commit(diff_base: str) -> str:
    if not diff_base or diff_base.startswith("-") or ".." in diff_base:
        raise ValueError("--diff-base requires one commit-ish, not a range or option")
    return fmt.git_output(
        "rev-parse", "--verify", "--end-of-options", diff_base + "^{commit}",
    ).decode().strip()


def changed_relpaths(base: str) -> set[str]:
    changed: set[str] = set()
    for args in (
        ("diff", "--name-only", "-z", "--no-renames", base, "HEAD"),
        ("diff", "--cached", "--name-only", "-z", "--no-renames", "HEAD"),
        ("diff", "--name-only", "-z", "--no-renames"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
    ):
        changed.update(fmt.git_paths(*args))
    return changed


def _added_lines_from_diff(diff_text: str) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    new_line = 0
    in_hunk = False
    for raw in diff_text.splitlines():
        if raw.startswith("@@"):
            match = re.search(r"\+(\d+)", raw)
            new_line = int(match.group(1)) if match else 0
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if raw.startswith("\\"):
            continue
        if raw.startswith("+"):
            rows.append((new_line, raw[1:]))
            new_line += 1
        elif raw.startswith("-"):
            continue
        else:
            new_line += 1
    return rows


def added_lines_for_path(root: Path, base: str, rel: str) -> list[tuple[int, str]]:
    try:
        proc = subprocess.run(
            [
                "git", "diff", "--unified=0", "--no-renames", "--diff-filter=ACMRT",
                "--text", "--no-color", "--no-ext-diff", "--no-textconv",
                base, "--", rel,
            ],
            cwd=root, capture_output=True, check=False,
        )
    except FileNotFoundError as vis:
        raise ValueError(f"Git diff failed: {vis}") from vis
    if proc.returncode not in (0, 1):
        detail = os.fsdecode(proc.stderr or b"").strip()
        raise ValueError(f"Git diff failed: {detail or proc.returncode}")
    try:
        text = proc.stdout.decode("utf-8")
    except UnicodeDecodeError as vis:
        raise ValueError(f"unreadable diff for {rel}: {vis}") from vis
    return _added_lines_from_diff(text)


def scan_diff(root: Path, diff_base: str) -> list[Finding]:
    base = verify_commit(diff_base)
    untracked = fmt.git_paths("ls-files", "--others", "--exclude-standard", "-z")
    findings: list[Finding] = []
    for rel in sorted(changed_relpaths(base)):
        live = contained_live_path(root, rel)
        if not live.exists() and not live.is_symlink():
            continue
        if live.is_dir():
            continue
        rel_path = Path(rel)
        env_hit = _env_finding(rel_path)
        if env_hit is not None:
            findings.append(env_hit)
        if not should_scan_contents(live, root):
            continue
        doc_example = rel in DOC_EXAMPLE_ALLOWLIST
        if rel in untracked:
            text = read_text_strict(live)
            for lineno, line in enumerate(text.splitlines(), start=1):
                findings.extend(scan_line(rel_path, lineno, line, doc_example=doc_example))
            continue
        for lineno, line in added_lines_for_path(root, base, rel):
            findings.extend(scan_line(rel_path, lineno, line, doc_example=doc_example))
    return findings


def collect_explicit_files(root: Path, values: list[str]) -> list[Path]:
    files: list[Path] = []
    root_res = root.resolve()
    for raw in values:
        if not raw or "\0" in raw:
            raise ValueError(f"invalid path: {raw!r}")
        given = Path(raw)
        candidate = given if given.is_absolute() else (root / given)
        try:
            resolved = candidate.resolve()
        except OSError as exc:
            raise ValueError(f"unreadable path: {raw}: {exc}") from exc
        if not resolved.is_relative_to(root_res):
            raise ValueError(f"repository path escapes root: {raw}")
        if not candidate.exists() and not candidate.is_symlink():
            raise ValueError(f"missing path: {raw}")
        if resolved.is_dir():
            for child in resolved.rglob("*"):
                if not child.is_file() and not child.is_symlink():
                    continue
                try:
                    child_res = child.resolve()
                except OSError as exc:
                    raise ValueError(f"unreadable path: {child}: {exc}") from exc
                if not child_res.is_relative_to(root_res):
                    raise ValueError(f"repository path escapes root: {child}")
                files.append(child)
            continue
        if not resolved.is_file():
            raise ValueError(f"missing path: {raw}")
        files.append(candidate)
    return files


def print_findings(findings: list[Finding]) -> None:
    print("Runtime hygiene violations found:", file=sys.stderr)
    for item in findings:
        where = f"{item.path}:{item.line}" if item.line else str(item.path)
        print(f"- {where}: {item.code}: {item.detail}", file=sys.stderr)
    print(
        "\nMove real paths/secrets into env vars, approved credential files, or per-skill .env (gitignored).",
        file=sys.stderr,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate craft-skills skill runtime hygiene")
    parser.add_argument("paths", nargs="*", help="Optional paths to scan; defaults to tracked repo files")
    parser.add_argument("--root", default=None, help="Repository root")
    parser.add_argument(
        "--diff-base",
        action="append",
        help="single base commit, supplied once; union committed/staged/unstaged/untracked changes",
    )
    args = parser.parse_args()

    try:
        if args.diff_base and args.paths:
            raise ValueError("pass either --diff-base or explicit paths, not both")
        if args.diff_base and len(args.diff_base) != 1:
            raise ValueError("--diff-base may be supplied only once")
        if args.root:
            root = bind_root(Path(args.root))
        elif args.paths:
            root = bind_root(Path.cwd())
        else:
            root = bind_root(Path(fmt.git_output("rev-parse", "--show-toplevel").decode().strip()))
        if args.diff_base or not args.paths:
            git_root = Path(fmt.git_output("rev-parse", "--show-toplevel").decode().strip()).resolve()
            if git_root != root:
                raise ValueError("--root must identify the Git worktree root")
        if args.diff_base:
            findings = scan_diff(root, args.diff_base[0])
        elif args.paths:
            findings = []
            for path in sorted(set(collect_explicit_files(root, args.paths))):
                findings.extend(scan_file(path, root))
        else:
            findings = []
            for rel in sorted(fmt.git_paths("ls-files", "-z")):
                live = contained_live_path(root, rel)
                if not live.is_file() and not live.is_symlink():
                    continue
                findings.extend(scan_file(live, root))
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"runtime-hygiene: input error: {exc}", file=sys.stderr)
        return 2

    if findings:
        print_findings(findings)
        return 1
    print("Runtime hygiene OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
