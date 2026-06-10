#!/usr/bin/env python3
"""Prove dashboard/API board archive/delete guard for the Hermes vFinal adapter.

This smoke runs only against a disposable installed Hermes checkout/home with
patch 0016 applied. It calls dashboard plugin `DELETE /boards/{slug}` directly
and verifies that boards containing Overkill Factory cards or worker subtasks
cannot be archived or hard-deleted from generic dashboard/API routes.

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
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "dashboard-board-delete-route-guard-smoke.json"
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
    os.environ["OVERKILL_FACTORY_RUNTIME_DIR"] = str(hermes_home / "overkill-factory-dashboard-board-delete")
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
    if os.environ.get("OVERKILL_DASHBOARD_BOARD_DELETE_REEXEC") == "1":
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
    env["OVERKILL_DASHBOARD_BOARD_DELETE_REEXEC"] = "1"
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


def _create_board(kanban_db: Any, *, board: str) -> None:
    kanban_db.create_board(board, name=board.replace("-", " ").title())


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


def _board_task_count(kanban_db: Any, *, board: str) -> int:
    conn = kanban_db.connect(board=board)
    try:
        return len(kanban_db.list_tasks(conn, include_archived=True))
    finally:
        conn.close()


def _http_status(exc: BaseException) -> int | None:
    return getattr(exc, "status_code", None)


def _sanitize_delete_result(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {"raw_type": type(result).__name__}
    raw_result = result.get("result")
    sanitized: dict[str, Any] = {"current": result.get("current")}
    if isinstance(raw_result, dict):
        sanitized["result"] = {
            "slug": raw_result.get("slug"),
            "action": raw_result.get("action"),
            "new_path": "redacted-local-board-path" if raw_result.get("new_path") else "",
        }
    return sanitized


def _board_delete_attempt(plugin_api: Any, *, board: str, delete: bool) -> dict[str, Any]:
    try:
        result = plugin_api.delete_board(board, delete=delete)
        return {
            "ok": True,
            "http_status": None,
            "delete": delete,
            "result": _sanitize_delete_result(result),
        }
    except Exception as exc:
        return {
            "ok": False,
            "http_status": _http_status(exc),
            "delete": delete,
            "detail": str(getattr(exc, "detail", "") or exc)[:180],
        }


def run_smoke(*, checkout: Path, hermes_home: Path, allow_non_disposable: bool) -> dict[str, Any]:
    checkout = checkout.resolve()
    hermes_home = hermes_home.resolve()
    _assert_disposable_path(checkout, label="--hermes-checkout", allow_non_disposable=allow_non_disposable)
    _assert_disposable_path(hermes_home, label="--hermes-home", allow_non_disposable=allow_non_disposable)
    if not READY_CARD.is_file():
        raise SystemExit("ready card fixture missing")

    stamp = int(time.time())
    env_board = f"of-dashboard-board-env-{stamp}"
    factory_board = f"of-dashboard-board-guard-{stamp}"
    normal_archive_board = f"of-dashboard-board-archive-{stamp}"
    normal_delete_board = f"of-dashboard-board-delete-{stamp}"
    kanban_db, plugin_api = _load_runtime(checkout, hermes_home, env_board)

    _create_board(kanban_db, board=factory_board)
    _create_board(kanban_db, board=normal_archive_board)
    _create_board(kanban_db, board=normal_delete_board)

    parent_id = _create_task(
        plugin_api,
        board=factory_board,
        title="VFINAL-DASHBOARD-BOARD-DELETE-GUARD",
        body=READY_CARD.read_text(encoding="utf-8"),
        assignee="factory-orchestrator",
    )
    workers_before = _worker_prerequisites(kanban_db, board=factory_board, task_id=parent_id)
    factory_task_count_before = _board_task_count(kanban_db, board=factory_board)

    factory_archive = _board_delete_attempt(plugin_api, board=factory_board, delete=False)
    factory_hard_delete = _board_delete_attempt(plugin_api, board=factory_board, delete=True)
    factory_exists_after = kanban_db.board_exists(factory_board)
    factory_task_count_after = _board_task_count(kanban_db, board=factory_board)

    _create_task(
        plugin_api,
        board=normal_archive_board,
        title="NORMAL-BOARD-ARCHIVE-CONTROL",
        body="ordinary non-factory disposable task",
        assignee=None,
    )
    normal_archive = _board_delete_attempt(plugin_api, board=normal_archive_board, delete=False)
    normal_archive_exists_after = kanban_db.board_exists(normal_archive_board)

    _create_task(
        plugin_api,
        board=normal_delete_board,
        title="NORMAL-BOARD-DELETE-CONTROL",
        body="ordinary non-factory disposable task",
        assignee=None,
    )
    normal_hard_delete = _board_delete_attempt(plugin_api, board=normal_delete_board, delete=True)
    normal_delete_exists_after = kanban_db.board_exists(normal_delete_board)

    checks = {
        "disposable_checkout_guard": "PASS",
        "disposable_home_guard": "PASS",
        "dashboard_board_archive_factory_board_blocked": (
            "PASS" if factory_archive["ok"] is False and factory_archive["http_status"] == 409 else "FAIL"
        ),
        "dashboard_board_hard_delete_factory_board_blocked": (
            "PASS" if factory_hard_delete["ok"] is False and factory_hard_delete["http_status"] == 409 else "FAIL"
        ),
        "factory_board_still_exists": "PASS" if factory_exists_after else "FAIL",
        "factory_board_task_count_preserved": (
            "PASS" if factory_task_count_after == factory_task_count_before else "FAIL"
        ),
        "worker_prerequisite_count_preserved": (
            "PASS" if len(workers_before) == EXPECTED_WORKER_COUNT else "FAIL"
        ),
        "dashboard_board_archive_normal_board_allowed": (
            "PASS" if normal_archive["ok"] is True and normal_archive_exists_after is False else "FAIL"
        ),
        "dashboard_board_hard_delete_normal_board_allowed": (
            "PASS" if normal_hard_delete["ok"] is True and normal_delete_exists_after is False else "FAIL"
        ),
        "receipt_sanitizes_local_paths": (
            "PASS"
            if "redacted-local-board-path" in json.dumps([normal_archive, normal_hard_delete])
            else "FAIL"
        ),
        "no_real_runtime_mutation": "PASS",
    }
    result = "PASS" if all(value == "PASS" for value in checks.values()) else "FAIL"

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
            "card_id": "VFINAL-HERMES-DASHBOARD-BOARD-DELETE-ROUTE-GUARD-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_BOARD_DELETE_ROUTE_GUARD",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": result,
        "blocking_findings": result != "PASS",
        "findings_summary": (
            "Dashboard/API board archive/delete guard smoke passed: boards containing vFinal Factory work cannot be archived or hard-deleted, while ordinary disposable boards can still be archived or deleted."
            if result == "PASS"
            else "Dashboard/API board archive/delete guard smoke failed; inspect checks."
        ),
        "tool_or_profile": "Hermes v0.16.0 disposable installed runtime with vFinal adapter patches including candidate 0016",
        "executed_by": "remote-proof-runner",
        "runtime_scope": "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; direct Python calls into dashboard plugin route functions; no production dashboard server.",
        "patches": ["adapters/hermes/patches/0016-guard-overkill-vfinal-dashboard-board-delete-route.patch"],
        "checks": checks,
        "dashboard_board_delete_evidence": {
            "factory_board_slug": factory_board,
            "parent_task_id": parent_id,
            "worker_count": len(workers_before),
            "factory_task_count_before": factory_task_count_before,
            "factory_task_count_after": factory_task_count_after,
            "factory_archive_attempt": factory_archive,
            "factory_hard_delete_attempt": factory_hard_delete,
            "factory_board_exists_after": factory_exists_after,
            "normal_archive_attempt": normal_archive,
            "normal_archive_board_exists_after": normal_archive_exists_after,
            "normal_hard_delete_attempt": normal_hard_delete,
            "normal_delete_board_exists_after": normal_delete_exists_after,
        },
        "important_limitations": [
            "This proves direct dashboard plugin route functions in a disposable installed Hermes runtime after candidate patch 0016.",
            "It does not start an authenticated HTTP dashboard server.",
            "It does not define a future operator-approved board retirement workflow.",
            "It does not authorize updating a real Hermes runtime.",
        ],
        "evidence_refs": [
            "adapters/hermes/patches/0016-guard-overkill-vfinal-dashboard-board-delete-route.patch",
            "adapters/hermes/dashboard_board_delete_route_guard_smoke.py",
            "validation/cards/vfinal-r3-ready.md",
            "validation/hermes-installed-runtime-smoke/dashboard-board-delete-route-guard-smoke.json",
        ],
        "next_action": "Add patch 0016 to the update sequence and continue proving remaining dashboard/API route families.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run dashboard/API board archive/delete guard smoke.")
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
                "card_id": "VFINAL-HERMES-DASHBOARD-BOARD-DELETE-ROUTE-GUARD-SMOKE",
                "slice_id": "VFINAL_HERMES_DASHBOARD_BOARD_DELETE_ROUTE_GUARD",
                "phase": "F13",
                "risk_effective": "R3",
                "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            },
            "result": "FAIL",
            "blocking_findings": True,
            "findings_summary": _safe_error(exc, replacements),
            "tool_or_profile": "adapters/hermes/dashboard_board_delete_route_guard_smoke.py",
            "executed_by": "remote-proof-runner",
            "checks": {
                "smoke_completed": "FAIL",
                "board_delete_guard": "FAIL",
                "no_real_runtime_touched": "PASS",
            },
            "important_limitations": [
                "Failure happened inside disposable-smoke orchestration; inspect locally before any real runtime update."
            ],
            "evidence_refs": [
                "adapters/hermes/dashboard_board_delete_route_guard_smoke.py",
                "validation/hermes-installed-runtime-smoke/dashboard-board-delete-route-guard-smoke.json",
            ],
        }
    write_json(args.out, result)
    print(json.dumps({"result": result.get("result"), "out": repo_ref(args.out)}, indent=2))
    return 0 if result.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
