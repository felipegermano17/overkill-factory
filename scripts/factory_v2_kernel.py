#!/usr/bin/env python3
"""Deterministic Overkill Factory V2 state contracts.

This module is intentionally small and boring. Agents may draft artifacts, but
Factory V2 state changes must pass through command, event, decision and
promotion contracts that can be replayed without trusting agent memory.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_public_json_artifacts import load_schemas, validate_node


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW_CATALOG = ROOT / "docs" / "factory-workflow.catalog.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_json_array_or_object(path: Path) -> list[Any] | dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, (list, dict)):
        raise ValueError(f"{path} must contain a JSON object or array")
    return data


def _schema_errors(schema_name: str, value: dict[str, Any], at: str) -> list[str]:
    schemas = load_schemas()
    schema = schemas[schema_name]
    return validate_node(schema, value, at, schemas=schemas, root_schema=schema)


def _payload(value: dict[str, Any]) -> dict[str, Any]:
    payload = value.get("payload")
    return payload if isinstance(payload, dict) else {}


def _refs(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def validate_factory_command(command: dict[str, Any], at: str = "factory_command") -> list[str]:
    errors = _schema_errors("factory-command.schema.json", command, at)
    command_type = command.get("command_type")
    payload = _payload(command)

    phase_bound_commands = {
        "advance_phase",
        "materialize_worker",
        "request_decision",
        "record_decision",
        "repair_required",
        "promote",
        "release",
        "learnback_candidate",
    }
    if command_type in phase_bound_commands and not payload.get("phase_id"):
        errors.append(f"{at}.payload.phase_id: required for {command_type}")
    if command_type == "materialize_worker" and not payload.get("worker_id"):
        errors.append(f"{at}.payload.worker_id: required for materialize_worker")
    if command_type in {"request_decision", "record_decision"} and not payload.get("decision_id"):
        errors.append(f"{at}.payload.decision_id: required for {command_type}")
    if command_type == "request_decision" and not _refs(payload.get("artifact_refs")):
        errors.append(f"{at}.payload.artifact_refs: decision requests require an evidence packet")
    if command_type == "repair_required" and not payload.get("blocked_reason"):
        errors.append(f"{at}.payload.blocked_reason: required for repair_required")
    if command_type in {"promote", "release"} and not _refs(payload.get("artifact_refs")):
        errors.append(f"{at}.payload.artifact_refs: required for {command_type}")
    return errors


def factory_event_hash(event: dict[str, Any]) -> str:
    normalized = copy.deepcopy(event)
    normalized.pop("event_hash", None)
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_factory_run_event(event: dict[str, Any], at: str = "factory_run_event") -> list[str]:
    errors = _schema_errors("factory-run-event.schema.json", event, at)
    expected_hash = factory_event_hash(event)
    if event.get("event_hash") != expected_hash:
        errors.append(f"{at}.event_hash: expected {expected_hash}")
    event_type = event.get("event_type")
    payload = _payload(event)
    if event_type in {"phase_advanced", "worker_materialized", "human_decision_requested"} and not payload.get("phase_id"):
        errors.append(f"{at}.payload.phase_id: required for {event_type}")
    if event_type == "human_decision_requested" and not _refs(payload.get("artifact_refs")):
        errors.append(f"{at}.payload.artifact_refs: human decisions require a delivered packet")
    return errors


def normalize_event_log(value: list[Any] | dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(value, dict) and value.get("record_type") == "factory_run_event":
        return [value]
    raw_events = value.get("event_log") if isinstance(value, dict) else value
    if not isinstance(raw_events, list):
        raise ValueError("event log input must be a JSON array or an object with event_log")
    events: list[dict[str, Any]] = []
    for index, item in enumerate(raw_events):
        if not isinstance(item, dict):
            raise ValueError(f"event_log[{index}] must be a JSON object")
        events.append(item)
    return events


def validate_factory_event_log(events: list[dict[str, Any]], at: str = "event_log") -> list[str]:
    errors: list[str] = []
    previous_hash: str | None = None
    seen_hashes: set[str] = set()
    for index, event in enumerate(events):
        event_at = f"{at}[{index}]"
        errors.extend(validate_factory_run_event(event, event_at))
        expected_sequence = index + 1
        if event.get("sequence") != expected_sequence:
            errors.append(f"{event_at}.sequence: expected contiguous sequence {expected_sequence}")
        if index == 0 and event.get("previous_event_hash") is not None:
            errors.append(f"{event_at}.previous_event_hash: first event must use null previous hash")
        if index > 0 and event.get("previous_event_hash") != previous_hash:
            errors.append(f"{event_at}.previous_event_hash: must equal previous event hash")
        event_hash = event.get("event_hash")
        if isinstance(event_hash, str):
            if event_hash in seen_hashes:
                errors.append(f"{event_at}.event_hash: duplicate event hash")
            seen_hashes.add(event_hash)
            previous_hash = event_hash
    return errors


def validate_factory_decision_outbox(outbox: dict[str, Any], at: str = "factory_decision_outbox") -> list[str]:
    errors = _schema_errors("factory-decision-outbox.schema.json", outbox, at)
    for index, decision in enumerate(outbox.get("pending_decisions") or []):
        if not isinstance(decision, dict):
            continue
        decision_at = f"{at}.pending_decisions[{index}]"
        if decision.get("status") == "pending" and not decision.get("required_packet_ref"):
            errors.append(f"{decision_at}.required_packet_ref: pending decisions require a packet")
        if decision.get("status") == "resolved" and not decision.get("recorded_decision_ref"):
            errors.append(f"{decision_at}.recorded_decision_ref: resolved decisions require recorded human decision")
        if decision.get("decision_type") == "human_gate" and decision.get("authority_required") != "human_operator":
            errors.append(f"{decision_at}.authority_required: human_gate decisions require human_operator authority")
    return errors


def validate_factory_promotion_packet(packet: dict[str, Any], at: str = "factory_promotion_packet") -> list[str]:
    errors = _schema_errors("factory-promotion-packet.schema.json", packet, at)
    evidence_refs = set(_refs(packet.get("evidence_refs")))
    for required_field in ("receipt_five_ref", "completion_audit_ref", "release_readiness_ref"):
        required_ref = packet.get(required_field)
        if isinstance(required_ref, str) and required_ref not in evidence_refs:
            errors.append(f"{at}.evidence_refs: must include {required_field} {required_ref}")
    if packet.get("promotion_scope") in {"product", "release"} and not packet.get("human_gate_record_ref"):
        errors.append(f"{at}.human_gate_record_ref: product/release promotion requires human gate record")
    if packet.get("decision") == "approve" and packet.get("promotion_scope") == "release":
        for required_field in ("rollback_ref", "monitoring_ref"):
            value = str(packet.get(required_field) or "")
            if value.startswith(("todo:", "missing:", "blocked:")):
                errors.append(f"{at}.{required_field}: release approval cannot use unresolved placeholder")
    return errors


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _phase_allows_human_decision(phase: dict[str, Any]) -> bool:
    text = " ".join(str(item) for item in _as_list(phase.get("required_gates")))
    lowered = text.lower()
    return "human" in lowered or "approval" in lowered


def _phase_allows_promotion(phase: dict[str, Any]) -> bool:
    text = " ".join(
        str(item)
        for item in [phase.get("phase_name")]
        + _as_list(phase.get("required_gates"))
        + _as_list(phase.get("allowed_next_actions"))
        + _as_list(phase.get("completion_detection"))
    )
    lowered = text.lower()
    return any(token in lowered for token in ("promotion", "promote", "release", "completion", "receipt", "done"))


def _allowed_commands_for_phase(phase: dict[str, Any]) -> list[str]:
    commands = ["advance_phase", "repair_required"]
    if _as_list(phase.get("required_workers")):
        commands.append("materialize_worker")
    if _phase_allows_human_decision(phase):
        commands.append("request_decision")
    if _phase_allows_promotion(phase):
        commands.append("promote")
    phase_name = str(phase.get("phase_name") or "").lower()
    if "release" in phase_name or "production" in phase_name:
        commands.append("release")
    if "learnback" in phase_name or "maturity" in phase_name:
        commands.append("learnback_candidate")
    return sorted(set(commands), key=commands.index)


def compile_workflow_catalog(
    catalog: dict[str, Any],
    *,
    catalog_ref: str = "docs/factory-workflow.catalog.json",
    plan_id: str | None = None,
    compiled_at: str | None = None,
) -> dict[str, Any]:
    source_phases = _as_list(catalog.get("phases"))
    phases: list[dict[str, Any]] = []
    for index, phase in enumerate(source_phases):
        if not isinstance(phase, dict):
            continue
        next_phase = source_phases[index + 1] if index + 1 < len(source_phases) and isinstance(source_phases[index + 1], dict) else None
        required_artifacts = [str(item) for item in _as_list(phase.get("required_artifacts"))]
        required_gates = [str(item) for item in _as_list(phase.get("required_gates"))]
        required_workers = [str(item) for item in _as_list(phase.get("required_workers"))]
        phases.append(
            {
                "phase_id": str(phase.get("phase_id") or ""),
                "phase_index": index + 1,
                "phase_name": str(phase.get("phase_name") or ""),
                "required_artifacts": required_artifacts,
                "required_gates": required_gates,
                "required_workers": required_workers,
                "allowed_commands": _allowed_commands_for_phase(phase),
                "blocked_actions": [str(item) for item in _as_list(phase.get("blocked_actions"))],
                "next_phase_id": str(next_phase.get("phase_id")) if next_phase else None,
                "auto_pass_allowed": not required_artifacts and not required_gates and not required_workers,
            }
        )
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-workflow-compiled-plan.schema.json",
        "record_type": "factory_workflow_compiled_plan",
        "plan_id": plan_id or f"{catalog.get('factory_method_version', 'factory')}-{catalog.get('catalog_version', 'v0')}",
        "compiled_at": compiled_at or utc_now(),
        "catalog_ref": catalog_ref,
        "catalog_version": str(catalog.get("catalog_version") or "unknown"),
        "phase_count": len(phases),
        "phases": phases,
        "compiler_guards": {
            "duplicate_phase_ids_blocked": True,
            "unknown_next_phase_blocked": True,
            "human_gate_requires_decision_outbox": True,
            "worker_materialization_requires_dispatch_readiness": True,
        },
    }


def validate_factory_workflow_compiled_plan(plan: dict[str, Any], at: str = "factory_workflow_compiled_plan") -> list[str]:
    errors = _schema_errors("factory-workflow-compiled-plan.schema.json", plan, at)
    phases = [phase for phase in plan.get("phases", []) if isinstance(phase, dict)]
    if plan.get("phase_count") != len(phases):
        errors.append(f"{at}.phase_count: must match phases length")
    phase_ids = [phase.get("phase_id") for phase in phases]
    duplicate_phase_ids = sorted({phase_id for phase_id in phase_ids if phase_ids.count(phase_id) > 1})
    if duplicate_phase_ids:
        errors.append(f"{at}.phases: duplicate phase ids {', '.join(str(item) for item in duplicate_phase_ids)}")
    known_phase_ids = {phase_id for phase_id in phase_ids if isinstance(phase_id, str)}
    for index, phase in enumerate(phases):
        phase_at = f"{at}.phases[{index}]"
        expected_index = index + 1
        if phase.get("phase_index") != expected_index:
            errors.append(f"{phase_at}.phase_index: expected {expected_index}")
        next_phase_id = phase.get("next_phase_id")
        if next_phase_id is not None and next_phase_id not in known_phase_ids:
            errors.append(f"{phase_at}.next_phase_id: unknown phase {next_phase_id}")
        if "request_decision" in phase.get("allowed_commands", []) and not any(
            "human" in str(gate).lower() or "approval" in str(gate).lower()
            for gate in _as_list(phase.get("required_gates"))
        ):
            errors.append(f"{phase_at}.allowed_commands: request_decision requires human/approval gate")
    return errors


def validate_factory_run(run: dict[str, Any], at: str = "factory_run") -> list[str]:
    errors = _schema_errors("factory-run.schema.json", run, at)

    runtime_target = run.get("runtime_target") if isinstance(run.get("runtime_target"), dict) else {}
    if runtime_target.get("ambient_runtime_allowed") is not False:
        errors.append(f"{at}.runtime_target.ambient_runtime_allowed: must be false")
    if not runtime_target.get("runtime_target_ref"):
        errors.append(f"{at}.runtime_target.runtime_target_ref: explicit Hermes/Kanban target is required")

    board_binding = run.get("board_binding") if isinstance(run.get("board_binding"), dict) else {}
    board_policy = board_binding.get("board_policy")
    board_ref = board_binding.get("board_ref")
    if board_policy == "factory_must_create_new_board" and board_ref is not None:
        errors.append(f"{at}.board_binding.board_ref: new-board policy must start without board_ref")
    if board_policy == "explicit_existing_board" and not board_ref:
        errors.append(f"{at}.board_binding.board_ref: existing-board policy requires explicit board_ref")

    commands = run.get("command_inbox") if isinstance(run.get("command_inbox"), list) else []
    for index, command in enumerate(commands):
        if isinstance(command, dict):
            errors.extend(validate_factory_command(command, f"{at}.command_inbox[{index}]"))
        else:
            errors.append(f"{at}.command_inbox[{index}]: expected object")

    events = run.get("event_log") if isinstance(run.get("event_log"), list) else []
    if all(isinstance(event, dict) for event in events):
        errors.extend(validate_factory_event_log(events, f"{at}.event_log"))
    else:
        errors.append(f"{at}.event_log: all events must be objects")
    if isinstance(run.get("state_version"), int) and run["state_version"] < len(events):
        errors.append(f"{at}.state_version: must be greater than or equal to event log length")

    decision_outbox = run.get("decision_outbox")
    if isinstance(decision_outbox, dict):
        errors.extend(validate_factory_decision_outbox(decision_outbox, f"{at}.decision_outbox"))
    else:
        errors.append(f"{at}.decision_outbox: expected object")

    for index, packet in enumerate(run.get("promotion_packets") or []):
        if isinstance(packet, dict):
            errors.extend(validate_factory_promotion_packet(packet, f"{at}.promotion_packets[{index}]"))
        else:
            errors.append(f"{at}.promotion_packets[{index}]: expected object")
    return errors
