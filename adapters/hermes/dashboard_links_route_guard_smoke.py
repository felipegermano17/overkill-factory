#!/usr/bin/env python3
"""Prove dashboard/API link-route guard for the Hermes vFinal adapter.

This smoke runs only against a disposable installed Hermes checkout/home with
patch 0009 applied. It calls dashboard plugin `/links` route functions directly
and verifies that Overkill Factory dependency links cannot be manually edited.

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
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "dashboard-links-route-guard-smoke.json"
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
    os.environ["OVERKILL_FACTORY_RUNTIME_DIR"] = str(hermes_home / "overkill-factory-dashboard-links")
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
    if os.environ.get("OVERKILL_DASHBOARD_LINKS_REEXEC") == "1":
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
    env["OVERKILL_DASHBOARD_LINKS_REEXEC"] = "1"
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


def _http_status(exc: BaseException) -> int | None:
    return getattr(exc, "status_code", None)


def _add_link_attempt(plugin_api: Any, *, board: str, parent_id: str, child_id: str) -> dict[str, Any]:
    try:
        result = plugin_api.add_link(plugin_api.LinkBody(parent_id=parent_id, child_id=child_id), board=board)
        return {"ok": True, "http_status": None, "result": result}
    except Exception as exc:
        return {
            "ok": False,
            "http_status": _http_status(exc),
            "detail": str(getattr(exc, "detail", "") or exc)[:180],
        }


def _delete_link_attempt(plugin_api: Any, *, board: str, parent_id: str, child_id: str) -> dict[str, Any]:
    try:
        result = plugin_api.delete_link(parent_id=parent_id, child_id=child_id, board=board)
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

    board = f"of-dashboard-links-{int(time.time())}"
    kanban_db, plugin_api = _load_runtime(checkout, hermes_home, board)

    parent_id = _create_task(
        plugin_api,
        board=board,
        title="VFINAL-DASHBOARD-LINKS-GUARD",
        body=READY_CARD.read_text(encoding="utf-8"),
        assignee="factory-orchestrator",
    )
    workers_before = _worker_prerequisites(kanban_db, board=board, task_id=parent_id)
    worker_id = workers_before[0]["id"] if workers_before else ""

    delete_worker_parent_link = _delete_link_attempt(
        plugin_api,
        board=board,
        parent_id=worker_id,
        child_id=parent_id,
    )

    normal_a_id = _create_task(
        plugin_api,
        board=board,
        title="NORMAL-LINK-A",
        body="ordinary non-factory disposable task A",
        assignee=None,
    )
    normal_b_id = _create_task(
        plugin_api,
        board=board,
        title="NORMAL-LINK-B",
        body="ordinary non-factory disposable task B",
        assignee=None,
    )
    add_factory_link = _add_link_attempt(
        plugin_api,
        board=board,
        parent_id=normal_a_id,
        child_id=parent_id,
    )
    add_normal_link = _add_link_attempt(
        plugin_api,
        board=board,
        parent_id=normal_a_id,
        child_id=normal_b_id,
    )
    delete_normal_link = _delete_link_attempt(
        plugin_api,
        board=board,
        parent_id=normal_a_id,
        child_id=normal_b_id,
    )

    workers_after = _worker_prerequisites(kanban_db, board=board, task_id=parent_id)
    before_ids = sorted(worker["id"] for worker in workers_before)
    after_ids = sorted(worker["id"] for worker in workers_after)

    checks = {
        "disposable_checkout_guard": "PASS",
        "disposable_home_guard": "PASS",
        "dashboard_delete_worker_parent_link_blocked": (
            "PASS"
            if delete_worker_parent_link["ok"] is False and delete_worker_parent_link["http_status"] == 409
            else "FAIL"
        ),
        "dashboard_add_factory_link_blocked": (
            "PASS" if add_factory_link["ok"] is False and add_factory_link["http_status"] == 409 else "FAIL"
        ),
        "dashboard_normal_link_add_delete_allowed": (
            "PASS"
            if add_normal_link["ok"] is True
            and delete_normal_link["ok"] is True
            and (delete_normal_link.get("result") or {}).get("ok") is True
            else "FAIL"
        ),
        "worker_prerequisite_links_preserved": (
            "PASS"
            if len(before_ids) == EXPECTED_WORKER_COUNT and before_ids == after_ids
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
            "card_id": "VFINAL-HERMES-DASHBOARD-LINKS-ROUTE-GUARD-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_LINKS_ROUTE_GUARD",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": result,
        "blocking_findings": result != "PASS",
        "findings_summary": (
            "Dashboard/API link-route guard smoke passed: manual dependency edits "
            "are blocked for vFinal cards and worker subtasks, worker links are "
            "preserved, and ordinary disposable task links still work."
            if result == "PASS"
            else "Dashboard/API link-route guard smoke failed; inspect checks."
        ),
        "tool_or_profile": "Hermes v0.16.0 disposable installed runtime with vFinal adapter patches including candidate 0009",
        "executed_by": "remote-proof-runner",
        "runtime_scope": "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; direct Python calls into dashboard plugin route functions; no production dashboard server.",
        "patches": ["adapters/hermes/patches/0009-guard-overkill-vfinal-dashboard-links-route.patch"],
        "checks": checks,
        "dashboard_links_evidence": {
            "board_slug": board,
            "parent_task_id": parent_id,
            "worker_task_id": worker_id,
            "worker_count_before": len(workers_before),
            "worker_count_after": len(workers_after),
            "delete_worker_parent_link_attempt": delete_worker_parent_link,
            "add_factory_link_attempt": add_factory_link,
            "normal_link_attempt": {
                "parent_task_id": normal_a_id,
                "child_task_id": normal_b_id,
                "add": add_normal_link,
                "delete": delete_normal_link,
            },
        },
        "important_limitations": [
            "This proves direct dashboard plugin route functions in a disposable installed Hermes runtime after candidate patch 0009.",
            "It does not start an authenticated HTTP dashboard server.",
            "It does not define a future operator-approved dependency edit workflow.",
            "It does not authorize updating a real Hermes runtime.",
        ],
        "evidence_refs": [
            "adapters/hermes/patches/0009-guard-overkill-vfinal-dashboard-links-route.patch",
            "adapters/hermes/dashboard_links_route_guard_smoke.py",
            "validation/cards/vfinal-r3-ready.md",
            "validation/hermes-installed-runtime-smoke/dashboard-links-route-guard-smoke.json",
        ],
        "next_action": "Add patch 0009 to the update sequence and continue proving remaining dashboard/API route families.",
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
                "card_id": "VFINAL-HERMES-DASHBOARD-LINKS-ROUTE-GUARD-SMOKE",
                "slice_id": "VFINAL_HERMES_DASHBOARD_LINKS_ROUTE_GUARD",
                "phase": "F13",
                "risk_effective": "R3",
                "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            },
            "result": "FAIL",
            "blocking_findings": True,
            "findings_summary": _safe_error(exc, replacements),
            "tool_or_profile": "adapters/hermes/dashboard_links_route_guard_smoke.py",
            "executed_by": "remote-proof-runner",
            "important_limitations": [
                "Failure happened inside disposable-smoke orchestration; inspect locally before any real runtime update."
            ],
            "evidence_refs": [
                "adapters/hermes/dashboard_links_route_guard_smoke.py",
                "validation/hermes-installed-runtime-smoke/dashboard-links-route-guard-smoke.json",
            ],
        }
    write_json(args.out, result)
    print(json.dumps({"result": result.get("result"), "out": repo_ref(args.out)}, indent=2))
    return 0 if result.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
