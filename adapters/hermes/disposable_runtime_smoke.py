#!/usr/bin/env python3
"""Disposable-runtime smoke for the Hermes vFinal adapter.

This is still repository-local validation, not a live Hermes installation. It
does prove the full adapter contract that Hermes must execute: before-ready
worker routing, idempotent retries, before-ready blocking, before-done evidence
blocking, before-done evidence reconciliation, and Kanban task JSON bridging.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = ROOT / "adapters" / "hermes" / "transition_hook.py"
BRIDGE_PATH = ROOT / "adapters" / "hermes" / "kanban_event_bridge.py"
FACTORYCTL_PATH = ROOT / "scripts" / "factoryctl.py"
READY_CARD = ROOT / "validation" / "cards" / "vfinal-r3-ready.md"
MISSING_INPUTS_CARD = ROOT / "validation" / "cards" / "vfinal-r3-missing-security-access.md"
CONTROL_TOWER_CARD = ROOT / "validation" / "cards" / "vfinal-control-tower-missing-interface.md"
DEFAULT_OUT = ROOT / "validation" / "hermes-disposable-runtime" / "disposable-runtime-smoke.json"

EXPECTED_READY_WORKERS = {
    "agentic-method-router",
    "software-development-planner",
    "data-metrics-worker",
    "agent-eval-worker",
    "dependency-integration-worker",
    "access-capability-worker",
    "security-architect-worker",
    "budget-cost-worker",
    "factory-maturity-auditor",
}

EXPECTED_CONTROL_TOWER_WORKERS = {
    "factory-concierge",
    "discord-control-tower-bridge",
    "control-tower-projection-worker",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_module(module_name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_transition_hook() -> Any:
    return load_module("overkill_transition_hook_disposable", HOOK_PATH)


def load_kanban_bridge() -> Any:
    return load_module("overkill_kanban_bridge_disposable", BRIDGE_PATH)


def load_factoryctl() -> Any:
    return load_module("overkill_factoryctl_disposable", FACTORYCTL_PATH)


def repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def public_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: public_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [public_safe(item) for item in value]
    if isinstance(value, str):
        candidate = Path(value)
        if candidate.is_absolute():
            try:
                return candidate.resolve().relative_to(ROOT).as_posix()
            except ValueError:
                return f"external:{candidate.name}"
    return value


def reset_generated_dir(path: Path, root: Path) -> None:
    resolved = path.resolve()
    resolved.relative_to(root.resolve())
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def reset_ledger(path: Path) -> None:
    write_json(
        path,
        {
            "$schema": "https://overkill-factory.dev/schemas/hermes-worker-ledger.schema.json",
            "ledger_type": "overkill_factory_hermes_worker_ledger",
            "tasks": {},
        },
    )


def hermes_task_payload(card_path: Path, *, title: str, status: str) -> dict[str, Any]:
    return {
        "id": "redacted",
        "title": title,
        "status": status,
        "assignee": "factory-orchestrator",
        "body": card_path.read_text(encoding="utf-8"),
    }


def write_synthetic_receipt(path: Path) -> dict[str, Any]:
    receipt = {
        "$schema": "https://overkill-factory.dev/schemas/receipt-five.schema.json",
        "receipt_five": {
            "changed": "Synthetic disposable adapter run completed without product or runtime mutation.",
            "artifact_paths": [
                "validation/hermes-disposable-runtime/disposable-runtime-smoke.json",
                "validation/hermes-disposable-runtime/worker-results",
            ],
            "verification_commands": ["python adapters/hermes/disposable_runtime_smoke.py"],
            "verification_result": "PASS",
            "reviewer_required": True,
            "reviewer_result": "Synthetic independent-review worker result attached.",
            "next_action": "Wire this same hook path into a disposable live Hermes runtime.",
        },
        "kanban_transition_event": {
            "from_status": "ready",
            "to_status": "done",
            "actor": "disposable-runtime-smoke",
            "worker": "factory-orchestrator",
            "receipt_refs": ["validation/hermes-disposable-runtime/synthetic-receipt-five.json"],
            "artifact_refs": ["validation/hermes-disposable-runtime/worker-results"],
        },
        "hermes_legacy_completion_required": False,
        "evidence_paths": ["validation/hermes-disposable-runtime/disposable-runtime-smoke.json"],
        "verification": {
            "passed": True,
            "commands": ["python adapters/hermes/disposable_runtime_smoke.py"],
        },
        "sandbox": {
            "passed": True,
            "invariants": ["No live Hermes state changed.", "No Discord API call executed.", "No production deployment ran."],
        },
        "rollback": {
            "verified": True,
            "evidence": "No rollback required because the smoke is local and synthetic.",
        },
    }
    write_json(path, receipt)
    return receipt


def blocking_before_done_workers(factoryctl: Any, card: dict[str, Any]) -> list[str]:
    workers: list[str] = []
    for worker_id in factoryctl.required_worker_ids(card):
        if factoryctl.worker_queue_class(worker_id, card) == "blocking-before-done":
            workers.append(worker_id)
    return workers


def write_worker_results(factoryctl: Any, card: dict[str, Any], results_dir: Path) -> list[str]:
    worker_ids = blocking_before_done_workers(factoryctl, card)
    for worker_id in worker_ids:
        evidence_ref = f"validation/hermes-disposable-runtime/evidence/{worker_id}.md"
        if worker_id == "human-gate-clerk":
            record = factoryctl.build_human_gate_record(
                card,
                gate_type=None,
                decision="approved",
                human_actor="synthetic-owner",
                approved_scope=card.get("scope_in", ["synthetic adapter proof"]),
                forbidden_scope=card.get("forbidden_actions", []),
                required_changes=[],
                risk_owner=None,
                security_owner=None,
                rollback_owner=None,
                evidence_refs=[evidence_ref],
                notes="Synthetic owner approval used only to prove before-done reconciliation.",
            )
        else:
            record = factoryctl.build_worker_result(
                worker_id,
                card,
                result="PASS",
                tool_or_profile=f"synthetic-{worker_id}",
                executed_by="disposable-runtime-smoke",
                evidence_refs=[evidence_ref],
                blocking_findings=False,
                findings_summary=f"Synthetic PASS for {worker_id} before-done reconciliation.",
                next_action="No action; this record is local adapter proof only.",
            )
        write_json(results_dir / f"{worker_id}-result.json", record)
    return worker_ids


def write_evidence_files(worker_ids: list[str], evidence_dir: Path) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for worker_id in worker_ids:
        path = evidence_dir / f"{worker_id}.md"
        path.write_text(
            (
                f"# Synthetic Evidence: {worker_id}\n\n"
                "This public-safe file exists only so the disposable adapter "
                "smoke can point to a concrete evidence artifact.\n"
            ),
            encoding="utf-8",
        )


def summarize_blocking_workers(result: dict[str, Any]) -> list[str]:
    gate = result.get("plan", {}).get("gate_report", {})
    blocked = gate.get("blocked_workers", [])
    return sorted(worker for worker in blocked if isinstance(worker, str))


def run_smoke(out_dir: Path | None = None) -> dict[str, Any]:
    output_dir = out_dir or DEFAULT_OUT.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    reset_generated_dir(output_dir / "worker-results", output_dir)
    reset_generated_dir(output_dir / "evidence", output_dir)

    hook = load_transition_hook()
    bridge = load_kanban_bridge()
    factoryctl = load_factoryctl()
    ready_card = factoryctl.load_json_like(READY_CARD)
    receipt_path = output_dir / "synthetic-receipt-five.json"
    worker_results_dir = output_dir / "worker-results"
    evidence_dir = output_dir / "evidence"
    ledger_path = output_dir / "worker-ledger.json"
    bridge_ledger_path = output_dir / "bridge-worker-ledger.json"

    reset_ledger(ledger_path)
    reset_ledger(bridge_ledger_path)
    write_synthetic_receipt(receipt_path)
    before_done_workers = write_worker_results(factoryctl, ready_card, worker_results_dir)
    write_evidence_files(before_done_workers, evidence_dir)

    ready_first = hook.build_hook_result(
        card_path=READY_CARD,
        from_status="draft",
        to_status="ready",
        receipt_path=None,
        worker_results_dir=None,
        ledger_path=ledger_path,
    )
    ready_retry = hook.build_hook_result(
        card_path=READY_CARD,
        from_status="draft",
        to_status="ready",
        receipt_path=None,
        worker_results_dir=None,
        ledger_path=ledger_path,
    )
    missing_inputs = hook.build_hook_result(
        card_path=MISSING_INPUTS_CARD,
        from_status="draft",
        to_status="ready",
        receipt_path=None,
        worker_results_dir=None,
        ledger_path=output_dir / "missing-inputs-worker-ledger.json",
    )
    control_tower_missing = hook.build_hook_result(
        card_path=CONTROL_TOWER_CARD,
        from_status="draft",
        to_status="ready",
        receipt_path=None,
        worker_results_dir=None,
        ledger_path=output_dir / "control-tower-worker-ledger.json",
    )
    done_missing = hook.build_hook_result(
        card_path=READY_CARD,
        from_status="ready",
        to_status="done",
        receipt_path=receipt_path,
        worker_results_dir=None,
        ledger_path=output_dir / "done-missing-worker-ledger.json",
    )
    done_satisfied = hook.build_hook_result(
        card_path=READY_CARD,
        from_status="ready",
        to_status="done",
        receipt_path=receipt_path,
        worker_results_dir=worker_results_dir,
        ledger_path=output_dir / "done-satisfied-worker-ledger.json",
    )
    bridge_ready = bridge.build_from_task_payload(
        hermes_task_payload(READY_CARD, title="OF-DISPOSABLE-BRIDGE-READY", status="draft"),
        from_status="draft",
        to_status="ready",
        ledger_path=bridge_ledger_path,
    )
    bridge_done = bridge.build_from_task_payload(
        hermes_task_payload(READY_CARD, title="OF-DISPOSABLE-BRIDGE-DONE", status="ready"),
        from_status="ready",
        to_status="done",
        ledger_path=output_dir / "bridge-done-worker-ledger.json",
        receipt_path=receipt_path,
        worker_results_dir=worker_results_dir,
    )

    artifacts = {
        "before-ready-technical-hook-result.json": ready_first,
        "before-ready-technical-retry-hook-result.json": ready_retry,
        "before-ready-missing-inputs-hook-result.json": missing_inputs,
        "before-ready-control-tower-hook-result.json": control_tower_missing,
        "before-done-missing-results-hook-result.json": done_missing,
        "before-done-satisfied-hook-result.json": done_satisfied,
        "bridge-before-ready-hook-result.json": bridge_ready,
        "bridge-before-done-hook-result.json": bridge_done,
    }
    for name, artifact in artifacts.items():
        write_json(output_dir / name, public_safe(artifact))

    ready_workers = {task["worker_id"] for task in ready_first["plan"]["worker_tasks"]}
    control_tower_workers = {task["worker_id"] for task in control_tower_missing["plan"]["worker_tasks"]}
    control_tower_blocked = set(summarize_blocking_workers(control_tower_missing))
    missing_block_fragments = [
        "security_architecture_plan required",
        "access_capability required",
        "autonomy_readiness_packet required",
    ]
    missing_input_reasons = missing_inputs.get("blocked_reasons", [])

    failures: list[str] = []
    if ready_first["transition_action"] != "allow_and_create_worker_tasks":
        failures.append("ready transition did not allow worker task creation")
    if ready_first["ledger"]["created"] == []:
        failures.append("ready transition did not create worker ledger rows")
    if ready_retry["ledger"]["created"] != []:
        failures.append("ready retry created duplicate worker tasks")
    missing_ready_workers = sorted(EXPECTED_READY_WORKERS - ready_workers)
    if missing_ready_workers:
        failures.append("ready transition missed vFinal workers: " + ", ".join(missing_ready_workers))
    if missing_inputs["transition_action"] != "block_transition":
        failures.append("missing-input card did not block before ready")
    for fragment in missing_block_fragments:
        if not any(fragment in reason for reason in missing_input_reasons):
            failures.append(f"missing-input card did not report {fragment}")
    missing_control_tower_workers = sorted(EXPECTED_CONTROL_TOWER_WORKERS - control_tower_workers)
    if missing_control_tower_workers:
        failures.append("control tower card missed workers: " + ", ".join(missing_control_tower_workers))
    missing_control_tower_blocks = sorted(EXPECTED_CONTROL_TOWER_WORKERS - control_tower_blocked)
    if missing_control_tower_blocks:
        failures.append("control tower card did not block workers: " + ", ".join(missing_control_tower_blocks))
    if done_missing["transition_action"] != "block_transition":
        failures.append("done transition without worker results did not block")
    if not any("result is required before done" in reason for reason in done_missing.get("blocked_reasons", [])):
        failures.append("done transition without worker results did not explain missing results")
    if done_satisfied["transition_action"] != "allow_done":
        failures.append("done transition with valid worker results did not allow done")
    if bridge_ready["transition_action"] != "allow_and_create_worker_tasks":
        failures.append("Kanban bridge ready transition did not allow worker task creation")
    if bridge_ready["bridge"]["worker_spawned"] is not False:
        failures.append("Kanban bridge reported worker spawn")
    if bridge_done["transition_action"] != "allow_done":
        failures.append("Kanban bridge done transition did not allow done")
    if bridge_done["bridge"]["worker_spawned"] is not False:
        failures.append("Kanban bridge done reported worker spawn")

    passed = not failures
    summary = {
        "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": "remote_proof_result",
        "created_at": utc_now(),
        "worker": {
            "id": "remote-proof-runner",
            "name": "Remote Proof Runner",
            "factory_phase": "F13-F16",
        },
        "card_ref": {
            "card_id": "VFINAL-HERMES-DISPOSABLE-RUNTIME-SMOKE",
            "slice_id": "VFINAL_HERMES_DISPOSABLE_RUNTIME",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "control-tower"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "PASS" if passed else "FAIL",
        "blocking_findings": not passed,
        "findings_summary": (
            "Disposable adapter runtime smoke passed before-ready, before-done and bridge checks."
            if passed
            else "Disposable adapter runtime smoke failed: " + "; ".join(failures)
        ),
        "tool_or_profile": "adapters/hermes/disposable_runtime_smoke.py",
        "executed_by": "remote-proof-runner",
        "failures": failures,
        "ready_transition_action": ready_first["transition_action"],
        "ready_retry_created": ready_retry["ledger"]["created"],
        "before_done_workers_satisfied": before_done_workers,
        "done_missing_transition_action": done_missing["transition_action"],
        "done_satisfied_transition_action": done_satisfied["transition_action"],
        "bridge_ready_transition_action": bridge_ready["transition_action"],
        "bridge_done_transition_action": bridge_done["transition_action"],
        "control_tower_required_workers": sorted(control_tower_workers),
        "control_tower_blocked_workers": sorted(control_tower_blocked),
        "evidence_refs": [
            "validation/cards/vfinal-r3-ready.md",
            "validation/cards/vfinal-r3-missing-security-access.md",
            "validation/cards/vfinal-control-tower-missing-interface.md",
            "validation/hermes-disposable-runtime/before-ready-technical-hook-result.json",
            "validation/hermes-disposable-runtime/before-ready-technical-retry-hook-result.json",
            "validation/hermes-disposable-runtime/before-ready-missing-inputs-hook-result.json",
            "validation/hermes-disposable-runtime/before-ready-control-tower-hook-result.json",
            "validation/hermes-disposable-runtime/before-done-missing-results-hook-result.json",
            "validation/hermes-disposable-runtime/before-done-satisfied-hook-result.json",
            "validation/hermes-disposable-runtime/bridge-before-ready-hook-result.json",
            "validation/hermes-disposable-runtime/bridge-before-done-hook-result.json",
            "validation/hermes-disposable-runtime/synthetic-receipt-five.json",
            "validation/hermes-disposable-runtime/worker-results",
        ],
        "next_action": "Install this same hook path into a disposable live Hermes runtime and prove CLI/dashboard/API parity.",
    }
    write_json(output_dir / "disposable-runtime-smoke.json", summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run disposable Hermes vFinal adapter runtime smoke.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    receipt = run_smoke(args.out.parent)
    if args.out != args.out.parent / "disposable-runtime-smoke.json":
        write_json(args.out, receipt)
    print(json.dumps({"result": receipt["result"], "out": repo_ref(args.out)}, indent=2))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
