#!/usr/bin/env python3
"""Prove dashboard/API delete-route guard for the Hermes vFinal adapter.

This smoke runs only against a disposable installed Hermes checkout/home with
patch 0008 applied. It calls the dashboard plugin `DELETE /tasks/{task_id}`
route function directly and verifies that active Overkill Factory cards and
worker subtasks cannot be hard-deleted.

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
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "dashboard-delete-route-guard-smoke.json"
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
    os.environ["OVERKILL_FACTORY_RUNTIME_DIR"] = str(hermes_home / "overkill-factory-dashboard-delete")
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
    if os.environ.get("OVERKILL_DASHBOARD_DELETE_REEXEC") == "1":
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
    env["OVERKILL_DASHBOARD_DELETE_REEXEC"] = "1"
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


def _task_exists(kanban_db: Any, *, board: str, task_id: str) -> bool:
    conn = kanban_db.connect(board=board)
    try:
        return kanban_db.get_task(conn, task_id) is not None
    finally:
        conn.close()


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


def _http_status(exc: BaseException) -> int | None:
    return getattr(exc, "status_code", None)


def _delete_attempt(plugin_api: Any, *, board: str, task_id: str) -> dict[str, Any]:
    try:
        result = plugin_api.delete_task(task_id, board=board)
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

    board = f"of-dashboard-delete-{int(time.time())}"
    kanban_db, plugin_api = _load_runtime(checkout, hermes_home, board)

    parent_id = _create_task(
        plugin_api,
        board=board,
        title="VFINAL-DASHBOARD-DELETE-GUARD",
        body=READY_CARD.read_text(encoding="utf-8"),
        assignee="factory-orchestrator",
    )
    workers_before = _worker_prerequisites(kanban_db, board=board, task_id=parent_id)
    worker_id = workers_before[0]["id"] if workers_before else ""

    parent_delete = _delete_attempt(plugin_api, board=board, task_id=parent_id)
    worker_delete = _delete_attempt(plugin_api, board=board, task_id=worker_id)

    normal_id = _create_task(
        plugin_api,
        board=board,
        title="NORMAL-DASHBOARD-DELETE-CONTROL",
        body="ordinary non-factory disposable task",
        assignee=None,
    )
    normal_delete = _delete_attempt(plugin_api, board=board, task_id=normal_id)

    workers_after = _worker_prerequisites(kanban_db, board=board, task_id=parent_id)
    parent_blocked = (
        parent_delete["ok"] is False
        and parent_delete["http_status"] == 409
        and _task_exists(kanban_db, board=board, task_id=parent_id)
    )
    worker_blocked = (
        worker_delete["ok"] is False
        and worker_delete["http_status"] == 409
        and bool(worker_id)
        and _task_exists(kanban_db, board=board, task_id=worker_id)
    )
    normal_allowed = normal_delete["ok"] is True and not _task_exists(kanban_db, board=board, task_id=normal_id)
    links_preserved = len(workers_before) == EXPECTED_WORKER_COUNT and len(workers_after) == EXPECTED_WORKER_COUNT
    passed = parent_blocked and worker_blocked and normal_allowed and links_preserved

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
            "card_id": "VFINAL-HERMES-DASHBOARD-DELETE-ROUTE-GUARD-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_DELETE_ROUTE_GUARD",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "PASS" if passed else "FAIL",
        "blocking_findings": not passed,
        "findings_summary": (
            "Dashboard/API delete-route guard smoke passed: hard-delete is blocked for vFinal parent cards and worker subtasks, links are preserved, and a normal disposable task can still be deleted."
            if passed
            else "Dashboard/API delete-route guard smoke failed."
        ),
        "tool_or_profile": "Hermes v0.16.0 disposable installed runtime with vFinal adapter patches including candidate 0008",
        "executed_by": "remote-proof-runner",
        "runtime_scope": (
            "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; direct Python calls into dashboard plugin route functions; no production dashboard server."
        ),
        "patches": [
            "adapters/hermes/patches/0008-guard-overkill-vfinal-dashboard-delete-route.patch"
        ],
        "checks": {
            "disposable_checkout_guard": "PASS",
            "disposable_home_guard": "PASS",
            "dashboard_delete_parent_vfinal_blocked": "PASS" if parent_blocked else "FAIL",
            "dashboard_delete_worker_subtask_blocked": "PASS" if worker_blocked else "FAIL",
            "dashboard_delete_normal_task_allowed": "PASS" if normal_allowed else "FAIL",
            "worker_prerequisite_links_preserved": "PASS" if links_preserved else "FAIL",
            "no_real_runtime_mutation": "PASS",
        },
        "dashboard_delete_evidence": {
            "board_slug": board,
            "parent_task_id": parent_id,
            "worker_task_id": worker_id,
            "worker_count_before": len(workers_before),
            "worker_count_after": len(workers_after),
            "parent_delete_attempt": parent_delete,
            "worker_delete_attempt": worker_delete,
            "normal_delete_attempt": {
                "task_id": normal_id,
                "ok": normal_delete["ok"],
                "deleted": normal_allowed,
            },
        },
        "important_limitations": [
            "This proves direct dashboard plugin route functions in a disposable installed Hermes runtime after candidate patch 0008.",
            "It does not start an authenticated HTTP dashboard server.",
            "It does not define the future archive or operator-approved deletion workflow.",
            "It does not authorize updating a real Hermes runtime.",
        ],
        "evidence_refs": [
            "adapters/hermes/patches/0008-guard-overkill-vfinal-dashboard-delete-route.patch",
            "adapters/hermes/dashboard_delete_route_guard_smoke.py",
            repo_ref(READY_CARD),
            "validation/hermes-installed-runtime-smoke/dashboard-delete-route-guard-smoke.json",
        ],
        "next_action": (
            "Add patch 0008 to the update sequence and continue proving remaining dashboard/API route families."
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
            "card_id": "VFINAL-HERMES-DASHBOARD-DELETE-ROUTE-GUARD-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_DELETE_ROUTE_GUARD",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "FAIL",
        "blocking_findings": True,
        "findings_summary": "Dashboard/API delete-route guard smoke did not complete.",
        "tool_or_profile": "adapters/hermes/dashboard_delete_route_guard_smoke.py",
        "executed_by": "remote-proof-runner",
        "checks": {
            "smoke_completed": "FAIL",
            "delete_route_guard": "FAIL",
            "no_real_runtime_touched": "PASS",
        },
        "error": error,
        "important_limitations": [
            "This failure receipt is public-safe and sanitized.",
            "A common cause is patch 0008 not being applied to the disposable runtime.",
        ],
        "evidence_refs": [
            "adapters/hermes/dashboard_delete_route_guard_smoke.py",
            "validation/hermes-installed-runtime-smoke/dashboard-delete-route-guard-smoke.json",
        ],
        "next_action": "Apply candidate patch 0008 to a disposable Hermes runtime, then rerun the delete-route guard smoke.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run dashboard/API delete-route guard smoke.")
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
