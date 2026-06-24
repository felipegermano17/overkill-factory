#!/usr/bin/env python3
"""Run a multi-context Overkill Factory validation battery."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path, PureWindowsPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FACTORYCTL = ROOT / "scripts" / "factoryctl.py"
BATTERY_SCHEMA = "https://overkill-factory.dev/schemas/factory-battery-result.schema.json"


def load_factoryctl() -> Any:
    spec = importlib.util.spec_from_file_location("battery_factoryctl", FACTORYCTL)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load factoryctl from scripts/factoryctl.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["battery_factoryctl"] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def public_path_ref(path: Path, fallback: str = "artifact") -> str:
    raw = str(path)
    windows_path = PureWindowsPath(raw)
    if windows_path.is_absolute() or (len(raw) >= 2 and raw[1] == ":"):
        return f"external:{windows_path.name or fallback}"
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except (OSError, ValueError):
        return f"external:{path.name or fallback}"


def scenario_pass(name: str, *, expected: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    for worker in expected.get("required_workers", []):
        if worker not in observed.get("required_workers", []):
            failures.append(f"missing required worker {worker}")
    for worker in expected.get("blocked_workers", []):
        if worker not in observed.get("blocked_workers", []):
            failures.append(f"missing blocked worker {worker}")
    expected_status = expected.get("gate_status")
    if expected_status and observed.get("gate_status") != expected_status:
        failures.append(f"gate_status expected {expected_status}, got {observed.get('gate_status')}")
    expected_action = expected.get("transition_action")
    if expected_action and observed.get("transition_action") != expected_action:
        failures.append(
            f"transition_action expected {expected_action}, got {observed.get('transition_action')}"
        )
    min_reasons = expected.get("min_blocked_reasons")
    if min_reasons is not None and len(observed.get("blocked_reasons", [])) < int(min_reasons):
        failures.append(f"expected at least {min_reasons} blocked reasons")
    return {
        "name": name,
        "passed": not failures,
        "failures": failures,
        "expected": expected,
        "observed": observed,
    }


def worker_result(factoryctl: Any, worker_id: str, card: dict[str, Any], evidence_ref: str) -> dict[str, Any]:
    if worker_id == "human-gate-clerk":
        return factoryctl.build_human_gate_record(
            card,
            gate_type=None,
            decision="approved",
            human_actor="battery-test-operator",
            approved_scope=["synthetic validation only"],
            forbidden_scope=card.get("forbidden_actions", []),
            required_changes=[],
            risk_owner="battery-risk-owner",
            security_owner="battery-security-owner",
            rollback_owner="battery-rollback-owner",
            evidence_refs=[evidence_ref],
            notes="Synthetic battery approval only; not reusable for real product work.",
            evidence_kind="synthetic",
            reusable_for_product=False,
        )
    record = factoryctl.build_worker_result(
        worker_id,
        card,
        result="PASS",
        tool_or_profile=f"battery:{worker_id}",
        executed_by="factory-battery",
        evidence_refs=[evidence_ref],
        blocking_findings=False,
        findings_summary="Synthetic battery result passed.",
        next_action="Run real specialist for product work.",
        evidence_kind="synthetic",
        reusable_for_product=False,
    )
    if worker_id == "evidence-reconciler":
        record["valid"] = True
    return record


def solana_bank_r4_card(factoryctl: Any, *, phase: str) -> dict[str, Any]:
    card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md")
    minimal_card = factoryctl.load_json_like(ROOT / "examples" / "minimal-hermes-project" / "card.md")
    card.update(
        {
            "card_id": f"KFP-SOLANA-BANK-R4-{phase}",
            "slice_id": "SOLANA_BANK_START_READINESS",
            "source_refs": [
                "Overkill Factory Solana bank R4 routing battery",
                "solanabr/solana-ai-kit@v2.0.2",
                "Solana wallet/signing/funds/mainnet risk controls",
            ],
            "outcome": "Route a Solana onchain digital bank workstream through R4 controls without authorizing execution.",
            "acceptance_criteria": [
                "router requires Solana, wallet, security, human, remote-proof and supply-chain controls",
                "mainnet, signing, funds and key access remain forbidden without explicit gates",
            ],
            "scope_in": [
                "gate validation only",
                "digital bank route classification",
                "wallet/signing/funds/mainnet risk classification",
            ],
            "scope_out": [
                "deploy",
                "devnet write",
                "mainnet write",
                "wallet signing",
                "funds movement",
                "key access",
                "customer release",
            ],
            "risk_class": "R4-financial-mainnet-critical",
            "why_this_class": "Digital banking, wallet signing, funds and mainnet authority are R4 even before implementation.",
            "phase": phase,
            "surfaces": [
                "solana",
                "onchain",
                "program",
                "account-pda",
                "cpi",
                "compute-units",
                "wallet",
                "wallet-ui",
                "transaction",
                "signing",
                "funds",
                "mainnet",
                "secrets",
                "release",
                "solana-test",
                "onchain-qa",
                "frontend",
            ],
            "risk_initial": "R4",
            "risk_effective": "R4",
            "authority_max": "validate_gate_only",
            "runtime_contract": {
                "mode": "read_only_gate_test",
                "remote_proof_required": True,
                "ttl": "ephemeral",
                "cost_owner": "operator",
                "cleanup_plan": "destroy test resources after proof",
                "secret_policy": "no real secrets or keys",
                "artifact_policy": "public-safe summaries only",
            },
            "human_gate_packet": {
                "gate_type": "R4_mainnet_financial",
                "required_approvers": ["product-owner", "CTO", "security-reviewer"],
                "decision_state": "pending_before_execution",
                "risk_owner": "product-owner",
                "security_owner": "security-reviewer",
                "rollback_owner": "release-worker",
                "waiver_policy": "no waiver without explicit human record",
                "operator_briefing_package_ref": "reports/factory-battery-r4/human-gate/operator-briefing-package.json",
                "approval_request_ref": "reports/factory-battery-r4/human-gate/APPROVAL_REQUEST.json",
                "evidence_index_ref": "reports/factory-battery-r4/human-gate/EVIDENCE_INDEX.json",
                "owner_review_ref": "reports/factory-battery-r4/human-gate/OWNER_REVIEW.md",
                "required_decision_assets": [
                    "markdown_document",
                    "pdf_document",
                    "approval_request_json",
                    "evidence_index_json",
                    "owner_review_markdown",
                ],
                "optional_explainer_assets": ["diagram", "video_explainer", "audio_explainer"],
                "decision_package_delivery": {
                    "operator_interface": "telegram",
                    "push_required": True,
                    "summary_only_forbidden": True,
                    "material_before_question": True,
                    "attachment_order": ["markdown_document", "pdf_document", "diagram", "video_explainer"],
                },
            },
            "r4_gate": {
                "gate_type": "R4_mainnet_financial",
                "decision_state": "pending_before_execution",
                "risk_owner": "product-owner",
                "security_owner": "security-reviewer",
                "rollback_owner": "release-worker",
                "required_approvers": ["product-owner", "CTO", "security-reviewer"],
                "waiver_policy": "no waiver without explicit human record",
            },
            "forbidden_actions": [
                "deploy",
                "devnet_write",
                "mainnet_write",
                "wallet_signing",
                "funds_movement",
                "key_access",
                "secret_access",
                "production_release",
            ],
        }
    )
    card["product_experience_plan"] = minimal_card["product_experience_plan"]
    card["product_face_packet"] = minimal_card["product_face_packet"]
    card["project_design_system"] = minimal_card["project_design_system"]
    card["professional_design_process"] = minimal_card["professional_design_process"]
    card["onchain_work_package"]["auditor_tool_ref"] = "solanabr/solana-ai-kit@v2.0.2 + solanabr/Auditor"
    card["security_scan_packet"]["required_tools"] = [
        "codex-security:security-scan",
        "solanabr/solana-ai-kit@v2.0.2",
        "solanabr/Auditor",
    ]
    return card


def write_required_results(factoryctl: Any, card: dict[str, Any], card_name: str, out_dir: Path) -> Path:
    results_dir = out_dir / card_name / "worker-results"
    evidence_dir = out_dir / card_name / "evidence"
    results_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for worker_id in factoryctl.required_worker_ids(card):
        evidence_path = evidence_dir / f"{worker_id}.md"
        evidence_ref = "README.md"
        evidence_path.write_text(
            "Synthetic battery evidence only; not a real product approval or audit.\n",
            encoding="utf-8",
        )
        record = worker_result(factoryctl, worker_id, card, evidence_ref)
        output_field = "human_gate_record" if worker_id == "human-gate-clerk" else record["record_type"]
        write_json(results_dir / f"{output_field}.json", record)
    return results_dir


def synthetic_done_receipt(factoryctl: Any, card: dict[str, Any]) -> dict[str, Any]:
    return {
        "receipt_five": {
            "changed": "Validated synthetic Solana battery card through ready and done gates.",
            "artifact_paths": ["examples/cards/v35_valid_onchain_auditor_scan.md"],
            "verification_commands": [
                "python scripts/factoryctl.py validate-card examples/cards/v35_valid_onchain_auditor_scan.md",
                "python scripts/factoryctl.py transition-plan --card examples/cards/v35_valid_onchain_auditor_scan.md --from-status ready --to-status done",
            ],
            "verification_result": "PASS",
            "reviewer_required": True,
            "reviewer_result": "PASS",
            "next_action": "Replace synthetic battery evidence with real Solana product evidence before production.",
        },
        "kanban_transition_event": {
            "from_status": "ready",
            "to_status": "done",
            "actor": "factory-battery",
            "worker": "evidence-reconciler",
            "receipt_refs": ["receipt_five", "receipt_five_reconciliation_result"],
            "artifact_refs": ["examples/cards/v35_valid_onchain_auditor_scan.md"],
            "allowed": True,
        },
        "receipt_five_reconciliation_result": worker_result(
            factoryctl,
            "evidence-reconciler",
            card,
            "examples/cards/v35_valid_onchain_auditor_scan.md",
        ),
        "independent_review_result": worker_result(
            factoryctl,
            "independent-reviewer",
            card,
            "examples/cards/v35_valid_onchain_auditor_scan.md",
        ),
    }


def run_battery(out_dir: Path) -> dict[str, Any]:
    factoryctl = load_factoryctl()
    scenarios: list[dict[str, Any]] = []
    ready_specs = [
        (
            "product-face-r2",
            ROOT / "examples" / "cards" / "v35_valid_product_face.md",
            {
                "gate_status": "ready_for_worker_execution",
                "required_workers": ["product-face", "independent-reviewer", "qa-verification-worker"],
            },
        ),
        (
            "solana-quasar-r3",
            ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md",
            {
                "gate_status": "ready_for_worker_execution",
                "required_workers": [
                    "codex-security",
                    "solana-quasar-auditor",
                    "human-gate-clerk",
                    "remote-proof-runner",
                    "supply-chain-gate",
                ],
            },
        ),
    ]
    for name, card_path, expected in ready_specs:
        card = factoryctl.load_json_like(card_path)
        report = factoryctl.build_gate_report(card)
        scenarios.append(
            scenario_pass(
                name,
                expected=expected,
                observed={
                    "gate_status": report["gate_status"],
                    "required_workers": report["required_workers"],
                    "blocked_workers": report["blocked_workers"],
                },
            )
        )

    bank_architecture_card = solana_bank_r4_card(factoryctl, phase="F7")
    bank_architecture_report = factoryctl.build_gate_report(bank_architecture_card)
    scenarios.append(
        scenario_pass(
            "solana-bank-r4-architecture",
            expected={
                "gate_status": "ready_for_worker_execution",
                "required_workers": [
                    "codex-security",
                    "solana-quasar-auditor",
                    "product-face",
                    "human-gate-clerk",
                    "appsec-owasp-specialist",
                    "cloud-infra-security-specialist",
                    "crypto-key-management-specialist",
                    "remote-proof-runner",
                    "release-ops-worker",
                    "public-safety-gate",
                    "supply-chain-gate",
                ],
            },
            observed={
                "gate_status": bank_architecture_report["gate_status"],
                "required_workers": bank_architecture_report["required_workers"],
                "blocked_workers": bank_architecture_report["blocked_workers"],
            },
        )
    )

    bank_implementation_card = solana_bank_r4_card(factoryctl, phase="F13")
    bank_implementation_report = factoryctl.build_gate_report(bank_implementation_card)
    scenarios.append(
        scenario_pass(
            "solana-bank-r4-implementation-blocked-without-product-face-result",
            expected={
                "gate_status": "blocked",
                "min_blocked_reasons": 1,
                "required_workers": [
                    "frontend-builder",
                    "solana-quasar-builder",
                    "solana-quasar-qa-engineer",
                    "wallet-transaction-builder",
                    "crypto-key-management-specialist",
                    "remote-proof-runner",
                    "release-ops-worker",
                    "supply-chain-gate",
                ],
            },
            observed={
                "gate_status": bank_implementation_report["gate_status"],
                "blocked_reasons": bank_implementation_report["card_validation_errors"]
                + bank_implementation_report["blocked_workers"],
                "required_workers": bank_implementation_report["required_workers"],
                "blocked_workers": bank_implementation_report["blocked_workers"],
            },
        )
    )

    invalid_specs = [
        ("invalid-product-face", ROOT / "examples" / "cards" / "v35_invalid_product_face.md"),
        ("invalid-onchain-no-auditor", ROOT / "examples" / "cards" / "v35_invalid_onchain_no_auditor.md"),
        ("invalid-r4-no-gate", ROOT / "examples" / "cards" / "v35_invalid_r4_no_gate.md"),
        ("invalid-security-no-scan", ROOT / "examples" / "cards" / "v35_invalid_security_no_scan.md"),
        ("invalid-self-review", ROOT / "examples" / "cards" / "v35_invalid_self_review.md"),
    ]
    for name, card_path in invalid_specs:
        card = factoryctl.load_json_like(card_path)
        report = factoryctl.build_gate_report(card)
        scenarios.append(
            scenario_pass(
                name,
                expected={"gate_status": "blocked", "min_blocked_reasons": 1},
                observed={
                    "gate_status": report["gate_status"],
                    "blocked_reasons": report["card_validation_errors"] + report["blocked_workers"],
                    "required_workers": report["required_workers"],
                    "blocked_workers": report["blocked_workers"],
                },
            )
        )

    solana_card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
    solana_card = factoryctl.load_json_like(solana_card_path)
    blocked_receipt = factoryctl.load_json_like(ROOT / "examples" / "minimal-hermes-project" / "expected-receipt-five.json")
    missing_plan = factoryctl.build_transition_plan(
        solana_card,
        solana_card_path,
        from_status="ready",
        to_status="done",
        receipt=blocked_receipt,
        worker_results_dir=out_dir / "missing-worker-results",
    )
    scenarios.append(
        scenario_pass(
            "done-blocks-missing-worker-results",
            expected={"transition_action": "block_transition", "min_blocked_reasons": 1},
            observed={
                "transition_action": missing_plan["transition_action"],
                "blocked_reasons": missing_plan["blocked_reasons"],
                "required_workers": missing_plan["gate_report"]["required_workers"],
                "blocked_workers": [],
            },
        )
    )

    synthetic_validation_card = json.loads(json.dumps(solana_card))
    synthetic_validation_card["source_refs"] = [
        *synthetic_validation_card.get("source_refs", []),
        "synthetic validation fixture",
    ]
    full_results = write_required_results(factoryctl, synthetic_validation_card, "solana-quasar-r3", out_dir)
    pass_plan = factoryctl.build_transition_plan(
        synthetic_validation_card,
        solana_card_path,
        from_status="ready",
        to_status="done",
        receipt=synthetic_done_receipt(factoryctl, synthetic_validation_card),
        worker_results_dir=full_results,
    )
    scenarios.append(
        scenario_pass(
            "done-allows-complete-worker-results",
            expected={"transition_action": "allow_done"},
            observed={
                "transition_action": pass_plan["transition_action"],
                "blocked_reasons": pass_plan["blocked_reasons"],
                "required_workers": pass_plan["gate_report"]["required_workers"],
                "blocked_workers": [],
            },
        )
    )

    passed = sum(1 for item in scenarios if item["passed"])
    return {
        "$schema": BATTERY_SCHEMA,
        "result_type": "factory_validation_battery",
        "scenario_count": len(scenarios),
        "passed_count": passed,
        "failed_count": len(scenarios) - passed,
        "scenarios": scenarios,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Overkill Factory validation battery.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / ".tmp" / "factory-runs" / "battery")
    parser.add_argument("--out", type=Path, default=ROOT / ".tmp" / "factory-runs" / "battery" / "factory-battery-results.json")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        scratch = Path(tmp)
        result = run_battery(scratch)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out, result)
    summary = args.out_dir / "factory-battery-summary.md"
    summary.write_text(
        "# Factory validation battery\n\n"
        f"- Scenarios: `{result['scenario_count']}`\n"
        f"- Passed: `{result['passed_count']}`\n"
        f"- Failed: `{result['failed_count']}`\n\n"
        "This battery spans Product Face, Solana/Quasar, Solana bank R4 routing, invalid-card rejection "
        "and done-transition reconciliation using public examples only.\n",
        encoding="utf-8",
    )
    print(json.dumps({"out": public_path_ref(args.out), "failed_count": result["failed_count"]}, indent=2))
    return 0 if result["failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
