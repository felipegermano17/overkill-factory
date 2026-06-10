#!/usr/bin/env python3
"""Prove dispatcher -> worker completion -> parent ingestion wiring.

This smoke runs only against a disposable installed Hermes checkout/home. It
creates a public-safe vFinal card, materializes worker subtasks as `ready`, lets
the Hermes dispatcher claim one worker subtask, and completes that subtask via a
synthetic spawn function that writes structured Overkill worker-result metadata.

It does not call a real model and does not prove specialist output quality.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
READY_CARD = ROOT / "validation" / "cards" / "vfinal-r3-ready.md"
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "worker-dispatch-completion-smoke.json"
EXPECTED_WORKER_COUNT = 23


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def _assert_disposable_home(path: Path, *, allow_non_disposable: bool) -> None:
    if allow_non_disposable:
        return
    lowered = str(path.resolve()).lower()
    if "\\.tmp\\" in lowered or "/.tmp/" in lowered or lowered.endswith("\\.tmp") or lowered.endswith("/.tmp"):
        return
    raise SystemExit(
        "--hermes-home must point to a disposable .tmp runtime, or pass "
        "--allow-non-disposable after an explicit operator decision."
    )


def _load_kanban_db(hermes_checkout: Path, hermes_home: Path, board: str) -> Any:
    os.environ["HERMES_HOME"] = str(hermes_home)
    os.environ["HOME"] = str(hermes_home)
    os.environ["HERMES_KANBAN_BOARD"] = board
    os.environ["OVERKILL_FACTORY_KANBAN_GATE"] = "1"
    os.environ["OVERKILL_FACTORY_ADAPTER_ROOT"] = str(ROOT)
    os.environ["OVERKILL_FACTORY_CREATE_WORKER_TASKS"] = "1"
    os.environ["OVERKILL_FACTORY_WORKER_TASK_STATUS"] = "ready"
    os.environ["OVERKILL_FACTORY_RUNTIME_DIR"] = str(hermes_home / "overkill-factory")
    sys.path.insert(0, str(hermes_checkout))
    from hermes_cli import kanban_db  # type: ignore

    return kanban_db


def _ensure_profile_dirs(hermes_home: Path, workers: set[str]) -> int:
    count = 0
    for worker in sorted(workers):
        if not worker:
            continue
        profile_dir = hermes_home if worker == "default" else hermes_home / "profiles" / worker
        if not profile_dir.is_dir():
            profile_dir.mkdir(parents=True, exist_ok=True)
            count += 1
    return count


def _result_files(hermes_home: Path, parent_task_id: str) -> list[str]:
    result_dir = hermes_home / "overkill-factory" / parent_task_id / "worker-results"
    if not result_dir.is_dir():
        return []
    return sorted(path.name for path in result_dir.glob("*.json"))


def run_smoke(
    *,
    hermes_checkout: Path,
    hermes_home: Path,
    allow_non_disposable: bool = False,
) -> dict[str, Any]:
    _assert_disposable_home(hermes_home, allow_non_disposable=allow_non_disposable)
    if not (hermes_checkout / "hermes_cli" / "kanban_db.py").is_file():
        raise SystemExit(f"missing Hermes kanban_db.py under {hermes_checkout}")
    if not READY_CARD.is_file():
        raise SystemExit(f"missing ready card fixture: {READY_CARD}")

    board = f"of-dispatch-complete-{int(time.time())}"
    kb = _load_kanban_db(hermes_checkout, hermes_home, board)
    kb.create_board(
        board,
        name="Overkill synthetic dispatch completion smoke",
        default_workdir=str(ROOT),
    )
    card_body = READY_CARD.read_text(encoding="utf-8")
    synthetic_completions: list[dict[str, Any]] = []

    with kb.connect_closing(board=board) as conn:
        parent_task_id = kb.create_task(
            conn,
            title="VFINAL synthetic dispatch completion smoke",
            body=card_body,
            assignee="factory-orchestrator",
            created_by="worker-dispatch-completion-smoke",
            workspace_kind="dir",
            workspace_path=str(ROOT),
            max_retries=1,
            board=board,
        )
        children = conn.execute(
            "SELECT id, assignee, status, body FROM tasks WHERE id != ? ORDER BY created_at, id",
            (parent_task_id,),
        ).fetchall()
        worker_ids = {str(row["assignee"] or "") for row in children}
        ensured_profile_count = _ensure_profile_dirs(hermes_home, worker_ids)

        def synthetic_spawn(task: Any, workspace: str, board: str | None = None) -> None:
            subtask = json.loads(task.body)
            record_type = str(subtask.get("expected_receipt_field") or "worker-result")
            worker_id = str(subtask.get("worker_id") or task.assignee or "worker")
            metadata = {
                "overkill_worker_result": {
                    "record_type": record_type,
                    "result": "PASS",
                    "blocking_findings": False,
                    "findings_summary": f"Synthetic dispatcher completion PASS for {worker_id}.",
                    "tool_or_profile": f"synthetic-dispatcher:{worker_id}",
                    "executed_by": "worker-dispatch-completion-smoke",
                    "evidence_refs": [
                        "validation/hermes-installed-runtime-smoke/worker-dispatch-completion-smoke.json"
                    ],
                    "next_action": (
                        "Use only as dispatcher completion wiring proof; "
                        "not real model proof."
                    ),
                }
            }
            complete_ok = kb.complete_task(
                conn,
                task.id,
                result="PASS",
                summary=f"Synthetic dispatcher worker completed {worker_id}.",
                metadata=metadata,
            )
            synthetic_completions.append(
                {
                    "task_id": task.id,
                    "worker_id": worker_id,
                    "record_type": record_type,
                    "complete_ok": bool(complete_ok),
                    "workspace_ref": "disposable-worker-workspace",
                }
            )
            return None

        dispatch_result = kb.dispatch_once(
            conn,
            spawn_fn=synthetic_spawn,
            max_spawn=1,
            failure_limit=1,
            board=board,
        )
        parent_row = conn.execute(
            "SELECT status FROM tasks WHERE id = ?",
            (parent_task_id,),
        ).fetchone()
        spawned_task_id = synthetic_completions[0]["task_id"] if synthetic_completions else ""
        child_event_kinds = [
            row["kind"]
            for row in conn.execute(
                "SELECT kind FROM task_events WHERE task_id = ? ORDER BY id",
                (spawned_task_id,),
            ).fetchall()
        ]
        parent_event_kinds = [
            row["kind"]
            for row in conn.execute(
                "SELECT kind FROM task_events WHERE task_id = ? ORDER BY id",
                (parent_task_id,),
            ).fetchall()
        ]

    result_files = _result_files(hermes_home, parent_task_id)
    checks = {
        "worker_subtasks_created": "PASS" if len(children) == EXPECTED_WORKER_COUNT else "FAIL",
        "profile_dirs_available": "PASS" if len(worker_ids) == EXPECTED_WORKER_COUNT else "FAIL",
        "dispatcher_claimed_one_worker": "PASS" if len(dispatch_result.spawned) == 1 else "FAIL",
        "synthetic_worker_completed": "PASS"
        if synthetic_completions and synthetic_completions[0]["complete_ok"]
        else "FAIL",
        "worker_result_ingested": "PASS" if result_files else "FAIL",
        "child_events_written": "PASS"
        if {"claimed", "completed", "overkill_worker_result_ingested"}.issubset(set(child_event_kinds))
        else "FAIL",
        "parent_event_written": "PASS"
        if "overkill_worker_result_ingested" in parent_event_kinds
        else "FAIL",
        "parent_waits_for_remaining_workers": "PASS"
        if parent_row is not None and parent_row["status"] == "todo"
        else "FAIL",
    }
    passed = all(value == "PASS" for value in checks.values())
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
            "card_id": "VFINAL-HERMES-WORKER-DISPATCH-COMPLETION-SMOKE",
            "slice_id": "VFINAL_HERMES_WORKER_DISPATCH_COMPLETION",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "worker-routing", "worker-results"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "PASS" if passed else "FAIL",
        "blocking_findings": not passed,
        "findings_summary": (
            "Disposable installed Hermes smoke passed for dispatcher claim, synthetic worker completion and parent worker-result ingestion."
            if passed
            else "Disposable installed Hermes dispatcher completion smoke failed."
        ),
        "tool_or_profile": "Hermes disposable installed runtime; dispatcher spawn function synthetic",
        "executed_by": "remote-proof-runner",
        "runtime_scope": (
            "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; "
            "no production board, secrets, deploy, real model call or real Hermes runtime mutation."
        ),
        "checks": checks,
        "disposable_task_evidence": {
            "board_slug": board,
            "parent_task_ref": "redacted-disposable-parent",
            "worker_subtask_count": len(children),
            "profile_dirs_created_by_smoke": ensured_profile_count,
            "dispatch_spawned_count": len(dispatch_result.spawned),
            "synthetic_completions": synthetic_completions,
            "parent_final_status": parent_row["status"] if parent_row is not None else None,
            "child_event_kinds": child_event_kinds,
            "parent_event_kinds": parent_event_kinds,
            "worker_result_files": result_files,
        },
        "important_limitations": [
            "This proves dispatcher claim, synthetic worker completion and automatic worker-result ingestion wiring only.",
            "The spawn function was synthetic; no real Hermes child process, model call, tool auth or specialist reasoning happened.",
            "Profile directories may be created only so Hermes marks the workers spawnable; this is not profile/model quality proof.",
            "This does not authorize updating a real Hermes runtime.",
        ],
        "evidence_refs": [
            repo_ref(READY_CARD),
            "validation/hermes-installed-runtime-smoke/worker-dispatch-completion-smoke.json",
            "validation/hermes-installed-runtime-smoke/worker-profile-readiness-local-stub-smoke.json",
        ],
        "next_action": (
            "Run a bounded real worker with a provisioned profile/model/tool path, "
            "then require autonomous kanban_complete/kanban_block evidence."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-checkout", type=Path, required=True)
    parser.add_argument("--hermes-home", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--allow-non-disposable", action="store_true")
    args = parser.parse_args(argv)

    receipt = run_smoke(
        hermes_checkout=args.hermes_checkout.expanduser().resolve(),
        hermes_home=args.hermes_home.expanduser().resolve(),
        allow_non_disposable=args.allow_non_disposable,
    )
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": receipt["result"], "out": repo_ref(out)}, indent=2))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
