"""Repository namespace classification shared by governance checkers."""

from __future__ import annotations

from typing import Any


def repo_namespace(reference: str) -> str:
    """Return the repository namespace from a package reference."""
    return reference.partition("/")[0]


def is_known_external_reference(reference: str, config: dict[str, Any], active_repos: set[str]) -> bool:
    """Return whether a reference belongs to a configured unavailable external repository."""
    external_repos = config.get("external_repos", [])
    return (
        isinstance(reference, str)
        and isinstance(external_repos, list)
        and repo_namespace(reference) in external_repos
        and repo_namespace(reference) not in active_repos
    )
