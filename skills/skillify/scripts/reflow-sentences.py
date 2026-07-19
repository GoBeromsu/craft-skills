#!/usr/bin/env python3
"""Enforce sentence-boundary line breaks in Markdown prose
(`skills/skillify/references/contract.md` §4).

The rule: break lines only where a sentence ends — one sentence per line in
paragraphs, one item per line in lists; never hard-wrap mid-sentence at a
column width.

Modes:
  (default)   check the given files/directories; report each suspected
              mid-sentence wrap as `path:line`; exit 1 if any found.
  --fix       rewrite the given files in place to sentence-per-line form.
              Joins wrapped paragraphs and list items, then splits at
              sentence boundaries. Idempotent: fixed files pass the check.
  --advisory  print violations but always exit 0 (non-blocking report).

Frontmatter, code fences, headings, tables, blockquotes, and blank lines pass
through untouched in both modes. Detection is deliberately conservative: a
line is flagged only when it lacks sentence-terminal punctuation AND its
continuation is unambiguous (next line starts lowercase, or the line ends on
a comma/dash/connective). Legacy hard-wrapped files stay green until a caller
passes them explicitly — scope is the caller's choice, like the other
validators' --diff-base mode.

This script owns line-break shape only. Frontmatter/package format is owned
by validate-skill-format.py; secret hygiene by validate-runtime-hygiene.py.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ABBREVIATIONS = [("e.g.", "\x00eg\x00"), ("i.e.", "\x00ie\x00"),
                 ("vs.", "\x00vs\x00"), ("cf.", "\x00cf\x00"),
                 ("etc.", "\x00etc\x00")]

SENTENCE_SPLIT = re.compile(r'([.!?][*_"”\'\)\]`]*)\s+(?=[A-Z“"*`(\[0-9§])')
LIST_START = re.compile(r"^(\s*)([-*+]|\d+\.)\s+")
TERMINAL_END = re.compile(r'[.!?:…][*_"”\'\)\]`]*$')
CONNECTIVE_END = re.compile(
    r"([,;(—–]|\b(?:and|or|the|a|an|of|to|with|for|in|on|at|by|its|their))$"
)
LOWERCASE_START = re.compile(r"^[a-z]")


def _protect(text: str) -> str:
    for abbr, token in ABBREVIATIONS:
        text = text.replace(abbr, token)
    return text


def _restore(text: str) -> str:
    for abbr, token in ABBREVIATIONS:
        text = text.replace(token, abbr)
    return text


def _split_sentences(text: str) -> list[str]:
    parts = SENTENCE_SPLIT.split(_protect(text))
    out = []
    for i in range(0, len(parts), 2):
        terminator = parts[i + 1] if i + 1 < len(parts) else ""
        line = (parts[i] + terminator).strip()
        if line:
            out.append(_restore(line))
    return out


def _is_structural(stripped: str) -> bool:
    """Lines that never participate in prose joining or wrap detection."""
    return (not stripped or stripped.startswith(("#", "|", ">", "<!--"))
            or stripped.startswith("```"))


def _frontmatter_end(lines: list[str]) -> int:
    """Index just past the closing frontmatter fence, or 0 when absent."""
    if not lines or lines[0] != "---":
        return 0
    for i in range(1, len(lines)):
        if lines[i] == "---":
            return i + 1
    return 0


def check_file(path: Path) -> list[int]:
    """Return 1-indexed line numbers of suspected mid-sentence wraps."""
    lines = path.read_text(encoding="utf-8").split("\n")
    start = _frontmatter_end(lines)
    violations: list[int] = []
    in_fence = False
    for i in range(start, len(lines) - 1):
        stripped = lines[i].strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or _is_structural(stripped):
            continue
        if lines[i].endswith("  "):  # explicit Markdown hard break
            continue
        nxt = lines[i + 1].strip()
        if _is_structural(nxt) or nxt.startswith("```"):
            continue
        protected = _protect(stripped)
        if TERMINAL_END.search(protected):
            continue
        next_content = LIST_START.sub("", nxt)
        if LOWERCASE_START.match(next_content) or CONNECTIVE_END.search(protected):
            violations.append(i + 1)
    return violations


def fix_file(path: Path) -> bool:
    """Rewrite to sentence-per-line form; return True when the file changed."""
    original = path.read_text(encoding="utf-8")
    lines = original.split("\n")
    out: list[str] = []
    start = _frontmatter_end(lines)
    out.extend(lines[:start])

    in_fence = False
    paragraph: list[str] = []
    item: tuple[str, str] | None = None

    def flush() -> None:
        nonlocal paragraph, item
        if paragraph:
            out.extend(_split_sentences(" ".join(paragraph)))
            paragraph = []
        if item is not None:
            prefix, text = item
            out.append(prefix + re.sub(r"\s+", " ", text).strip())
            item = None

    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            in_fence = not in_fence
            out.append(line)
        elif in_fence or _is_structural(stripped):
            flush()
            out.append(line)
        elif LIST_START.match(line):
            flush()
            marker = LIST_START.match(line)
            item = (line[: marker.end()], line[marker.end():])
        elif item is not None:
            item = (item[0], item[1] + " " + stripped)
        else:
            paragraph.append(stripped)
    flush()

    result = "\n".join(out)
    if result != original:
        path.write_text(result, encoding="utf-8")
        return True
    return False


def collect(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
        else:
            files.append(p)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+",
                        help="Markdown files or directories (recursed for *.md)")
    parser.add_argument("--fix", action="store_true",
                        help="rewrite files to sentence-per-line instead of checking")
    parser.add_argument("--advisory", action="store_true",
                        help="report violations but always exit 0")
    args = parser.parse_args()

    files = collect(args.paths)
    if args.fix:
        changed = [f for f in files if fix_file(f)]
        for f in changed:
            print(f"reflowed {f}")
        print(f"reflow: {len(changed)} of {len(files)} file(s) changed")
        return 0

    total = 0
    for f in files:
        for lineno in check_file(f):
            print(f"{f}:{lineno}: mid-sentence line break (contract §4)")
            total += 1
    if total:
        print(f"reflow-check: {total} violation(s) in {len(files)} file(s)")
        return 0 if args.advisory else 1
    print(f"reflow-check: OK — {len(files)} file(s) clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
