#!/usr/bin/env python3
"""Swiss Watch reliability audit for Overkill Factory.

This script is intentionally a validator, not a runtime. It reads the public
Factory V2 contracts and checks that the factory remains Hermes-native instead
of becoming a mini-Hermes sidecar runtime.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import factoryctl  # noqa: E402

PROGRAM_REF = "docs/maintenance/swiss-watch-reliability-program.md"
GEAR_MATRIX_REF = "docs/maintenance/swiss-watch-gear-matrix.md"
REQUIRED_BLOCK_KINDS = {"dependency", "needs_input", "capability", "transient"}
MANAGER_WORKERS = {"overkill-factory-gerente"}
DIMENSIONS = [
    "gear_contract",
    "hermes_native_authority",
    "autonomy_no_idle",
    "operator_experience",
    "worker_quality_floor",
    "block_classification",
    "security_boundary",
    "performance_loop_control",
]


def _items(value: Any) -> list[str]:
    return factoryctl.string_list(value)


def _worker_ids(registry: dict[str, Any]) -> set[str]:
    workers = registry.get("workers") if isinstance(registry.get("workers"), list) else []
    return {
        str(worker.get("worker_id") or "").strip()
        for worker in workers
        if isinstance(worker, dict) and str(worker.get("worker_id") or "").strip()
    }


def check(name: str, passed: bool, evidence_refs: list[str], remediation: str = "") -> dict[str, Any]:
    return {
        "check": name,
        "result": "PASS" if passed else "FAIL",
        "evidence_refs": evidence_refs,
        "remediation": remediation,
    }


def score(checks: list[dict[str, Any]]) -> int:
    if not checks:
        return 0
    return round((sum(1 for item in checks if item.get("result") == "PASS") / len(checks)) * 100)


def build_audit(
    compiled_plan: dict[str, Any],
    typed_block_policy: dict[str, Any],
    worker_registry: dict[str, Any],
    *,
    created_at: str | None = None,
) -> dict[str, Any]:
    created = created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    plan_errors = factoryctl.validate_factory_workflow_compiled_plan(compiled_plan)
    worker_ids = _worker_ids(worker_registry)
    phases = compiled_plan.get("phases") if isinstance(compiled_plan.get("phases"), list) else []
    terminal_phase_id = str(phases[-1].get("phase_id") if phases and isinstance(phases[-1], dict) else "")
    native_kinds = set(_items(typed_block_policy.get("native_block_kinds")))
    policy_authority = str(typed_block_policy.get("runtime_authority") or "").strip()
    policy_rules = typed_block_policy.get("kind_rules") if isinstance(typed_block_policy.get("kind_rules"), dict) else {}
    loop_policy = typed_block_policy.get("same_cause_loop_policy") if isinstance(typed_block_policy.get("same_cause_loop_policy"), dict) else {}

    gear_assessments: list[dict[str, Any]] = []
    for phase in phases:
        if not isinstance(phase, dict):
            continue
        phase_id = str(phase.get("phase_id") or "").strip()
        required_workers = set(_items(phase.get("required_workers")))
        missing_workers = sorted(required_workers - worker_ids - MANAGER_WORKERS)
        checks = [
            check(
                "input_output_contract",
                bool(_items(phase.get("required_artifacts"))) and bool(_items(phase.get("required_gates"))),
                ["templates/factory-workflow-compiled-plan.json", GEAR_MATRIX_REF],
                "Add required artifacts and gates to the compiled phase contract.",
            ),
            check(
                "worker_authority_contract",
                bool(required_workers) and not missing_workers,
                ["agents/worker-registry.public.json", "agents/hermes-profile-bindings.public.json"],
                "Register missing workers or explicitly classify manager-only operators: " + ", ".join(missing_workers),
            ),
            check(
                "hermes_native_next_action",
                "advance_phase" in _items(phase.get("allowed_commands")),
                ["docs/en/02-factory-flow-and-hermes-architecture.md", "templates/factory-workflow-compiled-plan.json"],
                "Route the phase through Factory V2 commands/events instead of agent prose.",
            ),
            check(
                "no_idle_operator_ux_guard",
                bool(_items(phase.get("blocked_actions"))),
                [PROGRAM_REF, "templates/hermes-typed-block-policy.json"],
                "Declare blocked actions that prevent idle loops, false human pages or unsafe shortcuts.",
            ),
            check(
                "handoff_chain",
                bool(phase.get("next_phase_id")) or phase_id == terminal_phase_id,
                ["docs/factory-workflow.catalog.json", "templates/factory-workflow-compiled-plan.json"],
                "Declare next_phase_id or make the phase terminal.",
            ),
        ]
        gear_assessments.append(
            {
                "phase_id": phase_id,
                "phase_name": str(phase.get("phase_name") or "").strip(),
                "score": score(checks),
                "result": "PASS" if all(item["result"] == "PASS" for item in checks) else "FAIL",
                "checks": checks,
                "missing_worker_ids": missing_workers,
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
            }
        )

    dimensions = [
        check(
            "gear_contract",
            not plan_errors and bool(gear_assessments) and all(item["score"] >= 80 for item in gear_assessments),
            ["templates/factory-workflow-compiled-plan.json", GEAR_MATRIX_REF],
            "; ".join(plan_errors) if plan_errors else "Fix phase gear checks below 80.",
        ),
        check(
            "hermes_native_authority",
            policy_authority == "hermes_kanban",
            ["templates/hermes-typed-block-policy.json", "docs/en/02-factory-flow-and-hermes-architecture.md"],
            "Typed block policy must keep runtime_authority=hermes_kanban.",
        ),
        check(
            "autonomy_no_idle",
            "dependency" in native_kinds and bool(policy_rules.get("dependency", {}).get("auto_resume_expected")),
            ["templates/hermes-typed-block-policy.json"],
            "Dependency blocks must auto-resume through Hermes state, not operator nudges.",
        ),
        check(
            "operator_experience",
            bool(policy_rules.get("needs_input", {}).get("decision_package_required"))
            and bool(policy_rules.get("needs_input", {}).get("delivery_receipt_required")),
            ["templates/hermes-typed-block-policy.json", "templates/operator-delivery-receipt.json"],
            "Human pages must include a decision package and delivery receipt.",
        ),
        check(
            "worker_quality_floor",
            "product_sot_result" in factoryctl.WORKER_QUALITY_FLOOR_REQUIRED_DIMENSIONS,
            ["schemas/worker-result.schema.json", "scripts/factoryctl.py"],
            "Real reusable Product SOT PASS must have a quality_floor.",
        ),
        check(
            "block_classification",
            REQUIRED_BLOCK_KINDS.issubset(native_kinds),
            ["templates/hermes-typed-block-policy.json"],
            "Typed block policy must cover dependency, needs_input, capability and transient.",
        ),
        check(
            "security_boundary",
            any("security" in worker for worker in worker_ids) and any("supply-chain" in worker for worker in worker_ids),
            ["agents/worker-registry.public.json", "scripts/public_safety_scan.py", "scripts/secret_safety_scan.py"],
            "Security and supply-chain workers must remain registered and scans must stay green.",
        ),
        check(
            "performance_loop_control",
            bool(loop_policy) and int(loop_policy.get("recurrence_limit") or 0) > 0 and bool(loop_policy.get("escalation_event")),
            ["templates/hermes-typed-block-policy.json"],
            "Same-cause loop handling must have a recurrence limit and escalation event.",
        ),
    ]
    result = "PASS" if all(item["result"] == "PASS" for item in dimensions) and all(item["result"] == "PASS" for item in gear_assessments) else "FAIL"
    return {
        "$schema": "https://overkill-factory.dev/schemas/swiss-watch-audit.schema.json",
        "record_type": "swiss_watch_reliability_audit",
        "created_at": created,
        "result": result,
        "score": score(dimensions),
        "rule_zero": {
            "factory_must_not_become_mini_hermes": True,
            "prefer_hermes_native_primitives": ["kanban", "typed_blocks", "dependencies", "dispatch", "runtime_state"],
            "factory_native_code_only_when_hermes_lacks_primitive": True,
        },
        "dimensions": dimensions,
        "gear_assessments": gear_assessments,
        "summary": {
            "phase_count": len(gear_assessments),
            "failing_phase_count": sum(1 for item in gear_assessments if item["result"] != "PASS"),
            "native_block_kinds": sorted(native_kinds),
            "runtime_authority": policy_authority,
        },
    }


def validate_audit(audit: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if audit.get("record_type") != "swiss_watch_reliability_audit":
        errors.append("record_type must be swiss_watch_reliability_audit")
    if audit.get("result") not in {"PASS", "FAIL"}:
        errors.append("result must be PASS or FAIL")
    rule_zero = audit.get("rule_zero") if isinstance(audit.get("rule_zero"), dict) else {}
    if rule_zero.get("factory_must_not_become_mini_hermes") is not True:
        errors.append("rule_zero.factory_must_not_become_mini_hermes must be true")
    if "kanban" not in _items(rule_zero.get("prefer_hermes_native_primitives")):
        errors.append("rule_zero.prefer_hermes_native_primitives must include kanban")
    dimensions = audit.get("dimensions") if isinstance(audit.get("dimensions"), list) else []
    present = {str(item.get("check") or "") for item in dimensions if isinstance(item, dict)}
    for dimension in DIMENSIONS:
        if dimension not in present:
            errors.append(f"dimensions missing {dimension}")
    gears = audit.get("gear_assessments") if isinstance(audit.get("gear_assessments"), list) else []
    if not gears:
        errors.append("gear_assessments must be non-empty")
    for index, gear in enumerate(gears):
        if not isinstance(gear, dict):
            errors.append(f"gear_assessments[{index}] must be an object")
            continue
        if gear.get("runtime_authority") != "hermes_kanban":
            errors.append(f"gear_assessments[{index}].runtime_authority must be hermes_kanban")
        if gear.get("local_state_authority") is not False:
            errors.append(f"gear_assessments[{index}].local_state_authority must be false")
    if audit.get("result") == "PASS":
        bad_dimensions = [str(item.get("check")) for item in dimensions if isinstance(item, dict) and item.get("result") != "PASS"]
        bad_gears = [str(item.get("phase_id")) for item in gears if isinstance(item, dict) and item.get("result") != "PASS"]
        if bad_dimensions:
            errors.append("PASS audit cannot contain failing dimensions: " + ", ".join(bad_dimensions))
        if bad_gears:
            errors.append("PASS audit cannot contain failing gears: " + ", ".join(bad_gears))
    return errors


def markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Swiss Watch Reliability Audit",
        "",
        f"Result: `{audit.get('result')}`",
        f"Score: `{audit.get('score')}`",
        f"Created at: `{audit.get('created_at')}`",
        "",
        "## Rule Zero",
        "",
        "The factory must not become a mini-Hermes. It uses Hermes-native Kanban, typed blocks, dependencies, dispatch and runtime state first; factory-native code exists only where Hermes lacks a primitive.",
        "",
        "## Dimensions",
        "",
    ]
    for item in audit.get("dimensions", []):
        if isinstance(item, dict):
            lines.append(f"- `{item.get('result')}` {item.get('check')}: {', '.join(_items(item.get('evidence_refs')))}")
    lines.extend(["", "## Gear Assessments", ""])
    for gear in audit.get("gear_assessments", []):
        if isinstance(gear, dict):
            lines.append(f"- `{gear.get('result')}` {gear.get('phase_id')} {gear.get('phase_name')} - score `{gear.get('score')}`")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Swiss Watch reliability scorecard from Hermes-native factory contracts.")
    parser.add_argument("--compiled-plan", type=Path, default=ROOT / "templates" / "factory-workflow-compiled-plan.json")
    parser.add_argument("--typed-block-policy", type=Path, default=ROOT / "templates" / "hermes-typed-block-policy.json")
    parser.add_argument("--worker-registry", type=Path, default=ROOT / "agents" / "worker-registry.public.json")
    parser.add_argument("--created-at")
    parser.add_argument("--out", type=Path, default=ROOT / ".tmp" / "swiss-watch-audit.json")
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)

    audit = build_audit(
        factoryctl.load_json_like(args.compiled_plan),
        factoryctl.load_json_like(args.typed_block_policy),
        factoryctl.load_json_like(args.worker_registry),
        created_at=args.created_at,
    )
    errors = validate_audit(audit)
    factoryctl.write_json(args.out, audit)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(audit), encoding="utf-8")
        print(f"Wrote {factoryctl.public_path_ref(args.markdown)}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0 if audit["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
