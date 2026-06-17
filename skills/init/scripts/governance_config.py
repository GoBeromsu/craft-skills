#!/usr/bin/env python3
"""Shared issue-driven governance configuration resolver for the init skill."""
from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

CONFIG_ENV = "ISSUE_GOVERNANCE_CONFIG"
DEFAULT_CONFIG_PATH = ".github/issue-driven-governance.yml"

DEFAULT_CONFIG: dict[str, Any] = {
    "churn_threshold": 1000,
    "default_branch": "main",
    "allowed_base": ["main", "release/*", "hotfix/*"],
    "labels": {
        "type": [
            {"name": "feat", "color": "0e8a16", "description": "Feature work"},
            {"name": "fix", "color": "d73a4a", "description": "Bug fix"},
            {"name": "chore", "color": "cfd3d7", "description": "Maintenance or tooling"},
            {"name": "docs", "color": "0075ca", "description": "Documentation"},
            {"name": "refactor", "color": "5319e7", "description": "Code change without feature or bug behavior"},
            {"name": "test", "color": "fbca04", "description": "Test-only change"},
        ],
        "domain": [],  # Repos may add product-specific ownership labels sparsely.
        "size": [
            {"name": "size/S", "color": "c2e0c6", "description": "Small change"},
            {"name": "size/M", "color": "fef2c0", "description": "Medium change"},
            {"name": "size/L", "color": "f9d0c4", "description": "Large change"},
            {"name": "size/XL", "color": "e99695", "description": "Extra large change"},
        ],
        "override": [
            {"name": "size/override", "color": "b60205", "description": "Explicit size-policy override"},
        ],
    },
    "non_logic_globs": [
        "**/test/**",
        "**/tests/**",
        "*_test.*",
        "test_*.*",
        "*.spec.*",
        "*.test.*",
        "docs/**",
        "*.md",
        "pnpm-lock.yaml",
        "uv.lock",
        "package-lock.json",
        "yarn.lock",
        "Cargo.lock",
        "go.sum",
        "poetry.lock",
        "**/migrations/**",
        "**/generated/**",
        "**/data/**",
    ],
}

_ENV_RE = re.compile(r"\$\{([^}:]+)(?::-(.*?))?\}")


def _expand_placeholders(value: str) -> str:
    """Expand ${ENV_VAR} and ${ENV_VAR:-fallback} placeholders."""
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        fallback = match.group(2)
        env_value = os.environ.get(name)
        if env_value is not None:
            return env_value
        return fallback or ""

    return _ENV_RE.sub(replace, value)


def _coerce_scalar(value: str) -> Any:
    value = value.strip().strip('"').strip("'")
    expanded = _expand_placeholders(value)
    lowered = expanded.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    try:
        return int(expanded)
    except ValueError:
        return expanded


def _parse_inline_list(value: str) -> list[Any]:
    inner = value.strip()[1:-1].strip()
    if not inner:
        return []
    return [_coerce_scalar(part.strip()) for part in inner.split(",")]


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for idx, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:idx]
    return line


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by governance fixtures.

    Supports nested mappings, scalar values, inline lists, and block lists of
    scalars or one-line dictionaries. This avoids a runtime PyYAML dependency.
    """
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]

    for raw_line in text.splitlines():
        line = _strip_comment(raw_line).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if stripped.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"list item without list parent: {raw_line}")
            item = stripped[2:].strip()
            if ":" in item and not item.startswith(("'", '"')):
                key, val = item.split(":", 1)
                obj: dict[str, Any] = {key.strip(): _parse_value(val.strip())}
                parent.append(obj)
                stack.append((indent, obj))
            else:
                parent.append(_parse_value(item))
            continue

        if ":" not in stripped:
            raise ValueError(f"expected key/value line: {raw_line}")
        key, val = stripped.split(":", 1)
        key = key.strip()
        val = val.strip()
        if val == "":
            next_container: Any = [] if _next_nonempty_is_list(text, raw_line) else {}
            parent[key] = next_container
            stack.append((indent, next_container))
        else:
            parent[key] = _parse_value(val)

    return root


def _next_nonempty_is_list(text: str, current_line: str) -> bool:
    lines = text.splitlines()
    try:
        start = lines.index(current_line) + 1
    except ValueError:
        return False
    current_indent = len(current_line) - len(current_line.lstrip(" "))
    for raw in lines[start:]:
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        return indent > current_indent and line.strip().startswith("- ")
    return False


def _parse_value(value: str) -> Any:
    if value.startswith("[") and value.endswith("]"):
        return _parse_inline_list(value)
    if value.startswith("{") and value.endswith("}"):
        return json.loads(value)
    return _coerce_scalar(value)


def _load_override(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(_expand_placeholders(text))
    return _parse_simple_yaml(text)


def _sparse_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _sparse_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _normalize_label(value: Any) -> dict[str, str]:
    if isinstance(value, str):
        return {"name": value, "color": "ededed", "description": ""}
    if isinstance(value, dict) and "name" in value:
        return {
            "name": str(value["name"]),
            "color": str(value.get("color", "ededed")).lstrip("#"),
            "description": str(value.get("description", "")),
        }
    raise ValueError(f"invalid label entry: {value!r}")


def _normalize(config: dict[str, Any]) -> dict[str, Any]:
    labels = config.setdefault("labels", {})
    for key in ("type", "domain", "size", "override"):
        labels[key] = [_normalize_label(item) for item in labels.get(key, [])]
    config["churn_threshold"] = int(config["churn_threshold"])
    config["default_branch"] = str(config["default_branch"])
    config["allowed_base"] = [str(item) for item in config.get("allowed_base", [])]
    config["non_logic_globs"] = [str(item) for item in config.get("non_logic_globs", [])]
    return config


def resolve_config(repo_root: str | Path) -> dict[str, Any]:
    """Return resolved governance config for repo_root.

    Defaults are merged with an optional sparse override at
    .github/issue-driven-governance.yml, or the path named by
    ${ISSUE_GOVERNANCE_CONFIG}. Environment placeholders inside config values are
    expanded during parsing.
    """
    root = Path(repo_root).resolve()
    override_name = os.environ.get(CONFIG_ENV, DEFAULT_CONFIG_PATH)
    override_path = Path(_expand_placeholders(override_name))
    if not override_path.is_absolute():
        override_path = root / override_path

    resolved = deepcopy(DEFAULT_CONFIG)
    if override_path.exists():
        resolved = _sparse_merge(resolved, _load_override(override_path))
    resolved["repo_root"] = str(root)
    resolved["config_path"] = str(override_path) if override_path.exists() else None
    return _normalize(resolved)


def all_label_specs(config: dict[str, Any]) -> list[dict[str, str]]:
    """Return type/domain/size/override label specs in deterministic order."""
    labels = config.get("labels", {})
    combined: list[dict[str, str]] = []
    for key in ("type", "domain", "size", "override"):
        combined.extend(labels.get(key, []))
    return sorted(combined, key=lambda item: item["name"])
