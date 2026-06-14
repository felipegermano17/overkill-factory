#!/usr/bin/env python3
"""Validate public JSON artifacts against bundled lightweight schemas.

This intentionally avoids third-party dependencies so CI can run on a clean
Python install. It supports the schema features used by this repository:
required fields, type, const, enum, properties, minProperties,
additionalProperties and arrays.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
SCAN_DIRS = [
    ROOT / "examples",
    ROOT / ".tmp" / "factory-runs",
    ROOT / "agents",
    ROOT / "templates",
    ROOT / "docs",
    ROOT / "planning-bundles",
]

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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_name(schema_ref: str) -> str:
    return schema_ref.rsplit("/", 1)[-1]


def load_schemas() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for path in sorted(SCHEMA_DIR.glob("*.json")):
        schema = load_json(path)
        schema_id = str(schema.get("$id") or "")
        schemas[path.name] = schema
        if schema_id:
            schemas[schema_name(schema_id)] = schema
    return schemas


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


def validate_node(schema: dict[str, Any], value: Any, at: str) -> list[str]:
    errors: list[str] = []
    if "type" in schema and not type_matches(schema["type"], value):
        errors.append(f"{at}: expected type {schema['type']}")
        return errors
    if "const" in schema and value != schema["const"]:
        errors.append(f"{at}: expected const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{at}: value {value!r} not in enum")
    if isinstance(value, str) and "minLength" in schema and len(value) < int(schema["minLength"]):
        errors.append(f"{at}: string shorter than minLength {schema['minLength']}")
    if isinstance(value, list) and "minItems" in schema and len(value) < int(schema["minItems"]):
        errors.append(f"{at}: array shorter than minItems {schema['minItems']}")
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
                    errors.extend(validate_node(subschema, value[field], f"{at}.{field}"))
        additional = schema.get("additionalProperties", True)
        if additional is False and isinstance(properties, dict):
            for field in value:
                if field not in properties:
                    errors.append(f"{at}: additional property {field} is not allowed")
        if isinstance(additional, dict):
            for field, item in value.items():
                if field not in properties:
                    errors.extend(validate_node(additional, item, f"{at}.{field}"))

    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            errors.extend(validate_node(schema["items"], item, f"{at}[{index}]"))

    return errors


def validate_domain_rules(data: dict[str, Any], at: str) -> list[str]:
    errors: list[str] = []
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
    if data.get("record_type") == "product_face_result" and data.get("reusable_for_product") is True:
        if not str(data.get("packet_ref") or "").strip():
            errors.append(f"{at}: reusable product_face_result requires packet_ref")
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
            if gate.get("status") != "PASS":
                errors.append(f"{at}: professional_design_process {gate_name}.status must be PASS")
        reviewer_role = str((data.get("comparative_review_gate") or {}).get("reviewer_role") or "").lower()
        if "independent" not in reviewer_role:
            errors.append(f"{at}: professional_design_process comparative_review_gate requires an independent reviewer")
    if data.get("record_type") == "factory_learning_proposal":
        serialized_refs = "\n".join(str(ref) for ref in data.get("source_evidence_refs", []))
        if PRIVATE_MARKERS.search(serialized_refs):
            errors.append(f"{at}: factory_learning_proposal source_evidence_refs must be public-safe")
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
    if data.get("record_type") == "discord_control_tower_ux_audit":
        serialized = json.dumps(data, sort_keys=True)
        if "todo" in serialized.lower():
            errors.append(f"{at}: discord_control_tower_ux_audit must not contain placeholder todo text")
        if PRIVATE_MARKERS.search(serialized):
            errors.append(f"{at}: discord_control_tower_ux_audit must not publish private Discord or local refs")
        study_gate = data.get("study_gate") if isinstance(data.get("study_gate"), dict) else {}
        if study_gate.get("discord_is_source_of_truth") is not False:
            errors.append(f"{at}: Discord UX audit must keep Discord out of source-of-truth role")
        if study_gate.get("recommended_role") == "primary_operator_cockpit_after_proof":
            proof = data.get("proof_pack_contract") if isinstance(data.get("proof_pack_contract"), dict) else {}
            if proof.get("required_before_acceptance") is not True:
                errors.append(f"{at}: primary Discord cockpit recommendation requires proof pack")
        required_checks = [
            "official_discord_primitives_studied",
            "rate_limits_and_retry_behavior_studied",
            "interaction_expiry_and_fallback_studied",
            "operator_5s_30s_5m_model_defined",
            "staleness_and_idempotency_checks_defined",
            "approval_ambiguity_checks_defined",
            "notification_load_checks_defined",
            "web_cockpit_boundary_defined",
        ]
        checks = data.get("checks") if isinstance(data.get("checks"), dict) else {}
        for field in required_checks:
            if checks.get(field) is not True:
                errors.append(f"{at}: discord_control_tower_ux_audit requires {field}=true")
    return errors


def iter_public_json() -> list[Path]:
    paths: list[Path] = []
    for directory in SCAN_DIRS:
        if directory.exists():
            paths.extend(sorted(directory.rglob("*.json")))
    return paths


def main() -> int:
    schemas = load_schemas()
    findings: list[str] = []
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
        for error in validate_node(schema, data, "$"):
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
