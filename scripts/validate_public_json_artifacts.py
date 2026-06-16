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

SCHEMA_DIR = ROOT / "schemas"
PUBLIC_SCHEMA_DIRS = [
    SCHEMA_DIR,
    ROOT / "agents",
    ROOT / "docs",
    ROOT / "examples",
    ROOT / "planning-bundles",
    ROOT / "products",
    ROOT / "templates",
]
SCAN_DIRS = [
    ROOT / "examples",
    ROOT / ".tmp" / "factory-runs",
    ROOT / "agents",
    ROOT / "templates",
    ROOT / "docs",
    ROOT / "planning-bundles",
    ROOT / "products",
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


def iter_public_json() -> list[Path]:
    paths: list[Path] = []
    for directory in SCAN_DIRS:
        if directory.exists():
            paths.extend(sorted(directory.rglob("*.json")))
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
