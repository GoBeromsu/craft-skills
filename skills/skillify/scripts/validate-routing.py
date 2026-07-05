#!/usr/bin/env python3
"""Deterministic Layer-1 routing validator for craft-skills skill packages.

This script owns the DETERMINISTIC half of routing audit:

  1. Load-key resolution — every Load key cell in every RESOLVER.md routing
     table must map to an existing directory under the skills root that contains
     either SKILL.md (leaf skill or flat skill) or RESOLVER.md (area dispatch).
  2. RESOLVER presence — manifest kind=area must carry its own RESOLVER.md.
     Manifest kind=thick may carry child SKILL.md recipes without a RESOLVER.md.
     Without a manifest entry, the legacy heuristic still treats a folder with
     ≥2 immediate-child leaf skills as an area.
  3. Spurious RESOLVER — a flat/single-leaf/thick skill directory must NOT carry a
     RESOLVER.md.

The JUDGMENT half of routing audit — are trigger phrases real user phrases? are
thick-schema fields coherent? are there phantom dispatcher clauses? — belongs to
agents/reviewer.md in the eval lane. This script performs only filesystem stat
checks, never judgment calls.

Finding codes:
  UNRESOLVED_LOAD_KEY    A Load key cell resolves to no SKILL.md or RESOLVER.md.
  SPURIOUS_RESOLVER      A non-area skill directory carries RESOLVER.md.
  MISSING_AREA_RESOLVER  A manifest area, or legacy area-shaped directory, lacks RESOLVER.md.

Exit codes:
  0  No findings (or --advisory mode).
  1  Findings present (unless --advisory).
  2  Internal error (e.g. --root path does not exist).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Default: script lives at skills/skillify/scripts/ → parents[2] is skills/
SKILLS_DIR = Path(__file__).resolve().parents[2]

_TABLE_HEADING_RE = re.compile(r"^##\s+Routing Table\b", re.IGNORECASE)
_MANIFEST_NAME = "skills-manifest.yaml"
_SECTION_HEADING_RE = re.compile(r"^##\s+\S")


@dataclass
class Finding:
    location: str  # path relative to skills_dir (for display)
    code: str
    detail: str


# ---------------------------------------------------------------------------
# Load-key parsing
# ---------------------------------------------------------------------------

def _is_separator_row(cells: list[str]) -> bool:
    """Return True when every non-empty cell consists only of dashes and colons."""
    return all(re.match(r"^[-:]*$", c) for c in cells if c)


def extract_load_keys(resolver_text: str) -> list[str]:
    """Return all Load key values from a RESOLVER.md thick routing table.

    Tolerates:
      - Leading ``dispatcher for:`` line and ## Boundary Charter prose.
      - Backtick-wrapped load keys: ````second-brain/terminology````.
      - Surrounding whitespace in cells.
    Returns an empty list when no ## Routing Table section is found.
    """
    keys: list[str] = []
    in_table = False
    header_seen = False

    for line in resolver_text.splitlines():
        stripped = line.strip()

        if _TABLE_HEADING_RE.match(stripped):
            in_table = True
            continue

        # A new ## section ends the routing table.
        if in_table and _SECTION_HEADING_RE.match(stripped):
            break

        if not in_table or not stripped.startswith("|"):
            continue

        # Split on pipe; discard the empty boundary strings produced by
        # the leading/trailing pipes.
        cols = [c.strip() for c in stripped.split("|")]
        cols = [c for c in cols if c != ""]

        if _is_separator_row(cols):
            continue

        # Header row: first cell contains "Trigger intent".
        if not header_seen:
            if "trigger intent" in cols[0].lower():
                header_seen = True
            continue

        # Data row: Load key is the 3rd column (0-indexed = 2).
        if len(cols) < 3:
            continue
        raw = cols[2].strip().strip("`").strip()
        if raw:
            keys.append(raw)

    return keys


# ---------------------------------------------------------------------------
# Resolution check
# ---------------------------------------------------------------------------

def _resolve_load_key(key: str, skills_dir: Path) -> bool:
    """Return True when key maps to an existing SKILL.md or RESOLVER.md."""
    target = skills_dir / key
    return (target / "SKILL.md").exists() or (target / "RESOLVER.md").exists()


def check_load_keys(resolver_path: Path, skills_dir: Path) -> list[Finding]:
    """Emit UNRESOLVED_LOAD_KEY for every load key that does not resolve."""
    findings: list[Finding] = []
    try:
        text = resolver_path.read_text(encoding="utf-8")
    except OSError as exc:
        rel = resolver_path.relative_to(skills_dir).as_posix()
        findings.append(Finding(rel, "UNRESOLVED_LOAD_KEY", f"could not read file: {exc}"))
        return findings

    rel = resolver_path.relative_to(skills_dir).as_posix()
    for key in extract_load_keys(text):
        if not _resolve_load_key(key, skills_dir):
            findings.append(Finding(
                rel,
                "UNRESOLVED_LOAD_KEY",
                f"load key `{key}` resolves to neither a SKILL.md nor a RESOLVER.md under skills/",
            ))
    return findings


# ---------------------------------------------------------------------------
# Presence rules
# ---------------------------------------------------------------------------

def _count_leaf_skills(directory: Path) -> int:
    """Count immediate child directories of directory that contain a SKILL.md."""
    return sum(
        1 for child in directory.iterdir()
        if child.is_dir() and (child / "SKILL.md").exists()
    )

def _strip_comment_lines(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def load_manifest_kinds(skills_dir: Path) -> dict[str, str]:
    """Return top-level skill name → manifest kind from skills-manifest.yaml."""
    manifest_path = skills_dir.parent / _MANIFEST_NAME
    if not manifest_path.is_file():
        return {}
    try:
        data = json.loads(_strip_comment_lines(manifest_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return {}

    kinds: dict[str, str] = {}
    packages = data.get("packages") if isinstance(data, dict) else None
    if not isinstance(packages, list):
        return kinds

    for package in packages:
        if not isinstance(package, dict):
            continue
        package_id = package.get("id")
        kind = package.get("kind")
        if not isinstance(package_id, str) or not isinstance(kind, str) or "/" not in package_id:
            continue
        skill_name = package_id.split("/", 1)[1]
        if "/" not in skill_name and kind in {"leaf", "thick", "area"}:
            kinds[skill_name] = kind
    return kinds


def check_resolver_presence(skills_dir: Path, manifest_kinds: dict[str, str] | None = None) -> list[Finding]:
    """Enforce RESOLVER rules across all directories under skills_dir.

    skills_dir itself is always exempt (its RESOLVER.md is the master).

    Rules applied to every other directory:
      - manifest kind=area and no RESOLVER.md → MISSING_AREA_RESOLVER
      - manifest kind!=area and has RESOLVER.md → SPURIOUS_RESOLVER
      - without manifest kind, legacy leaf_count >= 2 and no RESOLVER.md → MISSING_AREA_RESOLVER
      - without manifest kind, legacy leaf_count <  2 and has RESOLVER.md → SPURIOUS_RESOLVER
    """
    findings: list[Finding] = []
    manifest_kinds = manifest_kinds or {}

    for dirpath in sorted(skills_dir.rglob("*")):
        if not dirpath.is_dir():
            continue
        if dirpath == skills_dir:
            continue  # master RESOLVER is always exempt

        leaf_count = _count_leaf_skills(dirpath)
        has_resolver = (dirpath / "RESOLVER.md").exists()
        rel = dirpath.relative_to(skills_dir).as_posix()
        declared_kind = manifest_kinds.get(rel) if "/" not in rel else None
        is_area = declared_kind == "area" or (declared_kind is None and leaf_count >= 2)

        if is_area and not has_resolver:
            findings.append(Finding(
                rel,
                "MISSING_AREA_RESOLVER",
                f"{rel}/ has kind={declared_kind or 'legacy-area'} and {leaf_count} leaf skill(s) but no RESOLVER.md",
            ))
        elif not is_area and has_resolver:
            findings.append(Finding(
                rel,
                "SPURIOUS_RESOLVER",
                (
                    f"{rel}/ has kind={declared_kind or 'legacy-non-area'} and {leaf_count} leaf skill(s) "
                    "but carries a RESOLVER.md (RESOLVER required only for areas)"
                ),
            ))

    return findings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate craft-skills RESOLVER.md routing-table load keys and presence rules.",
    )
    ap.add_argument(
        "--root",
        help=(
            "skills/ directory to validate "
            "(default: derived from script location — skills/skillify/scripts/ → ../../..)"
        ),
    )
    ap.add_argument(
        "--advisory",
        action="store_true",
        help="print findings but always exit 0 (non-blocking inventory mode)",
    )
    args = ap.parse_args()

    global SKILLS_DIR
    if args.root:
        SKILLS_DIR = Path(args.root).resolve()

    if not SKILLS_DIR.exists():
        print(f"ERROR: skills directory not found: {SKILLS_DIR}", file=sys.stderr)
        return 2

    resolver_paths = sorted(SKILLS_DIR.rglob("RESOLVER.md"))
    findings: list[Finding] = []

    # Check 1 — load-key resolution across all RESOLVER.md files.
    for rpath in resolver_paths:
        findings.extend(check_load_keys(rpath, SKILLS_DIR))

    manifest_kinds = load_manifest_kinds(SKILLS_DIR)

    # Check 2 — RESOLVER presence rules.
    # Runs even when no RESOLVERs exist (e.g. to catch MISSING_AREA_RESOLVER).
    findings.extend(check_resolver_presence(SKILLS_DIR, manifest_kinds))

    if not findings:
        print(f"routing: OK — {len(resolver_paths)} RESOLVER(s) validated, 0 findings.")
        return 0

    for f in sorted(findings, key=lambda x: (x.code, x.location)):
        print(f"  [{f.code}] {f.location}: {f.detail}")
    print(f"routing: {len(findings)} finding(s) in {len(resolver_paths)} RESOLVER(s).")
    return 0 if args.advisory else 1


if __name__ == "__main__":
    raise SystemExit(main())
