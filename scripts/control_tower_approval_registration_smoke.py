#!/usr/bin/env python3
"""Create a public-safe Control Tower approval registration smoke receipt.

This proves the owner cockpit only turns a structured response into a
runtime-registerable event when the approval id, role, scope and expiry all
match the original request.
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
    + PRIVATE_ENV,
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def pending_approval(created_at: str) -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/approval-request.schema.json",
        "approval_id": "appr-example-plan",
        "project_id": "example-control-tower-project",
        "approval_type": "plan",
        "status": "pending",
        "risk": "R3",
        "scope": "approve bounded execution plan for first safe slice",
        "consequence": "The runtime may record a plan approval event, but execution still waits for Ready Gate.",
        "not_authorized": ["production release", "unbounded spend", "broad credential access"],
        "requested_by": "factory-concierge",
        "evidence_refs": ["docs/control-tower/discord-control-tower-os.md"],
        "expires_at": "2026-06-11T00:00:00Z",
        "created_at": created_at,
    }


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def evaluate_decision(
    approval: dict[str, Any],
    decision: dict[str, Any],
    *,
    now: str,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if decision.get("approval_id") != approval["approval_id"]:
        reasons.append("approval_id mismatch")
    if decision.get("actor_role") != "Factory Owner":
        reasons.append("actor role is not authorized")
    if decision.get("decision") not in {"approved", "rejected", "needs_changes"}:
        reasons.append("decision is not structured")
    if decision.get("scope") != approval["scope"]:
        reasons.append("decision scope does not match request")
    if parse_time(now) > parse_time(str(approval["expires_at"])):
        reasons.append("approval request expired")
    return (not reasons, reasons)


def register_decision(
    approval: dict[str, Any],
    decision: dict[str, Any],
    *,
    now: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    accepted, reasons = evaluate_decision(approval, decision, now=now)
    if not accepted:
        return (
            dict(approval),
            {
                "accepted": False,
                "reasons": reasons,
                "decision": decision,
            },
        )

    event = {
        "$schema": "https://overkill-factory.dev/schemas/control-tower-event.schema.json",
        "event_id": "evt-approval-recorded-example-plan",
        "event_type": "approval_recorded",
        "severity": "P2",
        "project_id": approval["project_id"],
        "source": "bridge",
        "summary": "Structured owner plan approval is ready to register in the runtime.",
        "details": "Contract-only smoke. No real runtime mutation is claimed.",
        "action_required": False,
        "owner_role": decision["actor_role"],
        "evidence_refs": list(approval.get("evidence_refs", [])),
        "discord_target": "owner-approvals",
        "created_at": now,
    }
    registered = dict(approval)
    registered.update(
        {
            "status": decision["decision"],
            "decided_by": decision["actor_role"],
            "decision_event_ref": event["event_id"],
        }
    )
    return registered, event


def validate_artifact(schemas: dict[str, dict[str, Any]], artifact: dict[str, Any]) -> None:
    schema_ref = str(artifact["$schema"])
    schema = schemas[validator.schema_name(schema_ref)]
    errors = validator.validate_node(schema, artifact, "$")
    if errors:
        raise AssertionError("; ".join(errors))


def assert_public_safe(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    match = PRIVATE_RE.search(text)
    if match:
        raise AssertionError(f"private-looking text in public smoke: {match.group(0)}")


def build_receipt(created_at: str | None = None) -> dict[str, Any]:
    timestamp = created_at or utc_now()
    approval = pending_approval(timestamp)
    valid_decision = {
        "approval_id": approval["approval_id"],
        "actor_role": "Factory Owner",
        "decision": "approved",
        "scope": approval["scope"],
    }
    registered_approval, approval_event = register_decision(
        approval,
        valid_decision,
        now="2026-06-10T12:00:00Z",
    )

    negative_inputs = [
        (
            "wrong_role",
            {
                "approval_id": approval["approval_id"],
                "actor_role": "Observer",
                "decision": "approved",
                "scope": approval["scope"],
            },
            "2026-06-10T12:00:00Z",
        ),
        (
            "expired_decision",
            valid_decision,
            "2026-06-12T00:00:00Z",
        ),
        (
            "scope_expansion",
            {
                "approval_id": approval["approval_id"],
                "actor_role": "Factory Owner",
                "decision": "approved",
                "scope": approval["scope"] + " plus production release",
            },
            "2026-06-10T12:00:00Z",
        ),
        (
            "unknown_approval",
            {
                "approval_id": "appr-unknown",
                "actor_role": "Factory Owner",
                "decision": "approved",
                "scope": approval["scope"],
            },
            "2026-06-10T12:00:00Z",
        ),
        (
            "ambiguous_decision",
            {
                "approval_id": approval["approval_id"],
                "actor_role": "Factory Owner",
                "decision": "maybe",
                "scope": approval["scope"],
            },
            "2026-06-10T12:00:00Z",
        ),
    ]
    negative_cases: list[dict[str, Any]] = []
    for name, decision, now in negative_inputs:
        _, outcome = register_decision(approval, decision, now=now)
        negative_cases.append({"case": name, "accepted": outcome["accepted"], "reasons": outcome["reasons"]})

    registration_checks = {
        "valid_decision_records_event": (
            registered_approval["status"] == "approved"
            and registered_approval["decision_event_ref"] == approval_event["event_id"]
            and approval_event["event_type"] == "approval_recorded"
        ),
        "wrong_role_rejected": any(
            case["case"] == "wrong_role" and not case["accepted"] for case in negative_cases
        ),
        "expired_decision_rejected": any(
            case["case"] == "expired_decision" and not case["accepted"] for case in negative_cases
        ),
        "scope_expansion_rejected": any(
            case["case"] == "scope_expansion" and not case["accepted"] for case in negative_cases
        ),
        "unknown_approval_rejected": any(
            case["case"] == "unknown_approval" and not case["accepted"] for case in negative_cases
        ),
        "ambiguous_decision_rejected": any(
            case["case"] == "ambiguous_decision" and not case["accepted"] for case in negative_cases
        ),
        "runtime_mutation_not_claimed": (
            approval_event["source"] == "bridge"
            and "No real runtime mutation is claimed" in approval_event["details"]
        ),
    }

    receipt = {
        "$schema": "https://overkill-factory.dev/schemas/control-tower-approval-registration-smoke.schema.json",
        "smoke_id": "control-tower-approval-registration-smoke",
        "result": "PASS" if all(registration_checks.values()) else "FAIL",
        "pending_approval": approval,
        "registered_approval": registered_approval,
        "approval_event": approval_event,
        "negative_cases": negative_cases,
        "registration_checks": registration_checks,
        "evidence_refs": [
            "docs/control-tower/discord-control-tower-os.md",
            "docs/methodology/overkill-factory-vfinal.md",
        ],
        "created_at": timestamp,
    }

    schemas = validator.load_schemas()
    for artifact in [approval, registered_approval, approval_event, receipt]:
        validate_artifact(schemas, artifact)
    assert_public_safe(receipt)
    if receipt["result"] != "PASS":
        raise AssertionError(f"approval registration checks failed: {registration_checks}")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "validation" / "control-tower" / "control-tower-approval-registration-smoke.json",
    )
    args = parser.parse_args()

    receipt = build_receipt()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
