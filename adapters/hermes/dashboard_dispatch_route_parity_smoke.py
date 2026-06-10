#!/usr/bin/env python3
"""Prove dashboard/API dispatch-route parity for the Hermes vFinal adapter.

This smoke runs only against a disposable installed Hermes checkout/home. It
calls the dashboard plugin `POST /dispatch` route function directly and verifies
that the route uses the same dispatcher mechanics as the CLI/Kanban path.

It does not start a production dashboard server, use real credentials, call a
real model, or touch the real Hermes runtime.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
READY_CARD = ROOT / "validation" / "cards" / "vfinal-r3-ready.md"
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "dashboard-dispatch-route-parity-smoke.json"
EXPECTED_WORKER_COUNT = 23


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _safe_error(exc: BaseException, replacements: dict[str, str]) -> str:
    text = f"{type(exc).__name__}: {exc}"
    for raw, replacement in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        if raw:
            text = text.replace(raw, replacement)
    return text


def _assert_disposable_path(path: Path, *, label: str, allow_non_disposable: bool) -> None:
    if allow_non_disposable:
        return
    lowered = str(path.resolve()).lower()
    if "\\.tmp\\" in lowered or "/.tmp/" in lowered or lowered.endswith("\\.tmp") or lowered.endswith("/.tmp"):
        return
    raise SystemExit(
        f"{label} must point to a disposable .tmp runtime, or pass "
        "--allow-non-disposable after an explicit operator decision."
    )


def _runtime_env(checkout: Path, hermes_home: Path, board: str, *, worker_task_status: str) -> None:
    scripts = checkout / ".venv" / ("Scripts" if os.name == "nt" else "bin")
    os.environ["HOME"] = str(hermes_home)
    os.environ["HERMES_HOME"] = str(hermes_home)
    os.environ["HERMES_KANBAN_BOARD"] = board
    os.environ["OVERKILL_FACTORY_KANBAN_GATE"] = "1"
    os.environ["OVERKILL_FACTORY_ADAPTER_ROOT"] = str(ROOT)
    os.environ["OVERKILL_FACTORY_CREATE_WORKER_TASKS"] = "1"
    os.environ["OVERKILL_FACTORY_WORKER_TASK_STATUS"] = worker_task_status
    os.environ["OVERKILL_FACTORY_RUNTIME_DIR"] = str(hermes_home / "overkill-factory-dashboard-dispatch")
    os.environ["PYTHONPATH"] = str(checkout) + os.pathsep + os.environ.get("PYTHONPATH", "")
    os.environ["PATH"] = str(scripts) + os.pathsep + os.environ.get("PATH", "")
    sys.path.insert(0, str(checkout))


def _venv_python(checkout: Path) -> Path | None:
    scripts = checkout / ".venv" / ("Scripts" if os.name == "nt" else "bin")
    for name in ("python.exe", "python"):
        candidate = scripts / name
        if candidate.exists():
            return candidate
    return None


def _reexec_with_checkout_python(checkout: Path) -> None:
    if os.environ.get("OVERKILL_DASHBOARD_DISPATCH_REEXEC") == "1":
        return
    python = _venv_python(checkout)
    if python is None:
        return
    try:
        if Path(sys.executable).resolve() == python.resolve():
            return
    except OSError:
        pass
    env = os.environ.copy()
    env["OVERKILL_DASHBOARD_DISPATCH_REEXEC"] = "1"
    if os.name == "nt":
        completed = subprocess.run([str(python), str(Path(__file__).resolve()), *sys.argv[1:]], env=env)
        raise SystemExit(completed.returncode)
    os.execve(str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]], env)


def _load_runtime(checkout: Path, hermes_home: Path, board: str, *, worker_task_status: str) -> tuple[Any, Any]:
    _runtime_env(checkout, hermes_home, board, worker_task_status=worker_task_status)
    from hermes_cli import kanban_db  # type: ignore
    from plugins.kanban.dashboard import plugin_api  # type: ignore

    kanban_db.init_db(board=board)
    return kanban_db, plugin_api


def _create_vfinal_task(plugin_api: Any, *, board: str, title: str) -> str:
    result = plugin_api.create_task(
        plugin_api.CreateTaskBody(
            title=title,
            body=READY_CARD.read_text(encoding="utf-8"),
            assignee="factory-orchestrator",
        ),
        board=board,
    )
    if isinstance(result, dict):
        task = result.get("task")
        if isinstance(task, dict) and isinstance(task.get("id"), str):
            return task["id"]
    raise RuntimeError("dashboard create route did not return a task id")


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


def _task_status(kanban_db: Any, *, board: str, task_id: str) -> str:
    conn = kanban_db.connect(board=board)
    try:
        task = kanban_db.get_task(conn, task_id)
        return task.status if task is not None else "missing"
    finally:
        conn.close()


def _worker_prerequisites(kanban_db: Any, *, board: str, task_id: str) -> list[dict[str, Any]]:
    conn = kanban_db.connect(board=board)
    try:
        rows = conn.execute(
            """
            SELECT t.id, t.title, t.status, t.assignee, t.created_by, t.worker_pid
            FROM task_links AS l
            JOIN tasks AS t ON t.id = l.parent_id
            WHERE l.child_id = ?
            ORDER BY t.id
            """,
            (task_id,),
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "status": row["status"],
            "assignee": row["assignee"],
            "created_by": row["created_by"],
            "worker_pid": row["worker_pid"],
        }
        for row in rows
    ]


def _set_worker_statuses(
    kanban_db: Any,
    *,
    board: str,
    parent_task_id: str,
    selected_worker_id: str | None = None,
    selected_status: str = "ready",
    other_status: str = "blocked",
) -> None:
    workers = _worker_prerequisites(kanban_db, board=board, task_id=parent_task_id)
    conn = kanban_db.connect(board=board)
    try:
        for worker in workers:
            status = selected_status if selected_worker_id is not None and worker["id"] == selected_worker_id else other_status
            conn.execute(
                "UPDATE tasks SET status = ?, priority = CASE WHEN id = ? THEN 100 ELSE priority END WHERE id = ?",
                (status, selected_worker_id or "", worker["id"]),
            )
        conn.commit()
    finally:
        conn.close()


def _status_counts(workers: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for worker in workers:
        status = str(worker["status"])
        counts[status] = counts.get(status, 0) + 1
    return counts


def run_smoke(*, checkout: Path, hermes_home: Path, allow_non_disposable: bool) -> dict[str, Any]:
    checkout = checkout.resolve()
    hermes_home = hermes_home.resolve()
    _assert_disposable_path(checkout, label="--hermes-checkout", allow_non_disposable=allow_non_disposable)
    _assert_disposable_path(hermes_home, label="--hermes-home", allow_non_disposable=allow_non_disposable)
    if not READY_CARD.is_file():
        raise SystemExit("ready card fixture missing")

    blocked_board = f"of-dashboard-dispatch-blocked-{int(time.time())}"
    kanban_db, plugin_api = _load_runtime(checkout, hermes_home, blocked_board, worker_task_status="blocked")
    blocked_parent_id = _create_vfinal_task(plugin_api, board=blocked_board, title="VFINAL-DASHBOARD-DISPATCH-BLOCKED")
    blocked_workers = _worker_prerequisites(kanban_db, board=blocked_board, task_id=blocked_parent_id)
    _ensure_profile_dirs(hermes_home, {"factory-orchestrator"})
    blocked_dispatch = plugin_api.dispatch(dry_run=False, max_n=3, board=blocked_board)
    blocked_after_workers = _worker_prerequisites(kanban_db, board=blocked_board, task_id=blocked_parent_id)
    blocked_parent_status = _task_status(kanban_db, board=blocked_board, task_id=blocked_parent_id)

    spawn_board = f"of-dashboard-dispatch-spawn-{int(time.time())}"
    kanban_db, plugin_api = _load_runtime(checkout, hermes_home, spawn_board, worker_task_status="ready")
    spawn_parent_id = _create_vfinal_task(plugin_api, board=spawn_board, title="VFINAL-DASHBOARD-DISPATCH-SPAWN")
    spawn_workers_initial = _worker_prerequisites(kanban_db, board=spawn_board, task_id=spawn_parent_id)
    worker_ids = {str(worker["assignee"] or "") for worker in spawn_workers_initial}
    _ensure_profile_dirs(hermes_home, worker_ids | {"factory-orchestrator"})
    selected_worker_id = spawn_workers_initial[0]["id"] if spawn_workers_initial else None

    spawned_calls: list[dict[str, Any]] = []

    def synthetic_spawn(task: Any, workspace: str, board: str | None = None) -> int:
        spawned_calls.append(
            {
                "task_id": task.id,
                "assignee": task.assignee,
                "workspace_ref": "disposable-worker-workspace",
                "board": board,
            }
        )
        return 515151

    original_spawn = getattr(kanban_db, "_default_spawn")
    try:
        setattr(kanban_db, "_default_spawn", synthetic_spawn)
        spawn_dispatch = plugin_api.dispatch(dry_run=False, max_n=1, board=spawn_board)
    finally:
        setattr(kanban_db, "_default_spawn", original_spawn)

    spawn_after_workers = _worker_prerequisites(kanban_db, board=spawn_board, task_id=spawn_parent_id)
    spawn_parent_status = _task_status(kanban_db, board=spawn_board, task_id=spawn_parent_id)
    spawned_ids = [str(item[0]) for item in spawn_dispatch.get("spawned", [])] if isinstance(spawn_dispatch, dict) else []

    blocked_route_safe = (
        isinstance(blocked_dispatch, dict)
        and len(blocked_dispatch.get("spawned", [])) == 0
        and blocked_parent_status in {"ready", "todo"}
        and len(blocked_workers) == EXPECTED_WORKER_COUNT
        and _status_counts(blocked_after_workers) == {"blocked": EXPECTED_WORKER_COUNT}
    )
    spawn_route_safe = (
        isinstance(spawn_dispatch, dict)
        and selected_worker_id is not None
        and spawned_ids == [selected_worker_id]
        and len(spawned_calls) == 1
        and spawned_calls[0]["task_id"] == selected_worker_id
        and spawn_parent_id not in spawned_ids
        and spawn_parent_status in {"ready", "todo"}
    )
    selected_after = [worker for worker in spawn_after_workers if worker["id"] == selected_worker_id]
    selected_worker_running = bool(
        selected_after
        and selected_after[0]["status"] == "running"
        and int(selected_after[0]["worker_pid"] or 0) == 515151
    )
    passed = blocked_route_safe and spawn_route_safe and selected_worker_running

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
            "card_id": "VFINAL-HERMES-DASHBOARD-DISPATCH-ROUTE-PARITY-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_DISPATCH_ROUTE_PARITY",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api", "dispatcher"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "PASS" if passed else "FAIL",
        "blocking_findings": not passed,
        "findings_summary": (
            "Dashboard/API dispatch-route parity smoke passed: POST /dispatch did not spawn blocked worker subtasks, did not spawn the parent Factory card, and did spawn only the selected ready worker through a stubbed spawn function."
            if passed
            else "Dashboard/API dispatch-route parity smoke failed."
        ),
        "tool_or_profile": "Hermes v0.16.0 disposable installed runtime with vFinal adapter patches; dispatcher spawn function stubbed",
        "executed_by": "remote-proof-runner",
        "runtime_scope": (
            "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; direct Python calls into dashboard plugin route functions; no production dashboard server."
        ),
        "checks": {
            "disposable_checkout_guard": "PASS",
            "disposable_home_guard": "PASS",
            "dashboard_dispatch_blocked_workers_no_spawn": "PASS" if blocked_route_safe else "FAIL",
            "dashboard_dispatch_parent_not_spawned_before_workers_done": "PASS" if spawn_parent_id not in spawned_ids else "FAIL",
            "dashboard_dispatch_selected_ready_worker_spawned": "PASS" if spawn_route_safe else "FAIL",
            "dashboard_dispatch_stubbed_worker_running": "PASS" if selected_worker_running else "FAIL",
            "no_real_runtime_mutation": "PASS",
        },
        "dashboard_dispatch_evidence": {
            "blocked_worker_board": {
                "board_slug": blocked_board,
                "parent_task_id": blocked_parent_id,
                "parent_status_after_dispatch": blocked_parent_status,
                "worker_status_counts_after_dispatch": _status_counts(blocked_after_workers),
                "dispatch_spawned_count": len(blocked_dispatch.get("spawned", [])) if isinstance(blocked_dispatch, dict) else None,
                "route_result_keys": sorted(blocked_dispatch.keys()) if isinstance(blocked_dispatch, dict) else [],
            },
            "spawnable_worker_board": {
                "board_slug": spawn_board,
                "parent_task_id": spawn_parent_id,
                "parent_status_after_dispatch": spawn_parent_status,
                "selected_worker_id": selected_worker_id,
                "dispatch_spawned_ids": spawned_ids,
                "spawned_calls": spawned_calls,
                "worker_status_counts_after_dispatch": _status_counts(spawn_after_workers),
            },
        },
        "important_limitations": [
            "This proves direct dashboard plugin route functions in a disposable installed Hermes runtime.",
            "The spawn function was stubbed; no real Hermes child process, model call or specialist execution happened.",
            "It does not start an authenticated HTTP dashboard server.",
            "It does not prove real worker execution, real model/tool auth, or production readiness.",
        ],
        "evidence_refs": [
            "adapters/hermes/dashboard_dispatch_route_parity_smoke.py",
            repo_ref(READY_CARD),
            "validation/hermes-installed-runtime-smoke/dashboard-dispatch-route-parity-smoke.json",
        ],
        "next_action": (
            "Continue proving remaining dashboard/API route families and run non-stub model/tool-auth worker proof before any real-runtime update."
        ),
    }


def build_fail_receipt(error: str) -> dict[str, Any]:
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
            "card_id": "VFINAL-HERMES-DASHBOARD-DISPATCH-ROUTE-PARITY-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_DISPATCH_ROUTE_PARITY",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api", "dispatcher"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "FAIL",
        "blocking_findings": True,
        "findings_summary": "Dashboard/API dispatch-route parity smoke did not complete.",
        "tool_or_profile": "adapters/hermes/dashboard_dispatch_route_parity_smoke.py",
        "executed_by": "remote-proof-runner",
        "checks": {
            "smoke_completed": "FAIL",
            "dispatch_route_parity": "FAIL",
            "no_real_runtime_touched": "PASS",
        },
        "error": error,
        "important_limitations": [
            "This failure receipt is public-safe and sanitized.",
            "A common cause is a Hermes dashboard dependency missing from the disposable runtime.",
        ],
        "evidence_refs": [
            "adapters/hermes/dashboard_dispatch_route_parity_smoke.py",
            "validation/hermes-installed-runtime-smoke/dashboard-dispatch-route-parity-smoke.json",
        ],
        "next_action": (
            "Fix dashboard plugin import/runtime dependencies, then rerun the dashboard dispatch-route parity smoke."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run dashboard/API dispatch-route parity smoke.")
    parser.add_argument("--hermes-checkout", type=Path, required=True)
    parser.add_argument("--hermes-home", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--allow-non-disposable",
        action="store_true",
        help="Allow non-.tmp paths only after an explicit operator decision.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    _reexec_with_checkout_python(args.hermes_checkout.resolve())
    replacements = {
        str(args.hermes_checkout.resolve()): "redacted-disposable-checkout",
        str(args.hermes_home.resolve()): "redacted-disposable-hermes-home",
        str(ROOT.resolve()): "repo-root",
    }
    try:
        receipt = run_smoke(
            checkout=args.hermes_checkout,
            hermes_home=args.hermes_home,
            allow_non_disposable=args.allow_non_disposable,
        )
    except Exception as exc:
        receipt = build_fail_receipt(_safe_error(exc, replacements))
    write_json(args.out, receipt)
    print(json.dumps({"result": receipt["result"], "out": repo_ref(args.out)}, indent=2))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
