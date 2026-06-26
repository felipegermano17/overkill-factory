#!/usr/bin/env python3
"""Validate public JSON artifacts against bundled lightweight schemas.

This intentionally avoids third-party dependencies so CI can run on a clean
Python install. It supports the schema features used by this repository and
fails closed when a public schema introduces a validation keyword this local
validator cannot enforce.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from public_refs import contains_private_kanban_task_marker  # noqa: E402
from factory_route_registry import (  # noqa: E402
    route_method_families,
    route_request_types,
    route_required_artifacts,
    route_required_workers,
    route_signal_types,
)
from factory_method_engines import validate_method_engine_registry_semantics  # noqa: E402
from factory_operating_systems import (  # noqa: E402
    validate_operating_system_registry_semantics,
    validate_operating_system_scorecard_semantics,
)

SCHEMA_DIR = ROOT / "schemas"
PUBLIC_SCHEMA_DIRS = [
    SCHEMA_DIR,
    ROOT / "agents",
    ROOT / "docs",
    ROOT / "examples",
    ROOT / "planning-bundles",
    ROOT / "fixtures" / "product-validation",
    ROOT / "templates",
]
SCAN_DIRS = [
    ROOT / "examples",
    ROOT / "agents",
    ROOT / "templates",
    ROOT / "docs",
    ROOT / "planning-bundles",
    ROOT / "fixtures" / "product-validation",
]
RUNTIME_LOCAL_JSON_DIRS = [
    ROOT / ".tmp" / "factory-runs" / "operator-inbox",
]
RUNTIME_LOCAL_JSON_PATHS = {
    ROOT / ".tmp" / "factory-runs" / "no-idle-watchdog-state.json",
}

SCHEMA_OPTIONAL = {
    ".tmp/factory-runs/product-face/console.json",
    ".tmp/factory-runs/product-face/state.json",
    ".tmp/factory-runs/product-face/static-summary.json",
    ".tmp/factory-runs/security/bandit-scripts-adapters.json",
}

PRODUCT_FACE_ALIGNMENT_FIELDS = (
    "packet_comparison",
    "source_promise_coverage",
    "design_fit_review",
    "project_design_system_comparison",
    "professional_design_process_comparison",
    "reference_quality_comparison",
)
REFERENCE_RESEARCH_SOURCE_TYPES = {
    "component_registry",
    "design_library",
    "design_system",
    "product_reference",
    "site_gallery",
    "user_flow_library",
}
REFERENCE_RESEARCH_LIBRARY_TYPES = {
    "component_registry",
    "design_library",
    "site_gallery",
    "user_flow_library",
}
REFERENCE_COMPARISON_DIMENSIONS = (
    "layout_hierarchy",
    "interaction_model",
    "state_coverage",
    "visual_language",
    "density_spacing",
)
PROFESSIONAL_DESIGN_GATE_ALLOWED_STATUSES = {"PASS", "BLOCKED", "NEEDS_REWORK", "PENDING"}
PROFESSIONAL_DESIGN_GATE_BLOCKING_STATUSES = {"BLOCKED", "NEEDS_REWORK", "PENDING"}
PROFESSIONAL_DESIGN_BLOCKER_FIELDS = ("blocker_id", "owner", "next_action", "basis")
PRIVATE_USERS_PATH = "C:" + r"[\\/]+" + "Users"
PRIVATE_SYNC_ROOT = "One" + "Drive"
PRIVATE_MARKERS = re.compile(
    PRIVATE_USERS_PATH + r"|" + PRIVATE_SYNC_ROOT + r"|guild_ref|channel_ref|thread_id|message_id",
    re.IGNORECASE,
)
SENSITIVE_LEARNING_ARTIFACTS = {"worker", "gate", "hook", "mcp_or_tool", "install_profile"}
RESEARCH_RECORD_TYPES = {
    "specialist_research_plan",
    "specialist_decision_packet",
    "product_context_packet",
    "product_creation_plan",
    "product_implementation_readiness",
    "project_design_system",
}
RAW_RESEARCH_FIELDS = {
    "raw_notes",
    "paper_dump",
    "source_dump",
    "screenshot_path",
    "conversation_history",
    "local_capture_path",
    "private_capture_path",
}
AUTOMATION_GITHUB_AUTHORITIES = {"github_pr", "release_candidate", "production_operation"}
AUTOMATION_REPO_BOUND_AUTHORITIES = {"bounded_edit", "local_commit", "github_pr", "release_candidate", "production_operation"}
AUTOMATION_REPO_BOUND_TARGETS = {"repo", "factory_issue", "release"}
AUTOMATION_REQUIRED_SAFETY_CHECKS = {"public_safety_scan", "secret_safety_scan"}
FACTORY_READINESS_SCORECARD_DIMENSIONS = {
    "build_install_health",
    "test_coverage_determinism",
    "lint_static_checks",
    "docs_onboarding_first_run",
    "task_discovery_issue_quality",
    "worker_profile_capability_readiness",
    "evidence_public_private_hygiene",
    "observability_incident_rollback",
    "security_secrets_supply_chain",
    "product_analytics_success_signals",
    "autonomy_risk_human_gates",
}
V1_COMPLETION_BLOCKING_STATUSES = {"BLOCKED", "MISSING", "FAIL", "UNKNOWN"}
V1_COMPLETION_FINDING_DESTINATIONS = {"v1_blocker", "vnext", "not_planned"}
UNIVERSAL_SIGNAL_ROUTE_REQUIRED_ARTIFACTS = route_required_artifacts()
UNIVERSAL_SIGNAL_ROUTE_REQUEST_TYPES = route_request_types()
UNIVERSAL_SIGNAL_ROUTE_SIGNAL_TYPES = route_signal_types()
UNIVERSAL_SIGNAL_ROUTE_METHOD_FAMILIES = route_method_families()


def public_worker_ids() -> set[str]:
    path = ROOT / "agents" / "worker-registry.public.json"
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    workers = data.get("workers") if isinstance(data.get("workers"), list) else []
    return {
        str(worker.get("worker_id") or "").strip()
        for worker in workers
        if isinstance(worker, dict) and str(worker.get("worker_id") or "").strip()
    }


def public_artifact_ref_error(ref: Any) -> str | None:
    value = str(ref or "").strip()
    normalized = value.replace("\\", "/")
    if not value:
        return "empty artifact ref"
    if contains_private_kanban_task_marker(value):
        return "raw Hermes Kanban task id"
    if PRIVATE_MARKERS.search(value):
        return "private local or runtime marker"
    if value.startswith("external:"):
        trusted_prefixes = (
            "external:sanitized",
            "external:operator",
            "external:public",
            "external:maintainer",
            "external:source-card",
            "external:memory",
        )
        if value.startswith(trusted_prefixes):
            return None
        return "untrusted external ref"
    if value.startswith(("http://", "https://", "file://")):
        return "absolute, URL, or private runtime ref"
    if Path(value).is_absolute() or ":" in normalized.split("/", 1)[0]:
        return "absolute, URL, or private runtime ref"
    if normalized.startswith((".tmp/", "tmp/", "reports/private/", "private/", "run-evidence/")) or "/.tmp/" in normalized:
        return "private or transient evidence location"
    return None


def text_items(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalized_check_ids(value: Any) -> set[str]:
    return {item.lower() for item in text_items(value)}


def passed_check_ids(checks: Any, *, phase: str | None = None) -> set[str]:
    if not isinstance(checks, list):
        return set()
    passed: set[str] = set()
    for check in checks:
        if not isinstance(check, dict):
            continue
        if phase is not None and str(check.get("phase") or "").strip().lower() != phase:
            continue
        if str(check.get("status") or "").strip().upper() == "PASS":
            passed.add(str(check.get("check_id") or "").strip().lower())
    return passed


def add_public_ref_errors(refs: Any, at: str, errors: list[str]) -> None:
    for index, ref in enumerate(text_items(refs)):
        reason = public_artifact_ref_error(ref)
        if reason:
            errors.append(f"{at}[{index}]: {reason}")


def validate_factory_readiness_scorecard_domain(data: dict[str, Any], at: str) -> list[str]:
    errors: list[str] = []
    target = data.get("target") if isinstance(data.get("target"), dict) else {}
    for field, ref in (
        ("target.target_ref", target.get("target_ref")),
        ("linked_feedback_loop_ref", data.get("linked_feedback_loop_ref")),
    ):
        if ref:
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.{field}: {reason}")

    remediation_loop = data.get("remediation_loop") if isinstance(data.get("remediation_loop"), dict) else {}
    if remediation_loop.get("loop_ref"):
        reason = public_artifact_ref_error(remediation_loop.get("loop_ref"))
        if reason:
            errors.append(f"{at}.remediation_loop.loop_ref: {reason}")

    dimensions = data.get("dimensions") if isinstance(data.get("dimensions"), list) else []
    seen: set[str] = set()
    duplicate_dimensions: set[str] = set()
    non_pass_statuses: set[str] = set()
    blocked_dimensions: set[str] = set()
    remediation_dimensions: set[str] = set()
    bounded_dimensions: set[str] = set()

    for dimension_index, dimension in enumerate(dimensions):
        if not isinstance(dimension, dict):
            continue
        dimension_id = str(dimension.get("dimension_id") or "").strip()
        if dimension_id in seen:
            duplicate_dimensions.add(dimension_id)
        seen.add(dimension_id)

        for ref_index, ref in enumerate(text_items(dimension.get("evidence_refs"))):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.dimensions[{dimension_index}].evidence_refs[{ref_index}]: {reason}")
        remediation_target_ref = str(dimension.get("remediation_target_ref") or "").strip()
        if remediation_target_ref:
            reason = public_artifact_ref_error(remediation_target_ref)
            if reason:
                errors.append(f"{at}.dimensions[{dimension_index}].remediation_target_ref: {reason}")

        status = str(dimension.get("status") or "").strip().upper()
        severity = str(dimension.get("severity") or "").strip()
        blocks = dimension.get("blocks_autonomous_execution") is True
        if status != "PASS":
            non_pass_statuses.add(dimension_id)
        if status == "REMEDIATION_REQUIRED":
            remediation_dimensions.add(dimension_id)
        if status == "BOUNDED":
            bounded_dimensions.add(dimension_id)
        if status == "BLOCKED" or blocks:
            blocked_dimensions.add(dimension_id)

        if status == "PASS":
            if severity != "none":
                errors.append(f"{at}.dimensions[{dimension_index}]: PASS requires severity=none")
            if blocks:
                errors.append(f"{at}.dimensions[{dimension_index}]: PASS cannot block autonomous execution")
            if remediation_target_ref != "not_required":
                errors.append(f"{at}.dimensions[{dimension_index}]: PASS requires remediation_target_ref=not_required")
        elif severity == "none":
            errors.append(f"{at}.dimensions[{dimension_index}]: non-PASS status requires non-none severity")
        elif remediation_target_ref == "not_required":
            errors.append(f"{at}.dimensions[{dimension_index}]: non-PASS status requires remediation target")

        if status == "BLOCKED" and not blocks:
            errors.append(f"{at}.dimensions[{dimension_index}]: BLOCKED status must block autonomous execution")
        if blocks and status != "BLOCKED":
            errors.append(f"{at}.dimensions[{dimension_index}]: blocking dimension must use BLOCKED status")

    for dimension_id in sorted(FACTORY_READINESS_SCORECARD_DIMENSIONS - seen):
        errors.append(f"{at}: factory_readiness_scorecard missing required dimension {dimension_id}")
    for dimension_id in sorted(seen - FACTORY_READINESS_SCORECARD_DIMENSIONS):
        errors.append(f"{at}: factory_readiness_scorecard unknown dimension {dimension_id}")
    for dimension_id in sorted(duplicate_dimensions):
        errors.append(f"{at}: factory_readiness_scorecard duplicate dimension {dimension_id}")

    verdict = str(data.get("verdict") or "").strip()
    autonomy = data.get("autonomy_boundary") if isinstance(data.get("autonomy_boundary"), dict) else {}
    allowed_scope = str(autonomy.get("allowed_scope") or "").strip()
    autonomy_allowed = autonomy.get("autonomous_execution_allowed") is True
    bounded_remediation_allowed = autonomy.get("bounded_remediation_allowed") is True
    material_autonomy_allowed = autonomy.get("material_autonomous_execution_allowed") is True
    remediation_required = remediation_loop.get("required") is True

    if non_pass_statuses and not remediation_required:
        errors.append(f"{at}: factory_readiness_scorecard non-PASS dimensions require remediation_loop.required=true")
    if blocked_dimensions:
        if verdict != "blocked":
            errors.append(f"{at}: factory_readiness_scorecard blocking dimensions require verdict=blocked")
        if autonomy_allowed:
            errors.append(f"{at}: factory_readiness_scorecard blocked verdict cannot allow autonomous execution")
        if allowed_scope != "none":
            errors.append(f"{at}: factory_readiness_scorecard blocked verdict requires allowed_scope=none")
    if verdict == "blocked" and not blocked_dimensions:
        errors.append(f"{at}: factory_readiness_scorecard verdict=blocked requires at least one blocking dimension")
    if verdict == "ready_for_autonomy":
        if non_pass_statuses:
            errors.append(f"{at}: factory_readiness_scorecard ready_for_autonomy requires all dimensions PASS")
        if not autonomy_allowed:
            errors.append(f"{at}: factory_readiness_scorecard ready_for_autonomy requires autonomous_execution_allowed=true")
        if not material_autonomy_allowed:
            errors.append(f"{at}: factory_readiness_scorecard ready_for_autonomy requires material_autonomous_execution_allowed=true")
        if allowed_scope != "material_execution":
            errors.append(f"{at}: factory_readiness_scorecard ready_for_autonomy requires allowed_scope=material_execution")
    if verdict == "ready_with_bounds":
        if blocked_dimensions:
            errors.append(f"{at}: factory_readiness_scorecard ready_with_bounds cannot include blocking dimensions")
        if not autonomy_allowed:
            errors.append(f"{at}: factory_readiness_scorecard ready_with_bounds requires autonomous_execution_allowed=true")
        if allowed_scope == "none":
            errors.append(f"{at}: factory_readiness_scorecard ready_with_bounds requires a non-none allowed_scope")
        if remediation_dimensions:
            if material_autonomy_allowed:
                errors.append(
                    f"{at}: factory_readiness_scorecard ready_with_bounds with remediation cannot allow material autonomous execution"
                )
            if allowed_scope == "material_execution":
                errors.append(
                    f"{at}: factory_readiness_scorecard ready_with_bounds with remediation cannot use allowed_scope=material_execution"
                )
            if not bounded_remediation_allowed:
                errors.append(
                    f"{at}: factory_readiness_scorecard ready_with_bounds with remediation requires bounded_remediation_allowed=true"
                )
    if verdict == "remediation_required":
        if not remediation_required:
            errors.append(f"{at}: factory_readiness_scorecard remediation_required requires remediation_loop.required=true")
        if not (remediation_dimensions or bounded_dimensions):
            errors.append(f"{at}: factory_readiness_scorecard remediation_required requires at least one non-PASS dimension")
        if allowed_scope == "material_execution":
            errors.append(f"{at}: factory_readiness_scorecard remediation_required cannot allow material_execution")
        if material_autonomy_allowed:
            errors.append(f"{at}: factory_readiness_scorecard remediation_required cannot allow material autonomous execution")

    public_boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
    if public_boundary.get("public_safe_refs_only") is not True:
        errors.append(f"{at}: factory_readiness_scorecard requires public_safe_refs_only=true")
    if public_boundary.get("raw_private_evidence_embedded") is not False:
        errors.append(f"{at}: factory_readiness_scorecard must not embed raw private evidence")
    if public_boundary.get("private_runtime_evidence_stays_local") is not True:
        errors.append(f"{at}: factory_readiness_scorecard private runtime evidence must stay local")
    if autonomy.get("not_product_acceptance") is not True:
        errors.append(f"{at}: factory_readiness_scorecard is not product acceptance")
    if autonomy.get("not_release_approval") is not True:
        errors.append(f"{at}: factory_readiness_scorecard is not release approval")

    return errors


def validate_factory_v1_completion_gate_domain(data: dict[str, Any], at: str) -> list[str]:
    errors: list[str] = []
    target = data.get("target") if isinstance(data.get("target"), dict) else {}
    reason = public_artifact_ref_error(target.get("target_ref"))
    if reason:
        errors.append(f"{at}.target.target_ref: {reason}")

    route_coverage = data.get("route_coverage") if isinstance(data.get("route_coverage"), dict) else {}
    for field in ("registry_ref", "corpus_ref", "scorecard_ref"):
        reason = public_artifact_ref_error(route_coverage.get(field))
        if reason:
            errors.append(f"{at}.route_coverage.{field}: {reason}")

    expected_routes = set(UNIVERSAL_SIGNAL_ROUTE_REQUIRED_ARTIFACTS)
    representative_signals = data.get("representative_signals") if isinstance(data.get("representative_signals"), list) else []
    represented_routes = {
        str(item.get("route_class") or "").strip()
        for item in representative_signals
        if isinstance(item, dict)
    }
    if data.get("decision") == "PASS":
        missing_routes = sorted(expected_routes - represented_routes)
        extra_routes = sorted(represented_routes - expected_routes)
        if missing_routes:
            errors.append(f"{at}: PASS missing representative route classes: {', '.join(missing_routes)}")
        if extra_routes:
            errors.append(f"{at}: PASS has unknown representative route classes: {', '.join(extra_routes)}")

    for index, item in enumerate(representative_signals):
        if not isinstance(item, dict):
            continue
        reason = public_artifact_ref_error(item.get("covered_by_ref"))
        if reason:
            errors.append(f"{at}.representative_signals[{index}].covered_by_ref: {reason}")

    blocking_evidence: list[str] = []
    evidence_items = data.get("required_evidence") if isinstance(data.get("required_evidence"), list) else []
    for index, item in enumerate(evidence_items):
        if not isinstance(item, dict):
            continue
        reason = public_artifact_ref_error(item.get("evidence_ref"))
        if reason:
            errors.append(f"{at}.required_evidence[{index}].evidence_ref: {reason}")
        status = str(item.get("status") or "").strip().upper()
        if item.get("blocks_v1_when_missing") is True and status in V1_COMPLETION_BLOCKING_STATUSES:
            blocking_evidence.append(str(item.get("evidence_id") or f"required_evidence[{index}]"))

    blocking_gates: list[str] = []
    gates = data.get("gates") if isinstance(data.get("gates"), list) else []
    for index, gate in enumerate(gates):
        if not isinstance(gate, dict):
            continue
        for ref_index, ref in enumerate(text_items(gate.get("evidence_refs"))):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.gates[{index}].evidence_refs[{ref_index}]: {reason}")
        status = str(gate.get("status") or "").strip().upper()
        if gate.get("blocks_v1") is True and status in V1_COMPLETION_BLOCKING_STATUSES:
            blocking_gates.append(str(gate.get("gate_id") or f"gates[{index}]"))

    open_v1_findings: list[str] = []
    findings = data.get("classified_findings") if isinstance(data.get("classified_findings"), list) else []
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            continue
        classification = str(finding.get("classification") or "").strip()
        status = str(finding.get("status") or "").strip()
        if classification not in V1_COMPLETION_FINDING_DESTINATIONS:
            errors.append(f"{at}.classified_findings[{index}]: unknown classification")
        if classification == "v1_blocker" and status not in {"resolved", "closed", "rejected"}:
            open_v1_findings.append(str(finding.get("finding_id") or f"classified_findings[{index}]"))
        for ref_index, ref in enumerate(text_items(finding.get("evidence_refs"))):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.classified_findings[{index}].evidence_refs[{ref_index}]: {reason}")

    policy = data.get("finding_policy") if isinstance(data.get("finding_policy"), dict) else {}
    if policy.get("no_open_ended_audit") is not True:
        errors.append(f"{at}: finding policy must forbid open-ended audit")
    if policy.get("new_findings_must_be_classified") is not True:
        errors.append(f"{at}: new findings must be classified")
    destinations = set(text_items(policy.get("accepted_destinations")))
    if destinations != V1_COMPLETION_FINDING_DESTINATIONS:
        errors.append(f"{at}: accepted destinations must be v1_blocker, vnext and not_planned")

    boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
    if boundary.get("public_safe_refs_only") is not True:
        errors.append(f"{at}: requires public_safe_refs_only=true")
    if boundary.get("raw_private_evidence_embedded") is not False:
        errors.append(f"{at}: must not embed raw private evidence")
    if boundary.get("private_runtime_evidence_stays_local") is not True:
        errors.append(f"{at}: private runtime evidence must stay local")

    decision = str(data.get("decision") or "").strip()
    completion_allowed = data.get("completion_claim_allowed") is True
    scope = data.get("completion_claim_scope") if isinstance(data.get("completion_claim_scope"), dict) else {}
    if decision == "PASS":
        if blocking_evidence:
            errors.append(f"{at}: PASS has blocking evidence: {', '.join(sorted(blocking_evidence))}")
        if blocking_gates:
            errors.append(f"{at}: PASS has blocking gates: {', '.join(sorted(blocking_gates))}")
        if open_v1_findings:
            errors.append(f"{at}: PASS has open v1 blockers: {', '.join(sorted(open_v1_findings))}")
        if not completion_allowed:
            errors.append(f"{at}: PASS requires completion_claim_allowed=true")
        if scope.get("factory_v1_public_kernel") is not True:
            errors.append(f"{at}: PASS requires factory_v1_public_kernel=true")
    if decision == "BLOCKED":
        if completion_allowed:
            errors.append(f"{at}: BLOCKED cannot allow completion claim")
        if scope.get("factory_v1_public_kernel") is not False:
            errors.append(f"{at}: BLOCKED requires factory_v1_public_kernel=false")
    for field in ("product_specific_completion", "universal_runtime_proof", "hosted_service_release"):
        if scope.get(field) is not False:
            errors.append(f"{at}: cannot claim {field}")

    return errors


ANNOTATION_SCHEMA_KEYWORDS = {
    "$comment",
    "$id",
    "$schema",
    "default",
    "description",
    "examples",
    "title",
}
SUPPORTED_SCHEMA_KEYWORDS = ANNOTATION_SCHEMA_KEYWORDS | {
    "$defs",
    "$ref",
    "additionalProperties",
    "allOf",
    "const",
    "contains",
    "else",
    "enum",
    "if",
    "items",
    "maxContains",
    "maximum",
    "maxItems",
    "maxLength",
    "minContains",
    "minimum",
    "minItems",
    "minLength",
    "minProperties",
    "oneOf",
    "pattern",
    "properties",
    "required",
    "then",
    "type",
    "uniqueItems",
}
SCHEMA_MAP_CHILDREN = {"$defs", "properties"}
SCHEMA_OBJECT_CHILDREN = {"additionalProperties", "contains", "else", "if", "items", "then"}
SCHEMA_ARRAY_CHILDREN = {"allOf", "oneOf"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_name(schema_ref: str) -> str:
    return schema_ref.rsplit("/", 1)[-1]


def iter_schema_files() -> list[Path]:
    paths: set[Path] = set()
    for directory in PUBLIC_SCHEMA_DIRS:
        if not directory.exists():
            continue
        if directory == SCHEMA_DIR:
            paths.update(directory.glob("*.json"))
        else:
            paths.update(directory.rglob("*.schema.json"))
    return sorted(paths)


def load_schemas() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for path in iter_schema_files():
        schema = load_json(path)
        schema_id = str(schema.get("$id") or "")
        schemas[path.name] = schema
        if schema_id:
            schemas[schema_name(schema_id)] = schema
    return schemas


def schema_path(parent: str, key: str | int) -> str:
    return f"{parent}/{str(key).replace('~', '~0').replace('/', '~1')}"


def validate_schema_keywords(schema: dict[str, Any], at: str = "$") -> list[str]:
    errors: list[str] = []
    for key, value in schema.items():
        if key not in SUPPORTED_SCHEMA_KEYWORDS:
            errors.append(f"{at}: unsupported JSON Schema keyword {key!r}")
            continue
        if key in SCHEMA_MAP_CHILDREN and isinstance(value, dict):
            for child_key, child_schema in value.items():
                if isinstance(child_schema, dict):
                    child_path = schema_path(schema_path(at, key), child_key)
                    errors.extend(validate_schema_keywords(child_schema, child_path))
        elif key in SCHEMA_OBJECT_CHILDREN and isinstance(value, dict):
            errors.extend(validate_schema_keywords(value, schema_path(at, key)))
        elif key in SCHEMA_ARRAY_CHILDREN and isinstance(value, list):
            for index, child_schema in enumerate(value):
                if isinstance(child_schema, dict):
                    errors.extend(validate_schema_keywords(child_schema, schema_path(schema_path(at, key), index)))
    return errors


def type_matches(expected: str | list[str], value: Any) -> bool:
    expected_types = [expected] if isinstance(expected, str) else expected
    for expected_type in expected_types:
        if expected_type == "object" and isinstance(value, dict):
            return True
        if expected_type == "array" and isinstance(value, list):
            return True
        if expected_type == "string" and isinstance(value, str):
            return True
        if expected_type == "boolean" and isinstance(value, bool):
            return True
        if expected_type == "null" and value is None:
            return True
        if expected_type == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if expected_type == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
    return False


def resolve_json_pointer(document: dict[str, Any], pointer: str) -> dict[str, Any] | None:
    if not pointer.startswith("#/"):
        return None
    current: Any = document
    for raw_part in pointer[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current if isinstance(current, dict) else None


def resolve_ref(ref: str, schemas: dict[str, dict[str, Any]] | None, root_schema: dict[str, Any]) -> dict[str, Any] | None:
    if ref.startswith("#/"):
        return resolve_json_pointer(root_schema, ref)
    if "#" in ref:
        schema_ref, pointer = ref.split("#", 1)
        target = schemas.get(schema_name(schema_ref)) if schemas else None
        if target is not None and pointer.startswith("/"):
            return resolve_json_pointer(target, f"#{pointer}")
        return target
    return schemas.get(schema_name(ref)) if schemas else None


def schema_matches(
    schema: dict[str, Any],
    value: Any,
    at: str,
    schemas: dict[str, dict[str, Any]] | None = None,
    root_schema: dict[str, Any] | None = None,
    seen_refs: set[str] | None = None,
) -> bool:
    return not validate_node(schema, value, at, schemas=schemas, root_schema=root_schema, seen_refs=seen_refs)


def validate_node(
    schema: dict[str, Any],
    value: Any,
    at: str,
    *,
    schemas: dict[str, dict[str, Any]] | None = None,
    root_schema: dict[str, Any] | None = None,
    seen_refs: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    root = root_schema or schema
    seen = seen_refs or set()
    ref = schema.get("$ref")
    if isinstance(ref, str):
        if ref in seen:
            errors.append(f"{at}: recursive $ref {ref!r} is not supported")
            return errors
        target = resolve_ref(ref, schemas, root)
        if target is None:
            errors.append(f"{at}: unresolved $ref {ref!r}")
            return errors
        errors.extend(validate_node(target, value, at, schemas=schemas, root_schema=target, seen_refs=seen | {ref}))
    if isinstance(schema.get("allOf"), list):
        for index, subschema in enumerate(schema["allOf"]):
            if isinstance(subschema, dict):
                errors.extend(validate_node(subschema, value, f"{at}.allOf[{index}]", schemas=schemas, root_schema=root, seen_refs=seen))
    if isinstance(schema.get("oneOf"), list):
        match_count = 0
        for subschema in schema["oneOf"]:
            if isinstance(subschema, dict) and schema_matches(
                subschema,
                value,
                at,
                schemas=schemas,
                root_schema=root,
                seen_refs=seen,
            ):
                match_count += 1
        if match_count != 1:
            errors.append(f"{at}: expected exactly one oneOf schema match, got {match_count}")
    if "if" in schema and isinstance(schema["if"], dict):
        if schema_matches(schema["if"], value, at, schemas=schemas, root_schema=root, seen_refs=seen):
            then_schema = schema.get("then")
            if isinstance(then_schema, dict):
                errors.extend(validate_node(then_schema, value, at, schemas=schemas, root_schema=root, seen_refs=seen))
        else:
            else_schema = schema.get("else")
            if isinstance(else_schema, dict):
                errors.extend(validate_node(else_schema, value, at, schemas=schemas, root_schema=root, seen_refs=seen))
    if "type" in schema and not type_matches(schema["type"], value):
        errors.append(f"{at}: expected type {schema['type']}")
        return errors
    if "const" in schema and value != schema["const"]:
        errors.append(f"{at}: expected const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{at}: value {value!r} not in enum")
    if isinstance(value, str) and "minLength" in schema and len(value) < int(schema["minLength"]):
        errors.append(f"{at}: string shorter than minLength {schema['minLength']}")
    if isinstance(value, str) and "maxLength" in schema and len(value) > int(schema["maxLength"]):
        errors.append(f"{at}: string longer than maxLength {schema['maxLength']}")
    if isinstance(value, str) and "pattern" in schema and not re.search(str(schema["pattern"]), value):
        errors.append(f"{at}: string does not match pattern {schema['pattern']!r}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{at}: number below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{at}: number above maximum {schema['maximum']}")
    if isinstance(value, list) and "minItems" in schema and len(value) < int(schema["minItems"]):
        errors.append(f"{at}: array shorter than minItems {schema['minItems']}")
    if isinstance(value, list) and "maxItems" in schema and len(value) > int(schema["maxItems"]):
        errors.append(f"{at}: array longer than maxItems {schema['maxItems']}")
    if isinstance(value, list) and schema.get("uniqueItems") is True:
        seen: set[str] = set()
        for index, item in enumerate(value):
            key = json.dumps(item, sort_keys=True)
            if key in seen:
                errors.append(f"{at}[{index}]: duplicate item violates uniqueItems")
            seen.add(key)
    if isinstance(value, list) and isinstance(schema.get("contains"), dict):
        contains_schema = schema["contains"]
        matched_count = sum(
            1
            for index, item in enumerate(value)
            if schema_matches(
                contains_schema,
                item,
                f"{at}[{index}]",
                schemas=schemas,
                root_schema=root,
                seen_refs=seen,
            )
        )
        min_contains = int(schema.get("minContains", 1))
        max_contains = schema.get("maxContains")
        if matched_count < min_contains:
            errors.append(f"{at}: array does not contain at least {min_contains} matching item(s)")
        if max_contains is not None and matched_count > int(max_contains):
            errors.append(f"{at}: array contains more than {int(max_contains)} matching item(s)")
    if isinstance(value, dict) and "minProperties" in schema and len(value) < int(schema["minProperties"]):
        errors.append(f"{at}: object has fewer properties than minProperties {schema['minProperties']}")

    if isinstance(value, dict):
        for field in schema.get("required", []):
            if field not in value:
                errors.append(f"{at}: missing required field {field}")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for field, subschema in properties.items():
                if field in value and isinstance(subschema, dict):
                    errors.extend(
                        validate_node(subschema, value[field], f"{at}.{field}", schemas=schemas, root_schema=root, seen_refs=seen)
                    )
        additional = schema.get("additionalProperties", True)
        if additional is False and isinstance(properties, dict):
            for field in value:
                if field not in properties:
                    errors.append(f"{at}: additional property {field} is not allowed")
        if isinstance(additional, dict):
            for field, item in value.items():
                if field not in properties:
                    errors.extend(validate_node(additional, item, f"{at}.{field}", schemas=schemas, root_schema=root, seen_refs=seen))

    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            errors.extend(validate_node(schema["items"], item, f"{at}[{index}]", schemas=schemas, root_schema=root, seen_refs=seen))

    return errors


def validate_domain_rules(data: dict[str, Any], at: str) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_public_ref_hygiene(data, at))
    if data.get("record_type") in RESEARCH_RECORD_TYPES:
        serialized = json.dumps(data, sort_keys=True)
        if PRIVATE_MARKERS.search(serialized):
            errors.append(f"{at}: research/product planning artifacts must not publish private local or runtime refs")
        present_raw_fields = sorted(field for field in RAW_RESEARCH_FIELDS if field in data)
        if present_raw_fields:
            errors.append(f"{at}: research/product planning artifacts must not contain raw dump fields: {', '.join(present_raw_fields)}")
        if data.get("record_type") == "specialist_decision_packet":
            if not data.get("resolutions"):
                errors.append(f"{at}: specialist_decision_packet must resolve research into operational factory decisions")
            impacts = data.get("impacts") if isinstance(data.get("impacts"), dict) else {}
            for field in ("sot", "architecture", "method_router", "gates", "proof"):
                if field not in impacts:
                    errors.append(f"{at}: specialist_decision_packet impacts must include {field}")
        if data.get("record_type") == "product_context_packet" and data.get("stale") is True:
            errors.append(f"{at}: public product_context_packet template must not be stale")
        if data.get("record_type") == "product_creation_plan" and data.get("complete_product_required") is not True:
            errors.append(f"{at}: product_creation_plan must preserve complete product scope")
    if data.get("record_type") in {"security_scan_result", "auditor_result", "product_face_result"}:
        if data.get("result") == "WAIVED":
            waiver = data.get("waiver")
            if not isinstance(waiver, dict):
                errors.append(f"{at}: WAIVED worker result requires waiver object")
            else:
                for field in ("owner", "reason", "expires_at", "reviewer_or_human_gate_ref"):
                    if not str(waiver.get(field) or "").strip():
                        errors.append(f"{at}.waiver: missing required field {field}")
                for field in ("compensating_controls", "evidence_refs"):
                    if not isinstance(waiver.get(field), list) or not waiver.get(field):
                        errors.append(f"{at}.waiver.{field}: expected non-empty array")
        if data.get("evidence_kind") == "waiver" and data.get("result") != "WAIVED":
            errors.append(f"{at}: evidence_kind=waiver requires result=WAIVED")
    if data.get("record_type") == "operational_evidence_bundle":
        artifacts = data.get("artifacts") if isinstance(data.get("artifacts"), list) else []
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                continue
            reason = public_artifact_ref_error(artifact.get("artifact_ref"))
            if reason:
                errors.append(f"{at}.artifacts[{index}].artifact_ref: {reason}")
        waiver = data.get("waiver") if isinstance(data.get("waiver"), dict) else {}
        waiver_refs = waiver.get("evidence_refs") if isinstance(waiver.get("evidence_refs"), list) else []
        for index, ref in enumerate(waiver_refs):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.waiver.evidence_refs[{index}]: {reason}")
        if data.get("verdict") == "WAIVED" and data.get("evidence_kind") != "waiver":
            errors.append(f"{at}: WAIVED operational_evidence_bundle requires evidence_kind=waiver")
        if data.get("evidence_kind") == "waiver" and data.get("verdict") != "WAIVED":
            errors.append(f"{at}: evidence_kind=waiver requires verdict=WAIVED")
        if data.get("evidence_kind") == "synthetic":
            if data.get("reusable_for_product") is not False:
                errors.append(f"{at}: synthetic operational_evidence_bundle requires reusable_for_product=false")
            if not data.get("cannot_satisfy"):
                errors.append(f"{at}: synthetic operational_evidence_bundle requires cannot_satisfy")
    if data.get("record_type") == "customer_readiness_gate":
        add_public_ref_errors(data.get("evidence_refs"), f"{at}.evidence_refs", errors)
        waiver = data.get("waiver") if isinstance(data.get("waiver"), dict) else {}
        add_public_ref_errors(waiver.get("evidence_refs"), f"{at}.waiver.evidence_refs", errors)
        decision = str(data.get("decision") or "").strip().upper()
        if decision == "WAIVED" and waiver.get("cannot_claim_customer_ready") is not True:
            errors.append(f"{at}: customer_readiness_gate WAIVED must set cannot_claim_customer_ready=true")
        if decision == "PASS" and waiver:
            errors.append(f"{at}: customer_readiness_gate PASS must not carry a waiver")
    if data.get("record_type") == "scale_slo_readiness_gate":
        add_public_ref_errors(data.get("evidence_refs"), f"{at}.evidence_refs", errors)
        waiver = data.get("waiver") if isinstance(data.get("waiver"), dict) else {}
        add_public_ref_errors(waiver.get("evidence_refs"), f"{at}.waiver.evidence_refs", errors)
        decision = str(data.get("decision") or "").strip().upper()
        proof_result = str(data.get("proof_result") or "").strip().upper()
        if decision == "WAIVED" and waiver.get("cannot_claim_scale_ready") is not True:
            errors.append(f"{at}: scale_slo_readiness_gate WAIVED must set cannot_claim_scale_ready=true")
        if decision == "PASS" and waiver:
            errors.append(f"{at}: scale_slo_readiness_gate PASS must not carry a waiver")
        if decision == "PASS" and proof_result != "PASS":
            errors.append(f"{at}: scale_slo_readiness_gate PASS requires proof_result PASS")
    if data.get("record_type") == "factory_sdlc_lifecycle_state":
        refs = data.get("evidence_refs") if isinstance(data.get("evidence_refs"), list) else []
        for index, ref in enumerate(refs):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.evidence_refs[{index}]: {reason}")
        gate = data.get("gate_predicate") if isinstance(data.get("gate_predicate"), dict) else {}
        gate_refs = gate.get("evidence_refs") if isinstance(gate.get("evidence_refs"), list) else []
        for index, ref in enumerate(gate_refs):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.gate_predicate.evidence_refs[{index}]: {reason}")
        phase_states = data.get("phase_states") if isinstance(data.get("phase_states"), list) else []
        for phase_index, phase in enumerate(phase_states):
            if not isinstance(phase, dict):
                continue
            phase_refs = phase.get("evidence_refs") if isinstance(phase.get("evidence_refs"), list) else []
            for index, ref in enumerate(phase_refs):
                reason = public_artifact_ref_error(ref)
                if reason:
                    errors.append(f"{at}.phase_states[{phase_index}].evidence_refs[{index}]: {reason}")
            phase_gate = phase.get("gate_predicate") if isinstance(phase.get("gate_predicate"), dict) else {}
            phase_gate_refs = phase_gate.get("evidence_refs") if isinstance(phase_gate.get("evidence_refs"), list) else []
            for index, ref in enumerate(phase_gate_refs):
                reason = public_artifact_ref_error(ref)
                if reason:
                    errors.append(f"{at}.phase_states[{phase_index}].gate_predicate.evidence_refs[{index}]: {reason}")
            status = str(phase.get("status") or "").strip().upper()
            human_gate = phase.get("human_gate") if isinstance(phase.get("human_gate"), dict) else {}
            recovery = phase.get("recovery_route") if isinstance(phase.get("recovery_route"), dict) else {}
            if status == "BLOCKED" and human_gate.get("required") is not True and recovery.get("required") is not True:
                errors.append(f"{at}.phase_states[{phase_index}]: non-human BLOCKED state requires recovery route")
        acceptance = data.get("lifecycle_acceptance") if isinstance(data.get("lifecycle_acceptance"), dict) else {}
        proof_level = str(acceptance.get("proof_level") or "")
        if acceptance.get("production_ready_claimed") is True and proof_level not in {"production_strict", "customer_validated"}:
            errors.append(f"{at}: production readiness requires production_strict or customer_validated proof")
        if acceptance.get("customer_ready_claimed") is True and proof_level != "customer_validated":
            errors.append(f"{at}: customer readiness requires customer_validated proof")
    if data.get("record_type") == "factory_sdlc_feedback_loop":
        linked_lifecycle = str(data.get("linked_lifecycle_state_ref") or "").strip()
        if linked_lifecycle:
            reason = public_artifact_ref_error(linked_lifecycle)
            if reason:
                errors.append(f"{at}.linked_lifecycle_state_ref: {reason}")
        source = data.get("source_signal") if isinstance(data.get("source_signal"), dict) else {}
        source_ref = str(source.get("signal_ref_public_safe") or "").strip()
        reason = public_artifact_ref_error(source_ref)
        if reason:
            errors.append(f"{at}.source_signal.signal_ref_public_safe: {reason}")
        if source.get("sensitivity_class") == "secret":
            errors.append(f"{at}: factory_sdlc_feedback_loop cannot publish secret-class signals")
        triage = data.get("triage_decision") if isinstance(data.get("triage_decision"), dict) else {}
        route_ref = str(triage.get("route_ref") or "").strip()
        reason = public_artifact_ref_error(route_ref)
        if reason:
            errors.append(f"{at}.triage_decision.route_ref: {reason}")
        routing = data.get("routing_decision") if isinstance(data.get("routing_decision"), dict) else {}
        router_ref = str(routing.get("router_ref") or "").strip()
        reason = public_artifact_ref_error(router_ref)
        if reason:
            errors.append(f"{at}.routing_decision.router_ref: {reason}")
        if routing.get("model_independence_preserved") is not True:
            errors.append(f"{at}: factory_sdlc_feedback_loop routing must preserve model independence")
        if routing.get("single_provider_assumption") is not False:
            errors.append(f"{at}: factory_sdlc_feedback_loop routing must not assume a single provider")
        evidence = data.get("execution_evidence") if isinstance(data.get("execution_evidence"), dict) else {}
        for field in ("evidence_refs", "validation_refs"):
            refs = evidence.get(field) if isinstance(evidence.get(field), list) else []
            for index, ref in enumerate(refs):
                reason = public_artifact_ref_error(ref)
                if reason:
                    errors.append(f"{at}.execution_evidence.{field}[{index}]: {reason}")
        if evidence.get("failed_outputs_consumable_as_success") is not False:
            errors.append(f"{at}: factory_sdlc_feedback_loop failed outputs cannot be consumed as success")
        learnback = data.get("learnback_decision") if isinstance(data.get("learnback_decision"), dict) else {}
        for field in ("source_evidence_refs", "validation_refs"):
            refs = learnback.get(field) if isinstance(learnback.get(field), list) else []
            for index, ref in enumerate(refs):
                reason = public_artifact_ref_error(ref)
                if reason:
                    errors.append(f"{at}.learnback_decision.{field}[{index}]: {reason}")
        classification = str(learnback.get("classification") or "").strip()
        target_artifact = str(learnback.get("target_artifact_type") or "").strip()
        promotion_boundary = str(learnback.get("promotion_boundary") or "").strip()
        if classification != "reject" and target_artifact == "none":
            errors.append(f"{at}: factory_sdlc_feedback_loop learnback requires an actionable target artifact")
        if classification == "reject" and target_artifact != "none":
            errors.append(f"{at}: factory_sdlc_feedback_loop rejected learnback must use target_artifact_type=none")
        if classification != "reject" and promotion_boundary == "rejected":
            errors.append(f"{at}: factory_sdlc_feedback_loop non-rejected learnback cannot use rejected promotion boundary")
        sovereignty = data.get("sovereignty_boundary") if isinstance(data.get("sovereignty_boundary"), dict) else {}
        if sovereignty.get("public_safe_refs_only") is not True:
            errors.append(f"{at}: factory_sdlc_feedback_loop requires public_safe_refs_only=true")
        if sovereignty.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: factory_sdlc_feedback_loop must not embed raw private evidence")
        if sovereignty.get("private_context_retained_outside_public_repo") is not True:
            errors.append(f"{at}: factory_sdlc_feedback_loop private context must stay outside the public repo")
    if data.get("record_type") == "universal_signal_intake":
        signal = data.get("signal") if isinstance(data.get("signal"), dict) else {}
        source_ref = str(signal.get("signal_ref_public_safe") or "").strip()
        reason = public_artifact_ref_error(source_ref)
        if reason:
            errors.append(f"{at}.signal.signal_ref_public_safe: {reason}")
        if signal.get("sensitivity_class") == "secret":
            errors.append(f"{at}: universal_signal_intake cannot publish secret-class signals")
        if signal.get("raw_private_embedded") is not False:
            errors.append(f"{at}: universal_signal_intake signal must not embed raw private evidence")
        classification = data.get("classification") if isinstance(data.get("classification"), dict) else {}
        if classification.get("can_start_execution") is not False:
            errors.append(f"{at}: universal_signal_intake classification cannot allow execution directly")
        route_class = str(classification.get("route_class") or "").strip()
        request_type = str(classification.get("request_type") or "").strip()
        signal_type = str(signal.get("signal_type") or "").strip()
        allowed_request_types = UNIVERSAL_SIGNAL_ROUTE_REQUEST_TYPES.get(route_class)
        if allowed_request_types and request_type and request_type not in allowed_request_types:
            errors.append(
                f"{at}: universal_signal_intake.classification.request_type is not valid "
                f"for route_class {route_class}: {request_type}"
            )
        allowed_signal_types = UNIVERSAL_SIGNAL_ROUTE_SIGNAL_TYPES.get(route_class)
        if allowed_signal_types and signal_type and signal_type not in allowed_signal_types:
            errors.append(
                f"{at}: universal_signal_intake.signal.signal_type is not valid "
                f"for route_class {route_class}: {signal_type}"
            )
        normalization = data.get("normalization") if isinstance(data.get("normalization"), dict) else {}
        if normalization.get("source_resolution_required") is not True:
            errors.append(f"{at}: universal_signal_intake source_resolution_required must be true")
        if normalization.get("no_chat_only_state") is not True:
            errors.append(f"{at}: universal_signal_intake no_chat_only_state must be true")
        route = data.get("route_decision") if isinstance(data.get("route_decision"), dict) else {}
        selected_method_family = str(route.get("selected_method_family") or "").strip()
        expected_method_family = UNIVERSAL_SIGNAL_ROUTE_METHOD_FAMILIES.get(route_class)
        if expected_method_family and selected_method_family and selected_method_family != expected_method_family:
            errors.append(
                f"{at}: universal_signal_intake.route_decision.selected_method_family "
                f"must match route registry for {route_class}: {expected_method_family}"
            )
        for field in ("method_contract_ref", "sdlc_feedback_loop_ref", "factory_workflow_phase_ref", "fallback_route"):
            route_ref = str(route.get(field) or "").strip()
            reason = public_artifact_ref_error(route_ref)
            if reason:
                errors.append(f"{at}.route_decision.{field}: {reason}")
        recovery = route.get("non_human_block_recovery") if isinstance(route.get("non_human_block_recovery"), dict) else {}
        recovery_ref = str(recovery.get("route_ref") or "").strip()
        reason = public_artifact_ref_error(recovery_ref)
        if reason:
            errors.append(f"{at}.route_decision.non_human_block_recovery.route_ref: {reason}")
        if recovery.get("required") is not True or recovery.get("factory_owned_repair_allowed") is not True:
            errors.append(f"{at}: universal_signal_intake non-human block must return to a factory-owned repair route")
        retry_policy = recovery.get("retry_policy") if isinstance(recovery.get("retry_policy"), dict) else {}
        max_attempts = retry_policy.get("max_attempts")
        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or max_attempts < 1:
            errors.append(f"{at}: universal_signal_intake non-human recovery requires retry_policy.max_attempts >= 1")
        artifacts = data.get("required_artifacts") if isinstance(data.get("required_artifacts"), list) else []
        artifact_types = {
            str(artifact.get("artifact_type") or "").strip()
            for artifact in artifacts
            if isinstance(artifact, dict)
        }
        missing_artifacts = sorted(UNIVERSAL_SIGNAL_ROUTE_REQUIRED_ARTIFACTS.get(route_class, set()) - artifact_types)
        if missing_artifacts:
            errors.append(
                f"{at}: universal_signal_intake {route_class} route missing required artifact types: "
                + ", ".join(missing_artifacts)
            )
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                continue
            artifact_ref = str(artifact.get("artifact_ref") or "").strip()
            reason = public_artifact_ref_error(artifact_ref)
            if reason:
                errors.append(f"{at}.required_artifacts[{index}].artifact_ref: {reason}")
            artifact_type = str(artifact.get("artifact_type") or "").strip()
            if artifact_type in UNIVERSAL_SIGNAL_ROUTE_REQUIRED_ARTIFACTS.get(route_class, set()):
                if artifact.get("blocks_execution_when_missing") is not True:
                    errors.append(
                        f"{at}.required_artifacts[{index}].blocks_execution_when_missing "
                        "must be true for required route artifact"
                    )
            owner_worker = str(artifact.get("owner_worker") or "").strip()
            if owner_worker and owner_worker not in public_worker_ids():
                errors.append(f"{at}.required_artifacts[{index}].owner_worker must be a registered worker: {owner_worker}")
        registry_required_workers = set(route_required_workers().get(route_class, []))
        required_workers = data.get("required_workers") if isinstance(data.get("required_workers"), list) else []
        intake_worker_ids = {
            str(worker.get("worker_id") or "").strip()
            for worker in required_workers
            if isinstance(worker, dict)
        }
        missing_workers = sorted(registry_required_workers - intake_worker_ids)
        if missing_workers:
            errors.append(
                f"{at}: universal_signal_intake {route_class} route missing required workers: "
                + ", ".join(missing_workers)
            )
        for index, worker in enumerate(required_workers):
            if not isinstance(worker, dict):
                continue
            worker_id = str(worker.get("worker_id") or "").strip()
            if worker_id and worker_id not in public_worker_ids():
                errors.append(f"{at}.required_workers[{index}].worker_id must be a registered worker: {worker_id}")
        handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else {}
        if handoff.get("factory_owned_next_step") is not True:
            errors.append(f"{at}: universal_signal_intake handoff.factory_owned_next_step must be true")
        boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
        if boundary.get("public_safe_refs_only") is not True:
            errors.append(f"{at}: universal_signal_intake requires public_safe_refs_only=true")
        if boundary.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: universal_signal_intake must not embed raw private evidence")
        if boundary.get("private_context_retained_outside_public_repo") is not True:
            errors.append(f"{at}: universal_signal_intake private context must stay outside the public repo")
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("execution_allowed") is not False:
            errors.append(f"{at}: universal_signal_intake acceptance.execution_allowed must be false")
        evidence_refs = acceptance.get("evidence_refs") if isinstance(acceptance.get("evidence_refs"), list) else []
        for index, ref in enumerate(evidence_refs):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.acceptance.evidence_refs[{index}]: {reason}")
    if data.get("record_type") == "source_resolution_packet":
        intake_ref = str(data.get("intake_ref_public_safe") or "").strip()
        reason = public_artifact_ref_error(intake_ref)
        if reason:
            errors.append(f"{at}.intake_ref_public_safe: {reason}")
        source_signal = data.get("source_signal") if isinstance(data.get("source_signal"), dict) else {}
        signal_ref = str(source_signal.get("signal_ref_public_safe") or "").strip()
        reason = public_artifact_ref_error(signal_ref)
        if reason:
            errors.append(f"{at}.source_signal.signal_ref_public_safe: {reason}")
        claim_classes = {
            str(item.get("class") or "").strip()
            for item in data.get("source_claim_classes", [])
            if isinstance(item, dict)
        }
        missing_claim_classes = sorted({"fact", "inference", "decision", "conflict", "gap", "stale"} - claim_classes)
        if missing_claim_classes:
            errors.append(f"{at}: source_resolution_packet missing claim classes: " + ", ".join(missing_claim_classes))
        resolution = data.get("resolution_policy") if isinstance(data.get("resolution_policy"), dict) else {}
        if resolution.get("source_resolution_required") is not True:
            errors.append(f"{at}: source_resolution_packet source_resolution_required must be true")
        if resolution.get("factory_owns_discoverable_gaps") is not True:
            errors.append(f"{at}: source_resolution_packet discoverable gaps must be factory-owned")
        if resolution.get("user_only_for_authority_access_risk_or_preference") is not True:
            errors.append(f"{at}: source_resolution_packet user gate must be limited to authority, access, risk or preference")
        if resolution.get("no_chat_only_state") is not True:
            errors.append(f"{at}: source_resolution_packet no_chat_only_state must be true")
        if resolution.get("claim_resolution_required_before_product_sot") is not True:
            errors.append(f"{at}: source_resolution_packet claim resolution must precede Product SOT")
        recovery = resolution.get("non_human_block_recovery") if isinstance(resolution.get("non_human_block_recovery"), dict) else {}
        if recovery.get("factory_owned_repair_allowed") is not True:
            errors.append(f"{at}: source_resolution_packet non-human block must return to factory-owned repair")
        retry_policy = recovery.get("retry_policy") if isinstance(recovery.get("retry_policy"), dict) else {}
        max_attempts = retry_policy.get("max_attempts")
        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or max_attempts < 1:
            errors.append(f"{at}: source_resolution_packet retry_policy.max_attempts must be >= 1")
        artifacts = data.get("next_artifacts") if isinstance(data.get("next_artifacts"), list) else []
        artifact_types = {
            str(artifact.get("artifact_type") or "").strip()
            for artifact in artifacts
            if isinstance(artifact, dict)
        }
        if "source_ledger" not in artifact_types:
            errors.append(f"{at}: source_resolution_packet requires source_ledger as a next artifact")
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                continue
            artifact_ref = str(artifact.get("artifact_ref") or "").strip()
            reason = public_artifact_ref_error(artifact_ref)
            if reason:
                errors.append(f"{at}.next_artifacts[{index}].artifact_ref: {reason}")
            if artifact.get("status") != "pending_factory_worker":
                errors.append(f"{at}.next_artifacts[{index}].status must be pending_factory_worker")
            if artifact.get("blocks_execution_when_missing") is not True:
                errors.append(f"{at}.next_artifacts[{index}].blocks_execution_when_missing must be true")
            owner_worker = str(artifact.get("owner_worker") or "").strip()
            if owner_worker and owner_worker not in public_worker_ids():
                errors.append(f"{at}.next_artifacts[{index}].owner_worker must be a registered worker: {owner_worker}")
        blocking_rules = data.get("blocking_rules") if isinstance(data.get("blocking_rules"), dict) else {}
        for field in (
            "source_resolution_required",
            "source_ledger_required",
            "execution_blocked_until_required_artifacts_pass",
            "human_gate_only_for_authority_access_risk_or_preference",
        ):
            if blocking_rules.get(field) is not True:
                errors.append(f"{at}.blocking_rules.{field} must be true")
        needs_product_sot = source_signal.get("needs_product_sot") is True
        if needs_product_sot and blocking_rules.get("product_sot_worker_required") is not True:
            errors.append(
                f"{at}.blocking_rules.product_sot_worker_required must be true when Product SOT is required"
            )
        if not isinstance(blocking_rules.get("product_sot_worker_required"), bool):
            errors.append(f"{at}.blocking_rules.product_sot_worker_required must be boolean")
        handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else {}
        if handoff.get("next_artifact") != "source_ledger":
            errors.append(f"{at}: source_resolution_packet.handoff.next_artifact must be source_ledger")
        if handoff.get("factory_owned_next_step") is not True:
            errors.append(f"{at}: source_resolution_packet.handoff.factory_owned_next_step must be true")
        boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
        if boundary.get("public_safe_refs_only") is not True:
            errors.append(f"{at}: source_resolution_packet requires public_safe_refs_only=true")
        if boundary.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: source_resolution_packet must not embed raw private evidence")
        if boundary.get("private_context_retained_outside_public_repo") is not True:
            errors.append(f"{at}: source_resolution_packet private context must stay outside the public repo")
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("source_resolution_packet_ready") is not True:
            errors.append(f"{at}: source_resolution_packet acceptance.source_resolution_packet_ready must be true")
        if acceptance.get("product_sot_generated") is not False:
            errors.append(f"{at}: source_resolution_packet must not claim Product SOT was generated")
        if acceptance.get("execution_allowed") is not False:
            errors.append(f"{at}: source_resolution_packet acceptance.execution_allowed must be false")
        evidence_refs = acceptance.get("evidence_refs") if isinstance(acceptance.get("evidence_refs"), list) else []
        for index, ref in enumerate(evidence_refs):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.acceptance.evidence_refs[{index}]: {reason}")
    if data.get("record_type") == "product_source_ledger":
        for field in ("source_resolution_ref", "source_ref_public_safe"):
            reason = public_artifact_ref_error(data.get(field))
            if reason:
                errors.append(f"{at}.{field}: {reason}")
        source_signal = data.get("source_signal") if isinstance(data.get("source_signal"), dict) else {}
        signal_ref = str(source_signal.get("signal_ref_public_safe") or "").strip()
        reason = public_artifact_ref_error(signal_ref)
        if reason:
            errors.append(f"{at}.source_signal.signal_ref_public_safe: {reason}")
        route_class = str(source_signal.get("route_class") or "").strip()
        request_type = str(source_signal.get("request_type") or "").strip()
        signal_type = str(source_signal.get("signal_type") or "").strip()
        allowed_request_types = UNIVERSAL_SIGNAL_ROUTE_REQUEST_TYPES.get(route_class)
        if allowed_request_types and request_type and request_type not in allowed_request_types:
            errors.append(
                f"{at}: product_source_ledger.source_signal.request_type is not valid "
                f"for route_class {route_class}: {request_type}"
            )
        allowed_signal_types = UNIVERSAL_SIGNAL_ROUTE_SIGNAL_TYPES.get(route_class)
        if allowed_signal_types and signal_type and signal_type not in allowed_signal_types:
            errors.append(
                f"{at}: product_source_ledger.source_signal.signal_type is not valid "
                f"for route_class {route_class}: {signal_type}"
            )
        for index, source in enumerate(data.get("source_map", []) if isinstance(data.get("source_map"), list) else []):
            if not isinstance(source, dict):
                continue
            reason = public_artifact_ref_error(source.get("source_ref_public_safe"))
            if reason:
                errors.append(f"{at}.source_map[{index}].source_ref_public_safe: {reason}")
            if source.get("raw_private_embedded") is not False:
                errors.append(f"{at}.source_map[{index}].raw_private_embedded must be false")
        claim_classes = {
            str(claim.get("claim_class") or "").strip()
            for claim in data.get("claim_table", []) if isinstance(claim, dict)
        }
        if "fact" not in claim_classes:
            errors.append(f"{at}: product_source_ledger requires at least one fact claim")
        for claim_index, claim in enumerate(data.get("claim_table", []) if isinstance(data.get("claim_table"), list) else []):
            if not isinstance(claim, dict):
                continue
            if claim.get("claim_class") == "conflict" and claim.get("status") == "promoted":
                errors.append(f"{at}.claim_table[{claim_index}] cannot promote unresolved conflict claims")
            for ref_index, ref in enumerate(claim.get("source_refs", []) if isinstance(claim.get("source_refs"), list) else []):
                reason = public_artifact_ref_error(ref)
                if reason:
                    errors.append(f"{at}.claim_table[{claim_index}].source_refs[{ref_index}]: {reason}")
        resolution_state = data.get("resolution_state") if isinstance(data.get("resolution_state"), dict) else {}
        if resolution_state.get("source_ledger_created") is not True:
            errors.append(f"{at}: product_source_ledger source_ledger_created must be true")
        if resolution_state.get("no_chat_only_state") is not True:
            errors.append(f"{at}: product_source_ledger no_chat_only_state must be true")
        blocking_rules = data.get("blocking_rules") if isinstance(data.get("blocking_rules"), dict) else {}
        for field in (
            "execution_blocked_until_required_artifacts_pass",
            "raw_private_evidence_must_stay_external",
            "human_gate_only_for_authority_access_risk_or_preference",
        ):
            if blocking_rules.get(field) is not True:
                errors.append(f"{at}.blocking_rules.{field} must be true")
        if not isinstance(blocking_rules.get("product_sot_blocked_until_claims_reviewed"), bool):
            errors.append(f"{at}.blocking_rules.product_sot_blocked_until_claims_reviewed must be boolean")
        handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else {}
        next_worker = str(handoff.get("next_worker") or "").strip()
        if handoff.get("factory_owned_next_step") is not True:
            errors.append(f"{at}: product_source_ledger.handoff.factory_owned_next_step must be true")
        if next_worker and next_worker not in public_worker_ids():
            errors.append(f"{at}.handoff.next_worker must be a registered worker: {next_worker}")
        boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
        if boundary.get("public_safe_refs_only") is not True:
            errors.append(f"{at}: product_source_ledger requires public_safe_refs_only=true")
        if boundary.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: product_source_ledger must not embed raw private evidence")
        if boundary.get("private_context_retained_outside_public_repo") is not True:
            errors.append(f"{at}: product_source_ledger private context must stay outside the public repo")
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("source_ledger_created") is not True:
            errors.append(f"{at}: product_source_ledger acceptance.source_ledger_created must be true")
        if acceptance.get("product_sot_generated") is not False:
            errors.append(f"{at}: product_source_ledger must not claim Product SOT was generated")
        if acceptance.get("execution_allowed") is not False:
            errors.append(f"{at}: product_source_ledger acceptance.execution_allowed must be false")
        for index, ref in enumerate(acceptance.get("evidence_refs", []) if isinstance(acceptance.get("evidence_refs"), list) else []):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.acceptance.evidence_refs[{index}]: {reason}")
    if data.get("record_type") == "operator_understanding_confirmation":
        reason = public_artifact_ref_error(data.get("source_ledger_ref"))
        if reason:
            errors.append(f"{at}.source_ledger_ref: {reason}")
        source_signal = data.get("source_signal") if isinstance(data.get("source_signal"), dict) else {}
        signal_ref = str(source_signal.get("signal_ref_public_safe") or "").strip()
        reason = public_artifact_ref_error(signal_ref)
        if reason:
            errors.append(f"{at}.source_signal.signal_ref_public_safe: {reason}")
        for index, source in enumerate(data.get("material_inventory", []) if isinstance(data.get("material_inventory"), list) else []):
            if not isinstance(source, dict):
                continue
            reason = public_artifact_ref_error(source.get("source_ref_public_safe"))
            if reason:
                errors.append(f"{at}.material_inventory[{index}].source_ref_public_safe: {reason}")
        understanding = data.get("product_understanding") if isinstance(data.get("product_understanding"), dict) else {}
        for field in (
            "what_the_factory_understands",
            "target_user_understanding",
            "business_or_success_understanding",
            "non_negotiables_understood",
            "open_uncertainties",
        ):
            values = understanding.get(field)
            if isinstance(values, list):
                for value_index, value in enumerate(values):
                    if PRIVATE_MARKERS.search(str(value or "")):
                        errors.append(f"{at}.product_understanding.{field}[{value_index}]: private local or runtime marker")
            elif PRIVATE_MARKERS.search(str(values or "")):
                errors.append(f"{at}.product_understanding.{field}: private local or runtime marker")
        questions = data.get("operator_questions") if isinstance(data.get("operator_questions"), list) else []
        if not questions:
            errors.append(f"{at}: operator_understanding_confirmation requires at least one operator question")
        if len(questions) > 5:
            errors.append(f"{at}: operator_understanding_confirmation must keep Telegram questions <= 5")
        for index, question in enumerate(questions):
            if not isinstance(question, dict):
                continue
            if question.get("required_before_product_sot") is not True:
                errors.append(f"{at}.operator_questions[{index}].required_before_product_sot must be true")
        state = data.get("confirmation_state") if isinstance(data.get("confirmation_state"), dict) else {}
        response_ref = str(state.get("operator_response_ref") or "").strip()
        if response_ref:
            reason = public_artifact_ref_error(response_ref)
            if reason and not response_ref.startswith("pending:"):
                errors.append(f"{at}.confirmation_state.operator_response_ref: {reason}")
        status = str(state.get("status") or "").strip()
        product_sot_allowed = state.get("product_sot_allowed") is True
        if status == "confirmed" and response_ref.startswith("pending:"):
            errors.append(f"{at}: operator_understanding_confirmation confirmed status requires a real operator_response_ref")
        if status == "confirmed" and not product_sot_allowed:
            errors.append(f"{at}: operator_understanding_confirmation confirmed status requires product_sot_allowed=true")
        if status != "confirmed" and product_sot_allowed:
            errors.append(f"{at}: operator_understanding_confirmation product_sot_allowed=true requires confirmed status")
        rules = data.get("blocking_rules") if isinstance(data.get("blocking_rules"), dict) else {}
        if rules.get("product_sot_blocked_until_operator_understanding_confirmed") is not True:
            errors.append(f"{at}: operator_understanding_confirmation must block Product SOT until confirmed")
        max_questions = rules.get("max_operator_questions_for_telegram")
        if not isinstance(max_questions, int) or isinstance(max_questions, bool) or max_questions < 1 or max_questions > 5:
            errors.append(f"{at}: operator_understanding_confirmation max_operator_questions_for_telegram must be 1..5")
        if rules.get("summarize_sources_do_not_dump") is not True:
            errors.append(f"{at}: operator_understanding_confirmation must summarize sources instead of dumping them")
        if rules.get("understanding_confirmation_is_not_execution_approval") is not True:
            errors.append(f"{at}: operator_understanding_confirmation must not be execution approval")
        handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else {}
        if status == "confirmed" and handoff.get("next_artifact") != "outcome_contract":
            errors.append(f"{at}: operator_understanding_confirmation confirmed handoff must go to outcome_contract")
        if status != "confirmed" and handoff.get("user_decision_required") is not True:
            errors.append(f"{at}: operator_understanding_confirmation pending handoff requires user_decision_required=true")
        boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
        if boundary.get("public_safe_refs_only") is not True:
            errors.append(f"{at}: operator_understanding_confirmation requires public_safe_refs_only=true")
        if boundary.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: operator_understanding_confirmation must not embed raw private evidence")
        if boundary.get("private_context_retained_outside_public_repo") is not True:
            errors.append(f"{at}: operator_understanding_confirmation private context must stay outside the public repo")
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("understanding_confirmation_created") is not True:
            errors.append(f"{at}: operator_understanding_confirmation acceptance.understanding_confirmation_created must be true")
        if acceptance.get("product_sot_allowed") is not product_sot_allowed:
            errors.append(f"{at}: operator_understanding_confirmation acceptance.product_sot_allowed must match confirmation state")
        if acceptance.get("product_sot_generated") is not False:
            errors.append(f"{at}: operator_understanding_confirmation must not claim Product SOT was generated")
        if acceptance.get("execution_allowed") is not False:
            errors.append(f"{at}: operator_understanding_confirmation acceptance.execution_allowed must be false")
        for index, ref in enumerate(acceptance.get("evidence_refs", []) if isinstance(acceptance.get("evidence_refs"), list) else []):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.acceptance.evidence_refs[{index}]: {reason}")
    if data.get("record_type") == "operator_interface_profile":
        capabilities = data.get("interface_capabilities") if isinstance(data.get("interface_capabilities"), dict) else {}
        if capabilities.get("supports_push_notifications") is not True:
            errors.append(f"{at}: operator_interface_profile must support proactive notifications")
        if data.get("primary_interface") == "telegram":
            formats = set(text_items(capabilities.get("supported_attachment_formats")))
            if not {"markdown", "pdf"}.issubset(formats):
                errors.append(f"{at}: telegram interface must support markdown and pdf attachments")
        conversation = data.get("conversation_policy") if isinstance(data.get("conversation_policy"), dict) else {}
        if conversation.get("status_polling_required") is not False:
            errors.append(f"{at}: operator_interface_profile must not require status polling")
        if conversation.get("operator_not_required_to_poll") is not True:
            errors.append(f"{at}: operator_interface_profile operator_not_required_to_poll must be true")
        proactive = data.get("proactive_notification_policy") if isinstance(data.get("proactive_notification_policy"), dict) else {}
        if proactive.get("enabled") is not True or proactive.get("operator_polling_required") is not False:
            errors.append(f"{at}: operator_interface_profile proactive notifications must be enabled and polling-free")
        notify_on = set(text_items(proactive.get("notify_on")))
        missing_notify = sorted({"decision_required", "gate_blocked", "worker_batch_completed", "idle_timeout_detected"} - notify_on)
        if missing_notify:
            errors.append(f"{at}: operator_interface_profile missing notify_on triggers: " + ", ".join(missing_notify))
        delivery = data.get("artifact_delivery_policy") if isinstance(data.get("artifact_delivery_policy"), dict) else {}
        if delivery.get("summary_only_forbidden_when_decision_required") is not True:
            errors.append(f"{at}: operator_interface_profile must forbid summary-only decision packages")
        required_formats = set(text_items(delivery.get("required_attachment_formats")))
        if not {"markdown", "pdf"}.issubset(required_formats):
            errors.append(f"{at}: operator_interface_profile required_attachment_formats must include markdown and pdf")
        send_for = set(text_items(delivery.get("send_for_artifact_types")))
        missing_deep = sorted({"operator_understanding_confirmation", "product_sot", "architecture_candidate"} - send_for)
        if missing_deep:
            errors.append(f"{at}: operator_interface_profile missing deep artifact types: " + ", ".join(missing_deep))
        boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
        if boundary.get("public_safe_refs_only") is not True or boundary.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: operator_interface_profile must keep public/private boundary strict")
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("operator_polling_required") is not False:
            errors.append(f"{at}: operator_interface_profile acceptance.operator_polling_required must be false")
        if acceptance.get("execution_allowed") is not False:
            errors.append(f"{at}: operator_interface_profile must not allow execution")
    if data.get("record_type") == "factory_start_conversation":
        for field in ("primary_interface_ref", "source_envelope_ref"):
            reason = public_artifact_ref_error(data.get(field))
            if reason:
                errors.append(f"{at}.{field}: {reason}")
        loop = data.get("product_understanding_loop") if isinstance(data.get("product_understanding_loop"), dict) else {}
        confirmed_ref = str(loop.get("confirmed_understanding_ref") or "").strip()
        if confirmed_ref and not confirmed_ref.startswith("pending:"):
            reason = public_artifact_ref_error(confirmed_ref)
            if reason:
                errors.append(f"{at}.product_understanding_loop.confirmed_understanding_ref: {reason}")
        boundary = data.get("factory_start_boundary") if isinstance(data.get("factory_start_boundary"), dict) else {}
        for field in (
            "factory_start_forbidden_until_understanding_confirmed",
            "manager_compiles_conversation_before_start",
            "new_project_creates_fresh_hermes_board",
            "bridge_does_not_create_cards",
            "execution_forbidden_at_start_conversation",
        ):
            if boundary.get(field) is not True:
                errors.append(f"{at}.factory_start_boundary.{field} must be true")
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("factory_start_allowed") is True and confirmed_ref.startswith("pending:"):
            errors.append(f"{at}: factory start cannot be allowed while understanding confirmation is pending")
        handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else {}
        start_request_ref = str(handoff.get("factory_bridge_start_request_ref") or "").strip()
        if acceptance.get("factory_start_allowed") is True:
            if start_request_ref.startswith(("pending:", "not-created")):
                errors.append(f"{at}: factory start cannot be allowed without a real factory start request ref")
            else:
                reason = public_artifact_ref_error(start_request_ref)
                if reason:
                    errors.append(f"{at}.handoff.factory_bridge_start_request_ref: {reason}")
        if acceptance.get("execution_allowed") is not False:
            errors.append(f"{at}: factory_start_conversation must not allow execution")
        if acceptance.get("operator_polling_required") is not False:
            errors.append(f"{at}: factory_start_conversation operator_polling_required must be false")
    if data.get("record_type") == "operator_briefing_package":
        primary_ref = str(data.get("primary_interface_ref") or "").strip()
        if primary_ref:
            reason = public_artifact_ref_error(primary_ref)
            if reason:
                errors.append(f"{at}.primary_interface_ref: {reason}")
        target = data.get("target_artifact") if isinstance(data.get("target_artifact"), dict) else {}
        reason = public_artifact_ref_error(target.get("artifact_ref"))
        if reason:
            errors.append(f"{at}.target_artifact.artifact_ref: {reason}")
        assets = data.get("delivery_assets") if isinstance(data.get("delivery_assets"), list) else []
        asset_kinds = {
            str(asset.get("kind") or "").strip()
            for asset in assets
            if isinstance(asset, dict)
        }
        for index, asset in enumerate(assets):
            if not isinstance(asset, dict):
                continue
            reason = public_artifact_ref_error(asset.get("asset_ref"))
            if reason:
                errors.append(f"{at}.delivery_assets[{index}].asset_ref: {reason}")
        if not {"markdown_document", "pdf_document"}.issubset(asset_kinds):
            errors.append(f"{at}: operator_briefing_package must include markdown_document and pdf_document")
        if target.get("decision_required") is True:
            required_assets = {
                str(asset.get("kind") or "").strip()
                for asset in assets
                if isinstance(asset, dict) and asset.get("required_for_operator_decision") is True
            }
            if not {"markdown_document", "pdf_document"}.issubset(required_assets):
                errors.append(f"{at}: decision briefings require markdown and pdf assets")
        boundary = data.get("decision_boundary") if isinstance(data.get("decision_boundary"), dict) else {}
        if boundary.get("briefing_is_not_source_of_truth") is not True:
            errors.append(f"{at}: briefing must not replace source of truth")
        if boundary.get("execution_not_allowed_from_briefing") is not True:
            errors.append(f"{at}: briefing must not allow execution")
        proactive = data.get("proactive_delivery") if isinstance(data.get("proactive_delivery"), dict) else {}
        if proactive.get("push_required") is not True or proactive.get("operator_polling_required") is not False:
            errors.append(f"{at}: briefing must be pushed proactively without operator polling")
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("summary_only") is not False:
            errors.append(f"{at}: operator_briefing_package summary_only must be false")
        if acceptance.get("execution_allowed") is not False:
            errors.append(f"{at}: operator_briefing_package must not allow execution")
    if data.get("record_type") == "outcome_contract":
        reason = public_artifact_ref_error(data.get("source_ledger_ref"))
        if reason:
            errors.append(f"{at}.source_ledger_ref: {reason}")
        reason = public_artifact_ref_error(data.get("operator_understanding_confirmation_ref"))
        if reason:
            errors.append(f"{at}.operator_understanding_confirmation_ref: {reason}")
        source_signal = data.get("source_signal") if isinstance(data.get("source_signal"), dict) else {}
        signal_ref = str(source_signal.get("signal_ref_public_safe") or "").strip()
        reason = public_artifact_ref_error(signal_ref)
        if reason:
            errors.append(f"{at}.source_signal.signal_ref_public_safe: {reason}")
        route_class = str(source_signal.get("route_class") or "").strip()
        request_type = str(source_signal.get("request_type") or "").strip()
        signal_type = str(source_signal.get("signal_type") or "").strip()
        allowed_request_types = UNIVERSAL_SIGNAL_ROUTE_REQUEST_TYPES.get(route_class)
        if allowed_request_types and request_type and request_type not in allowed_request_types:
            errors.append(
                f"{at}: outcome_contract.source_signal.request_type is not valid "
                f"for route_class {route_class}: {request_type}"
            )
        allowed_signal_types = UNIVERSAL_SIGNAL_ROUTE_SIGNAL_TYPES.get(route_class)
        if allowed_signal_types and signal_type and signal_type not in allowed_signal_types:
            errors.append(
                f"{at}: outcome_contract.source_signal.signal_type is not valid "
                f"for route_class {route_class}: {signal_type}"
            )
        for field in ("evidence_refs", "open_questions", "assumptions", "human_questions"):
            values = data.get(field) if isinstance(data.get(field), list) else []
            for index, value in enumerate(values):
                if field == "evidence_refs":
                    reason = public_artifact_ref_error(value)
                    if reason:
                        errors.append(f"{at}.{field}[{index}]: {reason}")
                elif PRIVATE_MARKERS.search(str(value or "")):
                    errors.append(f"{at}.{field}[{index}]: private local or runtime marker")
        blocking_rules = data.get("blocking_rules") if isinstance(data.get("blocking_rules"), dict) else {}
        for field in (
            "source_ledger_required",
            "execution_blocked_until_required_artifacts_pass",
            "raw_private_evidence_must_stay_external",
            "human_gate_only_for_authority_access_risk_or_preference",
        ):
            if blocking_rules.get(field) is not True:
                errors.append(f"{at}.blocking_rules.{field} must be true")
        if not isinstance(blocking_rules.get("product_sot_blocked_until_outcome_reviewed"), bool):
            errors.append(f"{at}.blocking_rules.product_sot_blocked_until_outcome_reviewed must be boolean")
        if source_signal.get("needs_product_sot") is True:
            understanding_ref = str(data.get("operator_understanding_confirmation_ref") or "").strip()
            if not understanding_ref:
                errors.append(f"{at}: outcome_contract requires operator_understanding_confirmation_ref before Product SOT")
            if understanding_ref.startswith("pending/"):
                errors.append(f"{at}: outcome_contract operator_understanding_confirmation_ref is still pending")
            if blocking_rules.get("operator_understanding_confirmation_required") is not True:
                errors.append(f"{at}: outcome_contract must require operator understanding confirmation when Product SOT is required")
        handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else {}
        next_worker = str(handoff.get("next_worker") or "").strip()
        if handoff.get("factory_owned_next_step") is not True:
            errors.append(f"{at}: outcome_contract.handoff.factory_owned_next_step must be true")
        if next_worker and next_worker not in public_worker_ids():
            errors.append(f"{at}.handoff.next_worker must be a registered worker: {next_worker}")
        boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
        if boundary.get("public_safe_refs_only") is not True:
            errors.append(f"{at}: outcome_contract requires public_safe_refs_only=true")
        if boundary.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: outcome_contract must not embed raw private evidence")
        if boundary.get("private_context_retained_outside_public_repo") is not True:
            errors.append(f"{at}: outcome_contract private context must stay outside the public repo")
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("outcome_contract_created") is not True:
            errors.append(f"{at}: outcome_contract acceptance.outcome_contract_created must be true")
        if acceptance.get("product_sot_generated") is not False:
            errors.append(f"{at}: outcome_contract must not claim Product SOT was generated")
        if acceptance.get("execution_allowed") is not False:
            errors.append(f"{at}: outcome_contract acceptance.execution_allowed must be false")
        for index, ref in enumerate(acceptance.get("evidence_refs", []) if isinstance(acceptance.get("evidence_refs"), list) else []):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.acceptance.evidence_refs[{index}]: {reason}")
    if data.get("record_type") == "product_sot":
        for field in ("outcome_contract_ref", "source_ledger_ref", "operator_understanding_confirmation_ref", "full_product_sot_scope_coverage_ref"):
            reason = public_artifact_ref_error(data.get(field))
            if reason:
                errors.append(f"{at}.{field}: {reason}")
        understanding_ref = str(data.get("operator_understanding_confirmation_ref") or "").strip()
        if not understanding_ref:
            errors.append(f"{at}: product_sot requires operator_understanding_confirmation_ref")
        if understanding_ref.startswith("pending/"):
            errors.append(f"{at}: product_sot operator_understanding_confirmation_ref is still pending")
        source_signal = data.get("source_signal") if isinstance(data.get("source_signal"), dict) else {}
        signal_ref = str(source_signal.get("signal_ref_public_safe") or "").strip()
        reason = public_artifact_ref_error(signal_ref)
        if reason:
            errors.append(f"{at}.source_signal.signal_ref_public_safe: {reason}")
        for field in (
            "scope_in",
            "scope_out",
            "risks",
            "data_and_metrics",
            "dependencies",
            "access_and_capabilities",
            "compliance_privacy",
            "operations_expected",
            "success_criteria",
            "open_decisions",
            "research_confirmations",
        ):
            values = data.get(field) if isinstance(data.get(field), list) else []
            for index, value in enumerate(values):
                if PRIVATE_MARKERS.search(str(value or "")):
                    errors.append(f"{at}.{field}[{index}]: private local or runtime marker")
        for field in ("evidence_refs", "research_decision_refs"):
            values = data.get(field) if isinstance(data.get(field), list) else []
            for index, value in enumerate(values):
                reason = public_artifact_ref_error(value)
                if reason:
                    errors.append(f"{at}.{field}[{index}]: {reason}")
        requirements = data.get("requirement_graph") if isinstance(data.get("requirement_graph"), list) else []
        if not requirements:
            errors.append(f"{at}: product_sot requires typed requirement_graph")
        for req_index, requirement in enumerate(requirements):
            if not isinstance(requirement, dict):
                continue
            for field in ("source_refs", "evidence_refs"):
                refs = requirement.get(field) if isinstance(requirement.get(field), list) else []
                for ref_index, ref in enumerate(refs):
                    reason = public_artifact_ref_error(ref)
                    if reason:
                        errors.append(f"{at}.requirement_graph[{req_index}].{field}[{ref_index}]: {reason}")
            if requirement.get("decision_state") in {"blocked", "open_decision"} and not str(requirement.get("blocker_id") or "").strip():
                errors.append(f"{at}.requirement_graph[{req_index}]: blocked/open decision requires blocker_id")
        blocking_rules = data.get("blocking_rules") if isinstance(data.get("blocking_rules"), dict) else {}
        for field in (
            "outcome_contract_required",
            "operator_understanding_confirmation_required",
            "full_scope_coverage_required",
            "method_contract_required",
            "execution_blocked_until_required_artifacts_pass",
            "raw_private_evidence_must_stay_external",
            "human_gate_only_for_authority_access_risk_or_preference",
        ):
            if blocking_rules.get(field) is not True:
                errors.append(f"{at}.blocking_rules.{field} must be true")
        handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else {}
        if handoff.get("next_artifact") != "full_product_sot_scope_coverage":
            errors.append(f"{at}.handoff.next_artifact must be full_product_sot_scope_coverage")
        if handoff.get("factory_owned_next_step") is not True:
            errors.append(f"{at}: product_sot.handoff.factory_owned_next_step must be true")
        next_worker = str(handoff.get("next_worker") or "").strip()
        if next_worker and next_worker not in public_worker_ids():
            errors.append(f"{at}.handoff.next_worker must be a registered worker: {next_worker}")
        boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
        if boundary.get("public_safe_refs_only") is not True:
            errors.append(f"{at}: product_sot requires public_safe_refs_only=true")
        if boundary.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: product_sot must not embed raw private evidence")
        if boundary.get("private_context_retained_outside_public_repo") is not True:
            errors.append(f"{at}: product_sot private context must stay outside the public repo")
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("product_sot_created") is not True:
            errors.append(f"{at}: product_sot acceptance.product_sot_created must be true")
        if acceptance.get("execution_allowed") is not False:
            errors.append(f"{at}: product_sot acceptance.execution_allowed must be false")
        for index, ref in enumerate(acceptance.get("evidence_refs", []) if isinstance(acceptance.get("evidence_refs"), list) else []):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.acceptance.evidence_refs[{index}]: {reason}")
    if data.get("record_type") == "full_product_sot_scope_coverage":
        reason = public_artifact_ref_error(data.get("product_sot_ref"))
        if reason:
            errors.append(f"{at}.product_sot_ref: {reason}")
        for field in ("coverage_policy", "completion_rule"):
            if PRIVATE_MARKERS.search(str(data.get(field) or "")):
                errors.append(f"{at}.{field}: private local or runtime marker")
        source_claims = data.get("source_claim_resolution") if isinstance(data.get("source_claim_resolution"), list) else []
        if not source_claims:
            errors.append(f"{at}: full_product_sot_scope_coverage requires source_claim_resolution")
        for index, item in enumerate(source_claims):
            if not isinstance(item, dict):
                continue
            for field in ("claim_ref", "authority_ref"):
                reason = public_artifact_ref_error(item.get(field))
                if reason:
                    errors.append(f"{at}.source_claim_resolution[{index}].{field}: {reason}")
            if PRIVATE_MARKERS.search(str(item.get("rationale") or "")):
                errors.append(f"{at}.source_claim_resolution[{index}].rationale: private local or runtime marker")
        requirements = data.get("requirement_coverage") if isinstance(data.get("requirement_coverage"), list) else []
        if not requirements:
            errors.append(f"{at}: full_product_sot_scope_coverage requires requirement_coverage")
        seen_requirements: set[str] = set()
        for index, item in enumerate(requirements):
            if not isinstance(item, dict):
                continue
            requirement_ref = str(item.get("requirement_ref") or "").strip()
            if requirement_ref:
                if requirement_ref in seen_requirements:
                    errors.append(f"{at}.requirement_coverage[{index}].requirement_ref is duplicated")
                seen_requirements.add(requirement_ref)
                reason = public_artifact_ref_error(requirement_ref)
                if reason:
                    errors.append(f"{at}.requirement_coverage[{index}].requirement_ref: {reason}")
            blocker_id = str(item.get("blocker_id") or "").strip()
            if item.get("status") in {"blocked", "human_decision_required"} and not blocker_id:
                errors.append(f"{at}.requirement_coverage[{index}]: blocked/human decision requires blocker_id")
            if blocker_id:
                reason = public_artifact_ref_error(blocker_id)
                if reason:
                    errors.append(f"{at}.requirement_coverage[{index}].blocker_id: {reason}")
            owner = str(item.get("owner") or "").strip()
            if owner and owner not in public_worker_ids():
                errors.append(f"{at}.requirement_coverage[{index}].owner must be a registered worker: {owner}")
            for field in ("work_unit_refs", "evidence_refs"):
                refs = item.get(field) if isinstance(item.get(field), list) else []
                for ref_index, ref in enumerate(refs):
                    reason = public_artifact_ref_error(ref)
                    if reason:
                        errors.append(f"{at}.requirement_coverage[{index}].{field}[{ref_index}]: {reason}")
            if PRIVATE_MARKERS.search(str(item.get("next_action") or "")):
                errors.append(f"{at}.requirement_coverage[{index}].next_action: private local or runtime marker")
        slice_policy = data.get("slice_policy") if isinstance(data.get("slice_policy"), dict) else {}
        if slice_policy.get("scope_reduction_forbidden") is not True:
            errors.append(f"{at}.slice_policy.scope_reduction_forbidden must be true")
        if slice_policy.get("slices_are_order_only") is not True:
            errors.append(f"{at}.slice_policy.slices_are_order_only must be true")
        for index, ref in enumerate(data.get("evidence_refs", []) if isinstance(data.get("evidence_refs"), list) else []):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.evidence_refs[{index}]: {reason}")
        blocking_rules = data.get("blocking_rules") if isinstance(data.get("blocking_rules"), dict) else {}
        for field in (
            "product_sot_required",
            "every_requirement_accounted",
            "scope_reduction_forbidden",
            "execution_blocked_until_method_readiness_and_gates_pass",
            "raw_private_evidence_must_stay_external",
        ):
            if blocking_rules.get(field) is not True:
                errors.append(f"{at}.blocking_rules.{field} must be true")
        handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else {}
        if handoff.get("next_artifact") != "method_contract":
            errors.append(f"{at}.handoff.next_artifact must be method_contract")
        if handoff.get("factory_owned_next_step") is not True:
            errors.append(f"{at}: full_product_sot_scope_coverage.handoff.factory_owned_next_step must be true")
        next_worker = str(handoff.get("next_worker") or "").strip()
        if next_worker and next_worker not in public_worker_ids():
            errors.append(f"{at}.handoff.next_worker must be a registered worker: {next_worker}")
        boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
        if boundary.get("public_safe_refs_only") is not True:
            errors.append(f"{at}: full_product_sot_scope_coverage requires public_safe_refs_only=true")
        if boundary.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: full_product_sot_scope_coverage must not embed raw private evidence")
        if boundary.get("private_context_retained_outside_public_repo") is not True:
            errors.append(f"{at}: full_product_sot_scope_coverage private context must stay outside the public repo")
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("full_scope_coverage_created") is not True:
            errors.append(f"{at}: full_product_sot_scope_coverage acceptance.full_scope_coverage_created must be true")
        if acceptance.get("execution_allowed") is not False:
            errors.append(f"{at}: full_product_sot_scope_coverage acceptance.execution_allowed must be false")
        if acceptance.get("scope_reduction_detected") is not False:
            errors.append(f"{at}: full_product_sot_scope_coverage acceptance.scope_reduction_detected must be false")
        if acceptance.get("requirements_accounted") != len(requirements):
            errors.append(f"{at}: full_product_sot_scope_coverage acceptance.requirements_accounted must match requirement_coverage length")
        for index, ref in enumerate(acceptance.get("evidence_refs", []) if isinstance(acceptance.get("evidence_refs"), list) else []):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.acceptance.evidence_refs[{index}]: {reason}")
    if data.get("record_type") == "method_contract":
        reason = public_artifact_ref_error(data.get("full_product_sot_scope_coverage_ref"))
        if reason:
            errors.append(f"{at}.full_product_sot_scope_coverage_ref: {reason}")
        if str(data.get("canonical_scope_source") or "").strip().lower() not in {
            "approved product sot",
            "product_sot",
            "product sot",
        }:
            errors.append(f"{at}.canonical_scope_source must be approved Product SOT")
        required_factory_artifacts = set(data.get("required_factory_artifacts") if isinstance(data.get("required_factory_artifacts"), list) else [])
        for artifact in ("full_product_sot_scope_coverage", "product_creation_plan", "product_implementation_readiness"):
            if artifact not in required_factory_artifacts:
                errors.append(f"{at}.required_factory_artifacts must include {artifact}")
        matrix = data.get("engineering_method_matrix") if isinstance(data.get("engineering_method_matrix"), list) else []
        if not matrix:
            errors.append(f"{at}.engineering_method_matrix is required")
        for index, item in enumerate(matrix):
            if not isinstance(item, dict):
                continue
            for field in ("surface_or_component", "methods", "reason", "required_artifacts", "evidence_required"):
                if not item.get(field):
                    errors.append(f"{at}.engineering_method_matrix[{index}].{field} is required")
            for field in ("surface_or_component", "reason"):
                if PRIVATE_MARKERS.search(str(item.get(field) or "")):
                    errors.append(f"{at}.engineering_method_matrix[{index}].{field}: private local or runtime marker")
        slice_policy = data.get("slice_execution_policy") if isinstance(data.get("slice_execution_policy"), dict) else {}
        if slice_policy.get("slices_are_execution_units_only") is not True:
            errors.append(f"{at}.slice_execution_policy.slices_are_execution_units_only must be true")
        if slice_policy.get("canonical_scope_must_not_shrink") is not True:
            errors.append(f"{at}.slice_execution_policy.canonical_scope_must_not_shrink must be true")
        if not (data.get("selected_methods") if isinstance(data.get("selected_methods"), list) else []):
            errors.append(f"{at}.selected_methods must be non-empty")
        for field in ("required_workers", "reviewers"):
            workers = data.get(field) if isinstance(data.get(field), list) else []
            for index, worker in enumerate(workers):
                if str(worker or "").strip() not in public_worker_ids():
                    errors.append(f"{at}.{field}[{index}] must be a registered worker: {worker}")
        for field in ("why_this_method", "production_route_decision", "authority_limit"):
            if PRIVATE_MARKERS.search(str(data.get(field) or "")):
                errors.append(f"{at}.{field}: private local or runtime marker")
        for index, value in enumerate(data.get("evidence_requirements", []) if isinstance(data.get("evidence_requirements"), list) else []):
            if PRIVATE_MARKERS.search(str(value or "")):
                errors.append(f"{at}.evidence_requirements[{index}]: private local or runtime marker")
        blocking_rules = data.get("blocking_rules") if isinstance(data.get("blocking_rules"), dict) else {}
        for field in (
            "full_scope_coverage_required",
            "product_creation_plan_required",
            "execution_blocked_until_ready_gate",
            "raw_private_evidence_must_stay_external",
            "operator_must_not_choose_internal_method",
        ):
            if blocking_rules.get(field) is not True:
                errors.append(f"{at}.blocking_rules.{field} must be true")
        handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else {}
        if handoff.get("next_artifact") != "product_creation_plan":
            errors.append(f"{at}.handoff.next_artifact must be product_creation_plan")
        if handoff.get("factory_owned_next_step") is not True:
            errors.append(f"{at}: method_contract.handoff.factory_owned_next_step must be true")
        next_worker = str(handoff.get("next_worker") or "").strip()
        if next_worker and next_worker not in public_worker_ids():
            errors.append(f"{at}.handoff.next_worker must be a registered worker: {next_worker}")
        boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
        if boundary.get("public_safe_refs_only") is not True:
            errors.append(f"{at}: method_contract requires public_safe_refs_only=true")
        if boundary.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: method_contract must not embed raw private evidence")
        if boundary.get("private_context_retained_outside_public_repo") is not True:
            errors.append(f"{at}: method_contract private context must stay outside the public repo")
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("method_contract_created") is not True:
            errors.append(f"{at}: method_contract acceptance.method_contract_created must be true")
        if acceptance.get("execution_allowed") is not False:
            errors.append(f"{at}: method_contract acceptance.execution_allowed must be false")
        if acceptance.get("selected_method_is_factory_owned") is not True:
            errors.append(f"{at}: method_contract acceptance.selected_method_is_factory_owned must be true")
        if acceptance.get("scope_reduction_detected") is not False:
            errors.append(f"{at}: method_contract acceptance.scope_reduction_detected must be false")
        for index, ref in enumerate(acceptance.get("evidence_refs", []) if isinstance(acceptance.get("evidence_refs"), list) else []):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.acceptance.evidence_refs[{index}]: {reason}")
    if data.get("record_type") == "product_creation_plan":
        for field in ("product_sot_ref", "method_contract_ref", "product_delivery_quality_profile_ref"):
            reason = public_artifact_ref_error(data.get(field))
            if reason:
                errors.append(f"{at}.{field}: {reason}")
        if data.get("complete_product_required") is not True:
            errors.append(f"{at}.complete_product_required must be true")
        for field in (
            "complete_product_scope",
            "production_readiness_scope",
            "release_promotion_ladder_refs",
            "complete_product_done_criteria",
            "slice_done_criteria",
            "stop_conditions",
            "evidence_refs",
        ):
            if not (data.get(field) if isinstance(data.get(field), list) else []):
                errors.append(f"{at}.{field} must be non-empty")
        work_units = data.get("work_units") if isinstance(data.get("work_units"), list) else []
        if not work_units:
            errors.append(f"{at}.work_units must be non-empty")
        unit_ids: set[str] = set()
        for index, unit in enumerate(work_units):
            if not isinstance(unit, dict):
                continue
            unit_id = str(unit.get("unit_id") or "").strip()
            if not unit_id:
                errors.append(f"{at}.work_units[{index}].unit_id is required")
            elif unit_id in unit_ids:
                errors.append(f"{at}.work_units[{index}].unit_id must be unique: {unit_id}")
            else:
                unit_ids.add(unit_id)
            for field in (
                "product_sot_requirement_refs",
                "scope_in",
                "scope_out",
                "verification",
                "proof_ids_required",
                "capability_profile_refs",
                "ready_rules",
                "blocked_when",
                "done_rules",
                "stop_conditions",
            ):
                if not (unit.get(field) if isinstance(unit.get(field), list) else []):
                    errors.append(f"{at}.work_units[{index}].{field} must be non-empty")
            for field in ("owner_worker", "reviewer_role", "expected_result"):
                if not str(unit.get(field) or "").strip():
                    errors.append(f"{at}.work_units[{index}].{field} is required")
            owner = str(unit.get("owner_worker") or "").strip()
            reviewer = str(unit.get("reviewer_role") or "").strip()
            blocker_owner = str(unit.get("blocker_owner") or "").strip()
            if owner and owner not in public_worker_ids():
                errors.append(f"{at}.work_units[{index}].owner_worker must be a registered worker: {owner}")
            if reviewer and reviewer not in public_worker_ids():
                errors.append(f"{at}.work_units[{index}].reviewer_role must be a registered worker: {reviewer}")
            if blocker_owner and blocker_owner not in public_worker_ids():
                errors.append(f"{at}.work_units[{index}].blocker_owner must be a registered worker: {blocker_owner}")
            if str(unit.get("status") or "").strip() == "blocked":
                for field in ("blocker_id", "blocker_owner", "next_action"):
                    if not str(unit.get(field) or "").strip():
                        errors.append(f"{at}.work_units[{index}].{field} is required when status is blocked")
            for ref_field in ("product_sot_requirement_refs", "capability_profile_refs"):
                refs = unit.get(ref_field) if isinstance(unit.get(ref_field), list) else []
                for ref_index, ref in enumerate(refs):
                    reason = public_artifact_ref_error(ref)
                    if reason:
                        errors.append(f"{at}.work_units[{index}].{ref_field}[{ref_index}]: {reason}")
        execution_order = data.get("execution_order") if isinstance(data.get("execution_order"), list) else []
        missing_order_refs = [unit_id for unit_id in execution_order if unit_id not in unit_ids]
        if missing_order_refs:
            errors.append(f"{at}.execution_order references unknown work_units: {', '.join(missing_order_refs)}")
        runtime_boundary = data.get("runtime_boundary") if isinstance(data.get("runtime_boundary"), dict) else {}
        if runtime_boundary.get("state_role") != "planning_only":
            errors.append(f"{at}.runtime_boundary.state_role must be planning_only")
        if runtime_boundary.get("runtime_authority") != "hermes_kanban":
            errors.append(f"{at}.runtime_boundary.runtime_authority must be hermes_kanban")
        if runtime_boundary.get("local_state_authority") is not False:
            errors.append(f"{at}.runtime_boundary.local_state_authority must be false")
        blocking_rules = data.get("blocking_rules") if isinstance(data.get("blocking_rules"), dict) else {}
        for field in (
            "product_sot_required",
            "method_contract_required",
            "product_implementation_readiness_required",
            "execution_blocked_until_ready_gate",
            "raw_private_evidence_must_stay_external",
        ):
            if blocking_rules.get(field) is not True:
                errors.append(f"{at}.blocking_rules.{field} must be true")
        handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else {}
        if handoff.get("next_artifact") != "product_implementation_readiness":
            errors.append(f"{at}.handoff.next_artifact must be product_implementation_readiness")
        if handoff.get("factory_owned_next_step") is not True:
            errors.append(f"{at}: product_creation_plan.handoff.factory_owned_next_step must be true")
        next_worker = str(handoff.get("next_worker") or "").strip()
        if next_worker and next_worker not in public_worker_ids():
            errors.append(f"{at}.handoff.next_worker must be a registered worker: {next_worker}")
        boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
        if boundary.get("public_safe_refs_only") is not True:
            errors.append(f"{at}: product_creation_plan requires public_safe_refs_only=true")
        if boundary.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: product_creation_plan must not embed raw private evidence")
        if boundary.get("private_context_retained_outside_public_repo") is not True:
            errors.append(f"{at}: product_creation_plan private context must stay outside the public repo")
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("product_creation_plan_created") is not True:
            errors.append(f"{at}: product_creation_plan acceptance.product_creation_plan_created must be true")
        if acceptance.get("execution_allowed") is not False:
            errors.append(f"{at}: product_creation_plan acceptance.execution_allowed must be false")
        if acceptance.get("scope_reduction_detected") is not False:
            errors.append(f"{at}: product_creation_plan acceptance.scope_reduction_detected must be false")
        if acceptance.get("work_units_accounted") != len(work_units):
            errors.append(f"{at}: product_creation_plan acceptance.work_units_accounted must match work_units length")
        for index, ref in enumerate(acceptance.get("evidence_refs", []) if isinstance(acceptance.get("evidence_refs"), list) else []):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.acceptance.evidence_refs[{index}]: {reason}")
    if data.get("record_type") == "product_implementation_readiness":
        for field in ("product_sot_ref", "method_contract_ref", "product_creation_plan_ref", "product_delivery_quality_profile_ref"):
            reason = public_artifact_ref_error(data.get(field))
            if reason:
                errors.append(f"{at}.{field}: {reason}")
        result = str(data.get("artifact_alignment_result") or "").strip().upper()
        if result not in {"PASS", "CONCERNS", "FAIL", "BLOCKED"}:
            errors.append(f"{at}.artifact_alignment_result must be PASS, CONCERNS, FAIL or BLOCKED")
        for field in (
            "product_delivery_quality_profile_trace",
            "requirements_trace",
            "proof_coverage",
            "allowed_next_actions",
            "forbidden_next_actions",
            "evidence_refs",
        ):
            if not (data.get(field) if isinstance(data.get(field), list) else []):
                errors.append(f"{at}.{field} must be non-empty")
        ready_units = [str(item or "").strip() for item in data.get("ready_work_units", []) if isinstance(data.get("ready_work_units"), list)]
        blocked_units = [str(item or "").strip() for item in data.get("blocked_work_units", []) if isinstance(data.get("blocked_work_units"), list)]
        overlapping_units = sorted(set(ready_units).intersection(blocked_units))
        if overlapping_units:
            errors.append(f"{at}: ready and blocked work units overlap: {', '.join(overlapping_units)}")
        if result == "PASS" and not ready_units:
            errors.append(f"{at}: PASS requires ready_work_units")
        if result in {"FAIL", "BLOCKED"} and ready_units:
            errors.append(f"{at}: FAIL/BLOCKED must not expose ready_work_units")
        if result == "BLOCKED" and not blocked_units:
            errors.append(f"{at}: BLOCKED requires blocked_work_units")
        concerns = data.get("concern_items") if isinstance(data.get("concern_items"), list) else []
        if result == "CONCERNS" and not concerns:
            errors.append(f"{at}: CONCERNS requires concern_items")
        for index, concern in enumerate(concerns):
            if not isinstance(concern, dict):
                continue
            for field in (
                "concern_id",
                "severity",
                "owner",
                "impact",
                "allowed_actions",
                "forbidden_actions",
                "allowed_ready_work_units",
                "expiry",
                "next_action",
                "evidence_refs",
            ):
                if not concern.get(field):
                    errors.append(f"{at}.concern_items[{index}].{field} is required")
            allowed_units = [str(item or "").strip() for item in concern.get("allowed_ready_work_units", []) if isinstance(concern.get("allowed_ready_work_units"), list)]
            missing_ready_units = [unit for unit in ready_units if unit not in allowed_units]
            if missing_ready_units:
                errors.append(f"{at}.concern_items[{index}].allowed_ready_work_units must cover ready_work_units: {', '.join(missing_ready_units)}")
            for ref_index, ref in enumerate(concern.get("evidence_refs", []) if isinstance(concern.get("evidence_refs"), list) else []):
                reason = public_artifact_ref_error(ref)
                if reason:
                    errors.append(f"{at}.concern_items[{index}].evidence_refs[{ref_index}]: {reason}")
        for index, item in enumerate(data.get("requirements_trace", []) if isinstance(data.get("requirements_trace"), list) else []):
            if not isinstance(item, dict):
                continue
            for field in ("requirement_ref", "work_unit_refs", "proof_refs", "status"):
                if not item.get(field):
                    errors.append(f"{at}.requirements_trace[{index}].{field} is required")
        blocking_rules = data.get("blocking_rules") if isinstance(data.get("blocking_rules"), dict) else {}
        for field in (
            "product_creation_plan_required",
            "blocked_or_failed_readiness_blocks_execution",
            "concerns_allow_only_ready_work_units",
            "complete_product_claim_forbidden_until_all_scope_reconciled",
            "raw_private_evidence_must_stay_external",
        ):
            if blocking_rules.get(field) is not True:
                errors.append(f"{at}.blocking_rules.{field} must be true")
        handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else {}
        if handoff.get("factory_owned_next_step") is not True:
            errors.append(f"{at}: product_implementation_readiness.handoff.factory_owned_next_step must be true")
        next_worker = str(handoff.get("next_worker") or "").strip()
        if next_worker and next_worker not in public_worker_ids():
            errors.append(f"{at}.handoff.next_worker must be a registered worker: {next_worker}")
        boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
        if boundary.get("public_safe_refs_only") is not True:
            errors.append(f"{at}: product_implementation_readiness requires public_safe_refs_only=true")
        if boundary.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: product_implementation_readiness must not embed raw private evidence")
        if boundary.get("private_context_retained_outside_public_repo") is not True:
            errors.append(f"{at}: product_implementation_readiness private context must stay outside the public repo")
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("product_implementation_readiness_created") is not True:
            errors.append(f"{at}: product_implementation_readiness acceptance.product_implementation_readiness_created must be true")
        material_allowed = acceptance.get("material_execution_allowed")
        scope = str(acceptance.get("allowed_execution_scope") or "").strip()
        if result in {"FAIL", "BLOCKED"}:
            if material_allowed is not False:
                errors.append(f"{at}: FAIL/BLOCKED requires material_execution_allowed=false")
            if scope != "none":
                errors.append(f"{at}: FAIL/BLOCKED requires allowed_execution_scope=none")
        if result == "CONCERNS":
            if material_allowed is not bool(ready_units):
                errors.append(f"{at}: CONCERNS material_execution_allowed must match ready_work_units")
            if ready_units and scope != "ready_work_units_only":
                errors.append(f"{at}: CONCERNS with ready units requires allowed_execution_scope=ready_work_units_only")
        if result == "PASS" and material_allowed is not True:
            errors.append(f"{at}: PASS requires material_execution_allowed=true")
        if acceptance.get("complete_product_claim_allowed") is not False:
            errors.append(f"{at}: complete_product_claim_allowed must be false")
        for index, ref in enumerate(acceptance.get("evidence_refs", []) if isinstance(acceptance.get("evidence_refs"), list) else []):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.acceptance.evidence_refs[{index}]: {reason}")
    if data.get("record_type") == "ready_work_unit_packet_manifest":
        for field in ("product_creation_plan_ref", "product_implementation_readiness_ref"):
            reason = public_artifact_ref_error(data.get(field))
            if reason:
                errors.append(f"{at}.{field}: {reason}")
        if data.get("complete_product_claim_allowed") is not False:
            errors.append(f"{at}: ready_work_unit_packet_manifest cannot allow complete-product claim")
        runtime = data.get("runtime_boundary") if isinstance(data.get("runtime_boundary"), dict) else {}
        if runtime.get("live_hermes_mutated") is not False:
            errors.append(f"{at}: ready_work_unit_packet_manifest must not claim live Hermes mutation")
        if runtime.get("hermes_materialization_requires_gate") is not True:
            errors.append(f"{at}: ready_work_unit_packet_manifest requires Hermes materialization gate")
        packets = data.get("packets") if isinstance(data.get("packets"), list) else []
        acceptance = data.get("acceptance") if isinstance(data.get("acceptance"), dict) else {}
        if acceptance.get("packet_count") != len(packets):
            errors.append(f"{at}: ready_work_unit_packet_manifest acceptance.packet_count must match packets length")
        if acceptance.get("complete_product_claim_allowed") is not False:
            errors.append(f"{at}: ready_work_unit_packet_manifest acceptance cannot allow complete-product claim")
        if acceptance.get("live_hermes_mutated") is not False:
            errors.append(f"{at}: ready_work_unit_packet_manifest acceptance must not claim live Hermes mutation")
        packet_ids: list[str] = []
        work_unit_ids: list[str] = []
        for index, packet in enumerate(packets):
            if not isinstance(packet, dict):
                errors.append(f"{at}.packets[{index}]: expected object")
                continue
            packet_id = str(packet.get("packet_id") or "").strip()
            work_unit_id = str(packet.get("work_unit_id") or "").strip()
            if packet_id:
                packet_ids.append(packet_id)
            if work_unit_id:
                work_unit_ids.append(work_unit_id)
            owner = str(packet.get("owner_worker") or "").strip()
            if owner and owner not in public_worker_ids():
                errors.append(f"{at}.packets[{index}].owner_worker must be a registered worker: {owner}")
            receipt = packet.get("receipt_five_contract") if isinstance(packet.get("receipt_five_contract"), dict) else {}
            if receipt.get("complete_product_claim_allowed") is not False:
                errors.append(f"{at}.packets[{index}].receipt_five_contract cannot allow complete-product claim")
            materialization = packet.get("hermes_materialization") if isinstance(packet.get("hermes_materialization"), dict) else {}
            if materialization.get("live_hermes_mutated") is not False:
                errors.append(f"{at}.packets[{index}].hermes_materialization must not claim live Hermes mutation")
            if materialization.get("dispatch_allowed_without_runtime_gate") is not False:
                errors.append(f"{at}.packets[{index}].hermes_materialization cannot dispatch without runtime gate")
            boundary = packet.get("public_private_boundary") if isinstance(packet.get("public_private_boundary"), dict) else {}
            if boundary.get("public_safe_refs_only") is not True:
                errors.append(f"{at}.packets[{index}] requires public_safe_refs_only=true")
            if boundary.get("raw_private_evidence_embedded") is not False:
                errors.append(f"{at}.packets[{index}] must not embed raw private evidence")
        duplicate_packets = sorted({packet_id for packet_id in packet_ids if packet_ids.count(packet_id) > 1})
        if duplicate_packets:
            errors.append(f"{at}: duplicate ready work-unit packet ids: {', '.join(duplicate_packets)}")
        duplicate_units = sorted({unit_id for unit_id in work_unit_ids if work_unit_ids.count(unit_id) > 1})
        if duplicate_units:
            errors.append(f"{at}: duplicate ready work-unit ids: {', '.join(duplicate_units)}")
        boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
        if boundary.get("public_safe_refs_only") is not True:
            errors.append(f"{at}: ready_work_unit_packet_manifest requires public_safe_refs_only=true")
        if boundary.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: ready_work_unit_packet_manifest must not embed raw private evidence")
        for index, ref in enumerate(data.get("evidence_refs", []) if isinstance(data.get("evidence_refs"), list) else []):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.evidence_refs[{index}]: {reason}")
        for index, ref in enumerate(acceptance.get("evidence_refs", []) if isinstance(acceptance.get("evidence_refs"), list) else []):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.acceptance.evidence_refs[{index}]: {reason}")
    if data.get("record_type") == "factory_readiness_scorecard":
        errors.extend(validate_factory_readiness_scorecard_domain(data, at))
    if data.get("record_type") == "factory_v1_completion_gate":
        errors.extend(validate_factory_v1_completion_gate_domain(data, at))
    if data.get("record_type") == "factory_automation_run_target":
        trigger = data.get("trigger") if isinstance(data.get("trigger"), dict) else {}
        target = data.get("target") if isinstance(data.get("target"), dict) else {}
        for field, ref in (
            ("trigger.trigger_ref_public_safe", trigger.get("trigger_ref_public_safe")),
            ("target.target_ref", target.get("target_ref")),
            ("runtime_target_ref", data.get("runtime_target_ref")),
            ("profile_binding_ref", data.get("profile_binding_ref")),
        ):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.{field}: {reason}")
        authority = str(data.get("authority_level") or "").strip()
        if authority in AUTOMATION_GITHUB_AUTHORITIES:
            preflight_missing = sorted(AUTOMATION_REQUIRED_SAFETY_CHECKS - normalized_check_ids(data.get("required_preflight_checks")))
            post_missing = sorted(AUTOMATION_REQUIRED_SAFETY_CHECKS - normalized_check_ids(data.get("required_post_checks")))
            if preflight_missing:
                errors.append(f"{at}: GitHub authority requires preflight checks: {', '.join(preflight_missing)}")
            if post_missing:
                errors.append(f"{at}: GitHub authority requires post checks: {', '.join(post_missing)}")
            if not text_items(data.get("human_gate_triggers")):
                errors.append(f"{at}: GitHub authority requires human_gate_triggers")
        policy = data.get("public_artifact_policy") if isinstance(data.get("public_artifact_policy"), dict) else {}
        if policy.get("public_safe_refs_only") is not True:
            errors.append(f"{at}.public_artifact_policy.public_safe_refs_only must be true")
        if policy.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}.public_artifact_policy.raw_private_evidence_embedded must be false")
        if policy.get("no_raw_screenshots_or_logs") is not True:
            errors.append(f"{at}.public_artifact_policy.no_raw_screenshots_or_logs must be true")
        if target.get("target_kind") == "external_research_track":
            forbidden_text = " ".join(text_items(data.get("forbidden_actions"))).lower()
            if "raw" not in forbidden_text or "private" not in forbidden_text:
                errors.append(f"{at}: external research automation must forbid raw/private evidence publication")
    if data.get("record_type") == "factory_automation_run_record":
        trigger = data.get("trigger_observed") if isinstance(data.get("trigger_observed"), dict) else {}
        target = data.get("target_resolved") if isinstance(data.get("target_resolved"), dict) else {}
        for field, ref in (
            ("trigger_observed.trigger_ref_public_safe", trigger.get("trigger_ref_public_safe")),
            ("target_resolved.target_ref", target.get("target_ref")),
        ):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.{field}: {reason}")
        add_public_ref_errors(data.get("evidence_refs_public_safe"), f"{at}.evidence_refs_public_safe", errors)
        add_public_ref_errors(data.get("issues_created_or_updated"), f"{at}.issues_created_or_updated", errors)
        add_public_ref_errors(data.get("prs_created_or_updated"), f"{at}.prs_created_or_updated", errors)
        checks = data.get("checks_run") if isinstance(data.get("checks_run"), list) else []
        for index, check in enumerate(checks):
            if not isinstance(check, dict):
                continue
            reason = public_artifact_ref_error(check.get("evidence_ref"))
            if reason:
                errors.append(f"{at}.checks_run[{index}].evidence_ref: {reason}")
        authority = str(data.get("authority_level") or "").strip()
        status = str(data.get("status") or "").strip().lower()
        target_kind = str(target.get("target_kind") or "").strip()
        if authority in AUTOMATION_REPO_BOUND_AUTHORITIES or target_kind in AUTOMATION_REPO_BOUND_TARGETS:
            git_state = data.get("git_state") if isinstance(data.get("git_state"), dict) else None
            if git_state is None:
                errors.append(f"{at}: repo-bound automation run requires git_state")
            elif not str(git_state.get("publication_state") or "").strip():
                errors.append(f"{at}.git_state: publication_state must distinguish local work from GitHub publication")
        if status == "completed":
            missing_post = sorted(normalized_check_ids(data.get("required_post_checks")) - passed_check_ids(checks, phase="post"))
            if missing_post:
                errors.append(f"{at}: completed automation run requires passed post checks: {', '.join(missing_post)}")
            if not data.get("completed_at"):
                errors.append(f"{at}: completed automation run requires completed_at")
            if not checks:
                errors.append(f"{at}: completed automation run requires checks_run")
            if not text_items(data.get("evidence_refs_public_safe")):
                errors.append(f"{at}: completed automation run requires evidence_refs_public_safe")
        if status in {"blocked", "failed"} and not str(data.get("blocked_reason") or "").strip():
            errors.append(f"{at}: {status} automation run requires blocked_reason")
        if authority in AUTOMATION_GITHUB_AUTHORITIES:
            missing = sorted(AUTOMATION_REQUIRED_SAFETY_CHECKS - passed_check_ids(checks))
            if missing:
                errors.append(f"{at}: GitHub authority requires passed safety checks: {', '.join(missing)}")
        if target_kind == "external_research_track":
            sources = data.get("external_research_sources") if isinstance(data.get("external_research_sources"), list) else []
            if not sources:
                errors.append(f"{at}: external research automation run requires external_research_sources")
            serialized = json.dumps(data, sort_keys=True)
            present_raw_fields = sorted(field for field in RAW_RESEARCH_FIELDS if f'"{field}"' in serialized)
            if present_raw_fields:
                errors.append(f"{at}: external research automation run must not contain raw dump fields: {', '.join(present_raw_fields)}")
            for index, source in enumerate(sources):
                if not isinstance(source, dict):
                    continue
                source_url = str(source.get("source_url") or "").strip()
                if not source_url.startswith(("https://", "http://")):
                    errors.append(f"{at}.external_research_sources[{index}].source_url must be a public URL")
                if PRIVATE_MARKERS.search(source_url):
                    errors.append(f"{at}.external_research_sources[{index}].source_url contains private marker")
                if source.get("raw_capture_embedded") is not False:
                    errors.append(f"{at}.external_research_sources[{index}].raw_capture_embedded must be false")
        policy = data.get("public_artifact_policy") if isinstance(data.get("public_artifact_policy"), dict) else {}
        if policy.get("public_safe_refs_only") is not True:
            errors.append(f"{at}.public_artifact_policy.public_safe_refs_only must be true")
        if policy.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}.public_artifact_policy.raw_private_evidence_embedded must be false")
        if policy.get("no_raw_screenshots_or_logs") is not True:
            errors.append(f"{at}.public_artifact_policy.no_raw_screenshots_or_logs must be true")
    if data.get("record_type") == "product_face_result" and data.get("reusable_for_product") is True:
        if not str(data.get("packet_ref") or "").strip():
            errors.append(f"{at}: reusable product_face_result requires packet_ref")
        if not str(data.get("project_design_system_ref") or "").strip():
            errors.append(f"{at}: reusable product_face_result requires project_design_system_ref")
        if not str(data.get("professional_design_process_ref") or "").strip():
            errors.append(f"{at}: reusable product_face_result requires professional_design_process_ref")
        for field in PRODUCT_FACE_ALIGNMENT_FIELDS:
            value = data.get(field)
            if not isinstance(value, dict) or value.get("status") != "pass":
                errors.append(f"{at}: reusable product_face_result requires {field}.status=pass")
        comparison = data.get("reference_quality_comparison")
        if isinstance(comparison, dict) and comparison.get("status") == "pass":
            if len([item for item in comparison.get("compared_source_ids") or [] if str(item).strip()]) < 3:
                errors.append(f"{at}: reusable product_face_result requires at least 3 compared reference ids")
            if comparison.get("reviewer_independent_from_implementation") is not True:
                errors.append(f"{at}: reference_quality_comparison requires independent reviewer proof")
            dimensions = comparison.get("dimensions") if isinstance(comparison.get("dimensions"), dict) else {}
            for dimension in REFERENCE_COMPARISON_DIMENSIONS:
                verdict = dimensions.get(dimension)
                if not isinstance(verdict, dict) or verdict.get("status") != "pass" or not str(verdict.get("basis") or "").strip():
                    errors.append(f"{at}: reference_quality_comparison.dimensions.{dimension} requires status=pass and basis")
    if data.get("record_type") == "professional_design_process":
        research = data.get("reference_research") if isinstance(data.get("reference_research"), dict) else {}
        sources = research.get("sources") if isinstance(research.get("sources"), list) else []
        library_searches = research.get("library_searches") if isinstance(research.get("library_searches"), list) else []
        rejected_references = research.get("rejected_references") if isinstance(research.get("rejected_references"), list) else []
        pattern_synthesis = research.get("pattern_synthesis") if isinstance(research.get("pattern_synthesis"), dict) else {}
        evidence_policy = research.get("reference_evidence_policy") if isinstance(research.get("reference_evidence_policy"), dict) else {}
        source_ids = {
            str(source.get("source_id")).strip()
            for source in sources
            if isinstance(source, dict) and str(source.get("source_id") or "").strip()
        }
        rejected_reference_ids = {
            str(rejected.get("source_id")).strip()
            for rejected in rejected_references
            if isinstance(rejected, dict) and str(rejected.get("source_id") or "").strip()
        }
        source_types: set[str] = set()
        if len(sources) < 3:
            errors.append(f"{at}: professional_design_process requires at least 3 reference sources")
        if len(library_searches) < 2:
            errors.append(f"{at}: professional_design_process requires at least 2 library searches")
        for index, search in enumerate(library_searches):
            if not isinstance(search, dict):
                errors.append(f"{at}.reference_research.library_searches[{index}]: expected object")
                continue
            for field in ("library", "library_url", "query_or_category", "searched_at"):
                if not str(search.get(field) or "").strip():
                    errors.append(f"{at}.reference_research.library_searches[{index}]: missing {field}")
            if len(search.get("selection_criteria") or []) < 2:
                errors.append(f"{at}.reference_research.library_searches[{index}]: requires at least 2 selection_criteria")
            if int(search.get("candidate_count") or 0) < 3:
                errors.append(f"{at}.reference_research.library_searches[{index}]: candidate_count must be at least 3")
            if not search.get("selected_source_ids"):
                errors.append(f"{at}.reference_research.library_searches[{index}]: selected_source_ids is required")
            if not search.get("rejected_candidate_ids"):
                errors.append(f"{at}.reference_research.library_searches[{index}]: rejected_candidate_ids is required")
            for field, declared_ids, target_name in (
                ("selected_source_ids", source_ids, "reference_research.sources"),
                ("rejected_candidate_ids", rejected_reference_ids, "reference_research.rejected_references"),
            ):
                seen: set[str] = set()
                for item_index, item_id in enumerate(str(item).strip() for item in search.get(field, []) if str(item).strip()):
                    if item_id in seen:
                        errors.append(
                            f"{at}.reference_research.library_searches[{index}].{field}: duplicate id {item_id}"
                        )
                    seen.add(item_id)
                    if item_id not in declared_ids:
                        errors.append(
                            f"{at}.reference_research.library_searches[{index}].{field}[{item_index}]: does not resolve to {target_name}: {item_id}"
                        )
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                errors.append(f"{at}.reference_research.sources[{index}]: expected object")
                continue
            source_type = str(source.get("source_type") or "").strip()
            if source_type not in REFERENCE_RESEARCH_SOURCE_TYPES:
                errors.append(f"{at}.reference_research.sources[{index}]: source_type must be a known reference type")
            else:
                source_types.add(source_type)
            for field in ("library_source", "candidate_reason", "license_or_terms_ref"):
                if not str(source.get(field) or "").strip():
                    errors.append(f"{at}.reference_research.sources[{index}]: missing {field}")
            if len(source.get("what_to_learn") or []) < 2:
                errors.append(f"{at}.reference_research.sources[{index}]: requires at least 2 what_to_learn items")
            if len(source.get("extracted_patterns") or []) < 2:
                errors.append(f"{at}.reference_research.sources[{index}]: requires at least 2 extracted_patterns")
            if len(source.get("selected_patterns") or []) < 2:
                errors.append(f"{at}.reference_research.sources[{index}]: requires at least 2 selected_patterns")
            if len(source.get("visual_dimensions_covered") or []) < 3:
                errors.append(f"{at}.reference_research.sources[{index}]: requires at least 3 visual_dimensions_covered")
            copy_policy = str(source.get("copy_policy") or "").lower()
            if copy_policy in {"copy", "blind_copy"}:
                errors.append(f"{at}.reference_research.sources[{index}]: copy_policy must not allow blind copying")
        if not (source_types & REFERENCE_RESEARCH_LIBRARY_TYPES):
            errors.append(f"{at}: professional_design_process requires a design library, component registry, site gallery or user-flow library source")
        if len(source_types) < 2:
            errors.append(f"{at}: professional_design_process requires at least 2 distinct source types")
        if len(rejected_references) < 2:
            errors.append(f"{at}: professional_design_process requires at least 2 rejected references")
        for index, rejected in enumerate(rejected_references):
            if not isinstance(rejected, dict):
                errors.append(f"{at}.reference_research.rejected_references[{index}]: expected object")
                continue
            for field in ("source_id", "source_url_or_ref", "rejection_reason"):
                if not str(rejected.get(field) or "").strip():
                    errors.append(f"{at}.reference_research.rejected_references[{index}]: missing {field}")
        for dimension in REFERENCE_COMPARISON_DIMENSIONS:
            if not str(pattern_synthesis.get(dimension) or "").strip():
                errors.append(f"{at}.reference_research.pattern_synthesis.{dimension}: required")
        for field in (
            "capture_required_before_implementation",
            "side_by_side_comparison_required_before_pass",
            "public_refs_only",
            "no_private_screenshots_in_repo",
        ):
            if evidence_policy.get(field) is not True:
                errors.append(f"{at}.reference_research.reference_evidence_policy.{field}: must be true")
        for gate_name in ("wireframe_gate", "prototype_gate", "comparative_review_gate"):
            gate = data.get(gate_name) if isinstance(data.get(gate_name), dict) else {}
            status = str(gate.get("status") or "").strip().upper()
            if status not in PROFESSIONAL_DESIGN_GATE_ALLOWED_STATUSES:
                errors.append(f"{at}: professional_design_process {gate_name}.status must be PASS, BLOCKED, NEEDS_REWORK or PENDING")
            elif status in PROFESSIONAL_DESIGN_GATE_BLOCKING_STATUSES:
                for field in PROFESSIONAL_DESIGN_BLOCKER_FIELDS:
                    if not str(gate.get(field) or "").strip():
                        errors.append(f"{at}: professional_design_process {gate_name}.{field} is required when status is {status}")
                if not gate.get("proof_refs"):
                    errors.append(f"{at}: professional_design_process {gate_name}.proof_refs is required when status is {status}")
        reviewer_role = str((data.get("comparative_review_gate") or {}).get("reviewer_role") or "").lower()
        comparative_status = str((data.get("comparative_review_gate") or {}).get("status") or "").strip().upper()
        if comparative_status == "PASS" and "independent" not in reviewer_role:
            errors.append(f"{at}: professional_design_process comparative_review_gate requires an independent reviewer")
    if data.get("record_type") == "project_design_system":
        source_contracts = data.get("source_contracts") if isinstance(data.get("source_contracts"), dict) else {}
        for field in (
            "product_experience_plan_ref",
            "product_face_packet_ref",
            "professional_design_process_ref",
            "reference_quality_packet_ref",
        ):
            reason = public_artifact_ref_error(source_contracts.get(field))
            if reason:
                errors.append(f"{at}.source_contracts.{field}: {reason}")
        tokens = data.get("tokens") if isinstance(data.get("tokens"), dict) else {}
        palette_policy = tokens.get("palette_policy") if isinstance(tokens.get("palette_policy"), dict) else {}
        if palette_policy.get("semantic_roles_required") is not True:
            errors.append(f"{at}: project_design_system requires semantic_roles_required=true")
        if palette_policy.get("not_one_hue_theme") is not True:
            errors.append(f"{at}: project_design_system requires not_one_hue_theme=true")
        if len(tokens.get("color_roles") if isinstance(tokens.get("color_roles"), list) else []) < 5:
            errors.append(f"{at}: project_design_system requires at least 5 color roles")
        if len(tokens.get("typography_roles") if isinstance(tokens.get("typography_roles"), list) else []) < 3:
            errors.append(f"{at}: project_design_system requires at least 3 typography roles")
        if len(data.get("component_contracts") if isinstance(data.get("component_contracts"), list) else []) < 3:
            errors.append(f"{at}: project_design_system requires at least 3 component contracts")
        quality = data.get("quality_bar") if isinstance(data.get("quality_bar"), dict) else {}
        for index, ref in enumerate(text_items(quality.get("reference_refs"))):
            reason = public_artifact_ref_error(ref)
            if reason:
                errors.append(f"{at}.quality_bar.reference_refs[{index}]: {reason}")
        proof = data.get("proof_contract") if isinstance(data.get("proof_contract"), dict) else {}
        if proof.get("must_be_compared_in_product_face_result") is not True:
            errors.append(f"{at}: project_design_system must require Product Face comparison")
        export = data.get("design_md_export") if isinstance(data.get("design_md_export"), dict) else {}
        if export.get("required") is not True:
            errors.append(f"{at}: project_design_system requires DESIGN.md export")
        if export.get("must_match_contract") is not True:
            errors.append(f"{at}: project_design_system DESIGN.md export must match contract")
        boundary = data.get("public_private_boundary") if isinstance(data.get("public_private_boundary"), dict) else {}
        if boundary.get("public_safe_refs_only") is not True:
            errors.append(f"{at}: project_design_system requires public_safe_refs_only=true")
        if boundary.get("raw_private_evidence_embedded") is not False:
            errors.append(f"{at}: project_design_system must not embed raw private evidence")
        if boundary.get("no_private_screenshots_in_repo") is not True:
            errors.append(f"{at}: project_design_system must not commit private screenshots")
    if data.get("record_type") == "factory_learning_proposal":
        serialized_refs = "\n".join(str(ref) for ref in data.get("source_evidence_refs", []))
        if PRIVATE_MARKERS.search(serialized_refs):
            errors.append(f"{at}: factory_learning_proposal source_evidence_refs must be public-safe")
        feedback_refs = data.get("sdlc_feedback_loop_refs") if isinstance(data.get("sdlc_feedback_loop_refs"), list) else []
        serialized_feedback_refs = "\n".join(str(ref) for ref in feedback_refs)
        if data.get("classification") != "reject" and not feedback_refs:
            errors.append(f"{at}: factory_learning_proposal requires sdlc_feedback_loop_refs for non-rejected learnback")
        if PRIVATE_MARKERS.search(serialized_feedback_refs):
            errors.append(f"{at}: factory_learning_proposal sdlc_feedback_loop_refs must be public-safe")
        validation = data.get("validation_plan") if isinstance(data.get("validation_plan"), dict) else {}
        if data.get("classification") != "reject" and validation.get("independent_review_required") is not True:
            errors.append(f"{at}: factory_learning_proposal requires independent review before activation")
        if data.get("classification") != "reject" and not str(validation.get("plan_review_ref") or "").strip():
            errors.append(f"{at}: factory_learning_proposal requires plan_review_ref")
        activation = data.get("activation_policy") if isinstance(data.get("activation_policy"), dict) else {}
        if data.get("proposed_artifact_type") in SENSITIVE_LEARNING_ARTIFACTS and activation.get("auto_activation_allowed") is True:
            errors.append(f"{at}: sensitive factory learning artifacts must not auto-activate")
        if activation.get("default_state") == "active" and activation.get("auto_activation_allowed") is True:
            errors.append(f"{at}: factory_learning_proposal must land inactive before activation")
        untrusted = data.get("untrusted_input_handling") if isinstance(data.get("untrusted_input_handling"), dict) else {}
        if data.get("source_trust") in {"external_untrusted", "mixed"}:
            if untrusted.get("reader_actor_split") is not True:
                errors.append(f"{at}: untrusted learning input requires reader_actor_split")
            if untrusted.get("privileged_actors_consume_structured_summary_only") is not True:
                errors.append(f"{at}: privileged actors must consume structured summaries only")
        tools = data.get("tool_governance") if isinstance(data.get("tool_governance"), dict) else {}
        active_tools = list(activation.get("active_tool_surfaces") or [])
        required_tools = list(tools.get("required") or [])
        if active_tools and tools.get("third_party_trust_status") in {"untrusted", "unknown"}:
            errors.append(f"{at}: active tool surfaces require reviewed trust status")
        if required_tools and not str(tools.get("supply_chain_review") or "").strip():
            errors.append(f"{at}: required tools require supply_chain_review")
    if data.get("record_type") == "execution_learnback_record":
        feedback_refs = []
        feedback_ref = str(data.get("sdlc_feedback_loop_ref") or "").strip()
        if feedback_ref:
            feedback_refs.append(feedback_ref)
        if isinstance(data.get("sdlc_feedback_loop_refs"), list):
            feedback_refs.extend(str(ref) for ref in data.get("sdlc_feedback_loop_refs", []))
        serialized_feedback_refs = "\n".join(feedback_refs)
        if data.get("method_version") == "OVERKILL_VFINAL" and not feedback_refs:
            errors.append(f"{at}: execution_learnback_record requires sdlc_feedback_loop_ref(s) for OVERKILL_VFINAL learnback")
        if PRIVATE_MARKERS.search(serialized_feedback_refs):
            errors.append(f"{at}: execution_learnback_record sdlc_feedback_loop_ref(s) must be public-safe")
    if data.get("record_type") == "factory_improvement_issue_candidate":
        feedback_refs = data.get("sdlc_feedback_loop_refs") if isinstance(data.get("sdlc_feedback_loop_refs"), list) else []
        serialized_feedback_refs = "\n".join(str(ref) for ref in feedback_refs)
        if data.get("route") in {"public_issue", "docs_update", "eval_or_test"} and not feedback_refs:
            errors.append(f"{at}: factory_improvement_issue_candidate requires sdlc_feedback_loop_refs for public/actionable routes")
        if PRIVATE_MARKERS.search(serialized_feedback_refs):
            errors.append(f"{at}: factory_improvement_issue_candidate sdlc_feedback_loop_refs must be public-safe")
    if data.get("record_type") == "owner_issue_intake_report":
        decisions = data.get("decisions") if isinstance(data.get("decisions"), list) else []
        actionable = {"needs_human_triage", "documentation_only", "implementation_candidate", "critical_factory_change", "private_operator_only"}
        for index, row in enumerate(decisions):
            if not isinstance(row, dict):
                continue
            decision = str(row.get("decision") or "").strip()
            if decision not in actionable:
                continue
            feedback_ref = str(row.get("sdlc_feedback_loop_ref") or "").strip()
            if not feedback_ref:
                errors.append(f"{at}.decisions[{index}]: actionable owner issue intake requires sdlc_feedback_loop_ref")
            else:
                reason = public_artifact_ref_error(feedback_ref)
                if reason:
                    errors.append(f"{at}.decisions[{index}].sdlc_feedback_loop_ref: {reason}")
            loop = row.get("sdlc_feedback_loop") if isinstance(row.get("sdlc_feedback_loop"), dict) else {}
            candidate = row.get("factory_card_candidate") if isinstance(row.get("factory_card_candidate"), dict) else {}
            if not loop:
                errors.append(f"{at}.decisions[{index}]: actionable owner issue intake requires sdlc_feedback_loop")
            else:
                if loop.get("loop_id") != feedback_ref:
                    errors.append(f"{at}.decisions[{index}]: sdlc_feedback_loop.loop_id must match sdlc_feedback_loop_ref")
                errors.extend(validate_domain_rules(loop, f"{at}.decisions[{index}].sdlc_feedback_loop"))
            if not candidate:
                errors.append(f"{at}.decisions[{index}]: actionable owner issue intake requires factory_card_candidate")
            elif candidate.get("sdlc_feedback_loop_ref") != feedback_ref:
                errors.append(f"{at}.decisions[{index}]: factory_card_candidate.sdlc_feedback_loop_ref must match row sdlc_feedback_loop_ref")
    if data.get("record_type") == "discord_control_tower_ux_audit":
        serialized = json.dumps(data, sort_keys=True)
        if "todo" in serialized.lower():
            errors.append(f"{at}: discord_control_tower_ux_audit must not contain placeholder todo text")
        if PRIVATE_MARKERS.search(serialized):
            errors.append(f"{at}: discord_control_tower_ux_audit must not publish private Discord or local refs")
        study_gate = data.get("study_gate") if isinstance(data.get("study_gate"), dict) else {}
        if study_gate.get("discord_is_source_of_truth") is not False:
            errors.append(f"{at}: Discord UX audit must keep Discord out of source-of-truth role")
        if study_gate.get("recommended_role") == "primary_operator_operator_console_after_proof":
            proof = data.get("proof_pack_contract") if isinstance(data.get("proof_pack_contract"), dict) else {}
            if proof.get("required_before_acceptance") is not True:
                errors.append(f"{at}: primary Discord operator_console recommendation requires proof pack")
        required_checks = [
            "official_discord_primitives_studied",
            "rate_limits_and_retry_behavior_studied",
            "interaction_expiry_and_fallback_studied",
            "operator_5s_30s_5m_model_defined",
            "staleness_and_idempotency_checks_defined",
            "approval_ambiguity_checks_defined",
            "notification_load_checks_defined",
            "web_operator_console_boundary_defined",
        ]
        checks = data.get("checks") if isinstance(data.get("checks"), dict) else {}
        for field in required_checks:
            if checks.get(field) is not True:
                errors.append(f"{at}: discord_control_tower_ux_audit requires {field}=true")
    if data.get("record_type") == "factory_operating_system_registry":
        errors.extend(validate_operating_system_registry_semantics(data, at))
    if data.get("record_type") == "factory_operating_system_scorecard":
        errors.extend(validate_operating_system_scorecard_semantics(data, at))
    if data.get("record_type") == "method_engine_registry":
        errors.extend(validate_method_engine_registry_semantics(data, at))
    return errors


def validate_public_ref_hygiene(value: Any, at: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, str):
        if contains_private_kanban_task_marker(value):
            errors.append(f"{at}: public artifact must not contain raw Hermes Kanban task id")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(validate_public_ref_hygiene(item, f"{at}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            errors.extend(validate_public_ref_hygiene(item, f"{at}.{key}"))
    return errors


def is_runtime_local_json(path: Path) -> bool:
    resolved_path = path.resolve()
    for runtime_path in RUNTIME_LOCAL_JSON_PATHS:
        if resolved_path == runtime_path.resolve():
            return True
    for directory in RUNTIME_LOCAL_JSON_DIRS:
        try:
            resolved_path.relative_to(directory.resolve())
        except ValueError:
            continue
        return True
    return False


def iter_public_json() -> list[Path]:
    paths: list[Path] = []
    for directory in SCAN_DIRS:
        if directory.exists():
            paths.extend(path for path in sorted(directory.rglob("*.json")) if not is_runtime_local_json(path))
    return paths


def main() -> int:
    schemas = load_schemas()
    findings: list[str] = []
    for schema_path_ref in iter_schema_files():
        schema = load_json(schema_path_ref)
        rel = schema_path_ref.relative_to(ROOT).as_posix()
        for error in validate_schema_keywords(schema):
            findings.append(f"{rel}: {error}")
    for path in iter_public_json():
        try:
            data = load_json(path)
        except json.JSONDecodeError as exc:
            findings.append(f"{path.relative_to(ROOT).as_posix()}: invalid JSON: {exc}")
            continue
        if not isinstance(data, dict):
            continue
        ref = str(data.get("$schema") or "")
        if not ref:
            rel = path.relative_to(ROOT).as_posix()
            if rel not in SCHEMA_OPTIONAL:
                findings.append(f"{rel}: missing $schema")
            continue
        if ref.startswith("https://json-schema.org/"):
            continue
        schema = schemas.get(schema_name(ref))
        if not schema:
            findings.append(f"{path.relative_to(ROOT).as_posix()}: schema not found for {ref}")
            continue
        for error in validate_node(schema, data, "$", schemas=schemas, root_schema=schema):
            findings.append(f"{path.relative_to(ROOT).as_posix()}: {error}")
        for error in validate_domain_rules(data, "$"):
            findings.append(f"{path.relative_to(ROOT).as_posix()}: {error}")

    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
