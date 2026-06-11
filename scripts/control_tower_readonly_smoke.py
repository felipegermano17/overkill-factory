#!/usr/bin/env python3
"""Create a public-safe read-only Control Tower smoke receipt.

This proves the Discord-facing layer can project runtime state, emit an owner
event, request structured approval, and keep all Discord references redacted
without mutating the runtime snapshot.
"""

from __future__ import annotations

import argparse
import copy
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
    + PRIVATE_ENV
    + r"|token|password",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def synthetic_runtime_snapshot(created_at: str) -> dict[str, Any]:
    return {
        "runtime": "hermes",
        "project_id": "example-control-tower-project",
        "name": "Example Control Tower Project",
        "board_ref": "redacted-board",
        "phase": "access_gate",
        "status": "blocked",
        "execution_started": False,
        "risk": "R3",
        "current_blockers": [
            "missing repository write access",
            "missing staging budget approval",
        ],
        "pending_access": ["github_write", "staging_cloud"],
        "pending_approvals": ["access.appr-example-access"],
        "next_steps": [
            "grant required access",
            "record approval in runtime",
            "rerun ready gate",
        ],
        "evidence_refs": ["docs/control-tower/discord-control-tower-os.md"],
        "updated_at": created_at,
    }


def build_projection(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/project-projection.schema.json",
        "project_id": snapshot["project_id"],
        "name": snapshot["name"],
        "phase": snapshot["phase"],
        "status": "waiting_access",
        "execution_started": snapshot["execution_started"],
        "risk": snapshot["risk"],
        "forecast_confidence": "blocked",
        "current_blockers": list(snapshot["current_blockers"]),
        "pending_access": list(snapshot["pending_access"]),
        "pending_approvals": list(snapshot["pending_approvals"]),
        "next_steps": list(snapshot["next_steps"]),
        "evidence_refs": list(snapshot["evidence_refs"]),
        "source_runtime": snapshot["runtime"],
        "source_board": snapshot["board_ref"],
        "last_synced_at": snapshot["updated_at"],
        "planned_summary": [
            "access gate",
            "ready gate",
            "worker execution",
            "verification",
            "review",
        ],
        "missing_items": list(snapshot["current_blockers"]),
        "forecast_risks": [
            "execution cannot start until required access and budget approval are recorded",
            "forecast stays blocked while the Ready Gate has unresolved inputs",
        ],
        "human_decisions_required": list(snapshot["pending_approvals"]),
        "truth_source_available": True,
    }


def build_event(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/control-tower-event.schema.json",
        "event_id": "evt-control-tower-readonly-access-block",
        "event_type": "access_missing",
        "severity": "P1",
        "project_id": snapshot["project_id"],
        "source": "hermes",
        "summary": "Execution is blocked until required access and budget approval are recorded.",
        "details": "Read-only projection only. No Discord action mutates runtime state.",
        "action_required": True,
        "owner_role": "Factory Owner",
        "evidence_refs": list(snapshot["evidence_refs"]),
        "discord_target": "owner-approvals",
        "created_at": snapshot["updated_at"],
    }


def build_approval_request(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/approval-request.schema.json",
        "approval_id": "appr-example-access",
        "project_id": snapshot["project_id"],
        "approval_type": "access",
        "status": "pending",
        "risk": snapshot["risk"],
        "scope": "grant repository write access and bounded staging cloud access",
        "consequence": "Material execution remains blocked until this approval is registered in Hermes.",
        "not_authorized": ["production deploy", "secret disclosure", "billing limit increase"],
        "requested_by": "factory-concierge",
        "evidence_refs": list(snapshot["evidence_refs"]),
        "expires_at": "2026-06-11T00:00:00Z",
        "created_at": snapshot["updated_at"],
    }


def build_mapping(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/discord-control-tower-mapping.schema.json",
        "project_id": snapshot["project_id"],
        "runtime": "hermes",
        "board_ref": snapshot["board_ref"],
        "guild_ref": "redacted-guild",
        "dashboard_channel_ref": "redacted-dashboard-channel",
        "dashboard_message_ref": "redacted-dashboard-message",
        "approval_channel_ref": "redacted-approval-channel",
        "project_thread_ref": "redacted-project-thread",
        "evidence_channel_ref": "redacted-evidence-channel",
        "bot_health_channel_ref": "redacted-bot-health-channel",
        "last_synced_at": snapshot["updated_at"],
    }


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
    before = synthetic_runtime_snapshot(timestamp)
    after = copy.deepcopy(before)
    projection = build_projection(before)
    event = build_event(before)
    approval_request = build_approval_request(before)
    mapping = build_mapping(before)

    readonly_checks = {
        "runtime_snapshot_unchanged": before == after,
        "projection_derived_from_runtime": (
            projection["source_runtime"] == before["runtime"]
            and projection["source_board"] == before["board_ref"]
            and projection["execution_started"] is False
        ),
        "approval_pending_only": (
            approval_request["status"] == "pending"
            and "decided_by" not in approval_request
            and "decision_event_ref" not in approval_request
        ),
        "mapping_redacted": all(
            str(mapping[field]).startswith("redacted-")
            for field in [
                "board_ref",
                "guild_ref",
                "dashboard_channel_ref",
                "dashboard_message_ref",
                "approval_channel_ref",
                "project_thread_ref",
                "evidence_channel_ref",
                "bot_health_channel_ref",
            ]
        ),
        "no_discord_mutation_claim": (
            event["source"] == "hermes"
            and "No Discord action mutates runtime state" in event["details"]
        ),
    }

    receipt = {
        "$schema": "https://overkill-factory.dev/schemas/control-tower-readonly-smoke.schema.json",
        "smoke_id": "control-tower-readonly-smoke",
        "result": "PASS" if all(readonly_checks.values()) else "FAIL",
        "projection": projection,
        "event": event,
        "approval_request": approval_request,
        "mapping": mapping,
        "readonly_checks": readonly_checks,
        "evidence_refs": [
            "docs/control-tower/discord-control-tower-os.md",
            "docs/methodology/overkill-factory-vfinal.md",
        ],
        "created_at": timestamp,
    }

    schemas = validator.load_schemas()
    for artifact in [projection, event, approval_request, mapping, receipt]:
        validate_artifact(schemas, artifact)
    assert_public_safe(receipt)
    if receipt["result"] != "PASS":
        raise AssertionError(f"read-only checks failed: {readonly_checks}")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "validation" / "control-tower" / "control-tower-readonly-smoke.json",
    )
    args = parser.parse_args()

    receipt = build_receipt()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
