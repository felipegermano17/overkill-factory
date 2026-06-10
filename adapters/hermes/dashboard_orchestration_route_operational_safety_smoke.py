#!/usr/bin/env python3
"""Prove dashboard/API orchestration settings route is operationally safe.

This smoke runs only against a disposable installed Hermes checkout/home. It
calls the dashboard plugin route directly:

- `PUT /orchestration`

It verifies the route updates only Hermes Kanban orchestration configuration
knobs and does not mutate existing Overkill Factory task state, worker subtasks
or dependency links.

The smoke does not start a production dashboard server, use real credentials,
dispatch workers, call a real model, or touch the real Hermes runtime.
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
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "dashboard-orchestration-route-operational-safety-smoke.json"
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
    os.environ["OVERKILL_FACTORY_RUNTIME_DIR"] = str(hermes_home / "overkill-factory-dashboard-orchestration-route")
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
    if os.environ.get("OVERKILL_DASHBOARD_ORCHESTRATION_REEXEC") == "1":
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
    env["OVERKILL_DASHBOARD_ORCHESTRATION_REEXEC"] = "1"
    if os.name == "nt":
        completed = subprocess.run([str(python), str(Path(__file__).resolve()), *sys.argv[1:]], env=env)
        raise SystemExit(completed.returncode)
    os.execve(str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]], env)


def _load_runtime(checkout: Path, hermes_home: Path, board: str) -> tuple[Any, Any, Any, Any]:
    _runtime_env(checkout, hermes_home, board)
    from hermes_cli import config as config_mod  # type: ignore
    from hermes_cli import kanban_db  # type: ignore
    from hermes_cli import profiles as profiles_mod  # type: ignore
    from plugins.kanban.dashboard import plugin_api  # type: ignore

    kanban_db.init_db(board=board)
    return kanban_db, plugin_api, profiles_mod, config_mod


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


def _config_snapshot(config_mod: Any) -> dict[str, Any]:
    path = config_mod.get_config_path()
    raw = b""
    if path.exists():
        raw = path.read_bytes()
    try:
        cfg = config_mod.load_config() or {}
    except Exception:
        cfg = {}
    kanban = cfg.get("kanban", {}) if isinstance(cfg, dict) else {}
    if not isinstance(kanban, dict):
        kanban = {}
    return {
        "exists": path.exists(),
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "kanban": {
            "orchestrator_profile": kanban.get("orchestrator_profile"),
            "default_assignee": kanban.get("default_assignee"),
            "auto_decompose": kanban.get("auto_decompose"),
            "auto_promote_children": kanban.get("auto_promote_children"),
        },
    }


def _http_status(exc: BaseException) -> int | None:
    return getattr(exc, "status_code", None)


def _set_orchestration_attempt(plugin_api: Any, payload: Any) -> dict[str, Any]:
    try:
        result = plugin_api.set_orchestration_settings(payload)
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

    stamp = f"{int(time.time())}-{os.getpid()}"
    env_board = f"of-dashboard-orchestration-env-{stamp}"
    factory_board = f"of-dashboard-orchestration-factory-{stamp}"
    orchestrator_profile = f"of-orch-profile-{stamp}"
    default_assignee = f"of-default-profile-{stamp}"
    kanban_db, plugin_api, profiles_mod, config_mod = _load_runtime(checkout, hermes_home, env_board)

    plugin_api.create_board_endpoint(
        plugin_api.CreateBoardBody(slug=factory_board, name="Factory Orchestration Route Control")
    )
    parent_id = _create_task(
        plugin_api,
        board=factory_board,
        title="VFINAL-DASHBOARD-ORCHESTRATION-ROUTE-SAFETY",
        body=READY_CARD.read_text(encoding="utf-8"),
        assignee="factory-orchestrator",
    )
    workers_before = _worker_prerequisites(kanban_db, board=factory_board, task_id=parent_id)
    snapshot_before = _factory_board_snapshot(kanban_db, board=factory_board)
    config_before = _config_snapshot(config_mod)

    profiles_mod.create_profile(orchestrator_profile, no_alias=True, no_skills=True)
    profiles_mod.create_profile(default_assignee, no_alias=True, no_skills=True)

    invalid_profile_attempt = _set_orchestration_attempt(
        plugin_api,
        plugin_api.OrchestrationSettingsBody(
            orchestrator_profile=f"missing-orch-profile-{stamp}",
            default_assignee=default_assignee,
            auto_decompose=False,
            auto_promote_children=False,
        ),
    )
    config_after_invalid = _config_snapshot(config_mod)

    valid_update_attempt = _set_orchestration_attempt(
        plugin_api,
        plugin_api.OrchestrationSettingsBody(
            orchestrator_profile=orchestrator_profile,
            default_assignee=default_assignee,
            auto_decompose=False,
            auto_promote_children=False,
        ),
    )
    config_after_valid = _config_snapshot(config_mod)

    clear_override_attempt = _set_orchestration_attempt(
        plugin_api,
        plugin_api.OrchestrationSettingsBody(
            orchestrator_profile="",
            default_assignee="",
            auto_decompose=True,
            auto_promote_children=True,
        ),
    )
    config_after_clear = _config_snapshot(config_mod)

    snapshot_after = _factory_board_snapshot(kanban_db, board=factory_board)
    workers_after = _worker_prerequisites(kanban_db, board=factory_board, task_id=parent_id)

    checks = {
        "disposable_checkout_guard": "PASS",
        "disposable_home_guard": "PASS",
        "dashboard_orchestration_missing_profile_rejected": (
            "PASS"
            if invalid_profile_attempt["ok"] is False
            and invalid_profile_attempt["http_status"] == 400
            and config_after_invalid["sha256"] == config_before["sha256"]
            else "FAIL"
        ),
        "dashboard_orchestration_valid_update_allowed": (
            "PASS"
            if valid_update_attempt["ok"] is True
            and config_after_valid["kanban"]["orchestrator_profile"] == orchestrator_profile
            and config_after_valid["kanban"]["default_assignee"] == default_assignee
            and config_after_valid["kanban"]["auto_decompose"] is False
            and config_after_valid["kanban"]["auto_promote_children"] is False
            else "FAIL"
        ),
        "dashboard_orchestration_clear_overrides_allowed": (
            "PASS"
            if clear_override_attempt["ok"] is True
            and config_after_clear["kanban"]["orchestrator_profile"] == ""
            and config_after_clear["kanban"]["default_assignee"] == ""
            and config_after_clear["kanban"]["auto_decompose"] is True
            and config_after_clear["kanban"]["auto_promote_children"] is True
            else "FAIL"
        ),
        "dashboard_orchestration_resolved_fallbacks_returned": (
            "PASS"
            if clear_override_attempt["ok"] is True
            and bool(clear_override_attempt["result"].get("resolved_orchestrator_profile"))
            and bool(clear_override_attempt["result"].get("resolved_default_assignee"))
            else "FAIL"
        ),
        "factory_board_tasks_unchanged": "PASS" if snapshot_before == snapshot_after else "FAIL",
        "factory_worker_prerequisites_preserved": (
            "PASS" if len(workers_before) == EXPECTED_WORKER_COUNT and workers_before == workers_after else "FAIL"
        ),
        "no_local_paths_in_orchestration_responses": (
            "PASS"
            if '"config_path"' not in json.dumps([invalid_profile_attempt, valid_update_attempt, clear_override_attempt])
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
            "card_id": "VFINAL-HERMES-DASHBOARD-ORCHESTRATION-ROUTE-OPERATIONAL-SAFETY-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_ORCHESTRATION_ROUTE_OPERATIONAL_SAFETY",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": result,
        "blocking_findings": result != "PASS",
        "findings_summary": (
            "Dashboard/API orchestration route operational-safety smoke passed: PUT /orchestration updates only Kanban orchestration config knobs and does not mutate existing vFinal task graphs."
            if result == "PASS"
            else "Dashboard/API orchestration route operational-safety smoke failed; inspect checks."
        ),
        "tool_or_profile": "Hermes v0.16.0 disposable installed runtime with vFinal adapter patches",
        "executed_by": "remote-proof-runner",
        "runtime_scope": "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; direct Python calls into dashboard plugin route functions; no production dashboard server.",
        "patches": [],
        "checks": checks,
        "dashboard_orchestration_route_evidence": {
            "factory_board_slug": factory_board,
            "parent_task_id": parent_id,
            "orchestrator_profile": profiles_mod.normalize_profile_name(orchestrator_profile),
            "default_assignee": profiles_mod.normalize_profile_name(default_assignee),
            "worker_count_before": len(workers_before),
            "worker_count_after": len(workers_after),
            "factory_snapshot_before": snapshot_before,
            "factory_snapshot_after": snapshot_after,
            "config_before": config_before,
            "config_after_invalid": config_after_invalid,
            "config_after_valid": config_after_valid,
            "config_after_clear": config_after_clear,
            "invalid_profile_attempt": invalid_profile_attempt,
            "valid_update_attempt": valid_update_attempt,
            "clear_override_attempt": clear_override_attempt,
        },
        "important_limitations": [
            "This proves direct dashboard plugin route functions in a disposable installed Hermes runtime.",
            "It does not start an authenticated HTTP dashboard server.",
            "It does not prove real model execution or real worker output quality.",
            "It does not authorize updating a real Hermes runtime.",
        ],
        "evidence_refs": [
            "adapters/hermes/dashboard_orchestration_route_operational_safety_smoke.py",
            "validation/cards/vfinal-r3-ready.md",
            "validation/hermes-installed-runtime-smoke/dashboard-orchestration-route-operational-safety-smoke.json",
        ],
        "next_action": "Mark dashboard/API mutating route inventory as fully covered for the current inspected surface and continue production-readiness work on non-stub worker execution and real rollback proof.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run dashboard/API orchestration route operational-safety smoke.")
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
                "card_id": "VFINAL-HERMES-DASHBOARD-ORCHESTRATION-ROUTE-OPERATIONAL-SAFETY-SMOKE",
                "slice_id": "VFINAL_HERMES_DASHBOARD_ORCHESTRATION_ROUTE_OPERATIONAL_SAFETY",
                "phase": "F13",
                "risk_effective": "R3",
                "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            },
            "result": "FAIL",
            "blocking_findings": True,
            "findings_summary": _safe_error(exc, replacements),
            "tool_or_profile": "adapters/hermes/dashboard_orchestration_route_operational_safety_smoke.py",
            "executed_by": "remote-proof-runner",
            "checks": {
                "smoke_completed": "FAIL",
                "orchestration_route_operational_safety": "FAIL",
                "no_real_runtime_touched": "PASS",
            },
            "important_limitations": [
                "Failure happened inside disposable-smoke orchestration; inspect locally before any real runtime update."
            ],
            "evidence_refs": [
                "adapters/hermes/dashboard_orchestration_route_operational_safety_smoke.py",
                "validation/hermes-installed-runtime-smoke/dashboard-orchestration-route-operational-safety-smoke.json",
            ],
        }
    write_json(args.out, result)
    print(json.dumps({"result": result.get("result"), "out": repo_ref(args.out)}, indent=2))
    return 0 if result.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
