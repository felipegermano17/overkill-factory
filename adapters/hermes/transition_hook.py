#!/usr/bin/env python3
"""Hermes transition hook for Overkill Factory cards.

Hermes can call this script before a Kanban transition. It produces the same
transition plan as `factoryctl.py`, persists idempotent worker subtasks in a
small JSON ledger, and exits non-zero by default when the transition must be
blocked.

This adapter intentionally does not execute specialist workers by itself. It
creates durable worker tasks and reconciles worker evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FACTORYCTL_PATH = ROOT / "scripts" / "factoryctl.py"
HOOK_SCHEMA = "https://overkill-factory.dev/schemas/hermes-transition-hook.schema.json"
ACTION_CREATE_WORKERS = "allow_and_create_worker_tasks"
ACTION_BLOCK_TRANSITION = "block_transition"
WORKER_LEDGER_HINT = "worker-ledger"


def load_factoryctl() -> Any:
    spec = importlib.util.spec_from_file_location("overkill_factoryctl", FACTORYCTL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load factoryctl from {FACTORYCTL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["overkill_factoryctl"] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def public_path_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except (OSError, ValueError):
        return f"external:{path.name or 'artifact'}"


def task_id(card_id: str, worker_id: str) -> str:
    digest = hashlib.sha256(f"{card_id}:{worker_id}".encode("utf-8")).hexdigest()[:16]
    return f"ofw_{digest}"


def is_blocking_action(action: str) -> bool:
    return action.startswith("block")


def load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "$schema": "https://overkill-factory.dev/schemas/hermes-worker-ledger.schema.json",
            "ledger_type": "overkill_factory_hermes_worker_ledger",
            "tasks": {},
        }
    data = load_json(path)
    data.setdefault("$schema", "https://overkill-factory.dev/schemas/hermes-worker-ledger.schema.json")
    data.setdefault("ledger_type", "overkill_factory_hermes_worker_ledger")
    if not isinstance(data.get("tasks"), dict):
        data["tasks"] = {}
    return data


def persist_worker_tasks(plan: dict[str, Any], ledger_path: Path) -> dict[str, Any]:
    ledger = load_ledger(ledger_path)
    tasks: dict[str, Any] = ledger["tasks"]
    created: list[str] = []
    unchanged: list[str] = []
    updated: list[str] = []
    card_id = str(plan.get("event", {}).get("card_id") or "factory-card")

    for task in plan.get("worker_tasks", []):
        worker_id = str(task.get("worker_id") or "").strip()
        if not worker_id or task.get("status") == "not_required_by_current_card":
            continue
        ident = task_id(card_id, worker_id)
        payload = {
            "task_id": ident,
            "card_id": card_id,
            "worker_id": worker_id,
            "title": task.get("title"),
            "queue_class": task.get("queue_class"),
            "required_before": task.get("required_before"),
            "expected_receipt_field": task.get("expected_receipt_field"),
            "status": task.get("status"),
            "packet": task.get("packet"),
        }
        previous = tasks.get(ident)
        if previous is None:
            tasks[ident] = payload
            created.append(ident)
        elif previous == payload:
            unchanged.append(ident)
        else:
            tasks[ident] = payload
            updated.append(ident)

    ledger["last_transition"] = plan.get("event", {})
    ledger["last_action"] = plan.get("transition_action")
    write_json(ledger_path, ledger)
    return {
        "ledger_path": public_path_ref(ledger_path),
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "task_count": len(tasks),
    }


def build_hook_result(
    *,
    card_path: Path,
    from_status: str,
    to_status: str,
    receipt_path: Path | None,
    worker_results_dir: Path | None,
    ledger_path: Path,
) -> dict[str, Any]:
    factoryctl = load_factoryctl()
    card = factoryctl.load_json_like(card_path)
    receipt = factoryctl.load_json_like(receipt_path) if receipt_path else None
    plan = factoryctl.build_transition_plan(
        card,
        card_path,
        from_status=from_status,
        to_status=to_status,
        receipt=receipt,
        worker_results_dir=worker_results_dir,
    )
    ledger_result = persist_worker_tasks(plan, ledger_path)
    return {
        "$schema": HOOK_SCHEMA,
        "hook_type": "overkill_factory_hermes_transition_hook",
        "transition_action": plan["transition_action"],
        "blocked_reasons": plan["blocked_reasons"],
        "completion_reconciliation": plan.get("completion_reconciliation"),
        "plan": plan,
        "ledger": ledger_result,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Overkill Factory transition hook for Hermes.")
    parser.add_argument("--card", type=Path, required=True)
    parser.add_argument("--from-status", required=True)
    parser.add_argument("--to-status", required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--worker-results-dir", type=Path)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--enforce", action="store_true", help="Deprecated; blocked transitions are fail-closed by default.")
    parser.add_argument("--report-only", action="store_true", help="Write the hook result without failing blocked transitions.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_hook_result(
        card_path=args.card,
        from_status=args.from_status,
        to_status=args.to_status,
        receipt_path=args.receipt,
        worker_results_dir=args.worker_results_dir,
        ledger_path=args.ledger,
    )
    if args.out:
        write_json(args.out, result)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    if not args.report_only and is_blocking_action(result["transition_action"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
