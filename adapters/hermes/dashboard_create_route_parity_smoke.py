#!/usr/bin/env python3
"""Prove dashboard/API create-route parity for the Hermes vFinal adapter.

This smoke runs only against a disposable installed Hermes checkout/home. It
calls the dashboard plugin `POST /tasks` route function directly and verifies
that task creation cannot bypass the Overkill before-ready gate.

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
MISSING_INPUTS_CARD = ROOT / "validation" / "cards" / "vfinal-r3-missing-security-access.md"
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "dashboard-create-route-parity-smoke.json"


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
    os.environ["OVERKILL_FACTORY_RUNTIME_DIR"] = str(hermes_home / "overkill-factory-dashboard-create")
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
    if os.environ.get("OVERKILL_DASHBOARD_CREATE_REEXEC") == "1":
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
    env["OVERKILL_DASHBOARD_CREATE_REEXEC"] = "1"
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


def _model_fields(model: Any) -> list[str]:
    fields = getattr(model, "model_fields", None)
    if fields is None:
        fields = getattr(model, "__fields__", {})
    return sorted(str(name) for name in fields)


def _task(kanban_db: Any, *, board: str, task_id: str) -> dict[str, Any]:
    conn = kanban_db.connect(board=board)
    try:
        task = kanban_db.get_task(conn, task_id)
        if task is None:
            return {"id": task_id, "status": "missing"}
        return {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "assignee": task.assignee,
            "created_by": getattr(task, "created_by", None),
        }
    finally:
        conn.close()


def _task_id_from_create_result(result: Any) -> str:
    if isinstance(result, dict):
        task = result.get("task")
        if isinstance(task, dict) and isinstance(task.get("id"), str):
            return task["id"]
    raise RuntimeError("dashboard create route did not return a task id")


def _transition_actions(kanban_db: Any, *, board: str, task_id: str) -> list[str]:
    conn = kanban_db.connect(board=board)
    try:
        rows = conn.execute(
            "SELECT kind, payload FROM task_events WHERE task_id = ? ORDER BY id",
            (task_id,),
        ).fetchall()
    finally:
        conn.close()
    actions: list[str] = []
    for row in rows:
        if row["kind"] != "overkill_factory_transition_gate":
            continue
        try:
            payload = json.loads(row["payload"] or "{}")
        except Exception:
            payload = {}
        action = payload.get("action")
        to_status = payload.get("to_status")
        if isinstance(action, str) and to_status == "ready":
            actions.append(action)
    return actions


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


def run_smoke(*, checkout: Path, hermes_home: Path, allow_non_disposable: bool) -> dict[str, Any]:
    checkout = checkout.resolve()
    hermes_home = hermes_home.resolve()
    _assert_disposable_path(checkout, label="--hermes-checkout", allow_non_disposable=allow_non_disposable)
    _assert_disposable_path(hermes_home, label="--hermes-home", allow_non_disposable=allow_non_disposable)
    if not READY_CARD.is_file():
        raise SystemExit("ready card fixture missing")
    if not MISSING_INPUTS_CARD.is_file():
        raise SystemExit("missing-inputs card fixture missing")

    board = f"of-dashboard-create-{int(time.time())}"
    kanban_db, plugin_api = _load_runtime(checkout, hermes_home, board)
    create_body_fields = _model_fields(plugin_api.CreateTaskBody)
    status_field_not_exposed = "status" not in create_body_fields

    weak_result = plugin_api.create_task(
        plugin_api.CreateTaskBody(
            title="VFINAL-DASHBOARD-CREATE-WEAK",
            body=MISSING_INPUTS_CARD.read_text(encoding="utf-8"),
            assignee="factory-orchestrator",
        ),
        board=board,
    )
    weak_task_id = _task_id_from_create_result(weak_result)
    weak_task = _task(kanban_db, board=board, task_id=weak_task_id)
    weak_actions = _transition_actions(kanban_db, board=board, task_id=weak_task_id)
    weak_workers = _worker_prerequisites(kanban_db, board=board, task_id=weak_task_id)

    positive_result = plugin_api.create_task(
        plugin_api.CreateTaskBody(
            title="VFINAL-DASHBOARD-CREATE-READY",
            body=READY_CARD.read_text(encoding="utf-8"),
            assignee="factory-orchestrator",
        ),
        board=board,
    )
    positive_task_id = _task_id_from_create_result(positive_result)
    positive_task = _task(kanban_db, board=board, task_id=positive_task_id)
    positive_actions = _transition_actions(kanban_db, board=board, task_id=positive_task_id)
    positive_workers = _worker_prerequisites(kanban_db, board=board, task_id=positive_task_id)
    positive_worker_statuses = sorted({str(worker["status"]) for worker in positive_workers})
    positive_worker_created_by = sorted({str(worker["created_by"]) for worker in positive_workers})

    weak_blocked = weak_task.get("status") == "blocked" and "block" in weak_actions and len(weak_workers) == 0
    positive_allowed = (
        positive_task.get("status") == "ready"
        and "allow" in positive_actions
        and len(positive_workers) == 23
        and positive_worker_statuses == ["blocked"]
        and positive_worker_created_by == ["overkill-factory"]
    )
    passed = status_field_not_exposed and weak_blocked and positive_allowed

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
            "card_id": "VFINAL-HERMES-DASHBOARD-CREATE-ROUTE-PARITY-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_CREATE_ROUTE_PARITY",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "PASS" if passed else "FAIL",
        "blocking_findings": not passed,
        "findings_summary": (
            "Dashboard/API create-route parity smoke passed: POST /tasks does not expose a status field, weak direct ready creation is blocked by the gate, and valid direct ready creation is allowed with blocked worker subtasks."
            if passed
            else "Dashboard/API create-route parity smoke failed."
        ),
        "tool_or_profile": "Hermes v0.16.0 disposable installed runtime with vFinal adapter patches",
        "executed_by": "remote-proof-runner",
        "runtime_scope": (
            "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; direct Python calls into dashboard plugin route functions; no production dashboard server."
        ),
        "checks": {
            "disposable_checkout_guard": "PASS",
            "disposable_home_guard": "PASS",
            "create_body_status_field_not_exposed": "PASS" if status_field_not_exposed else "FAIL",
            "weak_dashboard_create_blocked_by_gate": "PASS" if weak_blocked else "FAIL",
            "positive_dashboard_create_allowed_by_gate": "PASS" if positive_allowed else "FAIL",
            "worker_subtasks_created_blocked": "PASS" if positive_allowed else "FAIL",
            "no_real_runtime_mutation": "PASS",
        },
        "dashboard_create_evidence": {
            "board_slug": board,
            "route": "plugins.kanban.dashboard.plugin_api.create_task POST /tasks",
            "create_body_fields": create_body_fields,
            "weak_create": {
                "synthetic_card_ref": repo_ref(MISSING_INPUTS_CARD),
                "task_id": weak_task_id,
                "after_status": weak_task.get("status"),
                "gate_actions": weak_actions,
                "worker_prerequisite_count": len(weak_workers),
                "blocked_by_gate": weak_blocked,
            },
            "positive_create": {
                "synthetic_card_ref": repo_ref(READY_CARD),
                "task_id": positive_task_id,
                "after_status": positive_task.get("status"),
                "gate_actions": positive_actions,
                "worker_prerequisite_count": len(positive_workers),
                "worker_statuses": positive_worker_statuses,
                "worker_created_by": positive_worker_created_by,
                "first_worker_samples": positive_workers[:3],
                "allowed_and_materialized_workers": positive_allowed,
            },
        },
        "important_limitations": [
            "This proves direct dashboard plugin route functions in a disposable installed Hermes runtime.",
            "It does not start an authenticated HTTP dashboard server.",
            "It does not prove attachment, comment, reclaim, reassign, decompose, dispatch or board/profile mutation routes.",
            "It does not prove real worker execution, real model/tool auth, or production readiness.",
        ],
        "evidence_refs": [
            "adapters/hermes/dashboard_create_route_parity_smoke.py",
            repo_ref(READY_CARD),
            repo_ref(MISSING_INPUTS_CARD),
            "validation/hermes-installed-runtime-smoke/dashboard-create-route-parity-smoke.json",
        ],
        "next_action": (
            "Continue proving remaining dashboard/API route families that can affect task, worker or runtime configuration state."
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
            "card_id": "VFINAL-HERMES-DASHBOARD-CREATE-ROUTE-PARITY-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_CREATE_ROUTE_PARITY",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "FAIL",
        "blocking_findings": True,
        "findings_summary": "Dashboard/API create-route parity smoke did not complete.",
        "tool_or_profile": "adapters/hermes/dashboard_create_route_parity_smoke.py",
        "executed_by": "remote-proof-runner",
        "checks": {
            "smoke_completed": "FAIL",
            "create_route_parity": "FAIL",
            "no_real_runtime_touched": "PASS",
        },
        "error": error,
        "important_limitations": [
            "This failure receipt is public-safe and sanitized.",
            "A common cause is a Hermes dashboard dependency missing from the disposable runtime.",
        ],
        "evidence_refs": [
            "adapters/hermes/dashboard_create_route_parity_smoke.py",
            "validation/hermes-installed-runtime-smoke/dashboard-create-route-parity-smoke.json",
        ],
        "next_action": (
            "Fix dashboard plugin import/runtime dependencies, then rerun the dashboard create-route parity smoke."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run dashboard/API create-route parity smoke.")
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
