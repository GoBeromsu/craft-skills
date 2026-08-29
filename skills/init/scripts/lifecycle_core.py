"""Deterministic, effect-free lifecycle calculations for the init package."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import unicodedata
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
_CODE_SUFFIXES = frozenset({".c", ".cc", ".cpp", ".cs", ".go", ".h", ".hpp", ".java", ".js", ".jsx", ".kt", ".php", ".py", ".rb", ".rs", ".sh", ".swift", ".ts", ".tsx"})
_CONFIG_NAMES = frozenset({"Cargo.toml", "go.mod", "package.json", "pyproject.toml", "setup.cfg", "setup.py", "tox.ini", "tsconfig.json"})
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


def file_observation(root: Path, relative: str) -> dict[str, Any]:
    path = safe_path(root, relative, require_exists=True)
    info = os.lstat(path)
    data = path.read_bytes()
    return {"path": normalize_path(relative), "sha256": sha256_bytes(data), "mode": mode_of(info.st_mode), "size": len(data)}


def managed_envelope(managed_id: str, payload: bytes) -> bytes:
    if not managed_id or any(character.isspace() for character in managed_id):
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


def classify_loading_observations(observations: Mapping[str, Any]) -> dict[str, str]:
    """Marker arrays are unbound claims, never verified loading evidence."""
    return {"status": "unknown", "loading_class": "unknown"}


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
    def walk_error(error: OSError) -> None:
        path = Path(error.filename) if error.filename else root
        try:
            relative = normalized_relative(root, path, allow_root=True)
        except ValueError:
            relative = "."
        findings.append({"code": "INITV4-E-UNREADABLE", "path": relative})

    for current, names, files in os.walk(root, topdown=True, followlinks=False, onerror=walk_error):
        current_path = Path(current)
        current_relative = normalized_relative(root, current_path, allow_root=True)
        record = directories.setdefault(current_relative, {"files": [], "subdirectories": []})
        kept: list[str] = []
        for name in sorted(names):
            child = current_path / name
            relative = normalized_relative(root, child)
            info = os.lstat(child)
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
            path = current_path / name
            relative = normalized_relative(root, path)
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                findings.append({"code": "INITV4-E-SYMLINK", "path": relative})
            elif not stat.S_ISREG(info.st_mode):
                findings.append({"code": "INITV4-E-SPECIAL-FILE", "path": relative})
            elif name not in {"AGENTS.md", "CLAUDE.md", SNAPSHOT_NAME, JOURNAL_NAME} and ".craft-init-v4-" not in name:
                try:
                    with path.open("rb") as handle:
                        handle.read(1)
                except OSError:
                    findings.append({"code": "INITV4-E-UNREADABLE", "path": relative})
                else:
                    relevant = True
                    record["files"].append(relative)
        if not relevant and current_relative != "." and not record["subdirectories"]:
            directories.pop(current_relative, None)
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
    verified = resolved["status"] == "verified"
    return {
        "loader_class": resolved["loading_class"],
        "evidence_status": "probe-verified" if verified else "unavailable",
        "source_id": evidence.get("source_id") if evidence and isinstance(evidence.get("source_id"), str) else None,
        "runtime_version": evidence.get("runtime_version") if evidence and isinstance(evidence.get("runtime_version"), str) else None,
        "probe_fixture_sha256": evidence.get("fixture_sha256") if evidence and isinstance(evidence.get("fixture_sha256"), str) and _HASH.match(str(evidence.get("fixture_sha256"))) else None,
        "probe_result_sha256": evidence.get("raw_result_sha256") if evidence and isinstance(evidence.get("raw_result_sha256"), str) and _HASH.match(str(evidence.get("raw_result_sha256"))) else None,
    }


def discover_topology(root: Path, *, max_depth: int = 3, shim_policy: str = "off", loading_evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if not 1 <= max_depth <= 32 or shim_policy not in {"on", "off"}:
        raise ValueError("invalid topology settings")
    root = root.resolve(strict=True)
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
    return {"max_depth": max_depth, "shim_policy": shim_policy, "loader": _loader_snapshot(loading_evidence), "nodes": nodes, "coverage": coverage, "root_fallback_payload_sha256": None, "findings": findings, "exclusions": exclusions, "repository_name": root.name, "_root": root}


def build_managed_outputs(topology: Mapping[str, Any]) -> dict[str, Any]:
    if topology.get("findings"):
        raise ValueError("unsafe topology findings block mapping")
    topology_snapshot = {key: topology[key] for key in ("max_depth", "shim_policy", "loader", "nodes", "coverage", "root_fallback_payload_sha256")}
    effects: list[dict[str, Any]] = []
    owned: list[dict[str, Any]] = []
    root = topology.get("_root")
    if not isinstance(root, Path):
        raise ValueError("topology is missing its repository root")
    for node in topology_snapshot["nodes"]:
        scope = "repository root" if node["directory"] == "." else f"`{node['directory']}/`"
        payload = (f"# Managed Repository Instructions\n\nRepository: `{topology.get('repository_name', root.name)}`\nScope: {scope}\n\nFollow the nearest AGENTS.md instructions and preserve repository-local conventions.\n").encode("utf-8")
        data = managed_envelope(node["managed_id"], payload)
        path = node["agents_path"]
        destination = safe_path(root, path)
        if destination.exists():
            observed = file_observation(root, path)
            if destination.read_bytes() != data:
                parsed = parse_managed_envelope(destination.read_bytes())
                if parsed is None or parsed["managed_id"] != node["managed_id"]:
                    raise ValueError(f"unmanaged AGENTS file blocks mapping: {path}")
                effects.append({"action": "write", "path": path, "bytes": data, "mode": observed["mode"]})
            mode = observed["mode"]
        else:
            effects.append({"action": "write", "path": path, "bytes": data, "mode": NEW_FILE_MODE})
            mode = NEW_FILE_MODE
        owned.append({"path": path, "artifact_type": "agents-file", "managed_id": node["managed_id"], "status": "active", "payload_sha256": sha256_bytes(payload), "file_sha256": sha256_bytes(data), "mode": mode})
        if node["directory"] == ".":
            topology_snapshot["root_fallback_payload_sha256"] = sha256_bytes(payload)
    active_paths = {row["path"] for row in owned}
    for prior in topology.get("_prior_owned_artifacts", []):
        if prior["path"] not in active_paths:
            owned.append({**prior, "status": "stale"})
    owned.sort(key=lambda row: row["path"])
    result = {
        "topology": topology_snapshot,
        "effects": effects,
        "proposals": [],
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
                parsed = parse_managed_envelope(safe_path(root, row["path"], require_exists=True).read_bytes())
                if parsed is None or parsed["managed_id"] != row["managed_id"] or parsed["payload_sha256"] != row["payload_sha256"]:
                    findings.append({"code": "INITV4-E-OWNED-DRIFT", "path": row["path"]})
            if observed["mode"] != row.get("mode"):
                findings.append({"code": "INITV4-E-MODE-DRIFT", "path": row["path"]})
        except (OSError, ValueError):
            findings.append({"code": "INITV4-E-OWNED-UNSAFE", "path": row.get("path", "")})
    return {"valid": not findings, "findings": findings}


def validate_snapshot(snapshot: Mapping[str, Any]) -> None:
    if not isinstance(snapshot, Mapping) or set(snapshot) != {"schema_version", "repository_root", "owned_artifacts", "last_applied_topology"}:
        raise ValueError("snapshot has missing or unknown properties")
    if snapshot["schema_version"] != SCHEMA_VERSION or snapshot["repository_root"] != "." or not isinstance(snapshot["owned_artifacts"], list):
        raise ValueError("snapshot header is invalid")
    topology = snapshot["last_applied_topology"]
    required_topology = {"max_depth", "shim_policy", "loader", "nodes", "coverage", "root_fallback_payload_sha256"}
    if not isinstance(topology, Mapping) or set(topology) != required_topology or not 1 <= topology.get("max_depth", 0) <= 32 or topology.get("shim_policy") not in {"on", "off"}:
        raise ValueError("snapshot topology is invalid")
    # The checked-in schema is the final authority when jsonschema is available.
    try:
        import jsonschema
        schema = json.loads((Path(__file__).resolve().parents[1] / "templates" / "snapshot.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(dict(snapshot))
    except ImportError:
        if not all(isinstance(topology.get(key), list) for key in ("nodes", "coverage")):
            raise ValueError("snapshot topology arrays are invalid")
    except (OSError, json.JSONDecodeError, jsonschema.ValidationError) as error:
        raise ValueError(f"snapshot does not match schema: {error.message if hasattr(error, 'message') else error}") from error


def audit(root: Path) -> dict[str, Any]:
    snapshot_path = root / SNAPSHOT_NAME
    snapshot: dict[str, Any] | None = None
    findings: list[dict[str, Any]] = []
    try:
        snapshot_info = os.lstat(snapshot_path)
    except FileNotFoundError:
        snapshot_info = None
    if snapshot_info is not None:
        if not stat.S_ISREG(snapshot_info.st_mode) or stat.S_ISLNK(snapshot_info.st_mode):
            raise ValueError("ownership snapshot is unsafe (symlink or non-regular)")
        try:
            snapshot = json.loads(snapshot_path.read_bytes().decode("utf-8"))
            findings.extend(validate_ownership_snapshot(root, snapshot)["findings"])
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            findings.append({"code": "INITV4-E-SNAPSHOT-INVALID", "path": SNAPSHOT_NAME})
    if (root / JOURNAL_NAME).exists():
        findings.append({"code": "INITV4-E-TRANSACTION-ACTIVE", "path": JOURNAL_NAME})
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
        proposal = {"action": "remove-stale-file" if row.get("artifact_type") != "claude-shim" else "remove-stale-shim", "path": row["path"], "preimage_sha256": row.get("file_sha256"), "postimage_sha256": None}
        proposal["id"] = stable_id("P-" + proposal["action"].upper(), proposal)
        proposals.append(proposal)
        if proposal["id"] in accepted_ids:
            effects.append({"action": "delete", "path": row["path"], "proposal_id": proposal["id"]})
    accepted_paths = {effect["path"] for effect in effects}
    updated = dict(snapshot)
    updated["owned_artifacts"] = [dict(row) for row in snapshot.get("owned_artifacts", []) if row.get("path") not in accepted_paths]
    validate_snapshot(updated)
    return {"proposals": proposals, "effects": effects, "snapshot": updated}


def probe_loading(root: Path, receipt: Mapping[str, Any] | None = None) -> dict[str, Any]:
    root = root.resolve(strict=True)
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
