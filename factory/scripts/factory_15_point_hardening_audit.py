#!/usr/bin/env python3
"""Audit the Factory 15-point hardening program scope lock.

This audit is intentionally not a completion claim. It proves that the program
tracks every required point and that partial work cannot be reported as done.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_POINT_IDS = [f"P{i:02d}" for i in range(1, 16)]
REQUIRED_COMPLETION_BAR = {
    "public_issue_or_mapped_issue_section",
    "kanban_or_runtime_task_result_artifact",
    "productized_code_schema_template_or_doc_update",
    "regression_test_or_validator_coverage",
    "green_ci_and_merge_when_repo_changes",
    "live_or_simulated_behavior_proof",
    "no_factory_owned_blocker_left_as_passive_bureaucracy",
}
REQUIRED_WORKSTREAMS = {
    "control_plane_invariants",
    "discovery_preflight_capability",
    "operator_ux",
    "architecture_quality",
    "worker_safety_accountability",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def audit_program(program: dict[str, Any], *, require_complete: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if program.get("record_type") != "factory_15_point_hardening_program":
        errors.append("record_type must be factory_15_point_hardening_program")

    raw_scope_lock = program.get("scope_lock")
    scope_lock: dict[str, Any] = raw_scope_lock if isinstance(raw_scope_lock, dict) else {}
    if scope_lock.get("expected_point_count") != 15:
        errors.append("scope_lock.expected_point_count must be exactly 15")
    if scope_lock.get("partial_must_not_be_reported_done") is not True:
        errors.append("scope_lock.partial_must_not_be_reported_done must be true")
    if scope_lock.get("negative_closeout_counts_as_progress") is not False:
        errors.append("scope_lock.negative_closeout_counts_as_progress must be false")
    if scope_lock.get("factory_owned_blocker_requires_repair_loop") is not True:
        errors.append("scope_lock.factory_owned_blocker_requires_repair_loop must be true")
    if scope_lock.get("human_stop_requires_exact_external_authority") is not True:
        errors.append("scope_lock.human_stop_requires_exact_external_authority must be true")

    completion_bar = set(program.get("global_completion_bar") or [])
    missing_bar = sorted(REQUIRED_COMPLETION_BAR - completion_bar)
    if missing_bar:
        errors.append("global_completion_bar missing: " + ", ".join(missing_bar))

    points = program.get("points")
    if not isinstance(points, list):
        errors.append("points must be a list")
        points = []
    if len(points) != 15:
        errors.append(f"points must contain exactly 15 entries, found {len(points)}")

    ids = [str(point.get("id") or "") for point in points if isinstance(point, dict)]
    if ids != EXPECTED_POINT_IDS:
        errors.append(f"points must be ordered exactly {EXPECTED_POINT_IDS}, found {ids}")

    seen_workstreams: set[str] = set()
    incomplete_points: list[str] = []
    for expected_id, point in zip(EXPECTED_POINT_IDS, points):
        if not isinstance(point, dict):
            errors.append(f"{expected_id} must be an object")
            continue
        point_id = str(point.get("id") or "")
        for field in ("title", "problem", "required_behavior", "workstream"):
            if not str(point.get(field) or "").strip():
                errors.append(f"{point_id or expected_id}.{field} is required")
        workstream = str(point.get("workstream") or "")
        if workstream:
            seen_workstreams.add(workstream)
            if workstream not in REQUIRED_WORKSTREAMS:
                errors.append(f"{point_id}.workstream has unknown value {workstream}")
        for field in ("issue_refs", "required_artifact_classes", "verification"):
            value = point.get(field)
            if not isinstance(value, list) or not value or not all(str(item).strip() for item in value):
                errors.append(f"{point_id or expected_id}.{field} must be a non-empty string list")
        implementation_status = str(point.get("implementation_status") or "not_yet_claimed_complete")
        if implementation_status != "complete":
            incomplete_points.append(point_id or expected_id)

    missing_workstreams = sorted(REQUIRED_WORKSTREAMS - seen_workstreams)
    if missing_workstreams:
        errors.append("missing workstreams: " + ", ".join(missing_workstreams))

    program_status = str(program.get("status") or "")
    if incomplete_points and program_status == "complete":
        errors.append("program status cannot be complete while points lack implementation_status=complete")
    if require_complete and incomplete_points:
        errors.append("require-complete failed; incomplete points: " + ", ".join(incomplete_points))
    if incomplete_points:
        warnings.append("implementation incomplete for: " + ", ".join(incomplete_points))

    result = "FAIL" if errors else ("PASS_COMPLETE" if not incomplete_points else "PASS_SCOPE_LOCK_PARTIAL_IMPLEMENTATION")
    return {
        "result": result,
        "program_id": program.get("program_id"),
        "point_count": len(points),
        "expected_point_count": 15,
        "incomplete_point_ids": incomplete_points,
        "workstreams": sorted(seen_workstreams),
        "errors": errors,
        "warnings": warnings,
    }


def markdown_report(audit: dict[str, Any]) -> str:
    lines = [
        "# Factory 15-point hardening audit",
        "",
        f"Result: `{audit['result']}`",
        f"Program: `{audit.get('program_id')}`",
        f"Points: {audit['point_count']}/{audit['expected_point_count']}",
        "",
    ]
    if audit["errors"]:
        lines.append("## Errors")
        lines.extend(f"- {item}" for item in audit["errors"])
        lines.append("")
    if audit["warnings"]:
        lines.append("## Warnings")
        lines.extend(f"- {item}" for item in audit["warnings"])
        lines.append("")
    lines.append("## Incomplete point IDs")
    if audit["incomplete_point_ids"]:
        lines.extend(f"- {item}" for item in audit["incomplete_point_ids"])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit Factory 15-point hardening scope lock")
    parser.add_argument("program", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    audit = audit_program(load_json(args.program), require_complete=args.require_complete)
    text = json.dumps(audit, indent=2, sort_keys=True)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.write_text(markdown_report(audit), encoding="utf-8")
    print(text)
    return 1 if audit["result"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
