"""Local OMS runtime installation doctor for governance smoke checks."""

from __future__ import annotations

import json
import shutil
import tomllib
from pathlib import Path
from typing import Any

CHECKER_NAME = "install_doctor"
CHECKER_VERSION = "1"


def _repo_paths(config: dict[str, Any]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for repo in config.get("repos", []):
        if isinstance(repo, dict) and isinstance(repo.get("name"), str) and isinstance(repo.get("path"), str):
            paths[repo["name"]] = Path(repo["path"]).expanduser().resolve()
    return paths


def _finding(code: str, message: str, path: Path | None = None, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "checker": CHECKER_NAME,
        "severity": "advisory",
        "code": code,
        "package": None,
        "package_id": None,
        "message": message,
        "path": str(path) if path is not None else None,
        "details": details or {},
    }


def _expected_oms_version(repos: dict[str, Path]) -> tuple[str | None, Path | None]:
    oms_repo = repos.get("oh-my-secondbrain")
    if oms_repo is None:
        return None, None
    package_json = oms_repo / "package.json"
    if not package_json.is_file():
        return None, package_json
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, package_json
    version = data.get("version")
    return version if isinstance(version, str) else None, package_json


def _json_version(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    version = data.get("version")
    return version if isinstance(version, str) else None


def _command_exists(command: str) -> bool:
    if "/" in command:
        return Path(command).expanduser().exists()
    return shutil.which(command) is not None


def _codex_findings(home: Path) -> list[dict[str, Any]]:
    config_path = home / ".codex" / "config.toml"
    if not config_path.is_file():
        return [
            _finding(
                "install_doctor.codex_not_installed",
                "Codex OMS MCP registration 미설치: ~/.codex/config.toml is absent.",
                config_path,
            )
        ]

    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        return [
            _finding(
                "install_doctor.codex_config_invalid",
                "Codex config could not be parsed; OMS MCP registration cannot be checked.",
                config_path,
                {"error": str(exc)},
            )
        ]

    mcp_servers = config.get("mcp_servers")
    oms_server = mcp_servers.get("oms") if isinstance(mcp_servers, dict) else None
    if not isinstance(oms_server, dict):
        return [
            _finding(
                "install_doctor.codex_mcp_not_installed",
                "Codex OMS MCP registration 미설치: [mcp_servers.oms] is absent.",
                config_path,
            )
        ]

    command = oms_server.get("command")
    if not isinstance(command, str) or not command.strip():
        return [
            _finding(
                "install_doctor.codex_mcp_command_missing",
                "Codex OMS MCP registration does not declare a command.",
                config_path,
                {"server": "oms"},
            )
        ]
    if not _command_exists(command):
        return [
            _finding(
                "install_doctor.codex_mcp_command_not_found",
                "Codex OMS MCP command is not executable from its configured location or PATH.",
                config_path,
                {"server": "oms", "command": command},
            )
        ]
    return []


def _runtime_version_findings(runtime: str, manifest_candidates: list[Path], expected_version: str | None) -> list[dict[str, Any]]:
    existing = [path for path in manifest_candidates if path.is_file()]
    if not existing:
        return [
            _finding(
                f"install_doctor.{runtime}_not_installed",
                f"{runtime} OMS 설치물 미설치: no OMS runtime manifest found.",
                manifest_candidates[0] if manifest_candidates else None,
                {"candidate_paths": [str(path) for path in manifest_candidates]},
            )
        ]

    if expected_version is None:
        return [
            _finding(
                f"install_doctor.{runtime}_expected_version_unknown",
                f"{runtime} OMS install exists, but expected package version could not be read.",
                existing[0],
            )
        ]

    findings: list[dict[str, Any]] = []
    for manifest in existing:
        actual_version = _json_version(manifest)
        if actual_version is None:
            findings.append(
                _finding(
                    f"install_doctor.{runtime}_version_unreadable",
                    f"{runtime} OMS manifest has no readable version.",
                    manifest,
                    {"expected_version": expected_version},
                )
            )
        elif actual_version != expected_version:
            findings.append(
                _finding(
                    f"install_doctor.{runtime}_version_mismatch",
                    f"{runtime} OMS install version differs from oh-my-secondbrain/package.json.",
                    manifest,
                    {"expected_version": expected_version, "actual_version": actual_version},
                )
            )
    return findings


def _path_findings() -> list[dict[str, Any]]:
    oms_path = shutil.which("oms")
    if oms_path is None:
        return [
            _finding(
                "install_doctor.path_oms_not_installed",
                "PATH OMS 미설치: `oms` is not discoverable on PATH.",
                None,
            )
        ]
    return []


def check(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    del aggregate
    repos = _repo_paths(config)
    expected_version, expected_path = _expected_oms_version(repos)
    findings: list[dict[str, Any]] = []
    if expected_version is None:
        findings.append(
            _finding(
                "install_doctor.expected_version_unreadable",
                "Expected OMS version could not be read from oh-my-secondbrain/package.json.",
                expected_path,
            )
        )

    home = Path.home()
    findings.extend(_codex_findings(home))
    findings.extend(
        _runtime_version_findings(
            "claude",
            [
                home / ".claude" / "skills" / "oms" / ".claude-plugin" / "plugin.json",
                home / ".claude" / "plugins" / "oms" / ".claude-plugin" / "plugin.json",
            ],
            expected_version,
        )
    )
    findings.extend(
        _runtime_version_findings(
            "hermes",
            [
                home / ".hermes" / "adapters" / "oms" / "manifest.json",
                home / ".hermes" / "skills" / "knowledge-management" / "oms" / "manifest.json",
            ],
            expected_version,
        )
    )
    findings.extend(_path_findings())
    return findings


def run(aggregate: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    return check(aggregate, config)
