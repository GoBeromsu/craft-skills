#!/usr/bin/env python3
"""Run registered governance checkers and write JSON plus text reports."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import schema

CHECKER_MODULES = [
    "checkers.topology",
    "checkers.inventory_parity",
    "checkers.adapter_parity",
    "checkers.provenance",
    "checkers.hygiene",
    "checkers.deprecation",
    "checkers.routing_eval",
    "checkers.install_doctor",
]
PROFILE_CHECKERS = {
    "portable": [
        "checkers.topology",
        "checkers.inventory_parity",
        "checkers.provenance",
        "checkers.hygiene",
        "checkers.deprecation",
        "checkers.routing_eval",
        "checkers.install_doctor",
    ],
    "cross-repo": CHECKER_MODULES,
}
PROFILE_CASESETS = {
    "portable": ["docs/governance/routing-eval-cases.yaml"],
    "cross-repo": [
        "docs/governance/routing-eval-cases.yaml",
        "docs/governance/routing-eval-cases.cross-repo.yaml",
    ],
}
_BUILD_AGGREGATE_MODULE: Any | None = None


def _strip_comment_lines(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def _load_jsonish(path: Path) -> Any:
    try:
        return json.loads(_strip_comment_lines(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: expected JSON-compatible input: {exc}") from exc



def _load_build_aggregate() -> Any:
    global _BUILD_AGGREGATE_MODULE
    if _BUILD_AGGREGATE_MODULE is not None:
        return _BUILD_AGGREGATE_MODULE

    script_path = Path(__file__).with_name("build-aggregate.py")
    spec = importlib.util.spec_from_file_location("governance_build_aggregate", script_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"{script_path}: cannot load aggregate builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _BUILD_AGGREGATE_MODULE = module
    return module


def _blocking_finding(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "checker": "aggregate",
        "severity": "blocking",
        "code": code,
        "package_id": None,
        "message": message,
        "path": None,
        "details": details or {},
    }


def _stale_aggregate_findings(builder: Any, aggregate: dict[str, Any], aggregate_path: Path | None) -> list[dict[str, Any]]:
    if aggregate_path is None:
        return []
    expected_bytes = builder.render(aggregate, visibility="all").encode("utf-8")
    expected_sha = sha256(expected_bytes).hexdigest()

    if not aggregate_path.exists():
        return [
            _blocking_finding(
                "aggregate.missing",
                "--aggregate path was provided but does not exist.",
                {"aggregate_path": str(aggregate_path), "expected_sha256": expected_sha},
            )
        ]

    actual_bytes = aggregate_path.read_bytes()
    actual_sha = sha256(actual_bytes).hexdigest()
    if actual_sha == expected_sha:
        return []

    return [
        _blocking_finding(
            "aggregate.stale_or_hand_edited",
            "stale/hand-edited aggregate: --aggregate content does not match manifest-regenerated aggregate.",
            {
                "aggregate_path": str(aggregate_path),
                "expected_sha256": expected_sha,
                "actual_sha256": actual_sha,
            },
        )
    ]


def _summarize(findings: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"blocking": 0, "advisory": 0}
    for finding in findings:
        severity = finding.get("severity")
        if severity in summary:
            summary[severity] += 1
    summary["total"] = len(findings)
    return summary


def _text_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "Governance checker report",
        f"aggregate: {report['aggregate']}",
        f"checkers: {', '.join(report['checkers'])}",
        f"findings: {summary['total']} total; {summary['blocking']} blocking; {summary['advisory']} advisory",
        "",
    ]
    if not report["findings"]:
        lines.append("No findings.")
    else:
        for finding in report["findings"]:
            lines.append(
                f"[{finding.get('severity')}] {finding.get('checker')} {finding.get('code')} "
                f"{finding.get('package_id')}: {finding.get('message')}"
            )
            if finding.get("path"):
                lines.append(f"  path: {finding['path']}")
            details = finding.get("details") or {}
            if details:
                lines.append(f"  details: {json.dumps(details, ensure_ascii=False, sort_keys=True)}")
    return "\n".join(lines) + "\n"


def run(config_path: Path, aggregate_path: Path | None, profile: str = "portable") -> dict[str, Any]:
    config = _load_jsonish(config_path)
    builder = _load_build_aggregate()
    checker_config = {
        **config,
        "profile": profile,
        "routing_eval_casesets": PROFILE_CASESETS[profile],
    }
    aggregate = builder.build(config_path, visibility="all")
    findings: list[dict[str, Any]] = []
    checker_names: list[str] = ["schema"]

    findings.extend(_stale_aggregate_findings(builder, aggregate, aggregate_path))

    schema_findings = schema.validate_aggregate(aggregate, source="manifest-regenerated aggregate")
    findings.extend(schema_findings)

    if not schema_findings:
        for module_name in PROFILE_CHECKERS[profile]:
            module = importlib.import_module(module_name)
            checker_name = getattr(module, "CHECKER_NAME", module_name)
            checker_names.append(checker_name)
            checker_findings = module.run(aggregate, checker_config)
            if not isinstance(checker_findings, list):
                raise SystemExit(f"{module_name}: run() must return a list")
            findings.extend(checker_findings)

    findings.sort(key=lambda item: (str(item.get("severity")), str(item.get("checker")), str(item.get("package_id")), str(item.get("code"))))
    return {
        "schema_version": 1,
        "aggregate": str(aggregate_path) if aggregate_path is not None else "manifest-regenerated in memory",
        "aggregate_source": "manifest-regenerated in memory",
        "profile": profile,
        "casesets": PROFILE_CASESETS[profile],
        "checkers": checker_names,
        "summary": _summarize(findings),
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="JSON-compatible repos.yaml path")
    parser.add_argument("--aggregate", type=Path, default=None, help="optional aggregate JSON path; compared against a manifest-regenerated aggregate")
    parser.add_argument("--json-out", type=Path, required=True, help="JSON report output path")
    parser.add_argument("--text-out", type=Path, required=True, help="text report output path")
    parser.add_argument("--profile", choices=PROFILE_CHECKERS, default="portable", help="governance checker profile")
    args = parser.parse_args()

    report = run(args.config, args.aggregate, args.profile)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.text_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    args.text_out.write_text(_text_report(report), encoding="utf-8")
    print(f"wrote {args.json_out} and {args.text_out}")
    return 1 if report["summary"]["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
