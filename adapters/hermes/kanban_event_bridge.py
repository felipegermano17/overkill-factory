#!/usr/bin/env python3
"""Bridge Hermes Kanban task JSON into the Overkill transition hook.

This is the adapter edge between a real Hermes task/event payload and the
repository-local transition hook. It does not spawn workers and does not update
Hermes by itself.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = ROOT / "adapters" / "hermes" / "transition_hook.py"
BRIDGE_TYPE = "overkill_factory_hermes_kanban_event_bridge"


def load_transition_hook() -> Any:
    spec = importlib.util.spec_from_file_location("overkill_transition_hook", HOOK_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load transition hook from {HOOK_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["overkill_transition_hook"] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def extract_task(payload: dict[str, Any]) -> dict[str, Any]:
    task = payload.get("task")
    if isinstance(task, dict):
        return task
    if isinstance(payload.get("id"), str) and "body" in payload:
        return payload
    raise ValueError("Hermes payload must be a task object or contain a task object")


def extract_card_body(task: dict[str, Any]) -> str:
    body = task.get("body")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("Hermes task body must contain a JSON factory card")
    return body.strip()


def safe_label(raw: str | None) -> str:
    label = (raw or "hermes-kanban-card").strip().lower()
    label = re.sub(r"[^a-z0-9._-]+", "-", label).strip("-._")
    if not label:
        label = "hermes-kanban-card"
    if not label.endswith(".json"):
        label = f"{label}.json"
    return label[:80]


def build_from_task_payload(
    payload: dict[str, Any],
    *,
    from_status: str,
    to_status: str,
    ledger_path: Path,
    receipt_path: Path | None = None,
    worker_results_dir: Path | None = None,
    source_label: str | None = None,
    include_task_id: bool = False,
) -> dict[str, Any]:
    task = extract_task(payload)
    card_body = extract_card_body(task)
    hook = load_transition_hook()

    with tempfile.TemporaryDirectory(prefix="overkill-hermes-kanban-bridge-") as tmp:
        card_path = Path(tmp) / safe_label(source_label)
        card_path.write_text(card_body + "\n", encoding="utf-8")
        result = hook.build_hook_result(
            card_path=card_path,
            from_status=from_status,
            to_status=to_status,
            receipt_path=receipt_path,
            worker_results_dir=worker_results_dir,
            ledger_path=ledger_path,
        )

    task_id = str(task.get("id") or "").strip()
    result["bridge"] = {
        "bridge_type": BRIDGE_TYPE,
        "source": "hermes_kanban_task_json",
        "task_id": task_id if include_task_id and task_id else "redacted",
        "task_title": str(task.get("title") or ""),
        "task_status": str(task.get("status") or ""),
        "from_status": from_status,
        "to_status": to_status,
        "worker_spawned": False,
    }
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bridge Hermes task JSON into the Overkill transition hook.")
    parser.add_argument("--task-json", type=Path, required=True)
    parser.add_argument("--from-status", required=True)
    parser.add_argument("--to-status", required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--worker-results-dir", type=Path)
    parser.add_argument("--source-label")
    parser.add_argument("--include-task-id", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--enforce", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_from_task_payload(
        load_json(args.task_json),
        from_status=args.from_status,
        to_status=args.to_status,
        ledger_path=args.ledger,
        receipt_path=args.receipt,
        worker_results_dir=args.worker_results_dir,
        source_label=args.source_label,
        include_task_id=args.include_task_id,
    )
    if args.out:
        write_json(args.out, result)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    if args.enforce and result["transition_action"] == "block_transition":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
