#!/usr/bin/env python3
"""Run a multi-context Overkill Factory validation battery."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FACTORYCTL = ROOT / "scripts" / "factoryctl.py"
BATTERY_SCHEMA = "https://overkill-factory.dev/schemas/factory-battery-result.schema.json"


def load_factoryctl() -> Any:
    spec = importlib.util.spec_from_file_location("battery_factoryctl", FACTORYCTL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load factoryctl from {FACTORYCTL}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["battery_factoryctl"] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


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
    return factoryctl.build_worker_result(
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


def write_required_results(factoryctl: Any, card: dict[str, Any], card_name: str, out_dir: Path) -> Path:
    results_dir = out_dir / card_name / "worker-results"
    evidence_dir = out_dir / card_name / "evidence"
    results_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for worker_id in factoryctl.required_worker_ids(card):
        evidence_path = evidence_dir / f"{worker_id}.md"
        evidence_ref = factoryctl.source_card_ref(evidence_path)
        evidence_path.write_text(
            "Synthetic battery evidence only; not a real product approval or audit.\n",
            encoding="utf-8",
        )
        record = worker_result(factoryctl, worker_id, card, evidence_ref)
        output_field = "human_gate_record" if worker_id == "human-gate-clerk" else record["record_type"]
        write_json(results_dir / f"{output_field}.json", record)
    return results_dir


def run_battery(out_dir: Path) -> dict[str, Any]:
    factoryctl = load_factoryctl()
    scenarios: list[dict[str, Any]] = []
    ready_specs = [
        (
            "product-face-r2",
            ROOT / "validation" / "cards" / "product-face-saas-r2.md",
            {
                "gate_status": "ready_for_worker_execution",
                "required_workers": ["product-face", "independent-reviewer", "qa-verification-worker"],
            },
        ),
        (
            "solana-quasar-r3",
            ROOT / "validation" / "cards" / "solana-quasar-r3.md",
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
        (
            "cloud-release-r4",
            ROOT / "validation" / "cards" / "cloud-release-r4.md",
            {
                "gate_status": "ready_for_worker_execution",
                "required_workers": [
                    "codex-security",
                    "cloud-infra-security-specialist",
                    "release-ops-worker",
                    "detection-monitoring-worker",
                    "human-gate-clerk",
                ],
            },
        ),
        (
            "public-repo-release-r2",
            ROOT / "validation" / "cards" / "public-repo-release-r2.md",
            {
                "gate_status": "blocked",
                "required_workers": ["public-safety-gate", "supply-chain-gate"],
                "blocked_workers": ["codex-security", "release-ops-worker"],
            },
        ),
        (
            "agentic-browser-memory-r3",
            ROOT / "validation" / "cards" / "agentic-browser-memory-r3.md",
            {
                "gate_status": "ready_for_worker_execution",
                "required_workers": [
                    "agentic-ai-security-specialist",
                    "security-orchestrator",
                    "memory-steward",
                    "handoff-packer",
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

    receipt = factoryctl.load_json_like(ROOT / "pilots" / "quasar-vault-guard-test" / "evidence" / "receipt-five-first-slice.json")
    solana_card = factoryctl.load_json_like(ROOT / "validation" / "cards" / "solana-quasar-r3.md")
    missing_plan = factoryctl.build_transition_plan(
        solana_card,
        ROOT / "validation" / "cards" / "solana-quasar-r3.md",
        from_status="ready",
        to_status="done",
        receipt=receipt,
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

    full_results = write_required_results(factoryctl, solana_card, "solana-quasar-r3", out_dir)
    pass_plan = factoryctl.build_transition_plan(
        solana_card,
        ROOT / "validation" / "cards" / "solana-quasar-r3.md",
        from_status="ready",
        to_status="done",
        receipt=receipt,
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
    parser.add_argument("--out-dir", type=Path, default=ROOT / "validation" / "battery")
    parser.add_argument("--out", type=Path, default=ROOT / "validation" / "battery" / "factory-battery-results.json")
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
        "This battery spans Product Face, Solana/Quasar, cloud release, public repository release, "
        "agentic/browser/memory work, invalid-card rejection and done-transition reconciliation.\n",
        encoding="utf-8",
    )
    print(json.dumps({"out": str(args.out), "failed_count": result["failed_count"]}, indent=2))
    return 0 if result["failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
