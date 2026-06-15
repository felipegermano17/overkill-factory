#!/usr/bin/env python3
"""Materialize Overkill Factory worker gates in a real Hermes Kanban board."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any, Callable

from transition_hook import ACTION_BLOCK_TRANSITION, build_hook_result, write_json


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from public_refs import (  # noqa: E402
    PRIVATE_KANBAN_TASK_MARKER_RE,
    PUBLIC_SAFE_KANBAN_REF,
    sanitize_public_refs,
)

TASK_ID_RE = PRIVATE_KANBAN_TASK_MARKER_RE
LIVE_ADAPTER_SCHEMA = "https://overkill-factory.dev/schemas/hermes-live-adapter-result.schema.json"
ROUTE_READINESS_SCHEMA = "https://overkill-factory.dev/schemas/hermes-worker-route-readiness.schema.json"
Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def default_runner(argv: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("HOME", str(Path.home()))
    return subprocess.run(argv, text=True, capture_output=True, env=env)  # nosec B603


def run_checked(argv: list[str], runner: Runner = default_runner) -> subprocess.CompletedProcess[str]:
    completed = runner(argv)
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed: "
            + " ".join(argv)
            + "\nstdout:\n"
            + (completed.stdout or "")
            + "\nstderr:\n"
            + (completed.stderr or "")
        )
    return completed


def parse_json_output(output: str, *, command: str) -> Any:
    try:
        return json.loads(output or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{command} did not return JSON") from exc


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_task_id(output: str) -> str:
    text = (output or "").strip()
    if text:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            for key in ("id", "task_id"):
                value = data.get(key)
                if isinstance(value, str) and value:
                    return value
        match = TASK_ID_RE.search(text)
        if match:
            return match.group(0)
    raise RuntimeError(f"could not parse Hermes task id from output: {text!r}")


def hermes_kanban(hermes_bin: str, board: str, *args: str) -> list[str]:
    return [hermes_bin, "kanban", "--board", board, *args]


def public_safe_workspace_ref(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    normalized = text.replace("\\", "/")
    if normalized.lower().startswith("dir:"):
        normalized = normalized[4:]
    if re.match(r"^[A-Za-z]:/", normalized) or normalized.startswith("/"):
        return "redacted:absolute-hermes-workspace"
    return text


def normalize_task_record(record: dict[str, Any]) -> dict[str, Any]:
    task_id = str(record.get("task_id") or record.get("id") or "")
    normalized: dict[str, Any] = {"task_id": task_id}
    assignee = record.get("assignee") or record.get("profile")
    if assignee:
        normalized["assignee"] = str(assignee)
    workspace = record.get("workspace") or record.get("workspace_path")
    if workspace:
        normalized["workspace"] = public_safe_workspace_ref(workspace)
    for source_key, target_key in (
        ("current_run_id", "run_id"),
        ("run_id", "run_id"),
        ("worker_pid", "worker_pid"),
        ("pid", "worker_pid"),
    ):
        value = record.get(source_key)
        if value is not None and target_key not in normalized:
            normalized[target_key] = value
    return normalized


def list_tasks_by_status(
    *,
    hermes_bin: str,
    board: str,
    status: str,
    runner: Runner = default_runner,
) -> list[dict[str, Any]]:
    completed = run_checked(hermes_kanban(hermes_bin, board, "list", "--status", status, "--json"), runner)
    payload = parse_json_output(completed.stdout, command=f"hermes kanban list --status {status} --json")
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("tasks", "items", status):
            items = payload.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
    return []


def show_task(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    runner: Runner = default_runner,
) -> dict[str, Any]:
    completed = run_checked(hermes_kanban(hermes_bin, board, "show", task_id, "--json"), runner)
    payload = parse_json_output(completed.stdout, command="hermes kanban show --json")
    return payload if isinstance(payload, dict) else {}


def enrich_dispatch_task(
    *,
    hermes_bin: str,
    board: str,
    record: dict[str, Any],
    after_running_by_id: dict[str, dict[str, Any]],
    runner: Runner = default_runner,
) -> dict[str, Any]:
    task_id = str(record.get("task_id") or record.get("id") or "")
    merged: dict[str, Any] = {}
    if task_id:
        merged.update(after_running_by_id.get(task_id) or {})
    merged.update(record)
    normalized = normalize_task_record(merged)
    if task_id and ("run_id" not in normalized or "worker_pid" not in normalized):
        shown = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
        shown_normalized = normalize_task_record(shown)
        for key in ("run_id", "worker_pid", "assignee", "workspace"):
            if key not in normalized and key in shown_normalized:
                normalized[key] = shown_normalized[key]
    return normalized


def normalize_native_spawned(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("spawned")
    if not isinstance(records, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in records:
        if isinstance(item, dict):
            record = normalize_task_record(item)
            if record.get("task_id"):
                normalized.append(record)
    return normalized


def route_readiness_blockers(path: Path | None, required_worker_ids: list[str]) -> list[str]:
    if path is None:
        return ["route readiness manifest is required before live Hermes dispatch"]
    data = load_json(path)
    blockers: list[str] = []
    official_manifest = data.get("$schema") == ROUTE_READINESS_SCHEMA or "checks" in data
    if official_manifest:
        if data.get("$schema") != ROUTE_READINESS_SCHEMA:
            blockers.append("route readiness manifest must declare the official hermes-worker-route-readiness schema")
        if data.get("result") != "PASS":
            blockers.append(f"route readiness result is {data.get('result')!r}, expected PASS")
        if data.get("blocked_worker_count") not in {0, None}:
            blockers.append(f"route readiness has {data.get('blocked_worker_count')} blocked worker(s)")
        for worker_id in data.get("blocked_workers") or []:
            blockers.append(f"{worker_id}: route readiness reports worker blocked")
        raw_routes = data.get("checks") or []
    else:
        raw_routes = data.get("routes") or data.get("workers") or {}
    if isinstance(raw_routes, list):
        routes = {
            str(route.get("worker_id") or route.get("worker") or ""): route
            for route in raw_routes
            if isinstance(route, dict)
        }
    elif isinstance(raw_routes, dict):
        routes = {str(worker_id): route for worker_id, route in raw_routes.items() if isinstance(route, dict)}
    else:
        routes = {}
    for worker_id in sorted(set(required_worker_ids)):
        route = routes.get(worker_id)
        if not route:
            blockers.append(f"{worker_id}: missing route readiness record")
            continue
        checks = {
            "status_ready": str(route.get("status") or "ready").strip().lower() == "ready",
            "profile_exists": route.get("profile_exists") is True,
            "provider_configured": route.get("provider_configured", route.get("provider_status")) in {True, "pass", "PASS"},
            "model_configured": route.get("model_configured", route.get("model_status")) in {True, "pass", "PASS"},
            "credential_status": str(route.get("credential_status") or "").strip().lower() == "pass",
        }
        if not official_manifest:
            checks["capability_manifest"] = route.get("capability_manifest_ok", route.get("capability_status")) in {True, "pass", "PASS"}
        if route.get("blocked_reasons"):
            checks["blocked_reasons_empty"] = False
        failed = [name for name, ok in checks.items() if not ok]
        if failed:
            blockers.append(f"{worker_id}: route readiness failed ({', '.join(failed)})")
    return blockers


def ensure_non_empty_body(body: str) -> None:
    if not str(body or "").strip():
        raise RuntimeError("Hermes task body must be non-empty before dispatch")


def task_has_blocked_event(payload: dict[str, Any]) -> bool:
    if str(payload.get("status") or "").strip().lower() == "blocked":
        events = payload.get("events") or payload.get("history") or payload.get("timeline") or []
        if isinstance(events, list):
            return any("block" in str(event).lower() for event in events)
    return False


def ensure_blocked_event(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    reason: str,
    runner: Runner = default_runner,
) -> None:
    run_checked(
        hermes_kanban(hermes_bin, board, "block", task_id, reason),
        runner,
    )
    shown = run_checked(hermes_kanban(hermes_bin, board, "show", task_id, "--json"), runner)
    try:
        payload = json.loads(shown.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("Hermes show --json did not return JSON while verifying blocked event") from exc
    if not isinstance(payload, dict) or not task_has_blocked_event(payload):
        raise RuntimeError(f"Hermes task {task_id} is not durably blocked after block command")


def unblock_task(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    reason: str,
    runner: Runner = default_runner,
) -> None:
    run_checked(hermes_kanban(hermes_bin, board, "unblock", task_id, reason), runner)


def record_live_binding(
    *,
    ledger_path: Path,
    card_id: str,
    board: str,
    main_task_id: str,
    worker_task_ids: dict[str, str],
) -> None:
    ledger = load_json(ledger_path)
    tasks = ledger.setdefault("tasks", {})
    for task in tasks.values():
        if not isinstance(task, dict):
            continue
        worker_id = str(task.get("worker_id") or "")
        hermes_task_id = worker_task_ids.get(worker_id)
        if str(task.get("card_id") or "") != card_id or not hermes_task_id:
            continue
        task["materialization_state"] = "materialized_in_hermes"
        task["runtime_refs"] = {
            "hermes_board_ref": f"hermes:{board}",
            "hermes_task_ref": hermes_task_id,
            "hermes_run_ref": "external:pending-hermes-run",
        }
        task["local_record_role"] = "idempotency_projection"
    bindings = ledger.setdefault("live_bindings", {})
    bindings[card_id] = {
        "binding_role": "hermes_ref_projection",
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "board": board,
        "main_task_id": main_task_id,
        "worker_task_ids": worker_task_ids,
    }
    write_json(ledger_path, ledger)


def validate_live_binding(*, ledger_path: Path, card_id: str, board: str, main_task_id: str) -> None:
    ledger = load_json(ledger_path)
    if ledger.get("runtime_authority") != "hermes_kanban" or ledger.get("local_state_authority") is not False:
        raise RuntimeError("ledger is not a Hermes-authoritative projection; refuse to complete arbitrary Hermes task")
    binding = (ledger.get("live_bindings") or {}).get(card_id)
    if not isinstance(binding, dict):
        raise RuntimeError(f"missing live binding for card {card_id}; refuse to complete arbitrary Hermes task")
    if binding.get("runtime_authority") != "hermes_kanban" or binding.get("local_state_authority") is not False:
        raise RuntimeError("live binding is not a Hermes-authoritative projection; refuse to complete arbitrary Hermes task")
    if binding.get("binding_role") != "hermes_ref_projection":
        raise RuntimeError("live binding must be a Hermes ref projection")
    if binding.get("board") != board or binding.get("main_task_id") != main_task_id:
        raise RuntimeError("main task id does not match the live binding for this card and board")


def ensure_board(
    *,
    hermes_bin: str,
    board: str,
    default_workdir: str | None,
    runner: Runner = default_runner,
) -> bool:
    listed = run_checked([hermes_bin, "kanban", "boards", "list", "--json"], runner)
    boards = json.loads(listed.stdout or "[]")
    if any(isinstance(item, dict) and item.get("slug") == board for item in boards):
        return False
    args = [
        hermes_bin,
        "kanban",
        "boards",
        "create",
        board,
        "--name",
        "Overkill Factory Live Smoke",
        "--description",
        "Isolated board for Overkill Factory adapter validation.",
        "--icon",
        "O",
        "--color",
        "#0f766e",
    ]
    if default_workdir:
        args.extend(["--default-workdir", default_workdir])
    run_checked(args, runner)
    return True


def create_task(
    *,
    hermes_bin: str,
    board: str,
    title: str,
    body: str,
    assignee: str,
    idempotency_key: str,
    created_by: str,
    workspace: str,
    blocked: bool,
    runner: Runner = default_runner,
) -> str:
    ensure_non_empty_body(body)
    args = hermes_kanban(
        hermes_bin,
        board,
        "create",
        title,
        "--body",
        body,
        "--assignee",
        assignee,
        "--idempotency-key",
        idempotency_key,
        "--created-by",
        created_by,
        "--workspace",
        workspace,
        "--json",
    )
    if blocked:
        args.extend(["--initial-status", "blocked"])
    task_id = parse_task_id(run_checked(args, runner).stdout)
    if blocked:
        ensure_blocked_event(
            hermes_bin=hermes_bin,
            board=board,
            task_id=task_id,
            reason="Overkill Factory gate starts blocked until required authority evidence passes.",
            runner=runner,
        )
    return task_id


def materialize(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    card_path = args.card.resolve()
    ledger_path = args.ledger.resolve()
    result = build_hook_result(
        card_path=card_path,
        from_status=args.from_status,
        to_status=args.to_status,
        receipt_path=args.receipt,
        worker_results_dir=None,
        ledger_path=ledger_path,
    )
    plan = result["plan"]
    card_id = str(plan.get("event", {}).get("card_id") or card_path.stem)
    if args.dry_run:
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "materialize",
            "dry_run": True,
            "board": args.board,
            "board_created": False,
            "board_create_requested": bool(args.ensure_board),
            "board_create_checked": False,
            "main_task_id": None,
            "worker_task_ids": {},
            "hook": result,
        }
        if args.out:
            write_json(args.out, envelope)
        return envelope

    board_created = False
    if args.ensure_board:
        board_created = ensure_board(
            hermes_bin=args.hermes_bin,
            board=args.board,
            default_workdir=str(ROOT),
            runner=runner,
        )

    readiness_blockers = route_readiness_blockers(
        args.route_readiness,
        [
            str(task.get("worker_id"))
            for task in plan.get("worker_tasks", [])
            if str(task.get("worker_id") or "").strip() and task.get("status") != "not_required_by_current_card"
        ],
    )
    if readiness_blockers:
        raise RuntimeError("pre-dispatch route readiness blocked live materialization: " + "; ".join(readiness_blockers))

    main_task_id = create_task(
        hermes_bin=args.hermes_bin,
        board=args.board,
        title=f"OF {card_id} main gate",
        body=card_path.read_text(encoding="utf-8"),
        assignee=args.main_assignee,
        idempotency_key=f"overkill:{card_id}:main",
        created_by="overkill-factory",
        workspace=f"dir:{ROOT}",
        blocked=True,
        runner=runner,
    )
    worker_task_ids: dict[str, str] = {}
    review_promoted_worker_task_ids: dict[str, str] = {}
    for task in plan.get("worker_tasks", []):
        worker_id = str(task.get("worker_id") or "").strip()
        if not worker_id or task.get("status") == "not_required_by_current_card":
            continue
        packet = task.get("packet") or {}
        task_id = create_task(
            hermes_bin=args.hermes_bin,
            board=args.board,
            title=str(task.get("title") or f"OF {card_id} {worker_id}"),
            body=json.dumps(packet, indent=2, ensure_ascii=True),
            assignee=args.worker_assignee_prefix + worker_id,
            idempotency_key=f"overkill:{card_id}:{worker_id}",
            created_by="overkill-factory",
            workspace=f"dir:{ROOT}",
            blocked=not args.worker_ready,
            runner=runner,
        )
        worker_task_ids[worker_id] = task_id
        run_checked(hermes_kanban(args.hermes_bin, args.board, "link", task_id, main_task_id), runner)
        review_authorized = (
            task.get("dependency_authorization_state") == "review_ready"
            and task.get("status") == "requires_execution"
            and bool(task.get("review_task_authorizations"))
        )
        if review_authorized and not args.worker_ready:
            auth = task["review_task_authorizations"][0]
            requirement_id = str(auth.get("requirement_id") or "review-required-handoff")
            producer_ref = str(auth.get("producer_ref") or "producer-handoff")
            unblock_task(
                hermes_bin=args.hermes_bin,
                board=args.board,
                task_id=task_id,
                reason=(
                    "Review task authorized by valid review-required handoff "
                    f"{requirement_id} from {producer_ref}; non-review downstream remains gated."
                ),
                runner=runner,
            )
            review_promoted_worker_task_ids[worker_id] = task_id

    record_live_binding(
        ledger_path=ledger_path,
        card_id=card_id,
        board=args.board,
        main_task_id=main_task_id,
        worker_task_ids=worker_task_ids,
    )

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "materialize",
        "dry_run": False,
        "board": args.board,
        "board_created": board_created,
        "main_task_id": main_task_id,
        "worker_task_ids": worker_task_ids,
        "review_promoted_worker_task_ids": review_promoted_worker_task_ids,
        "hook": result,
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def enforce_done(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    result = build_hook_result(
        card_path=args.card.resolve(),
        from_status=args.from_status,
        to_status=args.to_status,
        receipt_path=args.receipt.resolve(),
        worker_results_dir=args.worker_results_dir.resolve(),
        ledger_path=args.ledger.resolve(),
    )
    blocked = result["transition_action"] == ACTION_BLOCK_TRANSITION
    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "enforce-done",
        "blocked": blocked,
        "board": args.board,
        "main_task_id": args.main_task_id,
        "hook": result,
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    if blocked:
        return public_envelope
    readiness_blockers = route_readiness_blockers(args.route_readiness, ["evidence-reconciler"])
    if readiness_blockers:
        raise RuntimeError("pre-completion route readiness blocked live completion: " + "; ".join(readiness_blockers))
    if args.complete_main:
        card_id = str(result.get("plan", {}).get("event", {}).get("card_id") or args.card.stem)
        validate_live_binding(
            ledger_path=args.ledger.resolve(),
            card_id=card_id,
            board=args.board,
            main_task_id=args.main_task_id,
        )
        metadata = json.dumps(load_json(args.receipt.resolve()), ensure_ascii=True)
        run_checked(
            hermes_kanban(
                args.hermes_bin,
                args.board,
                "complete",
                args.main_task_id,
                "--result",
                args.result,
                "--summary",
                args.summary,
                "--metadata",
                metadata,
            ),
            runner,
        )
    return public_envelope


def dispatch(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    before_ready = list_tasks_by_status(
        hermes_bin=args.hermes_bin,
        board=args.board,
        status="ready",
        runner=runner,
    )
    before_running = list_tasks_by_status(
        hermes_bin=args.hermes_bin,
        board=args.board,
        status="running",
        runner=runner,
    )
    before_ready_ids = {
        str(task.get("task_id") or task.get("id") or "")
        for task in before_ready
        if str(task.get("task_id") or task.get("id") or "").strip()
    }
    before_running_ids = {
        str(task.get("task_id") or task.get("id") or "")
        for task in before_running
        if str(task.get("task_id") or task.get("id") or "").strip()
    }

    dispatch_args = ["dispatch", "--json"]
    if args.dry_run:
        dispatch_args.append("--dry-run")
    if args.max is not None:
        dispatch_args.extend(["--max", str(args.max)])
    if args.failure_limit is not None:
        dispatch_args.extend(["--failure-limit", str(args.failure_limit)])
    completed = run_checked(hermes_kanban(args.hermes_bin, args.board, *dispatch_args), runner)
    native_payload = parse_json_output(completed.stdout, command="hermes kanban dispatch --json")
    if not isinstance(native_payload, dict):
        raise RuntimeError("hermes kanban dispatch --json returned a non-object payload")

    after_running = [] if args.dry_run else list_tasks_by_status(
        hermes_bin=args.hermes_bin,
        board=args.board,
        status="running",
        runner=runner,
    )
    after_running_by_id = {
        str(task.get("task_id") or task.get("id") or ""): task
        for task in after_running
        if str(task.get("task_id") or task.get("id") or "").strip()
    }

    spawned_by_this_command = [
        enrich_dispatch_task(
            hermes_bin=args.hermes_bin,
            board=args.board,
            record=record,
            after_running_by_id=after_running_by_id,
            runner=runner,
        )
        for record in normalize_native_spawned(native_payload)
    ]
    spawned_ids = {record["task_id"] for record in spawned_by_this_command if record.get("task_id")}
    observed_ids = sorted((set(after_running_by_id) - before_running_ids) & before_ready_ids)
    already_running_after_dispatch = [
        enrich_dispatch_task(
            hermes_bin=args.hermes_bin,
            board=args.board,
            record={"task_id": task_id, "observed_source": "ready_before_running_after_dispatch"},
            after_running_by_id=after_running_by_id,
            runner=runner,
        )
        for task_id in observed_ids
        if task_id not in spawned_ids
    ]
    for record in spawned_by_this_command:
        record["dispatch_observation"] = "native_dispatch_spawned"
    for record in already_running_after_dispatch:
        record["dispatch_observation"] = "already_running_after_native_dispatch"

    combined_spawned = [*spawned_by_this_command, *already_running_after_dispatch]
    native_sanitized = dict(native_payload)
    native_sanitized["spawned"] = normalize_native_spawned(native_payload)

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "dispatch",
        "dry_run": bool(args.dry_run),
        "board": args.board,
        "spawned": combined_spawned,
        "spawned_by_this_command": spawned_by_this_command,
        "already_running_after_dispatch": already_running_after_dispatch,
        "native_dispatch": native_sanitized,
        "dispatch_observed_state": {
            "ready_before_count": len(before_ready_ids),
            "running_before_count": len(before_running_ids),
            "running_after_count": len(after_running_by_id),
        },
        "hook": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "no_shadow_dispatcher": True,
            "reporting_policy": "Hermes dispatch remains authoritative; this adapter only enriches the returned report from Hermes state.",
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate Overkill Factory gates on Hermes Kanban.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_mat = sub.add_parser("materialize", help="Create the main card and required worker cards.")
    p_mat.add_argument("--card", type=Path, required=True)
    p_mat.add_argument("--board", required=True)
    p_mat.add_argument("--ledger", type=Path, required=True)
    p_mat.add_argument("--receipt", type=Path)
    p_mat.add_argument("--from-status", default="blocked")
    p_mat.add_argument("--to-status", default="ready")
    p_mat.add_argument("--hermes-bin", default="hermes")
    p_mat.add_argument("--main-assignee", default="factory-orchestrator")
    p_mat.add_argument("--worker-assignee-prefix", default="")
    p_mat.add_argument("--worker-ready", action="store_true")
    p_mat.add_argument("--ensure-board", action="store_true")
    p_mat.add_argument("--dry-run", action="store_true")
    p_mat.add_argument("--route-readiness", type=Path)
    p_mat.add_argument("--out", type=Path)

    p_done = sub.add_parser("enforce-done", help="Validate worker results before completing the main card.")
    p_done.add_argument("--card", type=Path, required=True)
    p_done.add_argument("--board", required=True)
    p_done.add_argument("--main-task-id", required=True)
    p_done.add_argument("--receipt", type=Path, required=True)
    p_done.add_argument("--worker-results-dir", type=Path, required=True)
    p_done.add_argument("--ledger", type=Path, required=True)
    p_done.add_argument("--from-status", default="ready")
    p_done.add_argument("--to-status", default="done")
    p_done.add_argument("--hermes-bin", default="hermes")
    p_done.add_argument("--complete-main", action="store_true")
    p_done.add_argument("--route-readiness", type=Path)
    p_done.add_argument("--result", default="Overkill Factory gate satisfied.")
    p_done.add_argument("--summary", default="Worker evidence reconciled by Overkill Factory.")
    p_done.add_argument("--out", type=Path)

    p_dispatch = sub.add_parser("dispatch", help="Run native Hermes dispatch and enrich the public-safe result.")
    p_dispatch.add_argument("--board", required=True)
    p_dispatch.add_argument("--hermes-bin", default="hermes")
    p_dispatch.add_argument("--dry-run", action="store_true")
    p_dispatch.add_argument("--max", type=int)
    p_dispatch.add_argument("--failure-limit", type=int)
    p_dispatch.add_argument("--out", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "materialize":
            envelope = materialize(args)
        elif args.command == "enforce-done":
            envelope = enforce_done(args)
        else:
            envelope = dispatch(args)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not args.out:
        print(json.dumps(envelope, indent=2, ensure_ascii=True))
    if args.command == "enforce-done" and envelope.get("blocked"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
