#!/usr/bin/env python3
"""Validate the public Factory V2 runtime contract set.

This check is intentionally stricter than plain JSON Schema validation. The
schemas prove shape; this script proves that the V2 slices are wired together
as a runtime contract set and that the Hermes integration relies on native
Kanban primitives instead of a shadow dispatcher.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_public_json_artifacts import load_schemas, validate_node  # noqa: E402


CONTRACT_TEMPLATES = {
    "profile_aliases": "agents/profile-compatibility-aliases.public.json",
    "skill_registry": "agents/skill-provider-registry.public.json",
    "skill_resolution": "templates/skill-ref-resolution-report.json",
    "capability_run": "templates/capability-acquisition-run.json",
    "run_plan": "templates/factory-run-plan.json",
    "run_manifest": "templates/full-product-run-manifest.json",
    "surface_stack": "templates/product-surface-stack-plan.json",
    "vertical_slice_graph": "templates/vertical-slice-graph.json",
    "dispatch_readiness": "templates/work-unit-dispatch-readiness.json",
    "e2e_release_proof": "templates/product-e2e-release-proof.json",
    "qa_repair_loop": "templates/qa-repair-loop-state.json",
    "typed_block_policy": "templates/hermes-typed-block-policy.json",
    "blocked_first": "templates/hermes-blocked-first-protocol-receipt.json",
    "operator_delivery": "templates/operator-delivery-receipt.json",
    "operator_policy": "templates/operator-notification-policy.json",
    "operator_channel_pack": "templates/operator-channel-pack.json",
    "brand_strategy": "templates/brand-strategy.json",
    "identity_system": "templates/identity-system.json",
    "component_registry": "templates/component-registry.json",
    "accessibility_report": "templates/accessibility-report.json",
    "visual_regression": "templates/visual-regression-proof.json",
    "storybook_catalog": "templates/storybook-equivalent-catalog.json",
    "security_route": "templates/security-route-contract.json",
    "security_state": "templates/security-state-ledger.json",
    "capability_broker": "templates/capability-broker.json",
    "capability_lease": "templates/capability-lease.json",
    "security_profile": "templates/security-profile.json",
}

HERMES_NATIVE_PRIMITIVES = {
    "gateway start",
    "kanban dispatch",
    "kanban watch",
    "kanban tail",
    "kanban runs",
    "kanban diagnostics",
    "kanban notify-list",
    "kanban notify-unsubscribe",
}

HERMES_TYPED_BLOCK_KINDS = {"dependency", "needs_input", "capability", "transient"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def schema_name(schema_ref: str) -> str:
    return schema_ref.rsplit("/", 1)[-1]


def artifact_ref(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def validate_artifact(path: Path, schemas: dict[str, Any], root: Path = ROOT) -> list[str]:
    data = load_json(path)
    ref = str(data.get("$schema") or "")
    if not ref:
        return [f"{artifact_ref(path, root)}: missing $schema"]
    schema = schemas.get(schema_name(ref))
    if not isinstance(schema, dict):
        return [f"{artifact_ref(path, root)}: schema not found for {ref}"]
    return [
        f"{artifact_ref(path, root)}: {error}"
        for error in validate_node(schema, data, "$", schemas=schemas, root_schema=schema)
    ]


def text_set(items: Any) -> set[str]:
    if not isinstance(items, list):
        return set()
    return {str(item).strip() for item in items if str(item).strip()}


def validate_runtime_contract_set(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    schemas = load_schemas()
    payloads: dict[str, dict[str, Any]] = {}

    for key, rel in CONTRACT_TEMPLATES.items():
        path = root / rel
        if not path.exists():
            errors.append(f"{rel}: missing V2 runtime contract template")
            continue
        errors.extend(validate_artifact(path, schemas, root))
        if not errors:
            payloads[key] = load_json(path)
        else:
            try:
                payloads[key] = load_json(path)
            except (OSError, ValueError, json.JSONDecodeError):
                pass

    run_plan = payloads.get("run_plan", {})
    manifest = payloads.get("run_manifest", {})
    dispatch = payloads.get("dispatch_readiness", {})
    blocked_first = payloads.get("blocked_first", {})
    typed_block_policy = payloads.get("typed_block_policy", {})
    operator_policy = payloads.get("operator_policy", {})
    operator_delivery = payloads.get("operator_delivery", {})
    capability_run = payloads.get("capability_run", {})

    plan_phases = [
        str(item.get("phase_id") or "")
        for item in run_plan.get("phases", [])
        if isinstance(item, dict)
    ]
    if len(plan_phases) < 8 or plan_phases != sorted(plan_phases, key=lambda item: int(item[1:]) if item[1:].isdigit() else 999):
        errors.append("factory-run-plan: phases must be an ordered F0..Fn runtime spine")
    if "F13" not in plan_phases or "F15" not in plan_phases:
        errors.append("factory-run-plan: must include dispatch and verification phases F13/F15")

    manifest_plan_ref = str(manifest.get("run_plan_ref") or "")
    if manifest_plan_ref != "templates/factory-run-plan.json":
        errors.append("full-product-run-manifest.run_plan_ref must point to templates/factory-run-plan.json")

    ready_units = [
        item for item in dispatch.get("work_units", []) if isinstance(item, dict) and item.get("dispatch_decision") == "ready"
    ]
    if not ready_units:
        errors.append("work-unit-dispatch-readiness: at least one ready work unit fixture is required")
    for index, unit in enumerate(ready_units):
        if unit.get("dependencies_satisfied") is not True:
            errors.append(f"work-unit-dispatch-readiness.work_units[{index}]: ready requires dependencies_satisfied=true")
        if not unit.get("hermes_task_plan_ref"):
            errors.append(f"work-unit-dispatch-readiness.work_units[{index}]: ready requires hermes_task_plan_ref")

    native = text_set(blocked_first.get("hermes_native_primitives_required"))
    missing_native = sorted(HERMES_NATIVE_PRIMITIVES - native)
    if missing_native:
        errors.append("hermes-blocked-first-protocol-receipt missing native primitives: " + ", ".join(missing_native))
    if blocked_first.get("shadow_dispatcher_allowed") is not False:
        errors.append("hermes-blocked-first-protocol-receipt.shadow_dispatcher_allowed must be false")
    if blocked_first.get("typed_block_policy_ref") != "templates/hermes-typed-block-policy.json":
        errors.append("hermes-blocked-first-protocol-receipt must point to templates/hermes-typed-block-policy.json")
    embedded_typed_block_policy = blocked_first.get("typed_block_policy") if isinstance(blocked_first.get("typed_block_policy"), dict) else {}
    native_block_kinds = text_set(embedded_typed_block_policy.get("native_block_kinds_required"))
    missing_block_kinds = sorted(HERMES_TYPED_BLOCK_KINDS - native_block_kinds)
    if missing_block_kinds:
        errors.append("hermes-blocked-first-protocol-receipt missing typed block kinds: " + ", ".join(missing_block_kinds))
    if embedded_typed_block_policy.get("untyped_block_forbidden") is not True:
        errors.append("hermes-blocked-first-protocol-receipt.typed_block_policy.untyped_block_forbidden must be true")
    if embedded_typed_block_policy.get("default_runtime_gate_kind") != "transient":
        errors.append("hermes-blocked-first-protocol-receipt default runtime gate block kind must be transient")
    dependency_policy = embedded_typed_block_policy.get("dependency_block_behavior") if isinstance(embedded_typed_block_policy.get("dependency_block_behavior"), dict) else {}
    if dependency_policy.get("operator_page_allowed") is not False or dependency_policy.get("auto_resume_expected") is not True:
        errors.append("dependency typed blocks must not page the operator and must auto-resume")
    needs_input_policy = embedded_typed_block_policy.get("needs_input_block_behavior") if isinstance(embedded_typed_block_policy.get("needs_input_block_behavior"), dict) else {}
    if needs_input_policy.get("operator_page_allowed") is not False:
        errors.append("needs_input typed blocks must not page the operator directly")
    if needs_input_policy.get("manager_report_required") is not True:
        errors.append("needs_input typed blocks require a manager report")
    if needs_input_policy.get("operator_delivery_receipt_required") is not True:
        errors.append("needs_input typed blocks require operator delivery receipt before asking for a decision")
    capability_policy = embedded_typed_block_policy.get("capability_block_behavior") if isinstance(embedded_typed_block_policy.get("capability_block_behavior"), dict) else {}
    if capability_policy.get("capability_acquisition_run_required") is not True or capability_policy.get("search_completed_required") is not True:
        errors.append("capability typed blocks require completed capability acquisition before blocking")
    if embedded_typed_block_policy.get("recurrence_limit") != 2:
        errors.append("hermes typed block recurrence_limit must match Hermes BLOCK_RECURRENCE_LIMIT=2")
    if embedded_typed_block_policy.get("loop_event_required") != "block_loop_detected":
        errors.append("hermes typed block policy must require block_loop_detected event handling")
    if embedded_typed_block_policy.get("dependency_wait_event_required") != "dependency_wait":
        errors.append("hermes typed block policy must require dependency_wait event handling")
    policy_kinds = text_set(typed_block_policy.get("native_block_kinds"))
    if HERMES_TYPED_BLOCK_KINDS - policy_kinds:
        errors.append("hermes-typed-block-policy must declare every native Hermes block kind")
    kind_rules = typed_block_policy.get("kind_rules") if isinstance(typed_block_policy.get("kind_rules"), dict) else {}
    dependency_rule = kind_rules.get("dependency") if isinstance(kind_rules.get("dependency"), dict) else {}
    if dependency_rule.get("route") != "todo" or dependency_rule.get("operator_page_allowed") is not False:
        errors.append("hermes-typed-block-policy dependency rule must route to todo and never page operator")
    needs_input_rule = kind_rules.get("needs_input") if isinstance(kind_rules.get("needs_input"), dict) else {}
    if needs_input_rule.get("delivery_receipt_required") is not True:
        errors.append("hermes-typed-block-policy needs_input rule must require delivery receipt")
    loop_policy = typed_block_policy.get("same_cause_loop_policy") if isinstance(typed_block_policy.get("same_cause_loop_policy"), dict) else {}
    if loop_policy.get("recurrence_limit") != 2 or loop_policy.get("escalation_event") != "block_loop_detected":
        errors.append("hermes-typed-block-policy loop policy must use recurrence_limit=2 and block_loop_detected")

    if operator_policy.get("human_gate_delivery_requires_receipt") is not True:
        errors.append("operator-notification-policy requires human_gate_delivery_requires_receipt=true")
    if operator_delivery.get("material_delivered_before_question") is not True:
        errors.append("operator-delivery-receipt requires material_delivered_before_question=true")
    if str(operator_delivery.get("primary_language") or "") != "pt-BR":
        errors.append("operator-delivery-receipt primary_language must be pt-BR for the default operator path")

    if capability_run.get("block_allowed") is True and capability_run.get("search_completed") is not True:
        errors.append("capability-acquisition-run cannot block before search_completed=true")
    if capability_run.get("activation_decision") == "activate" and capability_run.get("smoke_result") != "PASS":
        errors.append("capability-acquisition-run activation requires smoke_result PASS")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    errors = validate_runtime_contract_set(args.root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
