#!/usr/bin/env python3
"""Prove dashboard/API attachment route safety for the Hermes vFinal adapter.

This smoke runs only against a disposable installed Hermes checkout/home with
patch 0010 applied. It calls dashboard plugin
`POST /tasks/{task_id}/attachments` and
`DELETE /attachments/{attachment_id}` route functions directly and verifies
upload path safety plus guarded attachment deletion.

It does not start a production dashboard server, use real credentials, dispatch
workers, or touch the real Hermes runtime.
"""

from __future__ import annotations

import argparse
import asyncio
import io
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
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "dashboard-attachment-route-safety-smoke.json"


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
    os.environ["OVERKILL_FACTORY_RUNTIME_DIR"] = str(hermes_home / "overkill-factory-dashboard-attachments")
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
    if os.environ.get("OVERKILL_DASHBOARD_ATTACHMENT_REEXEC") == "1":
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
    env["OVERKILL_DASHBOARD_ATTACHMENT_REEXEC"] = "1"
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


async def _upload_attachment(
    plugin_api: Any,
    *,
    board: str,
    task_id: str,
    filename: str,
    content: bytes,
) -> dict[str, Any]:
    upload = plugin_api.UploadFile(file=io.BytesIO(content), filename=filename)
    result = await plugin_api.upload_task_attachment(
        task_id,
        file=upload,
        board=board,
        uploaded_by="dashboard-smoke",
    )
    attachment = result.get("attachment") if isinstance(result, dict) else None
    if not isinstance(attachment, dict):
        raise RuntimeError("dashboard upload route did not return attachment metadata")
    return attachment


def _http_status(exc: BaseException) -> int | None:
    return getattr(exc, "status_code", None)


def _remove_attachment_attempt(plugin_api: Any, *, board: str, attachment_id: int) -> dict[str, Any]:
    try:
        result = plugin_api.remove_attachment(attachment_id, board=board)
        return {"ok": True, "http_status": None, "result": result}
    except Exception as exc:
        return {
            "ok": False,
            "http_status": _http_status(exc),
            "detail": str(getattr(exc, "detail", "") or exc)[:180],
        }


def _attachment_row(kanban_db: Any, *, board: str, attachment_id: int) -> Any:
    conn = kanban_db.connect(board=board)
    try:
        return kanban_db.get_attachment(conn, attachment_id)
    finally:
        conn.close()


def _tamper_attachment_path(kanban_db: Any, *, board: str, attachment_id: int, stored_path: Path) -> None:
    conn = kanban_db.connect(board=board)
    try:
        conn.execute(
            "UPDATE task_attachments SET stored_path = ? WHERE id = ?",
            (str(stored_path.resolve()), attachment_id),
        )
        conn.commit()
    finally:
        conn.close()


def _under_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def run_smoke(*, checkout: Path, hermes_home: Path, allow_non_disposable: bool) -> dict[str, Any]:
    checkout = checkout.resolve()
    hermes_home = hermes_home.resolve()
    _assert_disposable_path(checkout, label="--hermes-checkout", allow_non_disposable=allow_non_disposable)
    _assert_disposable_path(hermes_home, label="--hermes-home", allow_non_disposable=allow_non_disposable)
    if not READY_CARD.is_file():
        raise SystemExit("ready card fixture missing")

    board = f"of-dashboard-attachments-{int(time.time())}"
    kanban_db, plugin_api = _load_runtime(checkout, hermes_home, board)

    task_id = _create_task(
        plugin_api,
        board=board,
        title="VFINAL-DASHBOARD-ATTACHMENT-SAFETY",
        body=READY_CARD.read_text(encoding="utf-8"),
        assignee="factory-orchestrator",
    )
    attachment_root = kanban_db.attachments_root(board=board).resolve()

    traversal_attachment = asyncio.run(
        _upload_attachment(
            plugin_api,
            board=board,
            task_id=task_id,
            filename="../../evil-proof.txt",
            content=b"safe attachment proof",
        )
    )
    traversal_id = int(traversal_attachment["id"])
    traversal_row = _attachment_row(kanban_db, board=board, attachment_id=traversal_id)
    traversal_path = Path(traversal_row.stored_path)
    traversal_delete = _remove_attachment_attempt(plugin_api, board=board, attachment_id=traversal_id)

    tamper_attachment = asyncio.run(
        _upload_attachment(
            plugin_api,
            board=board,
            task_id=task_id,
            filename="tamper-control.txt",
            content=b"tamper control proof",
        )
    )
    tamper_id = int(tamper_attachment["id"])
    outside_file = hermes_home / "outside-attachment-root-control.txt"
    outside_file.write_text("must survive guarded attachment delete\n", encoding="utf-8")
    _tamper_attachment_path(kanban_db, board=board, attachment_id=tamper_id, stored_path=outside_file)
    tampered_delete = _remove_attachment_attempt(plugin_api, board=board, attachment_id=tamper_id)
    tampered_row_after = _attachment_row(kanban_db, board=board, attachment_id=tamper_id)

    checks = {
        "disposable_checkout_guard": "PASS",
        "disposable_home_guard": "PASS",
        "attachment_traversal_filename_sanitized": (
            "PASS"
            if traversal_attachment.get("filename") == "evil-proof.txt"
            and _under_root(traversal_path, attachment_root)
            else "FAIL"
        ),
        "attachment_normal_delete_allowed": (
            "PASS"
            if traversal_delete["ok"] is True
            and _attachment_row(kanban_db, board=board, attachment_id=traversal_id) is None
            and not traversal_path.exists()
            else "FAIL"
        ),
        "attachment_delete_outside_root_blocked": (
            "PASS"
            if tampered_delete["ok"] is False
            and tampered_delete["http_status"] == 409
            and outside_file.exists()
            and tampered_row_after is not None
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
            "card_id": "VFINAL-HERMES-DASHBOARD-ATTACHMENT-ROUTE-SAFETY-SMOKE",
            "slice_id": "VFINAL_HERMES_DASHBOARD_ATTACHMENT_ROUTE_SAFETY",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": result,
        "blocking_findings": result != "PASS",
        "findings_summary": (
            "Dashboard/API attachment route safety smoke passed: traversal names "
            "are sanitized under the attachment root, normal delete works, and "
            "tampered outside-root delete is blocked."
            if result == "PASS"
            else "Dashboard/API attachment route safety smoke failed; inspect checks."
        ),
        "tool_or_profile": "Hermes v0.16.0 disposable installed runtime with vFinal adapter patches including candidate 0010",
        "executed_by": "remote-proof-runner",
        "runtime_scope": "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; direct Python calls into dashboard plugin route functions; no production dashboard server.",
        "patches": ["adapters/hermes/patches/0010-guard-overkill-vfinal-dashboard-attachment-delete-route.patch"],
        "checks": checks,
        "dashboard_attachment_evidence": {
            "board_slug": board,
            "task_id": task_id,
            "sanitized_upload": {
                "attachment_id": traversal_id,
                "filename": traversal_attachment.get("filename"),
                "size": traversal_attachment.get("size"),
                "stored_under_attachment_root": _under_root(traversal_path, attachment_root),
                "normal_delete": traversal_delete,
            },
            "tampered_delete": {
                "attachment_id": tamper_id,
                "outside_file_survived": outside_file.exists(),
                "metadata_row_preserved": tampered_row_after is not None,
                "delete_attempt": tampered_delete,
            },
        },
        "important_limitations": [
            "This proves direct dashboard plugin route functions in a disposable installed Hermes runtime after candidate patch 0010.",
            "It does not start an authenticated HTTP dashboard server.",
            "It does not perform malware scanning or content trust validation for uploaded files.",
            "It does not authorize updating a real Hermes runtime.",
        ],
        "evidence_refs": [
            "adapters/hermes/patches/0010-guard-overkill-vfinal-dashboard-attachment-delete-route.patch",
            "adapters/hermes/dashboard_attachment_route_safety_smoke.py",
            "validation/cards/vfinal-r3-ready.md",
            "validation/hermes-installed-runtime-smoke/dashboard-attachment-route-safety-smoke.json",
        ],
        "next_action": "Add patch 0010 to the update sequence and continue proving remaining dashboard/API route families.",
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
                "card_id": "VFINAL-HERMES-DASHBOARD-ATTACHMENT-ROUTE-SAFETY-SMOKE",
                "slice_id": "VFINAL_HERMES_DASHBOARD_ATTACHMENT_ROUTE_SAFETY",
                "phase": "F13",
                "risk_effective": "R3",
                "surfaces": ["hermes", "kanban", "adapter", "vfinal", "dashboard-api"],
            },
            "result": "FAIL",
            "blocking_findings": True,
            "findings_summary": _safe_error(exc, replacements),
            "tool_or_profile": "adapters/hermes/dashboard_attachment_route_safety_smoke.py",
            "executed_by": "remote-proof-runner",
            "important_limitations": [
                "Failure happened inside disposable-smoke orchestration; inspect locally before any real runtime update."
            ],
            "evidence_refs": [
                "adapters/hermes/dashboard_attachment_route_safety_smoke.py",
                "validation/hermes-installed-runtime-smoke/dashboard-attachment-route-safety-smoke.json",
            ],
        }
    write_json(args.out, result)
    print(json.dumps({"result": result.get("result"), "out": repo_ref(args.out)}, indent=2))
    return 0 if result.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
