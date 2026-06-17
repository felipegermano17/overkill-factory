#!/usr/bin/env python3
"""Materialize Overkill Factory worker gates in a real Hermes Kanban board."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
FACTORYCTL_PATH = SCRIPTS_DIR / "factoryctl.py"
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
RECOVERY_ATTEMPT_MARKER = "factory_recovery_attempt"
ACTIVE_OR_TERMINAL_STATUSES = {"ready", "running", "done", "complete", "completed"}
HISTORY_SOURCE_KEYS = ("events", "history", "timeline", "comments", "runs")
CONTRACT_DIGEST_ALGORITHM = "sha256"
IDEMPOTENCY_DIGEST_LENGTH = 16
VOLATILE_CONTRACT_KEYS = {
    "checked_at",
    "created_at",
    "generated_at",
    "last_checked_at",
    "timestamp",
    "updated_at",
}
CANONICALIZATION_VERSION = "v1"
IDEMPOTENCY_LINEAGE_POLICY = "base_identity_is_logical_lineage_contract_key_is_runtime_identity"
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
WORKER_MATERIALIZATION_CONTRACT_FIELDS = (
    "task_type",
    "worker_id",
    "gate_timing_class",
    "queue_class",
    "runtime_authority",
    "local_state_authority",
    "required_before",
    "expected_receipt_field",
    "status",
    "dependency_authorization_state",
    "review_task_authorizations",
    "recovery_route_refs",
    "packet",
)


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


def load_factoryctl() -> Any:
    spec = importlib.util.spec_from_file_location("overkill_factoryctl_live_adapter", FACTORYCTL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load factoryctl from {FACTORYCTL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["overkill_factoryctl_live_adapter"] = module
    spec.loader.exec_module(module)
    return module


def stable_contract_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): stable_contract_value(item)
            for key, item in sorted(value.items(), key=lambda entry: str(entry[0]))
            if str(key) not in VOLATILE_CONTRACT_KEYS
        }
    if isinstance(value, list):
        return [stable_contract_value(item) for item in value]
    return value


def contract_digest(value: Any) -> str:
    stable_value = stable_contract_value(value)
    if isinstance(stable_value, str):
        payload = stable_value
    else:
        payload = json.dumps(stable_value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compact_json_argument(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def idempotency_digest_fragment(digest: str) -> str:
    return digest[:IDEMPOTENCY_DIGEST_LENGTH]


def main_base_idempotency_key(card_id: str) -> str:
    return f"overkill:{card_id}:main"


def worker_base_idempotency_key(card_id: str, worker_id: str) -> str:
    return f"overkill:{card_id}:{worker_id}"


def main_task_idempotency_key(card_id: str, card_body: str) -> str:
    return f"{main_base_idempotency_key(card_id)}:{idempotency_digest_fragment(contract_digest(card_body))}"


def worker_materialization_contract(task: dict[str, Any]) -> dict[str, Any]:
    return {field: task[field] for field in WORKER_MATERIALIZATION_CONTRACT_FIELDS if field in task}


def worker_task_idempotency_key(card_id: str, worker_id: str, task_contract: dict[str, Any]) -> str:
    return f"{worker_base_idempotency_key(card_id, worker_id)}:{idempotency_digest_fragment(contract_digest(task_contract))}"


def recovery_route_digest(route: dict[str, Any]) -> str:
    return f"{CONTRACT_DIGEST_ALGORITHM}:{contract_digest(route)}"


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


def task_status(payload: dict[str, Any]) -> str:
    return str(payload.get("status") or "").strip().lower()


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


def strip_terminal_markup(value: str) -> str:
    return ANSI_ESCAPE_RE.sub("", value or "").replace("\r", "")


def parse_profile_list(output: str) -> dict[str, dict[str, str]]:
    profiles: dict[str, dict[str, str]] = {}
    for raw_line in strip_terminal_markup(output).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        while line and not (line[0].isalnum() or line[0] in {"_", "-", "."}):
            line = line[1:].lstrip()
        if not line:
            continue
        columns = line.split()
        if len(columns) < 2:
            continue
        profile = columns[0]
        if profile.lower() in {"profile", "profiles"}:
            continue
        if profile.lower().startswith("profile "):
            continue
        profiles[profile] = {
            "model": columns[1],
            "gateway": columns[2] if len(columns) > 2 else "",
            "alias": columns[3] if len(columns) > 3 else "",
        }
    return profiles


def status_has_provider_auth(status_output: str, provider_name: str) -> bool:
    target = " ".join(str(provider_name or "").split()).lower()
    if not target:
        return False
    for raw_line in strip_terminal_markup(status_output).splitlines():
        normalized = " ".join(raw_line.split()).lower()
        if target in normalized and "logged in" in normalized and "not logged in" not in normalized:
            return True
    return False


def required_workers_from_ready_plan(path: Path | None) -> list[str]:
    if path is None:
        return []
    plan = load_ready_work_unit_materialization_plan(path.resolve())
    workers: list[str] = []
    for task in plan.get("tasks", []):
        if not isinstance(task, dict):
            continue
        worker_id = str(task.get("owner_worker") or "").strip()
        if worker_id and worker_id not in workers:
            workers.append(worker_id)
    return workers


def build_route_readiness_manifest(
    *,
    required_workers: list[str],
    profiles: dict[str, dict[str, str]],
    auth_ready: bool,
    ledger_ref: str,
    credential_evidence_ref: str,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blocked_workers: list[str] = []
    for worker_id in required_workers:
        profile = profiles.get(worker_id)
        profile_exists = profile is not None
        model = str((profile or {}).get("model") or "").strip()
        model_configured = bool(model and model not in {"-", "\u2014"})
        provider_configured = bool(auth_ready)
        credential_status = "pass" if auth_ready else "fail"
        blocked_reasons: list[str] = []
        if not profile_exists:
            blocked_reasons.append("profile_missing")
        if not model_configured:
            blocked_reasons.append("model_missing")
        if not provider_configured:
            blocked_reasons.append("provider_auth_not_proven")
        if credential_status != "pass":
            blocked_reasons.append("credential_not_proven")
        status = "ready" if not blocked_reasons else "blocked"
        if status == "blocked":
            blocked_workers.append(worker_id)
        checks.append(
            {
                "worker_id": worker_id,
                "task_id": f"route:{worker_id}",
                "required_before": "materialize-ready-work-units",
                "queue_class": "runtime-readiness-before-materialization",
                "status": status,
                "profile_exists": profile_exists,
                "config_ref": f"hermes-profile:{worker_id}" if profile_exists else None,
                "model_configured": model_configured,
                "provider_configured": provider_configured,
                "credential_status": credential_status,
                "credential_evidence": [credential_evidence_ref] if credential_status == "pass" else [],
                "blocked_reasons": blocked_reasons,
            }
        )
    return {
        "$schema": ROUTE_READINESS_SCHEMA,
        "schema": "overkill_factory_hermes_worker_route_readiness.v1",
        "ledger_ref": ledger_ref,
        "hermes_home_ref": "redacted-hermes-home",
        "result": "PASS" if not blocked_workers else "BLOCKED",
        "worker_count": len(required_workers),
        "blocked_worker_count": len(blocked_workers),
        "blocked_workers": blocked_workers,
        "checks": checks,
        "production_rule": (
            "Route readiness is collected from read-only Hermes profile/status readback; "
            "blocked workers must be repaired before live materialization or dispatch."
        ),
    }


def collect_route_readiness(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    required_workers: list[str] = []
    for worker_id in required_workers_from_ready_plan(args.plan):
        if worker_id not in required_workers:
            required_workers.append(worker_id)
    for worker_id in args.worker or []:
        normalized = str(worker_id or "").strip()
        if normalized and normalized not in required_workers:
            required_workers.append(normalized)
    if not required_workers:
        raise RuntimeError("route readiness collection requires --plan or at least one --worker")

    profile_output = run_checked([args.hermes_bin, "profile", "list"], runner).stdout
    status_output = run_checked([args.hermes_bin, "status"], runner).stdout
    profiles = parse_profile_list(profile_output)
    auth_ready = status_has_provider_auth(status_output, args.required_auth_provider)
    manifest = build_route_readiness_manifest(
        required_workers=required_workers,
        profiles=profiles,
        auth_ready=auth_ready,
        ledger_ref=args.ledger_ref,
        credential_evidence_ref=args.credential_evidence_ref,
    )
    if args.out:
        write_json(args.out, manifest)
    return manifest


def ensure_non_empty_body(body: str) -> None:
    if not str(body or "").strip():
        raise RuntimeError("Hermes task body must be non-empty before dispatch")


def task_readback_status(payload: dict[str, Any]) -> str:
    status = str(payload.get("status") or "").strip().lower()
    task = payload.get("task")
    if not status and isinstance(task, dict):
        status = str(task.get("status") or "").strip().lower()
    return status


def task_readback_task(payload: dict[str, Any]) -> dict[str, Any]:
    task = payload.get("task")
    if isinstance(task, dict):
        return task
    return payload


def task_readback_id(payload: dict[str, Any]) -> str:
    task = task_readback_task(payload)
    return str(task.get("id") or task.get("task_id") or payload.get("id") or payload.get("task_id") or "").strip()


def task_readback_events(payload: dict[str, Any]) -> list[Any]:
    events = payload.get("events") or payload.get("history") or payload.get("timeline") or []
    if isinstance(events, list):
        return events
    task = payload.get("task")
    if isinstance(task, dict):
        nested_events = task.get("events") or task.get("history") or task.get("timeline") or []
        if isinstance(nested_events, list):
            return nested_events
    return []


def task_readback_assignee(payload: dict[str, Any]) -> str:
    return str(task_readback_task(payload).get("assignee") or "").strip()


def task_readback_body(payload: dict[str, Any]) -> str:
    return str(task_readback_task(payload).get("body") or "")


def task_dispatcher_workspace_ref(payload: dict[str, Any]) -> str:
    task = task_readback_task(payload)
    kind = str(task.get("workspace_kind") or task.get("workspace") or "").strip()
    path = str(task.get("workspace_path") or "").strip()
    if kind == "dir" and path:
        return f"dir:{path}"
    if kind:
        return kind
    return path


def ensure_dispatcher_visible_workspace(payload: dict[str, Any], *, task_id: str) -> None:
    workspace_ref = task_dispatcher_workspace_ref(payload)
    if not workspace_ref:
        raise RuntimeError(f"Hermes task {task_id} has no dispatcher workspace ref before release")
    normalized = workspace_ref.replace("\\", "/")
    if re.search(r"\b[A-Za-z]:/", normalized):
        raise RuntimeError(f"Hermes task {task_id} workspace is local to the adapter, not dispatcher-visible")


def pre_dispatch_activity_markers(payload: dict[str, Any]) -> list[str]:
    markers: list[str] = []
    for event in task_readback_events(payload):
        if not isinstance(event, dict):
            continue
        kind = str(event.get("kind") or event.get("type") or event.get("event") or event.get("action") or "").strip().lower()
        if kind in {"claimed", "spawned", "spawn_failed", "running"}:
            markers.append(kind)
    runs = payload.get("runs")
    if isinstance(runs, list):
        for run in runs:
            if isinstance(run, dict):
                status = str(run.get("status") or run.get("outcome") or "").strip().lower()
                if status and status != "blocked":
                    markers.append(f"run:{status}")
    return markers


def ensure_no_pre_dispatch_activity(payload: dict[str, Any], *, task_id: str) -> None:
    markers = pre_dispatch_activity_markers(payload)
    if markers:
        raise RuntimeError(f"Hermes task {task_id} had pre-dispatch activity: {', '.join(markers)}")


def ensure_ready_work_unit_readback_contract(
    *,
    payload: dict[str, Any],
    task_id: str,
    expected_assignee: str,
    expected_packet_id: str,
) -> None:
    if task_readback_status(payload) != "blocked":
        raise RuntimeError(f"Hermes task {task_id} is not blocked after ready work-unit materialization")
    if task_readback_assignee(payload) != expected_assignee:
        raise RuntimeError(f"Hermes task {task_id} assignee readback does not match target profile")
    try:
        body = json.loads(task_readback_body(payload))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Hermes task {task_id} body readback is not valid JSON") from exc
    if str(body.get("packet_id") or "").strip() != expected_packet_id:
        raise RuntimeError(f"Hermes task {task_id} body readback does not match ready work-unit packet")
    ensure_no_pre_dispatch_activity(payload, task_id=task_id)


def ready_work_unit_body(payload: dict[str, Any], *, task_id: str) -> dict[str, Any]:
    try:
        body = json.loads(task_readback_body(payload))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Hermes task {task_id} body readback is not valid JSON") from exc
    if not isinstance(body, dict):
        raise RuntimeError(f"Hermes task {task_id} body readback is not a JSON object")
    return body


def task_has_blocked_event(payload: dict[str, Any]) -> bool:
    if task_readback_status(payload) == "blocked":
        for event in task_readback_events(payload):
            if isinstance(event, dict):
                event_type = str(
                    event.get("type") or event.get("event") or event.get("action") or event.get("kind") or ""
                ).strip().lower()
                if event_type in {"block", "blocked"}:
                    return True
                continue
            text = str(event).lower()
            if re.search(r"\bblocked\b", text) and not re.search(r"\bunblocked\b", text):
                return True
    return False


def task_has_unblocked_event(payload: dict[str, Any], required_markers: list[str] | None = None) -> bool:
    if task_readback_status(payload) == "blocked":
        return False
    markers = [marker.strip().lower() for marker in (required_markers or []) if marker.strip()]
    unblocked_event_seen = False
    for event in task_readback_events(payload):
        if isinstance(event, dict):
            event_type = str(
                event.get("type") or event.get("event") or event.get("action") or event.get("kind") or ""
            ).strip().lower()
            if event_type in {"unblock", "unblocked"}:
                unblocked_event_seen = True
                if not markers or all(marker in str(event).lower() for marker in markers):
                    return True
            continue
        text = str(event).lower()
        if "unblock" not in text:
            continue
        if all(marker in text for marker in markers):
            return True
    return unblocked_event_seen and history_contains_markers(payload, markers)


def history_contains_markers(payload: dict[str, Any], markers: list[str]) -> bool:
    if not markers:
        return True
    for key, _index, item in history_items(payload):
        if key == "runs":
            continue
        text = json.dumps(item, ensure_ascii=True, sort_keys=True).lower() if isinstance(item, dict) else str(item).lower()
        if all(marker in text for marker in markers):
            return True
    return False


def worker_satisfied_by_reconciliation(plan: dict[str, Any], worker_id: str) -> bool:
    reconciliation = plan.get("completion_reconciliation")
    if not isinstance(reconciliation, dict):
        return False
    workers = reconciliation.get("workers")
    if not isinstance(workers, dict):
        return False
    row = workers.get(worker_id)
    return isinstance(row, dict) and row.get("satisfied") is True


def downstream_authorizations_by_worker(plan: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    by_worker: dict[str, list[dict[str, Any]]] = {}
    for authorization in plan.get("downstream_task_authorizations") or []:
        if not isinstance(authorization, dict):
            continue
        if (
            authorization.get("authorization_type") != "fresh_review_downstream_task"
            or authorization.get("authorization_state") != "worker_task_ready"
            or authorization.get("runtime_authority") != "hermes_kanban"
            or authorization.get("local_state_authority") is not False
        ):
            continue
        for worker_id in authorization.get("authorized_worker_ids") or []:
            worker_id = str(worker_id or "").strip()
            if worker_id and worker_id != "human-gate-clerk":
                by_worker.setdefault(worker_id, []).append(authorization)
    return by_worker


def downstream_worker_ready_after_fresh_review(
    plan: dict[str, Any],
    task: dict[str, Any],
    authorizations: dict[str, list[dict[str, Any]]],
) -> bool:
    if plan.get("transition_action") != "allow_and_create_worker_tasks":
        return False
    worker_id = str(task.get("worker_id") or "").strip()
    if not worker_id or worker_id == "human-gate-clerk":
        return False
    if worker_id not in authorizations:
        return False
    if task.get("status") != "requires_execution":
        return False
    if task.get("required_before") != "done":
        return False
    if task.get("dependency_authorization_state") == "review_ready":
        return False
    if worker_satisfied_by_reconciliation(plan, worker_id):
        return False
    return True


def history_items(payload: dict[str, Any]) -> list[tuple[str, int, Any]]:
    items: list[tuple[str, int, Any]] = []
    for key in HISTORY_SOURCE_KEYS:
        value = payload.get(key)
        if isinstance(value, list):
            items.extend((key, index, item) for index, item in enumerate(value))
    return items


def has_history_source(payload: dict[str, Any]) -> bool:
    return any(isinstance(payload.get(key), list) for key in HISTORY_SOURCE_KEYS)


def recovery_attempt_history_refs(payload: dict[str, Any], route_id: str, route_digest: str) -> list[str]:
    route = route_id.strip().lower()
    digest = route_digest.strip().lower()
    if not route or not digest:
        return []
    refs: list[str] = []
    for key, index, item in history_items(payload):
        text = json.dumps(item, ensure_ascii=True, sort_keys=True).lower() if isinstance(item, dict) else str(item).lower()
        if route in text and digest in text and RECOVERY_ATTEMPT_MARKER in text:
            refs.append(f"{key}:{index}")
    return refs


def retry_policy_max_attempts(route: dict[str, Any]) -> int:
    policy = route.get("retry_policy")
    value = policy.get("max_attempts") if isinstance(policy, dict) else None
    if isinstance(value, int) and value >= 1:
        return value
    return 1


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
    required_readback_markers: list[str] | None = None,
    runner: Runner = default_runner,
) -> None:
    if required_readback_markers:
        run_checked(
            hermes_kanban(
                hermes_bin,
                board,
                "comment",
                "--author",
                "overkill-factory",
                task_id,
                reason,
            ),
            runner,
        )
    run_checked(hermes_kanban(hermes_bin, board, "unblock", task_id, reason), runner)
    shown = run_checked(hermes_kanban(hermes_bin, board, "show", task_id, "--json"), runner)
    try:
        payload = json.loads(shown.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("Hermes show --json did not return JSON while verifying unblock event") from exc
    if not isinstance(payload, dict) or not task_has_unblocked_event(payload, required_readback_markers):
        raise RuntimeError(f"Hermes task {task_id} is not durably unblocked after unblock command")


def record_live_binding(
    *,
    ledger_path: Path,
    card_id: str,
    board: str,
    main_task_id: str,
    worker_task_ids: dict[str, str],
    idempotency_contract: dict[str, Any] | None = None,
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
        "card_id": card_id,
        "binding_role": "hermes_ref_projection",
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "board": board,
        "main_task_id": main_task_id,
        "worker_task_ids": worker_task_ids,
    }
    if idempotency_contract:
        bindings[card_id]["idempotency_contract"] = idempotency_contract
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
        shown_task = show_task(
            hermes_bin=hermes_bin,
            board=board,
            task_id=task_id,
            runner=runner,
        )
        status = task_status(shown_task)
        if status in ACTIVE_OR_TERMINAL_STATUSES:
            return task_id
        if not task_has_blocked_event(shown_task):
            ensure_blocked_event(
                hermes_bin=hermes_bin,
                board=board,
                task_id=task_id,
                reason="Overkill Factory gate starts blocked until required authority evidence passes.",
                runner=runner,
            )
    return task_id


def load_ready_work_unit_materialization_plan(path: Path) -> dict[str, Any]:
    plan = load_json(path)
    factoryctl = load_factoryctl()
    errors = factoryctl.validate_ready_work_unit_hermes_materialization_plan(plan)
    if errors:
        raise RuntimeError("invalid ready work-unit Hermes materialization plan: " + "; ".join(errors))
    return plan


def create_ready_work_unit_task(
    *,
    hermes_bin: str,
    board: str,
    task: dict[str, Any],
    worker_assignee_prefix: str,
    workspace_ref: str,
    runner: Runner = default_runner,
) -> str:
    create_policy = task.get("create_policy") if isinstance(task.get("create_policy"), dict) else {}
    block_policy = task.get("block_policy") if isinstance(task.get("block_policy"), dict) else {}
    if create_policy.get("create_with_assignee") is not False:
        raise RuntimeError("ready work-unit task create_policy must create without assignee before the blocked event")
    if create_policy.get("assign_after_block_event_verified") is not True:
        raise RuntimeError("ready work-unit task create_policy must assign only after the blocked event is verified")
    if create_policy.get("no_spawn_protocol") != "create-unassigned-default-block-assign-v2":
        raise RuntimeError("ready work-unit task create_policy must use the no-spawn create-unassigned-block-assign protocol")
    if block_policy.get("block_event_required_before_dispatch") is not True:
        raise RuntimeError("ready work-unit task must require a blocked event before dispatch")
    if block_policy.get("final_status_required") != "blocked":
        raise RuntimeError("ready work-unit task must require final blocked status before dispatch")

    body_contract = task.get("body_contract") if isinstance(task.get("body_contract"), dict) else {}
    ensure_non_empty_body(compact_json_argument(body_contract))
    target_assignee = str(create_policy.get("target_assignee_profile") or task.get("owner_worker") or "").strip()
    if not target_assignee:
        raise RuntimeError("ready work-unit task requires target_assignee_profile")
    task_id = parse_task_id(
        run_checked(
            hermes_kanban(
                hermes_bin,
                board,
                "create",
                str(task.get("title") or f"OF ready work unit {task.get('work_unit_id') or 'work-unit'}"),
                "--body",
                compact_json_argument(body_contract),
                "--idempotency-key",
                str(task.get("idempotency_key") or ""),
                "--created-by",
                "overkill-factory",
                "--workspace",
                workspace_ref,
                "--json",
            ),
            runner,
        ).stdout
    )
    ensure_blocked_event(
        hermes_bin=hermes_bin,
        board=board,
        task_id=task_id,
        reason=str(
            block_policy.get("blocked_reason")
            or "Overkill Factory ready work-unit runtime gate starts blocked until evidence passes."
        ),
        runner=runner,
    )
    blocked_task = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    ensure_no_pre_dispatch_activity(blocked_task, task_id=task_id)
    if not task_has_blocked_event(blocked_task):
        raise RuntimeError(f"Hermes task {task_id} lacks verified blocked event after materialization")
    if task_readback_status(blocked_task) != "blocked":
        raise RuntimeError(f"Hermes task {task_id} is not blocked before assignment")
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "assign",
            task_id,
            worker_assignee_prefix + target_assignee,
        ),
        runner,
    )
    final_task = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    try:
        ensure_ready_work_unit_readback_contract(
            payload=final_task,
            task_id=task_id,
            expected_assignee=worker_assignee_prefix + target_assignee,
            expected_packet_id=str(task.get("packet_id") or "").strip(),
        )
    except RuntimeError:
        if task_readback_status(final_task) != "blocked":
            ensure_blocked_event(
                hermes_bin=hermes_bin,
                board=board,
                task_id=task_id,
                reason="Ready work-unit assignment triggered unsafe non-blocked state; re-blocking before failing closed.",
                runner=runner,
            )
        raise
    return task_id


def materialize_ready_work_units(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    plan = load_ready_work_unit_materialization_plan(args.plan.resolve())
    board = str(args.board or plan.get("board") or "").strip()
    if not board:
        raise RuntimeError("ready work-unit materialization requires a board")
    if str(plan.get("board") or "").strip() and board != str(plan.get("board") or "").strip():
        raise RuntimeError("provided board does not match the ready work-unit materialization plan")

    if args.dry_run:
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "materialize-ready-work-units",
            "dry_run": True,
            "board": board,
            "board_created": False,
            "board_create_requested": bool(args.ensure_board),
            "board_create_checked": False,
            "materialization_plan_id": plan.get("plan_id"),
            "ready_work_unit_task_ids": {},
            "packet_task_ids": {},
            "runtime_gate": plan.get("runtime_gate", {}),
            "hook": {"plan": plan},
        }
        if args.out:
            write_json(args.out, envelope)
        return envelope

    required_workers = [
        str(task.get("owner_worker") or "").strip()
        for task in plan.get("tasks", [])
        if isinstance(task, dict) and str(task.get("owner_worker") or "").strip()
    ]
    readiness_blockers = route_readiness_blockers(args.route_readiness, required_workers)
    if readiness_blockers:
        raise RuntimeError("pre-dispatch route readiness blocked ready work-unit materialization: " + "; ".join(readiness_blockers))

    board_created = False
    if args.ensure_board:
        board_created = ensure_board(
            hermes_bin=args.hermes_bin,
            board=board,
            default_workdir=str(ROOT),
            runner=runner,
        )

    ready_work_unit_task_ids: dict[str, str] = {}
    packet_task_ids: dict[str, str] = {}
    for task in plan.get("tasks", []):
        if not isinstance(task, dict):
            continue
        task_id = create_ready_work_unit_task(
            hermes_bin=args.hermes_bin,
            board=board,
            task=task,
            worker_assignee_prefix=args.worker_assignee_prefix,
            workspace_ref=str(args.workspace or f"dir:{ROOT}"),
            runner=runner,
        )
        work_unit_id = str(task.get("work_unit_id") or "").strip()
        packet_id = str(task.get("packet_id") or "").strip()
        if work_unit_id:
            ready_work_unit_task_ids[work_unit_id] = task_id
        if packet_id:
            packet_task_ids[packet_id] = task_id

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "materialize-ready-work-units",
        "dry_run": False,
        "board": board,
        "board_created": board_created,
        "materialization_plan_id": plan.get("plan_id"),
        "ready_work_unit_task_ids": ready_work_unit_task_ids,
        "packet_task_ids": packet_task_ids,
        "runtime_gate": {
            **(plan.get("runtime_gate") if isinstance(plan.get("runtime_gate"), dict) else {}),
            "blocked_event_verified_task_ids": ready_work_unit_task_ids,
            "dispatch_allowed_by_this_step": False,
            "live_hermes_mutated": True,
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
        },
        "hook": {"plan": plan},
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def load_ready_work_unit_materialization_result(path: Path, *, plan: dict[str, Any], board: str) -> dict[str, Any]:
    result = load_json(path)
    if result.get("mode") != "materialize-ready-work-units":
        raise RuntimeError("ready work-unit release requires a materialize-ready-work-units result")
    if result.get("dry_run") is True:
        raise RuntimeError("ready work-unit release requires a real materialization result, not dry-run output")
    result_board = str(result.get("board") or "").strip()
    if result_board and result_board != board:
        raise RuntimeError("materialization result board does not match ready work-unit release board")
    plan_id = str(plan.get("plan_id") or "").strip()
    if plan_id and str(result.get("materialization_plan_id") or "").strip() != plan_id:
        raise RuntimeError("materialization result does not match the ready work-unit materialization plan")
    runtime_gate = result.get("runtime_gate")
    if not isinstance(runtime_gate, dict) or runtime_gate.get("live_hermes_mutated") is not True:
        raise RuntimeError("materialization result does not prove live Hermes materialization")
    if runtime_gate.get("dispatch_allowed_by_this_step") is not False:
        raise RuntimeError("materialization result must keep dispatch separated from materialization")
    work_unit_ids = {
        str(task.get("work_unit_id") or "").strip()
        for task in plan.get("tasks", [])
        if isinstance(task, dict) and str(task.get("work_unit_id") or "").strip()
    }
    packet_ids = {
        str(task.get("packet_id") or "").strip()
        for task in plan.get("tasks", [])
        if isinstance(task, dict) and str(task.get("packet_id") or "").strip()
    }
    result_work_units = set((result.get("ready_work_unit_task_ids") or {}).keys())
    result_packets = set((result.get("packet_task_ids") or {}).keys())
    missing_work_units = sorted(work_unit_ids - result_work_units)
    missing_packets = sorted(packet_ids - result_packets)
    if missing_work_units:
        raise RuntimeError("materialization result is missing work unit ids: " + ", ".join(missing_work_units))
    if missing_packets:
        raise RuntimeError("materialization result is missing packet ids: " + ", ".join(missing_packets))
    return result


def expected_ready_work_unit_tasks(plan: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = [task for task in plan.get("tasks", []) if isinstance(task, dict)]
    if not tasks:
        raise RuntimeError("ready work-unit release requires at least one task in the plan")
    return tasks


def expected_ready_work_unit_key(task: dict[str, Any]) -> tuple[str, str]:
    packet_id = str(task.get("packet_id") or "").strip()
    work_unit_id = str(task.get("work_unit_id") or "").strip()
    if not packet_id or not work_unit_id:
        raise RuntimeError("ready work-unit release requires packet_id and work_unit_id for every plan task")
    return packet_id, work_unit_id


def ready_work_unit_release_assignee(task: dict[str, Any], worker_assignee_prefix: str) -> str:
    create_policy = task.get("create_policy") if isinstance(task.get("create_policy"), dict) else {}
    assignee = str(create_policy.get("target_assignee_profile") or task.get("owner_worker") or "").strip()
    if not assignee:
        raise RuntimeError("ready work-unit release requires target_assignee_profile")
    return worker_assignee_prefix + assignee


def verify_ready_work_unit_release_candidate(
    *,
    payload: dict[str, Any],
    plan_task: dict[str, Any],
    worker_assignee_prefix: str,
) -> tuple[str, str, str]:
    task_id = task_readback_id(payload)
    if not task_id:
        raise RuntimeError("Hermes task readback has no task id")
    packet_id, work_unit_id = expected_ready_work_unit_key(plan_task)
    expected_assignee = ready_work_unit_release_assignee(plan_task, worker_assignee_prefix)
    if task_readback_status(payload) != "blocked":
        raise RuntimeError(f"Hermes task {task_id} is not blocked before ready work-unit release")
    if task_readback_assignee(payload) != expected_assignee:
        raise RuntimeError(f"Hermes task {task_id} assignee readback does not match target profile")
    body = ready_work_unit_body(payload, task_id=task_id)
    if str(body.get("packet_id") or "").strip() != packet_id:
        raise RuntimeError(f"Hermes task {task_id} body readback does not match ready work-unit packet")
    if str(body.get("work_unit_id") or "").strip() != work_unit_id:
        raise RuntimeError(f"Hermes task {task_id} body readback does not match ready work-unit id")
    if str(body.get("packet_type") or "").strip() != "ready_work_unit_execution_request":
        raise RuntimeError(f"Hermes task {task_id} body readback is not a ready work-unit execution request")
    if not task_has_blocked_event(payload):
        raise RuntimeError(f"Hermes task {task_id} lacks verified blocked event before release")
    ensure_no_pre_dispatch_activity(payload, task_id=task_id)
    ensure_dispatcher_visible_workspace(payload, task_id=task_id)
    return task_id, packet_id, work_unit_id


def blocked_ready_work_unit_readbacks(
    *,
    hermes_bin: str,
    board: str,
    runner: Runner = default_runner,
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    candidates: dict[tuple[str, str], list[dict[str, Any]]] = {}
    seen_task_ids: set[str] = set()
    for record in list_tasks_by_status(hermes_bin=hermes_bin, board=board, status="blocked", runner=runner):
        task_id = str(record.get("task_id") or record.get("id") or "").strip()
        if not task_id or task_id in seen_task_ids:
            continue
        seen_task_ids.add(task_id)
        payload = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
        try:
            body = ready_work_unit_body(payload, task_id=task_id)
        except RuntimeError:
            continue
        if str(body.get("packet_type") or "").strip() != "ready_work_unit_execution_request":
            continue
        packet_id = str(body.get("packet_id") or "").strip()
        work_unit_id = str(body.get("work_unit_id") or "").strip()
        if packet_id and work_unit_id:
            candidates.setdefault((packet_id, work_unit_id), []).append(payload)
    return candidates


def release_ready_work_units(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    plan = load_ready_work_unit_materialization_plan(args.plan.resolve())
    board = str(args.board or plan.get("board") or "").strip()
    if not board:
        raise RuntimeError("ready work-unit release requires a board")
    if str(plan.get("board") or "").strip() and board != str(plan.get("board") or "").strip():
        raise RuntimeError("provided board does not match the ready work-unit materialization plan")
    materialization_result = load_ready_work_unit_materialization_result(
        args.materialization_result.resolve(),
        plan=plan,
        board=board,
    )
    tasks = expected_ready_work_unit_tasks(plan)
    required_workers = [
        ready_work_unit_release_assignee(task, args.worker_assignee_prefix)
        for task in tasks
    ]
    readiness_blockers = route_readiness_blockers(args.route_readiness, required_workers)
    if readiness_blockers:
        raise RuntimeError("pre-dispatch route readiness blocked ready work-unit release: " + "; ".join(readiness_blockers))

    candidates = blocked_ready_work_unit_readbacks(hermes_bin=args.hermes_bin, board=board, runner=runner)
    verified: list[tuple[dict[str, Any], str, str, str]] = []
    for task in tasks:
        key = expected_ready_work_unit_key(task)
        matches = candidates.get(key) or []
        if len(matches) != 1:
            raise RuntimeError(
                f"ready work-unit release expected exactly one blocked Hermes task for packet {key[0]} / work unit {key[1]}, found {len(matches)}"
            )
        task_id, packet_id, work_unit_id = verify_ready_work_unit_release_candidate(
            payload=matches[0],
            plan_task=task,
            worker_assignee_prefix=args.worker_assignee_prefix,
        )
        verified.append((task, task_id, packet_id, work_unit_id))

    released_ready_work_unit_task_ids: dict[str, str] = {}
    released_packet_task_ids: dict[str, str] = {}
    release_reason = str(
        args.reason
        or "runtime_gate=blocked_event_verified_for_each_task; release_scope=ready_work_units_only; dispatch_separate=true"
    )
    required_markers = [
        "runtime_gate=blocked_event_verified_for_each_task",
        "release_scope=ready_work_units_only",
        "dispatch_separate=true",
    ]
    if not args.dry_run:
        for _task, task_id, packet_id, work_unit_id in verified:
            unblock_task(
                hermes_bin=args.hermes_bin,
                board=board,
                task_id=task_id,
                reason=release_reason,
                required_readback_markers=required_markers,
                runner=runner,
            )
            released_ready_work_unit_task_ids[work_unit_id] = task_id
            released_packet_task_ids[packet_id] = task_id

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "release-ready-work-units",
        "dry_run": bool(args.dry_run),
        "board": board,
        "materialization_plan_id": plan.get("plan_id"),
        "ready_work_unit_task_ids": {
            work_unit_id: task_id
            for _task, task_id, _packet_id, work_unit_id in verified
        },
        "packet_task_ids": {
            packet_id: task_id
            for _task, task_id, packet_id, _work_unit_id in verified
        },
        "released_ready_work_unit_task_ids": released_ready_work_unit_task_ids,
        "released_packet_task_ids": released_packet_task_ids,
        "runtime_gate": {
            **(plan.get("runtime_gate") if isinstance(plan.get("runtime_gate"), dict) else {}),
            "release_verified_task_count": len(verified),
            "dispatch_allowed_by_this_step": False,
            "native_dispatch_required_next": not args.dry_run,
            "complete_product_claim_allowed": False,
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
        },
        "hook": {
            "plan": plan,
            "materialization_result": materialization_result,
            "release_reason": release_reason,
            "no_shadow_dispatcher": True,
            "local_state_authority": False,
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def materialize(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    card_path = args.card.resolve()
    ledger_path = args.ledger.resolve()
    result = build_hook_result(
        card_path=card_path,
        from_status=args.from_status,
        to_status=args.to_status,
        receipt_path=args.receipt,
        worker_results_dir=args.worker_results_dir,
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

    card_body = card_path.read_text(encoding="utf-8")
    main_contract_digest = contract_digest(card_body)
    idempotency_contract: dict[str, Any] = {
        "digest_algorithm": CONTRACT_DIGEST_ALGORITHM,
        "canonicalization_version": CANONICALIZATION_VERSION,
        "volatile_fields_ignored": sorted(VOLATILE_CONTRACT_KEYS),
        "digest_scope": "main_card_body_and_stable_worker_packet_contract",
        "lineage_policy": IDEMPOTENCY_LINEAGE_POLICY,
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "main_task": {
            "idempotency_identity": {
                "card_id": card_id,
                "task_role": "main",
                "base_idempotency_key": main_base_idempotency_key(card_id),
            },
            "contract_digest": main_contract_digest,
            "idempotency_key": main_task_idempotency_key(card_id, card_body),
            "runtime_history_query_keys": [
                main_base_idempotency_key(card_id),
                main_task_idempotency_key(card_id, card_body),
            ],
            "previous_runtime_task_refs": [],
            "supersedes_idempotency_keys": [],
        },
        "worker_tasks": {},
    }

    main_task_id = create_task(
        hermes_bin=args.hermes_bin,
        board=args.board,
        title=f"OF {card_id} main gate",
        body=card_body,
        assignee=args.main_assignee,
        idempotency_key=idempotency_contract["main_task"]["idempotency_key"],
        created_by="overkill-factory",
        workspace=f"dir:{ROOT}",
        blocked=True,
        runner=runner,
    )
    worker_task_ids: dict[str, str] = {}
    review_promoted_worker_task_ids: dict[str, str] = {}
    recovery_promoted_worker_task_ids: dict[str, str] = {}
    recovery_retry_blocked_worker_task_ids: dict[str, str] = {}
    recovery_attempts: dict[str, dict[str, Any]] = {}
    downstream_promoted_worker_task_ids: dict[str, str] = {}
    downstream_authorizations = downstream_authorizations_by_worker(plan)
    for task in plan.get("worker_tasks", []):
        worker_id = str(task.get("worker_id") or "").strip()
        if not worker_id or task.get("status") == "not_required_by_current_card":
            continue
        packet = task.get("packet") or {}
        worker_task_contract = worker_materialization_contract(task)
        worker_idempotency_key = worker_task_idempotency_key(card_id, worker_id, worker_task_contract)
        worker_contract_digest = contract_digest(worker_task_contract)
        idempotency_contract["worker_tasks"][worker_id] = {
            "idempotency_identity": {
                "card_id": card_id,
                "worker_id": worker_id,
                "task_role": "worker",
                "base_idempotency_key": worker_base_idempotency_key(card_id, worker_id),
            },
            "contract_scope": "worker_task_materialization_contract",
            "contract_digest": worker_contract_digest,
            "idempotency_key": worker_idempotency_key,
            "runtime_history_query_keys": [
                worker_base_idempotency_key(card_id, worker_id),
                worker_idempotency_key,
            ],
            "previous_runtime_task_refs": [],
            "supersedes_idempotency_keys": [],
        }
        task_id = create_task(
            hermes_bin=args.hermes_bin,
            board=args.board,
            title=str(task.get("title") or f"OF {card_id} {worker_id}"),
            body=compact_json_argument(packet),
            assignee=args.worker_assignee_prefix + worker_id,
            idempotency_key=worker_idempotency_key,
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
        recovery_routes = [
            route
            for route in (packet.get("input_contract") or {}).get("recovery_routes", [])
            if isinstance(route, dict)
        ]
        authorized_recovery_routes = [
            route
            for route in recovery_routes
            if route.get("factory_owned_repair_allowed") is True and route.get("human_gate_required") is False
        ]
        recovery_authorized = bool(authorized_recovery_routes)
        if recovery_authorized and not args.worker_ready:
            route = authorized_recovery_routes[0]
            route_id = str(route.get("recovery_route_id") or "factory-recovery-route")
            route_digest = recovery_route_digest(route)
            fresh_review_ref = str(route.get("fresh_review_result_ref") or "fresh-review-required")
            shown_task = show_task(
                hermes_bin=args.hermes_bin,
                board=args.board,
                task_id=task_id,
                runner=runner,
            )
            task_status_value = task_status(shown_task)
            history_refs = recovery_attempt_history_refs(shown_task, route_id, route_digest)
            previous_attempts = len(history_refs)
            attempt_number = previous_attempts + 1
            max_attempts = retry_policy_max_attempts(route)
            recovery_attempts[worker_id] = {
                "recovery_route_id": route_id,
                "recovery_route_digest": route_digest,
                "worker_id": worker_id,
                "hermes_task_ref": task_id,
                "previous_attempts": previous_attempts,
                "attempt_number": attempt_number,
                "max_attempts": max_attempts,
                "attempt_source": "hermes_task_history",
                "history_refs": history_refs,
                "history_ref_count": len(history_refs),
                "task_status": task_status_value or "unknown",
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "attempted_this_run": False,
            }
            if task_status_value in ACTIVE_OR_TERMINAL_STATUSES:
                recovery_attempts[worker_id]["status"] = "already_active_no_new_attempt"
                continue
            if not has_history_source(shown_task):
                recovery_attempts[worker_id]["status"] = "history_unavailable"
                recovery_retry_blocked_worker_task_ids[worker_id] = task_id
                continue
            if attempt_number > max_attempts:
                recovery_attempts[worker_id]["status"] = "retry_limit_exceeded"
                recovery_retry_blocked_worker_task_ids[worker_id] = task_id
                continue
            recovery_attempts[worker_id]["status"] = "attempt_authorized"
            recovery_attempts[worker_id]["attempted_this_run"] = True
            unblock_task(
                hermes_bin=args.hermes_bin,
                board=args.board,
                task_id=task_id,
                reason=(
                    f"{RECOVERY_ATTEMPT_MARKER} route_id={route_id} "
                    f"route_digest={route_digest} "
                    f"attempt_number={attempt_number} max_attempts={max_attempts}; "
                    "Factory-owned recovery route authorized repair task; downstream remains gated until "
                    f"{fresh_review_ref} passes."
                ),
                required_readback_markers=[
                    RECOVERY_ATTEMPT_MARKER,
                    f"route_id={route_id}",
                    f"route_digest={route_digest}",
                    f"attempt_number={attempt_number}",
                    f"max_attempts={max_attempts}",
                ],
                runner=runner,
            )
            recovery_promoted_worker_task_ids[worker_id] = task_id
        downstream_authorized = (
            downstream_worker_ready_after_fresh_review(plan, task, downstream_authorizations)
            and worker_id not in review_promoted_worker_task_ids
            and worker_id not in recovery_promoted_worker_task_ids
        )
        if downstream_authorized and not args.worker_ready:
            auths = downstream_authorizations[worker_id]
            requirement_ids = [
                str(auth.get("requirement_id") or "").strip()
                for auth in auths
                if str(auth.get("requirement_id") or "").strip()
            ]
            review_refs = [
                str(auth.get("review_evidence_ref") or "").strip()
                for auth in auths
                if str(auth.get("review_evidence_ref") or "").strip()
            ]
            recovery_route_refs = [
                str(route_ref or "").strip()
                for auth in auths
                for route_ref in auth.get("recovery_route_refs") or []
                if str(route_ref or "").strip()
            ]
            recovery_route_digests = [
                str(route_digest or "").strip()
                for auth in auths
                for route_digest in auth.get("recovery_route_digests") or []
                if str(route_digest or "").strip()
            ]
            readback_markers = [
                f"authorized_worker_id={worker_id}",
                *[f"requirement_id={requirement_id}" for requirement_id in requirement_ids],
                *[f"review_evidence_ref={review_ref}" for review_ref in review_refs],
                *[f"recovery_route_ref={route_ref}" for route_ref in recovery_route_refs],
                *[f"recovery_route_digest={route_digest}" for route_digest in recovery_route_digests],
            ]
            unblock_task(
                hermes_bin=args.hermes_bin,
                board=args.board,
                task_id=task_id,
                reason=(
                    "Fresh PASS review authorized exact downstream worker "
                    f"{worker_id}; requirement(s): {', '.join(requirement_ids)}; "
                    f"review ref(s): {', '.join(review_refs)}; "
                    f"readback_markers: {' '.join(readback_markers)}; "
                    "main gate remains blocked."
                ),
                required_readback_markers=readback_markers,
                runner=runner,
            )
            downstream_promoted_worker_task_ids[worker_id] = task_id

    record_live_binding(
        ledger_path=ledger_path,
        card_id=card_id,
        board=args.board,
        main_task_id=main_task_id,
        worker_task_ids=worker_task_ids,
        idempotency_contract=idempotency_contract,
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
        "recovery_promoted_worker_task_ids": recovery_promoted_worker_task_ids,
        "recovery_retry_blocked_worker_task_ids": recovery_retry_blocked_worker_task_ids,
        "recovery_attempts": recovery_attempts,
        "downstream_promoted_worker_task_ids": downstream_promoted_worker_task_ids,
        "idempotency_contract": idempotency_contract,
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
    p_mat.add_argument("--worker-results-dir", type=Path)
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

    p_ready = sub.add_parser(
        "materialize-ready-work-units",
        help="Create blocked Hermes tasks from a ready work-unit materialization plan.",
    )
    p_ready.add_argument("--plan", type=Path, required=True)
    p_ready.add_argument("--board")
    p_ready.add_argument("--hermes-bin", default="hermes")
    p_ready.add_argument("--worker-assignee-prefix", default="")
    p_ready.add_argument("--workspace")
    p_ready.add_argument("--ensure-board", action="store_true")
    p_ready.add_argument("--dry-run", action="store_true")
    p_ready.add_argument("--route-readiness", type=Path)
    p_ready.add_argument("--out", type=Path)

    p_release = sub.add_parser(
        "release-ready-work-units",
        help="Release verified blocked ready work-unit tasks to ready without dispatching workers.",
    )
    p_release.add_argument("--plan", type=Path, required=True)
    p_release.add_argument("--materialization-result", type=Path, required=True)
    p_release.add_argument("--board")
    p_release.add_argument("--hermes-bin", default="hermes")
    p_release.add_argument("--worker-assignee-prefix", default="")
    p_release.add_argument("--route-readiness", type=Path, required=True)
    p_release.add_argument("--reason")
    p_release.add_argument("--dry-run", action="store_true")
    p_release.add_argument("--out", type=Path)

    p_route = sub.add_parser(
        "collect-route-readiness",
        help="Collect the public-safe Hermes worker route readiness manifest from read-only Hermes state.",
    )
    p_route.add_argument("--plan", type=Path)
    p_route.add_argument("--worker", action="append", default=[])
    p_route.add_argument("--hermes-bin", default="hermes")
    p_route.add_argument("--required-auth-provider", default="OpenAI Codex")
    p_route.add_argument("--credential-evidence-ref", default="external:hermes-status-auth-provider-ready")
    p_route.add_argument("--ledger-ref", default="external:hermes-worker-route-readiness-ledger")
    p_route.add_argument("--out", type=Path)

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
        elif args.command == "materialize-ready-work-units":
            envelope = materialize_ready_work_units(args)
        elif args.command == "release-ready-work-units":
            envelope = release_ready_work_units(args)
        elif args.command == "collect-route-readiness":
            envelope = collect_route_readiness(args)
        elif args.command == "enforce-done":
            envelope = enforce_done(args)
        elif args.command == "dispatch":
            envelope = dispatch(args)
        else:
            raise RuntimeError(f"unsupported command: {args.command}")
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
