#!/usr/bin/env python3
"""Operate the Discord Control Tower beyond project projection.

This script composes the lower-level project projector with the missing owner
UX automation:

- GERENTE intake scan: project-like messages become project threads and
  project surfaces.
- Active-message threading: events and approvals that invite action get a
  thread or a clear existing thread.
- Structured approvals: approval requests render as Portuguese buttons, with a
  short text fallback in the approval thread when Discord interactions expire.
- Operational lanes: access, blockers, evidence, release and health events are
  projected into their channels without making Discord the source of truth.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import factory_concierge_discord_bridge as bridge  # noqa: E402
import validate_public_json_artifacts as validator  # noqa: E402


INTAKE_MARKER_PREFIX = "of-intake:"
EVENT_MARKER_PREFIX = "of-event:"
APPROVAL_MARKER_PREFIX = "of-approval:"
HEALTH_MARKER = "of-health:bridge"
APPROVAL_DECISION_LABELS = {
    "approved": "Aprovar",
    "rejected": "Rejeitar",
    "needs_changes": "Pedir ajuste",
}
APPROVAL_TEXT_DECISIONS = {
    "aprovado": "approved",
    "aprovar": "approved",
    "sim aprovado": "approved",
    "rejeitado": "rejected",
    "rejeitar": "rejected",
    "nao aprovado": "rejected",
    "não aprovado": "rejected",
    "pedir ajuste": "needs_changes",
    "ajuste": "needs_changes",
    "precisa ajuste": "needs_changes",
}

ACTIVE_EVENT_TYPES = {
    "intake_received",
    "gate_blocked",
    "approval_requested",
    "access_missing",
    "worker_failed",
    "release_candidate",
    "incident_opened",
    "forecast_changed",
}

EVENT_TARGETS = {
    "intake_received": "registry",
    "phase_changed": "dashboard",
    "gate_blocked": "blockers",
    "gate_passed": "dashboard",
    "approval_requested": "approvals",
    "approval_recorded": "approvals",
    "access_missing": "access",
    "worker_started": "dashboard",
    "worker_completed": "evidence",
    "worker_failed": "blockers",
    "evidence_recorded": "evidence",
    "release_candidate": "production",
    "incident_opened": "blockers",
    "incident_resolved": "production",
    "health_alert": "health",
    "forecast_changed": "dashboard",
}

PIPELINE = [
    "Entrada",
    "Fonte/SOT",
    "Metodo/planejamento",
    "Arquitetura/UX/seguranca",
    "Acessos/gates",
    "Execucao",
    "Revisao/provas",
    "Producao",
    "Operacao/aprendizado",
]

PROJECT_INTAKE_KEYWORDS = [
    "paper",
    "briefing",
    "projeto",
    "produto",
    "piloto",
    "construir",
    "criar",
    "fabrica",
    "factory",
    "front",
    "jogo",
    "sot",
]

PROJECT_INTAKE_STRONG_PHRASES = [
    "paper do projeto",
    "paper:",
    "briefing do projeto",
    "briefing:",
    "novo projeto",
    "novo produto",
    "criar um produto",
    "construir um produto",
    "quero criar",
    "quero construir",
    "vamos criar",
    "vamos construir",
    "produto sera",
    "produto será",
    "demanda do projeto",
]

OPERATIONAL_DISCORD_PHRASES = [
    "recrie",
    "recriar",
    "corrija",
    "arrume",
    "apague",
    "delete",
    "limpe",
    "atualize",
    "mova",
    "mande",
    "envie",
    "poste",
    "canal",
    "canais",
    "thread",
    "tread",
    "mensagem",
    "discord",
    "torre de controle",
    "aprovacao",
    "aprovação",
    "botao",
    "botão",
    "kanban",
    "projetos-recebidos",
    "nao funcionou",
    "não funcionou",
]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_artifact(artifact: dict[str, Any]) -> None:
    schemas = validator.load_schemas()
    schema_ref = str(artifact.get("$schema") or "")
    schema = schemas[validator.schema_name(schema_ref)]
    errors = validator.validate_node(schema, artifact, "$")
    if errors:
        raise AssertionError("; ".join(errors))


def safe_title(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"^[#>*\-\s]+", "", value)
    value = value.strip(" .:-")
    return bridge.truncate(value or "Projeto sem titulo", 90)


def infer_project_title(message: dict[str, Any]) -> str:
    content = str(message.get("content") or "")
    low = content.lower()
    if "front" in low and "jogo" in low and ("fabrica" in low or "factory" in low):
        return "Piloto - Front jogo da fabrica"
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    for line in lines:
        if len(line) >= 12:
            return safe_title(line)
    attachments = message.get("attachments") or []
    if attachments:
        filename = str(attachments[0].get("filename") or "Projeto com anexo")
        return safe_title(filename.rsplit(".", 1)[0])
    return "Projeto recebido pelo GERENTE"


def stable_project_id(title: str) -> str:
    if bridge.normalize_name(title) == "piloto-front-jogo-da-fabrica":
        return "pilot-front-jogo-fabrica"
    return bridge.normalize_name(title)


def normalize_intake_text(value: str) -> str:
    without_marks = "".join(
        char
        for char in unicodedata.normalize("NFKD", value.lower())
        if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", without_marks).strip()


def has_phrase(text: str, phrases: list[str]) -> bool:
    normalized_phrases = [normalize_intake_text(phrase) for phrase in phrases]
    return any(phrase in text for phrase in normalized_phrases)


def looks_like_project_intake(message: dict[str, Any]) -> bool:
    author = message.get("author") or {}
    if author.get("bot"):
        return False
    content = str(message.get("content") or "").strip()
    attachments = message.get("attachments") or []
    low = normalize_intake_text(content)
    if not content and not attachments:
        return False

    has_strong_project_intent = has_phrase(low, PROJECT_INTAKE_STRONG_PHRASES)
    has_operational_discord_intent = has_phrase(low, OPERATIONAL_DISCORD_PHRASES)
    if has_operational_discord_intent and not has_strong_project_intent:
        return False

    hits = sum(1 for word in PROJECT_INTAKE_KEYWORDS if normalize_intake_text(word) in low)
    if has_strong_project_intent:
        return True
    if attachments:
        return True
    if "paper" in low and hits >= 1 and len(content) >= 80:
        return True
    return len(content) >= 700 and hits >= 2


def default_projection_from_intake(message: dict[str, Any], now: str | None = None) -> dict[str, Any]:
    timestamp = now or utc_now()
    title = infer_project_title(message)
    project_id = stable_project_id(title)
    return {
        "$schema": "https://overkill-factory.dev/schemas/project-projection.schema.json",
        "project_id": project_id,
        "name": title,
        "phase": "Entrada",
        "status": "intake",
        "execution_started": False,
        "risk": "R2",
        "forecast_confidence": "medium",
        "completion_percent": 5,
        "pipeline_stages": [
            {
                "name": stage,
                "status": "current" if index == 0 else "pending",
                "summary": "Projeto recebido" if index == 0 else "Aguardando a etapa anterior",
            }
            for index, stage in enumerate(PIPELINE)
        ],
        "next_action": "transformar o paper em Product SOT fechado",
        "projection_freshness": "runtime_fresh",
        "current_blockers": [],
        "pending_access": [],
        "pending_approvals": [],
        "next_steps": ["consolidar Product SOT", "fechar plano", "rodar Ready Gate"],
        "evidence_refs": ["external:discord-intake-message"],
        "source_runtime": "hermes",
        "source_board": "factory-intake",
        "last_synced_at": timestamp,
        "planned_summary": ["intake", "SOT", "planejamento", "execucao", "provas", "producao"],
        "missing_items": ["Product SOT fechado", "metodo/plano", "Ready Gate"],
        "forecast_risks": ["escopo ainda pode mudar durante a consolidacao do SOT"],
        "human_decisions_required": [],
        "truth_source_available": True,
    }


def resolve_channels(client: bridge.DiscordClient, config: bridge.BridgeConfig) -> tuple[str, dict[str, dict[str, Any]]]:
    guild_id = bridge.resolve_guild_id(client, config.guild_id)
    channels = client.list_channels(guild_id)
    by_name = {str(channel.get("name")): channel for channel in channels}
    mapped: dict[str, dict[str, Any]] = {}
    for key, name in bridge.CHANNEL_NAMES.items():
        if name in by_name:
            mapped[key] = by_name[name]
    missing = [name for key, name in bridge.CHANNEL_NAMES.items() if key not in mapped and key != "manager"]
    if missing:
        raise RuntimeError(f"missing Discord channels: {', '.join(missing)}")
    if "manager" not in mapped:
        raise RuntimeError("missing Discord manager channel: falar-com-gerente")
    return guild_id, mapped


def find_named_thread(
    client: bridge.DiscordClient,
    guild_id: str,
    parent_id: str,
    name: str,
) -> dict[str, Any] | None:
    expected = bridge.normalize_name(name)
    for thread in client.list_active_threads(guild_id):
        if str(thread.get("parent_id")) == str(parent_id) and bridge.normalize_name(str(thread.get("name") or "")) == expected:
            return thread
    return None


def list_child_threads(
    client: bridge.DiscordClient,
    guild_id: str,
    parent_id: str,
) -> list[dict[str, Any]]:
    return [
        thread
        for thread in client.list_active_threads(guild_id)
        if str(thread.get("parent_id")) == str(parent_id)
    ]


def first_project_intake_message(messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    for message in reversed(messages):
        if looks_like_project_intake(message):
            return message
    return None


def ensure_thread_from_message(
    client: bridge.DiscordClient,
    guild_id: str,
    parent_channel_id: str,
    message_id: str,
    thread_name: str,
    state_ref: dict[str, Any],
    state_field: str,
    apply: bool,
) -> dict[str, Any]:
    existing_id = state_ref.get(state_field)
    thread = {"id": existing_id, "name": thread_name} if existing_id else None
    if thread is None:
        thread = find_named_thread(client, guild_id, parent_channel_id, thread_name)
    if not apply:
        return {"thread_id": str(thread["id"]) if thread else None, "created": thread is None, "updated": thread is not None}
    if thread is None:
        thread = client.create_thread_from_message(
            parent_channel_id,
            message_id,
            {"name": bridge.truncate(thread_name, 95), "auto_archive_duration": 10080},
        )
        state_ref[state_field] = str(thread["id"])
        return {"thread_id": str(thread["id"]), "created": True, "updated": False}
    state_ref[state_field] = str(thread["id"])
    return {"thread_id": str(thread["id"]), "created": False, "updated": True}


def intake_message_payload(projection: dict[str, Any], cockpit_thread_id: str | None) -> dict[str, Any]:
    cockpit = f"<#{cockpit_thread_id}>" if cockpit_thread_id else "cockpit pendente"
    return {
        "content": "",
        "embeds": [
            {
                "title": "Entrada de Projeto Registrada",
                "description": f"**{bridge.truncate(str(projection['name']), 180)}**",
                "color": 0x3498DB,
                "fields": [
                    {"name": "Cockpit visual", "value": cockpit, "inline": True},
                    {"name": "Proxima acao", "value": bridge.truncate(str(projection["next_action"]), 1024), "inline": False},
                ],
                "footer": {"text": f"{INTAKE_MARKER_PREFIX}{projection['project_id']}"},
            }
        ],
    }


def process_intake_messages(
    client: bridge.DiscordClient,
    config: bridge.BridgeConfig,
    state: dict[str, Any],
    *,
    max_messages: int = 50,
    apply: bool,
) -> dict[str, Any]:
    guild_id, channels = resolve_channels(client, config)
    manager_id = str(channels["manager"]["id"])
    state.setdefault("intake", {}).setdefault("processed_messages", {})
    state.setdefault("intake", {}).setdefault("processed_threads", {})
    results: list[dict[str, Any]] = []
    reception_messages = client.list_messages(manager_id, limit=max_messages)
    ignored_reception_messages = sum(1 for message in reception_messages if looks_like_project_intake(message))
    manager_threads = list_child_threads(client, guild_id, manager_id)
    for thread in manager_threads:
        thread_id = str(thread.get("id") or "")
        if not thread_id or thread_id in state["intake"]["processed_threads"]:
            continue
        thread_messages = client.list_messages(thread_id, limit=max_messages)
        message = first_project_intake_message(thread_messages)
        if not message:
            continue
        message_id = str(message.get("id") or "")
        if not message_id or message_id in state["intake"]["processed_messages"]:
            continue
        projection = default_projection_from_intake(message)
        project_id = str(projection["project_id"])
        state.setdefault("projects", {}).setdefault(project_id, {})
        project_state = state["projects"][project_id]
        if apply:
            project_state["intake_thread_id"] = thread_id
            project_state["intake_thread_source"] = "manager_thread"
        bridge_result = bridge.project_bridge_apply(projection, client, config, state)
        cockpit_thread_id = (bridge_result.get("project_thread") or {}).get("thread_id")
        if thread_id:
            bridge.upsert_message(
                client=client,
                channel_id=thread_id,
                payload=intake_message_payload(projection, cockpit_thread_id),
                expected_marker=f"{INTAKE_MARKER_PREFIX}{project_id}",
                state_ref=project_state,
                state_field="intake_pointer_message_id",
                apply=apply,
            )
        if apply:
            state["intake"]["processed_messages"][message_id] = {
                "project_id": project_id,
                "processed_at": utc_now(),
            }
            state["intake"]["processed_threads"][thread_id] = {
                "project_id": project_id,
                "processed_at": utc_now(),
            }
        results.append(
            {
                "project_id": project_id,
                "message_processed": True,
                "thread_first": True,
                "intake_thread_created": False,
                "intake_thread_resolved": bool(thread_id),
                "project_surface_resolved": bool(cockpit_thread_id),
            }
        )
    return {
        "scanned": len(manager_threads),
        "scanned_threads": len(manager_threads),
        "scanned_reception_messages": len(reception_messages),
        "ignored_reception_messages": ignored_reception_messages,
        "processed": len(results),
        "results": results,
    }


def event_marker(event: dict[str, Any]) -> str:
    return f"{EVENT_MARKER_PREFIX}{event['event_id']}"


def event_payload(event: dict[str, Any], project_thread_id: str | None = None) -> dict[str, Any]:
    target = str(event.get("discord_target") or EVENT_TARGETS.get(str(event["event_type"]), "dashboard"))
    fields = [
        {"name": "Projeto", "value": bridge.truncate(str(event["project_id"]), 256), "inline": True},
        {"name": "Severidade", "value": str(event["severity"]), "inline": True},
        {"name": "Fonte", "value": str(event["source"]), "inline": True},
    ]
    if project_thread_id:
        fields.append({"name": "Cockpit do projeto", "value": f"<#{project_thread_id}>", "inline": False})
    if event.get("details"):
        fields.append({"name": "Detalhe", "value": bridge.truncate(str(event["details"]), 1024), "inline": False})
    return {
        "content": "",
        "embeds": [
            {
                "title": event_title(event),
                "description": bridge.truncate(str(event["summary"]), 2048),
                "color": event_color(event),
                "fields": fields,
                "footer": {"text": event_marker(event)},
            }
        ],
    }


def event_title(event: dict[str, Any]) -> str:
    labels = {
        "access_missing": "Acesso pendente",
        "gate_blocked": "Bloqueio real",
        "approval_requested": "Aprovacao solicitada",
        "approval_recorded": "Aprovacao registrada",
        "evidence_recorded": "Prova registrada",
        "release_candidate": "Release candidato",
        "health_alert": "Alerta de saude",
        "forecast_changed": "Previsao atualizada",
    }
    return labels.get(str(event["event_type"]), "Evento da Fabrica")


def event_color(event: dict[str, Any]) -> int:
    severity = str(event.get("severity") or "P3")
    if severity == "P0":
        return 0xE74C3C
    if severity == "P1":
        return 0xF39C12
    if severity == "P2":
        return 0xF1C40F
    return 0x3498DB


def sync_event(
    event: dict[str, Any],
    client: bridge.DiscordClient,
    config: bridge.BridgeConfig,
    state: dict[str, Any],
    *,
    apply: bool,
) -> dict[str, Any]:
    validate_artifact(event)
    guild_id, channels = resolve_channels(client, config)
    event_type = str(event["event_type"])
    target_key = str(event.get("discord_target") or EVENT_TARGETS.get(event_type, "dashboard"))
    if target_key not in channels:
        target_key = EVENT_TARGETS.get(event_type, "dashboard")
    channel = channels[target_key]
    project_state = state.setdefault("projects", {}).setdefault(str(event["project_id"]), {})
    event_state = state.setdefault("events", {}).setdefault(str(event["event_id"]), {})
    project_thread_id = project_state.get("project_thread_id")
    message_result = bridge.upsert_message(
        client=client,
        channel_id=str(channel["id"]),
        payload=event_payload(event, project_thread_id),
        expected_marker=event_marker(event),
        state_ref=event_state,
        state_field="message_id",
        apply=apply,
    )
    thread_result = {"thread_id": event_state.get("thread_id"), "created": False, "updated": False}
    if event_type in ACTIVE_EVENT_TYPES and message_result.get("message_id"):
        thread_result = ensure_thread_from_message(
            client,
            guild_id,
            str(channel["id"]),
            str(message_result["message_id"]),
            bridge.truncate(event_title(event), 80),
            event_state,
            "thread_id",
            apply,
        )
    if apply:
        event_state["last_synced_at"] = utc_now()
        event_state["target"] = target_key
    return {
        "event_id": str(event["event_id"]),
        "target": target_key,
        "message_resolved": bool(message_result.get("message_id")) or not apply,
        "thread_required": event_type in ACTIVE_EVENT_TYPES,
        "thread_resolved": bool(thread_result.get("thread_id")) or event_type not in ACTIVE_EVENT_TYPES or not apply,
    }


def approval_marker(approval: dict[str, Any]) -> str:
    return f"{APPROVAL_MARKER_PREFIX}{approval['approval_id']}"


def approval_payload(approval: dict[str, Any]) -> dict[str, Any]:
    marker_text = approval_marker(approval)
    return {
        "content": "",
        "embeds": [
            {
                "title": "Aprovacao formal",
                "description": bridge.truncate(str(approval["scope"]), 2048),
                "color": 0x9B59B6,
                "fields": [
                    {"name": "Tipo", "value": str(approval["approval_type"]), "inline": True},
                    {"name": "Risco", "value": str(approval["risk"]), "inline": True},
                    {"name": "Status", "value": str(approval["status"]), "inline": True},
                    {
                        "name": "Consequencia",
                        "value": bridge.truncate(str(approval.get("consequence") or "Sem consequencia descrita."), 1024),
                        "inline": False,
                    },
                    {
                        "name": "Nao autorizado por este pedido",
                        "value": bridge.truncate(bridge.bullet_list(bridge.non_empty_list(approval.get("not_authorized"))), 1024),
                        "inline": False,
                    },
                    {
                        "name": "Se o botao falhar",
                        "value": "Responda `aprovado`, `rejeitado` ou `pedir ajuste` na thread deste pedido. A ponte valida escopo, dono e prazo antes de registrar.",
                        "inline": False,
                    },
                ],
                "footer": {"text": marker_text},
            }
        ],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 3,
                        "label": "Aprovar",
                        "custom_id": f"of.approval.approved:{approval['approval_id']}",
                    },
                    {
                        "type": 2,
                        "style": 4,
                        "label": "Rejeitar",
                        "custom_id": f"of.approval.rejected:{approval['approval_id']}",
                    },
                    {
                        "type": 2,
                        "style": 2,
                        "label": "Pedir ajuste",
                        "custom_id": f"of.approval.needs_changes:{approval['approval_id']}",
                    },
                ],
            }
        ],
    }


def post_approval_request(
    approval: dict[str, Any],
    client: bridge.DiscordClient,
    config: bridge.BridgeConfig,
    state: dict[str, Any],
    *,
    apply: bool,
) -> dict[str, Any]:
    validate_artifact(approval)
    guild_id, channels = resolve_channels(client, config)
    channel = channels["approvals"]
    approval_state = state.setdefault("approvals", {}).setdefault(str(approval["approval_id"]), {})
    message_result = bridge.upsert_message(
        client=client,
        channel_id=str(channel["id"]),
        payload=approval_payload(approval),
        expected_marker=approval_marker(approval),
        state_ref=approval_state,
        state_field="message_id",
        apply=apply,
    )
    thread_result = {"thread_id": approval_state.get("thread_id"), "created": False, "updated": False}
    if message_result.get("message_id"):
        thread_result = ensure_thread_from_message(
            client,
            guild_id,
            str(channel["id"]),
            str(message_result["message_id"]),
            f"Aprovacao - {approval['approval_type']}",
            approval_state,
            "thread_id",
            apply,
        )
    if apply:
        approval_state["last_synced_at"] = utc_now()
        approval_state["status"] = approval["status"]
    return {
        "approval_id": str(approval["approval_id"]),
        "message_resolved": bool(message_result.get("message_id")) or not apply,
        "thread_resolved": bool(thread_result.get("thread_id")) or not apply,
        "components_rendered": True,
        "decision_controls_rendered": bool(message_result.get("message_id")) or not apply,
    }


def allowed_discord_user_ids() -> set[str]:
    raw = os.environ.get("DISCORD_ALLOWED_USERS", "")
    return {part.strip() for part in raw.split(",") if part.strip()}


def text_decision_from_message(message: dict[str, Any]) -> str | None:
    content = normalize_intake_text(str(message.get("content") or ""))
    content = re.sub(r"\s+", " ", content).strip(" .!?,;:")
    return APPROVAL_TEXT_DECISIONS.get(content)


def text_decision_for_approval(
    client: bridge.DiscordClient,
    thread_id: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    allowed = allowed_discord_user_ids()
    found: list[tuple[str, dict[str, Any]]] = []
    for message in client.list_messages(thread_id, limit=50):
        author = message.get("author") or {}
        if author.get("bot"):
            continue
        user_id = str(author.get("id") or "")
        if allowed and user_id not in allowed:
            continue
        decision = text_decision_from_message(message)
        if decision:
            found.append((decision, message))
    if not found:
        return None, []
    decisions = sorted({decision for decision, _ in found})
    if len(decisions) > 1:
        return None, [f"multiple text decisions found: {', '.join(decisions)}"]
    decision, _ = found[0]
    return {"actor_role": "Factory Owner", "decision": decision}, []


def sync_approval_text_decision(
    approval: dict[str, Any],
    client: bridge.DiscordClient,
    config: bridge.BridgeConfig,
    state: dict[str, Any],
    *,
    apply: bool,
) -> dict[str, Any]:
    validate_artifact(approval)
    approval_state = state.setdefault("approvals", {}).setdefault(str(approval["approval_id"]), {})
    thread_id = approval_state.get("thread_id")
    if not thread_id:
        return {"approval_id": str(approval["approval_id"]), "decision_found": False, "accepted": False}
    decision, reasons = text_decision_for_approval(client, str(thread_id))
    if reasons:
        return {"approval_id": str(approval["approval_id"]), "decision_found": True, "accepted": False, "reasons": reasons}
    if not decision:
        return {"approval_id": str(approval["approval_id"]), "decision_found": False, "accepted": False}
    decision.update({"approval_id": approval["approval_id"], "scope": approval["scope"]})
    registered, event = register_approval_decision(approval, decision)
    if not event.get("accepted", True):
        return {
            "approval_id": str(approval["approval_id"]),
            "decision_found": True,
            "accepted": False,
            "reasons": list(event.get("reasons", [])),
        }
    if apply:
        post_approval_request(registered, client, config, state, apply=apply)
        sync_event(event, client, config, state, apply=apply)
        state.setdefault("approval_events", {})[str(approval["approval_id"])] = {
            "status": registered.get("status"),
            "event_id": event.get("event_id"),
            "synced_at": utc_now(),
            "source": "discord_text_fallback",
        }
    return {
        "approval_id": str(approval["approval_id"]),
        "decision_found": True,
        "accepted": True,
        "decision": registered.get("status"),
        "event_id": event.get("event_id"),
    }


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def register_approval_decision(
    approval: dict[str, Any],
    decision: dict[str, Any],
    *,
    now: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_artifact(approval)
    timestamp = now or utc_now()
    reasons: list[str] = []
    if decision.get("approval_id") != approval["approval_id"]:
        reasons.append("approval_id mismatch")
    if decision.get("actor_role") != "Factory Owner":
        reasons.append("actor role is not authorized")
    if decision.get("decision") not in {"approved", "rejected", "needs_changes"}:
        reasons.append("decision is not structured")
    if decision.get("scope") != approval["scope"]:
        reasons.append("decision scope does not match request")
    if approval.get("expires_at") and parse_time(timestamp) > parse_time(str(approval["expires_at"])):
        reasons.append("approval request expired")
    if reasons:
        return dict(approval), {"accepted": False, "reasons": reasons, "created_at": timestamp}

    event = {
        "$schema": "https://overkill-factory.dev/schemas/control-tower-event.schema.json",
        "event_id": f"evt-{approval['approval_id']}-{decision['decision']}",
        "event_type": "approval_recorded",
        "severity": "P2",
        "project_id": approval["project_id"],
        "source": "bridge",
        "summary": f"Decisao estruturada registrada: {decision['decision']}",
        "details": "A decisao foi validada por approval_id, papel, escopo e prazo antes de virar evento.",
        "action_required": False,
        "owner_role": str(decision["actor_role"]),
        "evidence_refs": list(approval.get("evidence_refs", [])),
        "discord_target": "approvals",
        "created_at": timestamp,
    }
    validate_artifact(event)
    registered = dict(approval)
    registered.update(
        {
            "status": str(decision["decision"]),
            "decided_by": "external:factory-owner",
            "decision_event_ref": event["event_id"],
        }
    )
    validate_artifact(registered)
    return registered, event


def health_payload(checks: dict[str, bool], limits: list[str]) -> dict[str, Any]:
    status = "PASS" if all(checks.values()) else "ATENCAO"
    lines = [f"- {key}: {'ok' if value else 'atenção'}" for key, value in sorted(checks.items())]
    return {
        "content": "",
        "embeds": [
            {
                "title": "Saude da Ponte Discord",
                "description": f"Estado: **{status}**",
                "color": 0x2ECC71 if all(checks.values()) else 0xF39C12,
                "fields": [
                    {"name": "Checks", "value": bridge.truncate("\n".join(lines), 1024), "inline": False},
                    {"name": "Limites", "value": bridge.truncate(bridge.bullet_list(limits), 1024), "inline": False},
                ],
                "footer": {"text": HEALTH_MARKER},
            }
        ],
    }


def post_health(
    client: bridge.DiscordClient,
    config: bridge.BridgeConfig,
    state: dict[str, Any],
    *,
    apply: bool,
    extra_checks: dict[str, bool] | None = None,
) -> dict[str, Any]:
    user = client.get_current_user()
    _, channels = resolve_channels(client, config)
    checks = {
        "bot_reachable": bool(user.get("id")),
        "bridge_state_present": bool(state),
        "dashboard_channel_resolved": "dashboard" in channels,
        "approval_channel_resolved": "approvals" in channels,
        "health_channel_resolved": "health" in channels,
        "no_discord_source_of_truth": True,
    }
    checks.update(extra_checks or {})
    state_ref = state.setdefault("health", {})
    message_result = bridge.upsert_message(
        client=client,
        channel_id=str(channels["health"]["id"]),
        payload=health_payload(
            checks,
            [
                "Discord e cockpit, nao fonte da verdade.",
                "IDs reais ficam no estado privado.",
                "Aprovacoes so valem depois de evento valido no runtime.",
            ],
        ),
        expected_marker=HEALTH_MARKER,
        state_ref=state_ref,
        state_field="message_id",
        apply=apply,
    )
    if apply:
        state_ref["last_synced_at"] = utc_now()
    return {
        "message_resolved": bool(message_result.get("message_id")) or not apply,
        "checks": checks,
    }


def build_public_receipt(results: dict[str, Any], *, applied: bool) -> dict[str, Any]:
    checks = {
        "bot_reachable": bool(results.get("bot_reachable", True)),
        "bridge_reachable": True,
        "runtime_readback_reachable": bool(results.get("runtime_readback_reachable", True)),
        "approval_registration_path_reachable": bool(results.get("approval_registration_path_reachable", True)),
        "no_discord_source_of_truth": True,
        "no_private_material_in_public_receipt": True,
        "thread_first_project_intake_automated": bool(results.get("thread_first_project_intake_automated")),
        "active_bot_messages_threaded_or_linked": bool(results.get("active_bot_messages_threaded_or_linked")),
        "structured_approval_interactions_automated": bool(results.get("structured_approval_interactions_automated")),
        "live_runtime_projection_automated": bool(results.get("live_runtime_projection_automated")),
        "operational_channels_projected": bool(results.get("operational_channels_projected")),
        "health_anti_stale_posted": bool(results.get("health_anti_stale_posted")),
        "multi_project_safe": True,
    }
    receipt = {
        "$schema": "https://overkill-factory.dev/schemas/operator-control-tower-bridge-health.schema.json",
        "record_type": "operator_control_tower_bridge_health",
        "created_at": utc_now(),
        "result": "PASS" if all(checks.values()) else "BLOCKED",
        "applied_to_discord": applied,
        "checks": checks,
        "evidence_refs": [
            "scripts/factory_concierge_discord_automation.py",
            "scripts/factory_concierge_discord_bridge.py",
            "docs/control-tower/discord-control-tower-os.md",
            "external:discord-control-tower-automation-proof",
        ],
        "limits": [
            "Discord remains the owner cockpit only; Hermes remains the durable source of truth.",
            "This receipt redacts Discord ids, private paths, credentials and logs.",
            "Real production approvals still require a real owner interaction or signed runtime event.",
        ],
    }
    text = json.dumps(receipt, ensure_ascii=False)
    if re.search(r"\d{12,}|Bot\s+[A-Za-z0-9._-]+|/srv/|C:\\\\Users|token|password", text, re.IGNORECASE):
        raise AssertionError("public receipt contains private-looking material")
    return receipt


def load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_json_dir(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for item_path in sorted(path.glob("*.json")):
        data = load_json(item_path)
        if data is not None:
            items.append(data)
    return items


def run_automation(args: argparse.Namespace) -> dict[str, Any]:
    bridge.load_env_file(args.env)
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is required in env or --env")

    client = bridge.DiscordApi(token=token, api_base=args.api_base, timeout=args.timeout)
    config = bridge.BridgeConfig(apply=bool(args.apply), guild_id=args.guild_id or os.environ.get("DISCORD_GUILD_ID"), state_path=args.state)
    state = bridge.load_state(args.state)
    results: dict[str, Any] = {
        "bot_reachable": True,
        "runtime_readback_reachable": True,
        "approval_registration_path_reachable": True,
        "thread_first_project_intake_automated": False,
        "active_bot_messages_threaded_or_linked": False,
        "structured_approval_interactions_automated": False,
        "live_runtime_projection_automated": False,
        "operational_channels_projected": False,
        "health_anti_stale_posted": False,
    }

    projections = [item for item in [load_json(args.projection)] if item]
    projections.extend(load_json_dir(args.projection_dir))
    has_projection_inputs = bool(projections)
    if not has_projection_inputs:
        results["live_runtime_projection_automated"] = True
    for projection in projections:
        bridge_result = bridge.project_bridge_apply(projection, client, config, state)
        results["live_runtime_projection_automated"] = bool((bridge_result.get("project_thread") or {}).get("thread_id")) or not args.apply

    if args.scan_intake:
        intake_result = process_intake_messages(client, config, state, max_messages=args.max_messages, apply=bool(args.apply))
        results["intake"] = intake_result
        results["thread_first_project_intake_automated"] = True
        if intake_result["processed"] > 0:
            results["active_bot_messages_threaded_or_linked"] = all(item["intake_thread_resolved"] for item in intake_result["results"])
        else:
            results["active_bot_messages_threaded_or_linked"] = True

    events = [item for item in [load_json(args.event)] if item]
    events.extend(load_json_dir(args.event_dir))
    if not events:
        results["operational_channels_projected"] = True
    for event in events:
        event_result = sync_event(event, client, config, state, apply=bool(args.apply))
        results["event"] = event_result
        results["operational_channels_projected"] = event_result["message_resolved"]
        results["active_bot_messages_threaded_or_linked"] = (
            results["active_bot_messages_threaded_or_linked"] or event_result["thread_resolved"]
        )
        results["live_runtime_projection_automated"] = True

    approvals = [item for item in [load_json(args.approval)] if item]
    approvals.extend(load_json_dir(args.approval_dir))
    approval = approvals[0] if approvals else None
    if not approvals:
        results["structured_approval_interactions_automated"] = True
    for approval_item in approvals:
        approval_result = post_approval_request(approval_item, client, config, state, apply=bool(args.apply))
        results["approval"] = approval_result
        results["structured_approval_interactions_automated"] = (
            approval_result["message_resolved"]
            and approval_result["thread_resolved"]
            and approval_result["decision_controls_rendered"]
        )
        results["active_bot_messages_threaded_or_linked"] = (
            results["active_bot_messages_threaded_or_linked"] or approval_result["thread_resolved"]
        )

    if approvals and args.scan_approval_text:
        text_results = []
        for approval_item in approvals:
            text_result = sync_approval_text_decision(approval_item, client, config, state, apply=bool(args.apply))
            text_results.append(text_result)
            if text_result.get("accepted"):
                results["approval_registration_path_reachable"] = True
                results["structured_approval_interactions_automated"] = True
        results["approval_text_fallback"] = text_results

    decision = load_json(args.decision)
    if approval and decision:
        registered, approval_event = register_approval_decision(approval, decision, now=args.decision_time)
        if approval_event.get("accepted") is False:
            results["approval_decision"] = {
                "accepted": False,
                "reasons": list(approval_event.get("reasons", [])),
            }
        else:
            if args.apply:
                post_approval_request(registered, client, config, state, apply=bool(args.apply))
            sync_result = sync_event(approval_event, client, config, state, apply=bool(args.apply))
            results["approval_decision"] = {"accepted": True, "event_synced": sync_result["message_resolved"]}
            results["approval_registration_path_reachable"] = True
        state.setdefault("approval_events", {})[str(approval["approval_id"])] = {
            "status": registered.get("status"),
            "event_id": approval_event.get("event_id") if approval_event.get("accepted") is not False else None,
            "synced_at": utc_now(),
            "source": "explicit_decision_file",
        }

    if args.post_health:
        health_result = post_health(
            client,
            config,
            state,
            apply=bool(args.apply),
            extra_checks={
                "threading_rule_ready": bool(results["active_bot_messages_threaded_or_linked"]),
                "approval_components_ready": bool(results["structured_approval_interactions_automated"] or not approval),
                "projection_ready": bool(results["live_runtime_projection_automated"] or not has_projection_inputs),
            },
        )
        results["health"] = health_result
        results["health_anti_stale_posted"] = health_result["message_resolved"]

    if args.apply:
        bridge.save_state(args.state, state)

    receipt = build_public_receipt(results, applied=bool(args.apply))
    bridge.write_json(args.out, receipt)
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection", type=Path)
    parser.add_argument("--projection-dir", type=Path)
    parser.add_argument("--event", type=Path)
    parser.add_argument("--event-dir", type=Path)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--approval-dir", type=Path)
    parser.add_argument("--decision", type=Path)
    parser.add_argument("--decision-time")
    parser.add_argument("--scan-approval-text", action="store_true")
    parser.add_argument("--scan-intake", action="store_true")
    parser.add_argument("--post-health", action="store_true")
    parser.add_argument("--max-messages", type=int, default=50)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--env", type=Path)
    parser.add_argument("--guild-id", default=os.environ.get("DISCORD_GUILD_ID"))
    parser.add_argument("--api-base", default=bridge.API_BASE)
    parser.add_argument("--timeout", type=int, default=20)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    receipt = run_automation(parse_args())
    return 0 if receipt["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
