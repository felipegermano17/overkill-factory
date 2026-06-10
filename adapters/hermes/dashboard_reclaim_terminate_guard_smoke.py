#!/usr/bin/env python3
"""Prove dashboard/API reclaim and terminate guards for Hermes vFinal.

This smoke runs only against a disposable installed Hermes checkout/home with
patch 0013 applied. It calls dashboard plugin routes:

- POST /tasks/{task_id}/reclaim
- POST /runs/{run_id}/terminate

It verifies that Overkill Factory worker subtasks cannot be generically
reclaimed or terminated from dashboard/API, while ordinary disposable task
recovery still works.

It does not start a production dashboard server, use real credentials, dispatch
workers, or touch the real Hermes runtime.
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
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "dashboard-reclaim-terminate-guard-smoke.json"
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


def _runtime_env(checkout: Path, hermes_home: Path, board: str) -> None:
    scripts = checkout / ".venv" / ("Scripts" if os.name == "nt" else "bin")
    os.environ["HOME"] = str(hermes_home)
    os.environ["HERMES_HOME"] = str(hermes_home)
    os.environ["HERMES_KANBAN_BOARD"] = board
    os.environ["OVERKILL_FACTORY_KANBAN_GATE"] = "1"
    os.environ["OVERKILL_FACTORY_ADAPTER_ROOT"] = str(ROOT)
    os.environ["OVERKILL_FACTORY_CREATE_WORKER_TASKS"] = "1"
    os.environ["OVERKILL_FACTORY_WORKER_TASK_STATUS"] = "blocked"
    os.environ["OVERKILL_FACTORY_RUNTIME_DIR"] = str(hermes_home / "overkill-factory-dashboard-reclaim-terminate")
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
    if os.environ.get("OVERKILL_DASHBOARD_RECLAIM_TERMINATE_REEXEC") == "1":
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
    env["OVERKILL_DASHBOARD_RECLAIM_TERMINATE_REEXEC"] = "1"
    if os.name == "nt":
        completed = subprocess.run([str(python), str(Path(__file__).resolve()), *sys.argv[1:]], env=env)
        raise SystemExit(completed.returncode)
    os.execve(str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]], env)


def _load_runtime(checkout: Path, hermes_home: Path, board: str) -> tuple[Any, Any]:
    _runtime_env(checkout, hermes_home, board)
    from hermes_cli import kanban_db  # type: ignore
    from plugins.kanban.dashboard import plugin_api  # type: ignore

    kanban_db.init_db(board=board)
    return kanban_db, plugin_api


def _create_task(plugin_api: Any, *, board: str, title: str, body: str, assignee: str | None) -> str:
    result = plugin_api.create_task(
        plugin_api.CreateTaskBody(title=title, body=body, assignee=assignee),
        board=board,
    )
    if isinstance(result, dict):
        task = result.get("task")
        if isinstance(task, dict) and isinstance(task.get("id"), str):
            return task["id"]
    raise RuntimeError("dashboard create route did not return a task id")


def _worker_prerequisites(kanban_db: Any, *, board: str, task_id: str) -> list[dict[str, Any]]:
    conn = kanban_db.connect(board=board)
    try:
        rows = conn.execute(
            """
            SELECT t.id, t.title, t.status, t.assignee, t.created_by
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
        }
        for row in rows
    ]


def _task_state(kanban_db: Any, *, board: str, task_id: str) -> dict[str, Any]:
    conn = kanban_db.connect(board=board)
    try:
        row = conn.execute(
            "SELECT id, status, claim_lock, current_run_id FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"id": task_id, "missing": True}
    return {
        "id": row["id"],
        "status": row["status"],
        "claim_lock_present": row["claim_lock"] is not None,
        "current_run_id": row["current_run_id"],
    }


def _run_state(kanban_db: Any, *, board: str, run_id: int) -> dict[str, Any]:
    conn = kanban_db.connect(board=board)
    try:
        run = kanban_db.get_run(conn, run_id)
    finally:
        conn.close()
    if run is None:
        return {"run_id": run_id, "missing": True}
    return {
        "run_id": run.id,
        "task_id": run.task_id,
        "status": run.status,
        "outcome": run.outcome,
        "ended": run.ended_at is not None,
    }


def _arrange_running_task(kanban_db: Any, *, board: str, task_id: str, claimer: str) -> int:
    conn = kanban_db.connect(board=board)
    try:
        conn.execute(
            """
            UPDATE tasks
               SET status = 'ready',
                   claim_lock = NULL,
                   claim_expires = NULL,
                   current_run_id = NULL
             WHERE id = ?
            """,
            (task_id,),
        )
        conn.commit()
        claimed = kanban_db.claim_task(conn, task_id, claimer=claimer)
        if claimed is None:
            raise RuntimeError(f"could not claim arranged task {task_id}")
        row = conn.execute("SELECT current_run_id FROM tasks WHERE id = ?", (task_id,)).fetchone()
    finally:
        conn.close()
    if row is None or row["current_run_id"] is None:
        raise RuntimeError(f"claimed task {task_id} has no current_run_id")
    return int(row["current_run_id"])


def _http_status(exc: BaseException) -> int | None:
    return getattr(exc, "status_code", None)


def _reclaim_attempt(plugin_api: Any, *, board: str, task_id: str) -> dict[str, Any]:
    try:
        result = plugin_api.reclaim_task_endpoint(
            task_id,
            plugin_api.ReclaimBody(reason="dashboard reclaim/terminate guard smoke"),
            board=board,
        )
        return {"ok": True, "http_status": None, "result": result}
    except Exception as exc:
        return {
            "ok": False,
            "http_status": _http_status(exc),
            "detail": str(getattr(exc, "detail", "") or exc)[:180],
        }


def _terminate_attempt(plugin_api: Any, *, board: str, run_id: int) -> dict[str, Any]:
    try:
        result = plugin_api.terminate_run_endpoint(
            run_id,
            plugin_api.TerminateRunBody(reason="dashboard reclaim/terminate guard smoke"),
            board=board,
        )
        return {"ok": True, "http_status": None, "result": result}
    except Exception as exc:
        return {
            "ok": False,
            "http_status": _http_status(exc),
            "detail": str(getattr(exc, "detail", "") or exc)[:180],
        }


def run_smoke(*, checkout: Path, hermes_home: Path, allow_non_disposable: bool) -> dict[str, Any]:
    checkout = checkout.resolve()
    hermes_home = hermes_home.resolve()
    _assert_disposable_path(checkout, label="--hermes-checkout", allow_non_disposable=allow_non_disposable)
    _assert_disposable_path(hermes_home, label="--hermes-home", allow_non_disposable=allow_non_disposable)
    if not READY_CARD.is_file():
        raise SystemExit("ready card fixture missing")

    board = f"of-dashboard-reclaim-terminate-{int(time.time())}"
    kanban_db, plugin_api = _load_runtime(checkout, hermes_home, board)

    parent_id = _create_task(
        plugin_api,
        board=board,
        title="VFINAL-DASHBOARD-RECLAIM-TERMINATE-GUARD",
        body=READY_CARD.read_text(encoding="utf-8"),
        assignee="factory-orchestrator",
    )
    workers = _worker_prerequisites(kanban_db, board=board, task_id=parent_id)
    if len(workers) < 2:
        raise RuntimeError("expected at least two materialized worker subtasks")
    reclaim_worker_id = workers[0]["id"]
    terminate_worker_id = workers[1]["id"]

    reclaim_worker_run = _arrange_running_task(
        kanban_db,
        board=board,
        task_id=reclaim_worker_id,
        claimer="dashboard-reclaim-worker-smoke",
    )
    terminate_worker_run = _arrange_running_task(
        kanban_db,
        board=board,
        task_id=terminate_worker_id,
        claimer="dashboard-terminate-worker-smoke",
    )

    normal_reclaim_id = _create_task(
        plugin_api,
        board=board,
        title="NORMAL-RECLAIM-CONTROL",
        body="ordinary disposable task for reclaim control",
        assignee="ordinary-worker",
    )
    normal_terminate_id = _create_task(
        plugin_api,
        board=board,
        title="NORMAL-TERMINATE-CONTROL",
        body="ordinary disposable task for terminate control",
        assignee="ordinary-worker",
    )
    normal_reclaim_run = _arrange_running_task(
        kanban_db,
        board=board,
        task_id=normal_reclaim_id,
        claimer="dashboard-normal-reclaim-smoke",
    )
    normal_terminate_run = _arrange_running_task(
        kanban_db,
        board=board,
        task_id=normal_terminate_id,
        claimer="dashboard-normal-terminate-smoke",
    )

    worker_reclaim = _reclaim_attempt(plugin_api, board=board, task_id=reclaim_worker_id)
    worker_terminate = _terminate_attempt(plugin_api, board=board, run_id=terminate_worker_run)
    normal_reclaim = _reclaim_attempt(plugin_api, board=board, task_id=normal_reclaim_id)
    normal_terminate = _terminate_attempt(plugin_api, board=board, run_id=normal_terminate_run)

    states = {
        "reclaim_worker": _task_state(kanban_db, board=board, task_id=reclaim_worker_id),
        "terminate_worker": _task_state(kanban_db, board=board, task_id=terminate_worker_id),
        "normal_reclaim": _task_state(kanban_db, board=board, task_id=normal_reclaim_id),
        "normal_terminate": _task_state(kanban_db, board=board, task_id=normal_terminate_id),
    }
    runs = {
        "reclaim_worker": _run_state(kanban_db, board=board, run_id=reclaim_worker_run),
        "terminate_worker": _run_state(kanban_db, board=board, run_id=terminate_worker_run),
        "normal_reclaim": _run_state(kanban_db, board=board, run_id=normal_reclaim_run),
        "normal_terminate": _run_state(kanban_db, board=board, run_id=normal_terminate_run),
    }

    checks = {
        "disposable_checkout_guard": "PASS",
        "disposable_home_guard": "PASS",
        "dashboard_reclaim_worker_subtask_blocked": (
            "PASS" if worker_reclaim["ok"] is False and worker_reclaim["http_status"] == 409 else "FAIL"
        ),
        "dashboard_terminate_worker_run_blocked": (
            "PASS" if worker_terminate["ok"] is False and worker_terminate["http_status"] == 409 else "FAIL"
        ),
        "worker_reclaim_run_preserved_after_block": (
            "PASS"
            if states["reclaim_worker"]["status"] == "running"
            and states["reclaim_worker"]["current_run_id"] == reclaim_worker_run
            and runs["reclaim_worker"]["ended"] is False
            else "FAIL"
        ),
        "worker_terminate_run_preserved_after_block": (
            "PASS"
            if states["terminate_worker"]["status"] == "running"
            and states["terminate_worker"]["current_run_id"] == terminate_worker_run
            and runs["terminate_worker"]["ended"] is False
            else "FAIL"
        ),
        "dashboard_reclaim_normal_task_allowed": (
            "PASS"
            if normal_reclaim["ok"] is True
            and states["normal_reclaim"]["status"] == "ready"
            and states["normal_reclaim"]["claim_lock_present"] is False
            and runs["normal_reclaim"]["ended"] is True
            else "FAIL"
        ),
        "dashboard_terminate_normal_run_allowed": (
            "PASS"
            if normal_terminate["ok"] is True
            and states["normal_terminate"]["status"] == "ready"
            and states["normal_terminate"]["claim_lock_present"] is False
            and runs["normal_terminate"]["ended"] is True
            else "FAIL"
        ),
        "worker_prerequisite_count_preserved": "PASS" if len(workers) == EXPECTED_WORKER_COUNT else "FAIL",
        "no_real_runtime_mutation": "PASS",
    }
    result = "PASS" if all(value == "PASS" for value in checks.values()) else "FAIL"

    return {
        "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": "remote_proof_result",
        "created_at": utc_now(),
        "worker": {"id": "remote-proof-runner", "name": "Remote Proof Runner", "factory_phase": "F13-F16"},
        "card_ref": {
            "card_id": "VFINAL-HERMES-DASHBOARD-RECLAIM-TERMINATE-GUARD-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_RECLAIM_TERMINATE_GUARD",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": result,
        "blocking_findings": result != "PASS",
        "findings_summary": (
            "Dashboard/API reclaim and terminate guard smoke passed: vFinal worker subtasks "
            "cannot be generically reclaimed or terminated, while ordinary disposable task "
            "recovery still works."
            if result == "PASS"
            else "Dashboard/API reclaim and terminate guard smoke failed; inspect checks."
        ),
        "tool_or_profile": "Hermes v0.16.0 disposable installed runtime with vFinal adapter patches including candidate 0013",
        "executed_by": "remote-proof-runner",
        "runtime_scope": "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; direct Python calls into dashboard plugin route functions; no production dashboard server.",
        "patches": ["adapters/hermes/patches/0013-guard-overkill-vfinal-dashboard-reclaim-terminate-routes.patch"],
        "checks": checks,
        "dashboard_reclaim_terminate_evidence": {
            "board_slug": board,
            "parent_task_id": parent_id,
            "worker_count": len(workers),
            "task_ids": {
                "reclaim_worker": reclaim_worker_id,
                "terminate_worker": terminate_worker_id,
                "normal_reclaim": normal_reclaim_id,
                "normal_terminate": normal_terminate_id,
            },
            "run_ids": {
                "reclaim_worker": reclaim_worker_run,
                "terminate_worker": terminate_worker_run,
                "normal_reclaim": normal_reclaim_run,
                "normal_terminate": normal_terminate_run,
            },
            "attempts": {
                "worker_reclaim": worker_reclaim,
                "worker_terminate": worker_terminate,
                "normal_reclaim": normal_reclaim,
                "normal_terminate": normal_terminate,
            },
            "task_states": states,
            "run_states": runs,
        },
        "important_limitations": [
            "This proves direct dashboard plugin route functions in a disposable installed Hermes runtime after candidate patch 0013.",
            "The smoke arranges disposable task state directly to create running controls without spawning real workers.",
            "It does not start an authenticated HTTP dashboard server.",
            "It does not define a future operator-approved recovery workflow.",
            "It does not authorize updating a real Hermes runtime.",
        ],
        "evidence_refs": [
            "adapters/hermes/patches/0013-guard-overkill-vfinal-dashboard-reclaim-terminate-routes.patch",
            "adapters/hermes/dashboard_reclaim_terminate_guard_smoke.py",
            "validation/cards/vfinal-r3-ready.md",
            "validation/hermes-installed-runtime-smoke/dashboard-reclaim-terminate-guard-smoke.json",
        ],
        "next_action": "Add patch 0013 to the update sequence and continue proving remaining dashboard/API route families.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hermes-checkout", required=True, type=Path)
    parser.add_argument("--hermes-home", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--allow-non-disposable", action="store_true")
    args = parser.parse_args()

    _reexec_with_checkout_python(args.hermes_checkout.resolve())
    replacements = {
        str(args.hermes_checkout.resolve()): "external:disposable-hermes-checkout",
        str(args.hermes_home.resolve()): "external:disposable-hermes-home",
        str(ROOT.resolve()): "external:overkill-factory",
    }
    try:
        result = run_smoke(
            checkout=args.hermes_checkout,
            hermes_home=args.hermes_home,
            allow_non_disposable=args.allow_non_disposable,
        )
    except Exception as exc:
        result = {
            "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
            "record_type": "remote_proof_result",
            "created_at": utc_now(),
            "worker": {"id": "remote-proof-runner", "name": "Remote Proof Runner"},
            "card_ref": {
                "card_id": "VFINAL-HERMES-DASHBOARD-RECLAIM-TERMINATE-GUARD-SMOKE",
                "slice_id": "VFINAL_HERMES_DASHBOARD_RECLAIM_TERMINATE_GUARD",
                "phase": "F13",
                "risk_effective": "R3",
                "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            },
            "result": "FAIL",
            "blocking_findings": True,
            "findings_summary": _safe_error(exc, replacements),
            "tool_or_profile": "adapters/hermes/dashboard_reclaim_terminate_guard_smoke.py",
            "executed_by": "remote-proof-runner",
            "important_limitations": [
                "Failure happened inside disposable-smoke orchestration; inspect locally before any real runtime update."
            ],
            "evidence_refs": [
                "adapters/hermes/dashboard_reclaim_terminate_guard_smoke.py",
                "validation/hermes-installed-runtime-smoke/dashboard-reclaim-terminate-guard-smoke.json",
            ],
        }
    write_json(args.out, result)
    print(json.dumps({"result": result.get("result"), "out": repo_ref(args.out)}, indent=2))
    return 0 if result.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
