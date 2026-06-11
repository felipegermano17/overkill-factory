#!/usr/bin/env python3
"""Diagnose private Discord owner setup evidence without leaking it."""

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


DEFAULT_OUT = ROOT / "validation" / "control-tower" / "operator-control-tower-owner-setup-doctor.json"

REQUIRED_OWNER_CHECKS = [
    "server_exists",
    "bot_application_created",
    "bot_invited_to_server",
    "message_content_intent_enabled",
    "server_members_intent_enabled",
    "owner_user_allowlisted",
    "required_channels_exist",
    "owner_approval_channel_restricted",
    "bot_health_channel_available",
    "least_privilege_permissions_reviewed",
    "token_stored_outside_public_repo",
    "offboarding_plan_ready",
]

REQUIRED_CHANNELS = [
    "dashboard",
    "intake",
    "owner_approvals",
    "access_requests",
    "blockers",
    "evidence_feed",
    "release_room",
    "bot_health",
    "projects_area",
]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_ref(path: Path | None) -> str:
    if path is None:
        return "missing:discord-owner-setup"
    return "external:discord-owner-setup"


def load_private_json(path: Path | None, errors: list[str]) -> dict[str, Any] | None:
    if path is None:
        errors.append("owner_setup: missing")
        return None
    if proof.path_is_inside_repo(path):
        errors.append("owner_setup: private evidence path must be outside the public repository")
        return None
    try:
        return proof.load_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"owner_setup: {type(exc).__name__}")
        return None


def validate_if_present(artifact: dict[str, Any] | None, errors: list[str]) -> None:
    if artifact is None:
        return
    schemas = validator.load_schemas()
    errors.extend(f"owner_setup: {error}" for error in proof.validate_artifact(schemas, artifact))


def all_required_checks_passed(owner_setup: dict[str, Any] | None) -> bool:
    if owner_setup is None:
        return False
    checks = owner_setup.get("checks")
    return isinstance(checks, dict) and all(checks.get(key) is True for key in REQUIRED_OWNER_CHECKS)


def required_channel_refs_present(owner_setup: dict[str, Any] | None) -> bool:
    if owner_setup is None:
        return False
    channels = owner_setup.get("required_channels")
    return isinstance(channels, dict) and all(proof.is_real_ref(channels.get(key)) for key in REQUIRED_CHANNELS)


def has_real_evidence_refs(owner_setup: dict[str, Any] | None) -> bool:
    if owner_setup is None:
        return False
    refs = owner_setup.get("evidence_refs")
    return isinstance(refs, list) and bool(refs) and all(proof.is_real_ref(ref) for ref in refs)


def build_doctor_report(
    *,
    owner_setup_path: Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    owner_setup = load_private_json(owner_setup_path, errors)
    validate_if_present(owner_setup, errors)

    checks = {
        "owner_setup_file_present": owner_setup is not None,
        "owner_setup_schema_valid": not errors,
        "owner_setup_result_passed": owner_setup is not None and owner_setup.get("result") == "PASS",
        "required_owner_checks_passed": all_required_checks_passed(owner_setup),
        "required_channel_refs_present": required_channel_refs_present(owner_setup),
        "owner_setup_has_real_evidence_refs": has_real_evidence_refs(owner_setup),
    }
    blocking_items = [key for key, value in checks.items() if not value]
    result = "PASS" if not blocking_items else "BLOCKED"

    report = {
        "$schema": "https://overkill-factory.dev/schemas/operator-control-tower-owner-setup-doctor.schema.json",
        "record_type": "operator_control_tower_owner_setup_doctor",
        "created_at": created_at or utc_now(),
        "result": result,
        "summary": "Discord owner setup evidence is ready for the Operator Control Tower proof."
        if result == "PASS"
        else "Discord owner setup evidence is not ready for the Operator Control Tower proof.",
        "scope": "private Discord server, bot, intents, channel, permission and offboarding evidence",
        "environment_ref": "redacted-private-discord-owner-setup",
        "evidence_refs": [safe_ref(owner_setup_path)],
        "limits": [
            "This doctor report is public-safe and stores only redacted booleans and external evidence labels.",
            "PASS means the owner-side Discord setup evidence is shaped and complete enough for the Control Tower production proof.",
            "It does not store real Discord ids, private credentials, private endpoints or raw logs.",
        ],
        "decision": {
            "owner_setup_input": "ready" if result == "PASS" else "blocked",
            "next_required_action": "run_operator_control_tower_private_evidence_doctor"
            if result == "PASS"
            else "collect_or_fix_private_discord_owner_setup_evidence",
        },
        "checks": checks,
        "blocking_items": blocking_items,
        "input_errors": sorted(set(errors)),
    }
    proof.assert_public_safe(report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-setup", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_doctor_report(owner_setup_path=args.owner_setup)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": report["result"], "out": proof.repo_ref(args.out)}, indent=2))
    return 0 if report["result"] == "PASS" else 1


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
