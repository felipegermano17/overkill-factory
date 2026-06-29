#!/usr/bin/env python3
"""Run a real Hermes Kanban smoke for V3 production activation.

This is intentionally separate from the deterministic Factory Perfect Run. It
mutates a disposable Hermes Kanban board and proves that the live runtime can
create, comment, block, unblock and complete a card with Receipt Five metadata.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess  # nosec B404 - deliberate CLI integration with local Hermes.
import sys
import time
from pathlib import Path
from typing import Any

DEFAULT_BOARD = "of-v3-production-activation"
DEFAULT_TITLE = "Factory Perfect Run live Hermes smoke"


def _run(argv: list[str], *, cwd: Path, allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False)  # nosec B603
    if proc.returncode != 0 and not allow_failure:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(argv)}\n{proc.stdout}\n{proc.stderr}")
    return proc


def _parse_json(text: str) -> dict[str, Any]:
    return json.loads(text[text.find("{") :])


def _task_status(show_payload: dict[str, Any]) -> str | None:
    task = show_payload.get("task")
    if isinstance(task, dict):
        return task.get("status")
    return show_payload.get("status")


def _event_kinds(show_payload: dict[str, Any]) -> set[str]:
    return {str(event.get("kind")) for event in show_payload.get("events", []) if isinstance(event, dict)}


def sanitize_show_payload(show_payload: dict[str, Any]) -> dict[str, Any]:
    task = dict(show_payload.get("task") or {})
    if "workspace_path" in task:
        task["workspace_path"] = "redacted:hermes-workspace"
    return {
        "task": task,
        "latest_summary": show_payload.get("latest_summary"),
        "event_kinds": sorted(_event_kinds(show_payload)),
        "comment_count": len(show_payload.get("comments") or []),
        "run_count": len(show_payload.get("runs") or []),
        "runs": [
            {
                "status": run.get("status"),
                "outcome": run.get("outcome"),
                "summary": run.get("summary"),
                "metadata": run.get("metadata"),
            }
            for run in (show_payload.get("runs") or [])
            if isinstance(run, dict)
        ],
    }


def validate_smoke(blocked_payload: dict[str, Any], done_payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    blocked_status = _task_status(blocked_payload)
    done_status = _task_status(done_payload)
    if blocked_status != "blocked":
        errors.append(f"expected blocked status, got {blocked_status!r}")
    if done_status not in {"done", "complete", "completed"}:
        errors.append(f"expected done status, got {done_status!r}")
    done_events = _event_kinds(done_payload)
    for required in ["created", "commented", "blocked", "unblocked", "completed"]:
        if required not in done_events:
            errors.append(f"missing Hermes event kind: {required}")
    receipt_metadata = False
    for run in done_payload.get("runs") or []:
        if not isinstance(run, dict):
            continue
        metadata = run.get("metadata") or {}
        if metadata.get("receipt_five") == "present" and metadata.get("runtime") == "hermes_kanban":
            receipt_metadata = True
    if not receipt_metadata:
        errors.append("missing Receipt Five runtime metadata on completed run")
    return errors


def run_live_smoke(*, board: str, out: Path, cwd: Path, title: str = DEFAULT_TITLE) -> dict[str, Any]:
    hermes = shutil.which("hermes")
    if not hermes:
        raise RuntimeError("hermes CLI not found on PATH")

    out.parent.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    task_title = f"{title} {timestamp}"
    operations: list[dict[str, Any]] = []

    create_board = _run(
        [
            hermes,
            "kanban",
            "boards",
            "create",
            board,
            "--name",
            "Overkill Factory V3 Production Activation",
            "--description",
            "Disposable evidence board for V3 master-plan production activation",
            "--default-workdir",
            str(cwd),
        ],
        cwd=cwd,
        allow_failure=True,
    )
    operations.append({"operation": "boards.create", "returncode": create_board.returncode})

    create = _run(
        [
            hermes,
            "kanban",
            "--board",
            board,
            "create",
            task_title,
            "--body",
            "V3 production activation live smoke. Proves Hermes Kanban create/comment/block/unblock/complete with Receipt Five evidence.",
            "--assignee",
            "factory-orchestrator",
            "--workspace",
            "scratch",
            "--created-by",
            "overkill-factory",
            "--json",
        ],
        cwd=cwd,
    )
    create_payload = _parse_json(create.stdout)
    task_id = str(create_payload["id"])
    operations.append({"operation": "task.create", "returncode": create.returncode, "task_id": task_id})

    commands = [
        [hermes, "kanban", "--board", board, "comment", task_id, "Runtime truth: Hermes Kanban is the backbone; this card is live smoke evidence for V3 Production Activation."],
        [hermes, "kanban", "--board", board, "block", task_id, "human_gate_packet_required"],
    ]
    for argv in commands:
        proc = _run(argv, cwd=cwd)
        operations.append({"operation": ".".join(argv[3:5]), "returncode": proc.returncode})

    blocked = _run([hermes, "kanban", "--board", board, "show", "--json", task_id], cwd=cwd)
    blocked_payload = _parse_json(blocked.stdout)
    operations.append({"operation": "task.show.blocked", "returncode": blocked.returncode})

    for argv in [
        [hermes, "kanban", "--board", board, "unblock", task_id],
        [hermes, "kanban", "--board", board, "comment", task_id, "Receipt Five readback: changed live Hermes task state; why V3 activation smoke; evidence produced by factory_hermes_live_smoke.py; next release gate requires master-plan completion PASS."],
        [
            hermes,
            "kanban",
            "--board",
            board,
            "complete",
            task_id,
            "--result",
            "PASS: live Hermes Kanban smoke completed with create/comment/block/unblock/complete evidence.",
            "--summary",
            "Factory Perfect Run live smoke passed.",
            "--metadata",
            '{"receipt_five":"present","runtime":"hermes_kanban","activation":"v3-production-activation"}',
        ],
    ]:
        proc = _run(argv, cwd=cwd)
        operations.append({"operation": ".".join(argv[3:5]), "returncode": proc.returncode})

    done = _run([hermes, "kanban", "--board", board, "show", "--json", task_id], cwd=cwd)
    done_payload = _parse_json(done.stdout)
    operations.append({"operation": "task.show.done", "returncode": done.returncode})

    errors = validate_smoke(blocked_payload, done_payload)
    report = {
        "record_type": "factory_hermes_live_smoke",
        "result": "PASS" if not errors else "FAIL",
        "board_slug": board,
        "task_id": task_id,
        "runtime_authority": "hermes_kanban",
        "operations": operations,
        "blocked_status": _task_status(blocked_payload),
        "done_status": _task_status(done_payload),
        "blocked_show": sanitize_show_payload(blocked_payload),
        "done_show": sanitize_show_payload(done_payload),
        "errors": errors,
    }
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a live Hermes Kanban smoke for Overkill Factory V3.")
    parser.add_argument("--board", default=DEFAULT_BOARD)
    parser.add_argument("--out", type=Path, default=Path(".tmp/factory-hermes-live-smoke.json"))
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    args = parser.parse_args()
    report = run_live_smoke(board=args.board, out=args.out, cwd=args.cwd.resolve())
    print(f"Wrote {args.out}")
    print(report["result"])
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
