#!/usr/bin/env python3
"""Materialize Overkill Factory worker gates in a real Hermes Kanban board."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any, Callable

from transition_hook import ACTION_BLOCK_TRANSITION, build_hook_result, write_json


ROOT = Path(__file__).resolve().parents[2]
TASK_ID_RE = re.compile(r"\bt_[a-f0-9]{8,}\b")
LIVE_ADAPTER_SCHEMA = "https://overkill-factory.dev/schemas/hermes-live-adapter-result.schema.json"
Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def default_runner(argv: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("HOME", str(Path.home()))
    env.setdefault("HERMES_HOME", env["HOME"])
    return subprocess.run(argv, text=True, capture_output=True, env=env)  # nosec B603


def run_checked(argv: list[str], runner: Runner = default_runner) -> subprocess.CompletedProcess[str]:
    completed = runner(argv)
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed: "
            + " ".join(argv)
            + "\nstdout:\n"
            + (completed.stdout or "")
            + "\nstderr:\n"
            + (completed.stderr or "")
        )
    return completed


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_task_id(output: str) -> str:
    text = (output or "").strip()
    if text:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            for key in ("id", "task_id"):
                value = data.get(key)
                if isinstance(value, str) and value:
                    return value
        match = TASK_ID_RE.search(text)
        if match:
            return match.group(0)
    raise RuntimeError(f"could not parse Hermes task id from output: {text!r}")


def hermes_kanban(hermes_bin: str, board: str, *args: str) -> list[str]:
    return [hermes_bin, "kanban", "--board", board, *args]


def record_live_binding(
    *,
    ledger_path: Path,
    card_id: str,
    board: str,
    main_task_id: str,
    worker_task_ids: dict[str, str],
) -> None:
    ledger = load_json(ledger_path)
    bindings = ledger.setdefault("live_bindings", {})
    bindings[card_id] = {
        "board": board,
        "main_task_id": main_task_id,
        "worker_task_ids": worker_task_ids,
    }
    write_json(ledger_path, ledger)


def validate_live_binding(*, ledger_path: Path, card_id: str, board: str, main_task_id: str) -> None:
    ledger = load_json(ledger_path)
    binding = (ledger.get("live_bindings") or {}).get(card_id)
    if not isinstance(binding, dict):
        raise RuntimeError(f"missing live binding for card {card_id}; refuse to complete arbitrary Hermes task")
    if binding.get("board") != board or binding.get("main_task_id") != main_task_id:
        raise RuntimeError("main task id does not match the live binding for this card and board")


def ensure_board(
    *,
    hermes_bin: str,
    board: str,
    default_workdir: str | None,
    runner: Runner = default_runner,
) -> bool:
    listed = run_checked([hermes_bin, "kanban", "boards", "list", "--json"], runner)
    boards = json.loads(listed.stdout or "[]")
    if any(isinstance(item, dict) and item.get("slug") == board for item in boards):
        return False
    args = [
        hermes_bin,
        "kanban",
        "boards",
        "create",
        board,
        "--name",
        "Overkill Factory Live Smoke",
        "--description",
        "Isolated board for Overkill Factory adapter validation.",
        "--icon",
        "O",
        "--color",
        "#0f766e",
    ]
    if default_workdir:
        args.extend(["--default-workdir", default_workdir])
    run_checked(args, runner)
    return True


def board_exists(*, hermes_bin: str, board: str, runner: Runner = default_runner) -> bool:
    listed = run_checked([hermes_bin, "kanban", "boards", "list", "--json"], runner)
    boards = json.loads(listed.stdout or "[]")
    return any(isinstance(item, dict) and item.get("slug") == board for item in boards)


def block_task(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    reason: str,
    runner: Runner = default_runner,
) -> None:
    run_checked(hermes_kanban(hermes_bin, board, "block", task_id, reason), runner)


def create_task(
    *,
    hermes_bin: str,
    board: str,
    title: str,
    body: str,
    assignee: str,
    idempotency_key: str,
    created_by: str,
    workspace: str,
    blocked: bool,
    parents: list[str] | None = None,
    runner: Runner = default_runner,
) -> str:
    args = hermes_kanban(
        hermes_bin,
        board,
        "create",
        title,
        "--body",
        body,
        "--assignee",
        assignee,
        "--idempotency-key",
        idempotency_key,
        "--created-by",
        created_by,
        "--workspace",
        workspace,
        "--json",
    )
    for parent in parents or []:
        args.extend(["--parent", parent])
    if blocked:
        args.extend(["--initial-status", "blocked"])
    task_id = parse_task_id(run_checked(args, runner).stdout)
    if blocked:
        block_task(
            hermes_bin=hermes_bin,
            board=board,
            task_id=task_id,
            reason="Blocked by Overkill Factory adapter until required worker evidence exists.",
            runner=runner,
        )
    return task_id


def default_workspace_for_card(card_path: Path) -> Path:
    parent = card_path.parent
    if parent.name == "cards":
        return parent.parent
    return parent


def materialize(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    card_path = args.card.resolve()
    ledger_path = args.ledger.resolve()
    result = build_hook_result(
        card_path=card_path,
        from_status=args.from_status,
        to_status=args.to_status,
        receipt_path=None,
        worker_results_dir=None,
        ledger_path=ledger_path,
    )
    plan = result["plan"]
    card_id = str(plan.get("event", {}).get("card_id") or card_path.stem)
    workspace = args.workspace.resolve() if args.workspace else default_workspace_for_card(card_path)
    board_created = False
    if args.dry_run and args.ensure_board:
        board_created = not board_exists(hermes_bin=args.hermes_bin, board=args.board, runner=runner)
    elif args.ensure_board:
        board_created = ensure_board(
            hermes_bin=args.hermes_bin,
            board=args.board,
            default_workdir=str(workspace),
            runner=runner,
        )

    if args.dry_run:
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "materialize",
            "dry_run": True,
            "board": args.board,
            "board_created": board_created,
            "workspace": str(workspace),
            "main_task_id": None,
            "worker_task_ids": {},
            "hook": result,
        }
        if args.out:
            write_json(args.out, envelope)
        return envelope

    main_task_id = create_task(
        hermes_bin=args.hermes_bin,
        board=args.board,
        title=f"OF {card_id} main gate",
        body=card_path.read_text(encoding="utf-8"),
        assignee=args.main_assignee,
        idempotency_key=f"overkill:{card_id}:main",
        created_by="overkill-factory",
        workspace=f"dir:{workspace}",
        blocked=True,
        runner=runner,
    )
    worker_task_ids: dict[str, str] = {}
    before_ready_task_ids: list[str] = []
    pending_before_done: list[dict[str, Any]] = []
    ordered_worker_tasks: list[dict[str, Any]] = []
    for task in plan.get("worker_tasks", []):
        if task.get("status") == "not_required_by_current_card":
            continue
        if task.get("queue_class") == "blocking-before-done":
            pending_before_done.append(task)
        else:
            ordered_worker_tasks.append(task)
    ordered_worker_tasks.extend(pending_before_done)

    for task in ordered_worker_tasks:
        worker_id = str(task.get("worker_id") or "").strip()
        if not worker_id:
            continue
        packet = task.get("packet") or {}
        depends_on_before_ready = task.get("queue_class") == "blocking-before-done"
        task_id = create_task(
            hermes_bin=args.hermes_bin,
            board=args.board,
            title=str(task.get("title") or f"OF {card_id} {worker_id}"),
            body=json.dumps(packet, indent=2, ensure_ascii=True),
            assignee=args.worker_assignee_prefix + worker_id,
            idempotency_key=f"overkill:{card_id}:{worker_id}",
            created_by="overkill-factory",
            workspace=f"dir:{workspace}",
            blocked=not args.worker_ready,
            parents=before_ready_task_ids if depends_on_before_ready else None,
            runner=runner,
        )
        worker_task_ids[worker_id] = task_id
        if task.get("queue_class") == "blocking-before-ready":
            before_ready_task_ids.append(task_id)
        run_checked(hermes_kanban(args.hermes_bin, args.board, "link", task_id, main_task_id), runner)

    record_live_binding(
        ledger_path=ledger_path,
        card_id=card_id,
        board=args.board,
        main_task_id=main_task_id,
        worker_task_ids=worker_task_ids,
    )

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "materialize",
        "dry_run": False,
        "board": args.board,
        "board_created": board_created,
        "workspace": str(workspace),
        "main_task_id": main_task_id,
        "worker_task_ids": worker_task_ids,
        "hook": result,
    }
    if args.out:
        write_json(args.out, envelope)
    return envelope


def enforce_done(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    result = build_hook_result(
        card_path=args.card.resolve(),
        from_status=args.from_status,
        to_status=args.to_status,
        receipt_path=args.receipt.resolve(),
        worker_results_dir=args.worker_results_dir.resolve(),
        ledger_path=args.ledger.resolve(),
    )
    blocked = result["transition_action"] == ACTION_BLOCK_TRANSITION
    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "enforce-done",
        "blocked": blocked,
        "board": args.board,
        "main_task_id": args.main_task_id,
        "hook": result,
    }
    if args.out:
        write_json(args.out, envelope)
    if blocked:
        return envelope
    if args.complete_main:
        card_id = str(result.get("plan", {}).get("event", {}).get("card_id") or args.card.stem)
        validate_live_binding(
            ledger_path=args.ledger.resolve(),
            card_id=card_id,
            board=args.board,
            main_task_id=args.main_task_id,
        )
        metadata = json.dumps(load_json(args.receipt.resolve()), ensure_ascii=True)
        run_checked(
            hermes_kanban(
                args.hermes_bin,
                args.board,
                "complete",
                args.main_task_id,
                "--result",
                args.result,
                "--summary",
                args.summary,
                "--metadata",
                metadata,
            ),
            runner,
        )
    return envelope


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate Overkill Factory gates on Hermes Kanban.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_mat = sub.add_parser("materialize", help="Create the main card and required worker cards.")
    p_mat.add_argument("--card", type=Path, required=True)
    p_mat.add_argument("--board", required=True)
    p_mat.add_argument("--ledger", type=Path, required=True)
    p_mat.add_argument("--from-status", default="blocked")
    p_mat.add_argument("--to-status", default="ready")
    p_mat.add_argument("--hermes-bin", default="hermes")
    p_mat.add_argument("--main-assignee", default="factory-orchestrator")
    p_mat.add_argument("--worker-assignee-prefix", default="")
    p_mat.add_argument("--workspace", type=Path, help="Hermes workspace for the main and worker cards. Defaults to the card workspace.")
    p_mat.add_argument("--worker-ready", action="store_true")
    p_mat.add_argument("--ensure-board", action="store_true")
    p_mat.add_argument("--dry-run", action="store_true")
    p_mat.add_argument("--out", type=Path)

    p_done = sub.add_parser("enforce-done", help="Validate worker results before completing the main card.")
    p_done.add_argument("--card", type=Path, required=True)
    p_done.add_argument("--board", required=True)
    p_done.add_argument("--main-task-id", required=True)
    p_done.add_argument("--receipt", type=Path, required=True)
    p_done.add_argument("--worker-results-dir", type=Path, required=True)
    p_done.add_argument("--ledger", type=Path, required=True)
    p_done.add_argument("--from-status", default="ready")
    p_done.add_argument("--to-status", default="done")
    p_done.add_argument("--hermes-bin", default="hermes")
    p_done.add_argument("--complete-main", action="store_true")
    p_done.add_argument("--result", default="Overkill Factory gate satisfied.")
    p_done.add_argument("--summary", default="Worker evidence reconciled by Overkill Factory.")
    p_done.add_argument("--out", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        envelope = materialize(args) if args.command == "materialize" else enforce_done(args)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not args.out:
        print(json.dumps(envelope, indent=2, ensure_ascii=True))
    if args.command == "enforce-done" and envelope.get("blocked"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
