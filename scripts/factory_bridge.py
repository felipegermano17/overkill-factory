#!/usr/bin/env python3
"""Overkill Factory bridge between a human operator, Codex hooks and Hermes.

The bridge is deliberately not a factory worker. It records operator-facing
signals, summarizes pending decisions and carries responses back to the
factory runtime without granting itself gate authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INBOX = ROOT / ".tmp" / "factory-runs" / "operator-inbox"
EVENT_SCHEMA = "https://overkill-factory.dev/schemas/factory-bridge-event.schema.json"
DECISION_SCHEMA = "https://overkill-factory.dev/schemas/factory-bridge-decision.schema.json"
HANDOFF_SCHEMA = "https://overkill-factory.dev/schemas/factory-bridge-handoff.schema.json"
RUN_SCHEMA = "https://overkill-factory.dev/schemas/factory-bridge-run.schema.json"
SOURCE_ENVELOPE_SCHEMA = "https://overkill-factory.dev/schemas/factory-bridge-source-envelope.schema.json"
START_REQUEST_SCHEMA = "https://overkill-factory.dev/schemas/factory-bridge-start-request.schema.json"
FACTORY_GATEWAY_PROFILE = "overkill-factory-gerente"
FACTORY_ORCHESTRATOR_WORKER = "factory-orchestrator"

EVENTS_FILE = "events.jsonl"
PENDING_FILE = "pending.jsonl"
ACKS_FILE = "acks.jsonl"

EVENT_TYPES = {
    "intake_received",
    "run_started",
    "status_update",
    "transition_blocked",
    "human_gate_required",
    "decision_requested",
    "change_requested",
    "exception_detected",
    "handoff_requested",
    "learnback_forwarded",
    "factory_question",
    "worker_attention_required",
    "receipt_ready",
    "run_completed",
}
SEVERITIES = {"info", "notice", "warning", "blocked", "failed", "requires_user"}
SOURCES = {
    "automation",
    "bridge",
    "codex_hook",
    "factoryctl",
    "hermes_transition_hook",
    "human",
    "operator",
    "worker",
}
DECISION_TYPES = {
    "human_gate_response",
    "scope_change",
    "pause_resume",
    "status_request",
    "information_request",
    "exception_response",
    "handoff_request",
}
DECISIONS = {
    "approved",
    "rejected",
    "changes_requested",
    "acknowledged",
    "pause",
    "resume",
    "needs_replan",
    "needs_human_gate_record",
}
PROJECT_MODES = {"new_project", "existing_project"}
EXPLICIT_EXISTING_BOARD_REF = re.compile(r"^(?:kanban|hermes|run|board):[A-Za-z0-9_.:/@-]{3,}$")

PRIVATE_SYNC_ROOT = "One" + "Drive"
PRIVATE_MARKER = re.compile(
    r"(?:[A-Za-z]:[\\/]|" + PRIVATE_SYNC_ROOT + r"|guild_ref|channel_ref|thread_id|message_id)",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_inbox_dir(inbox_dir: Path | str | None = None) -> Path:
    return Path(inbox_dir) if inbox_dir is not None else DEFAULT_INBOX


def bridge_authority() -> dict[str, bool]:
    return {
        "can_close_gate": False,
        "can_execute_factory_work": False,
        "can_auto_approve_human_gate": False,
        "can_mutate_hermes_state": False,
    }


def prompt_authority() -> dict[str, bool]:
    return {
        "bridge_may_execute_factory_work": False,
        "bridge_may_auto_approve_human_gate": False,
        "bridge_may_close_runtime_card": False,
    }


def source_envelope_authority() -> dict[str, bool]:
    return {
        "bridge_may_summarize_source_material": False,
        "bridge_may_interpret_source_material": False,
        "bridge_may_select_scope": False,
        "factory_owns_source_resolution": True,
        "factory_owns_product_sot": True,
    }


def safe_ref(ref: str) -> str:
    value = str(ref or "").strip()
    if not value:
        return "external:sanitized:empty-ref"
    if PRIVATE_MARKER.search(value):
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
        return f"external:sanitized:private-ref-{digest}"
    normalized = value.replace("\\", "/")
    if Path(normalized).is_absolute():
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
        return f"external:sanitized:absolute-ref-{digest}"
    return normalized


def safe_refs(refs: list[str] | None) -> list[str]:
    return [safe_ref(ref) for ref in refs or []]


def validate_existing_board_ref(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("existing_project requires an explicit existing_board_ref")
    if PRIVATE_MARKER.search(raw) or Path(raw.replace("\\", "/")).is_absolute():
        raise ValueError("existing_board_ref must be an explicit runtime ref, not a private/local path")
    if not EXPLICIT_EXISTING_BOARD_REF.search(raw):
        raise ValueError("existing_board_ref must start with kanban:, hermes:, run:, or board:")
    return raw


def validate_choice(name: str, value: str, choices: set[str]) -> None:
    if value not in choices:
        raise ValueError(f"{name} must be one of {', '.join(sorted(choices))}: {value}")


def normalized_project_mode(project_mode: str) -> str:
    value = str(project_mode or "").strip()
    validate_choice("project_mode", value, PROJECT_MODES)
    return value


def build_target_board_policy(project_mode: str, existing_board_ref: str | None = None) -> dict[str, Any]:
    mode = normalized_project_mode(project_mode)
    raw_existing = str(existing_board_ref or "").strip()
    if mode == "new_project":
        if raw_existing:
            raise ValueError("new_project must not provide existing_board_ref; the factory start path creates a fresh board")
        return {
            "policy": "factory_must_create_new_board",
            "requires_new_hermes_board": True,
            "existing_board_ref": None,
            "requires_explicit_existing_board_ref": False,
            "board_creation_owner": "factory_start_path",
            "factory_start_path_required": True,
            "bridge_may_select_existing_board": False,
            "bridge_may_mutate_board": False,
        }
    if not raw_existing:
        raise ValueError("existing_project requires an explicit existing_board_ref")
    existing_ref = validate_existing_board_ref(raw_existing)
    return {
        "policy": "use_explicit_existing_board",
        "requires_new_hermes_board": False,
        "existing_board_ref": existing_ref,
        "requires_explicit_existing_board_ref": True,
        "board_creation_owner": "existing_runtime",
        "factory_start_path_required": True,
        "bridge_may_select_existing_board": False,
        "bridge_may_mutate_board": False,
    }


def factory_start_recipient() -> dict[str, Any]:
    return {
        "gateway_profile": FACTORY_GATEWAY_PROFILE,
        "orchestrator_worker": FACTORY_ORCHESTRATOR_WORKER,
        "handoff_contract": "factory_bridge_start_request",
        "bridge_may_execute_recipient_work": False,
        "bridge_may_create_hermes_board": False,
        "factory_start_path_required": True,
    }


def source_items(source_refs: list[str] | None) -> list[dict[str, Any]]:
    clean_refs = safe_refs(source_refs)
    if not clean_refs:
        raise ValueError("source_refs requires at least one operator-supplied source reference")
    return [
        {
            "source_ref": ref,
            "source_role": "operator_supplied_material",
            "received_as": "opaque_ref",
            "content_embedded": False,
            "bridge_summary_created": False,
            "bridge_interpretation_created": False,
        }
        for ref in clean_refs
    ]


def stable_event_id(
    *,
    run_id: str,
    event_type: str,
    severity: str,
    source: str,
    summary: str,
    refs: list[str],
    payload: dict[str, Any] | None,
) -> str:
    basis = {
        "run_id": run_id,
        "event_type": event_type,
        "severity": severity,
        "source": source,
        "summary": summary,
        "refs": refs,
        "payload": payload or {},
    }
    digest = hashlib.sha256(json.dumps(basis, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()[:18]
    return f"fbe_{digest}"


def read_jsonl_with_errors(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not path.exists():
        return [], []
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(
                {
                    "file": path.name,
                    "line": line_number,
                    "error": f"invalid JSONL record: {exc.msg}",
                }
            )
            continue
        if not isinstance(parsed, dict):
            errors.append(
                {
                    "file": path.name,
                    "line": line_number,
                    "error": "JSONL record must be an object",
                }
            )
            continue
        rows.append(parsed)
    return rows, errors


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows, _errors = read_jsonl_with_errors(path)
    return rows


def append_jsonl_unique(path: Path, record: dict[str, Any], key: str) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    for existing in read_jsonl(path):
        if existing.get(key) == record.get(key):
            return existing
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n")
    return record


def write_json(path: Path | None, data: dict[str, Any]) -> None:
    payload = json.dumps(data, indent=2, ensure_ascii=True) + "\n"
    if path is None:
        print(payload, end="")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def emit_event(
    *,
    inbox_dir: Path | str | None = None,
    run_id: str,
    event_type: str,
    severity: str,
    source: str,
    summary: str,
    refs: list[str] | None = None,
    requires_user: bool = False,
    payload: dict[str, Any] | None = None,
    event_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    validate_choice("event_type", event_type, EVENT_TYPES)
    validate_choice("severity", severity, SEVERITIES)
    validate_choice("source", source, SOURCES)
    clean_refs = safe_refs(refs)
    ident = event_id or stable_event_id(
        run_id=run_id,
        event_type=event_type,
        severity=severity,
        source=source,
        summary=summary,
        refs=clean_refs,
        payload=payload,
    )
    event = {
        "$schema": EVENT_SCHEMA,
        "record_type": "factory_bridge_event",
        "event_id": ident,
        "run_id": run_id,
        "event_type": event_type,
        "severity": severity,
        "source": source,
        "summary": summary,
        "refs": clean_refs,
        "requires_user": bool(requires_user),
        "created_at": created_at or utc_now(),
        "payload": payload or {},
        "factory_authority": bridge_authority(),
    }
    inbox = normalize_inbox_dir(inbox_dir)
    stored = append_jsonl_unique(inbox / EVENTS_FILE, event, "event_id")
    if event["requires_user"] or severity in {"blocked", "failed", "requires_user"}:
        append_jsonl_unique(inbox / PENDING_FILE, stored, "event_id")
    return stored


def ack_event(
    *,
    inbox_dir: Path | str | None = None,
    event_id: str,
    actor: str,
    response: str,
    evidence_ref: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    ack = {
        "record_type": "factory_bridge_ack",
        "event_id": event_id,
        "actor": actor,
        "response": response,
        "evidence_ref": safe_ref(evidence_ref or "external:operator:chat-response"),
        "created_at": created_at or utc_now(),
        "factory_authority": bridge_authority(),
    }
    inbox = normalize_inbox_dir(inbox_dir)
    return append_jsonl_unique(inbox / ACKS_FILE, ack, "event_id")


def event_is_acked(event: dict[str, Any], acked_ids: set[str]) -> bool:
    return str(event.get("event_id") or "") in acked_ids


def summarize_inbox(*, inbox_dir: Path | str | None = None, max_items: int = 10) -> dict[str, Any]:
    inbox = normalize_inbox_dir(inbox_dir)
    events, event_errors = read_jsonl_with_errors(inbox / EVENTS_FILE)
    pending, pending_errors = read_jsonl_with_errors(inbox / PENDING_FILE)
    acks, ack_errors = read_jsonl_with_errors(inbox / ACKS_FILE)
    read_errors = event_errors + pending_errors + ack_errors
    acked_ids = {str(ack.get("event_id") or "") for ack in acks}
    open_pending = [event for event in pending if not event_is_acked(event, acked_ids)]
    open_pending.sort(key=lambda row: str(row.get("created_at") or ""))
    recent_events = events[-max_items:]
    return {
        "record_type": "factory_bridge_inbox_summary",
        "inbox_ref": "external:operator:inbox",
        "generated_at": utc_now(),
        "event_count": len(events),
        "ack_count": len(acks),
        "pending_count": len(open_pending),
        "pending_events": open_pending[:max_items],
        "recent_events": recent_events,
        "inbox_health": {
            "inbox_dir_exists": inbox.exists(),
            "events_file_exists": (inbox / EVENTS_FILE).exists(),
            "pending_file_exists": (inbox / PENDING_FILE).exists(),
            "acks_file_exists": (inbox / ACKS_FILE).exists(),
            "jsonl_error_count": len(read_errors),
            "jsonl_errors": read_errors[:max_items],
            "status": "warning" if read_errors or not inbox.exists() else "ok",
        },
        "authority": bridge_authority(),
    }


def classify_prompt(prompt: str) -> dict[str, Any]:
    normalized = " ".join(prompt.lower().strip().split())
    mode = "intake_bridge"
    reason = "default intake signal"
    start_terms = (
        "dar start",
        "startar",
        "inicie",
        "iniciar",
        "comece",
        "começar",
        "pode iniciar",
        "pode rodar",
        "rodar a fabrica",
        "rodar a fábrica",
        "start request",
    )
    explicit_start_authority_terms = (
        "com esse material",
        "com esses materiais",
        "material de start",
        "materiais de start",
        "ja enviado",
        "já enviado",
        "ja enviei",
        "já enviei",
        "autorizo",
        "autorizado",
        "aprovado",
        "aprovada",
        "pode iniciar",
        "pode rodar",
        "faz o que tem que ser feito",
    )
    if any(term in normalized for term in start_terms) and any(
        term in normalized for term in explicit_start_authority_terms
    ):
        mode = "start_bridge"
        reason = "operator explicitly authorized factory start from supplied material"
    if any(term in normalized for term in ("status", "como esta", "como está", "quanto falta", "andamento", "progresso")):
        mode = "status_bridge"
        reason = "operator asked for current state"
    if any(term in normalized for term in ("por que", "porque", "bloqueado", "falhou", "qual worker", "o que aconteceu")):
        mode = "question_bridge"
        reason = "operator asked for explanation or diagnostic information"
    if any(term in normalized for term in ("aprovo", "aprovado", "rejeito", "waiver", "gate", "decido", "decision")):
        mode = "decision_bridge"
        reason = "operator supplied or requested a decision"
    if mode != "decision_bridge" and any(
        term in normalized for term in ("mude", "alter", "change", "escopo", "pausa", "resume", "continua", "replane")
    ):
        mode = "change_bridge"
        reason = "operator requested a scope or runtime-control change"
    if any(term in normalized for term in ("bug", "erro", "exception", "quebrou", "travou", "corrigir ponte")):
        mode = "exception_bridge"
        reason = "operator reported an operational exception"
    if any(term in normalized for term in ("handoff", "passa para outro agente", "continuidade", "transferir")):
        mode = "handoff_bridge"
        reason = "operator requested continuity or transfer"
    if any(term in normalized for term in ("aprenda", "learnback", "melhore a fabrica", "melhorar a fabrica", "factory mechanic")):
        mode = "learnback_forwarding"
        reason = "operator supplied learnback; bridge forwards it without activating changes"
    requires_runtime_target = mode in {
        "status_bridge",
        "question_bridge",
        "decision_bridge",
        "change_bridge",
        "exception_bridge",
        "handoff_bridge",
    }
    return {
        "record_type": "factory_bridge_prompt_classification",
        "bridge_mode": mode,
        "reason": reason,
        "runtime_target_contract": {
            "explicit_runtime_target_ref_required": requires_runtime_target,
            "ambient_runtime_allowed": False,
            "bridge_may_guess_runtime_target": False,
        },
        "authority": prompt_authority(),
    }


def format_hook_context(summary: dict[str, Any], classification: dict[str, Any] | None = None) -> str:
    lines = [
        "Overkill Factory Bridge context",
        "Durable Operator Inbox: repo-local JSONL queue under .tmp/factory-runs/operator-inbox.",
        "Codex hooks are wake-up/context hooks, not a runtime watcher.",
        "Codex hooks do not watch the machine while Codex is closed.",
        "Hermes, worker results and Receipt Five remain the source of truth.",
        "The bridge must not close gates, execute factory work or auto-approve human gates.",
        "For intake_bridge, create or point to a sealed source envelope; do not summarize or interpret source material.",
        (
            "For start_bridge, hand a factory_bridge_start_request to "
            f"{FACTORY_GATEWAY_PROFILE}/{FACTORY_ORCHESTRATOR_WORKER}; the bridge must not create Hermes boards or cards."
        ),
        "For new_project, the factory start path must create a fresh Hermes board.",
        "For existing_project, use only an explicit existing board or run reference.",
        (
            "For status_bridge, resolve the explicit factory runtime target before reading Hermes; "
            "do not treat an ambient/default Hermes store as proof that a run is missing."
        ),
    ]
    if classification:
        lines.append(f"Bridge mode: {classification['bridge_mode']} ({classification['reason']}).")
        runtime_contract = classification.get("runtime_target_contract") or {}
        if runtime_contract.get("explicit_runtime_target_ref_required"):
            lines.append("Runtime target: explicit board/run ref required before reading Hermes state.")
        lines.append("Runtime target: ambient/default Hermes store is not authority.")
    health = summary.get("inbox_health") or {}
    if health.get("status") != "ok":
        lines.append("Inbox health: warning.")
        if not health.get("inbox_dir_exists"):
            lines.append("- operator inbox directory does not exist yet")
        for error in health.get("jsonl_errors") or []:
            lines.append(f"- {error.get('file')} line {error.get('line')}: {error.get('error')}")
    pending = summary.get("pending_events", [])
    lines.append(f"Pending operator events: {summary.get('pending_count', 0)}.")
    for event in pending[:5]:
        lines.append(
            f"- {event.get('event_type')} [{event.get('severity')}]: {event.get('summary')} "
            f"(event_id={event.get('event_id')})"
        )
    if not pending:
        lines.append("- none")
    return "\n".join(lines)


def hook_event_name(payload: dict[str, Any]) -> str:
    for key in ("hook_event_name", "hookEventName", "event", "event_name"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    return "Unknown"


def prompt_from_hook_payload(payload: dict[str, Any]) -> str:
    for key in ("prompt", "user_prompt", "userPrompt", "message"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return ""


def codex_hook_response(payload: dict[str, Any], *, inbox_dir: Path | str | None = None) -> dict[str, Any]:
    name = hook_event_name(payload)
    summary = summarize_inbox(inbox_dir=inbox_dir)
    if name == "UserPromptSubmit":
        classification = classify_prompt(prompt_from_hook_payload(payload))
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": format_hook_context(summary, classification),
            }
        }
    if name == "SessionStart":
        return {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": format_hook_context(summary),
            }
        }
    if name == "Stop":
        return {"continue": True}
    return {
        "hookSpecificOutput": {
            "hookEventName": name,
            "additionalContext": format_hook_context(summary),
        }
    }


def build_decision_record(
    *,
    run_id: str,
    event_id: str,
    decision_type: str,
    decision: str,
    actor: str,
    summary: str,
    evidence_refs: list[str] | None = None,
    human_gate_record_ref: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    validate_choice("decision_type", decision_type, DECISION_TYPES)
    validate_choice("decision", decision, DECISIONS)
    if decision_type == "human_gate_response" and not human_gate_record_ref:
        raise ValueError("human_gate_response requires --human-gate-record-ref")
    clean_evidence_refs = safe_refs(evidence_refs)
    clean_human_gate_record_ref = safe_ref(human_gate_record_ref) if human_gate_record_ref else None
    if decision_type == "human_gate_response" and clean_human_gate_record_ref not in clean_evidence_refs:
        clean_evidence_refs.append(str(clean_human_gate_record_ref))
    return {
        "$schema": DECISION_SCHEMA,
        "record_type": "factory_bridge_decision",
        "run_id": run_id,
        "event_id": event_id,
        "decision_type": decision_type,
        "decision": decision,
        "actor": actor,
        "summary": summary,
        "evidence_refs": clean_evidence_refs,
        "human_gate_record_ref": clean_human_gate_record_ref,
        "created_at": created_at or utc_now(),
        "authority": {
            "closes_factory_gate": False,
            "requires_factory_record": decision_type == "human_gate_response",
            "requires_replan": decision in {"changes_requested", "needs_replan"},
            "forwards_to_factory": True,
        },
    }


def build_handoff_packet(*, run_id: str, inbox_dir: Path | str | None = None) -> dict[str, Any]:
    summary = summarize_inbox(inbox_dir=inbox_dir)
    return {
        "$schema": HANDOFF_SCHEMA,
        "record_type": "factory_bridge_handoff",
        "run_id": run_id,
        "created_at": utc_now(),
        "inbox_summary": {
            "event_count": summary["event_count"],
            "ack_count": summary["ack_count"],
            "pending_count": summary["pending_count"],
        },
        "pending_operator_events": summary["pending_events"],
        "safe_next_actions": [
            "resolve the explicit factory runtime target, then read Hermes/card runtime state",
            "read worker results and Receipt Five",
            f"forward factory start requests to {FACTORY_GATEWAY_PROFILE}/{FACTORY_ORCHESTRATOR_WORKER}",
            "record structured response",
            "forward learnback to Factory Mechanic as candidate input",
            "ask the human when a gate requires human authority",
        ],
        "forbidden_actions": [
            "act as a factory worker",
            "create Hermes boards or cards directly as the bridge",
            "close Hermes card without Receipt Five",
            "auto-approve human gate",
            "execute material factory work from a status request",
            "activate Factory Mechanic changes without explicit human gate",
        ],
        "authority": bridge_authority(),
    }


def build_source_envelope(
    *,
    run_id: str,
    operator_goal: str,
    project_mode: str,
    source_refs: list[str] | None,
    existing_board_ref: str | None = None,
    created_by: str = "operator",
    created_at: str | None = None,
) -> dict[str, Any]:
    mode = normalized_project_mode(project_mode)
    return {
        "$schema": SOURCE_ENVELOPE_SCHEMA,
        "record_type": "factory_bridge_source_envelope",
        "run_id": run_id,
        "operator_goal": operator_goal,
        "project_mode": mode,
        "created_by": created_by,
        "created_at": created_at or utc_now(),
        "source_items": source_items(source_refs),
        "source_handling": {
            "sealed_raw_materials": True,
            "bridge_summarized_material": False,
            "bridge_interpreted_material": False,
            "bridge_selected_scope": False,
            "factory_owns_source_resolution": True,
            "factory_owns_product_sot": True,
        },
        "target_board_policy": build_target_board_policy(mode, existing_board_ref),
        "handoff_to_factory": factory_start_recipient(),
        "start_readiness": {
            "ready_to_request_factory_start": True,
            "blocked_reasons": [],
        },
        "forbidden_bridge_actions": [
            "summarize source material as product truth",
            "interpret source material into Product SOT",
            "select product scope for the factory",
            "create Hermes board directly",
            "create Hermes cards directly",
            "dispatch workers",
        ],
        "authority": source_envelope_authority(),
    }


def build_start_request(
    *,
    run_id: str,
    operator_goal: str,
    project_mode: str,
    source_envelope_ref: str,
    existing_board_ref: str | None = None,
    run_record_ref: str | None = None,
    created_by: str = "operator",
    created_at: str | None = None,
) -> dict[str, Any]:
    mode = normalized_project_mode(project_mode)
    return {
        "$schema": START_REQUEST_SCHEMA,
        "record_type": "factory_bridge_start_request",
        "run_id": run_id,
        "operator_goal": operator_goal,
        "project_mode": mode,
        "created_by": created_by,
        "created_at": created_at or utc_now(),
        "source_envelope_ref": safe_ref(source_envelope_ref),
        "run_record_ref": safe_ref(run_record_ref or "external:operator:bridge-run-record"),
        "handoff_to_factory": factory_start_recipient(),
        "target_board_policy": build_target_board_policy(mode, existing_board_ref),
        "bridge_limits": {
            "bridge_must_not_create_hermes_board": True,
            "bridge_must_not_create_hermes_cards": True,
            "bridge_must_not_dispatch_workers": True,
            "bridge_must_not_choose_runtime_board": True,
            "bridge_only_registers_operator_intent": True,
        },
        "requested_factory_action": {
            "action": "start_factory_run",
            "owner": FACTORY_ORCHESTRATOR_WORKER,
            "gateway_profile": FACTORY_GATEWAY_PROFILE,
            "factory_must_materialize_runtime_state": True,
        },
        "authority": bridge_authority(),
    }


def build_run_record(
    *,
    run_id: str,
    goal: str,
    project_mode: str = "new_project",
    existing_board_ref: str | None = None,
    source_envelope_ref: str | None = None,
    start_request_ref: str | None = None,
    created_by: str = "operator",
    created_at: str | None = None,
) -> dict[str, Any]:
    mode = normalized_project_mode(project_mode)
    record: dict[str, Any] = {
        "$schema": RUN_SCHEMA,
        "record_type": "factory_bridge_run",
        "run_id": run_id,
        "goal": goal,
        "project_mode": mode,
        "created_by": created_by,
        "created_at": created_at or utc_now(),
        "state": "operator_bridge_active",
        "inbox_ref": "external:operator:inbox",
        "target_board_policy": build_target_board_policy(mode, existing_board_ref),
        "handoff_to_factory": factory_start_recipient(),
        "authority": bridge_authority(),
    }
    if source_envelope_ref:
        record["source_envelope_ref"] = safe_ref(source_envelope_ref)
    if start_request_ref:
        record["start_request_ref"] = safe_ref(start_request_ref)
    return {
        **record,
    }


def read_stdin_json() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    return json.loads(raw)


def command_init_run(args: argparse.Namespace) -> int:
    record = build_run_record(
        run_id=args.run_id,
        goal=args.goal,
        project_mode=args.project_mode,
        existing_board_ref=args.existing_board_ref,
        source_envelope_ref=args.source_envelope_ref,
        start_request_ref=args.start_request_ref,
        created_by=args.created_by,
    )
    write_json(args.out, record)
    return 0


def command_source_envelope(args: argparse.Namespace) -> int:
    record = build_source_envelope(
        run_id=args.run_id,
        operator_goal=args.operator_goal,
        project_mode=args.project_mode,
        source_refs=args.source_ref,
        existing_board_ref=args.existing_board_ref,
        created_by=args.created_by,
    )
    write_json(args.out, record)
    return 0


def command_start_request(args: argparse.Namespace) -> int:
    record = build_start_request(
        run_id=args.run_id,
        operator_goal=args.operator_goal,
        project_mode=args.project_mode,
        source_envelope_ref=args.source_envelope_ref,
        existing_board_ref=args.existing_board_ref,
        run_record_ref=args.run_record_ref,
        created_by=args.created_by,
    )
    write_json(args.out, record)
    return 0


def command_emit_event(args: argparse.Namespace) -> int:
    payload = json.loads(args.payload_json) if args.payload_json else {}
    event = emit_event(
        inbox_dir=args.inbox_dir,
        run_id=args.run_id,
        event_type=args.event_type,
        severity=args.severity,
        source=args.source,
        summary=args.summary,
        refs=args.ref,
        requires_user=args.requires_user,
        payload=payload,
    )
    write_json(args.out, event)
    return 0


def command_summary(args: argparse.Namespace) -> int:
    summary = summarize_inbox(inbox_dir=args.inbox_dir, max_items=args.max_items)
    if args.text:
        print(format_hook_context(summary))
    else:
        write_json(args.out, summary)
    return 0


def command_ack(args: argparse.Namespace) -> int:
    ack = ack_event(
        inbox_dir=args.inbox_dir,
        event_id=args.event_id,
        actor=args.actor,
        response=args.response,
        evidence_ref=args.evidence_ref,
    )
    write_json(args.out, ack)
    return 0


def command_classify_prompt(args: argparse.Namespace) -> int:
    result = classify_prompt(args.prompt)
    write_json(args.out, result)
    return 0


def command_decision_record(args: argparse.Namespace) -> int:
    record = build_decision_record(
        run_id=args.run_id,
        event_id=args.event_id,
        decision_type=args.decision_type,
        decision=args.decision,
        actor=args.actor,
        summary=args.summary,
        evidence_refs=args.evidence_ref,
        human_gate_record_ref=args.human_gate_record_ref,
    )
    write_json(args.out, record)
    return 0


def command_handoff(args: argparse.Namespace) -> int:
    packet = build_handoff_packet(run_id=args.run_id, inbox_dir=args.inbox_dir)
    write_json(args.out, packet)
    return 0


def command_codex_hook(args: argparse.Namespace) -> int:
    payload = read_stdin_json()
    response = codex_hook_response(payload, inbox_dir=args.inbox_dir)
    write_json(None, response)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate the Overkill Factory bridge inbox.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_run = subparsers.add_parser("init-run", help="Create a bridge run record.")
    init_run.add_argument("--run-id", required=True)
    init_run.add_argument("--goal", required=True)
    init_run.add_argument("--project-mode", required=True, choices=sorted(PROJECT_MODES))
    init_run.add_argument("--existing-board-ref")
    init_run.add_argument("--source-envelope-ref")
    init_run.add_argument("--start-request-ref")
    init_run.add_argument("--created-by", default="operator")
    init_run.add_argument("--out", type=Path)
    init_run.set_defaults(func=command_init_run)

    envelope = subparsers.add_parser("source-envelope", help="Create a sealed source envelope for factory intake.")
    envelope.add_argument("--run-id", required=True)
    envelope.add_argument("--operator-goal", required=True)
    envelope.add_argument("--project-mode", required=True, choices=sorted(PROJECT_MODES))
    envelope.add_argument("--source-ref", action="append", default=[], required=True)
    envelope.add_argument("--existing-board-ref")
    envelope.add_argument("--created-by", default="operator")
    envelope.add_argument("--out", type=Path)
    envelope.set_defaults(func=command_source_envelope)

    start_request = subparsers.add_parser(
        "start-request",
        help="Create a start request addressed to the factory gateway/orchestrator.",
    )
    start_request.add_argument("--run-id", required=True)
    start_request.add_argument("--operator-goal", required=True)
    start_request.add_argument("--project-mode", required=True, choices=sorted(PROJECT_MODES))
    start_request.add_argument("--source-envelope-ref", required=True)
    start_request.add_argument("--existing-board-ref")
    start_request.add_argument("--run-record-ref")
    start_request.add_argument("--created-by", default="operator")
    start_request.add_argument("--out", type=Path)
    start_request.set_defaults(func=command_start_request)

    emit = subparsers.add_parser("emit-event", help="Append an idempotent operator event.")
    emit.add_argument("--inbox-dir", type=Path, default=DEFAULT_INBOX)
    emit.add_argument("--run-id", required=True)
    emit.add_argument("--event-type", required=True, choices=sorted(EVENT_TYPES))
    emit.add_argument("--severity", required=True, choices=sorted(SEVERITIES))
    emit.add_argument("--source", required=True, choices=sorted(SOURCES))
    emit.add_argument("--summary", required=True)
    emit.add_argument("--ref", action="append", default=[])
    emit.add_argument("--requires-user", action="store_true")
    emit.add_argument("--payload-json")
    emit.add_argument("--out", type=Path)
    emit.set_defaults(func=command_emit_event)

    summary = subparsers.add_parser("summarize-inbox", help="Summarize pending operator events.")
    summary.add_argument("--inbox-dir", type=Path, default=DEFAULT_INBOX)
    summary.add_argument("--max-items", type=int, default=10)
    summary.add_argument("--text", action="store_true")
    summary.add_argument("--out", type=Path)
    summary.set_defaults(func=command_summary)

    ack = subparsers.add_parser("ack", help="Acknowledge an operator event.")
    ack.add_argument("--inbox-dir", type=Path, default=DEFAULT_INBOX)
    ack.add_argument("--event-id", required=True)
    ack.add_argument("--actor", required=True)
    ack.add_argument("--response", required=True)
    ack.add_argument("--evidence-ref")
    ack.add_argument("--out", type=Path)
    ack.set_defaults(func=command_ack)

    classify = subparsers.add_parser("classify-prompt", help="Classify an operator prompt into a bridge mode.")
    classify.add_argument("--prompt", required=True)
    classify.add_argument("--out", type=Path)
    classify.set_defaults(func=command_classify_prompt)

    decision = subparsers.add_parser("decision-record", help="Create a bridge decision forwarding record.")
    decision.add_argument("--run-id", required=True)
    decision.add_argument("--event-id", required=True)
    decision.add_argument("--decision-type", required=True, choices=sorted(DECISION_TYPES))
    decision.add_argument("--decision", required=True, choices=sorted(DECISIONS))
    decision.add_argument("--actor", required=True)
    decision.add_argument("--summary", required=True)
    decision.add_argument("--evidence-ref", action="append", default=[])
    decision.add_argument("--human-gate-record-ref")
    decision.add_argument("--out", type=Path)
    decision.set_defaults(func=command_decision_record)

    handoff = subparsers.add_parser("handoff", help="Create a bridge handoff packet.")
    handoff.add_argument("--inbox-dir", type=Path, default=DEFAULT_INBOX)
    handoff.add_argument("--run-id", required=True)
    handoff.add_argument("--out", type=Path)
    handoff.set_defaults(func=command_handoff)

    hook = subparsers.add_parser("codex-hook", help="Read a Codex hook payload from stdin and emit hook JSON.")
    hook.add_argument("--inbox-dir", type=Path, default=DEFAULT_INBOX)
    hook.set_defaults(func=command_codex_hook)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
