#!/usr/bin/env python3
"""StatusSnapshot v0 contract helpers for Issue #84 fixtures.

This module intentionally uses only Python stdlib. The JSON Schema file is the
public artifact; these helpers implement the fail-closed domain checks that are
hard to express with the repository's lightweight schema validator.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_URL = "https://overkill-factory.dev/schemas/factory-status-snapshot.schema.json"
SCHEMA_VERSION = "status-snapshot-v0"

REQUIRED_TOP_LEVEL = [
    "$schema",
    "schema_version",
    "record_type",
    "fixture_id",
    "fixture_name",
    "kind",
    "title",
    "phase",
    "risk_effective",
    "observed_at",
    "freshness_state",
    "current_state",
    "source_refs",
    "canonical_refs",
    "gate_states",
    "blockers",
    "worker_state",
    "review_state",
    "receipt_five_status",
    "evidence_refs",
    "public_private_boundary",
    "state_flags",
    "forbidden_actions",
    "next_safe_action",
    "validation_expectations",
]

FRESHNESS_STATES = {
    "current",
    "stale",
    "missing",
    "manual_estimate",
    "contradictory",
    "superseded",
    "private_unavailable",
    "loading",
    "error",
}

CURRENT_STATES = {
    "success",
    "empty",
    "loading",
    "error",
    "blocked",
    "stale",
    "missing",
    "missing-gate",
    "contradictory",
    "private_unavailable",
    "superseded",
    "manual_estimate",
    "security_negative",
}

GATE_STATES = {"passed", "failed", "missing", "stale", "blocked", "superseded", "waived", "pending"}
REVIEW_STATES = {"passed", "failed", "missing", "stale", "blocked", "superseded", "waived", "pending", "not_required"}
RECEIPT_STATES = {"present", "missing", "stale", "invalid", "review_missing", "not_applicable"}
PUBLIC_SAFETY_STATES = {"public_safe", "private_redacted", "blocked", "missing", "unverified"}
VERIFICATION_STATES = {
    "verified_public_api",
    "verified_relative_artifact",
    "json_and_receipt_validated",
    "private_redacted",
    "missing",
    "unverified",
    "blocked",
}
NEXT_ACTION_TYPES = {"review", "block", "refresh", "fix", "none", "implement", "release", "approve_gate", "mutate_runtime"}
FAIL_CLOSED_ACTION_TYPES = {"review", "block", "refresh", "fix", "none"}
DANGEROUS_ACTION_TYPES = {"implement", "release", "approve_gate", "mutate_runtime"}
FAIL_CLOSED_STATES = {
    "stale",
    "missing",
    "missing-gate",
    "contradictory",
    "private_unavailable",
    "superseded",
    "manual_estimate",
    "blocked",
    "error",
}


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def _require_object(value: Any, field: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{field}: expected object")
        return {}
    return value


def _require_nonempty_list(value: Any, field: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list) or not value:
        errors.append(f"{field}: expected non-empty array")
        return []
    return value


def _check_enum(value: Any, allowed: set[str], field: str, errors: list[str]) -> None:
    if value not in allowed:
        errors.append(f"{field}: value {value!r} not in {sorted(allowed)}")


def validate_snapshot(data: dict[str, Any]) -> list[str]:
    """Return contract errors for one StatusSnapshot v0 object."""
    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"$: missing required field {field}")

    if data.get("$schema") != SCHEMA_URL:
        errors.append(f"$.schema: expected {SCHEMA_URL}")
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"$.schema_version: expected {SCHEMA_VERSION}")
    if data.get("record_type") != "factory_status_snapshot":
        errors.append("$.record_type: expected factory_status_snapshot")

    for field in ("fixture_id", "fixture_name", "kind", "title", "phase", "risk_effective", "observed_at"):
        if field in data and not str(data.get(field) or "").strip():
            errors.append(f"$.{field}: expected non-empty string")

    if "freshness_state" in data:
        _check_enum(data.get("freshness_state"), FRESHNESS_STATES, "$.freshness_state", errors)
    if "current_state" in data:
        _check_enum(data.get("current_state"), CURRENT_STATES, "$.current_state", errors)

    for field in ("source_refs", "canonical_refs", "gate_states", "worker_state", "evidence_refs", "forbidden_actions"):
        _require_nonempty_list(data.get(field), f"$.{field}", errors)

    for idx, gate in enumerate(data.get("gate_states") or []):
        if not isinstance(gate, dict):
            errors.append(f"$.gate_states[{idx}]: expected object")
            continue
        for field in ("id", "label", "state", "source_refs"):
            if field not in gate:
                errors.append(f"$.gate_states[{idx}]: missing {field}")
        _check_enum(gate.get("state"), GATE_STATES, f"$.gate_states[{idx}].state", errors)
        _require_nonempty_list(gate.get("source_refs"), f"$.gate_states[{idx}].source_refs", errors)

    blockers = data.get("blockers")
    if blockers is not None and not isinstance(blockers, list):
        errors.append("$.blockers: expected array")
    for idx, blocker in enumerate(blockers or []):
        if not isinstance(blocker, dict):
            errors.append(f"$.blockers[{idx}]: expected object")
            continue
        for field in ("id", "state", "summary", "unblock_condition", "source_refs"):
            if field not in blocker:
                errors.append(f"$.blockers[{idx}]: missing {field}")
        _require_nonempty_list(blocker.get("source_refs"), f"$.blockers[{idx}].source_refs", errors)

    review_state = _require_object(data.get("review_state"), "$.review_state", errors)
    if review_state:
        for field in ("required", "status", "executor_identity", "reviewer_identity", "source_refs"):
            if field not in review_state:
                errors.append(f"$.review_state: missing {field}")
        _check_enum(review_state.get("status"), REVIEW_STATES, "$.review_state.status", errors)
        if review_state.get("required") is not False and review_state.get("executor_identity") == review_state.get("reviewer_identity"):
            errors.append("$.review_state: executor_identity must differ from reviewer_identity when review is required")
        _require_nonempty_list(review_state.get("source_refs"), "$.review_state.source_refs", errors)

    receipt = _require_object(data.get("receipt_five_status"), "$.receipt_five_status", errors)
    if receipt:
        for field in ("status", "reviewer_required", "changed", "artifact_paths", "verification_commands", "verification_result", "next_action"):
            if field not in receipt:
                errors.append(f"$.receipt_five_status: missing {field}")
        _check_enum(receipt.get("status"), RECEIPT_STATES, "$.receipt_five_status.status", errors)
        _require_nonempty_list(receipt.get("artifact_paths"), "$.receipt_five_status.artifact_paths", errors)
        _require_nonempty_list(receipt.get("verification_commands"), "$.receipt_five_status.verification_commands", errors)
        if receipt.get("reviewer_required") and not str(receipt.get("reviewer_result") or "").strip():
            errors.append("$.receipt_five_status: reviewer_result required when reviewer_required=true")

    for idx, evidence in enumerate(data.get("evidence_refs") or []):
        if not isinstance(evidence, dict):
            errors.append(f"$.evidence_refs[{idx}]: expected object")
            continue
        for field in ("id", "kind", "source_refs", "freshness_state", "public_safety_state", "verification_status", "raw_payload_included"):
            if field not in evidence:
                errors.append(f"$.evidence_refs[{idx}]: missing {field}")
        _require_nonempty_list(evidence.get("source_refs"), f"$.evidence_refs[{idx}].source_refs", errors)
        _check_enum(evidence.get("freshness_state"), FRESHNESS_STATES, f"$.evidence_refs[{idx}].freshness_state", errors)
        _check_enum(evidence.get("public_safety_state"), PUBLIC_SAFETY_STATES, f"$.evidence_refs[{idx}].public_safety_state", errors)
        _check_enum(evidence.get("verification_status"), VERIFICATION_STATES, f"$.evidence_refs[{idx}].verification_status", errors)
        if evidence.get("raw_payload_included") is not False:
            errors.append(f"$.evidence_refs[{idx}].raw_payload_included: must be false")

    boundary = _require_object(data.get("public_private_boundary"), "$.public_private_boundary", errors)
    if boundary:
        for field in ("allowed_refs", "blocked_refs", "raw_private_payload_included"):
            if field not in boundary:
                errors.append(f"$.public_private_boundary: missing {field}")
        _require_nonempty_list(boundary.get("allowed_refs"), "$.public_private_boundary.allowed_refs", errors)
        _require_nonempty_list(boundary.get("blocked_refs"), "$.public_private_boundary.blocked_refs", errors)
        if boundary.get("raw_private_payload_included") is not False:
            errors.append("$.public_private_boundary.raw_private_payload_included: must be false")

    state_flags = _require_object(data.get("state_flags"), "$.state_flags", errors)
    if state_flags:
        for field in ("request", "approval", "blocked", "done", "released", "superseded", "implemented", "validated", "integrated"):
            if field not in state_flags:
                errors.append(f"$.state_flags: missing {field}")
            elif not isinstance(state_flags.get(field), bool):
                errors.append(f"$.state_flags.{field}: expected boolean")

    action = _require_object(data.get("next_safe_action"), "$.next_safe_action", errors)
    if action:
        for field in ("action_type", "label", "source_refs", "forbidden_action_taken"):
            if field not in action:
                errors.append(f"$.next_safe_action: missing {field}")
        _check_enum(action.get("action_type"), NEXT_ACTION_TYPES, "$.next_safe_action.action_type", errors)
        _require_nonempty_list(action.get("source_refs"), "$.next_safe_action.source_refs", errors)
        if action.get("forbidden_action_taken") is not False:
            errors.append("$.next_safe_action.forbidden_action_taken: must be false")

    expectations = _require_object(data.get("validation_expectations"), "$.validation_expectations", errors)
    if expectations:
        for field in ("expected_fixture_validator", "evidence_ref_public_safety_expected", "fail_closed_required", "required_assertions"):
            if field not in expectations:
                errors.append(f"$.validation_expectations: missing {field}")
        if expectations.get("expected_fixture_validator") not in {"pass", "fail"}:
            errors.append("$.validation_expectations.expected_fixture_validator: expected pass/fail")
        if expectations.get("evidence_ref_public_safety_expected") not in {"pass", "fail"}:
            errors.append("$.validation_expectations.evidence_ref_public_safety_expected: expected pass/fail")
        if not isinstance(expectations.get("fail_closed_required"), bool):
            errors.append("$.validation_expectations.fail_closed_required: expected boolean")
        _require_nonempty_list(expectations.get("required_assertions"), "$.validation_expectations.required_assertions", errors)

    return errors


def fail_closed_required(data: dict[str, Any]) -> bool:
    raw_expectations = data.get("validation_expectations")
    expectations: dict[str, Any] = raw_expectations if isinstance(raw_expectations, dict) else {}
    if expectations.get("fail_closed_required") is True:
        return True
    return data.get("freshness_state") in FAIL_CLOSED_STATES or data.get("current_state") in FAIL_CLOSED_STATES


def fail_closed_errors(data: dict[str, Any]) -> list[str]:
    """Return errors if a fail-closed case exposes a dangerous next action."""
    if not fail_closed_required(data):
        return []
    errors: list[str] = []
    raw_action = data.get("next_safe_action")
    action: dict[str, Any] = raw_action if isinstance(raw_action, dict) else {}
    action_type = action.get("action_type")
    if action_type not in FAIL_CLOSED_ACTION_TYPES:
        errors.append(f"{data.get('fixture_id', '<unknown>')}: fail-closed case uses unsafe next action {action_type!r}")
    if action_type in DANGEROUS_ACTION_TYPES:
        errors.append(f"{data.get('fixture_id', '<unknown>')}: dangerous next action {action_type!r} is forbidden")
    if action.get("forbidden_action_taken") is not False:
        errors.append(f"{data.get('fixture_id', '<unknown>')}: forbidden_action_taken must remain false")
    raw_state_flags = data.get("state_flags")
    state_flags: dict[str, Any] = raw_state_flags if isinstance(raw_state_flags, dict) else {}
    if state_flags.get("released") and data.get("current_state") != "contradictory":
        errors.append(f"{data.get('fixture_id', '<unknown>')}: released flag may only appear in contradiction fixtures")
    return errors


def fixture_paths(directory: str | Path) -> list[Path]:
    return sorted(Path(directory).glob("FX*.json"))


def load_fixtures(directory: str | Path) -> list[tuple[Path, dict[str, Any]]]:
    return [(path, load_json(path)) for path in fixture_paths(directory)]
