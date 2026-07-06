#!/usr/bin/env python3
"""Validate that craft-skills skill packages do not commit runtime-specific values.

Default mode scans tracked files. CI can use --diff-base to scan only newly
added lines, so the guard blocks new leaks without turning legacy cleanup into a
single huge migration.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

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

SKIP_PARTS = {".git", ".claude-plugin", "node_modules", "__pycache__"}
DOC_EXAMPLE_ALLOWLIST = {"skills/skillify/references/runtime-hygiene.md"}
PLACEHOLDER_MARKERS = ("<", ">", "YOUR_", "REDACTED", "PLACEHOLDER", "EXAMPLE", "DUMMY", "XXXX")


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
    Rule("SECRET_GITHUB_TOKEN", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"), "GitHub token"),
    Rule("SECRET_SLACK_TOKEN", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"), "Slack token"),
    Rule("SECRET_OPENAI_KEY", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b"), "OpenAI-style API key"),
    Rule("SECRET_ANTHROPIC_KEY", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{32,}\b"), "Anthropic API key"),
    Rule(
        "SECRET_ASSIGNMENT",
        re.compile(r"(?i)\b(api[_-]?key|secret|token|password|client[_-]?secret)\b\s*[:=]\s*['\"]?([^'\"\s#`<>]{16,})"),
        "secret-like assignment",
    ),
]

RUNTIME_RULES = [
    Rule("RUNTIME_HOME_PATH", re.compile(r"(?<![A-Za-z0-9_<>])/(?:Users|home)/[A-Za-z0-9._-]+/[^\s`'\")\]}]+"), "host-specific home path"),
    Rule("RUNTIME_ABS_VOLUME_PATH", re.compile(r"(?<![A-Za-z0-9_<>])/(?:Volumes|opt|var|etc)/[^\s`'\")\]}]+"), "host-specific absolute path"),
]
REAL_ENV_PATH_RE = re.compile(r"(^|/)\.env(?:\.[A-Za-z0-9_-]+)?$")


def repo_root() -> Path:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
        return Path(out)
    except Exception:
        return Path.cwd()


def tracked_files(root: Path) -> list[Path]:
    try:
        out = subprocess.check_output(["git", "ls-files", "-z"], cwd=root)
        names = [n.decode() for n in out.split(b"\0") if n]
        return [root / n for n in names]
    except Exception:
        return [p for p in root.rglob("*") if p.is_file()]


def is_text_candidate(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in SKIP_PARTS for part in rel.parts):
        return False
    return path.suffix in TEXT_EXTENSIONS or path.name in {"SKILL.md", ".gitignore"}


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


def scan_line(rel: Path, lineno: int, line: str, *, doc_example: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    if not line.strip():
        return findings

    for rule in SECRET_RULES:
        for match in rule.pattern.finditer(line):
            matched = match.group(0)
            if is_placeholder(matched):
                continue
            if rule.code == "SECRET_ASSIGNMENT":
                value = match.group(2)
                if any(marker in value for marker in (".", "(", ")", "[", "]", "{", "}")):
                    continue
            findings.append(Finding(rel, lineno, rule.code, rule.detail))

    if doc_example:
        return findings

    for rule in RUNTIME_RULES:
        for match in rule.pattern.finditer(line):
            matched = match.group(0)
            if is_placeholder(matched):
                continue
            findings.append(Finding(rel, lineno, rule.code, f"{rule.detail}: {matched}"))
    return findings


def scan_file(path: Path, root: Path) -> list[Finding]:
    rel = path.relative_to(root)
    rel_s = rel.as_posix()
    findings: list[Finding] = []

    if REAL_ENV_PATH_RE.search(rel_s) and not rel_s.endswith(".env.example"):
        findings.append(Finding(rel, 0, "RUNTIME_ENV_FILE", "tracked real env file; commit only .env.example placeholders"))

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return findings

    doc_example = rel_s in DOC_EXAMPLE_ALLOWLIST
    for lineno, line in enumerate(text.splitlines(), start=1):
        findings.extend(scan_line(rel, lineno, line, doc_example=doc_example))
    return findings


def diff_compare_base(root: Path, diff_base: str) -> str:
    """Return a git revision to diff against while including the working tree.

    `git diff origin/main...HEAD` is useful in CI but ignores uncommitted local
    fixes. For local skillify checks, resolve three-dot ranges to their merge
    base and diff that base against the current working tree. On a clean CI
    checkout this is equivalent; locally it validates what would be committed.
    """
    if "..." in diff_base:
        left, right = diff_base.split("...", 1)
        if not right:
            right = "HEAD"
        return subprocess.check_output(["git", "merge-base", left, right], cwd=root, text=True).strip()
    return diff_base


def diff_added_lines(root: Path, diff_base: str) -> list[tuple[Path, int, str]]:
    compare_base = diff_compare_base(root, diff_base)
    out = subprocess.check_output(
        ["git", "diff", "--unified=0", "--diff-filter=ACMRT", compare_base, "--"],
        cwd=root,
        text=True,
        errors="replace",
    )
    current: Path | None = None
    new_line = 0
    rows: list[tuple[Path, int, str]] = []
    for raw in out.splitlines():
        if raw.startswith("+++ "):
            # Supports both default git prefixes (b/) and mnemonic prefixes (w/).
            plus_path = raw[4:]
            if plus_path == "/dev/null":
                current = None
            elif len(plus_path) > 2 and plus_path[1] == "/":
                current = Path(plus_path[2:])
            else:
                current = Path(plus_path)
            continue
        if raw.startswith("@@"):
            m = re.search(r"\+(\d+)(?:,(\d+))?", raw)
            new_line = int(m.group(1)) if m else 0
            continue
        if current is None:
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            rows.append((current, new_line, raw[1:]))
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            continue
        else:
            new_line += 1
    return rows


def scan_diff(root: Path, diff_base: str) -> list[Finding]:
    findings: list[Finding] = []
    checked_paths: set[Path] = set()
    for rel, line_no, line in diff_added_lines(root, diff_base):
        path = root / rel
        if not is_text_candidate(path, root):
            continue
        rel_s = rel.as_posix()
        checked_paths.add(rel)
        doc_example = rel_s in DOC_EXAMPLE_ALLOWLIST
        findings.extend(scan_line(rel, line_no, line, doc_example=doc_example))
    for rel in checked_paths:
        rel_s = rel.as_posix()
        if REAL_ENV_PATH_RE.search(rel_s) and not rel_s.endswith(".env.example"):
            findings.append(Finding(rel, 0, "RUNTIME_ENV_FILE", "new tracked real env file; commit only .env.example placeholders"))
    return findings


def print_findings(findings: list[Finding]) -> None:
    print("Runtime hygiene violations found:", file=__import__("sys").stderr)
    for f in findings:
        where = f"{f.path}:{f.line}" if f.line else str(f.path)
        print(f"- {where}: {f.code}: {f.detail}", file=__import__("sys").stderr)
    print("\nMove real paths/secrets into env vars, approved credential files, or per-skill .env (gitignored).", file=__import__("sys").stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate craft-skills skill runtime hygiene")
    parser.add_argument("paths", nargs="*", help="Optional paths to scan; defaults to tracked repo files")
    parser.add_argument("--root", default=None, help="Repository root")
    parser.add_argument("--diff-base", help="Scan only added lines compared with this git revision/range")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else repo_root().resolve()
    if args.diff_base:
        findings = scan_diff(root, args.diff_base)
    elif args.paths:
        files: list[Path] = []
        for p in args.paths:
            c = (root / p).resolve() if not Path(p).is_absolute() else Path(p).resolve()
            if c.is_dir():
                files.extend(x for x in c.rglob("*") if x.is_file())
            elif c.exists():
                files.append(c)
        findings = []
        for path in sorted(set(files)):
            try:
                path.relative_to(root)
            except ValueError:
                continue
            if is_text_candidate(path, root):
                findings.extend(scan_file(path, root))
    else:
        findings = []
        for path in tracked_files(root):
            if is_text_candidate(path, root):
                findings.extend(scan_file(path, root))

    if findings:
        print_findings(findings)
        return 1
    print("Runtime hygiene OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
