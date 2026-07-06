#!/usr/bin/env python3
"""기술 문서 source manifest 검증기 (harness-agnostic).

technical-report yaml 의 must 항목마다 섹션별 *.sources.yaml manifest 의 source 근거가
붙어 있는지 검사한다. 현재 주장에는 current source 가 필요하고, stale/deferred 만으로는
통과하지 않는다. 민감정보(호스트·포트·토큰·사설 IP·실경로)는 거부한다.

경로는 ${ENV_VAR} 또는 플래그로 받는다(스킬에 박지 않는다):
  TECHNICAL_REPORT_YAML  — technical-report yaml(SSOT) 경로. 기본 ./technical-report.yaml
  TECHNICAL_REPORT_BOOK  — book 디렉토리. 기본 ./book (source-dir 기본은 <book>/sources)
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, NewType

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required", file=sys.stderr)
    sys.exit(2)

SectionId = NewType("SectionId", str)
SourceId = NewType("SourceId", str)

CURRENT_STATUSES: Final = frozenset({"present", "accepted-adr", "current-code", "current-plan"})
NON_CURRENT_STATUSES: Final = frozenset({"historical", "external-background", "deferred", "stale-exclusion"})
ALL_STATUSES: Final = CURRENT_STATUSES | NON_CURRENT_STATUSES
REQUIRED_MANIFEST_FIELDS: Final = (
    "section_id",
    "section_file",
    "source_material_concept",
    "source_of_truth",
    "source_material",
    "stale_exclusions",
    "must_coverage",
)
REQUIRED_SOURCE_FIELDS: Final = ("id", "kind", "status", "path_or_url", "role", "supports")
FIXTURE_NAMES: Final = ("missing-must", "missing-local", "stale-current", "duplicate-section", "secret-leak")
PRIVATE_VALUE_PATTERNS: Final = (
    re.compile(r"(?i)(?:token|secret|password|api[_-]?key)\s*[:=]\s*['\"]?[^'\"\s]{6,}"),
    re.compile(r"\b(?:10|127|172\.(?:1[6-9]|2[0-9]|3[0-1])|192\.168|100)\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    re.compile(r"\b[A-Za-z0-9.-]+\.ts\.net\b"),
    re.compile(r"(?i)\b(?:bearer|sk-[A-Za-z0-9]|ghp_[A-Za-z0-9]|xox[baprs]-)"),
    re.compile(r"(?:^|[\s:'\"])/(?:Users|home|var/private|private)(?:/|[\s,'\"]|$)"),
    re.compile(r"(?i)\b[A-Za-z0-9.-]*(?:tailnet|dev-kube|internal|private)[A-Za-z0-9.-]*\b"),
    re.compile(r"\b[A-Za-z0-9.-]+:\d{2,5}\b"),
)


def env_path(name: str, fallback: Path) -> Path:
    value = os.environ.get(name)
    return Path(value) if value else fallback


@dataclass(frozen=True, slots=True)
class SectionSpec:
    section_id: SectionId
    title: str
    file: str
    coverage_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SourceRef:
    source_id: SourceId
    kind: str
    status: str
    path_or_url: str
    role: str
    supports: tuple[str, ...]
    group: str


@dataclass(frozen=True, slots=True)
class Manifest:
    section_id: SectionId
    section_file: str
    source_material_concept: str
    sources: tuple[SourceRef, ...]
    must_coverage: Mapping[str, tuple[SourceId, ...]]
    raw_text: str
    origin: str


def load_structure(yaml_path: Path) -> Mapping[SectionId, SectionSpec]:
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("document"), dict):
        raise ConfigError("technical-report yaml missing document mapping")

    specs: dict[SectionId, SectionSpec] = {}
    for raw_id, raw_section in raw["document"].items():
        if not isinstance(raw_id, str) or not isinstance(raw_section, dict):
            raise ConfigError("technical-report yaml has invalid section entry")
        coverage_keys = section_coverage_keys(raw_section)
        section_id = SectionId(raw_id)
        specs[section_id] = SectionSpec(
            section_id=section_id,
            title=required_str(raw_section, "title", raw_id),
            file=required_str(raw_section, "file", raw_id),
            coverage_keys=coverage_keys,
        )
    return specs


def section_coverage_keys(raw_section: Mapping[str, object]) -> tuple[str, ...]:
    keys: list[str] = []
    for index, _item in enumerate(required_list(raw_section, "must", "section")):
        keys.append(f"section.must.{index}")
    headings = raw_section.get("headings") or {}
    if not isinstance(headings, dict):
        raise ConfigError("technical-report yaml headings must be a mapping")
    for heading, raw_heading in headings.items():
        if not isinstance(heading, str) or not isinstance(raw_heading, dict):
            raise ConfigError("technical-report yaml heading entry is invalid")
        for index, _item in enumerate(required_list(raw_heading, "must", heading)):
            keys.append(f"heading.{heading}.must.{index}")
    return tuple(keys)


def required_str(data: Mapping[str, object], key: str, context: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{context}: required string field missing: {key}")
    return value


def required_list(data: Mapping[str, object], key: str, context: str) -> list[object]:
    value = data.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ConfigError(f"{context}: expected list field: {key}")
    return value


def load_manifests(source_dir: Path) -> tuple[Manifest, ...]:
    manifests: list[Manifest] = []
    for path in sorted(source_dir.glob("*.sources.yaml")):
        text = path.read_text(encoding="utf-8")
        try:
            docs = list(yaml.safe_load_all(text))
        except yaml.YAMLError as exc:
            raise ManifestParseError(f"{path}: invalid YAML: {exc}") from exc
        for index, doc in enumerate(docs, start=1):
            if doc is None:
                continue
            if not isinstance(doc, dict):
                raise ManifestParseError(f"{path}: document {index} must be a mapping")
            manifests.append(parse_manifest(doc, text, f"{path}#{index}"))
    return tuple(manifests)


def parse_manifest(raw: Mapping[str, object], raw_text: str, origin: str) -> Manifest:
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in raw:
            raise ManifestParseError(f"{origin}: required field missing: {field}")
    section_id = SectionId(required_str(raw, "section_id", origin))
    sources: list[SourceRef] = []
    for group in ("source_of_truth", "source_material", "stale_exclusions"):
        entries = raw.get(group)
        if not isinstance(entries, list):
            raise ManifestParseError(f"{origin}: {group} must be a list")
        for index, entry in enumerate(entries, start=1):
            sources.append(parse_source(entry, group, index, origin))
    coverage = parse_coverage(raw.get("must_coverage"), origin)
    return Manifest(
        section_id=section_id,
        section_file=required_str(raw, "section_file", origin),
        source_material_concept=required_str(raw, "source_material_concept", origin),
        sources=tuple(sources),
        must_coverage=coverage,
        raw_text=raw_text,
        origin=origin,
    )


def parse_source(raw: object, group: str, index: int, origin: str) -> SourceRef:
    if not isinstance(raw, dict):
        raise ManifestParseError(f"{origin}: {group}[{index}] must be a mapping")
    for field in REQUIRED_SOURCE_FIELDS:
        if field not in raw:
            raise ManifestParseError(f"{origin}: {group}[{index}] missing source field: {field}")
    status = required_str(raw, "status", origin)
    if status not in ALL_STATUSES:
        raise ManifestParseError(f"{origin}: {group}[{index}] unknown status: {status}")
    supports = raw.get("supports")
    if not isinstance(supports, list) or not all(isinstance(item, str) and item.strip() for item in supports):
        raise ManifestParseError(f"{origin}: {group}[{index}].supports must be a non-empty string list")
    return SourceRef(
        source_id=SourceId(required_str(raw, "id", origin)),
        kind=required_str(raw, "kind", origin),
        status=status,
        path_or_url=required_str(raw, "path_or_url", origin),
        role=required_str(raw, "role", origin),
        supports=tuple(supports),
        group=group,
    )


def parse_coverage(raw: object, origin: str) -> Mapping[str, tuple[SourceId, ...]]:
    if not isinstance(raw, dict):
        raise ManifestParseError(f"{origin}: must_coverage must be a mapping")
    coverage: dict[str, tuple[SourceId, ...]] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            raise ManifestParseError(f"{origin}: must_coverage keys must be strings")
        if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
            raise ManifestParseError(f"{origin}: must_coverage.{key} must be a non-empty source-id list")
        coverage[key] = tuple(SourceId(item) for item in value)
    return coverage


def validate_manifest_set(
    specs: Mapping[SectionId, SectionSpec],
    manifests: Sequence[Manifest],
    repo_root: Path,
    section_filter: SectionId | None,
) -> tuple[str, ...]:
    errors: list[str] = []
    selected_specs = filter_specs(specs, section_filter)
    if not manifests:
        errors.append("missing source manifest: no *.sources.yaml files found")
        errors.append("section manifest coverage missing for all configured sections")
        return tuple(errors)

    ids = [manifest.section_id for manifest in manifests]
    for section_id, count in Counter(ids).items():
        if count > 1:
            errors.append(f"duplicate section manifest: {section_id}")

    by_id = {manifest.section_id: manifest for manifest in manifests}
    expected_ids = set(selected_specs)
    actual_ids = set(ids)
    for section_id in sorted(expected_ids - actual_ids):
        errors.append(f"missing section manifest: {section_id}")
    for section_id in sorted(actual_ids - set(specs)):
        errors.append(f"unknown section manifest: {section_id}")

    for section_id, spec in selected_specs.items():
        manifest = by_id.get(section_id)
        if manifest is None:
            continue
        errors.extend(validate_manifest(spec, manifest, repo_root))
    return tuple(errors)


def filter_specs(
    specs: Mapping[SectionId, SectionSpec],
    section_filter: SectionId | None,
) -> Mapping[SectionId, SectionSpec]:
    if section_filter is None:
        return specs
    if section_filter not in specs:
        raise ConfigError(f"unknown --section: {section_filter}")
    return {section_filter: specs[section_filter]}


def validate_manifest(spec: SectionSpec, manifest: Manifest, repo_root: Path) -> tuple[str, ...]:
    errors: list[str] = []
    if manifest.section_file != spec.file:
        errors.append(f"{manifest.origin}: section_file mismatch: expected {spec.file}, got {manifest.section_file}")
    errors.extend(scan_sensitive_text(manifest.raw_text, manifest.origin))

    source_ids = [source.source_id for source in manifest.sources]
    for source_id, count in Counter(source_ids).items():
        if count > 1:
            errors.append(f"{manifest.origin}: duplicate source id: {source_id}")
    source_by_id = {source.source_id: source for source in manifest.sources}
    for source in manifest.sources:
        errors.extend(validate_source(source, repo_root, manifest.origin))

    expected_keys = set(spec.coverage_keys)
    actual_keys = set(manifest.must_coverage)
    for key in sorted(expected_keys - actual_keys):
        errors.append(f"{manifest.origin}: missing must_coverage key: {key}")
    for key in sorted(actual_keys - expected_keys):
        errors.append(f"{manifest.origin}: unknown must_coverage key: {key}")
    for key, ids in manifest.must_coverage.items():
        support_sources = [source_by_id[source_id] for source_id in ids if source_id in source_by_id]
        for source_id in ids:
            if source_id not in source_by_id:
                errors.append(f"{manifest.origin}: {key} cites unknown source id: {source_id}")
        if support_sources and all(source.status in NON_CURRENT_STATUSES for source in support_sources):
            statuses = ", ".join(sorted({source.status for source in support_sources}))
            errors.append(f"{manifest.origin}: current claim {key} backed only by non-current sources: {statuses}")
    return tuple(errors)


def validate_source(source: SourceRef, repo_root: Path, origin: str) -> tuple[str, ...]:
    errors: list[str] = []
    path_or_url = source.path_or_url
    if is_non_local(path_or_url):
        if source.status in CURRENT_STATUSES:
            errors.append(f"{origin}: non-local source must use non-current status: {source.source_id}")
        return tuple(errors)
    candidate = repo_root / path_or_url
    if not candidate.exists():
        errors.append(f"{origin}: missing local source path for {source.source_id}: {path_or_url}")
    return tuple(errors)


def is_non_local(path_or_url: str) -> bool:
    return path_or_url.startswith(("http://", "https://"))


def scan_sensitive_text(text: str, origin: str) -> tuple[str, ...]:
    errors: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for pattern in PRIVATE_VALUE_PATTERNS:
            if pattern.search(line):
                errors.append(f"{origin}: sensitive/private value rejected at line {line_no}")
                break
    return tuple(errors)


def check_book_mentions(book_dir: Path, manifests: Sequence[Manifest]) -> tuple[str, ...]:
    errors: list[str] = []
    for manifest in manifests:
        book_file = book_dir / manifest.section_file
        if not book_file.is_file():
            errors.append(f"{manifest.origin}: section file missing for mention check: {manifest.section_file}")
            continue
        text = book_file.read_text(encoding="utf-8")
        tokens = {token for source in manifest.sources for token in source.supports if len(token) >= 4}
        if tokens and not any(token in text for token in tokens):
            errors.append(f"{manifest.origin}: no source support labels are mentioned in {manifest.section_file}")
    return tuple(errors)


def explain_manifests(specs: Mapping[SectionId, SectionSpec], manifests: Sequence[Manifest]) -> str:
    lines = ["source manifest explanation"]
    by_id = {manifest.section_id: manifest for manifest in manifests}
    for section_id, spec in specs.items():
        manifest = by_id.get(section_id)
        if manifest is None:
            lines.append(f"- {section_id}: missing manifest for {spec.file}")
            continue
        lines.append(f"- {section_id}: {manifest.section_file}")
        lines.append(f"  source_of_truth/source_material/stale_exclusions: {len(manifest.sources)} sources")
        lines.append(f"  must_coverage: {len(manifest.must_coverage)}/{len(spec.coverage_keys)}")
    return "\n".join(lines)


def run_fixture(name: str, yaml_path: Path) -> int:
    specs = load_structure(yaml_path)
    first = next(iter(specs.values()))
    with tempfile.TemporaryDirectory(prefix="technical-report-source-fixture-") as tmp:
        root = Path(tmp)
        source_dir = root / "sources"
        source_dir.mkdir()
        write_fixture(source_dir, name, first)
        manifests = load_fixture_manifests(source_dir)
        errors = validate_manifest_set(specs, manifests, root, first.section_id)
        print(f"[fixture {name}]")
        for error in errors:
            print(f"ERROR: {error}")
        if errors:
            return 1
        print("OK")
        return 0


def write_fixture(source_dir: Path, name: str, spec: SectionSpec) -> None:
    key = spec.coverage_keys[0]
    current_source: dict[str, object] = {
        "id": "current",
        "kind": "repo-file",
        "status": "present",
        "path_or_url": "existing.md",
        "role": "current support",
        "supports": ["fixture"],
    }
    base = {
        "section_id": str(spec.section_id),
        "section_file": spec.file,
        "source_material_concept": "fixture concept",
        "source_of_truth": [current_source],
        "source_material": [],
        "stale_exclusions": [],
        "must_coverage": {coverage_key: ["current"] for coverage_key in spec.coverage_keys},
    }
    (source_dir.parent / "existing.md").write_text("fixture\n", encoding="utf-8")
    match name:
        case "missing-must":
            base["must_coverage"] = {}
        case "missing-local":
            current_source["path_or_url"] = "missing.md"
        case "stale-current":
            current_source["status"] = "historical"
        case "duplicate-section":
            write_yaml(source_dir / "a.sources.yaml", base)
            write_yaml(source_dir / "b.sources.yaml", base)
            return
        case "secret-leak":
            base["source_material_concept"] = "tok" + "en: sample-secret-value"
        case unreachable:
            raise ConfigError(f"unknown fixture: {unreachable}")
    if name == "stale-current":
        base["must_coverage"] = {key: ["current"]}
    write_yaml(source_dir / "fixture.sources.yaml", base)


def load_fixture_manifests(source_dir: Path) -> tuple[Manifest, ...]:
    manifests: list[Manifest] = []
    for path in sorted(source_dir.glob("*.sources.yaml")):
        text = path.read_text(encoding="utf-8")
        try:
            docs = list(yaml.safe_load_all(text))
        except yaml.YAMLError as exc:
            raise ManifestParseError(f"{path.name}: invalid YAML: {exc}") from exc
        for index, doc in enumerate(docs, start=1):
            if doc is None:
                continue
            if not isinstance(doc, dict):
                raise ManifestParseError(f"{path.name}: document {index} must be a mapping")
            manifests.append(parse_manifest(doc, text, f"{path.name}#{index}"))
    return tuple(manifests)


def write_yaml(path: Path, data: Mapping[str, object]) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def print_errors(errors: Iterable[str]) -> None:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)


class ConfigError(RuntimeError):
    pass


class ManifestParseError(RuntimeError):
    pass


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate technical-report source manifests")
    parser.add_argument("--yaml", type=Path, default=None,
                        help="technical-report yaml(SSOT) path (default: $TECHNICAL_REPORT_YAML or ./technical-report.yaml)")
    parser.add_argument("--book", type=Path, default=None,
                        help="book directory (default: $TECHNICAL_REPORT_BOOK or ./book)")
    parser.add_argument("--source-dir", type=Path, default=None, help="directory containing *.sources.yaml manifests")
    parser.add_argument("--section", type=str, default=None, help="validate one section id, such as 4_approach")
    parser.add_argument("--explain", action="store_true", help="print manifest coverage summary")
    parser.add_argument("--check-book-mentions", action="store_true", help="check source support labels appear in section text")
    parser.add_argument("--fixture", choices=FIXTURE_NAMES, default=None, help="run a built-in negative fixture")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    yaml_path = args.yaml or env_path("TECHNICAL_REPORT_YAML", Path("technical-report.yaml"))
    if args.fixture is not None:
        if not yaml_path.is_file():
            print(f"ERROR: yaml not found: {yaml_path} (--yaml or $TECHNICAL_REPORT_YAML)", file=sys.stderr)
            return 2
        return run_fixture(args.fixture, yaml_path)
    try:
        specs = load_structure(yaml_path)
        book_dir = args.book or env_path("TECHNICAL_REPORT_BOOK", Path("book"))
        source_dir = args.source_dir or book_dir / "sources"
        section_filter = SectionId(args.section) if args.section else None
        if not source_dir.is_dir():
            print_errors([f"missing source manifest directory: {source_dir}", "section manifest coverage missing"])
            return 1
        manifests = load_manifests(source_dir)
        errors = list(validate_manifest_set(specs, manifests, Path.cwd(), section_filter))
        if args.check_book_mentions:
            errors.extend(check_book_mentions(book_dir, manifests))
        if args.explain:
            selected = filter_specs(specs, section_filter)
            print(explain_manifests(selected, manifests))
        if errors:
            print_errors(errors)
            return 1
        print(f"OK: {len(manifests)} source manifest(s) validated")
        return 0
    except (ConfigError, ManifestParseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
