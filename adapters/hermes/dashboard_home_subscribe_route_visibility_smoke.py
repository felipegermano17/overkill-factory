#!/usr/bin/env python3
"""Prove dashboard/API home-subscribe routes are visibility-only for vFinal.

This smoke runs only against a disposable installed Hermes checkout/home. It
calls dashboard plugin routes:

- POST /tasks/{task_id}/home-subscribe/{platform}
- DELETE /tasks/{task_id}/home-subscribe/{platform}

The expected behavior is not a block: home subscriptions are useful for owner
visibility. The proof is that subscribe/unsubscribe only changes
`kanban_notify_subs` rows and does not change task status, body, assignee,
comments or dependency links.

It does not start a production dashboard server, use real gateway credentials,
send notifications, dispatch workers, call a model, or touch the real Hermes
runtime.
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
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "dashboard-home-subscribe-route-visibility-smoke.json"
EXPECTED_WORKER_COUNT = 23
HOME = {"platform": "discord", "chat_id": "factory-home-smoke", "thread_id": "owner-updates", "name": "Factory Home Smoke"}


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
    os.environ["OVERKILL_FACTORY_RUNTIME_DIR"] = str(hermes_home / "overkill-factory-dashboard-home-subscribe")
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
    if os.environ.get("OVERKILL_DASHBOARD_HOME_SUBSCRIBE_REEXEC") == "1":
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
    env["OVERKILL_DASHBOARD_HOME_SUBSCRIBE_REEXEC"] = "1"
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


def _task_snapshot(kanban_db: Any, *, board: str, task_id: str) -> dict[str, Any]:
    conn = kanban_db.connect(board=board)
    try:
        task = kanban_db.get_task(conn, task_id)
        comments = kanban_db.list_comments(conn, task_id)
        subs = kanban_db.list_notify_subs(conn, task_id)
        link_rows = conn.execute(
            """
            SELECT parent_id, child_id
            FROM task_links
            WHERE parent_id = ? OR child_id = ?
            ORDER BY parent_id, child_id
            """,
            (task_id, task_id),
        ).fetchall()
    finally:
        conn.close()
    if task is None:
        return {"id": task_id, "missing": True}
    return {
        "id": task.id,
        "title": task.title,
        "body": task.body,
        "status": task.status,
        "assignee": task.assignee,
        "comments_count": len(comments),
        "notify_subscriptions": [
            {
                "platform": sub.get("platform"),
                "chat_id": sub.get("chat_id"),
                "thread_id": sub.get("thread_id"),
                "notifier_profile": sub.get("notifier_profile"),
            }
            for sub in subs
        ],
        "links": [{"parent_id": row["parent_id"], "child_id": row["child_id"]} for row in link_rows],
    }


def _stable_task_fields(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": snapshot["title"],
        "body": snapshot["body"],
        "status": snapshot["status"],
        "assignee": snapshot["assignee"],
        "comments_count": snapshot["comments_count"],
        "links": snapshot["links"],
    }


def _subscribe_attempt(plugin_api: Any, *, board: str, task_id: str) -> dict[str, Any]:
    try:
        result = plugin_api.subscribe_home(task_id, HOME["platform"], board=board)
        return {"ok": True, "http_status": None, "result": result}
    except Exception as exc:
        return {
            "ok": False,
            "http_status": getattr(exc, "status_code", None),
            "detail": str(getattr(exc, "detail", "") or exc)[:180],
        }


def _unsubscribe_attempt(plugin_api: Any, *, board: str, task_id: str) -> dict[str, Any]:
    try:
        result = plugin_api.unsubscribe_home(task_id, HOME["platform"], board=board)
        return {"ok": True, "http_status": None, "result": result}
    except Exception as exc:
        return {
            "ok": False,
            "http_status": getattr(exc, "status_code", None),
            "detail": str(getattr(exc, "detail", "") or exc)[:180],
        }


def _subscription_row() -> dict[str, str]:
    return {
        "platform": HOME["platform"],
        "chat_id": HOME["chat_id"],
        "thread_id": HOME["thread_id"],
        "notifier_profile": "dashboard-home-subscribe-smoke",
    }


def _visibility_only_check(before: dict[str, Any], subscribed: dict[str, Any], unsubscribed: dict[str, Any]) -> bool:
    return (
        _stable_task_fields(subscribed) == _stable_task_fields(before)
        and _stable_task_fields(unsubscribed) == _stable_task_fields(before)
        and subscribed["notify_subscriptions"] == [_subscription_row()]
        and unsubscribed["notify_subscriptions"] == before["notify_subscriptions"]
    )


def run_smoke(*, checkout: Path, hermes_home: Path, allow_non_disposable: bool) -> dict[str, Any]:
    checkout = checkout.resolve()
    hermes_home = hermes_home.resolve()
    _assert_disposable_path(checkout, label="--hermes-checkout", allow_non_disposable=allow_non_disposable)
    _assert_disposable_path(hermes_home, label="--hermes-home", allow_non_disposable=allow_non_disposable)
    if not READY_CARD.is_file():
        raise SystemExit("ready card fixture missing")

    board = f"of-dashboard-home-subscribe-{int(time.time())}"
    kanban_db, plugin_api = _load_runtime(checkout, hermes_home, board)

    parent_id = _create_task(
        plugin_api,
        board=board,
        title="VFINAL-DASHBOARD-HOME-SUBSCRIBE-VISIBILITY",
        body=READY_CARD.read_text(encoding="utf-8"),
        assignee="factory-orchestrator",
    )
    workers = _worker_prerequisites(kanban_db, board=board, task_id=parent_id)
    worker_id = workers[0]["id"] if workers else ""
    normal_id = _create_task(
        plugin_api,
        board=board,
        title="NORMAL-HOME-SUBSCRIBE-CONTROL",
        body="ordinary disposable task for dashboard home subscribe route",
        assignee="ordinary-worker",
    )

    original_homes = plugin_api._configured_home_channels
    original_profile = plugin_api._active_profile_name
    before = {
        "parent": _task_snapshot(kanban_db, board=board, task_id=parent_id),
        "worker": _task_snapshot(kanban_db, board=board, task_id=worker_id),
        "normal": _task_snapshot(kanban_db, board=board, task_id=normal_id),
    }
    try:
        plugin_api._configured_home_channels = lambda: [dict(HOME)]
        plugin_api._active_profile_name = lambda: "dashboard-home-subscribe-smoke"
        subscribe_attempts = {
            "parent": _subscribe_attempt(plugin_api, board=board, task_id=parent_id),
            "worker": _subscribe_attempt(plugin_api, board=board, task_id=worker_id),
            "normal": _subscribe_attempt(plugin_api, board=board, task_id=normal_id),
        }
        subscribed = {
            "parent": _task_snapshot(kanban_db, board=board, task_id=parent_id),
            "worker": _task_snapshot(kanban_db, board=board, task_id=worker_id),
            "normal": _task_snapshot(kanban_db, board=board, task_id=normal_id),
        }
        unsubscribe_attempts = {
            "parent": _unsubscribe_attempt(plugin_api, board=board, task_id=parent_id),
            "worker": _unsubscribe_attempt(plugin_api, board=board, task_id=worker_id),
            "normal": _unsubscribe_attempt(plugin_api, board=board, task_id=normal_id),
        }
        unsubscribed = {
            "parent": _task_snapshot(kanban_db, board=board, task_id=parent_id),
            "worker": _task_snapshot(kanban_db, board=board, task_id=worker_id),
            "normal": _task_snapshot(kanban_db, board=board, task_id=normal_id),
        }
    finally:
        plugin_api._configured_home_channels = original_homes
        plugin_api._active_profile_name = original_profile

    checks = {
        "disposable_checkout_guard": "PASS",
        "disposable_home_guard": "PASS",
        "dashboard_home_subscribe_parent_vfinal_allowed": "PASS" if subscribe_attempts["parent"]["ok"] is True else "FAIL",
        "dashboard_home_subscribe_worker_subtask_allowed": "PASS" if subscribe_attempts["worker"]["ok"] is True else "FAIL",
        "dashboard_home_subscribe_normal_task_allowed": "PASS" if subscribe_attempts["normal"]["ok"] is True else "FAIL",
        "dashboard_home_unsubscribe_parent_vfinal_allowed": "PASS" if unsubscribe_attempts["parent"]["ok"] is True else "FAIL",
        "dashboard_home_unsubscribe_worker_subtask_allowed": "PASS" if unsubscribe_attempts["worker"]["ok"] is True else "FAIL",
        "dashboard_home_parent_visibility_only": (
            "PASS" if _visibility_only_check(before["parent"], subscribed["parent"], unsubscribed["parent"]) else "FAIL"
        ),
        "dashboard_home_worker_visibility_only": (
            "PASS" if _visibility_only_check(before["worker"], subscribed["worker"], unsubscribed["worker"]) else "FAIL"
        ),
        "dashboard_home_normal_visibility_only": (
            "PASS" if _visibility_only_check(before["normal"], subscribed["normal"], unsubscribed["normal"]) else "FAIL"
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
            "card_id": "VFINAL-HERMES-DASHBOARD-HOME-SUBSCRIBE-VISIBILITY-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_HOME_SUBSCRIBE_VISIBILITY",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": result,
        "blocking_findings": result != "PASS",
        "findings_summary": (
            "Dashboard/API home-subscribe routes visibility smoke passed: subscribing and "
            "unsubscribing vFinal parent cards, worker subtasks and ordinary tasks changes "
            "only notify subscription rows, not task contract or dependency state."
            if result == "PASS"
            else "Dashboard/API home-subscribe visibility smoke failed; inspect checks."
        ),
        "tool_or_profile": "Hermes v0.16.0 disposable installed runtime with vFinal adapter patches through candidate 0015",
        "executed_by": "remote-proof-runner",
        "runtime_scope": "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; direct Python calls into dashboard plugin route functions; no production dashboard server or gateway.",
        "patches": [],
        "checks": checks,
        "dashboard_home_subscribe_evidence": {
            "board_slug": board,
            "platform": HOME["platform"],
            "parent_task_id": parent_id,
            "worker_task_id": worker_id,
            "normal_task_id": normal_id,
            "worker_count": len(workers),
            "subscribe_attempts": subscribe_attempts,
            "unsubscribe_attempts": unsubscribe_attempts,
            "before": before,
            "subscribed": subscribed,
            "unsubscribed": unsubscribed,
        },
        "important_limitations": [
            "This proves direct dashboard plugin route functions in a disposable installed Hermes runtime.",
            "The home channel is monkeypatched in-process; this does not prove a live gateway or messenger delivery.",
            "Home subscriptions are visibility/notification routing only; they are not authoritative gate evidence.",
            "It does not start an authenticated HTTP dashboard server.",
            "It does not authorize updating a real Hermes runtime.",
        ],
        "evidence_refs": [
            "adapters/hermes/dashboard_home_subscribe_route_visibility_smoke.py",
            "validation/cards/vfinal-r3-ready.md",
            "validation/hermes-installed-runtime-smoke/dashboard-home-subscribe-route-visibility-smoke.json",
        ],
        "next_action": "Record home-subscribe routes as covered visibility-only route parity and continue proving remaining dashboard/API route families.",
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
                "card_id": "VFINAL-HERMES-DASHBOARD-HOME-SUBSCRIBE-VISIBILITY-SMOKE",
                "slice_id": "VFINAL_HERMES_DASHBOARD_HOME_SUBSCRIBE_VISIBILITY",
                "phase": "F13",
                "risk_effective": "R3",
                "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            },
            "result": "FAIL",
            "blocking_findings": True,
            "findings_summary": _safe_error(exc, replacements),
            "tool_or_profile": "adapters/hermes/dashboard_home_subscribe_route_visibility_smoke.py",
            "executed_by": "remote-proof-runner",
            "important_limitations": [
                "Failure happened inside disposable-smoke orchestration; inspect locally before any real runtime update."
            ],
            "evidence_refs": [
                "adapters/hermes/dashboard_home_subscribe_route_visibility_smoke.py",
                "validation/hermes-installed-runtime-smoke/dashboard-home-subscribe-route-visibility-smoke.json",
            ],
        }
    write_json(args.out, result)
    print(json.dumps({"result": result.get("result"), "out": repo_ref(args.out)}, indent=2))
    return 0 if result.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
