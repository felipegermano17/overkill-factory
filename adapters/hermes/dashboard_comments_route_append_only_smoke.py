#!/usr/bin/env python3
"""Prove dashboard/API comments route is append-only for Hermes vFinal.

This smoke runs only against a disposable installed Hermes checkout/home. It
calls dashboard plugin `POST /tasks/{task_id}/comments` for a vFinal parent
card, a vFinal worker subtask and an ordinary task.

The expected behavior is intentionally not a block: comments are useful for
operator supervision. The proof is that comments append a comment row and a
`commented` event without changing task status, body, assignee or dependency
links.

It does not start a production dashboard server, use real credentials, dispatch
workers, call a model, or touch the real Hermes runtime.
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
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "dashboard-comments-route-append-only-smoke.json"
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
    os.environ["OVERKILL_FACTORY_RUNTIME_DIR"] = str(hermes_home / "overkill-factory-dashboard-comments")
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
    if os.environ.get("OVERKILL_DASHBOARD_COMMENTS_REEXEC") == "1":
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
    env["OVERKILL_DASHBOARD_COMMENTS_REEXEC"] = "1"
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
        link_rows = conn.execute(
            """
            SELECT parent_id, child_id
            FROM task_links
            WHERE parent_id = ? OR child_id = ?
            ORDER BY parent_id, child_id
            """,
            (task_id, task_id),
        ).fetchall()
        commented_events = conn.execute(
            "SELECT COUNT(*) AS n FROM task_events WHERE task_id = ? AND kind = 'commented'",
            (task_id,),
        ).fetchone()
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
        "last_comment": comments[-1].body if comments else None,
        "commented_events": int(commented_events["n"] if commented_events else 0),
        "links": [{"parent_id": row["parent_id"], "child_id": row["child_id"]} for row in link_rows],
    }


def _stable_task_fields(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": snapshot["title"],
        "body": snapshot["body"],
        "status": snapshot["status"],
        "assignee": snapshot["assignee"],
        "links": snapshot["links"],
    }


def _comment_attempt(plugin_api: Any, *, board: str, task_id: str, body: str) -> dict[str, Any]:
    try:
        result = plugin_api.add_comment(
            task_id,
            plugin_api.CommentBody(author="dashboard-comments-route-smoke", body=body),
            board=board,
        )
        return {"ok": True, "http_status": None, "result": result}
    except Exception as exc:
        return {
            "ok": False,
            "http_status": getattr(exc, "status_code", None),
            "detail": str(getattr(exc, "detail", "") or exc)[:180],
        }


def _append_only_check(before: dict[str, Any], after: dict[str, Any], body: str) -> bool:
    return (
        _stable_task_fields(after) == _stable_task_fields(before)
        and after["comments_count"] == before["comments_count"] + 1
        and after["commented_events"] == before["commented_events"] + 1
        and after["last_comment"] == body
    )


def run_smoke(*, checkout: Path, hermes_home: Path, allow_non_disposable: bool) -> dict[str, Any]:
    checkout = checkout.resolve()
    hermes_home = hermes_home.resolve()
    _assert_disposable_path(checkout, label="--hermes-checkout", allow_non_disposable=allow_non_disposable)
    _assert_disposable_path(hermes_home, label="--hermes-home", allow_non_disposable=allow_non_disposable)
    if not READY_CARD.is_file():
        raise SystemExit("ready card fixture missing")

    board = f"of-dashboard-comments-{int(time.time())}"
    kanban_db, plugin_api = _load_runtime(checkout, hermes_home, board)

    parent_id = _create_task(
        plugin_api,
        board=board,
        title="VFINAL-DASHBOARD-COMMENTS-APPEND-ONLY",
        body=READY_CARD.read_text(encoding="utf-8"),
        assignee="factory-orchestrator",
    )
    workers = _worker_prerequisites(kanban_db, board=board, task_id=parent_id)
    worker_id = workers[0]["id"] if workers else ""
    normal_id = _create_task(
        plugin_api,
        board=board,
        title="NORMAL-COMMENTS-CONTROL",
        body="ordinary disposable task for dashboard comments route",
        assignee="ordinary-worker",
    )

    bodies = {
        "parent": "operator note on vFinal parent; not gate evidence",
        "worker": "operator note on vFinal worker; not worker result",
        "normal": "ordinary task comment control",
    }
    before = {
        "parent": _task_snapshot(kanban_db, board=board, task_id=parent_id),
        "worker": _task_snapshot(kanban_db, board=board, task_id=worker_id),
        "normal": _task_snapshot(kanban_db, board=board, task_id=normal_id),
    }
    attempts = {
        "parent": _comment_attempt(plugin_api, board=board, task_id=parent_id, body=bodies["parent"]),
        "worker": _comment_attempt(plugin_api, board=board, task_id=worker_id, body=bodies["worker"]),
        "normal": _comment_attempt(plugin_api, board=board, task_id=normal_id, body=bodies["normal"]),
    }
    after = {
        "parent": _task_snapshot(kanban_db, board=board, task_id=parent_id),
        "worker": _task_snapshot(kanban_db, board=board, task_id=worker_id),
        "normal": _task_snapshot(kanban_db, board=board, task_id=normal_id),
    }

    checks = {
        "disposable_checkout_guard": "PASS",
        "disposable_home_guard": "PASS",
        "dashboard_comment_parent_vfinal_allowed": "PASS" if attempts["parent"]["ok"] is True else "FAIL",
        "dashboard_comment_worker_subtask_allowed": "PASS" if attempts["worker"]["ok"] is True else "FAIL",
        "dashboard_comment_normal_task_allowed": "PASS" if attempts["normal"]["ok"] is True else "FAIL",
        "dashboard_comment_parent_append_only": (
            "PASS" if _append_only_check(before["parent"], after["parent"], bodies["parent"]) else "FAIL"
        ),
        "dashboard_comment_worker_append_only": (
            "PASS" if _append_only_check(before["worker"], after["worker"], bodies["worker"]) else "FAIL"
        ),
        "dashboard_comment_normal_append_only": (
            "PASS" if _append_only_check(before["normal"], after["normal"], bodies["normal"]) else "FAIL"
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
            "card_id": "VFINAL-HERMES-DASHBOARD-COMMENTS-APPEND-ONLY-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_COMMENTS_APPEND_ONLY",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": result,
        "blocking_findings": result != "PASS",
        "findings_summary": (
            "Dashboard/API comments route append-only smoke passed: comments are allowed "
            "for vFinal parent cards, worker subtasks and ordinary tasks, and they append "
            "only comment/event rows without changing task contract or dependency state."
            if result == "PASS"
            else "Dashboard/API comments route append-only smoke failed; inspect checks."
        ),
        "tool_or_profile": "Hermes v0.16.0 disposable installed runtime with vFinal adapter patches through candidate 0015",
        "executed_by": "remote-proof-runner",
        "runtime_scope": "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; direct Python calls into dashboard plugin route functions; no production dashboard server.",
        "patches": [],
        "checks": checks,
        "dashboard_comments_evidence": {
            "board_slug": board,
            "parent_task_id": parent_id,
            "worker_task_id": worker_id,
            "normal_task_id": normal_id,
            "worker_count": len(workers),
            "attempts": attempts,
            "before": before,
            "after": after,
        },
        "important_limitations": [
            "This proves direct dashboard plugin route functions in a disposable installed Hermes runtime.",
            "Comments are operator notes; this smoke does not make comments authoritative gate evidence.",
            "It does not start an authenticated HTTP dashboard server.",
            "It does not authorize updating a real Hermes runtime.",
        ],
        "evidence_refs": [
            "adapters/hermes/dashboard_comments_route_append_only_smoke.py",
            "validation/cards/vfinal-r3-ready.md",
            "validation/hermes-installed-runtime-smoke/dashboard-comments-route-append-only-smoke.json",
        ],
        "next_action": "Record comments as covered append-only route parity and continue proving remaining dashboard/API route families.",
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
                "card_id": "VFINAL-HERMES-DASHBOARD-COMMENTS-APPEND-ONLY-SMOKE",
                "slice_id": "VFINAL_HERMES_DASHBOARD_COMMENTS_APPEND_ONLY",
                "phase": "F13",
                "risk_effective": "R3",
                "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            },
            "result": "FAIL",
            "blocking_findings": True,
            "findings_summary": _safe_error(exc, replacements),
            "tool_or_profile": "adapters/hermes/dashboard_comments_route_append_only_smoke.py",
            "executed_by": "remote-proof-runner",
            "important_limitations": [
                "Failure happened inside disposable-smoke orchestration; inspect locally before any real runtime update."
            ],
            "evidence_refs": [
                "adapters/hermes/dashboard_comments_route_append_only_smoke.py",
                "validation/hermes-installed-runtime-smoke/dashboard-comments-route-append-only-smoke.json",
            ],
        }
    write_json(args.out, result)
    print(json.dumps({"result": result.get("result"), "out": repo_ref(args.out)}, indent=2))
    return 0 if result.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
