#!/usr/bin/env python3
"""Executable audit for missing or partial world-class product processes.

This is not a phase reordering audit. It checks whether the factory explicitly
models product-creation processes such as PRD-grade requirements, system design,
analytics, GTM, QA strategy and release readiness.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = ROOT / "templates" / "factory-world-class-process-registry.json"
PRIVATE_REF_RE = re.compile(r"((?<![A-Za-z])[A-Za-z]:[\\/]|\\\\|/home/|/Users/|/srv/|/var/|file://)", re.I)
REQUIRED_PROCESS_KEYS = {
    "prd_grade_product_requirements",
    "system_design_review",
    "design_review_and_accessibility",
    "product_analytics_plan",
    "go_to_market_distribution_review",
    "qa_strategy_and_test_matrix",
    "release_readiness_review",
    "post_launch_review",
    "ai_eval_and_model_risk_review",
}
VALID_SHAPES = {
    "phase_and_gate",
    "phase_or_gate",
    "gate",
    "parallel_lane",
    "parallel_lane_and_gate",
    "template_and_gate",
    "contract_and_gate",
    "continuous_lane_and_receipt",
    "receipt_section",
    "worker_packet_obligation",
}
NEW_OR_PARTIAL = {"missing_new", "partial_covered"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def list_field(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    return value if isinstance(value, list) else []


def dict_field(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    return cast(dict[str, Any], value) if isinstance(value, dict) else {}


def private_ref_errors(value: Any, at: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, str):
        if PRIVATE_REF_RE.search(value):
            errors.append(f"{at}: private/local refs are forbidden in public process registry")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(private_ref_errors(item, f"{at}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            errors.extend(private_ref_errors(item, f"{at}.{key}"))
    return errors


def validate_world_class_process_registry(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("record_type") != "factory_world_class_process_registry":
        errors.append("$.record_type must be factory_world_class_process_registry")
    policy = dict_field(registry, "integration_policy")
    for key in (
        "do_not_only_reorder_existing_phases",
        "process_can_be_phase_gate_lane_contract_template_worker_or_receipt",
        "hermes_runtime_floor_preserved",
        "overkill_method_contract_gate_layer_preserved",
    ):
        if policy.get(key) is not True:
            errors.append(f"$.integration_policy.{key} must be true")

    processes = [item for item in list_field(registry, "processes") if isinstance(item, dict)]
    by_key = {str(item.get("process_key")): item for item in processes}
    missing_required = sorted(REQUIRED_PROCESS_KEYS - set(by_key))
    if missing_required:
        errors.append("missing required world-class process keys: " + ", ".join(missing_required))

    required_declared = set(str(item) for item in list_field(registry, "required_process_keys"))
    missing_from_declared = sorted(REQUIRED_PROCESS_KEYS - required_declared)
    if missing_from_declared:
        errors.append("$.required_process_keys must include: " + ", ".join(missing_from_declared))

    new_or_partial_count = sum(1 for item in processes if item.get("coverage_status") in NEW_OR_PARTIAL)
    minimum = int(registry.get("minimum_new_or_partial_processes") or 8)
    if new_or_partial_count < minimum:
        errors.append("registry must identify missing or partial world-class processes, not only existing coverage")
    if new_or_partial_count == 0:
        errors.append("registry must not be only a reordering of existing phases")

    for index, process in enumerate(processes):
        prefix = f"$.processes[{index}:{process.get('process_key')}]"
        if process.get("coverage_status") not in {"missing_new", "partial_covered", "existing_core"}:
            errors.append(f"{prefix}.coverage_status is invalid")
        if process.get("factory_shape") not in VALID_SHAPES:
            errors.append(f"{prefix}.factory_shape must choose a productized shape beyond raw phase labels")
        for key in ("trigger_conditions", "required_artifacts", "required_gates", "proof_requirements", "reference_methods"):
            if not list_field(process, key):
                errors.append(f"{prefix}.{key} must be non-empty")
        for key in ("integration_decision", "insertion_point", "risk_if_absent"):
            if not str(process.get(key) or "").strip():
                errors.append(f"{prefix}.{key} must be non-empty")

    if not any(str(item).lower().find("raw study") >= 0 for item in list_field(registry, "non_goals")):
        errors.append("$.non_goals must reject publishing raw study docs")
    errors.extend(private_ref_errors(registry))
    return errors


def build_world_class_process_gap_audit(registry_path: Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    registry = load_json(registry_path)
    errors = validate_world_class_process_registry(registry)
    processes = [item for item in list_field(registry, "processes") if isinstance(item, dict)]
    new_or_partial = [item for item in processes if item.get("coverage_status") in NEW_OR_PARTIAL]
    missing_new = [item for item in processes if item.get("coverage_status") == "missing_new"]
    partial = [item for item in processes if item.get("coverage_status") == "partial_covered"]
    result = "PASS" if not errors else "FAIL"
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-world-class-process-gap-audit.schema.json",
        "record_type": "factory_world_class_process_gap_audit",
        "audit_id": "factory-world-class-process-gap-audit-v1",
        "result": result,
        "score": max(0, 100 - len(errors) * 10),
        "thesis": "The factory must not just reorder existing phases; it must explicitly add or strengthen missing world-class product processes.",
        "registry_ref": str(registry_path.relative_to(ROOT) if registry_path.is_relative_to(ROOT) else registry_path),
        "processes": processes,
        "summary": {
            "process_count": len(processes),
            "new_or_partial_process_count": len(new_or_partial),
            "missing_new_count": len(missing_new),
            "partial_covered_count": len(partial),
            "required_process_count": len(REQUIRED_PROCESS_KEYS),
            "errors": len(errors),
        },
        "missing_new_process_keys": [str(item.get("process_key")) for item in missing_new],
        "partial_covered_process_keys": [str(item.get("process_key")) for item in partial],
        "errors": errors,
    }


def audit_to_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Factory World-Class Process Gap Audit",
        "",
        f"Result: {audit['result']}",
        f"Score: {audit['score']}",
        "",
        "This audit is not just reorder work. It checks for missing_or_partial world-class processes.",
        "",
        "## Process Findings",
        "",
    ]
    for item in audit["processes"]:
        lines.append(f"- {item['name']} (`{item['process_key']}`): {item['coverage_status']}")
        lines.append(f"  - shape: {item['factory_shape']}")
        lines.append(f"  - decision: {item['integration_decision']}")
    if audit["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in audit["errors"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Factory world-class process gap audit")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)

    audit = build_world_class_process_gap_audit(args.registry)
    if args.out:
        write_json(args.out, audit)
        print(f"Wrote {args.out}")
    else:
        print(json.dumps(audit, indent=2, sort_keys=True))
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(audit_to_markdown(audit), encoding="utf-8")
        print(f"Wrote {args.markdown}")
    if audit["errors"]:
        for error in audit["errors"]:
            print(error, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
