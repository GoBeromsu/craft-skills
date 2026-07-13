#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TypeAlias

JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

_PLUGIN_ID = "craft-skills@craft-skills"
_FINGERPRINTS = {
    "skills/backend/references/persistence.md": (
        "runtime application role",
        "privileged migration/admin role",
        "dedicated disposable non-production target",
    ),
    "skills/testing/references/integration.md": (
        "application-owned transaction",
        "transaction-local RLS",
        "allowed and denied tenant paths",
    ),
    "skills/cicd/references/pipeline-safety.md": (
        "immutable release resolver",
        "no schema change or backward compatibility",
        "code rollback is not database recovery",
    ),
}


class InstallVerificationError(Exception):
    pass


def _installed_entries(payload: JsonValue) -> list[JsonObject]:
    if isinstance(payload, list):
        return [entry for entry in payload if isinstance(entry, dict)]
    if not isinstance(payload, dict):
        return []
    installed = payload.get("installed", [])
    return [entry for entry in installed if isinstance(entry, dict)] if isinstance(installed, list) else []


def _source_path(entry: JsonObject) -> Path | None:
    source = entry.get("source")
    if not isinstance(source, dict):
        return None
    value = source.get("path")
    return Path(value).resolve() if isinstance(value, str) else None


def verify(plugin_list: Path, expected_version: str, forbidden_source: Path | None) -> Path:
    payload = json.loads(plugin_list.read_text(encoding="utf-8"))
    matches = [entry for entry in _installed_entries(payload) if entry.get("pluginId") == _PLUGIN_ID]
    if len(matches) != 1:
        raise InstallVerificationError(f"expected one installed {_PLUGIN_ID} entry, found {len(matches)}")
    entry = matches[0]
    if entry.get("installed") is not True or entry.get("enabled") is not True:
        raise InstallVerificationError(f"{_PLUGIN_ID} must be installed and enabled")
    if entry.get("version") != expected_version:
        raise InstallVerificationError(f"expected version {expected_version}, found {entry.get('version')!r}")
    source = _source_path(entry)
    if source is None or not source.is_dir():
        raise InstallVerificationError("installed plugin source path is missing")
    if forbidden_source is not None and source == forbidden_source.resolve():
        raise InstallVerificationError("installed plugin still resolves to the forbidden prior source")
    for relative, fingerprints in _FINGERPRINTS.items():
        path = source / relative
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        missing = [fingerprint for fingerprint in fingerprints if fingerprint not in text]
        if missing:
            raise InstallVerificationError(f"{relative} is missing required guidance: {', '.join(missing)}")
    return source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-list", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--forbid-source", type=Path)
    args = parser.parse_args()
    try:
        source = verify(args.plugin_list, args.expected_version, args.forbid_source)
    except (OSError, InstallVerificationError, json.JSONDecodeError) as error:
        print(f"verify_plugin_install: {error}")
        return 1
    print(f"verify_plugin_install: {args.expected_version} installed and verified at {source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
