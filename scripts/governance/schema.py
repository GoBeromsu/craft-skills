"""Schema validation for generated governance aggregates."""

from __future__ import annotations

from typing import Any

CHECKER_NAME = "schema"
CHECKER_VERSION = "1"

KIND_VALUES = {"leaf", "thick", "area", "adapter-wrapper", "runtime-hook", "command"}
LIFECYCLE_VALUES = {"proposed", "admitted", "active", "deprecated", "archived", "deleted"}
VISIBILITY_VALUES = {"public", "private", "mixed"}
ADAPTER_STATUS_VALUES = {"generated", "hand-written", "omitted"}
PROFILE_ENUMS = {
    "topology": KIND_VALUES,
    "discovery_parity": {"strict", "declared-omissions", "skip"},
    "adapter_parity": {"strict", "declared-omissions", "skip"},
    "provenance_license": {"strict", "warn", "skip"},
    "private_data_hygiene": {"strict", "warn", "skip"},
    "deprecation": {"strict", "warn", "skip"},
    "routing_eval": {"smoke", "full", "skip"},
    "install_doctor": {"package", "runtime", "skip"},
}

REQUIRED_PACKAGE_FIELDS = [
    "schema_version",
    "id",
    "name",
    "kind",
    "lifecycle",
    "version",
    "owner_repo",
    "owner_domain",
    "visibility",
    "compatibility",
    "provenance",
    "validation_profile",
]


def _finding(code: str, message: str, package: dict[str, Any] | None = None, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "checker": CHECKER_NAME,
        "severity": "blocking",
        "code": code,
        "package_id": package.get("id") if isinstance(package, dict) else None,
        "message": message,
        "path": None,
        "details": details or {},
    }


def _require_string(
    findings: list[dict[str, Any]],
    package: dict[str, Any],
    field: str,
    *,
    allow_empty: bool = False,
) -> None:
    value = package.get(field)
    if not isinstance(value, str) or (not allow_empty and not value):
        findings.append(_finding("schema.package_field_type", f"package.{field} must be a non-empty string", package, {"field": field}))


def _validate_string_array(
    findings: list[dict[str, Any]],
    package: dict[str, Any],
    field: str,
    *,
    required: bool,
) -> None:
    if field not in package:
        if required:
            findings.append(_finding("schema.package_missing_field", f"package.{field} is required", package, {"field": field}))
        return
    value = package.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        findings.append(_finding("schema.package_field_type", f"package.{field} must be an array of strings", package, {"field": field}))


def _validate_provenance(findings: list[dict[str, Any]], package: dict[str, Any]) -> None:
    provenance = package.get("provenance")
    if not isinstance(provenance, dict):
        findings.append(_finding("schema.package_field_type", "package.provenance must be an object", package, {"field": "provenance"}))
        return
    for field in ["upstream", "commit", "license", "absorbed_from"]:
        if field not in provenance:
            findings.append(_finding("schema.provenance_missing_field", f"package.provenance.{field} is required", package, {"field": field}))
    absorbed_from = provenance.get("absorbed_from")
    if not isinstance(absorbed_from, list) or any(not isinstance(item, str) for item in absorbed_from):
        findings.append(
            _finding(
                "schema.provenance_field_type",
                "package.provenance.absorbed_from must be an array of strings",
                package,
                {"field": "absorbed_from"},
            )
        )


def _validate_adapters(findings: list[dict[str, Any]], package: dict[str, Any]) -> None:
    if "adapters" not in package:
        return
    adapters = package.get("adapters")
    if isinstance(adapters, dict):
        iterable = list(adapters.values())
    elif isinstance(adapters, list):
        iterable = adapters
    else:
        findings.append(_finding("schema.adapters_type", "package.adapters must be an array or object", package, {"field": "adapters"}))
        return

    for index, adapter in enumerate(iterable):
        if not isinstance(adapter, dict):
            findings.append(_finding("schema.adapter_type", "every adapter declaration must be an object", package, {"index": index}))
            continue
        for field in ["runtime", "surface", "status", "reason"]:
            if field not in adapter:
                findings.append(_finding("schema.adapter_missing_field", f"adapter.{field} is required", package, {"index": index, "field": field}))
        for field in ["runtime", "surface"]:
            if not isinstance(adapter.get(field), str) or not adapter.get(field):
                findings.append(_finding("schema.adapter_field_type", f"adapter.{field} must be a non-empty string", package, {"index": index, "field": field}))
        status = adapter.get("status")
        if status not in ADAPTER_STATUS_VALUES:
            findings.append(
                _finding(
                    "schema.adapter_enum",
                    "adapter.status has an unsupported value",
                    package,
                    {"index": index, "field": "status", "value": status, "allowed": sorted(ADAPTER_STATUS_VALUES)},
                )
            )
        reason = adapter.get("reason")
        if reason is not None and not isinstance(reason, str):
            findings.append(_finding("schema.adapter_field_type", "adapter.reason must be a string or null", package, {"index": index, "field": "reason"}))


def _validate_profile(findings: list[dict[str, Any]], package: dict[str, Any]) -> None:
    profile = package.get("validation_profile")
    if not isinstance(profile, dict):
        findings.append(_finding("schema.package_field_type", "package.validation_profile must be an object", package, {"field": "validation_profile"}))
        return
    for field, allowed in PROFILE_ENUMS.items():
        if field in profile and profile[field] not in allowed:
            findings.append(
                _finding(
                    "schema.validation_profile_enum",
                    f"package.validation_profile.{field} has an unsupported value",
                    package,
                    {"field": field, "value": profile[field], "allowed": sorted(allowed)},
                )
            )


def _validate_package(package: Any) -> list[dict[str, Any]]:
    if not isinstance(package, dict):
        return [_finding("schema.package_type", "every aggregate package must be an object")]

    findings: list[dict[str, Any]] = []
    for field in REQUIRED_PACKAGE_FIELDS:
        if field not in package:
            findings.append(_finding("schema.package_missing_field", f"package.{field} is required", package, {"field": field}))

    if package.get("schema_version") != 1:
        findings.append(_finding("schema.package_schema_version", "package.schema_version must be 1", package, {"value": package.get("schema_version")}))

    for field in ["id", "name", "version", "owner_repo", "owner_domain"]:
        _require_string(findings, package, field)

    for field, allowed in [("kind", KIND_VALUES), ("lifecycle", LIFECYCLE_VALUES), ("visibility", VISIBILITY_VALUES)]:
        if package.get(field) not in allowed:
            findings.append(
                _finding(
                    "schema.package_enum",
                    f"package.{field} has an unsupported value",
                    package,
                    {"field": field, "value": package.get(field), "allowed": sorted(allowed)},
                )
            )

    _validate_string_array(findings, package, "compatibility", required=True)
    _validate_string_array(findings, package, "replacement_for", required=False)
    _validate_string_array(findings, package, "children", required=False)
    replaced_by = package.get("replaced_by")
    if replaced_by is not None and not isinstance(replaced_by, str) and not (
        isinstance(replaced_by, list) and all(isinstance(item, str) for item in replaced_by)
    ):
        findings.append(_finding("schema.package_field_type", "package.replaced_by must be a string, array of strings, or null", package, {"field": "replaced_by"}))

    _validate_provenance(findings, package)
    _validate_adapters(findings, package)
    _validate_profile(findings, package)
    return findings


def validate_aggregate(aggregate: Any, *, source: str = "aggregate") -> list[dict[str, Any]]:
    """Return blocking schema findings for an aggregate-like object."""

    if not isinstance(aggregate, dict):
        return [_finding("schema.aggregate_type", f"{source} must be an object")]

    findings: list[dict[str, Any]] = []
    for field in ["schema_version", "generated", "generator", "source_manifests", "packages"]:
        if field not in aggregate:
            findings.append(_finding("schema.aggregate_missing_field", f"aggregate.{field} is required", details={"field": field}))

    if aggregate.get("schema_version") != 1:
        findings.append(_finding("schema.aggregate_schema_version", "aggregate.schema_version must be 1", details={"value": aggregate.get("schema_version")}))
    if aggregate.get("generated") is not True:
        findings.append(_finding("schema.aggregate_generated", "aggregate.generated must be true", details={"value": aggregate.get("generated")}))

    generator = aggregate.get("generator")
    if not isinstance(generator, dict):
        findings.append(_finding("schema.generator_type", "aggregate.generator must be an object"))
    else:
        for field in ["name", "version"]:
            if not isinstance(generator.get(field), str) or not generator.get(field):
                findings.append(_finding("schema.generator_field_type", f"aggregate.generator.{field} must be a non-empty string", details={"field": field}))

    source_manifests = aggregate.get("source_manifests")
    if not isinstance(source_manifests, list) or any(not isinstance(item, str) for item in source_manifests):
        findings.append(_finding("schema.source_manifests_type", "aggregate.source_manifests must be an array of strings"))
    elif len(set(source_manifests)) != len(source_manifests):
        findings.append(_finding("schema.source_manifests_unique", "aggregate.source_manifests must be unique"))

    packages = aggregate.get("packages")
    if not isinstance(packages, list):
        findings.append(_finding("schema.packages_type", "aggregate.packages must be an array"))
        return findings

    seen_ids: set[str] = set()
    for package in packages:
        findings.extend(_validate_package(package))
        if isinstance(package, dict) and isinstance(package.get("id"), str):
            package_id = package["id"]
            if package_id in seen_ids:
                findings.append(_finding("schema.duplicate_package_id", "aggregate package ids must be unique", package, {"id": package_id}))
            seen_ids.add(package_id)

    return findings
