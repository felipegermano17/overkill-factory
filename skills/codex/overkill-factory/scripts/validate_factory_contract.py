#!/usr/bin/env python3
"""Lightweight Overkill Factory card/receipt validator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


CARD_REQUIRED = {
    "factory_method_version",
    "phase",
    "surfaces",
    "risk_initial",
    "risk_effective",
    "authority_max",
    "owner_worker",
    "executor_identity",
    "reviewer_identity",
    "runtime_decision",
    "runtime_contract",
    "security_contract",
    "forbidden_actions",
    "done_definition",
    "transition_event_required",
    "kanban_transition_event_ref",
}

ALLOWED_SOURCE_STATES = {"backlog", "compiled", "inference", "promoted", "raw", "rejected"}

RECEIPT_REQUIRED = {
    "changed",
    "artifact_paths",
    "verification_commands",
    "verification_result",
    "reviewer_required",
    "next_action",
}
V2_APPROVAL_KEYS = ["qa", "independent_review", "security_review", "cybersecurity_review", "cto_gate", "felipe_gate"]


def load_json(path: Path) -> dict:
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1])
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def validate_card(data: dict) -> list[str]:
    errors: list[str] = []
    missing = sorted(CARD_REQUIRED - set(data))
    if missing:
        errors.append("missing card fields: " + ", ".join(missing))
    source_state = str(data.get("source_state", "")).strip()
    if source_state and source_state not in ALLOWED_SOURCE_STATES:
        errors.append("source_state must be one of " + ", ".join(sorted(ALLOWED_SOURCE_STATES)))
    if data.get("executor_identity") == data.get("reviewer_identity"):
        errors.append("executor_identity and reviewer_identity must differ")
    surfaces = {str(v).lower() for v in data.get("surfaces", []) if str(v).strip()}
    risk = str(data.get("risk_effective", "")).upper()
    if surfaces & {"ux", "frontend", "mobile", "wallet-ui"} and not data.get("product_face_packet"):
        errors.append("product_face_packet required for product-face surfaces")
    if surfaces & {"solana-quasar", "account-pda", "cpi", "compute-units", "funds", "mainnet"}:
        package = data.get("onchain_work_package")
        if not isinstance(package, dict):
            errors.append("onchain_work_package required for onchain surfaces")
        elif not package.get("quasar_source_ref"):
            errors.append("quasar_source_ref required for onchain work")
        elif risk in {"R3", "R4"} and package.get("auditor_required") is not True:
            errors.append("auditor_required=true required for R3/R4 onchain work")
    if risk in {"R3", "R4"} and not data.get("security_scan_packet"):
        errors.append("security_scan_packet required for R3/R4 work")
    if risk in {"R3", "R4"} and not data.get("human_gate_packet"):
        errors.append("human_gate_packet required for R3/R4 work")
    review = data.get("review", {}) if isinstance(data.get("review"), dict) else {}
    if data.get("risk_class") == "R3-financial-critical" and review.get("CTO_gate_required") is not True:
        errors.append("review.CTO_gate_required=true required for R3-financial-critical work")
    if risk in {"R3", "R4"} and surfaces & {"security", "cybersecurity", "auth", "infra", "backend", "api", "wallet", "funds", "mainnet", "onchain", "solana", "solana-quasar"}:
        if data.get("security_role_separation") is not True and not data.get("security_role_separation_exception"):
            errors.append("security_role_separation=true or security_role_separation_exception required for R3/R4 security-sensitive work")
    if risk == "R4" and not data.get("r4_gate"):
        errors.append("r4_gate required for R4 work")
    return errors


def validate_receipt(data: dict) -> list[str]:
    errors: list[str] = []
    receipt = data.get("receipt_five")
    if not isinstance(receipt, dict):
        return ["receipt_five object is required"]
    missing = sorted(RECEIPT_REQUIRED - set(receipt))
    if missing:
        errors.append("missing receipt_five fields: " + ", ".join(missing))
    if receipt.get("reviewer_required") is True and not receipt.get("reviewer_result"):
        errors.append("reviewer_result required when reviewer_required=true")
    if not isinstance(data.get("kanban_transition_event"), dict):
        errors.append("kanban_transition_event object is required")
    scan = data.get("security_scan_result")
    if isinstance(scan, dict):
        required = ["scanner_agent", "tool", "result", "findings_summary"]
        missing = [field for field in required if not str(scan.get(field) or "").strip()]
        if missing:
            errors.append("security_scan_result missing " + ", ".join(missing))
        if not isinstance(scan.get("scope"), list) or not any(str(item).strip() for item in scan.get("scope", [])):
            errors.append("security_scan_result scope must be a non-empty string array")
        if not isinstance(scan.get("evidence_refs"), list) or not any(str(item).strip() for item in scan.get("evidence_refs", [])):
            errors.append("security_scan_result evidence_refs must be a non-empty string array")
        security_ref = " ".join(str(scan.get(field) or "") for field in ("scanner_agent", "tool")).lower()
        if "codex-security" not in security_ref and "cybersecurity" not in security_ref:
            errors.append("security_scan_result must reference Codex Security or cybersecurity")
        if str(scan.get("result") or "").upper() not in {"PASS", "WAIVED"}:
            errors.append("security_scan_result result must be PASS or WAIVED")
        if scan.get("blocking_findings") is True and not isinstance(data.get("security_exception"), dict):
            errors.append("security_scan_result blocking findings require security_exception")
    if data.get("hermes_kaxis_v2_completion_required") is True:
        has_evidence = any(
            isinstance(data.get(field), list) and any(str(item).strip() for item in data.get(field, []))
            for field in ("evidence_paths", "evidence", "artifacts")
        )
        if not has_evidence:
            errors.append("Hermes V2 metadata requires evidence_paths, evidence or artifacts")
        verification = data.get("verification")
        commands = verification.get("commands") or verification.get("verify_commands") or verification.get("tests") if isinstance(verification, dict) else None
        if not isinstance(verification, dict) or verification.get("passed") is not True or not isinstance(commands, list) or not any(str(item).strip() for item in commands):
            errors.append("Hermes V2 metadata requires verification.passed=true with commands")
        sandbox = data.get("sandbox")
        invariants = sandbox.get("invariants") or sandbox.get("invariant_results") if isinstance(sandbox, dict) else None
        if not isinstance(sandbox, dict) or sandbox.get("passed") is not True or not isinstance(invariants, list) or not invariants:
            errors.append("Hermes V2 metadata requires sandbox.passed=true with invariants")
        rollback = data.get("rollback")
        if not isinstance(rollback, dict) or rollback.get("verified") is not True or not str(rollback.get("evidence") or rollback.get("evidence_path") or "").strip():
            errors.append("Hermes V2 metadata requires rollback.verified=true with evidence")
        approvals = data.get("approvals")
        if not isinstance(approvals, dict):
            errors.append("Hermes V2 metadata requires approvals object")
        else:
            missing = []
            for key in V2_APPROVAL_KEYS:
                approval = approvals.get(key)
                if not isinstance(approval, dict) or approval.get("approved") is not True or not str(approval.get("actor") or approval.get("by") or approval.get("profile") or "").strip() or not str(approval.get("at") or approval.get("timestamp") or approval.get("time") or "").strip():
                    missing.append(key)
            if missing:
                errors.append("Hermes V2 metadata missing approval records: " + ", ".join(missing))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--receipt", action="store_true")
    args = parser.parse_args()

    data = load_json(args.path)
    errors = validate_receipt(data) if args.receipt else validate_card(data)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
