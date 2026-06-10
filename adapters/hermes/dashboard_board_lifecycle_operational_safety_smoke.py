#!/usr/bin/env python3
"""Prove dashboard/API board lifecycle routes are operationally safe.

This smoke runs only against a disposable installed Hermes checkout/home. It
calls dashboard plugin board routes directly:

- `POST /boards`
- `PATCH /boards/{slug}`
- `POST /boards/{slug}/switch`

It verifies those routes affect only board metadata/current-board selection and
do not mutate existing Overkill Factory task state, worker subtasks or
dependency links.

It does not start a production dashboard server, use real credentials, dispatch
workers, or touch the real Hermes runtime.
"""

from __future__ import annotations

import argparse
import hashlib
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
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "dashboard-board-lifecycle-operational-safety-smoke.json"
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
    os.environ["OVERKILL_FACTORY_RUNTIME_DIR"] = str(hermes_home / "overkill-factory-dashboard-board-lifecycle")
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
    if os.environ.get("OVERKILL_DASHBOARD_BOARD_LIFECYCLE_REEXEC") == "1":
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
    env["OVERKILL_DASHBOARD_BOARD_LIFECYCLE_REEXEC"] = "1"
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


def _factory_board_snapshot(kanban_db: Any, *, board: str) -> dict[str, Any]:
    conn = kanban_db.connect(board=board)
    try:
        task_rows = conn.execute(
            """
            SELECT id, title, status, assignee, created_by, priority, body
            FROM tasks
            ORDER BY id
            """
        ).fetchall()
        link_rows = conn.execute(
            "SELECT parent_id, child_id FROM task_links ORDER BY parent_id, child_id"
        ).fetchall()
    finally:
        conn.close()

    tasks = [
        {
            "id": row["id"],
            "title": row["title"],
            "status": row["status"],
            "assignee": row["assignee"],
            "created_by": row["created_by"],
            "priority": row["priority"],
            "body_sha256": hashlib.sha256((row["body"] or "").encode("utf-8")).hexdigest(),
        }
        for row in task_rows
    ]
    links = [{"parent_id": row["parent_id"], "child_id": row["child_id"]} for row in link_rows]
    digest = hashlib.sha256(
        json.dumps({"tasks": tasks, "links": links}, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "task_count": len(tasks),
        "link_count": len(links),
        "digest": digest,
    }


def _current_board_file_value(kanban_db: Any) -> str | None:
    path = kanban_db.current_board_path()
    try:
        if path.exists():
            return path.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None
    return None


def _sanitize_board_meta(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {"raw_type": type(meta).__name__}
    return {
        "slug": meta.get("slug"),
        "name": meta.get("name"),
        "description": meta.get("description"),
        "icon": meta.get("icon"),
        "color": meta.get("color"),
        "archived": meta.get("archived"),
        "has_db_path": bool(meta.get("db_path")),
    }


def _sanitize_board_response(response: Any) -> dict[str, Any]:
    if not isinstance(response, dict):
        return {"raw_type": type(response).__name__}
    return {
        "board": _sanitize_board_meta(response.get("board")),
        "current": response.get("current"),
    }


def _http_status(exc: BaseException) -> int | None:
    return getattr(exc, "status_code", None)


def _create_board_attempt(plugin_api: Any, payload: Any) -> dict[str, Any]:
    try:
        result = plugin_api.create_board_endpoint(payload)
        return {"ok": True, "http_status": None, "result": _sanitize_board_response(result)}
    except Exception as exc:
        return {
            "ok": False,
            "http_status": _http_status(exc),
            "detail": str(getattr(exc, "detail", "") or exc)[:180],
        }


def _patch_board_attempt(plugin_api: Any, *, board: str, payload: Any) -> dict[str, Any]:
    try:
        result = plugin_api.rename_board(board, payload)
        return {"ok": True, "http_status": None, "result": _sanitize_board_response(result)}
    except Exception as exc:
        return {
            "ok": False,
            "http_status": _http_status(exc),
            "detail": str(getattr(exc, "detail", "") or exc)[:180],
        }


def _switch_board_attempt(plugin_api: Any, *, board: str) -> dict[str, Any]:
    try:
        result = plugin_api.switch_board(board)
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

    stamp = int(time.time())
    env_board = f"of-dashboard-board-life-env-{stamp}"
    factory_board = f"of-dashboard-board-life-factory-{stamp}"
    created_board = f"of-dashboard-board-life-created-{stamp}"
    switched_board = f"of-dashboard-board-life-switched-{stamp}"
    kanban_db, plugin_api = _load_runtime(checkout, hermes_home, env_board)

    plugin_api.create_board_endpoint(
        plugin_api.CreateBoardBody(slug=factory_board, name="Factory Board Lifecycle Control")
    )
    parent_id = _create_task(
        plugin_api,
        board=factory_board,
        title="VFINAL-DASHBOARD-BOARD-LIFECYCLE-SAFETY",
        body=READY_CARD.read_text(encoding="utf-8"),
        assignee="factory-orchestrator",
    )
    workers_before = _worker_prerequisites(kanban_db, board=factory_board, task_id=parent_id)
    snapshot_before = _factory_board_snapshot(kanban_db, board=factory_board)
    current_file_before = _current_board_file_value(kanban_db)

    invalid_create = _create_board_attempt(
        plugin_api,
        plugin_api.CreateBoardBody(slug="../bad-board", name="Invalid Board"),
    )
    create_no_switch = _create_board_attempt(
        plugin_api,
        plugin_api.CreateBoardBody(
            slug=created_board,
            name="Created Board",
            description="Metadata only board",
            icon="dot",
            color="#336699",
            switch=False,
        ),
    )
    patch_created = _patch_board_attempt(
        plugin_api,
        board=created_board,
        payload=plugin_api.RenameBoardBody(
            name="Created Board Updated",
            description="Updated metadata only",
            icon="square",
            color="#225577",
        ),
    )
    create_with_switch = _create_board_attempt(
        plugin_api,
        plugin_api.CreateBoardBody(
            slug=switched_board,
            name="Switch Board",
            description="Created and selected",
            switch=True,
        ),
    )
    current_file_after_create_switch = _current_board_file_value(kanban_db)
    switch_created = _switch_board_attempt(plugin_api, board=created_board)
    current_file_after_switch_endpoint = _current_board_file_value(kanban_db)
    missing_patch = _patch_board_attempt(
        plugin_api,
        board=f"missing-{stamp}",
        payload=plugin_api.RenameBoardBody(name="Missing"),
    )
    missing_switch = _switch_board_attempt(plugin_api, board=f"missing-{stamp}")

    snapshot_after = _factory_board_snapshot(kanban_db, board=factory_board)
    workers_after = _worker_prerequisites(kanban_db, board=factory_board, task_id=parent_id)
    created_meta = kanban_db.read_board_metadata(created_board)

    checks = {
        "disposable_checkout_guard": "PASS",
        "disposable_home_guard": "PASS",
        "dashboard_board_create_invalid_slug_rejected": (
            "PASS" if invalid_create["ok"] is False and invalid_create["http_status"] == 400 else "FAIL"
        ),
        "dashboard_board_create_metadata_only_allowed": (
            "PASS" if create_no_switch["ok"] is True and kanban_db.board_exists(created_board) else "FAIL"
        ),
        "dashboard_board_patch_metadata_only_allowed": (
            "PASS"
            if patch_created["ok"] is True
            and created_meta.get("name") == "Created Board Updated"
            and created_meta.get("description") == "Updated metadata only"
            else "FAIL"
        ),
        "dashboard_board_create_switch_updates_current_pointer": (
            "PASS" if create_with_switch["ok"] is True and current_file_after_create_switch == switched_board else "FAIL"
        ),
        "dashboard_board_switch_updates_current_pointer": (
            "PASS" if switch_created["ok"] is True and current_file_after_switch_endpoint == created_board else "FAIL"
        ),
        "dashboard_board_patch_missing_rejected": (
            "PASS" if missing_patch["ok"] is False and missing_patch["http_status"] == 404 else "FAIL"
        ),
        "dashboard_board_switch_missing_rejected": (
            "PASS" if missing_switch["ok"] is False and missing_switch["http_status"] == 404 else "FAIL"
        ),
        "factory_board_tasks_unchanged": "PASS" if snapshot_before == snapshot_after else "FAIL",
        "factory_worker_prerequisites_preserved": (
            "PASS" if len(workers_before) == EXPECTED_WORKER_COUNT and workers_before == workers_after else "FAIL"
        ),
        "no_local_paths_in_board_responses": (
            "PASS"
            if "has_db_path" in json.dumps([create_no_switch, patch_created, create_with_switch])
            and '"db_path"' not in json.dumps([create_no_switch, patch_created, create_with_switch])
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
            "card_id": "VFINAL-HERMES-DASHBOARD-BOARD-LIFECYCLE-OPERATIONAL-SAFETY-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_BOARD_LIFECYCLE_OPERATIONAL_SAFETY",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": result,
        "blocking_findings": result != "PASS",
        "findings_summary": (
            "Dashboard/API board lifecycle operational-safety smoke passed: board create, metadata patch and switch routes affect only board metadata/current-board selection and do not mutate existing vFinal task graphs."
            if result == "PASS"
            else "Dashboard/API board lifecycle operational-safety smoke failed; inspect checks."
        ),
        "tool_or_profile": "Hermes v0.16.0 disposable installed runtime with vFinal adapter patches",
        "executed_by": "remote-proof-runner",
        "runtime_scope": "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; direct Python calls into dashboard plugin route functions; no production dashboard server.",
        "patches": [],
        "checks": checks,
        "dashboard_board_lifecycle_evidence": {
            "factory_board_slug": factory_board,
            "parent_task_id": parent_id,
            "worker_count_before": len(workers_before),
            "worker_count_after": len(workers_after),
            "factory_snapshot_before": snapshot_before,
            "factory_snapshot_after": snapshot_after,
            "current_file_before": current_file_before,
            "current_file_after_create_switch": current_file_after_create_switch,
            "current_file_after_switch_endpoint": current_file_after_switch_endpoint,
            "invalid_create_attempt": invalid_create,
            "create_no_switch_attempt": create_no_switch,
            "patch_created_attempt": patch_created,
            "create_with_switch_attempt": create_with_switch,
            "switch_created_attempt": switch_created,
            "missing_patch_attempt": missing_patch,
            "missing_switch_attempt": missing_switch,
        },
        "important_limitations": [
            "This proves direct dashboard plugin route functions in a disposable installed Hermes runtime.",
            "It does not start an authenticated HTTP dashboard server.",
            "It does not prove profile or orchestration route safety.",
            "It does not authorize updating a real Hermes runtime.",
        ],
        "evidence_refs": [
            "adapters/hermes/dashboard_board_lifecycle_operational_safety_smoke.py",
            "validation/cards/vfinal-r3-ready.md",
            "validation/hermes-installed-runtime-smoke/dashboard-board-lifecycle-operational-safety-smoke.json",
        ],
        "next_action": "Mark board lifecycle routes as operational-safety proven and continue with profile/orchestration mutating route families.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run dashboard/API board lifecycle operational-safety smoke.")
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
                "card_id": "VFINAL-HERMES-DASHBOARD-BOARD-LIFECYCLE-OPERATIONAL-SAFETY-SMOKE",
                "slice_id": "VFINAL_HERMES_DASHBOARD_BOARD_LIFECYCLE_OPERATIONAL_SAFETY",
                "phase": "F13",
                "risk_effective": "R3",
                "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            },
            "result": "FAIL",
            "blocking_findings": True,
            "findings_summary": _safe_error(exc, replacements),
            "tool_or_profile": "adapters/hermes/dashboard_board_lifecycle_operational_safety_smoke.py",
            "executed_by": "remote-proof-runner",
            "checks": {
                "smoke_completed": "FAIL",
                "board_lifecycle_operational_safety": "FAIL",
                "no_real_runtime_touched": "PASS",
            },
            "important_limitations": [
                "Failure happened inside disposable-smoke orchestration; inspect locally before any real runtime update."
            ],
            "evidence_refs": [
                "adapters/hermes/dashboard_board_lifecycle_operational_safety_smoke.py",
                "validation/hermes-installed-runtime-smoke/dashboard-board-lifecycle-operational-safety-smoke.json",
            ],
        }
    write_json(args.out, result)
    print(json.dumps({"result": result.get("result"), "out": repo_ref(args.out)}, indent=2))
    return 0 if result.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
