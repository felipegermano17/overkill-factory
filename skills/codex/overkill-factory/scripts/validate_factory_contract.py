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

RECEIPT_REQUIRED = {
    "changed",
    "artifact_paths",
    "verification_commands",
    "verification_result",
    "reviewer_required",
    "next_action",
}


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
        elif risk in {"R3", "R4"} and package.get("auditor_required") is not True:
            errors.append("auditor_required=true required for R3/R4 onchain work")
    if risk in {"R3", "R4"} and not data.get("security_scan_packet"):
        errors.append("security_scan_packet required for R3/R4 work")
    if risk in {"R3", "R4"} and not data.get("human_gate_packet"):
        errors.append("human_gate_packet required for R3/R4 work")
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
