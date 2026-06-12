#!/usr/bin/env python3
"""Diagnose private Operator Control Tower evidence without leaking it.

The production proof reads real Discord or cockpit evidence from outside the
public repository. This helper gives a public-safe preflight for those private
files: it reports which proof inputs are missing or malformed, but never writes
raw ids, URLs, paths, tokens or logs to the repository.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import operator_control_tower_proof as proof  # noqa: E402
import validate_public_json_artifacts as validator  # noqa: E402


DEFAULT_OUT = ROOT / ".tmp" / "factory-runs" / "control-tower" / "operator-control-tower-private-evidence-doctor.json"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_ref(label: str, path: Path | None) -> str:
    if path is None:
        return f"missing:{label}"
    return proof.private_evidence_ref(label)


def load_private_json(path: Path | None, label: str, errors: list[str]) -> dict[str, Any] | None:
    if path is None:
        errors.append(f"{label}: missing")
        return None
    if proof.path_is_inside_repo(path):
        errors.append(f"{label}: private evidence path must be outside the public repository")
        return None
    try:
        return proof.load_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"{label}: {type(exc).__name__}")
        return None


def validate_if_present(
    schemas: dict[str, dict[str, Any]],
    label: str,
    artifact: dict[str, Any] | None,
    errors: list[str],
) -> None:
    if artifact is None:
        return
    errors.extend(f"{label}: {error}" for error in proof.validate_artifact(schemas, artifact))


def build_doctor_report(
    *,
    mapping_path: Path | None = None,
    runtime_event_path: Path | None = None,
    bridge_health_path: Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    schemas = validator.load_schemas()

    mapping = load_private_json(mapping_path, "mapping", errors)
    runtime_event = load_private_json(runtime_event_path, "runtime_registration_event", errors)
    bridge_health = load_private_json(bridge_health_path, "bridge_health", errors)

    validate_if_present(schemas, "mapping", mapping, errors)
    validate_if_present(schemas, "runtime_registration_event", runtime_event, errors)
    validate_if_present(schemas, "bridge_health", bridge_health, errors)

    checks = {
        "mapping_file_present": mapping is not None,
        "runtime_registration_event_file_present": runtime_event is not None,
        "bridge_health_file_present": bridge_health is not None,
        "mapping_has_real_refs": mapping is not None
        and all(proof.is_real_ref(mapping.get(field)) for field in proof.MAPPING_REQUIRED_REAL_REFS),
        "runtime_event_registers_owner_decision": proof.runtime_event_registers_owner_decision(runtime_event),
        "mapping_runtime_project_matches": proof.mapping_runtime_project_matches(mapping, runtime_event),
        "bridge_health_uses_contract": proof.bridge_health_uses_contract(bridge_health),
        "bridge_health_checks_pass": proof.bridge_health_checks_pass(bridge_health),
        "bridge_health_has_real_evidence_refs": proof.bridge_health_has_real_evidence_refs(bridge_health),
        "private_inputs_schema_valid": not errors,
    }
    blocking_items = [key for key, value in checks.items() if not value]
    result = "PASS" if not blocking_items else "BLOCKED"

    report = {
        "$schema": "https://overkill-factory.dev/schemas/operator-control-tower-private-evidence-doctor.schema.json",
        "record_type": "operator_control_tower_private_evidence_doctor",
        "created_at": created_at or utc_now(),
        "result": result,
        "summary": "Private Operator Control Tower evidence is ready for the production proof."
        if result == "PASS"
        else "Private Operator Control Tower evidence is not ready for the production proof.",
        "scope": "private Control Tower mapping, runtime approval event and bridge health evidence",
        "environment_ref": "redacted-private-operator-control-tower-evidence",
        "evidence_refs": sorted(
            {
                safe_ref("mapping", mapping_path),
                safe_ref("runtime_registration_event", runtime_event_path),
                safe_ref("bridge_health", bridge_health_path),
            }
        ),
        "limits": [
            "This doctor report is public-safe and stores only redacted booleans and external evidence labels.",
            "PASS only means the private evidence files are shaped well enough for the production proof harness.",
            "The production proof and update receipt must still be generated separately.",
        ],
        "decision": {
            "operator_control_tower_production_proof_input": "ready" if result == "PASS" else "blocked",
            "next_required_action": "run_operator_control_tower_proof"
            if result == "PASS"
            else "collect_or_fix_private_control_tower_evidence",
        },
        "checks": checks,
        "blocking_items": blocking_items,
        "input_errors": sorted(set(errors)),
    }
    proof.assert_public_safe(report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--runtime-registration-event", type=Path)
    parser.add_argument("--bridge-health", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_doctor_report(
        mapping_path=args.mapping,
        runtime_event_path=args.runtime_registration_event,
        bridge_health_path=args.bridge_health,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": report["result"], "out": proof.repo_ref(args.out)}, indent=2))
    return 0 if report["result"] == "PASS" else 1


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
