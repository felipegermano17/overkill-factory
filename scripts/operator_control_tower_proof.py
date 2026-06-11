#!/usr/bin/env python3
"""Validate the production Operator Control Tower gate.

This script is deliberately public-safe. It may read private real Discord or
bridge evidence from external paths, but it writes only redacted evidence refs
and boolean checks to the public repository.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_public_json_artifacts as validator  # noqa: E402


DEFAULT_READONLY = ROOT / "validation" / "control-tower" / "control-tower-readonly-smoke.json"
DEFAULT_APPROVAL = ROOT / "validation" / "control-tower" / "control-tower-approval-registration-smoke.json"
DEFAULT_OUT = ROOT / "validation" / "control-tower" / "operator-control-tower-production-readiness.json"
DEFAULT_PROOF_OUT = ROOT / "validation" / "hermes-production-proof" / "operator-control-tower.json"
BRIDGE_HEALTH_SCHEMA = "https://overkill-factory.dev/schemas/operator-control-tower-bridge-health.schema.json"
BRIDGE_HEALTH_REQUIRED_CHECKS = [
    "bot_reachable",
    "bridge_reachable",
    "runtime_readback_reachable",
    "approval_registration_path_reachable",
    "no_discord_source_of_truth",
    "no_private_material_in_public_receipt",
]
MAPPING_REQUIRED_REAL_REFS = [
    "project_id",
    "board_ref",
    "guild_ref",
    "dashboard_message_ref",
    "approval_channel_ref",
    "bot_health_channel_ref",
]

PRIVATE_PRODUCT = "KA" + "XIS"
PRIVATE_ENV = "V" + "M"
PRIVATE_USERS_PATH = "C:" + "\\\\" + "Users"
PRIVATE_SYNC_ROOT = "One" + "Drive"
PRIVATE_RE = re.compile(
    re.escape(PRIVATE_USERS_PATH)
    + r"|"
    + PRIVATE_SYNC_ROOT
    + r"|"
    + PRIVATE_PRODUCT
    + r"|"
    + PRIVATE_PRODUCT
    + r" "
    + PRIVATE_ENV
    + r"|token|password|secret|webhook",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_ref(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def private_evidence_ref(label: str) -> str:
    return {
        "mapping": "external:discord-control-tower-mapping",
        "runtime_registration_event": "external:runtime-approval-event",
        "bridge_health": "external:bridge-health",
    }.get(label, f"external:{label}")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def validate_artifact(schemas: dict[str, dict[str, Any]], artifact: dict[str, Any]) -> list[str]:
    schema_ref = str(artifact.get("$schema") or "")
    if not schema_ref:
        return ["missing $schema"]
    schema = schemas.get(validator.schema_name(schema_ref))
    if not schema:
        return [f"schema not found for {schema_ref}"]
    return validator.validate_node(schema, artifact, "$")


def is_real_ref(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    lowered = text.lower()
    return not (
        lowered.startswith("redacted-")
        or lowered.startswith("example-")
        or lowered in {"tbd", "todo", "unknown", "missing", "not-applied"}
    )


def all_true(values: Any) -> bool:
    return isinstance(values, dict) and bool(values) and all(value is True for value in values.values())


def bridge_health_uses_contract(bridge_health: dict[str, Any] | None) -> bool:
    return bridge_health is not None and (
        bridge_health.get("$schema") == BRIDGE_HEALTH_SCHEMA
        and bridge_health.get("record_type") == "operator_control_tower_bridge_health"
    )


def bridge_health_checks_pass(bridge_health: dict[str, Any] | None) -> bool:
    if not bridge_health_uses_contract(bridge_health):
        return False
    checks = bridge_health.get("checks")
    return (
        bridge_health.get("result") == "PASS"
        and isinstance(checks, dict)
        and all(checks.get(key) is True for key in BRIDGE_HEALTH_REQUIRED_CHECKS)
    )


def bridge_health_has_real_evidence_refs(bridge_health: dict[str, Any] | None) -> bool:
    if not bridge_health_uses_contract(bridge_health):
        return False
    evidence_refs = bridge_health.get("evidence_refs")
    return isinstance(evidence_refs, list) and bool(evidence_refs) and all(is_real_ref(ref) for ref in evidence_refs)


def runtime_event_registers_owner_decision(runtime_event: dict[str, Any] | None) -> bool:
    return (
        runtime_event is not None
        and runtime_event.get("event_type") == "approval_recorded"
        and runtime_event.get("source") in {"bridge", "hermes"}
        and is_real_ref(runtime_event.get("event_id"))
        and is_real_ref(runtime_event.get("project_id"))
    )


def mapping_runtime_project_matches(
    mapping: dict[str, Any] | None,
    runtime_event: dict[str, Any] | None,
) -> bool:
    if mapping is None or runtime_event is None:
        return False
    return (
        is_real_ref(mapping.get("project_id"))
        and is_real_ref(runtime_event.get("project_id"))
        and mapping.get("project_id") == runtime_event.get("project_id")
    )


def path_is_inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT)
        return True
    except ValueError:
        return False


def assert_public_safe(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    match = PRIVATE_RE.search(text)
    if match:
        raise AssertionError(f"private-looking text in public receipt: {match.group(0)}")


def build_readiness(
    *,
    readonly: dict[str, Any] | None,
    approval: dict[str, Any] | None,
    mapping: dict[str, Any] | None,
    runtime_event: dict[str, Any] | None,
    bridge_health: dict[str, Any] | None,
    evidence_refs: list[str],
    created_at: str | None = None,
) -> dict[str, Any]:
    checks = {
        "control_tower_readonly_contract_passed": readonly is not None
        and readonly.get("result") == "PASS"
        and all_true(readonly.get("readonly_checks")),
        "approval_registration_contract_passed": approval is not None
        and approval.get("result") == "PASS"
        and all_true(approval.get("registration_checks")),
        "real_discord_mapping_present": mapping is not None,
        "real_discord_mapping_has_non_placeholder_refs": mapping is not None
        and all(is_real_ref(mapping.get(field)) for field in MAPPING_REQUIRED_REAL_REFS),
        "runtime_registration_event_present": runtime_event is not None,
        "runtime_registration_event_registers_owner_decision": runtime_event_registers_owner_decision(runtime_event),
        "mapping_runtime_project_matches": mapping_runtime_project_matches(mapping, runtime_event),
        "bridge_health_present": bridge_health is not None,
        "bridge_health_uses_contract": bridge_health_uses_contract(bridge_health),
        "bridge_health_checks_passed": bridge_health_checks_pass(bridge_health),
        "bridge_health_has_real_evidence_refs": bridge_health_has_real_evidence_refs(bridge_health),
    }
    blocking_items = [key for key, value in checks.items() if not value]
    result = "PASS" if not blocking_items else "BLOCKED"
    receipt = {
        "$schema": "https://overkill-factory.dev/schemas/operator-control-tower-production-readiness.schema.json",
        "record_type": "operator_control_tower_production_readiness",
        "created_at": created_at or utc_now(),
        "result": result,
        "checks": checks,
        "blocking_items": blocking_items,
        "evidence_refs": evidence_refs,
        "limits": [
            "This receipt is public-safe and intentionally redacts real Discord, runtime and bridge identifiers.",
            "PASS proves the operator-facing status, approval registration path and bridge health evidence shape for the current production preflight only.",
            "It does not let Discord become the source of truth; Hermes/runtime gates remain authoritative.",
        ],
    }
    assert_public_safe(receipt)
    return receipt


def build_production_proof(readiness_ref: str, evidence_refs: list[str], created_at: str | None = None) -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/hermes-production-proof.schema.json",
        "record_type": "hermes_production_proof",
        "created_at": created_at or utc_now(),
        "proof_type": "operator_control_tower",
        "result": "PASS",
        "summary": "The owner-facing Control Tower has a real Discord mapping, a runtime-registerable approval event path, bridge health evidence, and passing public-safe contract smokes.",
        "scope": "operator-facing Control Tower, Discord mapping, runtime approval registration path, bridge health evidence",
        "environment_ref": "redacted-real-operator-control-tower",
        "evidence_refs": [readiness_ref, *evidence_refs],
        "limits": [
            "This proof is public-safe and does not store real Discord ids, runtime ids, private URLs, credentials or raw logs.",
            "Discord remains the human cockpit only; Hermes or the selected runtime remains the durable source of truth.",
            "Future channels, roles, approval kinds or bridge behavior changes need a fresh Control Tower proof.",
        ],
        "decision": {
            "real_runtime_update": "allowed_for_explicit_operator_gate"
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readonly-smoke", type=Path, default=DEFAULT_READONLY)
    parser.add_argument("--approval-smoke", type=Path, default=DEFAULT_APPROVAL)
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--runtime-registration-event", type=Path)
    parser.add_argument("--bridge-health", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--production-proof-out", type=Path, default=DEFAULT_PROOF_OUT)
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    schemas = validator.load_schemas()
    evidence_refs = [repo_ref(args.readonly_smoke), repo_ref(args.approval_smoke)]
    errors: list[str] = []

    def optional_load(path: Path | None, label: str, *, private_evidence: bool = False) -> dict[str, Any] | None:
        if path is None:
            return None
        if private_evidence:
            if path_is_inside_repo(path):
                errors.append(f"{label}: private evidence path must be outside the public repository")
                return None
            evidence_refs.append(private_evidence_ref(label))
        else:
            evidence_refs.append(repo_ref(path))
        try:
            return load_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{label}: {type(exc).__name__}")
            return None

    readonly = optional_load(args.readonly_smoke, "readonly_smoke")
    approval = optional_load(args.approval_smoke, "approval_smoke")
    mapping = optional_load(args.mapping, "mapping", private_evidence=True)
    runtime_event = optional_load(
        args.runtime_registration_event,
        "runtime_registration_event",
        private_evidence=True,
    )
    bridge_health = optional_load(args.bridge_health, "bridge_health", private_evidence=True)

    for label, artifact in [
        ("readonly_smoke", readonly),
        ("approval_smoke", approval),
        ("mapping", mapping),
        ("runtime_registration_event", runtime_event),
        ("bridge_health", bridge_health),
    ]:
        if artifact is not None:
            errors.extend(f"{label}: {error}" for error in validate_artifact(schemas, artifact))

    readiness = build_readiness(
        readonly=readonly,
        approval=approval,
        mapping=mapping,
        runtime_event=runtime_event,
        bridge_health=bridge_health,
        evidence_refs=sorted(set(evidence_refs)),
    )
    if errors:
        readiness["result"] = "FAIL"
        readiness["blocking_items"] = sorted(set([*readiness["blocking_items"], "invalid_input_artifact"]))
        readiness["input_errors"] = errors

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(readiness, indent=2) + "\n", encoding="utf-8")

    if readiness["result"] == "PASS":
        proof = build_production_proof(repo_ref(args.out), sorted(set(evidence_refs)))
        assert_public_safe(proof)
        args.production_proof_out.parent.mkdir(parents=True, exist_ok=True)
        args.production_proof_out.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    elif args.production_proof_out.exists():
        args.production_proof_out.unlink()

    print(json.dumps({"result": readiness["result"], "out": repo_ref(args.out)}, indent=2))
    return 0 if readiness["result"] == "PASS" else 1


def main_with_args_for_test(argv: list[str]) -> int:
    return main_with_args(argv)


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
