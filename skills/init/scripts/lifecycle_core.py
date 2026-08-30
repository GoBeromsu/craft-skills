"""Deterministic, effect-free lifecycle calculations for the init package."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import unicodedata
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = 1
SNAPSHOT_NAME = ".agents-map.json"
JOURNAL_NAME = ".agents-map.transaction.json"
SHIM_BYTES = b"@AGENTS.md\n"
NEW_FILE_MODE = 0o644
MARKER_BEGIN = "<!-- init:managed id={id} sha256={sha256} -->"
MARKER_END = "<!-- /init:managed id={id} -->"
_HASH = re.compile(r"^[0-9a-f]{64}$")
_MARKER = re.compile(r"^<!-- init:managed id=([^\s>]+) sha256=([0-9a-f]{64}) -->\n(.*?)<!-- /init:managed id=\1 -->\n?$", re.DOTALL)
EXCLUDED_DIRS = frozenset({".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", ".cache", "__pycache__"})
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_PINNED_ROOT_FD: ContextVar[int | None] = ContextVar("init_lifecycle_root_fd", default=None)
_CODE_SUFFIXES = frozenset({".c", ".cc", ".cpp", ".cs", ".go", ".h", ".hpp", ".java", ".js", ".jsx", ".kt", ".php", ".py", ".rb", ".rs", ".sh", ".swift", ".ts", ".tsx"})
_CONFIG_NAMES = frozenset({"Cargo.toml", "Makefile", "go.mod", "package.json", "pyproject.toml", "setup.cfg", "setup.py", "tox.ini", "tsconfig.json"})
_BOUNDARY_NAMES = frozenset({"__init__.py", "index.js", "index.jsx", "index.ts", "index.tsx", "main.go", "mod.rs"})
_FACTOR_NAMES = ("file-count", "subdirectory-count", "code-ratio", "unique-patterns", "module-boundary", "symbol-density", "export-count", "reference-centrality")


def canonical_json(value: Any, *, pretty: bool = False) -> bytes:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=None if pretty else (",", ":"), indent=2 if pretty else None)
    return (text + "\n" if pretty else text).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_path(value: str | PurePosixPath, *, allow_root: bool = False) -> str:
    value = unicodedata.normalize("NFC", str(value))
    if value == "." and allow_root:
        return value
    if not value or value == "." or value.startswith("/") or "\\" in value or "\x00" in value:
        raise ValueError("path must be a non-empty relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError("path contains an unsafe component")
    normalized = path.as_posix()
    if normalized != value:
        raise ValueError("path is not normalized")
    return normalized


def normalized_relative(root: Path, path: Path, *, allow_root: bool = False) -> str:
    root = root.resolve(strict=True)
    try:
        relative = path.absolute().relative_to(root)
    except ValueError as exc:
        raise ValueError("path escapes repository root") from exc
    return normalize_path(relative.as_posix(), allow_root=allow_root)


def safe_path(root: Path, relative: str, *, require_exists: bool = False) -> Path:
    relative = normalize_path(relative)
    root_real = root.resolve(strict=True)
    candidate = root.joinpath(*PurePosixPath(relative).parts)
    parent = candidate.parent
    try:
        parent_real = parent.resolve(strict=True)
    except FileNotFoundError:
        parent_real = parent.resolve(strict=False)
    try:
        parent_real.relative_to(root_real)
    except ValueError as exc:
        raise ValueError("path parent escapes repository root") from exc
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            break
        if stat.S_ISLNK(info.st_mode):
            raise ValueError("symlink path is unsafe")
    if require_exists:
        info = os.lstat(candidate)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("path is not a regular file")
    return candidate


def mode_of(st_mode: int) -> int:
    mode = stat.S_IMODE(st_mode)
    if not 0 <= mode <= 0o7777:
        raise ValueError("unsupported mode")
    return mode


@contextmanager
def operation_root(root: Path) -> Iterable[None]:
    existing = _PINNED_ROOT_FD.get()
    if existing is not None:
        yield
        return
    descriptor = os.open(
        root.resolve(strict=True),
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | _NOFOLLOW,
    )
    token = _PINNED_ROOT_FD.set(descriptor)
    try:
        yield
    finally:
        _PINNED_ROOT_FD.reset(token)
        os.close(descriptor)


def pinned_root_fd(root: Path) -> int:
    pinned = _PINNED_ROOT_FD.get()
    if pinned is not None:
        return os.dup(pinned)
    return os.open(
        root.resolve(strict=True),
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | _NOFOLLOW,
    )


def file_observation(root: Path, relative: str) -> dict[str, Any]:
    data, mode = _read_relative_nofollow(root, relative)
    return {"path": normalize_path(relative), "sha256": sha256_bytes(data), "mode": mode, "size": len(data)}


def _read_relative_nofollow(root: Path, relative: str) -> tuple[bytes, int]:
    parts = PurePosixPath(normalize_path(relative)).parts
    directory_fd = pinned_root_fd(root)
    try:
        for part in parts[:-1]:
            next_fd = os.open(
                part,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | _NOFOLLOW,
                dir_fd=directory_fd,
            )
            os.close(directory_fd)
            directory_fd = next_fd
        descriptor = os.open(parts[-1], os.O_RDONLY | _NOFOLLOW | getattr(os, "O_NONBLOCK", 0), dir_fd=directory_fd)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("path is not a regular file")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks), mode_of(info.st_mode)
        finally:
            os.close(descriptor)
    finally:
        os.close(directory_fd)


def managed_envelope(managed_id: str, payload: bytes) -> bytes:
    if not managed_id or ">" in managed_id or any(character.isspace() for character in managed_id):
        raise ValueError("managed id must be non-empty and whitespace-free")
    payload_hash = sha256_bytes(payload)
    try:
        payload_text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("managed payload must be UTF-8") from exc
    if not payload.endswith(b"\n"):
        raise ValueError("managed payload must end with LF")
    return (MARKER_BEGIN.format(id=managed_id, sha256=payload_hash) + "\n" + payload_text + MARKER_END.format(id=managed_id) + "\n").encode("utf-8")


def parse_managed_envelope(data: bytes) -> dict[str, str] | None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    match = _MARKER.match(text)
    if not match:
        return None
    managed_id, payload_hash, payload = match.groups()
    raw_payload = payload.encode("utf-8")
    if sha256_bytes(raw_payload) != payload_hash:
        return None
    return {"managed_id": managed_id, "payload": payload, "payload_sha256": payload_hash, "file_sha256": sha256_bytes(data)}


def _managed_region_span(data: bytes, managed_id: str, payload_hash: str) -> tuple[int, int]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("managed region file must be UTF-8") from error
    begin = f"<!-- init:managed id={managed_id} sha256={payload_hash} -->"
    end = f"<!-- /init:managed id={managed_id} -->"
    start = text.find(begin)
    finish = text.find(end, start + len(begin)) if start >= 0 else -1
    if start < 0 or finish < 0 or text.find(begin, start + 1) >= 0:
        raise ValueError("managed region is missing or ambiguous")
    payload_start = start + len(begin)
    if payload_start >= len(text) or text[payload_start] != "\n":
        raise ValueError("managed region payload boundary is invalid")
    payload_start += 1
    payload_end = finish
    if sha256_bytes(text[payload_start:payload_end].encode("utf-8")) != payload_hash:
        raise ValueError("managed region payload hash is invalid")
    finish += len(end)
    if finish < len(text) and text[finish] == "\n":
        finish += 1
    return len(text[:start].encode("utf-8")), len(text[:finish].encode("utf-8"))


def stable_id(prefix: str, fields: Mapping[str, Any]) -> str:
    return f"{prefix}-{sha256_bytes(canonical_json(dict(fields)))[:12]}"


def loading_result(evidence: Mapping[str, Any]) -> dict[str, str]:
    status = str(evidence.get("status", "unknown"))
    candidate = evidence.get("loading_class")
    classes = {"file-scoped", "recursive", "ancestor-only"}
    if status == "verified" and candidate in classes:
        return {"status": status, "loading_class": str(candidate)}
    if status not in {"unknown", "conflicted", "unavailable", "version-mismatch"}:
        status = "unknown"
    return {"status": status, "loading_class": "unknown"}


def _classify_bound_loading_observations(observations: Mapping[str, Any]) -> dict[str, str]:
    expected = {
        "file-scoped": {
            "root": ["ROOT"],
            "child": ["CHILD"],
            "sibling": ["SIBLING"],
            "precedence": {"child": "CHILD", "sibling": "SIBLING"},
        },
        "recursive": {
            "root": ["ROOT", "CHILD", "SIBLING"],
            "child": ["CHILD"],
            "sibling": ["SIBLING"],
            "precedence": {"child": "CHILD", "sibling": "SIBLING"},
        },
        "ancestor-only": {
            "root": ["ROOT"],
            "child": ["ROOT", "CHILD"],
            "sibling": ["ROOT", "SIBLING"],
            "precedence": {"child": "CHILD", "sibling": "SIBLING"},
        },
    }
    normalized: dict[str, Any] = {}
    for location in ("root", "child", "sibling"):
        value = observations.get(location)
        if not isinstance(value, list) or not all(isinstance(marker, str) for marker in value):
            return {"status": "unknown", "loading_class": "unknown"}
        normalized[location] = value
    precedence = observations.get("precedence")
    if not isinstance(precedence, Mapping) or dict(precedence) != {"child": "CHILD", "sibling": "SIBLING"}:
        return {"status": "unknown", "loading_class": "unknown"}
    normalized["precedence"] = dict(precedence)
    matches = [name for name, matrix in expected.items() if normalized == matrix]
    if len(matches) == 1:
        return {"status": "verified", "loading_class": matches[0]}
    if matches:
        return {"status": "conflicted", "loading_class": "unknown"}
    return {"status": "unknown", "loading_class": "unknown"}


def _receipt_status(receipt: Mapping[str, Any], fixture_sha256: str) -> dict[str, str]:
    source_id = receipt.get("source_id")
    runtime_version = receipt.get("runtime_version")
    source_probe = receipt.get("source_probe_result")
    version_probe = receipt.get("version_probe_result")
    execution_status = receipt.get("execution_status")
    observations = receipt.get("observations")
    if not isinstance(source_id, str) or not source_id or not isinstance(runtime_version, str) or not runtime_version:
        return {"status": "unknown", "loading_class": "unknown"}
    if not isinstance(source_probe, Mapping) or not isinstance(version_probe, Mapping):
        return {"status": "unknown", "loading_class": "unknown"}
    if source_probe.get("status") == "unavailable" or version_probe.get("status") == "unavailable" or execution_status == "unavailable":
        return {"status": "unavailable", "loading_class": "unknown"}
    if source_probe.get("source_id") != source_id or source_probe.get("status") != "available":
        return {"status": "conflicted", "loading_class": "unknown"}
    if version_probe.get("runtime_version") != runtime_version:
        return {"status": "version-mismatch", "loading_class": "unknown"}
    if version_probe.get("status") != "available" or execution_status != "applicable":
        return {"status": "unknown", "loading_class": "unknown"}
    if receipt.get("fixture_sha256") != fixture_sha256 or not isinstance(observations, Mapping):
        return {"status": "unknown", "loading_class": "unknown"}
    raw_result_sha256 = receipt.get("raw_result_sha256")
    if not isinstance(raw_result_sha256, str) or raw_result_sha256 != sha256_bytes(canonical_json(dict(observations))):
        return {"status": "unknown", "loading_class": "unknown"}
    return _classify_bound_loading_observations(observations)


def coverage_status(expected_chain: Iterable[str], observed_chain: Iterable[str] | None, evidence: Mapping[str, Any], *, fallback_present: bool = False) -> dict[str, str]:
    result = loading_result(evidence)
    expected = list(expected_chain)
    observed = list(observed_chain or [])
    if result["loading_class"] == "unknown":
        return {"status": "unverified", "basis": "root-fallback" if fallback_present else "none"}
    if observed == expected:
        return {"status": "covered", "basis": "native"}
    if not observed or any(path not in observed for path in expected):
        return {"status": "gap", "basis": "native"}
    return {"status": "ambiguous", "basis": "native"}


def _walk(root: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    directories: dict[str, dict[str, Any]] = {".": {"files": [], "subdirectories": []}}
    exclusions: list[dict[str, str]] = []
    findings: list[dict[str, str]] = []
    try:
        pinned = _PINNED_ROOT_FD.get()
        walker = (
            os.fwalk(".", topdown=True, follow_symlinks=False, dir_fd=pinned)
            if pinned is not None
            else os.fwalk(root, topdown=True, follow_symlinks=False)
        )
        for current, names, files, directory_fd in walker:
            relative_text = (
                PurePosixPath(current).as_posix().removeprefix("./")
                if pinned is not None
                else os.path.relpath(current, root)
            )
            current_relative = "." if relative_text == "." else normalize_path(PurePosixPath(relative_text).as_posix())
            record = directories.setdefault(current_relative, {"files": [], "subdirectories": []})
            kept: list[str] = []
            for name in sorted(names):
                relative = normalize_path(name if current_relative == "." else f"{current_relative}/{name}")
                try:
                    info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                except OSError:
                    findings.append({"code": "INITV4-E-UNREADABLE", "path": relative})
                    continue
                if stat.S_ISLNK(info.st_mode):
                    findings.append({"code": "INITV4-E-SYMLINK", "path": relative})
                elif name in EXCLUDED_DIRS:
                    exclusions.append({"path": relative, "reason": "excluded-directory"})
                elif stat.S_ISDIR(info.st_mode):
                    kept.append(name)
                    record["subdirectories"].append(relative)
                    directories.setdefault(relative, {"files": [], "subdirectories": []})
                else:
                    findings.append({"code": "INITV4-E-SPECIAL-FILE", "path": relative})
            names[:] = kept
            relevant = False
            for name in sorted(files):
                relative = normalize_path(name if current_relative == "." else f"{current_relative}/{name}")
                try:
                    info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                except OSError:
                    findings.append({"code": "INITV4-E-UNREADABLE", "path": relative})
                    continue
                if stat.S_ISLNK(info.st_mode):
                    findings.append({"code": "INITV4-E-SYMLINK", "path": relative})
                elif not stat.S_ISREG(info.st_mode):
                    findings.append({"code": "INITV4-E-SPECIAL-FILE", "path": relative})
                elif name not in {"AGENTS.md", "CLAUDE.md", SNAPSHOT_NAME, JOURNAL_NAME} and ".craft-init-v4-" not in name:
                    try:
                        descriptor = os.open(
                            name,
                            os.O_RDONLY | _NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
                            dir_fd=directory_fd,
                        )
                        os.close(descriptor)
                    except OSError:
                        findings.append({"code": "INITV4-E-UNREADABLE", "path": relative})
                    else:
                        relevant = True
                        record["files"].append(relative)
            if not relevant and current_relative != "." and not record["subdirectories"]:
                directories.pop(current_relative, None)
    except OSError:
        findings.append({"code": "INITV4-E-UNREADABLE", "path": "."})
    return directories, sorted(exclusions, key=lambda item: item["path"]), sorted(findings, key=lambda item: (item["path"], item["code"]))


def _factors(directory: str, record: Mapping[str, Any]) -> tuple[list[dict[str, Any]], int, bool]:
    files = sorted(str(path) for path in record.get("files", []))
    subdirectories = sorted(str(path) for path in record.get("subdirectories", []))
    names = {PurePosixPath(path).name for path in files}
    code_files = [path for path in files if PurePosixPath(path).suffix.lower() in _CODE_SUFFIXES]
    ratio = len(code_files) / len(files) if files else 0.0
    own_config = bool(names & _CONFIG_NAMES)
    boundary = bool(names & _BOUNDARY_NAMES)
    measured = [
        ("file-count", len(files), 3 if len(files) > 20 else 0, files),
        ("subdirectory-count", len(subdirectories), 2 if len(subdirectories) > 5 else 0, subdirectories),
        ("code-ratio", ratio, 2 if ratio > 0.70 else 0, files),
        ("unique-patterns", own_config, 1 if own_config else 0, sorted(path for path in files if PurePosixPath(path).name in _CONFIG_NAMES)),
        ("module-boundary", boundary, 2 if boundary else 0, sorted(path for path in files if PurePosixPath(path).name in _BOUNDARY_NAMES)),
    ]
    factors = [{"name": name, "measured": True, "value": value, "points": points, "evidence_paths": evidence} for name, value, points, evidence in measured]
    factors.extend({"name": name, "measured": False, "value": None, "points": 0, "evidence_paths": []} for name in _FACTOR_NAMES[5:])
    return factors, sum(item["points"] for item in factors), own_config or boundary


def _loader_snapshot(evidence: Mapping[str, Any] | None) -> dict[str, Any]:
    resolved = loading_result(evidence or {})
    receipt = evidence.get("receipt") if evidence and isinstance(evidence.get("receipt"), Mapping) else {}
    status_map = {
        "verified": "probe-verified",
        "conflicted": "conflicted",
        "unavailable": "unavailable",
        "version-mismatch": "version-mismatch",
        "unknown": "source-only" if receipt else "unavailable",
    }
    return {
        "loader_class": resolved["loading_class"],
        "evidence_status": status_map.get(resolved["status"], "unavailable"),
        "source_id": receipt.get("source_id") if isinstance(receipt.get("source_id"), str) else None,
        "runtime_version": receipt.get("runtime_version") if isinstance(receipt.get("runtime_version"), str) else None,
        "probe_fixture_sha256": evidence.get("fixture_sha256") if evidence and isinstance(evidence.get("fixture_sha256"), str) and _HASH.match(str(evidence.get("fixture_sha256"))) else None,
        "probe_result_sha256": receipt.get("raw_result_sha256") if isinstance(receipt.get("raw_result_sha256"), str) and _HASH.match(str(receipt.get("raw_result_sha256"))) else None,
    }


def discover_topology(root: Path, *, max_depth: int = 3, shim_policy: str = "off", loading_evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if not 1 <= max_depth <= 32 or shim_policy not in {"on", "off"}:
        raise ValueError("invalid topology settings")
    root = root.absolute() if _PINNED_ROOT_FD.get() is not None else root.resolve(strict=True)
    inventory, exclusions, findings = _walk(root)
    nodes: list[dict[str, Any]] = []
    for directory in sorted(inventory):
        depth = 0 if directory == "." else len(PurePosixPath(directory).parts)
        factors, score, distinct = _factors(directory, inventory[directory])
        decision = "root" if directory == "." else ("high-score" if score > 15 else "distinct-domain")
        if directory != "." and (depth > max_depth or not (score > 15 or (8 <= score <= 15 and distinct))):
            continue
        agents_path = "AGENTS.md" if directory == "." else f"{directory}/AGENTS.md"
        nodes.append({"directory": directory, "agents_path": agents_path, "parent_agents_path": None, "managed_id": stable_id("init", {"directory": directory}), "score": score, "decision": decision, "factors": factors})
    for node in nodes:
        if node["directory"] == ".":
            continue
        ancestors = [candidate for candidate in nodes if candidate["directory"] != node["directory"] and (candidate["directory"] == "." or node["directory"].startswith(candidate["directory"] + "/"))]
        node["parent_agents_path"] = max(ancestors, key=lambda item: 0 if item["directory"] == "." else len(PurePosixPath(item["directory"]).parts))["agents_path"]
    evidence = loading_result(loading_evidence or {})
    coverage = []
    for directory in sorted(inventory):
        chain = [node["agents_path"] for node in nodes if node["directory"] == "." or directory == node["directory"] or directory.startswith(node["directory"] + "/")]
        state = coverage_status(chain, None, evidence, fallback_present=bool(chain))
        coverage.append({"directory": directory, "expected_chain": chain, "status_at_apply": state["status"], "basis_at_apply": state["basis"]})
    return {"max_depth": max_depth, "shim_policy": shim_policy, "loader": _loader_snapshot(loading_evidence), "nodes": nodes, "coverage": coverage, "root_fallback_payload_sha256": None, "findings": findings, "exclusions": exclusions, "repository_name": root.name, "_root": root, "_inventory": inventory}


def _render_managed_payload(
    topology: Mapping[str, Any],
    node: Mapping[str, Any],
    migrated_claude: str | None = None,
) -> bytes:
    inventory = topology.get("_inventory", {})
    record = inventory.get(node["directory"], {"files": [], "subdirectories": []})
    files = sorted(str(path) for path in record.get("files", []))
    directories = sorted(str(path) for path in record.get("subdirectories", []))
    configs = [path for path in files if PurePosixPath(path).name in _CONFIG_NAMES]
    entry_points = [path for path in files if PurePosixPath(path).name in _BOUNDARY_NAMES]
    suffix_counts: dict[str, int] = {}
    for path in files:
        suffix = PurePosixPath(path).suffix.lower() or "<none>"
        suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1
    commands: list[str] = []
    root = topology.get("_root")
    if isinstance(root, Path):
        for path in configs:
            try:
                config_bytes, _ = _read_relative_nofollow(root, path)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
                continue
            if PurePosixPath(path).name == "package.json":
                try:
                    package = json.loads(config_bytes.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                scripts = package.get("scripts") if isinstance(package, Mapping) else None
                if isinstance(scripts, Mapping):
                    commands.extend(
                        f"`npm run {name}` — declared package script: `{command}`"
                        for name, command in sorted(scripts.items())
                        if isinstance(name, str) and isinstance(command, str)
                    )
            elif PurePosixPath(path).name == "Makefile":
                try:
                    makefile = config_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                targets = sorted(
                    {
                        match.group(1)
                        for line in makefile.splitlines()
                        if (match := re.match(r"^([A-Za-z0-9][A-Za-z0-9_.-]*):", line))
                        and not line[match.end():].startswith("=")
                    }
                )
                commands.extend(f"`make {target}` — declared Makefile target." for target in targets)
        for path in files:
            if PurePosixPath(path).suffix != ".sh":
                continue
            try:
                script_bytes, script_mode = _read_relative_nofollow(root, path)
            except (OSError, ValueError):
                continue
            if script_bytes.startswith(b"#!") and script_mode & 0o111:
                commands.append(f"`./{path}` — executable script with a declared shebang.")
    child_scopes = sorted(
        candidate["directory"]
        for candidate in topology["nodes"]
        if candidate["parent_agents_path"] == node["agents_path"]
    )
    scope = "repository root" if node["directory"] == "." else f"`{node['directory']}/`"
    is_root = node["directory"] == "."
    file_limit = 20 if is_root else 8
    directory_limit = 12 if is_root else 5
    evidence_limit = 10 if is_root else 3
    command_limit = 30 if is_root else 5
    displayed_commands = commands[:command_limit]
    displayed_entries = entry_points[:evidence_limit]
    displayed_configs = configs[:evidence_limit]
    lines = [
        "# Managed Repository Instructions",
        "",
        f"Repository: `{topology.get('repository_name', 'repository')}`",
        f"Scope: {scope}",
        f"Placement: {node['decision']} (score {node['score']})",
        "",
        "## Repository evidence",
        "",
        f"- Files directly observed: {len(files)}.",
        f"- Child directories directly observed: {len(directories)}.",
        "- File types: " + (", ".join(f"`{suffix}`={count}" for suffix, count in sorted(suffix_counts.items())) or "none."),
        "- Configurations: " + (", ".join(f"`{path}`" for path in displayed_configs) or "none observed."),
        "- Entry boundaries: " + (", ".join(f"`{path}`" for path in displayed_entries) or "none observed."),
        "",
        "### Direct files",
        "",
        *([f"- `{path}`" for path in files[:file_limit]] or ["- No first-party regular files were observed directly in this scope."]),
        *([f"- {len(files) - file_limit} additional direct files are summarized by type above."] if len(files) > file_limit else []),
        "",
        "### Direct child directories",
        "",
        *([f"- `{path}/`" for path in directories[:directory_limit]] or ["- No direct child directory was observed."]),
        *([f"- {len(directories) - directory_limit} additional child directories are summarized by count above."] if len(directories) > directory_limit else []),
        "",
        "## Entry points and configuration",
        "",
        *([f"- Entry point: `{path}`." for path in displayed_entries] or ["- No entry boundary was asserted."]),
        *([f"- {len(entry_points) - evidence_limit} additional entry points are summarized below."] if len(entry_points) > evidence_limit else []),
        *([f"- Configuration: `{path}`." for path in displayed_configs] or ["- No local configuration was observed."]),
        *([f"- {len(configs) - evidence_limit} additional configurations are summarized below."] if len(configs) > evidence_limit else []),
    ]
    lines.extend(
        [
            "",
            "## Commands",
            "",
            *(displayed_commands if displayed_commands else ["- No executable command was asserted because no declared package script was observed."]),
            *([f"- {len(commands) - command_limit} additional declared commands were omitted to preserve the scope budget."] if len(commands) > command_limit else []),
            "",
            "## Observed conventions",
            "",
            "- Predominant file types: " + (", ".join(f"`{suffix}` ({count})" for suffix, count in sorted(suffix_counts.items(), key=lambda item: (-item[1], item[0]))[:5]) or "none."),
            "- Local configuration ownership: " + (", ".join(f"`{path}`" for path in displayed_configs) or "none observed.") + (f" (+{len(configs) - evidence_limit} summarized)" if len(configs) > evidence_limit else ""),
            "- Local entry-point ownership: " + (", ".join(f"`{path}`" for path in displayed_entries) or "none observed.") + (f" (+{len(entry_points) - evidence_limit} summarized)" if len(entry_points) > evidence_limit else ""),
            "",
            "## Scope relationships",
            "",
            f"- Parent instruction: `{node['parent_agents_path']}`." if node["parent_agents_path"] else "- This is the root instruction.",
            *([f"- `{directory}/` has nearer managed instructions." for directory in child_scopes] or ["- No nearer managed child instruction was selected."]),
        ]
    )
    if node["directory"] == ".":
        lines.extend(
            [
                "",
                "## Loading and coverage",
                "",
                f"- Loader class: `{topology['loader']['loader_class']}`.",
                f"- Loader evidence status: `{topology['loader']['evidence_status']}`.",
                f"- Placement depth bound: `{topology['max_depth']}`; complete coverage remains independent.",
                "",
                "## Constraints",
                "",
                "- Use only repository facts listed above; do not invent commands, entry points, or conventions.",
                "- Preserve unmanaged bytes and require evidence-bound acceptance before replacing incumbent instructions.",
                "- Keep `AGENTS.md` canonical; a sibling `CLAUDE.md` may contain only the exact `@AGENTS.md` adapter.",
                "",
                "## Working rule",
                "",
                "Read every `AGENTS.md` from the repository root through the target directory; the nearest instruction wins on conflict.",
                "Run only commands declared above or commands independently verified from repository configuration.",
                "Verify changed behavior at the narrowest observable repository surface before delivery.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## Local override boundary",
                "",
                f"Inherit `{node['parent_agents_path']}` and apply only the local evidence in this file.",
                "Do not duplicate or weaken parent commands and constraints.",
                "",
            ]
        )
    if migrated_claude is not None:
        lines.extend(
            [
                "## Migrated Claude instructions",
                "",
                "The following substantive incumbent instructions were preserved before installing the exact sibling adapter:",
                "",
                migrated_claude.rstrip("\n"),
                "",
            ]
        )
    rendered = "\n".join(lines)
    line_count = len(rendered.splitlines())
    minimum, maximum = (50, 150) if node["directory"] == "." else (30, 80)
    if not minimum <= line_count <= maximum:
        raise ValueError(
            f"managed payload for {node['agents_path']} has {line_count} lines; "
            f"required range is {minimum}..{maximum}"
        )
    return rendered.encode("utf-8")


def _proposal(
    operation: str,
    action: str,
    path: str,
    before: bytes,
    before_mode: int,
    after: bytes | None,
    after_mode: int | None,
    coupled_targets: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    fields = {
        "operation": operation,
        "action": action,
        "path": path,
        "pre_exists": True,
        "preimage_sha256": sha256_bytes(before),
        "pre_mode": before_mode,
        "post_exists": after is not None,
        "postimage_sha256": sha256_bytes(after) if after is not None else None,
        "post_mode": after_mode,
        "coupled_targets": [dict(target) for target in coupled_targets],
    }
    return {**fields, "id": stable_id("P-" + action.upper(), fields)}


def build_managed_outputs(topology: Mapping[str, Any]) -> dict[str, Any]:
    if topology.get("findings"):
        raise ValueError("unsafe topology findings block mapping")
    topology_snapshot = {key: topology[key] for key in ("max_depth", "shim_policy", "loader", "nodes", "coverage", "root_fallback_payload_sha256")}
    effects: list[dict[str, Any]] = []
    proposals: list[dict[str, Any]] = []
    owned: list[dict[str, Any]] = []
    root = topology.get("_root")
    if not isinstance(root, Path):
        raise ValueError("topology is missing its repository root")
    for node in topology_snapshot["nodes"]:
        claude_path = "CLAUDE.md" if node["directory"] == "." else f"{node['directory']}/CLAUDE.md"
        claude_before: bytes | None = None
        claude_observed: dict[str, Any] | None = None
        migrated_claude: str | None = None
        if topology_snapshot["shim_policy"] == "on":
            try:
                claude_observed = file_observation(root, claude_path)
                claude_before, _ = _read_relative_nofollow(root, claude_path)
            except FileNotFoundError:
                claude_observed = None
        if claude_before is not None:
            if claude_before != SHIM_BYTES:
                try:
                    migrated_claude = claude_before.decode("utf-8")
                except UnicodeDecodeError as error:
                    raise ValueError(f"substantive CLAUDE file is not UTF-8: {claude_path}") from error
        payload = _render_managed_payload(topology, node, migrated_claude)
        data = managed_envelope(node["managed_id"], payload)
        path = node["agents_path"]
        agents_before: bytes | None = None
        agents_before_mode: int | None = None
        try:
            observed = file_observation(root, path)
            before, _ = _read_relative_nofollow(root, path)
        except FileNotFoundError:
            observed = None
        if observed is not None:
            agents_before = before
            agents_before_mode = observed["mode"]
            if before != data:
                parsed = parse_managed_envelope(before)
                if parsed is None or parsed["managed_id"] != node["managed_id"]:
                    proposal = _proposal("map", "adopt-managed-payload", path, before, observed["mode"], data, observed["mode"])
                    proposals.append(proposal)
                    effects.append(
                        {
                            "action": "write",
                            "path": path,
                            "bytes": data,
                            "mode": observed["mode"],
                            "proposal_id": proposal["id"],
                            "expected_pre_sha256": observed["sha256"],
                            "expected_pre_mode": observed["mode"],
                        }
                    )
                else:
                    effects.append(
                        {
                            "action": "write",
                            "path": path,
                            "bytes": data,
                            "mode": observed["mode"],
                            "expected_pre_sha256": observed["sha256"],
                            "expected_pre_mode": observed["mode"],
                        }
                    )
            mode = observed["mode"]
        else:
            effects.append({"action": "write", "path": path, "bytes": data, "mode": NEW_FILE_MODE})
            mode = NEW_FILE_MODE
        owned.append({"path": path, "artifact_type": "agents-file", "managed_id": node["managed_id"], "status": "active", "payload_sha256": sha256_bytes(payload), "file_sha256": sha256_bytes(data), "mode": mode})
        if node["directory"] == ".":
            topology_snapshot["root_fallback_payload_sha256"] = sha256_bytes(payload)

        prior_shim = next(
            (
                row
                for row in topology.get("_prior_owned_artifacts", [])
                if row["path"] == claude_path and row["artifact_type"] == "claude-shim"
            ),
            None,
        )
        if topology_snapshot["shim_policy"] == "on":
            if claude_observed is not None:
                observed = claude_observed
                before = claude_before if claude_before is not None else _read_relative_nofollow(root, claude_path)[0]
                if before != SHIM_BYTES:
                    coupled_agents = {
                        "path": path,
                        "action": "replace" if agents_before is not None else "create",
                        "pre_exists": agents_before is not None,
                        "preimage_sha256": sha256_bytes(agents_before) if agents_before is not None else None,
                        "pre_mode": agents_before_mode,
                        "post_exists": True,
                        "postimage_sha256": sha256_bytes(data),
                        "post_mode": mode,
                    }
                    proposal = _proposal(
                        "map",
                        "merge-claude-and-replace-shim",
                        claude_path,
                        before,
                        observed["mode"],
                        SHIM_BYTES,
                        observed["mode"],
                        [coupled_agents],
                    )
                    proposals.append(proposal)
                    effects.append(
                        {
                            "action": "write",
                            "path": claude_path,
                            "bytes": SHIM_BYTES,
                            "mode": observed["mode"],
                            "proposal_id": proposal["id"],
                            "expected_pre_sha256": observed["sha256"],
                            "expected_pre_mode": observed["mode"],
                        }
                    )
                    shim_mode = observed["mode"]
                else:
                    shim_mode = observed["mode"]
            else:
                effects.append({"action": "write", "path": claude_path, "bytes": SHIM_BYTES, "mode": NEW_FILE_MODE})
                shim_mode = NEW_FILE_MODE
            owned.append(
                {
                    "path": claude_path,
                    "artifact_type": "claude-shim",
                    "managed_id": stable_id("shim", {"path": claude_path}),
                    "status": "active",
                    "payload_sha256": None,
                    "file_sha256": sha256_bytes(SHIM_BYTES),
                    "mode": shim_mode,
                }
            )
        elif prior_shim is not None:
            # Off never deletes during map. It marks the proven exact shim stale
            # so guarded prune can remove it with explicit acceptance.
            owned.append({**prior_shim, "status": "stale"})
    active_paths = {row["path"] for row in owned}
    for prior in topology.get("_prior_owned_artifacts", []):
        if prior["path"] not in active_paths:
            owned.append({**prior, "status": "stale"})
    owned.sort(key=lambda row: row["path"])
    result = {
        "topology": topology_snapshot,
        "effects": effects,
        "proposals": proposals,
        "coverage": list(topology_snapshot["coverage"]),
        "snapshot": {
            "schema_version": SCHEMA_VERSION,
            "repository_root": ".",
            "owned_artifacts": owned,
            "last_applied_topology": topology_snapshot,
        },
    }
    validate_snapshot(result["snapshot"])
    return result


def validate_ownership_snapshot(root: Path, snapshot: Mapping[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    try:
        validate_snapshot(snapshot)
    except ValueError as error:
        return {"valid": False, "findings": [{"code": "INITV4-E-SNAPSHOT-INVALID", "path": SNAPSHOT_NAME, "message": str(error)}]}
    for row in sorted(snapshot.get("owned_artifacts", []), key=lambda item: item.get("path", "")):
        try:
            observed = file_observation(root, row["path"])
            expected = row.get("file_sha256")
            if expected is not None and observed["sha256"] != expected:
                findings.append({"code": "INITV4-E-OWNED-DRIFT", "path": row["path"]})
            if row["artifact_type"] == "agents-region":
                data, _ = _read_relative_nofollow(root, row["path"])
                try:
                    _managed_region_span(data, row["managed_id"], row["payload_sha256"])
                except ValueError:
                    findings.append({"code": "INITV4-E-OWNED-DRIFT", "path": row["path"]})
            if observed["mode"] != row.get("mode"):
                findings.append({"code": "INITV4-E-MODE-DRIFT", "path": row["path"]})
        except (OSError, ValueError):
            findings.append({"code": "INITV4-E-OWNED-UNSAFE", "path": row.get("path", "")})
    return {"valid": not findings, "findings": findings}


def validate_snapshot(snapshot: Mapping[str, Any]) -> None:
    if not isinstance(snapshot, Mapping) or set(snapshot) != {"schema_version", "repository_root", "owned_artifacts", "last_applied_topology"}:
        raise ValueError("snapshot has missing or unknown properties")
    if (
        not isinstance(snapshot["schema_version"], int)
        or isinstance(snapshot["schema_version"], bool)
        or snapshot["schema_version"] != SCHEMA_VERSION
        or snapshot["repository_root"] != "."
        or not isinstance(snapshot["owned_artifacts"], list)
    ):
        raise ValueError("snapshot header is invalid")
    topology = snapshot["last_applied_topology"]
    required_topology = {"max_depth", "shim_policy", "loader", "nodes", "coverage", "root_fallback_payload_sha256"}
    if not isinstance(topology, Mapping) or set(topology) != required_topology:
        raise ValueError("snapshot topology is invalid")
    max_depth = topology["max_depth"]
    if (
        not isinstance(max_depth, int)
        or isinstance(max_depth, bool)
        or not 1 <= max_depth <= 32
        or not isinstance(topology["shim_policy"], str)
        or topology["shim_policy"] not in {"on", "off"}
    ):
        raise ValueError("snapshot topology is invalid")
    loader = topology["loader"]
    loader_keys = {"loader_class", "evidence_status", "source_id", "runtime_version", "probe_fixture_sha256", "probe_result_sha256"}
    statuses = {"probe-verified", "source-only", "conflicted", "unavailable", "version-mismatch", "not-automatable"}
    if not isinstance(loader, Mapping) or set(loader) != loader_keys:
        raise ValueError("snapshot loader evidence is invalid")
    if (
        not isinstance(loader["loader_class"], str)
        or not isinstance(loader["evidence_status"], str)
        or loader["loader_class"] not in {"file-scoped", "recursive", "ancestor-only", "unknown"}
        or loader["evidence_status"] not in statuses
    ):
        raise ValueError("snapshot loader class/status is invalid")
    if loader["evidence_status"] != "probe-verified" and loader["loader_class"] != "unknown":
        raise ValueError("unverified loader evidence must remain unknown")
    for key in ("source_id", "runtime_version"):
        if loader[key] is not None and (not isinstance(loader[key], str) or not loader[key]):
            raise ValueError("snapshot loader identity is invalid")
    for key in ("probe_fixture_sha256", "probe_result_sha256"):
        if loader[key] is not None and (not isinstance(loader[key], str) or not _HASH.match(loader[key])):
            raise ValueError("snapshot loader hash is invalid")

    if not isinstance(topology["nodes"], list) or not isinstance(topology["coverage"], list):
        raise ValueError("snapshot topology arrays are invalid")
    factor_names = set(_FACTOR_NAMES)
    for node in topology["nodes"]:
        keys = {"directory", "agents_path", "parent_agents_path", "managed_id", "score", "decision", "factors"}
        if not isinstance(node, Mapping) or set(node) != keys:
            raise ValueError("snapshot node is invalid")
        directory = node["directory"]
        if not isinstance(directory, str) or not isinstance(node["agents_path"], str):
            raise ValueError("snapshot node path is invalid")
        if directory != ".":
            normalize_path(directory)
        normalize_path(node["agents_path"])
        if node["parent_agents_path"] is not None:
            if not isinstance(node["parent_agents_path"], str):
                raise ValueError("snapshot parent path is invalid")
            normalize_path(node["parent_agents_path"])
        if not isinstance(node["managed_id"], str) or not node["managed_id"] or ">" in node["managed_id"] or any(character.isspace() for character in node["managed_id"]):
            raise ValueError("snapshot managed id is invalid")
        if not isinstance(node["score"], int) or isinstance(node["score"], bool) or not 0 <= node["score"] <= 17 or not isinstance(node["decision"], str) or node["decision"] not in {"root", "high-score", "distinct-domain"}:
            raise ValueError("snapshot node decision is invalid")
        if not isinstance(node["factors"], list):
            raise ValueError("snapshot node factors are invalid")
        for factor in node["factors"]:
            factor_keys = {"name", "measured", "value", "points", "evidence_paths"}
            if not isinstance(factor, Mapping) or set(factor) != factor_keys or not isinstance(factor["name"], str) or factor["name"] not in factor_names:
                raise ValueError("snapshot factor is invalid")
            if not isinstance(factor["measured"], bool) or not isinstance(factor["points"], int) or isinstance(factor["points"], bool) or not 0 <= factor["points"] <= 3:
                raise ValueError("snapshot factor measurement is invalid")
            if not isinstance(factor["evidence_paths"], list):
                raise ValueError("snapshot factor evidence is invalid")
            for path in factor["evidence_paths"]:
                if not isinstance(path, str):
                    raise ValueError("snapshot factor evidence path is invalid")
                normalize_path(path)
    for coverage in topology["coverage"]:
        keys = {"directory", "expected_chain", "status_at_apply", "basis_at_apply"}
        if not isinstance(coverage, Mapping) or set(coverage) != keys:
            raise ValueError("snapshot coverage is invalid")
        if not isinstance(coverage["directory"], str):
            raise ValueError("snapshot coverage directory is invalid")
        if coverage["directory"] != ".":
            normalize_path(coverage["directory"])
        if not isinstance(coverage["expected_chain"], list):
            raise ValueError("snapshot coverage chain is invalid")
        for path in coverage["expected_chain"]:
            if not isinstance(path, str):
                raise ValueError("snapshot coverage path is invalid")
            normalize_path(path)
        if (
            not isinstance(coverage["status_at_apply"], str)
            or not isinstance(coverage["basis_at_apply"], str)
            or coverage["status_at_apply"] not in {"covered", "gap", "ambiguous", "unverified"}
            or coverage["basis_at_apply"] not in {"native", "root-fallback", "none"}
        ):
            raise ValueError("snapshot coverage status is invalid")
    root_hash = topology["root_fallback_payload_sha256"]
    if root_hash is not None and (not isinstance(root_hash, str) or not _HASH.match(root_hash)):
        raise ValueError("snapshot root fallback hash is invalid")

    owned_keys = {"path", "artifact_type", "managed_id", "status", "payload_sha256", "file_sha256", "mode"}
    for row in snapshot["owned_artifacts"]:
        if not isinstance(row, Mapping) or set(row) != owned_keys:
            raise ValueError("snapshot owned artifact is invalid")
        if not isinstance(row["path"], str):
            raise ValueError("snapshot ownership path is invalid")
        normalize_path(row["path"])
        if (
            not isinstance(row["artifact_type"], str)
            or not isinstance(row["status"], str)
            or row["artifact_type"] not in {"agents-region", "agents-file", "claude-shim"}
            or row["status"] not in {"active", "stale"}
        ):
            raise ValueError("snapshot ownership kind/status is invalid")
        if not isinstance(row["managed_id"], str) or not row["managed_id"] or ">" in row["managed_id"]:
            raise ValueError("snapshot ownership id is invalid")
        if not isinstance(row["mode"], int) or isinstance(row["mode"], bool) or not 0 <= row["mode"] <= 4095:
            raise ValueError("snapshot ownership mode is invalid")
        for key in ("payload_sha256", "file_sha256"):
            if row[key] is not None and (not isinstance(row[key], str) or not _HASH.match(row[key])):
                raise ValueError("snapshot ownership hash is invalid")
        if row["artifact_type"] == "agents-region" and (row["payload_sha256"] is None or row["file_sha256"] is not None):
            raise ValueError("agents-region ownership hashes are invalid")
        if row["artifact_type"] == "agents-file" and (row["payload_sha256"] is None or row["file_sha256"] is None):
            raise ValueError("agents-file ownership hashes are invalid")
        if row["artifact_type"] == "claude-shim" and (row["payload_sha256"] is not None or row["file_sha256"] is None):
            raise ValueError("claude-shim ownership hashes are invalid")


def audit(root: Path) -> dict[str, Any]:
    snapshot: dict[str, Any] | None = None
    findings: list[dict[str, Any]] = []
    root_fd = pinned_root_fd(root)
    try:
        snapshot_info = os.stat(SNAPSHOT_NAME, dir_fd=root_fd, follow_symlinks=False)
    except FileNotFoundError:
        snapshot_info = None
    if snapshot_info is not None:
        if not stat.S_ISREG(snapshot_info.st_mode) or stat.S_ISLNK(snapshot_info.st_mode):
            os.close(root_fd)
            raise ValueError("ownership snapshot is unsafe (symlink or non-regular)")
        try:
            descriptor = os.open(SNAPSHOT_NAME, os.O_RDONLY | _NOFOLLOW, dir_fd=root_fd)
            try:
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                snapshot_bytes = b"".join(chunks)
            finally:
                os.close(descriptor)
            snapshot = json.loads(snapshot_bytes.decode("utf-8"))
            findings.extend(validate_ownership_snapshot(root, snapshot)["findings"])
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            findings.append({"code": "INITV4-E-SNAPSHOT-INVALID", "path": SNAPSHOT_NAME})
    try:
        os.stat(JOURNAL_NAME, dir_fd=root_fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        findings.append({"code": "INITV4-E-TRANSACTION-ACTIVE", "path": JOURNAL_NAME})
    os.close(root_fd)
    topology = discover_topology(root)
    findings.extend(topology["findings"])
    public_topology = {key: value for key, value in topology.items() if key != "_root"}
    return {"findings": sorted(findings, key=lambda item: (item["code"], item.get("path", ""))), "topology": public_topology, "snapshot": snapshot, "mutations": []}


def plan_prune(root: Path, snapshot: Mapping[str, Any], accepted_ids: set[str]) -> dict[str, Any]:
    proposals: list[dict[str, Any]] = []
    effects: list[dict[str, Any]] = []
    for row in sorted(snapshot.get("owned_artifacts", []), key=lambda item: item.get("path", "")):
        if row.get("status") != "stale":
            continue
        observed = file_observation(root, row["path"])
        if row["artifact_type"] == "agents-region":
            source, _ = _read_relative_nofollow(root, row["path"])
            start, finish = _managed_region_span(source, row["managed_id"], row["payload_sha256"])
            post_bytes = source[:start] + source[finish:]
            action = "remove-stale-region"
        else:
            post_bytes = None
            action = "remove-stale-shim" if row["artifact_type"] == "claude-shim" else "remove-stale-file"
        proposal = {
            "operation": "prune",
            "action": action,
            "path": row["path"],
            "pre_exists": True,
            "preimage_sha256": observed["sha256"],
            "pre_mode": observed["mode"],
            "post_exists": post_bytes is not None,
            "postimage_sha256": sha256_bytes(post_bytes) if post_bytes is not None else None,
            "post_mode": observed["mode"] if post_bytes is not None else None,
        }
        proposal["id"] = stable_id("P-" + proposal["action"].upper(), proposal)
        proposals.append(proposal)
        if proposal["id"] in accepted_ids:
            effect: dict[str, Any] = {
                "action": "delete" if post_bytes is None else "write",
                "path": row["path"],
                "proposal_id": proposal["id"],
                "expected_pre_sha256": observed["sha256"],
                "expected_pre_mode": observed["mode"],
            }
            if post_bytes is not None:
                effect.update({"bytes": post_bytes, "mode": observed["mode"]})
            effects.append(effect)
    accepted_paths = {effect["path"] for effect in effects}
    updated = dict(snapshot)
    updated["owned_artifacts"] = [dict(row) for row in snapshot.get("owned_artifacts", []) if row.get("path") not in accepted_paths]
    validate_snapshot(updated)
    return {"proposals": proposals, "effects": effects, "snapshot": updated}


def probe_loading(root: Path, receipt: Mapping[str, Any] | None = None) -> dict[str, Any]:
    root = root.absolute() if _PINNED_ROOT_FD.get() is not None else root.resolve(strict=True)
    fixture = {
        "root": {"path": "AGENTS.md", "marker": "ROOT"},
        "child": {"path": "child/AGENTS.md", "marker": "CHILD"},
        "sibling": {"path": "sibling/AGENTS.md", "marker": "SIBLING"},
    }
    result: dict[str, Any] = {
        "root": normalized_relative(root, root, allow_root=True),
        "fixture": fixture,
        "fixture_sha256": sha256_bytes(canonical_json(fixture)),
    }
    if receipt is None:
        result.update(
            {
                "status": "unknown",
                "loading_class": "unknown",
                "reason": "no applicable sentinel observations",
            }
        )
        return result
    result["receipt"] = dict(receipt)
    observations = receipt.get("observations")
    if isinstance(observations, Mapping):
        result["observations"] = dict(observations)
    result.update(_receipt_status(receipt, result["fixture_sha256"]))
    if result["status"] != "verified":
        result["reason"] = "receipt did not bind a complete applicable sentinel matrix"
    return result


def transaction_basis(operation: str, targets: Iterable[Mapping[str, Any]], snapshot: Mapping[str, Any]) -> dict[str, Any]:
    if operation not in {"map", "prune"}:
        raise ValueError("invalid operation")
    fields = ("path", "action", "pre_exists", "pre_sha256", "pre_mode", "post_exists", "post_sha256", "post_mode")
    def entry(value: Mapping[str, Any]) -> dict[str, Any]:
        result = {field: value.get(field) for field in fields}
        normalize_path(str(result["path"]))
        return result
    return {"operation": operation, "targets": [entry(item) for item in sorted(targets, key=lambda item: str(item["path"]))], "snapshot": entry(snapshot)}


def transaction_id(basis: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json(dict(basis)))


def derived_transaction_paths(transaction_id_value: str, target_path: str) -> dict[str, str]:
    if not _HASH.match(transaction_id_value):
        raise ValueError("invalid transaction id")
    target_path = normalize_path(target_path)
    parent, _, name = target_path.rpartition("/")
    stem = f"{name if name.startswith('.') else f'.{name}'}.craft-init-v4-{transaction_id_value[:12]}"
    prefix = f"{parent}/" if parent else ""
    return {"pre_recovery_path": prefix + stem + ".pre", "post_recovery_path": prefix + stem + ".post", "apply_path": prefix + stem + ".apply", "next_path": f"{JOURNAL_NAME}.{transaction_id_value[:12]}.next"}


def expected_apply(entry: Mapping[str, Any], direction: str) -> dict[str, Any] | None:
    if direction not in {"forward", "rollback", "complete"}:
        raise ValueError("invalid apply direction")
    use_post = direction in {"forward", "complete"}
    exists = entry.get("post_exists") if use_post else entry.get("pre_exists")
    if not exists:
        return None
    return {"sha256": entry.get("post_sha256") if use_post else entry.get("pre_sha256"), "mode": entry.get("post_mode") if use_post else entry.get("pre_mode")}


def validate_apply_observation(entry: Mapping[str, Any], direction: str, observed: Mapping[str, Any]) -> bool:
    expected = expected_apply(entry, direction)
    return expected is not None and observed.get("regular") is True and observed.get("sha256") == expected["sha256"] and observed.get("mode") == expected["mode"]
