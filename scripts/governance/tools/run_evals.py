#!/usr/bin/env python3
"""Create and validate structural evaluation receipts for skill-local eval inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

RUNTIMES = ("Claude Code", "Codex", "Hermes", "generic")
RESULTS = {"passed", "failed", "pending"}
TRIGGER_COUNT = 16
BEHAVIOR_COUNT = 3


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON input {path}: {error}") from error


def _case_list(value: Any, label: str) -> list[dict[str, Any]]:
    if isinstance(value, list):
        cases = value
    elif isinstance(value, dict):
        for key in ("cases", "scenarios", "triggers"):
            if isinstance(value.get(key), list):
                cases = value[key]
                break
        else:
            raise ValueError(f"{label} must be a JSON array or object with a cases array")
    else:
        raise ValueError(f"{label} must be a JSON array or object with a cases array")

    if not all(isinstance(case, dict) for case in cases):
        raise ValueError(f"{label} cases must be objects")
    return cases


def _source_cases(skill: str, root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Any, Any]:
    evals_dir = root / "skills" / skill / "evals"
    behavior_input = _load_json(evals_dir / "evals.json")
    trigger_input = _load_json(evals_dir / "triggers.json")
    behaviors = _case_list(behavior_input, "evals/evals.json")
    triggers = _case_list(trigger_input, "evals/triggers.json")

    if len(triggers) != TRIGGER_COUNT:
        raise ValueError(f"evals/triggers.json must contain exactly {TRIGGER_COUNT} prompts")
    if len(behaviors) != BEHAVIOR_COUNT:
        raise ValueError(f"evals/evals.json must contain exactly {BEHAVIOR_COUNT} behavior scenarios")

    def receipt_case(source: dict[str, Any], kind: str, index: int) -> dict[str, Any]:
        case_id = source.get("case_id", source.get("id"))
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"{kind} case {index} is missing a non-empty case_id")
        if "expected" not in source:
            raise ValueError(f"{kind} case {case_id!r} is missing expected")
        return {
            "case_id": case_id,
            "kind": kind,
            "expected": source["expected"],
            "actual": None,
            "result": "pending",
        }

    behavior_cases = [receipt_case(case, "behavior", index) for index, case in enumerate(behaviors, 1)]
    trigger_cases = [receipt_case(case, "trigger", index) for index, case in enumerate(triggers, 1)]
    case_ids = [case["case_id"] for case in behavior_cases + trigger_cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("eval input case_id values must be unique")
    return behavior_cases, trigger_cases, behavior_input, trigger_input


def _tree_sha(root: Path) -> str:
    process = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode:
        raise ValueError(process.stderr.strip() or "unable to resolve HEAD tree")
    return process.stdout.strip()


def emit_receipt(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    behavior_cases, trigger_cases, behavior_input, trigger_input = _source_cases(args.skill, root)
    cases = trigger_cases + behavior_cases
    runtimes = []
    for runtime in RUNTIMES:
        runtime_cases = [dict(case) for case in cases]
        runtimes.append(
            {
                "runtime": runtime,
                "runner_identity": None,
                "cases": runtime_cases,
                "raw_result_hash": _sha256(runtime_cases),
                "pass_rate": 0.0,
            }
        )
    return {
        "protocol_version": 1,
        "protocol_hash": _sha256({"evals": behavior_input, "triggers": trigger_input}),
        "skill": args.skill,
        "pr": args.pr,
        "tested_tree_sha": _tree_sha(root),
        "inputs": {
            "baseline_ref": args.baseline_ref,
            "candidate_ref": args.candidate_ref,
            "no_skill_ref": args.no_skill_ref,
        },
        "runtimes": runtimes,
        "pass_rate": 0.0,
    }


def _rate(cases: list[dict[str, Any]]) -> float:
    return sum(case["result"] == "passed" for case in cases) / len(cases)


def validate_receipt(receipt: Any, root: Path, supplied_skill: str | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(receipt, dict):
        return ["receipt must be a JSON object"]
    if receipt.get("protocol_version") != 1:
        errors.append("protocol_version must be 1")
    skill = receipt.get("skill")
    if not isinstance(skill, str) or not skill:
        errors.append("skill must be a non-empty string")
    elif supplied_skill is not None and skill != supplied_skill:
        errors.append(f"receipt skill {skill!r} does not match {supplied_skill!r}")
    for key in ("pr", "tested_tree_sha"):
        if not isinstance(receipt.get(key), str) or not receipt[key]:
            errors.append(f"{key} must be a non-empty string")
    inputs = receipt.get("inputs")
    if not isinstance(inputs, dict) or any(
        not isinstance(inputs.get(key), str) or not inputs[key]
        for key in ("baseline_ref", "candidate_ref", "no_skill_ref")
    ):
        errors.append("inputs must contain non-empty baseline_ref, candidate_ref, and no_skill_ref strings")

    source_signature: list[tuple[Any, Any, Any]] | None = None
    if isinstance(skill, str) and skill:
        evals_dir = root / "skills" / skill / "evals"
        if evals_dir.exists():
            try:
                behavior_cases, trigger_cases, behavior_input, trigger_input = _source_cases(skill, root)
            except ValueError as error:
                errors.append(str(error))
            else:
                expected_hash = _sha256({"evals": behavior_input, "triggers": trigger_input})
                if receipt.get("protocol_hash") != expected_hash:
                    errors.append("protocol_hash does not match local eval inputs")
                source_signature = [
                    (case["case_id"], case["kind"], case["expected"])
                    for case in trigger_cases + behavior_cases
                ]
    if not isinstance(receipt.get("protocol_hash"), str) or not receipt.get("protocol_hash"):
        errors.append("protocol_hash must be a non-empty string")

    runtimes = receipt.get("runtimes")
    if not isinstance(runtimes, list) or len(runtimes) != len(RUNTIMES):
        return errors + [f"runtimes must contain exactly {len(RUNTIMES)} rows"]
    names = [runtime.get("runtime") if isinstance(runtime, dict) else None for runtime in runtimes]
    if set(names) != set(RUNTIMES) or len(set(names)) != len(RUNTIMES):
        errors.append("runtimes must contain one row for each required runtime")

    all_cases: list[dict[str, Any]] = []
    for index, runtime in enumerate(runtimes, 1):
        if not isinstance(runtime, dict):
            errors.append(f"runtime row {index} must be an object")
            continue
        cases = runtime.get("cases")
        if not isinstance(cases, list) or len(cases) != TRIGGER_COUNT + BEHAVIOR_COUNT:
            errors.append(f"runtime row {index} must contain exactly 19 cases")
            continue
        if not all(isinstance(case, dict) for case in cases):
            errors.append(f"runtime row {index} cases must be objects")
            continue
        case_ids = [case.get("case_id") for case in cases]
        if len(set(case_ids)) != len(cases) or any(not isinstance(case_id, str) or not case_id for case_id in case_ids):
            errors.append(f"runtime row {index} case_id values must be unique non-empty strings")
        kinds = [case.get("kind") for case in cases]
        if kinds.count("trigger") != TRIGGER_COUNT or kinds.count("behavior") != BEHAVIOR_COUNT:
            errors.append(f"runtime row {index} must contain 16 trigger and 3 behavior cases")
        if any(case.get("result") not in RESULTS for case in cases):
            errors.append(f"runtime row {index} has an invalid result")
        if any("expected" not in case or "actual" not in case for case in cases):
            errors.append(f"runtime row {index} cases must contain expected and actual fields")
        if source_signature is not None:
            signature = [(case.get("case_id"), case.get("kind"), case.get("expected")) for case in cases]
            if signature != source_signature:
                errors.append(f"runtime row {index} cases do not match local eval inputs")
        expected_hash = _sha256(cases)
        if runtime.get("raw_result_hash") != expected_hash:
            errors.append(f"runtime row {index} raw_result_hash does not match cases")
        expected_rate = _rate(cases)
        if runtime.get("pass_rate") != expected_rate:
            errors.append(f"runtime row {index} pass_rate does not match cases")
        if any(case.get("result") != "passed" for case in cases):
            errors.append(f"runtime row {index} contains non-passing cases")
        all_cases.extend(cases)

    if all_cases:
        expected_rate = _rate(all_cases)
        if receipt.get("pass_rate") != expected_rate:
            errors.append("pass_rate does not match all runtime cases")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", nargs="?", help="skill package name")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit", type=Path, metavar="OUT_JSON", help="write a pending receipt skeleton")
    mode.add_argument("--validate", type=Path, metavar="RECEIPT_JSON", help="validate a completed receipt")
    parser.add_argument("--pr", help="pull request identifier for emitted receipts")
    parser.add_argument("--baseline-ref", help="baseline ref used by the evaluation")
    parser.add_argument("--candidate-ref", help="candidate ref used by the evaluation")
    parser.add_argument("--no-skill-ref", help="reference without the skill used by the evaluation")
    args = parser.parse_args()
    root = Path.cwd()

    if args.emit:
        missing = [
            flag
            for flag, value in (("skill", args.skill), ("--pr", args.pr), ("--baseline-ref", args.baseline_ref), ("--candidate-ref", args.candidate_ref), ("--no-skill-ref", args.no_skill_ref))
            if not value
        ]
        if missing:
            parser.error("--emit requires " + ", ".join(missing))
        try:
            receipt = emit_receipt(args, root)
        except ValueError as error:
            parser.error(str(error))
        args.emit.parent.mkdir(parents=True, exist_ok=True)
        args.emit.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0

    try:
        receipt = _load_json(args.validate)
    except ValueError as error:
        print(f"run_evals: {error}")
        return 1
    errors = validate_receipt(receipt, root, args.skill)
    if errors:
        for error in errors:
            print(f"run_evals: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
