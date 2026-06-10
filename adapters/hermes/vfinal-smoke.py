#!/usr/bin/env python3
"""Disposable vFinal smoke for the Hermes transition hook.

This is not live Hermes validation. It proves that the public adapter path can
route and block vFinal cards through the same transition-hook surface that
Hermes calls.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = ROOT / "adapters" / "hermes" / "transition_hook.py"
BRIDGE_PATH = ROOT / "adapters" / "hermes" / "kanban_event_bridge.py"
READY_CARD = ROOT / "validation" / "cards" / "vfinal-r3-ready.md"
BLOCKED_CARD = ROOT / "validation" / "cards" / "vfinal-r3-missing-security-access.md"
DEFAULT_OUT = ROOT / "validation" / "hermes-smoke" / "vfinal-transition-smoke.json"

REQUIRED_VFINAL_WORKERS = {
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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_transition_hook() -> Any:
    spec = importlib.util.spec_from_file_location("overkill_transition_hook", HOOK_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load transition hook from {HOOK_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["overkill_transition_hook"] = module
    spec.loader.exec_module(module)
    return module


def load_kanban_bridge() -> Any:
    spec = importlib.util.spec_from_file_location("overkill_kanban_bridge", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Kanban bridge from {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["overkill_kanban_bridge"] = module
    spec.loader.exec_module(module)
    return module


def repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def run_smoke() -> dict[str, Any]:
    hook = load_transition_hook()
    bridge = load_kanban_bridge()
    with tempfile.TemporaryDirectory(prefix="overkill-vfinal-hermes-smoke-") as tmp:
        tmp_path = Path(tmp)
        ready = hook.build_hook_result(
            card_path=READY_CARD,
            from_status="draft",
            to_status="ready",
            receipt_path=None,
            worker_results_dir=None,
            ledger_path=tmp_path / "ready-worker-ledger.json",
        )
        blocked = hook.build_hook_result(
            card_path=BLOCKED_CARD,
            from_status="draft",
            to_status="ready",
            receipt_path=None,
            worker_results_dir=None,
            ledger_path=tmp_path / "blocked-worker-ledger.json",
        )
        bridge_ready = bridge.build_from_task_payload(
            {
                "id": "redacted",
                "title": "OF-VFINAL-BRIDGE-SMOKE",
                "status": "blocked",
                "assignee": "factory-orchestrator",
                "body": READY_CARD.read_text(encoding="utf-8"),
            },
            from_status="blocked",
            to_status="ready",
            ledger_path=tmp_path / "bridge-worker-ledger.json",
        )

    ready_workers = {task["worker_id"] for task in ready["plan"]["worker_tasks"]}
    missing_ready_workers = sorted(REQUIRED_VFINAL_WORKERS - ready_workers)
    blocked_reasons = blocked.get("blocked_reasons", [])
    expected_block_fragments = [
        "security_architecture_plan required",
        "access_capability required",
        "autonomy_readiness_packet required",
    ]
    missing_block_reasons = [
        fragment for fragment in expected_block_fragments if not any(fragment in reason for reason in blocked_reasons)
    ]
    passed = (
        ready["transition_action"] == "allow_and_create_worker_tasks"
        and not ready.get("blocked_reasons")
        and not missing_ready_workers
        and blocked["transition_action"] == "block_transition"
        and not missing_block_reasons
        and bridge_ready["transition_action"] == "allow_and_create_worker_tasks"
        and bridge_ready["bridge"]["worker_spawned"] is False
    )
    return {
        "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": "remote_proof_result",
        "created_at": utc_now(),
        "worker": {
            "id": "remote-proof-runner",
            "name": "Remote Proof Runner",
            "factory_phase": "F13-F16",
        },
        "card_ref": {
            "card_id": "VFINAL-HERMES-ADAPTER-SMOKE",
            "slice_id": "VFINAL_ADAPTER_SMOKE",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "adapter", "vfinal"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "PASS" if passed else "FAIL",
        "blocking_findings": not passed,
        "findings_summary": (
            "vFinal transition hook smoke passed."
            if passed
            else "vFinal transition hook smoke failed."
        ),
        "tool_or_profile": "adapters/hermes/vfinal-smoke.py",
        "executed_by": "remote-proof-runner",
        "ready_transition_action": ready["transition_action"],
        "blocked_transition_action": blocked["transition_action"],
        "bridge_transition_action": bridge_ready["transition_action"],
        "bridge_worker_spawned": bridge_ready["bridge"]["worker_spawned"],
        "ready_workers_checked": sorted(REQUIRED_VFINAL_WORKERS),
        "missing_ready_workers": missing_ready_workers,
        "blocked_reasons": blocked_reasons,
        "missing_block_reasons": missing_block_reasons,
        "evidence_refs": [
            repo_ref(READY_CARD),
            repo_ref(BLOCKED_CARD),
            "adapters/hermes/kanban_event_bridge.py",
            "validation/hermes-smoke/vfinal-transition-smoke.json",
        ],
        "next_action": "Run the same transition path against a disposable real Hermes runtime before a product pilot.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run disposable vFinal Hermes adapter smoke.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    receipt = run_smoke()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": receipt["result"], "out": repo_ref(args.out)}, indent=2))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
