#!/usr/bin/env python3
"""Materialize Overkill Factory worker gates in a real Hermes Kanban board."""

from __future__ import annotations

import argparse
import copy
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
READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES = {"done", "complete", "completed"}
READY_WORK_UNIT_RELEASE_QUERY_STATUSES = ["blocked", "done"]
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
READY_WORK_UNIT_DIRECT_BODY_LIMIT = 12000
READY_WORK_UNIT_CONTEXT_TRANSPORT_MODE = "hermes_comment_chunks.v1"
READY_WORK_UNIT_CONTEXT_CHUNK_AUTHOR = "overkill-factory-context"
READY_WORK_UNIT_CONTEXT_CHUNK_SIZE = 5000
READY_WORK_UNIT_SUPERSESSION_MARKER = "ready_work_unit_superseded"
READY_WORK_UNIT_RECOVERY_AUTHOR = "overkill-factory-recovery"
READY_WORK_UNIT_RECONCILIATION_AUTHOR = "overkill-factory-reconciliation"
READY_WORK_UNIT_RELEASE_REQUIRED_MARKERS = [
    "runtime_gate=blocked_event_verified_for_each_task",
    "release_scope=ready_work_units_only",
    "dispatch_separate=true",
]
READY_WORK_UNIT_REPAIR_COMPLETED_MARKERS = ["ready_work_unit_repair_completed", "repair completed"]
READY_WORK_UNIT_REPAIR_REVIEW_PASSED_MARKERS = ["ready_work_unit_repair_review_passed"]
READY_WORK_UNIT_RETRY_AUTHORIZED_MARKERS = ["ready_work_unit_retry_authorized"]
READY_WORK_UNIT_DONE_AUTHORIZED_MARKERS = ["ready_work_unit_done_authorized"]
READY_WORK_UNIT_DONE_DEFINITION_SATISFIED_MARKERS = ["ready_work_unit_done_definition_satisfied"]
READY_WORK_UNIT_HUMAN_GATE_MARKERS = ["human_gate_required", "human-gate-required"]
READY_WORK_UNIT_RECONCILIATION_RETRY_READBACK_MARKERS = [
    "ready_work_unit_retry_authorized",
    "post_release_ready_work_unit",
]
READY_WORK_UNIT_RECONCILIATION_DONE_READBACK_MARKERS = [
    "ready_work_unit_done_authorized",
    "post_release_ready_work_unit",
]
READY_WORK_UNIT_POST_REPAIR_REVIEW_REQUIRED_MARKER = "ready_work_unit_post_repair_review_required"
READY_WORK_UNIT_POST_REPAIR_REVIEW_CREATED_MARKER = "ready_work_unit_post_repair_review_task_created"
READY_WORK_UNIT_POST_REPAIR_REVIEW_RESULT_MARKER = "ready_work_unit_post_repair_review_result"
READY_WORK_UNIT_POST_REPAIR_AUTHORITY_REQUIRED_MARKER = "ready_work_unit_post_repair_authority_required"
READY_WORK_UNIT_POST_REPAIR_AUTHORITY_CREATED_MARKER = "ready_work_unit_post_repair_authority_task_created"
READY_WORK_UNIT_POST_REPAIR_AUTHORITY_RESULT_MARKER = "ready_work_unit_post_repair_authority_result"
READY_WORK_UNIT_SUPERSEDED_PARENT_UNLINKED_MARKER = "ready_work_unit_superseded_parent_unlinked"
READY_WORK_UNIT_REVIEW_CLOSEOUT_MARKER = "ready_work_unit_review_closeout"
READY_WORK_UNIT_REVIEW_PASSED_MARKER = "ready_work_unit_review_passed"
READY_WORK_UNIT_REVIEW_CLOSEOUT_READBACK_MARKERS = [
    READY_WORK_UNIT_REVIEW_CLOSEOUT_MARKER,
    READY_WORK_UNIT_REVIEW_PASSED_MARKER,
]
PRODUCT_CREATION_CLOSEOUT_MARKER = "product_creation_run_closeout"
PRODUCT_CREATION_CLOSEOUT_NEXT_ROUTE_MARKER = "product_creation_closeout_next_route"
PRODUCT_CREATION_CLOSEOUT_READBACK_MARKERS = [
    PRODUCT_CREATION_CLOSEOUT_MARKER,
    PRODUCT_CREATION_CLOSEOUT_NEXT_ROUTE_MARKER,
]
RELEASE_READINESS_REVIEW_CLOSEOUT_MARKER = "release_readiness_review_closeout"
RELEASE_READINESS_REVIEW_PASSED_MARKER = "release_readiness_review_passed"
RELEASE_READINESS_REVIEW_BLOCKED_MARKER = "release_readiness_review_blocked"
RELEASE_READINESS_REVIEW_PARENT_EDGE_REPAIRED_MARKER = "release_readiness_review_parent_edge_repaired"
RELEASE_READINESS_REVIEW_CLOSEOUT_READBACK_MARKERS = [
    RELEASE_READINESS_REVIEW_CLOSEOUT_MARKER,
    RELEASE_READINESS_REVIEW_PASSED_MARKER,
]
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
    return subprocess.run(  # nosec B603
        argv,
        text=True,
        capture_output=True,
        env=env,
        encoding="utf-8",
        errors="replace",
    )


def safe_command_for_error(argv: list[str]) -> str:
    redacted: list[str] = []
    redact_next = False
    for arg in argv:
        if redact_next:
            digest = hashlib.sha256(str(arg).encode("utf-8", errors="replace")).hexdigest()[:12]
            redacted.append(f"<redacted len={len(str(arg))} sha256={digest}>")
            redact_next = False
            continue
        redacted.append(str(arg))
        if arg == "--body":
            redact_next = True
            continue
        if len(str(arg)) > 500:
            digest = hashlib.sha256(str(arg).encode("utf-8", errors="replace")).hexdigest()[:12]
            redacted[-1] = f"<redacted-long-arg len={len(str(arg))} sha256={digest}>"
    return " ".join(redacted)


def run_checked(argv: list[str], runner: Runner = default_runner) -> subprocess.CompletedProcess[str]:
    completed = runner(argv)
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed: "
            + safe_command_for_error(argv)
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


def task_run_records(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    runner: Runner = default_runner,
) -> list[dict[str, Any]]:
    completed = run_checked(hermes_kanban(hermes_bin, board, "runs", task_id, "--json"), runner)
    payload = parse_json_output(completed.stdout, command="hermes kanban runs --json")
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        runs = payload.get("runs")
        if isinstance(runs, list):
            return [item for item in runs if isinstance(item, dict)]
    return []


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


def task_readback_comments(payload: dict[str, Any]) -> list[dict[str, Any]]:
    comments = payload.get("comments")
    if isinstance(comments, list):
        return [comment for comment in comments if isinstance(comment, dict)]
    task = payload.get("task")
    if isinstance(task, dict):
        nested = task.get("comments")
        if isinstance(nested, list):
            return [comment for comment in nested if isinstance(comment, dict)]
    return []


def task_readback_parents(payload: dict[str, Any]) -> list[str]:
    raw_parents = payload.get("parents")
    if not isinstance(raw_parents, list):
        task = payload.get("task")
        raw_parents = task.get("parents") if isinstance(task, dict) else []
    parents: list[str] = []
    for parent in raw_parents if isinstance(raw_parents, list) else []:
        if isinstance(parent, dict):
            parent_id = str(parent.get("id") or parent.get("task_id") or "").strip()
        else:
            parent_id = str(parent or "").strip()
        if parent_id:
            parents.append(parent_id)
    return parents


def task_readback_children(payload: dict[str, Any]) -> list[str]:
    raw_children = payload.get("children")
    if not isinstance(raw_children, list):
        task = payload.get("task")
        raw_children = task.get("children") if isinstance(task, dict) else []
    children: list[str] = []
    for child in raw_children if isinstance(raw_children, list) else []:
        if isinstance(child, dict):
            child_id = str(child.get("id") or child.get("task_id") or "").strip()
        else:
            child_id = str(child or "").strip()
        if child_id:
            children.append(child_id)
    return children


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
    task = task_readback_task(payload)
    if task.get("current_run_id") or task.get("run_id"):
        markers.append("current_run_id")
    if task.get("worker_pid"):
        markers.append("worker_pid")
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


def task_has_ready_work_unit_supersession(payload: dict[str, Any]) -> bool:
    for comment in task_readback_comments(payload):
        if str(comment.get("author") or "").strip() != READY_WORK_UNIT_RECOVERY_AUTHOR:
            continue
        raw_body = str(comment.get("body") or comment.get("text") or comment.get("content") or "")
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            continue
        if isinstance(body, dict) and body.get("marker") == READY_WORK_UNIT_SUPERSESSION_MARKER:
            return True
    for event in task_readback_events(payload):
        if not isinstance(event, dict):
            continue
        event_body = event.get("payload")
        if isinstance(event_body, dict) and event_body.get("marker") == READY_WORK_UNIT_SUPERSESSION_MARKER:
            return True
    return False


def ready_work_unit_contamination_markers(payload: dict[str, Any]) -> list[str]:
    status = task_readback_status(payload)
    if status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
        return []
    if task_has_ready_work_unit_supersession(payload):
        return []
    return pre_dispatch_activity_markers(payload)


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
    body = ready_work_unit_body(payload, task_id=task_id)
    if str(body.get("packet_id") or "").strip() != expected_packet_id:
        raise RuntimeError(f"Hermes task {task_id} body readback does not match ready work-unit packet")
    ensure_no_pre_dispatch_activity(payload, task_id=task_id)


def ready_work_unit_readback_contract_error(
    *,
    payload: dict[str, Any],
    task_id: str,
    expected_assignee: str,
    expected_packet_id: str,
) -> str | None:
    try:
        ensure_ready_work_unit_readback_contract(
            payload=payload,
            task_id=task_id,
            expected_assignee=expected_assignee,
            expected_packet_id=expected_packet_id,
        )
    except RuntimeError as exc:
        return str(exc)
    return None


def ready_work_unit_body_transport_comments(*, payload: dict[str, Any], task_id: str, manifest: dict[str, Any]) -> list[str]:
    transport = manifest.get("context_transport")
    if not isinstance(transport, dict):
        raise RuntimeError(f"Hermes task {task_id} body transport manifest is missing")
    chunk_count = int(transport.get("chunk_count") or 0)
    expected_digest = str(transport.get("sha256") or "").strip()
    if chunk_count <= 0 or not expected_digest:
        raise RuntimeError(f"Hermes task {task_id} body transport manifest is incomplete")

    chunks_by_index: dict[int, str] = {}
    for comment in task_readback_comments(payload):
        if str(comment.get("author") or "").strip() != READY_WORK_UNIT_CONTEXT_CHUNK_AUTHOR:
            continue
        raw_body = str(comment.get("body") or comment.get("text") or comment.get("content") or "")
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            continue
        if not isinstance(body, dict):
            continue
        if body.get("context_transport") != READY_WORK_UNIT_CONTEXT_TRANSPORT_MODE:
            continue
        if str(body.get("packet_id") or "").strip() != str(manifest.get("packet_id") or "").strip():
            continue
        if str(body.get("sha256") or "").strip() != expected_digest:
            continue
        raw_index = body.get("chunk_index")
        index = int(raw_index) if raw_index is not None else -1
        if index < 0 or index >= chunk_count:
            raise RuntimeError(f"Hermes task {task_id} body transport chunk index is out of range")
        if index in chunks_by_index:
            raise RuntimeError(f"Hermes task {task_id} body transport has duplicate chunk {index}")
        chunks_by_index[index] = str(body.get("data") or "")

    missing = [index for index in range(chunk_count) if index not in chunks_by_index]
    if missing:
        raise RuntimeError(f"Hermes task {task_id} body transport is missing chunks: {missing}")
    chunks = [chunks_by_index[index] for index in range(chunk_count)]
    joined = "".join(chunks)
    actual_digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    if actual_digest != expected_digest:
        raise RuntimeError(f"Hermes task {task_id} body transport sha256 does not match manifest")
    return chunks


def ready_work_unit_body_from_transport(*, payload: dict[str, Any], task_id: str, manifest: dict[str, Any]) -> dict[str, Any]:
    chunks = ready_work_unit_body_transport_comments(payload=payload, task_id=task_id, manifest=manifest)
    try:
        body = json.loads("".join(chunks))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Hermes task {task_id} reconstructed ready work-unit body is not valid JSON") from exc
    if not isinstance(body, dict):
        raise RuntimeError(f"Hermes task {task_id} reconstructed ready work-unit body is not a JSON object")
    return body


def ready_work_unit_body(payload: dict[str, Any], *, task_id: str) -> dict[str, Any]:
    try:
        body = json.loads(task_readback_body(payload))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Hermes task {task_id} body readback is not valid JSON") from exc
    if not isinstance(body, dict):
        raise RuntimeError(f"Hermes task {task_id} body readback is not a JSON object")
    transport = body.get("context_transport")
    if isinstance(transport, dict):
        mode = str(transport.get("mode") or "").strip()
        if mode == READY_WORK_UNIT_CONTEXT_TRANSPORT_MODE:
            return ready_work_unit_body_from_transport(payload=payload, task_id=task_id, manifest=body)
        raise RuntimeError(f"Hermes task {task_id} has unsupported ready work-unit body transport: {mode}")
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


def history_contains_any_marker(payload: dict[str, Any], markers: list[str]) -> bool:
    return any(history_contains_markers(payload, [marker]) for marker in markers if marker.strip())


def history_contains_all_markers_anywhere(payload: dict[str, Any], markers: list[str]) -> bool:
    return all(history_contains_any_marker(payload, [marker]) for marker in markers if marker.strip())


def task_has_ready_work_unit_release_record(payload: dict[str, Any]) -> bool:
    return history_contains_markers(
        payload,
        READY_WORK_UNIT_RELEASE_REQUIRED_MARKERS,
    ) or task_has_unblocked_event(
        payload,
        required_markers=READY_WORK_UNIT_RELEASE_REQUIRED_MARKERS,
    )


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


def promote_task(
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
    run_checked(hermes_kanban(hermes_bin, board, "promote", task_id, reason), runner)
    shown = run_checked(hermes_kanban(hermes_bin, board, "show", task_id, "--json"), runner)
    try:
        payload = json.loads(shown.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("Hermes show --json did not return JSON while verifying promote event") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Hermes show --json did not return an object while verifying promote event")
    status = task_readback_status(payload)
    if status not in {"ready", "running", "done"}:
        raise RuntimeError(f"Hermes task {task_id} was not promoted into an executable state")
    if required_readback_markers and not history_contains_all_markers_anywhere(payload, required_readback_markers):
        raise RuntimeError(f"Hermes task {task_id} promote readback is missing required retry markers")


def unlink_task_dependency(
    *,
    hermes_bin: str,
    board: str,
    parent_task_id: str,
    child_task_id: str,
    work_unit_id: str,
    authority_task_ref: str | None,
    runner: Runner = default_runner,
) -> bool:
    child_payload = show_task(hermes_bin=hermes_bin, board=board, task_id=child_task_id, runner=runner)
    if parent_task_id not in task_readback_parents(child_payload):
        return False
    run_checked(hermes_kanban(hermes_bin, board, "unlink", parent_task_id, child_task_id), runner)
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "comment",
            "--author",
            READY_WORK_UNIT_RECONCILIATION_AUTHOR,
            child_task_id,
            compact_json_argument(
                {
                    "marker": READY_WORK_UNIT_SUPERSEDED_PARENT_UNLINKED_MARKER,
                    "work_unit_id": work_unit_id,
                    "superseded_parent_ref": parent_task_id,
                    "authority_task_ref": authority_task_ref,
                    "reason": "newer post-repair authority selected retry/done path; stale blocked review parent no longer owns execution gating",
                    "runtime_authority": "hermes_kanban",
                    "local_state_authority": False,
                    "complete_product_claim_allowed": False,
                }
            ),
        ),
        runner,
    )
    readback = show_task(hermes_bin=hermes_bin, board=board, task_id=child_task_id, runner=runner)
    if parent_task_id in task_readback_parents(readback):
        raise RuntimeError(f"Hermes task {child_task_id} still has superseded parent {parent_task_id} after unlink")
    return True


def complete_task(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    result: str,
    summary: str,
    metadata: dict[str, Any],
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
                READY_WORK_UNIT_RECONCILIATION_AUTHOR,
                task_id,
                compact_json_argument(metadata),
            ),
            runner,
        )
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "complete",
            task_id,
            "--result",
            result,
            "--summary",
            summary,
            "--metadata",
            compact_json_argument(metadata),
        ),
        runner,
    )
    payload = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    if task_readback_status(payload) not in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
        raise RuntimeError(f"Hermes task {task_id} is not durably completed after complete command")
    if required_readback_markers and not history_contains_all_markers_anywhere(payload, required_readback_markers):
        raise RuntimeError(f"Hermes task {task_id} completion readback lacks required reconciliation markers")


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


def create_blocked_task_before_assignment(
    *,
    hermes_bin: str,
    board: str,
    title: str,
    body: str,
    assignee: str,
    idempotency_key: str,
    created_by: str,
    workspace: str,
    blocked_reason: str,
    runner: Runner = default_runner,
) -> str:
    ensure_non_empty_body(body)
    task_id = parse_task_id(
        run_checked(
            hermes_kanban(
                hermes_bin,
                board,
                "create",
                title,
                "--body",
                body,
                "--idempotency-key",
                idempotency_key,
                "--created-by",
                created_by,
                "--workspace",
                workspace,
                "--json",
            ),
            runner,
        ).stdout
    )
    ensure_blocked_event(
        hermes_bin=hermes_bin,
        board=board,
        task_id=task_id,
        reason=blocked_reason,
        runner=runner,
    )
    blocked_task = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    ensure_no_pre_dispatch_activity(blocked_task, task_id=task_id)
    if task_readback_status(blocked_task) != "blocked":
        raise RuntimeError(f"Hermes task {task_id} is not blocked before assignment")
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "assign",
            task_id,
            assignee,
        ),
        runner,
    )
    assigned_task = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    ensure_no_pre_dispatch_activity(assigned_task, task_id=task_id)
    if task_readback_status(assigned_task) != "blocked":
        raise RuntimeError(f"Hermes task {task_id} is not blocked after assignment")
    return task_id


def ready_work_unit_create_body_and_chunks(body_contract: dict[str, Any]) -> tuple[str, list[str]]:
    full_body = compact_json_argument(body_contract)
    if len(full_body) <= READY_WORK_UNIT_DIRECT_BODY_LIMIT:
        return full_body, []

    digest = hashlib.sha256(full_body.encode("utf-8")).hexdigest()
    chunks = [
        full_body[index : index + READY_WORK_UNIT_CONTEXT_CHUNK_SIZE]
        for index in range(0, len(full_body), READY_WORK_UNIT_CONTEXT_CHUNK_SIZE)
    ]
    manifest = {
        "packet_id": body_contract.get("packet_id"),
        "packet_type": body_contract.get("packet_type"),
        "work_unit_id": body_contract.get("work_unit_id"),
        "context_transport": {
            "mode": READY_WORK_UNIT_CONTEXT_TRANSPORT_MODE,
            "author": READY_WORK_UNIT_CONTEXT_CHUNK_AUTHOR,
            "encoding": "utf-8-json-chunks",
            "chunk_count": len(chunks),
            "sha256": digest,
            "payload_type": "ready_work_unit_execution_request",
            "instruction": (
                "Reconstruct the full ready work-unit packet from durable Hermes comments "
                "before execution; block if chunks are missing or digest mismatches."
            ),
        },
    }
    comment_bodies = [
        compact_json_argument(
            {
                "context_transport": READY_WORK_UNIT_CONTEXT_TRANSPORT_MODE,
                "packet_id": body_contract.get("packet_id"),
                "work_unit_id": body_contract.get("work_unit_id"),
                "chunk_index": index,
                "chunk_count": len(chunks),
                "sha256": digest,
                "data": chunk,
            }
        )
        for index, chunk in enumerate(chunks)
    ]
    return compact_json_argument(manifest), comment_bodies


def post_ready_work_unit_context_chunks(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    chunks: list[str],
    runner: Runner = default_runner,
) -> None:
    for chunk in chunks:
        run_checked(
            hermes_kanban(
                hermes_bin,
                board,
                "comment",
                "--author",
                READY_WORK_UNIT_CONTEXT_CHUNK_AUTHOR,
                task_id,
                chunk,
            ),
            runner,
        )


def load_ready_work_unit_materialization_plan(path: Path) -> dict[str, Any]:
    plan = load_json(path)
    factoryctl = load_factoryctl()
    errors = factoryctl.validate_ready_work_unit_hermes_materialization_plan(plan)
    if errors:
        raise RuntimeError("invalid ready work-unit Hermes materialization plan: " + "; ".join(errors))
    return plan


def load_product_creation_plan(path: Path) -> dict[str, Any]:
    plan = load_json(path)
    factoryctl = load_factoryctl()
    errors = factoryctl.validate_product_creation_plan(plan)
    if errors:
        raise RuntimeError("invalid product creation plan: " + "; ".join(errors))
    return plan


def ensure_public_safe_optional_ref(value: str | None, *, field: str) -> str | None:
    ref = str(value or "").strip()
    if not ref:
        return None
    factoryctl = load_factoryctl()
    _sanitized, redaction = factoryctl.sanitize_public_ref(ref)
    if redaction is not None:
        raise RuntimeError(f"{field} must be public-safe")
    return ref


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
    create_body, context_chunks = ready_work_unit_create_body_and_chunks(body_contract)
    ensure_non_empty_body(create_body)
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
                create_body,
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
    post_ready_work_unit_context_chunks(
        hermes_bin=hermes_bin,
        board=board,
        task_id=task_id,
        chunks=context_chunks,
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


def verify_ready_work_unit_identity(
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
    if task_readback_assignee(payload) != expected_assignee:
        raise RuntimeError(f"Hermes task {task_id} assignee readback does not match target profile")
    body = ready_work_unit_body(payload, task_id=task_id)
    if str(body.get("packet_id") or "").strip() != packet_id:
        raise RuntimeError(f"Hermes task {task_id} body readback does not match ready work-unit packet")
    if str(body.get("work_unit_id") or "").strip() != work_unit_id:
        raise RuntimeError(f"Hermes task {task_id} body readback does not match ready work-unit id")
    if str(body.get("packet_type") or "").strip() != "ready_work_unit_execution_request":
        raise RuntimeError(f"Hermes task {task_id} body readback is not a ready work-unit execution request")
    return task_id, packet_id, work_unit_id


def ready_work_unit_dependencies(tasks: list[dict[str, Any]]) -> dict[str, list[str]]:
    work_unit_ids = {
        str(task.get("work_unit_id") or "").strip()
        for task in tasks
        if str(task.get("work_unit_id") or "").strip()
    }
    dependencies: dict[str, set[str]] = {work_unit_id: set() for work_unit_id in work_unit_ids}
    for task in tasks:
        body = task.get("body_contract") if isinstance(task.get("body_contract"), dict) else {}
        context_packet = body.get("work_unit_context_packet") if isinstance(body.get("work_unit_context_packet"), dict) else {}
        embedded = context_packet.get("embedded_payloads") if isinstance(context_packet.get("embedded_payloads"), dict) else {}
        product_plan = embedded.get("product_creation_plan") if isinstance(embedded.get("product_creation_plan"), dict) else {}
        graph = product_plan.get("dependency_graph") if isinstance(product_plan.get("dependency_graph"), list) else []
        for edge in graph:
            if not isinstance(edge, dict):
                continue
            source = str(edge.get("from") or "").strip()
            target = str(edge.get("to") or "").strip()
            if source in work_unit_ids and target in work_unit_ids:
                dependencies.setdefault(target, set()).add(source)
    if any(dependencies.values()):
        return {work_unit_id: sorted(deps) for work_unit_id, deps in sorted(dependencies.items())}

    for task in tasks:
        work_unit_id = str(task.get("work_unit_id") or "").strip()
        body = task.get("body_contract") if isinstance(task.get("body_contract"), dict) else {}
        refs = body.get("dependency_refs") if isinstance(body.get("dependency_refs"), list) else []
        for ref in refs:
            dep = str(ref or "").strip()
            if dep in work_unit_ids and dep != work_unit_id:
                dependencies.setdefault(work_unit_id, set()).add(dep)
    return {work_unit_id: sorted(deps) for work_unit_id, deps in sorted(dependencies.items())}


def ready_work_unit_readbacks_by_status(
    *,
    hermes_bin: str,
    board: str,
    statuses: list[str],
    include_superseded: bool = False,
    runner: Runner = default_runner,
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    candidates: dict[tuple[str, str], list[dict[str, Any]]] = {}
    seen_task_ids: set[str] = set()
    for status in statuses:
        for record in list_tasks_by_status(hermes_bin=hermes_bin, board=board, status=status, runner=runner):
            task_id = str(record.get("task_id") or record.get("id") or "").strip()
            if not task_id or task_id in seen_task_ids:
                continue
            seen_task_ids.add(task_id)
            payload = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
            try:
                body = ready_work_unit_body(payload, task_id=task_id)
            except RuntimeError:
                continue
            if not include_superseded and task_has_ready_work_unit_supersession(payload):
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

    candidates = ready_work_unit_readbacks_by_status(
        hermes_bin=args.hermes_bin,
        board=board,
        statuses=READY_WORK_UNIT_RELEASE_QUERY_STATUSES,
        runner=runner,
    )
    verified: list[tuple[dict[str, Any], str, str, str, str]] = []
    post_release_blocked: dict[str, str] = {}
    for task in tasks:
        key = expected_ready_work_unit_key(task)
        matches = candidates.get(key) or []
        if len(matches) != 1:
            raise RuntimeError(
                f"ready work-unit release expected exactly one blocked or completed Hermes task for packet {key[0]} / work unit {key[1]}, found {len(matches)}"
            )
        status = task_readback_status(matches[0])
        if status == "blocked":
            if task_has_ready_work_unit_release_record(matches[0]):
                task_id, packet_id, work_unit_id = verify_ready_work_unit_identity(
                    payload=matches[0],
                    plan_task=task,
                    worker_assignee_prefix=args.worker_assignee_prefix,
                )
                if not task_has_blocked_event(matches[0]):
                    raise RuntimeError(f"Hermes task {task_id} is post-release blocked but lacks a blocked event")
                status = "blocked_after_release"
                post_release_blocked[work_unit_id] = task_id
            else:
                task_id, packet_id, work_unit_id = verify_ready_work_unit_release_candidate(
                    payload=matches[0],
                    plan_task=task,
                    worker_assignee_prefix=args.worker_assignee_prefix,
                )
        elif status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
            task_id, packet_id, work_unit_id = verify_ready_work_unit_identity(
                payload=matches[0],
                plan_task=task,
                worker_assignee_prefix=args.worker_assignee_prefix,
            )
        else:
            raise RuntimeError(f"Hermes task for ready work unit {key[1]} is not releasable or satisfied: {status}")
        verified.append((task, task_id, packet_id, work_unit_id, status))

    dependencies = ready_work_unit_dependencies(tasks)
    status_by_work_unit = {work_unit_id: status for _task, _task_id, _packet_id, work_unit_id, status in verified}
    satisfied_work_unit_ids = sorted(
        work_unit_id
        for work_unit_id, status in status_by_work_unit.items()
        if status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES
    )
    dependency_blockers: dict[str, list[str]] = {}
    eligible: list[tuple[dict[str, Any], str, str, str, str]] = []
    for item in verified:
        _task, _task_id, _packet_id, work_unit_id, status = item
        if status != "blocked":
            continue
        blockers = [
            dep
            for dep in dependencies.get(work_unit_id, [])
            if status_by_work_unit.get(dep) not in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES
        ]
        if blockers:
            dependency_blockers[work_unit_id] = blockers
            continue
        eligible.append(item)

    released_ready_work_unit_task_ids: dict[str, str] = {}
    released_packet_task_ids: dict[str, str] = {}
    release_reason = str(
        args.reason
        or "runtime_gate=blocked_event_verified_for_each_task; release_scope=ready_work_units_only; dispatch_separate=true"
    )
    required_markers = READY_WORK_UNIT_RELEASE_REQUIRED_MARKERS
    if not args.dry_run:
        for _task, task_id, packet_id, work_unit_id, _status in eligible:
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
            for _task, task_id, _packet_id, work_unit_id, _status in verified
        },
        "packet_task_ids": {
            packet_id: task_id
            for _task, task_id, packet_id, _work_unit_id, _status in verified
        },
        "released_ready_work_unit_task_ids": released_ready_work_unit_task_ids,
        "released_packet_task_ids": released_packet_task_ids,
        "release_wave": {
            "eligible_work_unit_ids": sorted(work_unit_id for _task, _task_id, _packet_id, work_unit_id, _status in eligible),
            "held_work_unit_ids": sorted(dependency_blockers.keys()),
            "satisfied_work_unit_ids": satisfied_work_unit_ids,
            "post_release_blocked_work_unit_ids": sorted(post_release_blocked.keys()),
            "post_release_reconciliation_required_next": bool(post_release_blocked),
            "post_release_reconciliation_command": "reconcile-ready-work-units",
            "dependency_blockers": {key: dependency_blockers[key] for key in sorted(dependency_blockers)},
        },
        "runtime_gate": {
            **(plan.get("runtime_gate") if isinstance(plan.get("runtime_gate"), dict) else {}),
            "release_verified_task_count": len(verified),
            "release_eligible_task_count": len(eligible),
            "release_held_task_count": len(dependency_blockers) + len(post_release_blocked),
            "release_satisfied_task_count": len(satisfied_work_unit_ids),
            "post_release_blocked_task_count": len(post_release_blocked),
            "dispatch_allowed_by_this_step": False,
            "native_dispatch_required_next": bool(released_ready_work_unit_task_ids),
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


def ready_work_unit_post_release_reconciliation_flags(payload: dict[str, Any]) -> dict[str, bool]:
    repair_completed = history_contains_any_marker(payload, READY_WORK_UNIT_REPAIR_COMPLETED_MARKERS)
    repair_review_passed = history_contains_all_markers_anywhere(payload, READY_WORK_UNIT_REPAIR_REVIEW_PASSED_MARKERS)
    retry_authorized = history_contains_all_markers_anywhere(payload, READY_WORK_UNIT_RETRY_AUTHORIZED_MARKERS)
    done_authorized = history_contains_all_markers_anywhere(payload, READY_WORK_UNIT_DONE_AUTHORIZED_MARKERS)
    done_definition_satisfied = history_contains_all_markers_anywhere(
        payload,
        READY_WORK_UNIT_DONE_DEFINITION_SATISFIED_MARKERS,
    )
    human_gate_required = history_contains_any_marker(payload, READY_WORK_UNIT_HUMAN_GATE_MARKERS)
    return {
        "repair_completed": repair_completed,
        "repair_review_passed": repair_review_passed,
        "retry_authorized": retry_authorized,
        "done_authorized": done_authorized,
        "done_definition_satisfied": done_definition_satisfied,
        "human_gate_required": human_gate_required,
    }


def classify_ready_work_unit_post_release_reconciliation(payload: dict[str, Any]) -> dict[str, Any]:
    status = task_readback_status(payload)
    release_record_seen = task_has_ready_work_unit_release_record(payload)
    flags = ready_work_unit_post_release_reconciliation_flags(payload)
    decision = "not_post_release_blocked"
    next_action = "release-ready-work-units must release the ready work unit before post-release reconciliation"
    actionable = False

    if status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
        decision = "already_satisfied"
        next_action = "no reconciliation needed"
    elif status != "blocked":
        decision = "wait_for_runtime_state"
        next_action = f"task is {status or 'unknown'}, not blocked"
    elif not release_record_seen:
        decision = "not_released_yet"
        next_action = "run release-ready-work-units when dependency blockers are satisfied"
    elif not task_has_blocked_event(payload):
        decision = "invalid_blocked_readback"
        next_action = "preserve task and repair missing Hermes blocked-event evidence before retry"
    elif flags["human_gate_required"]:
        decision = "human_gate_required"
        next_action = "wait for explicit human gate; no automatic retry or completion"
    elif flags["repair_completed"] and flags["repair_review_passed"] and flags["done_authorized"] and flags["done_definition_satisfied"]:
        decision = "complete_parent"
        next_action = "complete the parent ready work unit through Hermes complete"
        actionable = True
    elif flags["repair_completed"] and flags["repair_review_passed"] and flags["retry_authorized"]:
        decision = "retry_parent"
        next_action = "unblock parent ready work unit for another Hermes worker attempt"
        actionable = True
    elif flags["repair_completed"] and flags["repair_review_passed"]:
        decision = "awaiting_retry_or_done_authority"
        next_action = "repair review passed, but no explicit retry or done authority marker exists"
    elif flags["repair_completed"]:
        decision = "awaiting_repair_review"
        next_action = "repair evidence exists, but independent repair review is not complete"
    else:
        decision = "awaiting_repair"
        next_action = "create or wait for factory repair and independent review evidence"

    return {
        "status": status,
        "release_record_seen": release_record_seen,
        "decision": decision,
        "next_action": next_action,
        "actionable_by_adapter": actionable,
        "complete_product_claim_allowed": False,
        **flags,
    }


def ready_work_unit_post_repair_review_idempotency_key(*, plan_task: dict[str, Any], parent_task_id: str) -> str:
    base = str(plan_task.get("idempotency_key") or "").strip()
    if not base:
        _packet_id, work_unit_id = expected_ready_work_unit_key(plan_task)
        base = f"overkill:ready-work-unit:{work_unit_id}"
    digest = idempotency_digest_fragment(
        contract_digest(
            {
                "base_idempotency_key": base,
                "parent_task_id": parent_task_id,
                "route": "post_repair_review",
                "version": "v1",
            }
        )
    )
    return f"{base}:post-repair-review:{digest}"


def ready_work_unit_post_repair_review_body(
    *,
    plan_task: dict[str, Any],
    parent_task_id: str,
    packet_id: str,
    work_unit_id: str,
) -> dict[str, Any]:
    done_definition = {}
    body_contract = plan_task.get("body_contract") if isinstance(plan_task.get("body_contract"), dict) else {}
    if isinstance(body_contract.get("done_definition"), dict):
        done_definition = body_contract["done_definition"]
    elif isinstance(body_contract.get("work_unit_context_packet"), dict):
        embedded_payloads = body_contract["work_unit_context_packet"].get("embedded_payloads", {})
        embedded_payloads = embedded_payloads if isinstance(embedded_payloads, dict) else {}
        current = embedded_payloads.get("current_work_unit", {})
        if isinstance(current, dict) and isinstance(current.get("done_definition"), dict):
            done_definition = current["done_definition"]
    return {
        "packet_type": "ready_work_unit_post_repair_review_request",
        "marker": READY_WORK_UNIT_POST_REPAIR_REVIEW_REQUIRED_MARKER,
        "parent_packet_id": packet_id,
        "parent_work_unit_id": work_unit_id,
        "parent_task_ref": parent_task_id,
        "reviewer_role": "independent-reviewer",
        "review_scope": "post_repair_result_only",
        "review_must_not_approve": [
            "complete_product",
            "release",
            "deployment",
            "customer_ready",
            "security_gate",
            "human_gate",
        ],
        "required_positive_outcomes": [
            {
                "markers": [
                    "ready_work_unit_repair_review_passed",
                    "ready_work_unit_retry_authorized",
                ],
                "meaning": "repair is accepted and parent may be retried by Hermes reconciliation",
            },
            {
                "markers": [
                    "ready_work_unit_repair_review_passed",
                    "ready_work_unit_done_authorized",
                    "ready_work_unit_done_definition_satisfied",
                ],
                "meaning": "parent ready work unit may be completed, not the whole product",
            },
            {
                "markers": ["human_gate_required"],
                "meaning": "stop automatic mutation until explicit human authority exists",
            },
        ],
        "blocked_outcome_required_fields": [
            "owner",
            "reason",
            "next_repair_action",
        ],
        "done_definition": done_definition,
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "complete_product_claim_allowed": False,
        "public_private_boundary": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
        },
    }


def create_post_repair_review_task(
    *,
    hermes_bin: str,
    board: str,
    plan_task: dict[str, Any],
    parent_payload: dict[str, Any],
    parent_task_id: str,
    packet_id: str,
    work_unit_id: str,
    worker_assignee_prefix: str,
    workspace_ref: str,
    runner: Runner = default_runner,
) -> str:
    body = ready_work_unit_post_repair_review_body(
        plan_task=plan_task,
        parent_task_id=parent_task_id,
        packet_id=packet_id,
        work_unit_id=work_unit_id,
    )
    task_id = create_task(
        hermes_bin=hermes_bin,
        board=board,
        title=f"OF post-repair review for ready work unit {work_unit_id}",
        body=compact_json_argument(body),
        assignee=worker_assignee_prefix + "independent-reviewer",
        idempotency_key=ready_work_unit_post_repair_review_idempotency_key(
            plan_task=plan_task,
            parent_task_id=parent_task_id,
        ),
        created_by="overkill-factory",
        workspace=workspace_ref or task_dispatcher_workspace_ref(parent_payload) or "scratch",
        blocked=False,
        runner=runner,
    )
    run_checked(hermes_kanban(hermes_bin, board, "link", task_id, parent_task_id), runner)
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "comment",
            "--author",
            READY_WORK_UNIT_RECONCILIATION_AUTHOR,
            parent_task_id,
            compact_json_argument(
                {
                    "marker": READY_WORK_UNIT_POST_REPAIR_REVIEW_CREATED_MARKER,
                    "work_unit_id": work_unit_id,
                    "review_task_ref": task_id,
                    "reviewer_role": "independent-reviewer",
                    "reconciliation_scope": "post_release_ready_work_unit",
                    "runtime_authority": "hermes_kanban",
                    "local_state_authority": False,
                    "complete_product_claim_allowed": False,
                }
            ),
        ),
        runner,
    )
    return task_id


def parse_json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    text = value.strip()
    if not text.startswith("{"):
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def existing_post_repair_review_task_ref(payload: dict[str, Any], *, work_unit_id: str) -> str:
    for comment in reversed(task_readback_comments(payload)):
        marker = parse_json_object(comment.get("body") or comment.get("text") or comment.get("payload"))
        if marker.get("marker") != READY_WORK_UNIT_POST_REPAIR_REVIEW_CREATED_MARKER:
            continue
        if str(marker.get("work_unit_id") or "").strip() != work_unit_id:
            continue
        review_task_ref = str(marker.get("review_task_ref") or "").strip()
        if review_task_ref:
            return review_task_ref
    return ""


def existing_post_repair_authority_task_ref(
    payload: dict[str, Any],
    *,
    work_unit_id: str,
    review_task_ref: str | None = None,
) -> str:
    expected_review_task_ref = str(review_task_ref or "").strip()
    for comment in reversed(task_readback_comments(payload)):
        marker = parse_json_object(comment.get("body") or comment.get("text") or comment.get("payload"))
        if marker.get("marker") != READY_WORK_UNIT_POST_REPAIR_AUTHORITY_CREATED_MARKER:
            continue
        if str(marker.get("work_unit_id") or "").strip() != work_unit_id:
            continue
        marker_review_task_ref = str(marker.get("review_task_ref") or "").strip()
        if expected_review_task_ref and marker_review_task_ref != expected_review_task_ref:
            continue
        authority_task_ref = str(marker.get("authority_task_ref") or "").strip()
        if authority_task_ref:
            return authority_task_ref
    return ""


def ready_work_unit_post_repair_authority_idempotency_key(
    *,
    plan_task: dict[str, Any],
    parent_task_id: str,
    review_task_ref: str,
) -> str:
    base = str(plan_task.get("idempotency_key") or "").strip()
    if not base:
        _packet_id, work_unit_id = expected_ready_work_unit_key(plan_task)
        base = f"overkill:ready-work-unit:{work_unit_id}"
    digest = idempotency_digest_fragment(
        contract_digest(
            {
                "base_idempotency_key": base,
                "parent_task_id": parent_task_id,
                "review_task_ref": review_task_ref,
                "route": "post_repair_authority",
                "version": "v1",
            }
        )
    )
    return f"{base}:post-repair-authority:{digest}"


def ready_work_unit_post_repair_authority_body(
    *,
    parent_task_id: str,
    packet_id: str,
    work_unit_id: str,
    review_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "packet_type": "ready_work_unit_post_repair_authority_request",
        "marker": READY_WORK_UNIT_POST_REPAIR_AUTHORITY_REQUIRED_MARKER,
        "parent_packet_id": packet_id,
        "parent_work_unit_id": work_unit_id,
        "parent_task_ref": parent_task_id,
        "review_task_ref": review_result.get("review_task_ref"),
        "repair_task_ref": review_result.get("repair_task_ref"),
        "review_result_marker": review_result.get("marker"),
        "review_result_status": review_result.get("status"),
        "authority_scope": "post_repair_retry_or_done_only",
        "authority_must_choose_one": [
            {
                "markers": [
                    "ready_work_unit_repair_review_passed",
                    "ready_work_unit_retry_authorized",
                ],
                "meaning": "parent ready work unit may be retried by Hermes reconciliation",
            },
            {
                "markers": [
                    "ready_work_unit_repair_review_passed",
                    "ready_work_unit_done_authorized",
                    "ready_work_unit_done_definition_satisfied",
                ],
                "meaning": "parent ready work unit may be completed, not the whole product",
            },
            {
                "markers": ["human_gate_required"],
                "meaning": "stop automatic mutation until explicit human authority exists",
            },
            {
                "markers": ["structured_block"],
                "required_fields": ["owner", "reason", "next_authority_action"],
                "meaning": "authority cannot be granted yet; route the next non-human action",
            },
        ],
        "review_must_not_approve": [
            "complete_product",
            "release",
            "deployment",
            "customer_ready",
            "security_gate",
            "human_gate",
        ],
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "complete_product_claim_allowed": False,
        "public_private_boundary": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
        },
    }


def create_post_repair_authority_task(
    *,
    hermes_bin: str,
    board: str,
    plan_task: dict[str, Any],
    parent_payload: dict[str, Any],
    parent_task_id: str,
    packet_id: str,
    work_unit_id: str,
    review_result: dict[str, Any],
    worker_assignee_prefix: str,
    workspace_ref: str,
    runner: Runner = default_runner,
) -> str:
    body = ready_work_unit_post_repair_authority_body(
        parent_task_id=parent_task_id,
        packet_id=packet_id,
        work_unit_id=work_unit_id,
        review_result=review_result,
    )
    task_id = create_task(
        hermes_bin=hermes_bin,
        board=board,
        title=f"OF post-repair authority decision for ready work unit {work_unit_id}",
        body=compact_json_argument(body),
        assignee=worker_assignee_prefix + "independent-reviewer",
        idempotency_key=ready_work_unit_post_repair_authority_idempotency_key(
            plan_task=plan_task,
            parent_task_id=parent_task_id,
            review_task_ref=str(review_result.get("review_task_ref") or ""),
        ),
        created_by="overkill-factory",
        workspace=workspace_ref or task_dispatcher_workspace_ref(parent_payload) or "scratch",
        blocked=False,
        runner=runner,
    )
    run_checked(hermes_kanban(hermes_bin, board, "link", task_id, parent_task_id), runner)
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "comment",
            "--author",
            READY_WORK_UNIT_RECONCILIATION_AUTHOR,
            parent_task_id,
            compact_json_argument(
                {
                    "marker": READY_WORK_UNIT_POST_REPAIR_AUTHORITY_CREATED_MARKER,
                    "work_unit_id": work_unit_id,
                    "authority_task_ref": task_id,
                    "review_task_ref": review_result.get("review_task_ref"),
                    "repair_task_ref": review_result.get("repair_task_ref"),
                    "authority_scope": "post_repair_retry_or_done_only",
                    "runtime_authority": "hermes_kanban",
                    "local_state_authority": False,
                    "complete_product_claim_allowed": False,
                }
            ),
        ),
        runner,
    )
    return task_id


def no_forbidden_approvals_claimed(metadata: dict[str, Any]) -> bool:
    approvals = metadata.get("no_forbidden_approvals")
    if not isinstance(approvals, dict):
        return False
    return all(value is False for value in approvals.values())


def post_repair_review_result_from_run(
    *,
    run: dict[str, Any],
    parent_task_id: str,
    work_unit_id: str,
    review_task_id: str,
) -> dict[str, Any] | None:
    metadata = run.get("metadata")
    if not isinstance(metadata, dict):
        return None

    parent_ref = str(metadata.get("parent_task_ref") or metadata.get("parent_ref") or "").strip()
    live_readback = metadata.get("live_readback")
    if not parent_ref and isinstance(live_readback, dict):
        parent = live_readback.get("parent")
        if isinstance(parent, dict):
            parent_ref = str(parent.get("id") or parent.get("task_id") or "").strip()
    if parent_ref and parent_ref != parent_task_id:
        return None

    metadata_work_unit = str(metadata.get("parent_work_unit_id") or metadata.get("work_unit_id") or "").strip()
    if metadata_work_unit and metadata_work_unit != work_unit_id:
        return None

    nested_review = metadata.get("independent_review_result")
    nested_review = nested_review if isinstance(nested_review, dict) else {}
    nested_review_target = str(
        nested_review.get("review_target")
        or nested_review.get("reviewed_parent_card_id")
        or nested_review.get("parent_task_ref")
        or ""
    ).strip()
    nested_verdict = str(nested_review.get("verdict") or "").strip().upper()
    explicit_marker = metadata.get("marker") == READY_WORK_UNIT_POST_REPAIR_REVIEW_RESULT_MARKER
    reviewed_repair_card = str(metadata.get("reviewed_repair_card") or metadata.get("repair_task_ref") or "").strip()
    review_scope = str(metadata.get("review_scope") or "").strip().lower()
    run_profile = str(run.get("profile") or run.get("assignee") or "").strip()
    if not explicit_marker and not reviewed_repair_card and "repair" not in review_scope and not nested_review_target:
        return None
    if run_profile and run_profile != "independent-reviewer":
        return None

    status = str(run.get("status") or "").strip().lower()
    outcome = str(run.get("outcome") or "").strip().lower()
    validation_result = str(metadata.get("validation_result") or metadata.get("result") or "").strip().upper()
    blocking_findings = metadata.get("blocking_findings")
    if blocking_findings is None:
        blocking_findings = nested_review.get("blocking_findings")
    human_gate_required = metadata.get("human_gate_required") is True or nested_review.get("human_gate_required") is True

    explicit_pass = metadata.get("ready_work_unit_repair_review_passed") is True
    nested_pass = (
        status in {"done", "complete", "completed"}
        and outcome in {"", "completed", "done", "pass", "passed"}
        and nested_verdict.startswith("PASS")
        and blocking_findings is False
        and nested_review_target == parent_task_id
    )
    legacy_pass = (
        status in {"done", "complete", "completed"}
        and outcome in {"", "completed", "done", "pass", "passed"}
        and validation_result == "PASS"
        and blocking_findings is False
        and no_forbidden_approvals_claimed(metadata)
        and bool(parent_ref)
        and bool(reviewed_repair_card)
    )
    blocked = (
        metadata.get("review_blocked") is True
        or blocking_findings is True
        or status == "blocked"
        or outcome == "blocked"
    )
    repair_review_passed = explicit_pass or legacy_pass or nested_pass
    if not repair_review_passed and not blocked and not human_gate_required:
        return None

    retry_authorized = metadata.get("ready_work_unit_retry_authorized") is True
    done_authorized = metadata.get("ready_work_unit_done_authorized") is True
    done_definition_satisfied = metadata.get("ready_work_unit_done_definition_satisfied") is True
    return {
        "marker": READY_WORK_UNIT_POST_REPAIR_REVIEW_RESULT_MARKER,
        "review_task_ref": review_task_id,
        "repair_task_ref": reviewed_repair_card or None,
        "parent_task_ref": parent_task_id,
        "work_unit_id": work_unit_id,
        "source": "hermes_run_metadata",
        "status": "human_gate_required" if human_gate_required else "passed" if repair_review_passed else "blocked",
        "repair_review_passed": repair_review_passed,
        "retry_authorized": retry_authorized,
        "done_authorized": done_authorized,
        "done_definition_satisfied": done_definition_satisfied,
        "human_gate_required": human_gate_required,
        "blocked": blocked and not repair_review_passed,
        "complete_product_claim_allowed": False,
    }


def apply_post_repair_review_result(row: dict[str, Any], result: dict[str, Any] | None) -> dict[str, Any]:
    if not result:
        return row
    merged = dict(row)
    merged["post_repair_review_result"] = result
    merged["repair_review_passed"] = result.get("repair_review_passed") is True
    merged["retry_authorized"] = result.get("retry_authorized") is True
    merged["done_authorized"] = result.get("done_authorized") is True
    merged["done_definition_satisfied"] = result.get("done_definition_satisfied") is True
    merged["human_gate_required"] = result.get("human_gate_required") is True

    if merged["human_gate_required"]:
        merged["decision"] = "human_gate_required"
        merged["next_action"] = "wait for explicit human gate; no automatic retry or completion"
        merged["actionable_by_adapter"] = False
    elif result.get("blocked") is True:
        merged["decision"] = "repair_review_blocked"
        merged["next_action"] = "post-repair review blocked; route a factory-owned repair attempt before retry"
        merged["actionable_by_adapter"] = False
    elif (
        merged.get("repair_completed")
        and merged["repair_review_passed"]
        and merged["done_authorized"]
        and merged["done_definition_satisfied"]
    ):
        merged["decision"] = "complete_parent"
        merged["next_action"] = "complete the parent ready work unit through Hermes complete"
        merged["actionable_by_adapter"] = True
    elif merged.get("repair_completed") and merged["repair_review_passed"] and merged["retry_authorized"]:
        merged["decision"] = "retry_parent"
        merged["next_action"] = "unblock parent ready work unit for another Hermes worker attempt"
        merged["actionable_by_adapter"] = True
    elif merged["repair_completed"] and merged["repair_review_passed"]:
        merged["decision"] = "awaiting_retry_or_done_authority"
        merged["next_action"] = "repair review passed, but no explicit retry or done authority marker exists"
        merged["actionable_by_adapter"] = False
    return merged


def post_repair_review_results_by_work_unit(
    *,
    hermes_bin: str,
    board: str,
    parent_task_ids_by_work_unit: dict[str, str],
    worker_assignee_prefix: str,
    runner: Runner = default_runner,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    latest_sort_key: dict[str, tuple[int, int]] = {}
    seen_task_ids: set[str] = set()
    expected_assignee = worker_assignee_prefix + "independent-reviewer"
    for status in ["done", "blocked", "running"]:
        for record in list_tasks_by_status(hermes_bin=hermes_bin, board=board, status=status, runner=runner):
            task_id = str(record.get("task_id") or record.get("id") or "").strip()
            if not task_id or task_id in seen_task_ids:
                continue
            seen_task_ids.add(task_id)
            assignee = str(record.get("assignee") or record.get("profile") or "").strip()
            if assignee and assignee != expected_assignee:
                continue
            try:
                runs = task_run_records(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
            except RuntimeError:
                continue
            for run in runs:
                for work_unit_id, parent_task_id in parent_task_ids_by_work_unit.items():
                    result = post_repair_review_result_from_run(
                        run=run,
                        parent_task_id=parent_task_id,
                        work_unit_id=work_unit_id,
                        review_task_id=task_id,
                    )
                    if not result:
                        continue
                    run_id = int(run.get("id") or run.get("run_id") or 0)
                    ended_at = int(run.get("ended_at") or run.get("finished_at") or run.get("started_at") or 0)
                    sort_key = (ended_at, run_id)
                    if sort_key >= latest_sort_key.get(work_unit_id, (0, 0)):
                        latest_sort_key[work_unit_id] = sort_key
                        results[work_unit_id] = result
    return results


def post_repair_authority_result_from_run(
    *,
    run: dict[str, Any],
    authority_task_id: str,
    parent_task_id: str,
    work_unit_id: str,
    review_task_ref: str,
) -> dict[str, Any] | None:
    metadata = run.get("metadata")
    if not isinstance(metadata, dict):
        return None
    review_result = metadata.get("independent_review_result")
    review_result = review_result if isinstance(review_result, dict) else {}
    authority_decision = review_result.get("authority_decision")
    authority_decision = authority_decision if isinstance(authority_decision, dict) else {}
    selected_markers = metadata.get("selected_markers")
    if not isinstance(selected_markers, list):
        selected_markers = review_result.get("selected_markers")
    if not isinstance(selected_markers, list):
        selected_markers = authority_decision.get("selected_markers")
    markers = {str(marker or "").strip() for marker in (selected_markers or []) if str(marker or "").strip()}
    if not markers:
        for marker_key in (
            "ready_work_unit_repair_review_passed",
            "ready_work_unit_retry_authorized",
            "ready_work_unit_done_authorized",
            "ready_work_unit_done_definition_satisfied",
            "human_gate_required",
        ):
            if metadata.get(marker_key) is True or review_result.get(marker_key) is True:
                markers.add(marker_key)
    status = str(run.get("status") or "").strip().lower()
    outcome = str(run.get("outcome") or "").strip().lower()
    blocked = status == "blocked" or outcome == "blocked" or "structured_block" in markers
    if not markers and not blocked:
        return None
    repair_review_passed = "ready_work_unit_repair_review_passed" in markers
    retry_authorized = "ready_work_unit_retry_authorized" in markers
    done_authorized = "ready_work_unit_done_authorized" in markers
    done_definition_satisfied = "ready_work_unit_done_definition_satisfied" in markers
    authority_verdict = str(review_result.get("verdict") or "").strip().upper()
    if authority_verdict.startswith("PASS") and (retry_authorized or done_authorized or done_definition_satisfied):
        repair_review_passed = True
    human_gate_required = "human_gate_required" in markers or metadata.get("human_gate_required") is True
    return {
        "marker": READY_WORK_UNIT_POST_REPAIR_AUTHORITY_RESULT_MARKER,
        "authority_task_ref": authority_task_id,
        "review_task_ref": review_task_ref or None,
        "parent_task_ref": parent_task_id,
        "work_unit_id": work_unit_id,
        "source": "hermes_run_metadata",
        "status": "human_gate_required" if human_gate_required else "passed" if repair_review_passed else "blocked",
        "repair_review_passed": repair_review_passed,
        "retry_authorized": retry_authorized,
        "done_authorized": done_authorized,
        "done_definition_satisfied": done_definition_satisfied,
        "human_gate_required": human_gate_required,
        "blocked": blocked and not repair_review_passed,
        "complete_product_claim_allowed": False,
    }


def apply_post_repair_authority_result(row: dict[str, Any], result: dict[str, Any] | None) -> dict[str, Any]:
    if not result:
        return row
    merged = dict(row)
    merged["post_repair_authority_result"] = result
    merged["repair_review_passed"] = bool(merged.get("repair_review_passed")) or result.get("repair_review_passed") is True
    merged["retry_authorized"] = bool(merged.get("retry_authorized")) or result.get("retry_authorized") is True
    merged["done_authorized"] = bool(merged.get("done_authorized")) or result.get("done_authorized") is True
    merged["done_definition_satisfied"] = (
        bool(merged.get("done_definition_satisfied")) or result.get("done_definition_satisfied") is True
    )
    merged["human_gate_required"] = bool(merged.get("human_gate_required")) or result.get("human_gate_required") is True
    if merged["human_gate_required"]:
        merged["decision"] = "human_gate_required"
        merged["next_action"] = "wait for explicit human gate; no automatic retry or completion"
        merged["actionable_by_adapter"] = False
    elif result.get("blocked") is True:
        merged["decision"] = "authority_blocked"
        merged["next_action"] = "post-repair authority task blocked; route the declared next action before retry"
        merged["actionable_by_adapter"] = False
    elif (
        merged.get("repair_completed")
        and merged["repair_review_passed"]
        and merged["done_authorized"]
        and merged["done_definition_satisfied"]
    ):
        merged["decision"] = "complete_parent"
        merged["next_action"] = "complete the parent ready work unit through Hermes complete"
        merged["actionable_by_adapter"] = True
    elif merged.get("repair_completed") and merged["repair_review_passed"] and merged["retry_authorized"]:
        merged["decision"] = "retry_parent"
        merged["next_action"] = "unblock parent ready work unit for another Hermes worker attempt"
        merged["actionable_by_adapter"] = True
    return merged


def post_repair_authority_results_by_work_unit(
    *,
    hermes_bin: str,
    board: str,
    parent_task_ids_by_work_unit: dict[str, str],
    review_task_refs_by_work_unit: dict[str, str] | None = None,
    worker_assignee_prefix: str,
    runner: Runner = default_runner,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    latest_sort_key: dict[str, tuple[int, int]] = {}
    seen_task_ids: set[str] = set()
    expected_assignee = worker_assignee_prefix + "independent-reviewer"
    for status in ["done", "blocked", "running"]:
        for record in list_tasks_by_status(hermes_bin=hermes_bin, board=board, status=status, runner=runner):
            task_id = str(record.get("task_id") or record.get("id") or "").strip()
            if not task_id or task_id in seen_task_ids:
                continue
            seen_task_ids.add(task_id)
            assignee = str(record.get("assignee") or record.get("profile") or "").strip()
            if assignee and assignee != expected_assignee:
                continue
            try:
                payload = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
                body = parse_json_object(task_readback_body(payload))
            except RuntimeError:
                continue
            if body.get("packet_type") != "ready_work_unit_post_repair_authority_request":
                continue
            work_unit_id = str(body.get("parent_work_unit_id") or "").strip()
            parent_task_id = str(body.get("parent_task_ref") or "").strip()
            if not work_unit_id or parent_task_ids_by_work_unit.get(work_unit_id) != parent_task_id:
                continue
            review_task_ref = str(body.get("review_task_ref") or "").strip()
            expected_review_task_ref = str((review_task_refs_by_work_unit or {}).get(work_unit_id) or "").strip()
            if expected_review_task_ref and review_task_ref != expected_review_task_ref:
                continue
            try:
                runs = task_run_records(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
            except RuntimeError:
                continue
            for run in runs:
                result = post_repair_authority_result_from_run(
                    run=run,
                    authority_task_id=task_id,
                    parent_task_id=parent_task_id,
                    work_unit_id=work_unit_id,
                    review_task_ref=review_task_ref,
                )
                if not result:
                    continue
                run_id = int(run.get("id") or run.get("run_id") or 0)
                ended_at = int(run.get("ended_at") or run.get("finished_at") or run.get("started_at") or 0)
                sort_key = (ended_at, run_id)
                if sort_key >= latest_sort_key.get(work_unit_id, (0, 0)):
                    latest_sort_key[work_unit_id] = sort_key
                    results[work_unit_id] = result
    return results


def nested_string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(nested_string_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(nested_string_values(item))
        return values
    return []


def string_targets_task_ref(value: str, task_id: str) -> bool:
    text = str(value or "").strip()
    if not text or not task_id:
        return False
    exact_refs = {
        task_id,
        f"kanban:{task_id}",
        f"workspace:{task_id}",
    }
    if text in exact_refs:
        return True
    return (
        f"kanban:{task_id}" in text
        or f"workspace:{task_id}" in text
        or f"workspaces/{task_id}/" in text
        or f"task_id={task_id}" in text
    )


def review_metadata_targets_task(metadata: dict[str, Any], *, task_id: str) -> bool:
    review_result = metadata.get("independent_review_result")
    review_result = review_result if isinstance(review_result, dict) else {}
    explicit_fields = (
        metadata.get("review_target"),
        metadata.get("review_comment_task_id"),
        metadata.get("parent_task_ref"),
        review_result.get("review_target"),
        review_result.get("review_comment_task_id"),
        review_result.get("parent_task_ref"),
        review_result.get("reviewed_parent_card_id"),
    )
    if any(string_targets_task_ref(str(value or ""), task_id) for value in explicit_fields):
        return True
    return any(string_targets_task_ref(value, task_id) for value in nested_string_values(metadata))


def ready_work_unit_review_result_from_run(
    *,
    run: dict[str, Any],
    review_task_id: str,
    parent_task_id: str,
    work_unit_id: str,
    expected_assignee: str = "independent-reviewer",
) -> dict[str, Any] | None:
    metadata = run.get("metadata")
    if not isinstance(metadata, dict):
        return None
    run_profile = str(run.get("profile") or run.get("assignee") or "").strip()
    if run_profile and run_profile not in {"independent-reviewer", expected_assignee}:
        return None
    if not review_metadata_targets_task(metadata, task_id=parent_task_id):
        return None
    review_result = metadata.get("independent_review_result")
    review_result = review_result if isinstance(review_result, dict) else {}
    verdict = str(review_result.get("verdict") or metadata.get("verdict") or "").strip().upper()
    status = str(run.get("status") or "").strip().lower()
    outcome = str(run.get("outcome") or "").strip().lower()
    required_fixes = review_result.get("required_fixes")
    required_fixes = required_fixes if isinstance(required_fixes, list) else []
    blocking_findings = metadata.get("blocking_findings")
    if blocking_findings is None:
        blocking_findings = review_result.get("blocking_findings")
    human_gate_required = (
        metadata.get("human_gate_required") is True
        or review_result.get("human_gate_required") is True
        or metadata.get("production_promotion_approved") == "human_gate_required"
    )
    pass_result = (
        status in {"done", "complete", "completed"}
        and outcome in {"", "completed", "done", "pass", "passed", "success", "succeeded"}
        and verdict.startswith("PASS")
        and blocking_findings is not True
    )
    blocked = (
        blocking_findings is True
        or status == "blocked"
        or outcome == "blocked"
        or verdict.startswith("BLOCK")
        or bool(required_fixes)
    )
    if not pass_result and not blocked and not human_gate_required:
        return None
    return {
        "marker": "ready_work_unit_review_result",
        "review_task_ref": review_task_id,
        "parent_task_ref": parent_task_id,
        "work_unit_id": work_unit_id,
        "source": "hermes_run_metadata",
        "status": "human_gate_required" if human_gate_required else "passed" if pass_result else "blocked",
        "verdict": verdict or None,
        "review_passed": pass_result,
        "blocked": blocked and not pass_result,
        "human_gate_required": human_gate_required,
        "required_fix_count": len(required_fixes),
        "complete_product_claim_allowed": False,
    }


def ready_work_unit_review_results_by_work_unit(
    *,
    hermes_bin: str,
    board: str,
    parent_task_ids_by_work_unit: dict[str, str],
    worker_assignee_prefix: str,
    runner: Runner = default_runner,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    latest_sort_key: dict[str, tuple[int, int]] = {}
    seen_task_ids: set[str] = set()
    expected_assignee = worker_assignee_prefix + "independent-reviewer"
    for status in ["done", "blocked", "running"]:
        for record in list_tasks_by_status(hermes_bin=hermes_bin, board=board, status=status, runner=runner):
            task_id = str(record.get("task_id") or record.get("id") or "").strip()
            if not task_id or task_id in seen_task_ids:
                continue
            seen_task_ids.add(task_id)
            assignee = str(record.get("assignee") or record.get("profile") or "").strip()
            if assignee and assignee != expected_assignee:
                continue
            try:
                runs = task_run_records(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
            except RuntimeError:
                continue
            for run in runs:
                for work_unit_id, parent_task_id in parent_task_ids_by_work_unit.items():
                    result = ready_work_unit_review_result_from_run(
                        run=run,
                        review_task_id=task_id,
                        parent_task_id=parent_task_id,
                        work_unit_id=work_unit_id,
                        expected_assignee=expected_assignee,
                    )
                    if not result:
                        continue
                    run_id = int(run.get("id") or run.get("run_id") or 0)
                    ended_at = int(run.get("ended_at") or run.get("finished_at") or run.get("started_at") or 0)
                    sort_key = (ended_at, run_id)
                    if sort_key >= latest_sort_key.get(work_unit_id, (0, 0)):
                        latest_sort_key[work_unit_id] = sort_key
                        results[work_unit_id] = result
    return results


def superseded_post_repair_review_parent_ids(
    *,
    hermes_bin: str,
    board: str,
    parent_payload: dict[str, Any],
    parent_task_id: str,
    work_unit_id: str,
    authority_result: dict[str, Any] | None,
    runner: Runner = default_runner,
) -> list[str]:
    if not authority_result:
        return []
    if not (authority_result.get("retry_authorized") is True or authority_result.get("done_authorized") is True):
        return []
    authority_task_ref = str(authority_result.get("authority_task_ref") or "").strip()
    stale_parent_ids: list[str] = []
    for candidate_parent_id in task_readback_parents(parent_payload):
        if not candidate_parent_id or candidate_parent_id == authority_task_ref:
            continue
        try:
            candidate_payload = show_task(
                hermes_bin=hermes_bin,
                board=board,
                task_id=candidate_parent_id,
                runner=runner,
            )
            candidate_body = parse_json_object(task_readback_body(candidate_payload))
        except RuntimeError:
            continue
        if candidate_body.get("packet_type") != "ready_work_unit_post_repair_review_request":
            continue
        if str(candidate_body.get("parent_work_unit_id") or "").strip() != work_unit_id:
            continue
        if str(candidate_body.get("parent_task_ref") or "").strip() != parent_task_id:
            continue
        if task_readback_status(candidate_payload) != "blocked":
            continue
        stale_parent_ids.append(candidate_parent_id)
    return stale_parent_ids


def reconcile_ready_work_units(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    plan = load_ready_work_unit_materialization_plan(args.plan.resolve())
    board = str(args.board or plan.get("board") or "").strip()
    if not board:
        raise RuntimeError("ready work-unit reconciliation requires a board")
    if str(plan.get("board") or "").strip() and board != str(plan.get("board") or "").strip():
        raise RuntimeError("provided board does not match the ready work-unit materialization plan")
    materialization_result = load_ready_work_unit_materialization_result(
        args.materialization_result.resolve(),
        plan=plan,
        board=board,
    )
    tasks = expected_ready_work_unit_tasks(plan)
    candidates = ready_work_unit_readbacks_by_status(
        hermes_bin=args.hermes_bin,
        board=board,
        statuses=["todo", "blocked", "ready", "running", "done"],
        runner=runner,
    )

    verified: list[tuple[dict[str, Any], dict[str, Any], str, str, str, str]] = []
    for task in tasks:
        key = expected_ready_work_unit_key(task)
        matches = candidates.get(key) or []
        if len(matches) != 1:
            raise RuntimeError(
                f"ready work-unit reconciliation expected exactly one active Hermes task for packet {key[0]} / work unit {key[1]}, found {len(matches)}"
            )
        task_id, packet_id, work_unit_id = verify_ready_work_unit_identity(
            payload=matches[0],
            plan_task=task,
            worker_assignee_prefix=args.worker_assignee_prefix,
        )
        verified.append((task, matches[0], task_id, packet_id, work_unit_id, task_readback_status(matches[0])))

    review_results = post_repair_review_results_by_work_unit(
        hermes_bin=args.hermes_bin,
        board=board,
        parent_task_ids_by_work_unit={
            work_unit_id: task_id
            for _task, _payload, task_id, _packet_id, work_unit_id, _status in verified
        },
        worker_assignee_prefix=args.worker_assignee_prefix,
        runner=runner,
    )
    authority_results = post_repair_authority_results_by_work_unit(
        hermes_bin=args.hermes_bin,
        board=board,
        parent_task_ids_by_work_unit={
            work_unit_id: task_id
            for _task, _payload, task_id, _packet_id, work_unit_id, _status in verified
        },
        review_task_refs_by_work_unit={
            work_unit_id: str(result.get("review_task_ref") or "").strip()
            for work_unit_id, result in review_results.items()
            if str(result.get("review_task_ref") or "").strip()
        },
        worker_assignee_prefix=args.worker_assignee_prefix,
        runner=runner,
    )

    dependencies = ready_work_unit_dependencies(tasks)
    status_by_work_unit = {work_unit_id: status for _task, _payload, _task_id, _packet_id, work_unit_id, status in verified}
    dependency_blockers: dict[str, list[str]] = {}
    for _task, _payload, _task_id, _packet_id, work_unit_id, status in verified:
        if status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
            continue
        blockers = [
            dep
            for dep in dependencies.get(work_unit_id, [])
            if status_by_work_unit.get(dep) not in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES
        ]
        if blockers:
            dependency_blockers[work_unit_id] = blockers

    reconciliation: dict[str, dict[str, Any]] = {}
    retry_candidates: list[tuple[dict[str, Any], dict[str, Any], str, str, str, str]] = []
    complete_candidates: list[tuple[dict[str, Any], str, str, str]] = []
    post_repair_review_candidates: list[tuple[dict[str, Any], dict[str, Any], str, str, str]] = []
    post_repair_authority_candidates: list[tuple[dict[str, Any], dict[str, Any], str, str, str, dict[str, Any]]] = []
    superseded_parent_candidates: dict[str, list[str]] = {}
    post_repair_review_required_work_unit_ids: set[str] = set()
    existing_post_repair_review_task_ids: dict[str, str] = {}
    post_repair_authority_required_work_unit_ids: set[str] = set()
    existing_post_repair_authority_task_ids: dict[str, str] = {}
    post_release_blocked_count = 0
    human_gate_count = 0
    incomplete_count = 0
    post_repair_review_result_count = 0
    post_repair_authority_result_count = 0
    for task, payload, task_id, packet_id, work_unit_id, status in verified:
        row = classify_ready_work_unit_post_release_reconciliation(payload)
        row["task_ref"] = task_id
        row["packet_id"] = packet_id
        row["dependency_blockers"] = dependency_blockers.get(work_unit_id, [])
        review_result = review_results.get(work_unit_id)
        if review_result:
            row = apply_post_repair_review_result(row, review_result)
            post_repair_review_result_count += 1
        authority_result = authority_results.get(work_unit_id)
        if authority_result:
            row = apply_post_repair_authority_result(row, authority_result)
            post_repair_authority_result_count += 1
        row["post_repair_review_required"] = row["decision"] == "awaiting_repair_review"
        existing_review_task_id = ""
        if row["post_repair_review_required"]:
            post_repair_review_required_work_unit_ids.add(work_unit_id)
            existing_review_task_id = existing_post_repair_review_task_ref(payload, work_unit_id=work_unit_id)
            if existing_review_task_id:
                existing_post_repair_review_task_ids[work_unit_id] = existing_review_task_id
        elif review_result and review_result.get("review_task_ref"):
            existing_review_task_id = str(review_result["review_task_ref"])
            existing_post_repair_review_task_ids[work_unit_id] = existing_review_task_id
        row["post_repair_review_task_ref"] = existing_review_task_id or None
        row["post_repair_review_task_exists"] = bool(existing_review_task_id)
        existing_authority_task_id = ""
        if row["decision"] == "awaiting_retry_or_done_authority":
            post_repair_authority_required_work_unit_ids.add(work_unit_id)
            existing_authority_task_id = existing_post_repair_authority_task_ref(
                payload,
                work_unit_id=work_unit_id,
                review_task_ref=str((review_result or {}).get("review_task_ref") or "").strip(),
            )
            if existing_authority_task_id:
                existing_post_repair_authority_task_ids[work_unit_id] = existing_authority_task_id
        elif authority_result and authority_result.get("authority_task_ref"):
            existing_authority_task_id = str(authority_result["authority_task_ref"])
            existing_post_repair_authority_task_ids[work_unit_id] = existing_authority_task_id
        row["post_repair_authority_required"] = row["decision"] == "awaiting_retry_or_done_authority"
        row["post_repair_authority_task_ref"] = existing_authority_task_id or None
        row["post_repair_authority_task_exists"] = bool(existing_authority_task_id)
        superseded_parent_ids = []
        if row["decision"] in {"retry_parent", "complete_parent"}:
            superseded_parent_ids = superseded_post_repair_review_parent_ids(
                hermes_bin=args.hermes_bin,
                board=board,
                parent_payload=payload,
                parent_task_id=task_id,
                work_unit_id=work_unit_id,
                authority_result=authority_result,
                runner=runner,
            )
            if superseded_parent_ids:
                superseded_parent_candidates[work_unit_id] = superseded_parent_ids
        row["superseded_post_repair_review_parent_refs"] = superseded_parent_ids
        reconciliation[work_unit_id] = row
        if status == "blocked" and row["release_record_seen"]:
            post_release_blocked_count += 1
        if row["decision"] == "human_gate_required":
            human_gate_count += 1
        if row["decision"] in {
            "awaiting_repair",
            "awaiting_repair_review",
            "awaiting_retry_or_done_authority",
            "invalid_blocked_readback",
        }:
            incomplete_count += 1
        if row["decision"] == "retry_parent":
            retry_candidates.append((task, payload, task_id, packet_id, work_unit_id, status))
        elif row["decision"] == "complete_parent":
            complete_candidates.append((task, task_id, packet_id, work_unit_id))
        elif row["decision"] == "awaiting_repair_review" and not existing_review_task_id:
            post_repair_review_candidates.append((task, payload, task_id, packet_id, work_unit_id))
        elif row["decision"] == "awaiting_retry_or_done_authority" and not existing_authority_task_id:
            review_result = row.get("post_repair_review_result")
            if isinstance(review_result, dict):
                post_repair_authority_candidates.append((task, payload, task_id, packet_id, work_unit_id, review_result))

    if not args.dry_run and retry_candidates:
        required_workers = [
            ready_work_unit_release_assignee(task, args.worker_assignee_prefix)
            for task, _payload, _task_id, _packet_id, _work_unit_id, _status in retry_candidates
        ]
        readiness_blockers = route_readiness_blockers(args.route_readiness, required_workers)
        if readiness_blockers:
            raise RuntimeError("pre-retry route readiness blocked ready work-unit reconciliation: " + "; ".join(readiness_blockers))
    if not args.dry_run and args.create_post_repair_review_tasks and post_repair_review_candidates:
        readiness_blockers = route_readiness_blockers(
            args.route_readiness,
            [args.worker_assignee_prefix + "independent-reviewer"],
        )
        if readiness_blockers:
            raise RuntimeError("post-repair review route readiness blocked ready work-unit reconciliation: " + "; ".join(readiness_blockers))
    if not args.dry_run and args.create_post_repair_authority_tasks and post_repair_authority_candidates:
        readiness_blockers = route_readiness_blockers(
            args.route_readiness,
            [args.worker_assignee_prefix + "independent-reviewer"],
        )
        if readiness_blockers:
            raise RuntimeError(
                "post-repair authority route readiness blocked ready work-unit reconciliation: " + "; ".join(readiness_blockers)
            )

    retry_ready_work_unit_task_ids: dict[str, str] = {}
    unblocked_ready_work_unit_task_ids: dict[str, str] = {}
    completed_ready_work_unit_task_ids: dict[str, str] = {}
    created_post_repair_review_task_ids: dict[str, str] = {}
    post_repair_review_task_ids: dict[str, str] = dict(existing_post_repair_review_task_ids)
    created_post_repair_authority_task_ids: dict[str, str] = {}
    post_repair_authority_task_ids: dict[str, str] = dict(existing_post_repair_authority_task_ids)
    unlinked_superseded_parent_task_ids: dict[str, list[str]] = {}
    promoted_ready_work_unit_task_ids: dict[str, str] = {}
    retry_reason = str(
        args.reason
        or "ready_work_unit_retry_authorized; ready_work_unit_repair_review_passed; reconciliation_scope=post_release_ready_work_unit; dispatch_separate=true"
    )
    if not args.dry_run:
        if args.create_post_repair_review_tasks:
            workspace_ref = str(args.post_repair_review_workspace or "").strip()
            for task, payload, task_id, packet_id, work_unit_id in post_repair_review_candidates:
                review_task_id = create_post_repair_review_task(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    plan_task=task,
                    parent_payload=payload,
                    parent_task_id=task_id,
                    packet_id=packet_id,
                    work_unit_id=work_unit_id,
                    worker_assignee_prefix=args.worker_assignee_prefix,
                    workspace_ref=workspace_ref,
                    runner=runner,
                )
                post_repair_review_task_ids[work_unit_id] = review_task_id
                created_post_repair_review_task_ids[work_unit_id] = review_task_id
        if args.create_post_repair_authority_tasks:
            workspace_ref = str(args.post_repair_authority_workspace or "").strip()
            for task, payload, task_id, packet_id, work_unit_id, review_result in post_repair_authority_candidates:
                authority_task_id = create_post_repair_authority_task(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    plan_task=task,
                    parent_payload=payload,
                    parent_task_id=task_id,
                    packet_id=packet_id,
                    work_unit_id=work_unit_id,
                    review_result=review_result,
                    worker_assignee_prefix=args.worker_assignee_prefix,
                    workspace_ref=workspace_ref,
                    runner=runner,
                )
                post_repair_authority_task_ids[work_unit_id] = authority_task_id
                created_post_repair_authority_task_ids[work_unit_id] = authority_task_id
        for _task, _payload, task_id, _packet_id, work_unit_id, _status in retry_candidates:
            unlinked_parent_ids: list[str] = []
            authority_result = authority_results.get(work_unit_id)
            authority_task_ref = None
            if isinstance(authority_result, dict):
                authority_task_ref = str(authority_result.get("authority_task_ref") or "").strip() or None
            for superseded_parent_id in superseded_parent_candidates.get(work_unit_id, []):
                if unlink_task_dependency(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    parent_task_id=superseded_parent_id,
                    child_task_id=task_id,
                    work_unit_id=work_unit_id,
                    authority_task_ref=authority_task_ref,
                    runner=runner,
                ):
                    unlinked_parent_ids.append(superseded_parent_id)
            if unlinked_parent_ids:
                unlinked_superseded_parent_task_ids[work_unit_id] = unlinked_parent_ids
            current_payload = show_task(hermes_bin=args.hermes_bin, board=board, task_id=task_id, runner=runner)
            current_status = task_readback_status(current_payload)
            if current_status == "blocked":
                unblock_task(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    task_id=task_id,
                    reason=retry_reason,
                    required_readback_markers=READY_WORK_UNIT_RECONCILIATION_RETRY_READBACK_MARKERS,
                    runner=runner,
                )
                unblocked_ready_work_unit_task_ids[work_unit_id] = task_id
                retry_ready_work_unit_task_ids[work_unit_id] = task_id
            elif current_status == "todo":
                promote_task(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    task_id=task_id,
                    reason=retry_reason,
                    required_readback_markers=READY_WORK_UNIT_RECONCILIATION_RETRY_READBACK_MARKERS,
                    runner=runner,
                )
                promoted_ready_work_unit_task_ids[work_unit_id] = task_id
                retry_ready_work_unit_task_ids[work_unit_id] = task_id
            elif current_status in {"ready", "running", "done"}:
                retry_ready_work_unit_task_ids[work_unit_id] = task_id
            else:
                raise RuntimeError(f"ready work-unit {work_unit_id} is not in a retryable state after supersession cleanup")
        for _task, task_id, packet_id, work_unit_id in complete_candidates:
            unlinked_parent_ids = []
            authority_result = authority_results.get(work_unit_id)
            authority_task_ref = None
            if isinstance(authority_result, dict):
                authority_task_ref = str(authority_result.get("authority_task_ref") or "").strip() or None
            for superseded_parent_id in superseded_parent_candidates.get(work_unit_id, []):
                if unlink_task_dependency(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    parent_task_id=superseded_parent_id,
                    child_task_id=task_id,
                    work_unit_id=work_unit_id,
                    authority_task_ref=authority_task_ref,
                    runner=runner,
                ):
                    unlinked_parent_ids.append(superseded_parent_id)
            if unlinked_parent_ids:
                unlinked_superseded_parent_task_ids[work_unit_id] = unlinked_parent_ids
            metadata = {
                "marker": "ready_work_unit_post_release_reconciliation",
                "work_unit_id": work_unit_id,
                "packet_id": packet_id,
                "ready_work_unit_done_authorized": True,
                "ready_work_unit_done_definition_satisfied": True,
                "ready_work_unit_repair_review_passed": True,
                "reconciliation_scope": "post_release_ready_work_unit",
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "complete_product_claim_allowed": False,
            }
            complete_task(
                hermes_bin=args.hermes_bin,
                board=board,
                task_id=task_id,
                result=args.completion_result,
                summary=args.completion_summary,
                metadata=metadata,
                required_readback_markers=READY_WORK_UNIT_RECONCILIATION_DONE_READBACK_MARKERS,
                runner=runner,
            )
            completed_ready_work_unit_task_ids[work_unit_id] = task_id

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "reconcile-ready-work-units",
        "dry_run": bool(args.dry_run),
        "board": board,
        "materialization_plan_id": plan.get("plan_id"),
        "ready_work_unit_task_ids": {
            work_unit_id: task_id
            for _task, _payload, task_id, _packet_id, work_unit_id, _status in verified
        },
        "packet_task_ids": {
            packet_id: task_id
            for _task, _payload, task_id, packet_id, _work_unit_id, _status in verified
        },
        "retry_ready_work_unit_task_ids": retry_ready_work_unit_task_ids,
        "unblocked_ready_work_unit_task_ids": unblocked_ready_work_unit_task_ids,
        "completed_ready_work_unit_task_ids": completed_ready_work_unit_task_ids,
        "post_repair_review_task_ids": post_repair_review_task_ids,
        "existing_post_repair_review_task_ids": existing_post_repair_review_task_ids,
        "created_post_repair_review_task_ids": created_post_repair_review_task_ids,
        "post_repair_review_required_work_unit_ids": sorted(
            post_repair_review_required_work_unit_ids
        ),
        "post_repair_authority_task_ids": post_repair_authority_task_ids,
        "existing_post_repair_authority_task_ids": existing_post_repair_authority_task_ids,
        "created_post_repair_authority_task_ids": created_post_repair_authority_task_ids,
        "superseded_post_repair_review_parent_task_ids": superseded_parent_candidates,
        "unlinked_superseded_post_repair_review_parent_task_ids": unlinked_superseded_parent_task_ids,
        "post_repair_authority_required_work_unit_ids": sorted(
            post_repair_authority_required_work_unit_ids
        ),
        "promoted_ready_work_unit_task_ids": promoted_ready_work_unit_task_ids,
        "post_release_reconciliation": reconciliation,
        "release_wave": {
            "held_work_unit_ids": sorted(dependency_blockers.keys()),
            "dependency_blockers": {key: dependency_blockers[key] for key in sorted(dependency_blockers)},
            "release_ready_work_units_required_next": bool(
                retry_ready_work_unit_task_ids or completed_ready_work_unit_task_ids
            ),
        },
        "runtime_gate": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "reconciliation_verified_task_count": len(verified),
            "post_release_blocked_task_count": post_release_blocked_count,
            "retry_candidate_count": len(retry_candidates),
            "complete_candidate_count": len(complete_candidates),
            "post_repair_review_required_count": len(post_repair_review_required_work_unit_ids),
            "post_repair_review_missing_task_count": len(post_repair_review_candidates),
            "post_repair_review_existing_task_count": len(existing_post_repair_review_task_ids),
            "post_repair_review_result_count": post_repair_review_result_count,
            "post_repair_review_task_created_count": len(created_post_repair_review_task_ids),
            "post_repair_authority_required_count": len(post_repair_authority_required_work_unit_ids),
            "post_repair_authority_missing_task_count": len(post_repair_authority_candidates),
            "post_repair_authority_existing_task_count": len(existing_post_repair_authority_task_ids),
            "post_repair_authority_result_count": post_repair_authority_result_count,
            "post_repair_authority_task_created_count": len(created_post_repair_authority_task_ids),
            "superseded_post_repair_review_parent_count": sum(
                len(parent_ids) for parent_ids in superseded_parent_candidates.values()
            ),
            "superseded_post_repair_review_parent_unlinked_count": sum(
                len(parent_ids) for parent_ids in unlinked_superseded_parent_task_ids.values()
            ),
            "retry_unblocked_task_count": len(unblocked_ready_work_unit_task_ids),
            "retry_promoted_task_count": len(promoted_ready_work_unit_task_ids),
            "completed_task_count": len(completed_ready_work_unit_task_ids),
            "human_gate_required_count": human_gate_count,
            "incomplete_repair_or_review_count": incomplete_count,
            "dispatch_allowed_by_this_step": False,
            "native_dispatch_required_next": bool(retry_ready_work_unit_task_ids),
            "complete_product_claim_allowed": False,
        },
        "hook": {
            "plan": plan,
            "materialization_result": materialization_result,
            "retry_reason": retry_reason,
            "no_shadow_dispatcher": True,
            "local_state_authority": False,
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def close_reviewed_ready_work_units(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    plan = load_ready_work_unit_materialization_plan(args.plan.resolve())
    board = str(args.board or plan.get("board") or "").strip()
    if not board:
        raise RuntimeError("reviewed ready work-unit closeout requires a board")
    if str(plan.get("board") or "").strip() and board != str(plan.get("board") or "").strip():
        raise RuntimeError("provided board does not match the ready work-unit materialization plan")
    materialization_result = load_ready_work_unit_materialization_result(
        args.materialization_result.resolve(),
        plan=plan,
        board=board,
    )
    tasks = expected_ready_work_unit_tasks(plan)
    candidates = ready_work_unit_readbacks_by_status(
        hermes_bin=args.hermes_bin,
        board=board,
        statuses=["blocked", "done"],
        runner=runner,
    )

    verified: list[tuple[dict[str, Any], dict[str, Any], str, str, str, str]] = []
    for task in tasks:
        key = expected_ready_work_unit_key(task)
        matches = candidates.get(key) or []
        if len(matches) != 1:
            raise RuntimeError(
                f"reviewed ready work-unit closeout expected exactly one active Hermes task for packet {key[0]} / work unit {key[1]}, found {len(matches)}"
            )
        task_id, packet_id, work_unit_id = verify_ready_work_unit_identity(
            payload=matches[0],
            plan_task=task,
            worker_assignee_prefix=args.worker_assignee_prefix,
        )
        verified.append((task, matches[0], task_id, packet_id, work_unit_id, task_readback_status(matches[0])))

    review_results = ready_work_unit_review_results_by_work_unit(
        hermes_bin=args.hermes_bin,
        board=board,
        parent_task_ids_by_work_unit={
            work_unit_id: task_id
            for _task, _payload, task_id, _packet_id, work_unit_id, _status in verified
        },
        worker_assignee_prefix=args.worker_assignee_prefix,
        runner=runner,
    )

    closeout: dict[str, dict[str, Any]] = {}
    complete_candidates: list[tuple[dict[str, Any], str, str, str, dict[str, Any]]] = []
    human_gate_count = 0
    blocked_review_count = 0
    awaiting_review_count = 0
    already_satisfied_count = 0
    for task, payload, task_id, packet_id, work_unit_id, status in verified:
        review_result = review_results.get(work_unit_id)
        row: dict[str, Any] = {
            "status": status,
            "task_ref": task_id,
            "packet_id": packet_id,
            "work_unit_id": work_unit_id,
            "release_record_seen": task_has_ready_work_unit_release_record(payload),
            "complete_product_claim_allowed": False,
            "review_result": review_result,
            "decision": "awaiting_review",
            "actionable_by_adapter": False,
            "next_action": "wait for independent-reviewer PASS/BLOCK for this exact ready work unit",
        }
        if status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
            already_satisfied_count += 1
            row["decision"] = "already_satisfied"
            row["next_action"] = "no closeout needed"
        elif status != "blocked":
            row["decision"] = "wait_for_runtime_state"
            row["next_action"] = f"task is {status or 'unknown'}, not blocked"
        elif not row["release_record_seen"]:
            row["decision"] = "not_released_yet"
            row["next_action"] = "release-ready-work-units must release the task before review closeout"
        elif not review_result:
            awaiting_review_count += 1
        elif review_result.get("human_gate_required") is True:
            human_gate_count += 1
            row["decision"] = "human_gate_required"
            row["next_action"] = "wait for explicit human gate; no automatic closeout"
        elif review_result.get("blocked") is True:
            blocked_review_count += 1
            row["decision"] = "review_blocked"
            row["next_action"] = "route the independent-reviewer findings to the owning worker for repair"
        elif review_result.get("review_passed") is True:
            row["decision"] = "complete_parent"
            row["actionable_by_adapter"] = True
            row["next_action"] = "complete only this ready work unit through Hermes complete"
            complete_candidates.append((task, task_id, packet_id, work_unit_id, review_result))
        closeout[work_unit_id] = row

    completed_ready_work_unit_task_ids: dict[str, str] = {}
    if not args.dry_run:
        for _task, task_id, packet_id, work_unit_id, review_result in complete_candidates:
            metadata = {
                "marker": READY_WORK_UNIT_REVIEW_CLOSEOUT_MARKER,
                "work_unit_id": work_unit_id,
                "packet_id": packet_id,
                "ready_work_unit_review_passed": True,
                "review_task_ref": review_result.get("review_task_ref"),
                "review_verdict": review_result.get("verdict"),
                "reconciliation_scope": "reviewed_ready_work_unit",
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "complete_product_claim_allowed": False,
                "dispatch_allowed_by_this_step": False,
            }
            result = (
                args.completion_result
                or f"{READY_WORK_UNIT_REVIEW_PASSED_MARKER};work_unit_id={work_unit_id};scope=work_unit_only"
            )
            summary = (
                args.completion_summary
                or (
                    f"Ready work unit {work_unit_id} completed after independent review "
                    f"{review_result.get('review_task_ref') or 'review'} PASS; this grants no product/release/security/customer-ready/human-gate approval."
                )
            )
            complete_task(
                hermes_bin=args.hermes_bin,
                board=board,
                task_id=task_id,
                result=result,
                summary=summary,
                metadata=metadata,
                required_readback_markers=READY_WORK_UNIT_REVIEW_CLOSEOUT_READBACK_MARKERS,
                runner=runner,
            )
            completed_ready_work_unit_task_ids[work_unit_id] = task_id

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "close-reviewed-ready-work-units",
        "dry_run": bool(args.dry_run),
        "board": board,
        "materialization_plan_id": plan.get("plan_id"),
        "ready_work_unit_task_ids": {
            work_unit_id: task_id
            for _task, _payload, task_id, _packet_id, work_unit_id, _status in verified
        },
        "packet_task_ids": {
            packet_id: task_id
            for _task, _payload, task_id, packet_id, _work_unit_id, _status in verified
        },
        "completed_ready_work_unit_task_ids": completed_ready_work_unit_task_ids,
        "reviewed_ready_work_unit_closeout": closeout,
        "runtime_gate": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "reviewed_task_count": len(verified),
            "review_result_count": len(review_results),
            "complete_candidate_count": len(complete_candidates),
            "completed_task_count": len(completed_ready_work_unit_task_ids),
            "already_satisfied_count": already_satisfied_count,
            "awaiting_review_count": awaiting_review_count,
            "blocked_review_count": blocked_review_count,
            "human_gate_required_count": human_gate_count,
            "dispatch_allowed_by_this_step": False,
            "native_dispatch_required_next": False,
            "complete_product_claim_allowed": False,
        },
        "hook": {
            "plan": plan,
            "materialization_result": materialization_result,
            "no_shadow_dispatcher": True,
            "local_state_authority": False,
            "closeout_scope": "ready_work_unit_only",
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def release_readiness_review_has_parent_edge(
    *,
    parent_payload: dict[str, Any],
    review_payload: dict[str, Any],
    parent_task_id: str,
    review_task_id: str,
) -> bool:
    return (
        review_task_id in task_readback_parents(parent_payload)
        or review_task_id in task_readback_children(parent_payload)
        or parent_task_id in task_readback_parents(review_payload)
        or parent_task_id in task_readback_children(review_payload)
    )


def release_readiness_review_result_from_run(
    *,
    run: dict[str, Any],
    parent_task_id: str,
    review_task_id: str,
    expected_assignee: str = "independent-reviewer",
) -> dict[str, Any] | None:
    metadata = run.get("metadata")
    if not isinstance(metadata, dict):
        return None
    run_profile = str(run.get("profile") or run.get("assignee") or "").strip()
    if run_profile and run_profile not in {"independent-reviewer", expected_assignee}:
        return None
    if not review_metadata_targets_task(metadata, task_id=parent_task_id):
        return None
    review_result = metadata.get("independent_review_result")
    review_result = review_result if isinstance(review_result, dict) else {}
    verdict = str(review_result.get("verdict") or metadata.get("verdict") or "").strip().upper()
    status = str(run.get("status") or "").strip().lower()
    outcome = str(run.get("outcome") or "").strip().lower()
    required_fixes = review_result.get("required_fixes")
    required_fixes = required_fixes if isinstance(required_fixes, list) else []
    blocking_findings = metadata.get("blocking_findings")
    if blocking_findings is None:
        blocking_findings = review_result.get("blocking_findings")
    production_promotion_allowed = (
        metadata.get("production_promotion_allowed") is True
        or metadata.get("production_promotion_approved") is True
        or review_result.get("production_promotion_allowed") is True
        or review_result.get("production_promotion_approved") is True
    )
    complete_product_claim_allowed = (
        metadata.get("complete_product_claim_allowed") is True
        or review_result.get("complete_product_claim_allowed") is True
    )
    human_gate_required = (
        metadata.get("human_gate_required") is True
        or review_result.get("human_gate_required") is True
        or metadata.get("production_promotion_approved") == "human_gate_required"
        or review_result.get("production_promotion_approved") == "human_gate_required"
    )
    pass_result = (
        status in {"done", "complete", "completed"}
        and outcome in {"", "completed", "done", "pass", "passed", "success", "succeeded"}
        and verdict.startswith("PASS")
        and blocking_findings is not True
        and not required_fixes
    )
    blocked = (
        blocking_findings is True
        or status == "blocked"
        or outcome == "blocked"
        or verdict.startswith("BLOCK")
        or bool(required_fixes)
    )
    if not pass_result and not blocked and not human_gate_required and not production_promotion_allowed and not complete_product_claim_allowed:
        return None
    return {
        "marker": "release_readiness_review_result",
        "review_task_ref": review_task_id,
        "parent_task_ref": parent_task_id,
        "source": "hermes_run_metadata",
        "status": (
            "forbidden_approval_claim"
            if production_promotion_allowed or complete_product_claim_allowed
            else "human_gate_required"
            if human_gate_required
            else "passed"
            if pass_result
            else "blocked"
        ),
        "verdict": verdict or None,
        "review_passed": pass_result,
        "blocked": blocked and not pass_result,
        "human_gate_required": human_gate_required,
        "required_fix_count": len(required_fixes),
        "production_promotion_allowed": False,
        "complete_product_claim_allowed": False,
        "forbidden_approval_claim": production_promotion_allowed or complete_product_claim_allowed,
    }


def repair_release_readiness_review_parent_edge(
    *,
    hermes_bin: str,
    board: str,
    parent_task_id: str,
    review_task_id: str,
    runner: Runner = default_runner,
) -> bool:
    run_checked(hermes_kanban(hermes_bin, board, "link", review_task_id, parent_task_id), runner)
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "comment",
            "--author",
            READY_WORK_UNIT_RECONCILIATION_AUTHOR,
            parent_task_id,
            compact_json_argument(
                {
                    "marker": RELEASE_READINESS_REVIEW_PARENT_EDGE_REPAIRED_MARKER,
                    "review_task_ref": review_task_id,
                    "parent_task_ref": parent_task_id,
                    "reason": "release-readiness review relationship was explicit in review metadata but missing as a durable Hermes edge",
                    "runtime_authority": "hermes_kanban",
                    "local_state_authority": False,
                    "production_promotion_allowed": False,
                    "complete_product_claim_allowed": False,
                }
            ),
        ),
        runner,
    )
    return True


def close_release_readiness_review(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    board = str(args.board or "").strip()
    parent_task_id = str(args.parent_task or "").strip()
    review_task_id = str(args.review_task or "").strip()
    if not board:
        raise RuntimeError("release readiness review closeout requires a board")
    if not parent_task_id:
        raise RuntimeError("release readiness review closeout requires --parent-task")
    if not review_task_id:
        raise RuntimeError("release readiness review closeout requires --review-task")

    parent_payload = show_task(hermes_bin=args.hermes_bin, board=board, task_id=parent_task_id, runner=runner)
    review_payload = show_task(hermes_bin=args.hermes_bin, board=board, task_id=review_task_id, runner=runner)
    parent_body = parse_json_object(task_readback_body(parent_payload))
    if parent_body.get("next_action") != "release_readiness_required":
        raise RuntimeError("parent task is not a release_readiness_required next-route task")

    parent_edge_present = release_readiness_review_has_parent_edge(
        parent_payload=parent_payload,
        review_payload=review_payload,
        parent_task_id=parent_task_id,
        review_task_id=review_task_id,
    )
    review_runs = task_run_records(
        hermes_bin=args.hermes_bin,
        board=board,
        task_id=review_task_id,
        runner=runner,
    )
    expected_assignee = str(args.worker_assignee_prefix or "") + "independent-reviewer"
    review_result: dict[str, Any] | None = None
    latest_sort_key = (0, 0)
    for run in review_runs:
        candidate = release_readiness_review_result_from_run(
            run=run,
            parent_task_id=parent_task_id,
            review_task_id=review_task_id,
            expected_assignee=expected_assignee,
        )
        if not candidate:
            continue
        run_id = int(run.get("id") or run.get("run_id") or 0)
        ended_at = int(run.get("ended_at") or run.get("finished_at") or run.get("started_at") or 0)
        sort_key = (ended_at, run_id)
        if sort_key >= latest_sort_key:
            latest_sort_key = sort_key
            review_result = candidate

    parent_edge_repaired = False
    if not parent_edge_present and review_result and args.repair_missing_parent_edge and not args.dry_run:
        repair_release_readiness_review_parent_edge(
            hermes_bin=args.hermes_bin,
            board=board,
            parent_task_id=parent_task_id,
            review_task_id=review_task_id,
            runner=runner,
        )
        parent_payload = show_task(hermes_bin=args.hermes_bin, board=board, task_id=parent_task_id, runner=runner)
        review_payload = show_task(hermes_bin=args.hermes_bin, board=board, task_id=review_task_id, runner=runner)
        parent_edge_present = release_readiness_review_has_parent_edge(
            parent_payload=parent_payload,
            review_payload=review_payload,
            parent_task_id=parent_task_id,
            review_task_id=review_task_id,
        )
        parent_edge_repaired = parent_edge_present

    parent_status = task_readback_status(parent_payload)
    decision = "awaiting_review"
    next_action = "wait for independent-reviewer PASS/BLOCK for this exact release-readiness packet"
    actionable = False
    blocked_review_count = 0
    human_gate_count = 0
    if parent_status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
        decision = "already_satisfied"
        next_action = "no closeout needed"
    elif not parent_edge_present:
        decision = "missing_durable_parent_edge"
        next_action = "repair durable Hermes parent/dependency edge before consuming review result"
    elif not review_result:
        decision = "awaiting_review"
    elif review_result.get("forbidden_approval_claim") is True:
        decision = "forbidden_approval_claim"
        next_action = "reject review result that claims product completion or production promotion"
        blocked_review_count = 1
    elif review_result.get("human_gate_required") is True:
        decision = "human_gate_required"
        next_action = "wait for explicit human promotion gate; no automatic release closeout"
        human_gate_count = 1
    elif review_result.get("blocked") is True:
        decision = "repair_required"
        next_action = "route release-readiness packet back to release-ops-worker repair/retry"
        blocked_review_count = 1
    elif review_result.get("review_passed") is True:
        decision = "release_readiness_review_passed"
        next_action = "complete release-readiness packet only; production promotion remains separately blocked"
        actionable = parent_status == "blocked"

    completed_release_readiness_task_ids: dict[str, str] = {}
    if actionable and not args.dry_run:
        metadata = {
            "marker": RELEASE_READINESS_REVIEW_CLOSEOUT_MARKER,
            RELEASE_READINESS_REVIEW_PASSED_MARKER: True,
            "review_task_ref": review_task_id,
            "parent_task_ref": parent_task_id,
            "review_result": review_result,
            "release_readiness_scope": "packet_only",
            "production_promotion_allowed": False,
            "complete_product_claim_allowed": False,
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "dispatch_allowed_by_this_step": False,
        }
        complete_task(
            hermes_bin=args.hermes_bin,
            board=board,
            task_id=parent_task_id,
            result=f"{RELEASE_READINESS_REVIEW_PASSED_MARKER};scope=release_readiness_packet_only",
            summary=(
                "Release readiness packet accepted after independent-reviewer PASS; "
                "production/customer/mainnet promotion remains blocked and unapproved."
            ),
            metadata=metadata,
            required_readback_markers=RELEASE_READINESS_REVIEW_CLOSEOUT_READBACK_MARKERS,
            runner=runner,
        )
        completed_release_readiness_task_ids["release_readiness"] = parent_task_id

    closeout = {
        "$schema": "https://overkill-factory.dev/schemas/release-readiness-review-closeout.schema.json",
        "record_type": "release_readiness_review_closeout",
        "parent_task_ref": parent_task_id,
        "review_task_ref": review_task_id,
        "decision": decision,
        "next_action": next_action,
        "parent_status": parent_status,
        "review_status": task_readback_status(review_payload),
        "parent_edge_present": parent_edge_present,
        "parent_edge_repaired": parent_edge_repaired,
        "review_result": review_result,
        "production_promotion_allowed": False,
        "complete_product_claim_allowed": False,
        "dispatch_allowed_by_this_step": False,
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "public_private_boundary": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
        },
    }
    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "close-release-readiness-review",
        "dry_run": bool(args.dry_run),
        "board": board,
        "release_readiness_review_closeout": closeout,
        "completed_release_readiness_task_ids": completed_release_readiness_task_ids,
        "runtime_gate": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "review_result_count": 1 if review_result else 0,
            "complete_candidate_count": 1 if actionable else 0,
            "completed_task_count": len(completed_release_readiness_task_ids),
            "blocked_review_count": blocked_review_count,
            "human_gate_required_count": human_gate_count,
            "parent_edge_present": parent_edge_present,
            "parent_edge_repaired": parent_edge_repaired,
            "dispatch_allowed_by_this_step": False,
            "native_dispatch_required_next": False,
            "production_promotion_allowed": False,
            "complete_product_claim_allowed": False,
        },
        "hook": {
            "no_shadow_dispatcher": True,
            "local_state_authority": False,
            "closeout_scope": "release_readiness_review_only",
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def active_product_creation_work_units(product_creation_plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    active: dict[str, dict[str, Any]] = {}
    for unit in product_creation_plan.get("work_units", []):
        if not isinstance(unit, dict):
            continue
        unit_id = str(unit.get("unit_id") or "").strip()
        status = str(unit.get("status") or "").strip().lower()
        if not unit_id or status in {"rejected", "superseded"}:
            continue
        active[unit_id] = unit
    return active


def work_unit_materialization_tasks_by_id(materialization_plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    for task in materialization_plan.get("tasks", []):
        if not isinstance(task, dict):
            continue
        work_unit_id = str(task.get("work_unit_id") or "").strip()
        if work_unit_id:
            tasks[work_unit_id] = task
    return tasks


def product_creation_embedded_plan_ids(materialization_plan: dict[str, Any]) -> set[str]:
    plan_ids: set[str] = set()
    for task in materialization_plan.get("tasks", []):
        if not isinstance(task, dict):
            continue
        body = task.get("body_contract") if isinstance(task.get("body_contract"), dict) else {}
        packet = body.get("work_unit_context_packet") if isinstance(body.get("work_unit_context_packet"), dict) else {}
        embedded = packet.get("embedded_payloads") if isinstance(packet.get("embedded_payloads"), dict) else {}
        product_plan = embedded.get("product_creation_plan") if isinstance(embedded.get("product_creation_plan"), dict) else {}
        plan_id = str(product_plan.get("plan_id") or "").strip()
        if plan_id:
            plan_ids.add(plan_id)
    return plan_ids


def product_creation_closeout_next_action(
    *,
    product_creation_plan: dict[str, Any],
    release_readiness_ref: str | None,
    product_delivery_ref: str | None,
    product_promotion_gate_ref: str | None,
    learnback_ref: str | None,
    blocker_decisions: list[str],
) -> str:
    if any(decision == "human_gate_required" for decision in blocker_decisions):
        return "human_gate_required"
    if any(decision == "repair_required" for decision in blocker_decisions):
        return "repair_required"
    if blocker_decisions:
        return "blocked_with_owner"
    if not release_readiness_ref and product_creation_plan.get("production_readiness_scope"):
        return "release_readiness_required"
    if product_creation_plan.get("complete_product_required") is True and not product_delivery_ref:
        return "material_product_execution_required"
    if not learnback_ref:
        return "learnback_required"
    if product_promotion_gate_ref:
        return "product_closeout_ready"
    return "product_promotion_gate_required"


def product_creation_closeout_next_assignee(next_action: str, override: str | None) -> str:
    explicit = str(override or "").strip()
    if explicit:
        return explicit
    if next_action == "release_readiness_required":
        return "release-ops-worker"
    if next_action == "learnback_required":
        return "skill-eval-distiller"
    return "factory-orchestrator"


def product_creation_closeout_idempotency_key(
    *,
    product_creation_plan_id: str,
    materialization_plan_id: str,
    next_action: str,
) -> str:
    digest = idempotency_digest_fragment(
        contract_digest(
            {
                "product_creation_plan_id": product_creation_plan_id,
                "materialization_plan_id": materialization_plan_id,
                "next_action": next_action,
                "marker": PRODUCT_CREATION_CLOSEOUT_NEXT_ROUTE_MARKER,
                "no_spawn_protocol": "create-unassigned-block-assign-v3",
                "next_task_contract_version": "worker-consumable-v1",
                "idempotency_version": "v3",
            }
        )
    )
    return f"overkill:product-creation-closeout:{product_creation_plan_id}:{next_action}:{digest}"


def product_creation_next_route_contract(next_action: str, closeout: dict[str, Any]) -> dict[str, Any]:
    product_creation_plan_id = str(closeout.get("product_creation_plan_id") or "product-creation-plan")
    materialization_plan_id = str(closeout.get("materialization_plan_id") or "ready-work-unit-plan")
    common = {
        "source_refs": [
            f"product-creation-plan:{product_creation_plan_id}",
            f"ready-work-unit-materialization:{materialization_plan_id}",
            f"product-creation-closeout:{next_action}",
        ],
        "forbidden_actions": [
            "complete_product_claim",
            "production_release_approval",
            "customer_ready_claim",
            "deploy",
            "infrastructure_mutation",
            "secret_access",
            "private_evidence_publication",
            "raw_dogfood_log_publication",
            "local_path_publication",
        ],
        "public_private_boundary": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
            "private_runtime_refs_must_be_summarized": True,
        },
    }
    if next_action == "learnback_required":
        return {
            **common,
            "done_definition": [
                "classify dogfood outcomes into public-safe factory learnings",
                "identify systemic gaps, rejected non-gaps, and already-fixed gaps",
                "create or update public-safe improvement issues only when a real factory gap remains",
                "leave product completion, production promotion, deploy, and customer-ready claims forbidden",
                "complete only when learnback result includes owner, decision, evidence class, and next action",
            ],
            "evidence_expected": [
                "product creation closeout summary",
                "release readiness closeout summary",
                "work-unit aggregate coverage",
                "blocker and repair history classification",
                "worker feedback and runtime contract gaps",
                "public-safe issue/proposal refs for remaining factory improvements",
            ],
            "output_contract": {
                "receipt_field": "learnback_result",
                "allowed_results": ["PASS", "BLOCK"],
                "pass_requires": [
                    "public-safe learnback summary",
                    "gap classification",
                    "remaining issue refs or explicit no-new-gap rationale",
                    "no private evidence embedded",
                ],
                "block_requires": ["owner", "reason", "missing_contract_fields", "next_repair_action"],
                "may_create_public_safe_issue": True,
            },
        }
    if next_action == "release_readiness_required":
        return {
            **common,
            "done_definition": [
                "prepare release readiness packet",
                "state smoke, rollback, monitoring, support, human gate and promotion blockers",
                "create independent review route when review is required",
                "do not approve production promotion",
            ],
            "evidence_expected": [
                "release plan",
                "smoke result or reason blocked",
                "rollback plan",
                "monitoring/support plan",
                "human promotion gate status",
                "visible blockers with owner and next action",
            ],
            "output_contract": {
                "receipt_field": "release_ops_result",
                "allowed_results": ["PASS", "BLOCK"],
                "pass_requires": ["release readiness packet", "promotion blockers remain explicit"],
                "block_requires": ["owner", "reason", "next_repair_action"],
                "production_promotion_allowed": False,
            },
        }
    if next_action == "material_product_execution_required":
        return {
            **common,
            "forbidden_actions": common["forbidden_actions"]
            + [
                "create_loose_material_product_tasks",
                "create_todo_or_ready_material_product_tasks",
                "dispatch_material_product_workers_without_blocked_graph",
                "route_material_product_execution_without_dependency_edges",
            ],
            "material_product_execution_graph_contract": {
                "materialization_protocol": "create-unassigned-default-block-assign-v2",
                "deterministic_graph_required": True,
                "blocked_event_required_before_any_worker_dispatch": True,
                "create_sequence": [
                    "create_task_without_assignee",
                    "block_task_with_durable_event",
                    "verify_blocked_event_in_show_json",
                    "assign_target_worker_after_block_readback",
                    "link_dependency_edges_before_release",
                    "keep_each_material_task_blocked_until_runtime_gate",
                ],
                "required_nodes": [
                    "execution_packet",
                    "implementation",
                    "product_face_result",
                    "qa_verification",
                    "public_safety_gate",
                    "appsec_gate",
                    "independent_review",
                    "delivery_handoff",
                ],
                "required_edges": [
                    {"from": "execution_packet", "to": "implementation"},
                    {"from": "implementation", "to": "product_face_result"},
                    {"from": "implementation", "to": "qa_verification"},
                    {"from": "implementation", "to": "public_safety_gate"},
                    {"from": "implementation", "to": "appsec_gate"},
                    {"from": "product_face_result", "to": "qa_verification"},
                    {"from": "product_face_result", "to": "public_safety_gate"},
                    {"from": "product_face_result", "to": "appsec_gate"},
                    {"from": "qa_verification", "to": "independent_review"},
                    {"from": "public_safety_gate", "to": "independent_review"},
                    {"from": "appsec_gate", "to": "independent_review"},
                    {"from": "independent_review", "to": "delivery_handoff"},
                ],
                "node_authority_rules": {
                    "implementation": {
                        "allowed_after_runtime_gate": ["build_or_repair_scoped_artifact"],
                        "forbidden_actions_must_not_include": ["implement_product"],
                        "replacement_for_broad_implementation_forbid": "implement_product_outside_scope",
                        "forbidden_actions_still_required": [
                            "complete_product_claim",
                            "production_release_approval",
                            "customer_ready_claim",
                            "deploy",
                            "infrastructure_mutation",
                            "secret_access",
                            "private_evidence_publication",
                            "raw_dogfood_log_publication",
                            "local_path_publication",
                        ],
                    }
                },
                "pass_requires": [
                    "blocked_dependency_graph_ref",
                    "no_spawn_readback_evidence",
                    "task_ids_by_required_node",
                    "dependency_edges_readback",
                    "each_task_has_blocked_event_before_assignment_or_dispatch",
                ],
                "block_requires": [
                    "owner",
                    "reason",
                    "missing_graph_node_or_edge",
                    "next_repair_action",
                ],
            },
            "done_definition": [
                "route material product implementation before any promotion gate",
                "create the material execution graph with verified blocked/no-spawn readback before any worker dispatch",
                "create or repair executable product work units instead of treating planning readiness as product completion",
                "require product delivery proof before learnback or product promotion can close the product",
                "do not claim complete product, production release, deploy, or customer-ready status",
            ],
            "evidence_expected": [
                "executable product artifact or product delivery proof bundle",
                "Product Face Result for visible surfaces with states, journeys, screenshots and viewport evidence",
                "implementation verification commands and results",
                "public-safe evidence refs for product delivery proof",
            ],
            "output_contract": {
                "receipt_field": "material_product_execution_result",
                "allowed_results": ["PASS", "BLOCK"],
                "pass_requires": [
                    "product_delivery_ref",
                    "executable product proof",
                    "Product Face Result when visible surface exists",
                    "verification evidence refs",
                    "blocked_dependency_graph_ref",
                    "no_spawn_readback_evidence",
                    "remaining release/promotion blockers acknowledged",
                ],
                "block_requires": ["owner", "reason", "next_repair_action"],
                "complete_product_claim_allowed": False,
                "production_promotion_allowed": False,
            },
        }
    if next_action == "product_promotion_gate_required":
        return {
            **common,
            "done_definition": [
                "obtain or record an explicit product promotion human gate",
                "verify release readiness and learnback refs are present before asking for promotion",
                "block with owner, reason, and next action if the human gate is absent or denied",
                "do not claim complete product, production release, deploy, or customer-ready status",
            ],
            "evidence_expected": [
                "product creation closeout summary",
                "release readiness reviewed ref",
                "learnback reviewed ref",
                "explicit product promotion human gate decision",
            ],
            "output_contract": {
                "receipt_field": "product_promotion_gate_result",
                "allowed_results": ["PASS", "BLOCK"],
                "pass_requires": [
                    "product_promotion_gate_ref",
                    "public-safe gate decision",
                    "decision authority",
                    "promotion scope",
                    "remaining forbidden actions acknowledged",
                ],
                "block_requires": ["owner", "reason", "next_repair_action"],
                "complete_product_claim_allowed": False,
                "production_promotion_allowed": False,
            },
        }
    return {
        **common,
        "done_definition": [
            "consume the product creation closeout next action",
            "produce a public-safe result or block with owner, reason and next action",
        ],
        "evidence_expected": ["product creation closeout summary", "blocker inventory", "next action decision"],
        "output_contract": {
            "allowed_results": ["PASS", "BLOCK"],
            "block_requires": ["owner", "reason", "next_repair_action"],
        },
    }


def create_product_creation_closeout_next_task(
    *,
    args: argparse.Namespace,
    board: str,
    closeout: dict[str, Any],
    runner: Runner,
) -> str:
    next_action = str(closeout.get("next_action") or "blocked_with_owner")
    assignee = product_creation_closeout_next_assignee(next_action, args.next_assignee)
    product_creation_plan_id = str(closeout.get("product_creation_plan_id") or "product-creation-plan")
    materialization_plan_id = str(closeout.get("materialization_plan_id") or "ready-work-unit-plan")
    body = compact_json_argument(
        {
            "packet_type": "product_creation_run_closeout_next_action",
            "marker": PRODUCT_CREATION_CLOSEOUT_NEXT_ROUTE_MARKER,
            "product_creation_plan_id": product_creation_plan_id,
            "materialization_plan_id": materialization_plan_id,
            "next_action": next_action,
            "decision": closeout.get("decision"),
            "work_unit_count": closeout.get("work_unit_count"),
            "terminal_work_unit_count": closeout.get("terminal_work_unit_count"),
            "review_passed_work_unit_count": closeout.get("review_passed_work_unit_count"),
            "blocker_count": len(closeout.get("blockers") or []),
            "blockers": closeout.get("blockers") or [],
            "proof_id_coverage": closeout.get("proof_id_coverage") or {},
            "requirement_coverage": closeout.get("requirement_coverage") or {},
            "complete_product_claim_allowed": False,
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "dispatch_allowed_by_this_step": False,
            **product_creation_next_route_contract(next_action, closeout),
        }
    )
    task_id = create_blocked_task_before_assignment(
        hermes_bin=args.hermes_bin,
        board=board,
        title=f"OF product creation closeout next gate: {next_action}",
        body=body,
        assignee=assignee,
        idempotency_key=product_creation_closeout_idempotency_key(
            product_creation_plan_id=product_creation_plan_id,
            materialization_plan_id=materialization_plan_id,
            next_action=next_action,
        ),
        created_by="overkill-factory",
        workspace=str(args.workspace or "scratch"),
        blocked_reason=(
            "Product creation closeout next-route task starts blocked; "
            "dispatch is forbidden until the next gate has explicit authority."
        ),
        runner=runner,
    )
    run_checked(
        hermes_kanban(
            args.hermes_bin,
            board,
            "comment",
            "--author",
            READY_WORK_UNIT_RECONCILIATION_AUTHOR,
            task_id,
            compact_json_argument(
                {
                    "marker": PRODUCT_CREATION_CLOSEOUT_MARKER,
                    "next_route_marker": PRODUCT_CREATION_CLOSEOUT_NEXT_ROUTE_MARKER,
                    "product_creation_plan_id": product_creation_plan_id,
                    "materialization_plan_id": materialization_plan_id,
                    "next_action": next_action,
                    "complete_product_claim_allowed": False,
                    "dispatch_allowed_by_this_step": False,
                    "runtime_authority": "hermes_kanban",
                    "local_state_authority": False,
                }
            ),
        ),
        runner,
    )
    payload = show_task(hermes_bin=args.hermes_bin, board=board, task_id=task_id, runner=runner)
    if task_readback_status(payload) != "blocked":
        raise RuntimeError(f"product creation closeout next-route task {task_id} is not durably blocked")
    if not history_contains_all_markers_anywhere(payload, PRODUCT_CREATION_CLOSEOUT_READBACK_MARKERS):
        raise RuntimeError(f"product creation closeout next-route task {task_id} lacks closeout readback markers")
    return task_id


def close_product_creation_run(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    product_creation_plan = load_product_creation_plan(args.product_creation_plan.resolve())
    materialization_plan = load_ready_work_unit_materialization_plan(args.plan.resolve())
    board = str(args.board or materialization_plan.get("board") or "").strip()
    if not board:
        raise RuntimeError("product creation closeout requires a board")
    if str(materialization_plan.get("board") or "").strip() and board != str(materialization_plan.get("board") or "").strip():
        raise RuntimeError("provided board does not match the ready work-unit materialization plan")
    materialization_result = load_ready_work_unit_materialization_result(
        args.materialization_result.resolve(),
        plan=materialization_plan,
        board=board,
    )
    release_readiness_ref = ensure_public_safe_optional_ref(args.release_readiness_ref, field="release_readiness_ref")
    product_delivery_ref = ensure_public_safe_optional_ref(args.product_delivery_ref, field="product_delivery_ref")
    product_promotion_gate_ref = ensure_public_safe_optional_ref(
        args.product_promotion_gate_ref,
        field="product_promotion_gate_ref",
    )
    learnback_ref = ensure_public_safe_optional_ref(args.learnback_ref, field="learnback_ref")

    product_creation_plan_id = str(product_creation_plan.get("plan_id") or "").strip()
    materialization_plan_id = str(materialization_plan.get("plan_id") or "").strip()
    embedded_plan_ids = product_creation_embedded_plan_ids(materialization_plan)
    active_units = active_product_creation_work_units(product_creation_plan)
    materialized_tasks = work_unit_materialization_tasks_by_id(materialization_plan)
    expected_unit_ids = set(active_units)
    materialized_unit_ids = set(materialized_tasks)

    closeout_blockers: list[dict[str, Any]] = []
    if embedded_plan_ids and product_creation_plan_id not in embedded_plan_ids:
        closeout_blockers.append(
            {
                "blocker_id": "product_creation_plan_mismatch",
                "owner": "factory-orchestrator",
                "reason": "materialized ready work units embed a different Product Creation Plan id",
                "next_repair_action": "refresh ready work-unit packets from the canonical Product Creation Plan",
            }
        )
    missing_materialized_units = sorted(expected_unit_ids - materialized_unit_ids)
    extra_materialized_units = sorted(materialized_unit_ids - expected_unit_ids)
    if missing_materialized_units:
        closeout_blockers.append(
            {
                "blocker_id": "missing_materialized_work_units",
                "owner": "factory-orchestrator",
                "reason": "not every active Product Creation Plan work unit was materialized",
                "work_unit_ids": missing_materialized_units,
                "next_repair_action": "materialize missing ready work units or refresh the Product Creation Plan",
            }
        )
    if extra_materialized_units:
        closeout_blockers.append(
            {
                "blocker_id": "extra_materialized_work_units",
                "owner": "factory-orchestrator",
                "reason": "materialization plan contains work units outside the active Product Creation Plan",
                "work_unit_ids": extra_materialized_units,
                "next_repair_action": "supersede stale runtime tasks or refresh the canonical Product Creation Plan",
            }
        )

    all_candidates = ready_work_unit_readbacks_by_status(
        hermes_bin=args.hermes_bin,
        board=board,
        statuses=["blocked", "ready", "running", "todo", "done"],
        include_superseded=True,
        runner=runner,
    )

    unit_rows: dict[str, dict[str, Any]] = {}
    verified_parent_task_ids: dict[str, str] = {}
    for work_unit_id in sorted(expected_unit_ids):
        unit = active_units[work_unit_id]
        task = materialized_tasks.get(work_unit_id)
        packet_id = str((task or {}).get("packet_id") or "").strip()
        matches = all_candidates.get((packet_id, work_unit_id), []) if packet_id else []
        active_matches = [payload for payload in matches if not task_has_ready_work_unit_supersession(payload)]
        superseded_count = len(matches) - len(active_matches)
        row: dict[str, Any] = {
            "work_unit_id": work_unit_id,
            "packet_id": packet_id,
            "proof_ids_required": string_list(unit.get("proof_ids_required")),
            "product_sot_requirement_refs": string_list(unit.get("product_sot_requirement_refs")),
            "active_task_count": len(active_matches),
            "superseded_task_count": superseded_count,
            "status": "missing_runtime_task",
            "review_passed": False,
            "terminal": False,
            "decision": "blocked_with_owner",
            "next_action": "repair runtime materialization for this work unit",
        }
        if not task:
            row["blocker_id"] = "not_in_materialization_plan"
        elif len(active_matches) != 1:
            row["blocker_id"] = "ambiguous_or_missing_active_ready_work_unit"
            row["next_action"] = "ensure exactly one non-superseded Hermes task represents this work unit"
        else:
            payload = active_matches[0]
            task_id, _packet_id, _work_unit_id = verify_ready_work_unit_identity(
                payload=payload,
                plan_task=task,
                worker_assignee_prefix=args.worker_assignee_prefix,
            )
            status = task_readback_status(payload)
            release_record_seen = task_has_ready_work_unit_release_record(payload)
            row.update(
                {
                    "task_ref": task_id,
                    "status": status,
                    "release_record_seen": release_record_seen,
                    "terminal": status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES,
                }
            )
            if not release_record_seen:
                row["blocker_id"] = "missing_release_record"
                row["decision"] = "blocked_with_owner"
                row["next_action"] = "route through release-ready-work-units before product closeout"
            else:
                verified_parent_task_ids[work_unit_id] = task_id
                if status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
                    row["decision"] = "awaiting_review_readback"
                    row["next_action"] = "verify exact independent-reviewer PASS metadata"
                elif history_contains_any_marker(payload, READY_WORK_UNIT_HUMAN_GATE_MARKERS):
                    row["decision"] = "human_gate_required"
                    row["blocker_id"] = "human_gate_required"
                    row["next_action"] = "wait for explicit human gate"
                elif status == "blocked":
                    row["decision"] = "repair_required"
                    row["blocker_id"] = "work_unit_blocked"
                    row["next_action"] = "route blocker to owner worker for repair/retry"
                else:
                    row["decision"] = "blocked_with_owner"
                    row["blocker_id"] = "work_unit_not_terminal"
                    row["next_action"] = "wait for Hermes terminal state or route repair"
        unit_rows[work_unit_id] = row

    review_results = ready_work_unit_review_results_by_work_unit(
        hermes_bin=args.hermes_bin,
        board=board,
        parent_task_ids_by_work_unit=verified_parent_task_ids,
        worker_assignee_prefix=args.worker_assignee_prefix,
        runner=runner,
    )
    for work_unit_id, review_result in review_results.items():
        row = unit_rows.get(work_unit_id)
        if not row:
            continue
        row["review_result"] = review_result
        if review_result.get("human_gate_required") is True:
            row["decision"] = "human_gate_required"
            row["blocker_id"] = "human_gate_required"
            row["next_action"] = "wait for explicit human gate"
        elif review_result.get("blocked") is True:
            row["decision"] = "repair_required"
            row["blocker_id"] = "review_blocked"
            row["next_action"] = "route independent-reviewer findings to owner worker"
        elif row.get("terminal") is True and review_result.get("review_passed") is True:
            row["review_passed"] = True
            row["decision"] = "work_unit_closed"
            row["next_action"] = "aggregate into product-level closeout only"

    blocker_decisions: list[str] = []
    proof_id_coverage: dict[str, dict[str, Any]] = {}
    requirement_coverage: dict[str, dict[str, Any]] = {}
    for work_unit_id, row in unit_rows.items():
        decision = str(row.get("decision") or "")
        if decision != "work_unit_closed":
            blocker_decisions.append(decision or "blocked_with_owner")
            closeout_blockers.append(
                {
                    "blocker_id": str(row.get("blocker_id") or f"{work_unit_id}_not_closed"),
                    "owner": str(active_units.get(work_unit_id, {}).get("owner_worker") or "factory-orchestrator"),
                    "work_unit_id": work_unit_id,
                    "reason": str(row.get("next_action") or "work unit is not ready for product-level closeout"),
                    "next_repair_action": str(row.get("next_action") or "route repair"),
                }
            )
        for proof_id in row.get("proof_ids_required") or []:
            proof_row = proof_id_coverage.setdefault(
                proof_id,
                {"proof_id": proof_id, "work_unit_ids": [], "status": "covered_by_review_pass"},
            )
            proof_row["work_unit_ids"].append(work_unit_id)
            if decision != "work_unit_closed":
                proof_row["status"] = "blocked_or_unproven"
        for requirement_ref in row.get("product_sot_requirement_refs") or []:
            req_row = requirement_coverage.setdefault(
                requirement_ref,
                {"requirement_ref": requirement_ref, "work_unit_ids": [], "status": "covered_by_closed_work_unit"},
            )
            req_row["work_unit_ids"].append(work_unit_id)
            if decision != "work_unit_closed":
                req_row["status"] = "blocked_or_unproven"

    next_action = product_creation_closeout_next_action(
        product_creation_plan=product_creation_plan,
        release_readiness_ref=release_readiness_ref,
        product_delivery_ref=product_delivery_ref,
        product_promotion_gate_ref=product_promotion_gate_ref,
        learnback_ref=learnback_ref,
        blocker_decisions=blocker_decisions,
    )
    terminal_count = sum(1 for row in unit_rows.values() if row.get("terminal") is True)
    review_passed_count = sum(1 for row in unit_rows.values() if row.get("review_passed") is True)
    closeout = {
        "$schema": "https://overkill-factory.dev/schemas/product-creation-run-closeout.schema.json",
        "record_type": "product_creation_run_closeout",
        "product_creation_plan_id": product_creation_plan_id,
        "materialization_plan_id": materialization_plan_id,
        "decision": next_action,
        "next_action": next_action,
        "complete_product_claim_allowed": False,
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "dispatch_allowed_by_this_step": False,
        "work_unit_count": len(unit_rows),
        "terminal_work_unit_count": terminal_count,
        "review_passed_work_unit_count": review_passed_count,
        "blockers": closeout_blockers,
        "work_units": unit_rows,
        "proof_id_coverage": proof_id_coverage,
        "requirement_coverage": requirement_coverage,
        "release_readiness_ref": release_readiness_ref,
        "product_delivery_ref": product_delivery_ref,
        "product_promotion_gate_ref": product_promotion_gate_ref,
        "learnback_ref": learnback_ref,
        "public_private_boundary": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
        },
    }

    next_route_task_ids: dict[str, str] = {}
    if not args.dry_run:
        task_id = create_product_creation_closeout_next_task(
            args=args,
            board=board,
            closeout=closeout,
            runner=runner,
        )
        next_route_task_ids[next_action] = task_id

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "close-product-creation-run",
        "dry_run": bool(args.dry_run),
        "board": board,
        "materialization_plan_id": materialization_plan_id,
        "product_creation_plan_id": product_creation_plan_id,
        "ready_work_unit_task_ids": {
            work_unit_id: str(row.get("task_ref") or "")
            for work_unit_id, row in unit_rows.items()
            if row.get("task_ref")
        },
        "product_creation_run_closeout": closeout,
        "product_creation_next_route_task_ids": next_route_task_ids,
        "runtime_gate": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "work_unit_count": len(unit_rows),
            "terminal_work_unit_count": terminal_count,
            "review_passed_work_unit_count": review_passed_count,
            "blocker_count": len(closeout_blockers),
            "next_action": next_action,
            "dispatch_allowed_by_this_step": False,
            "native_dispatch_required_next": False,
            "complete_product_claim_allowed": False,
            "next_route_task_created_count": len(next_route_task_ids),
        },
        "hook": {
            "product_creation_plan": product_creation_plan,
            "materialization_plan": materialization_plan,
            "materialization_result": materialization_result,
            "no_shadow_dispatcher": True,
            "local_state_authority": False,
            "closeout_scope": "product_creation_run",
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def ready_work_unit_replacement_idempotency_key(
    *, plan_task: dict[str, Any], contaminated_task_ids: list[str]
) -> str:
    base = str(plan_task.get("idempotency_key") or "").strip()
    if not base:
        _packet_id, work_unit_id = expected_ready_work_unit_key(plan_task)
        base = f"overkill:ready-work-unit:{work_unit_id}"
    digest = idempotency_digest_fragment(
        contract_digest(
            {
                "base_idempotency_key": base,
                "contaminated_task_ids": sorted(contaminated_task_ids),
                "recovery_marker": READY_WORK_UNIT_SUPERSESSION_MARKER,
                "version": "v1",
            }
        )
    )
    return f"{base}:supersedes:{digest}"


def replacement_ready_work_unit_task(
    *,
    plan_task: dict[str, Any],
    contaminated_task_ids: list[str],
    contamination_markers: list[str],
) -> dict[str, Any]:
    replacement = copy.deepcopy(plan_task)
    replacement["idempotency_key"] = ready_work_unit_replacement_idempotency_key(
        plan_task=plan_task,
        contaminated_task_ids=contaminated_task_ids,
    )
    title = str(replacement.get("title") or "").strip()
    if title and " clean replacement" not in title:
        replacement["title"] = f"{title} clean replacement"
    body = replacement.get("body_contract") if isinstance(replacement.get("body_contract"), dict) else {}
    body["runtime_lineage"] = {
        "lineage_type": "ready_work_unit_supersession",
        "supersedes_runtime_task_refs": sorted(contaminated_task_ids),
        "supersession_marker": READY_WORK_UNIT_SUPERSESSION_MARKER,
        "contamination_markers": sorted(set(contamination_markers)),
        "complete_product_claim_allowed": False,
    }
    body["supersedes_runtime_task_refs"] = sorted(contaminated_task_ids)
    body["complete_product_claim_allowed"] = False
    replacement["body_contract"] = body
    replacement["work_unit_context_packet"] = body.get("work_unit_context_packet")
    return replacement


def mark_ready_work_unit_superseded(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    replacement_task_id: str | None,
    work_unit_id: str,
    contamination_markers: list[str],
    runner: Runner = default_runner,
) -> None:
    payload = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    if task_readback_status(payload) != "blocked":
        ensure_blocked_event(
            hermes_bin=hermes_bin,
            board=board,
            task_id=task_id,
            reason=(
                "Ready work-unit superseded after pre-dispatch runtime activity; "
                "preserve history and use the clean replacement lineage."
            ),
            runner=runner,
        )
    comment = compact_json_argument(
        {
            "marker": READY_WORK_UNIT_SUPERSESSION_MARKER,
            "work_unit_id": work_unit_id,
            "replacement_task_ref": replacement_task_id or "planned-clean-replacement",
            "contamination_markers": sorted(set(contamination_markers)),
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "complete_product_claim_allowed": False,
            "reason": "superseded contaminated ready work-unit runtime lineage; clean replacement required",
        }
    )
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "comment",
            "--author",
            READY_WORK_UNIT_RECOVERY_AUTHOR,
            task_id,
            comment,
        ),
        runner,
    )


def recover_ready_work_units(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    plan = load_ready_work_unit_materialization_plan(args.plan.resolve())
    board = str(args.board or plan.get("board") or "").strip()
    if not board:
        raise RuntimeError("ready work-unit recovery requires a board")
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
    if args.create_replacements:
        readiness_blockers = route_readiness_blockers(args.route_readiness, required_workers)
        if readiness_blockers:
            raise RuntimeError(
                "pre-dispatch route readiness blocked ready work-unit recovery: " + "; ".join(readiness_blockers)
            )

    candidates = ready_work_unit_readbacks_by_status(
        hermes_bin=args.hermes_bin,
        board=board,
        statuses=["blocked", "ready", "running", "todo", "triage"],
        include_superseded=True,
        runner=runner,
    )
    dependencies = ready_work_unit_dependencies(tasks)
    active_status_by_work_unit: dict[str, str] = {}
    for task in tasks:
        key = expected_ready_work_unit_key(task)
        matches = candidates.get(key) or []
        active_matches = [
            payload for payload in matches if not task_has_ready_work_unit_supersession(payload)
        ]
        if active_matches:
            active_status_by_work_unit[key[1]] = task_readback_status(active_matches[0])
    recovery_plan: dict[str, Any] = {}
    replacement_ready_work_unit_task_ids: dict[str, str] = {}
    superseded_ready_work_unit_task_ids: dict[str, list[str]] = {}
    existing_clean_replacement_task_ids: dict[str, str] = {}
    missing_work_unit_ids: list[str] = []
    clean_work_unit_ids: list[str] = []

    for task in tasks:
        key = expected_ready_work_unit_key(task)
        packet_id, work_unit_id = key
        matches = candidates.get(key) or []
        active_matches = [
            payload for payload in matches if not task_has_ready_work_unit_supersession(payload)
        ]
        if not active_matches:
            missing_work_unit_ids.append(work_unit_id)
            recovery_plan[work_unit_id] = {
                "packet_id": packet_id,
                "status": "missing_active_runtime_task",
                "next_action": "materialize a clean ready work-unit task before release",
            }
            continue

        contaminated: list[tuple[dict[str, Any], list[str]]] = []
        clean_blocked: list[dict[str, Any]] = []
        dependency_blockers = [
            dep
            for dep in dependencies.get(work_unit_id, [])
            if active_status_by_work_unit.get(dep) not in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES
        ]
        for payload in active_matches:
            markers = ready_work_unit_contamination_markers(payload)
            legal_release_seen = history_contains_markers(
                payload,
                READY_WORK_UNIT_RELEASE_REQUIRED_MARKERS,
            ) or task_has_unblocked_event(
                payload,
                required_markers=READY_WORK_UNIT_RELEASE_REQUIRED_MARKERS,
            )
            if markers:
                if dependency_blockers or not legal_release_seen:
                    contaminated.append((payload, markers))
                continue
            if task_readback_status(payload) == "blocked":
                contract_error = ready_work_unit_readback_contract_error(
                    payload=payload,
                    task_id=task_readback_id(payload),
                    expected_assignee=ready_work_unit_release_assignee(task, args.worker_assignee_prefix),
                    expected_packet_id=packet_id,
                )
                if contract_error:
                    contaminated.append((payload, ["invalid_blocked_replacement_contract"]))
                else:
                    clean_blocked.append(payload)

        if not contaminated:
            clean_work_unit_ids.append(work_unit_id)
            recovery_plan[work_unit_id] = {
                "packet_id": packet_id,
                "status": "clean_no_recovery_needed",
                "active_task_count": len(active_matches),
                "dependency_blockers": dependency_blockers,
            }
            continue

        contaminated_task_ids = [task_readback_id(payload) for payload, _markers in contaminated]
        contamination_markers = sorted({marker for _payload, markers in contaminated for marker in markers})
        replacement_task_id: str | None = None
        replacement_task = replacement_ready_work_unit_task(
            plan_task=task,
            contaminated_task_ids=contaminated_task_ids,
            contamination_markers=contamination_markers,
        )
        if clean_blocked:
            replacement_task_id = task_readback_id(clean_blocked[0])
            existing_clean_replacement_task_ids[work_unit_id] = replacement_task_id
        elif args.create_replacements:
            workspace_ref = str(args.workspace or "scratch").strip() or "scratch"
            replacement_task_id = create_ready_work_unit_task(
                hermes_bin=args.hermes_bin,
                board=board,
                task=replacement_task,
                worker_assignee_prefix=args.worker_assignee_prefix,
                workspace_ref=workspace_ref,
                runner=runner,
            )
            replacement_ready_work_unit_task_ids[work_unit_id] = replacement_task_id

        superseded_task_ids_for_plan = [
            task_id
            for task_id in contaminated_task_ids
            if not replacement_task_id or task_id != replacement_task_id
        ]
        if args.create_replacements or clean_blocked:
            for payload, markers in contaminated:
                if task_readback_id(payload) == replacement_task_id:
                    continue
                mark_ready_work_unit_superseded(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    task_id=task_readback_id(payload),
                    replacement_task_id=replacement_task_id,
                    work_unit_id=work_unit_id,
                    contamination_markers=markers,
                    runner=runner,
                )
        superseded_ready_work_unit_task_ids[work_unit_id] = superseded_task_ids_for_plan
        recovery_plan[work_unit_id] = {
            "packet_id": packet_id,
            "status": "replacement_created" if replacement_task_id and args.create_replacements else "replacement_planned",
            "contaminated_task_refs": superseded_task_ids_for_plan,
            "contamination_markers": contamination_markers,
            "replacement_task_ref": replacement_task_id,
            "replacement_idempotency_key": replacement_task["idempotency_key"],
            "preserve_history": True,
            "complete_product_claim_allowed": False,
        }

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "recover-ready-work-units",
        "dry_run": not bool(args.create_replacements),
        "board": board,
        "materialization_plan_id": plan.get("plan_id"),
        "ready_work_unit_task_ids": materialization_result.get("ready_work_unit_task_ids") or {},
        "replacement_ready_work_unit_task_ids": replacement_ready_work_unit_task_ids,
        "superseded_ready_work_unit_task_ids": superseded_ready_work_unit_task_ids,
        "existing_clean_replacement_task_ids": existing_clean_replacement_task_ids,
        "recovery_plan": recovery_plan,
        "runtime_gate": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "complete_product_claim_allowed": False,
            "recovery_required_before_product_completion": bool(superseded_ready_work_unit_task_ids),
            "replacement_created_count": len(replacement_ready_work_unit_task_ids),
            "superseded_task_count": sum(len(ids) for ids in superseded_ready_work_unit_task_ids.values()),
            "missing_active_task_count": len(missing_work_unit_ids),
            "clean_task_count": len(clean_work_unit_ids),
        },
        "hook": {
            "plan": plan,
            "materialization_result": materialization_result,
            "supersession_marker": READY_WORK_UNIT_SUPERSESSION_MARKER,
            "create_replacements": bool(args.create_replacements),
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

    p_recover_ready = sub.add_parser(
        "recover-ready-work-units",
        help="Plan or create clean replacements for contaminated ready work-unit runtime tasks.",
    )
    p_recover_ready.add_argument("--plan", type=Path, required=True)
    p_recover_ready.add_argument("--materialization-result", type=Path, required=True)
    p_recover_ready.add_argument("--board")
    p_recover_ready.add_argument("--hermes-bin", default="hermes")
    p_recover_ready.add_argument("--worker-assignee-prefix", default="")
    p_recover_ready.add_argument("--route-readiness", type=Path)
    p_recover_ready.add_argument("--workspace")
    p_recover_ready.add_argument("--create-replacements", action="store_true")
    p_recover_ready.add_argument("--out", type=Path)

    p_reconcile_ready = sub.add_parser(
        "reconcile-ready-work-units",
        help="Reconcile post-release blocked ready work units after repair/review evidence.",
    )
    p_reconcile_ready.add_argument("--plan", type=Path, required=True)
    p_reconcile_ready.add_argument("--materialization-result", type=Path, required=True)
    p_reconcile_ready.add_argument("--board")
    p_reconcile_ready.add_argument("--hermes-bin", default="hermes")
    p_reconcile_ready.add_argument("--worker-assignee-prefix", default="")
    p_reconcile_ready.add_argument("--route-readiness", type=Path)
    p_reconcile_ready.add_argument("--reason")
    p_reconcile_ready.add_argument("--create-post-repair-review-tasks", action="store_true")
    p_reconcile_ready.add_argument("--create-post-repair-authority-tasks", action="store_true")
    p_reconcile_ready.add_argument("--post-repair-review-workspace")
    p_reconcile_ready.add_argument("--post-repair-authority-workspace")
    p_reconcile_ready.add_argument("--completion-result", default="Ready work-unit reconciliation satisfied.")
    p_reconcile_ready.add_argument(
        "--completion-summary",
        default="Post-release repair/review evidence reconciled by Overkill Factory.",
    )
    p_reconcile_ready.add_argument("--dry-run", action="store_true")
    p_reconcile_ready.add_argument("--out", type=Path)

    p_close_reviewed_ready = sub.add_parser(
        "close-reviewed-ready-work-units",
        help="Complete blocked ready work units only after exact independent-reviewer PASS evidence.",
    )
    p_close_reviewed_ready.add_argument("--plan", type=Path, required=True)
    p_close_reviewed_ready.add_argument("--materialization-result", type=Path, required=True)
    p_close_reviewed_ready.add_argument("--board")
    p_close_reviewed_ready.add_argument("--hermes-bin", default="hermes")
    p_close_reviewed_ready.add_argument("--worker-assignee-prefix", default="")
    p_close_reviewed_ready.add_argument("--completion-result")
    p_close_reviewed_ready.add_argument("--completion-summary")
    p_close_reviewed_ready.add_argument("--dry-run", action="store_true")
    p_close_reviewed_ready.add_argument("--out", type=Path)

    p_close_product_run = sub.add_parser(
        "close-product-creation-run",
        help="Aggregate terminal reviewed ready work units into the next product-level gate without dispatching.",
    )
    p_close_product_run.add_argument("--product-creation-plan", type=Path, required=True)
    p_close_product_run.add_argument("--plan", type=Path, required=True)
    p_close_product_run.add_argument("--materialization-result", type=Path, required=True)
    p_close_product_run.add_argument("--board")
    p_close_product_run.add_argument("--hermes-bin", default="hermes")
    p_close_product_run.add_argument("--worker-assignee-prefix", default="")
    p_close_product_run.add_argument("--release-readiness-ref")
    p_close_product_run.add_argument("--product-delivery-ref")
    p_close_product_run.add_argument("--product-promotion-gate-ref")
    p_close_product_run.add_argument("--learnback-ref")
    p_close_product_run.add_argument("--next-assignee")
    p_close_product_run.add_argument("--workspace", default="scratch")
    p_close_product_run.add_argument("--dry-run", action="store_true")
    p_close_product_run.add_argument("--out", type=Path)

    p_close_release_readiness_review = sub.add_parser(
        "close-release-readiness-review",
        help="Consume an independent-reviewer release-readiness PASS/BLOCK without approving production release.",
    )
    p_close_release_readiness_review.add_argument("--board", required=True)
    p_close_release_readiness_review.add_argument("--parent-task", required=True)
    p_close_release_readiness_review.add_argument("--review-task", required=True)
    p_close_release_readiness_review.add_argument("--hermes-bin", default="hermes")
    p_close_release_readiness_review.add_argument("--worker-assignee-prefix", default="")
    p_close_release_readiness_review.add_argument("--repair-missing-parent-edge", action="store_true")
    p_close_release_readiness_review.add_argument("--dry-run", action="store_true")
    p_close_release_readiness_review.add_argument("--out", type=Path)

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
        elif args.command == "recover-ready-work-units":
            envelope = recover_ready_work_units(args)
        elif args.command == "reconcile-ready-work-units":
            envelope = reconcile_ready_work_units(args)
        elif args.command == "close-reviewed-ready-work-units":
            envelope = close_reviewed_ready_work_units(args)
        elif args.command == "close-product-creation-run":
            envelope = close_product_creation_run(args)
        elif args.command == "close-release-readiness-review":
            envelope = close_release_readiness_review(args)
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
