#!/usr/bin/env python3
"""Validate public JSON artifacts against bundled lightweight schemas.

This intentionally avoids third-party dependencies so CI can run on a clean
Python install. It supports the schema features used by this repository:
required fields, type, const, enum, properties, minProperties,
additionalProperties and arrays.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
SCAN_DIRS = [ROOT / "examples", ROOT / ".tmp" / "factory-runs", ROOT / "agents", ROOT / "templates"]

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
)


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
        for field in PRODUCT_FACE_ALIGNMENT_FIELDS:
            value = data.get(field)
            if not isinstance(value, dict) or value.get("status") != "pass":
                errors.append(f"{at}: reusable product_face_result requires {field}.status=pass")
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
