#!/usr/bin/env python3
"""Hermes cron-friendly no-idle watchdog for Overkill Factory boards.

The watchdog is intentionally small: it does not schedule workers itself, does
not approve gates, and does not complete cards. It asks the public Hermes live
adapter to classify each board, optionally creates one safe remediation card,
and then calls native Hermes dispatch only when the adapter says dispatch is
the next required action.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
LIVE_ADAPTER = ROOT / "adapters" / "hermes" / "live_kanban_adapter.py"
DEFAULT_STATE_FILE = ROOT / ".tmp" / "factory-runs" / "no-idle-watchdog-state.json"
DEFAULT_INBOX_DIR = ROOT / ".tmp" / "factory-runs" / "operator-inbox"
DEFAULT_EXCLUDED_BOARDS = {"default"}
Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def default_runner(argv: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("HOME", str(Path.home()))
    return subprocess.run(  # nosec B603
        argv,
        text=True,
        capture_output=True,
        env=env,
        encoding="utf-8",
        errors="replace",
    )


def run_json(argv: list[str], *, runner: Runner = default_runner) -> Any:
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
    try:
        return json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("command did not return JSON: " + " ".join(argv)) from exc


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"boards": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"boards": {}}
    if not isinstance(data, dict):
        return {"boards": {}}
    data.setdefault("boards", {})
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def board_slug(row: dict[str, Any]) -> str:
    return str(row.get("slug") or row.get("name") or "").strip()


def board_total(row: dict[str, Any]) -> int:
    value = row.get("total")
    if isinstance(value, int):
        return value
    counts = row.get("counts")
    if isinstance(counts, dict):
        return sum(int(item) for item in counts.values() if isinstance(item, int))
    return 0


def discover_boards(
    *,
    hermes_bin: str,
    excluded_boards: set[str],
    runner: Runner = default_runner,
) -> list[str]:
    rows = run_json([hermes_bin, "kanban", "boards", "list", "--json"], runner=runner)
    if not isinstance(rows, list):
        return []
    boards: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        slug = board_slug(row)
        if not slug or slug in excluded_boards:
            continue
        if row.get("archived") is True:
            continue
        if board_total(row) <= 0:
            continue
        boards.append(slug)
    return boards


def run_no_idle(
    *,
    board: str,
    hermes_bin: str,
    create_remediation: bool,
    workspace: str,
    assignee: str,
    runner: Runner = default_runner,
) -> dict[str, Any]:
    argv = [
        sys.executable,
        str(LIVE_ADAPTER),
        "no-idle",
        "--board",
        board,
        "--hermes-bin",
        hermes_bin,
        "--workspace",
        workspace,
        "--assignee",
        assignee,
    ]
    if create_remediation:
        argv.append("--create-remediation")
    result = run_json(argv, runner=runner)
    if not isinstance(result, dict):
        raise RuntimeError("no-idle returned a non-object payload")
    return result


def run_dispatch(
    *,
    board: str,
    hermes_bin: str,
    max_dispatch: int,
    runner: Runner = default_runner,
) -> dict[str, Any]:
    argv = [
        sys.executable,
        str(LIVE_ADAPTER),
        "dispatch",
        "--board",
        board,
        "--hermes-bin",
        hermes_bin,
        "--max",
        str(max_dispatch),
    ]
    result = run_json(argv, runner=runner)
    if not isinstance(result, dict):
        raise RuntimeError("dispatch returned a non-object payload")
    return result


def emit_operator_event(
    *,
    board: str,
    status: str,
    summary: str,
    inbox_dir: Path,
    runner: Runner = default_runner,
) -> None:
    event_type = "human_gate_required" if status == "human_gate_required" else "worker_attention_required"
    severity = "requires_user" if status == "human_gate_required" else "notice"
    argv = [
        sys.executable,
        str(ROOT / "scripts" / "factory_bridge.py"),
        "emit-event",
        "--inbox-dir",
        str(inbox_dir),
        "--run-id",
        board,
        "--event-type",
        event_type,
        "--severity",
        severity,
        "--source",
        "automation",
        "--summary",
        summary,
        "--ref",
        f"hermes-board:{board}",
    ]
    if status == "human_gate_required":
        argv.append("--requires-user")
    completed = runner(argv)
    if completed.returncode != 0:
        raise RuntimeError(
            "failed to emit operator event\nstdout:\n"
            + (completed.stdout or "")
            + "\nstderr:\n"
            + (completed.stderr or "")
        )


def no_idle_signature(no_idle_result: dict[str, Any], dispatch_result: dict[str, Any] | None) -> dict[str, Any]:
    state = no_idle_result.get("no_idle_state") if isinstance(no_idle_result.get("no_idle_state"), dict) else {}
    counts = state.get("state") if isinstance(state.get("state"), dict) else {}
    dispatch_state = dispatch_result.get("dispatch_observed_state") if isinstance(dispatch_result, dict) else {}
    spawned = dispatch_result.get("spawned") if isinstance(dispatch_result, dict) else []
    return {
        "status": state.get("status"),
        "classification": state.get("classification"),
        "counts": {
            key: value.get("count")
            for key, value in counts.items()
            if isinstance(value, dict) and key in {"ready", "running", "todo", "blocked"}
        },
        "remediation_task_id": no_idle_result.get("remediation_task_id"),
        "dispatch": dispatch_state,
        "spawned_count": len(spawned) if isinstance(spawned, list) else 0,
    }


def summarize_board(board: str, signature: dict[str, Any]) -> str:
    status = signature.get("status")
    counts = signature.get("counts") if isinstance(signature.get("counts"), dict) else {}
    spawned = signature.get("spawned_count") or 0
    if status == "human_gate_required":
        return f"[Overkill Factory] {board}: gate humano real pendente."
    if status == "remediation_required":
        return (
            f"[Overkill Factory] {board}: no-idle detectado; remediação segura "
            f"criada/confirmada. todo={counts.get('todo', 0)} blocked={counts.get('blocked', 0)}."
        )
    if status == "dispatch_available" or spawned:
        return f"[Overkill Factory] {board}: dispatch nativo acionado; spawned={spawned}."
    if status == "active":
        return f"[Overkill Factory] {board}: workers em execução."
    return f"[Overkill Factory] {board}: estado {status or 'desconhecido'}."


def process_board(
    *,
    board: str,
    hermes_bin: str,
    create_remediation: bool,
    dispatch: bool,
    max_dispatch: int,
    workspace: str,
    assignee: str,
    inbox_dir: Path,
    emit_events: bool,
    state: dict[str, Any],
    runner: Runner = default_runner,
) -> str | None:
    no_idle_result = run_no_idle(
        board=board,
        hermes_bin=hermes_bin,
        create_remediation=create_remediation,
        workspace=workspace,
        assignee=assignee,
        runner=runner,
    )
    no_idle_state = no_idle_result.get("no_idle_state")
    if not isinstance(no_idle_state, dict):
        raise RuntimeError(f"no-idle result for {board} has no state object")
    dispatch_result: dict[str, Any] | None = None
    if dispatch and no_idle_state.get("native_dispatch_required_next") is True:
        dispatch_result = run_dispatch(
            board=board,
            hermes_bin=hermes_bin,
            max_dispatch=max_dispatch,
            runner=runner,
        )
    signature = no_idle_signature(no_idle_result, dispatch_result)
    previous = state.setdefault("boards", {}).get(board)
    state["boards"][board] = signature
    if previous == signature:
        return None
    summary = summarize_board(board, signature)
    if emit_events and signature.get("status") in {"human_gate_required", "remediation_required"}:
        emit_operator_event(
            board=board,
            status=str(signature.get("status") or ""),
            summary=summary,
            inbox_dir=inbox_dir,
            runner=runner,
        )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Overkill Factory no-idle watchdog for Hermes boards.")
    parser.add_argument("--board", action="append", default=[], help="Board slug to inspect. Repeatable.")
    parser.add_argument("--all-nonempty-boards", action="store_true", help="Discover all non-empty non-archived boards.")
    parser.add_argument("--exclude-board", action="append", default=sorted(DEFAULT_EXCLUDED_BOARDS))
    parser.add_argument("--hermes-bin", default="hermes")
    parser.add_argument("--create-remediation", action="store_true")
    parser.add_argument("--dispatch", action="store_true", help="Call native Hermes dispatch when no-idle says it is next.")
    parser.add_argument("--max-dispatch", type=int, default=1)
    parser.add_argument("--workspace", default="scratch")
    parser.add_argument("--assignee", default="factory-orchestrator")
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    parser.add_argument("--inbox-dir", type=Path, default=DEFAULT_INBOX_DIR)
    parser.add_argument("--emit-events", action="store_true")
    return parser


def main(argv: list[str] | None = None, *, runner: Runner = default_runner) -> int:
    args = build_parser().parse_args(argv)
    boards = list(dict.fromkeys(args.board))
    if args.all_nonempty_boards:
        discovered = discover_boards(
            hermes_bin=args.hermes_bin,
            excluded_boards=set(args.exclude_board),
            runner=runner,
        )
        boards = list(dict.fromkeys([*boards, *discovered]))
    if not boards:
        return 0
    state = load_state(args.state_file)
    messages: list[str] = []
    for board in boards:
        message = process_board(
            board=board,
            hermes_bin=args.hermes_bin,
            create_remediation=args.create_remediation,
            dispatch=args.dispatch,
            max_dispatch=args.max_dispatch,
            workspace=args.workspace,
            assignee=args.assignee,
            inbox_dir=args.inbox_dir,
            emit_events=args.emit_events,
            state=state,
            runner=runner,
        )
        if message:
            messages.append(message)
    save_state(args.state_file, state)
    if messages:
        print("\n".join(messages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
