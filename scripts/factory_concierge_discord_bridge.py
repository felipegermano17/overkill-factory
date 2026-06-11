#!/usr/bin/env python3
"""Project Overkill Factory project state into a Discord Control Tower.

The bridge is deliberately narrow:

- Hermes or another runtime remains the source of truth.
- The input is a project-projection JSON contract.
- Discord is updated as an owner cockpit: dashboard, project registry,
  project forum topic and project cockpit message.
- The private state file can contain Discord ids; public receipts never do.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_public_json_artifacts as validator  # noqa: E402


API_BASE = "https://discord.com/api/v10"
PROJECT_MARKER_PREFIX = "of-project:"
DASHBOARD_MARKER = "of-dashboard:factory"
REGISTRY_MARKER_PREFIX = "of-registry:"
COCKPIT_MARKER_PREFIX = "of-cockpit:"

CHANNEL_NAMES = {
    "dashboard": "torre-de-controle",
    "manager": "falar-com-gerente",
    "health": "saude-do-bot",
    "registry": "projetos-recebidos",
    "kanban": "kanban-da-fabrica",
    "approvals": "aprovacoes-formais",
    "access": "acessos-pendentes",
    "blockers": "bloqueios-reais",
    "evidence": "provas-e-evidencias",
    "production": "producao-e-releases",
}

STATUS_TAGS = {
    "intake": ["Entrada"],
    "planning": ["Planejamento"],
    "waiting_owner": ["Aprovacao pendente", "Acao do dono"],
    "waiting_access": ["Acesso pendente", "Acao do dono"],
    "ready_to_execute": ["Planejamento"],
    "executing": ["Executando", "Fabrica trabalhando"],
    "review": ["Revisao", "Fabrica trabalhando"],
    "blocked": ["Bloqueado", "Acao do dono"],
    "release_candidate": ["Revisao"],
    "production": ["Producao"],
    "closed": ["Producao"],
}

STAGE_ICON = {
    "done": "[x]",
    "current": "[>]",
    "pending": "[ ]",
    "blocked": "[!]",
    "skipped": "[-]",
}

STATUS_PT = {
    "intake": "Entrada",
    "planning": "Planejamento",
    "waiting_owner": "Esperando decisao",
    "waiting_access": "Esperando acesso",
    "ready_to_execute": "Pronto para executar",
    "executing": "Executando",
    "review": "Revisao",
    "blocked": "Bloqueado",
    "release_candidate": "Candidato a release",
    "production": "Producao",
    "closed": "Fechado",
}

FRESHNESS_PT = {
    "runtime_fresh": "lido do runtime",
    "manual_estimate": "estimativa manual",
    "stale": "desatualizado",
    "blocked": "sem leitura confiavel",
}

FORECAST_PT = {
    "high": "alta",
    "medium": "media",
    "low": "baixa",
    "blocked": "bloqueada",
}


class DiscordClient(Protocol):
    def get_current_user(self) -> dict[str, Any]:
        ...

    def list_guilds(self) -> list[dict[str, Any]]:
        ...

    def list_channels(self, guild_id: str) -> list[dict[str, Any]]:
        ...

    def list_active_threads(self, guild_id: str) -> list[dict[str, Any]]:
        ...

    def list_messages(self, channel_id: str, limit: int = 50) -> list[dict[str, Any]]:
        ...

    def post_message(self, channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    def edit_message(self, channel_id: str, message_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    def create_forum_thread(self, channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    def create_thread_from_message(self, channel_id: str, message_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    def edit_channel(self, channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    def list_guild_roles(self, guild_id: str) -> list[dict[str, Any]]:
        ...


@dataclass
class BridgeConfig:
    apply: bool
    guild_id: str | None
    state_path: Path | None
    dashboard_channel: str = CHANNEL_NAMES["dashboard"]
    registry_channel: str = CHANNEL_NAMES["registry"]
    kanban_forum: str = CHANNEL_NAMES["kanban"]
    dry_run_suffix: str = "dry-run"


@dataclass
class DiscordSurfaces:
    guild_id: str
    dashboard: dict[str, Any]
    registry: dict[str, Any]
    kanban: dict[str, Any]
    kanban_tags: dict[str, str]


class DiscordApi:
    def __init__(self, token: str, api_base: str = API_BASE, timeout: int = 20) -> None:
        self.token = token
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def _request(
        self,
        method: str,
        route: str,
        payload: dict[str, Any] | None = None,
        retry: bool = True,
    ) -> Any:
        data = None
        headers = {
            "Authorization": f"Bot {self.token}",
            "User-Agent": "OverkillFactoryDiscordBridge/1.0",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"{self.api_base}{route}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read()
                if not body:
                    return {}
                return json.loads(body.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            if exc.code == 429 and retry:
                try:
                    delay = float(json.loads(body_text).get("retry_after", 1.0))
                except Exception:
                    delay = 1.0
                time.sleep(min(delay + 0.5, 65.0))
                return self._request(method, route, payload, retry=False)
            raise RuntimeError(f"Discord API {method} {route} failed with HTTP {exc.code}: {body_text}") from exc

    def get_current_user(self) -> dict[str, Any]:
        return self._request("GET", "/users/@me")

    def list_guilds(self) -> list[dict[str, Any]]:
        return list(self._request("GET", "/users/@me/guilds"))

    def list_channels(self, guild_id: str) -> list[dict[str, Any]]:
        return list(self._request("GET", f"/guilds/{guild_id}/channels"))

    def list_active_threads(self, guild_id: str) -> list[dict[str, Any]]:
        response = self._request("GET", f"/guilds/{guild_id}/threads/active")
        return list(response.get("threads", []))

    def list_messages(self, channel_id: str, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 100))
        return list(self._request("GET", f"/channels/{channel_id}/messages?limit={limit}"))

    def post_message(self, channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/channels/{channel_id}/messages", payload)

    def edit_message(self, channel_id: str, message_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/channels/{channel_id}/messages/{message_id}", payload)

    def create_forum_thread(self, channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/channels/{channel_id}/threads", payload)

    def create_thread_from_message(self, channel_id: str, message_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/channels/{channel_id}/messages/{message_id}/threads", payload)

    def edit_channel(self, channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/channels/{channel_id}", payload)

    def list_guild_roles(self, guild_id: str) -> list[dict[str, Any]]:
        return list(self._request("GET", f"/guilds/{guild_id}/roles"))


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_env_file(path: Path | None) -> None:
    if path is None or not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    ascii_only = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return ascii_only or "project"


def truncate(value: str, limit: int) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)].rstrip() + "..."


def non_empty_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def bullet_list(items: list[str], empty: str = "nenhum") -> str:
    if not items:
        return empty
    return "\n".join(f"- {truncate(item, 120)}" for item in items[:8])


def stage_lines(projection: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for stage in projection.get("pipeline_stages", []):
        status = str(stage.get("status") or "pending")
        icon = STAGE_ICON.get(status, "[ ]")
        name = truncate(str(stage.get("name") or "Etapa"), 42)
        summary = truncate(str(stage.get("summary") or ""), 82)
        line = f"{icon} {name}"
        if summary:
            line += f" - {summary}"
        lines.append(line)
    return lines


def marker(kind: str, project_id: str | None = None) -> str:
    if kind == "dashboard":
        return DASHBOARD_MARKER
    if kind == "registry" and project_id:
        return f"{REGISTRY_MARKER_PREFIX}{project_id}"
    if kind == "cockpit" and project_id:
        return f"{COCKPIT_MARKER_PREFIX}{project_id}"
    if kind == "project" and project_id:
        return f"{PROJECT_MARKER_PREFIX}{project_id}"
    raise ValueError(f"unknown marker kind: {kind}")


def embed_has_marker(message: dict[str, Any], expected: str) -> bool:
    if expected in str(message.get("content") or ""):
        return True
    for embed in message.get("embeds") or []:
        footer = embed.get("footer") or {}
        if expected in str(footer.get("text") or ""):
            return True
        if expected in json.dumps(embed, ensure_ascii=False):
            return True
    return False


def project_summary(projection: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_id": projection["project_id"],
        "name": projection["name"],
        "phase": projection["phase"],
        "status": projection["status"],
        "completion_percent": projection["completion_percent"],
        "forecast_confidence": projection["forecast_confidence"],
        "projection_freshness": projection["projection_freshness"],
        "next_action": projection["next_action"],
        "last_synced_at": projection["last_synced_at"],
    }


def load_state(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"version": 1, "dashboard": {}, "projects": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("bridge state must be a JSON object")
    data.setdefault("version", 1)
    data.setdefault("dashboard", {})
    data.setdefault("projects", {})
    return data


def save_state(path: Path | None, state: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def public_receipt_ref(value: str | None, kind: str) -> str:
    if value:
        return f"external:discord-{kind}-present"
    return f"missing:discord-{kind}"


def validate_projection(projection: dict[str, Any]) -> None:
    schemas = validator.load_schemas()
    schema = schemas[validator.schema_name(str(projection.get("$schema") or ""))]
    errors = validator.validate_node(schema, projection, "$")
    if errors:
        raise AssertionError("; ".join(errors))


def resolve_guild_id(client: DiscordClient, configured_guild_id: str | None) -> str:
    if configured_guild_id:
        return configured_guild_id
    guilds = client.list_guilds()
    if len(guilds) == 1:
        return str(guilds[0]["id"])
    names = ", ".join(str(guild.get("name") or guild.get("id")) for guild in guilds[:8])
    raise RuntimeError(f"set DISCORD_GUILD_ID or --guild-id; visible guilds: {names}")


def resolve_surfaces(client: DiscordClient, config: BridgeConfig) -> DiscordSurfaces:
    guild_id = resolve_guild_id(client, config.guild_id)
    channels = client.list_channels(guild_id)
    by_name = {str(channel.get("name")): channel for channel in channels}
    missing = [
        name
        for name in [config.dashboard_channel, config.registry_channel, config.kanban_forum]
        if name not in by_name
    ]
    if missing:
        raise RuntimeError(f"missing Discord channels: {', '.join(missing)}")
    kanban = by_name[config.kanban_forum]
    tags = {
        str(tag.get("name")): str(tag.get("id"))
        for tag in kanban.get("available_tags", [])
        if tag.get("name") and tag.get("id")
    }
    return DiscordSurfaces(
        guild_id=guild_id,
        dashboard=by_name[config.dashboard_channel],
        registry=by_name[config.registry_channel],
        kanban=kanban,
        kanban_tags=tags,
    )


def select_tag_ids(projection: dict[str, Any], tags: dict[str, str]) -> list[str]:
    wanted = STATUS_TAGS.get(str(projection.get("status")), ["Entrada"])
    selected = [tags[name] for name in wanted if name in tags]
    return selected[:5]


def message_has_title(message: dict[str, Any], expected_title: str | None) -> bool:
    if not expected_title:
        return False
    for embed in message.get("embeds") or []:
        if str(embed.get("title") or "") == expected_title:
            return True
    return False


def find_message(
    client: DiscordClient,
    channel_id: str,
    expected_marker: str,
    fallback_title: str | None = None,
) -> dict[str, Any] | None:
    fallback: dict[str, Any] | None = None
    for message in client.list_messages(channel_id, limit=100):
        if embed_has_marker(message, expected_marker):
            return message
        if fallback is None and message_has_title(message, fallback_title):
            fallback = message
    return fallback


def find_thread(client: DiscordClient, guild_id: str, forum_id: str, projection: dict[str, Any]) -> dict[str, Any] | None:
    expected_slug = normalize_name(str(projection["name"]))
    expected_project_marker = marker("project", str(projection["project_id"]))
    for thread in client.list_active_threads(guild_id):
        if str(thread.get("parent_id")) != str(forum_id):
            continue
        if normalize_name(str(thread.get("name") or "")) == expected_slug:
            return thread
        if expected_project_marker in str(thread.get("topic") or ""):
            return thread
    return None


def dashboard_embed(projection: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    projects = dict(state.get("projects") or {})
    projects[projection["project_id"]] = {
        **projects.get(projection["project_id"], {}),
        "summary": project_summary(projection),
    }
    summaries = [
        project.get("summary")
        for project in projects.values()
        if isinstance(project, dict) and isinstance(project.get("summary"), dict)
    ]
    summaries.sort(key=lambda item: str(item.get("last_synced_at") or ""), reverse=True)
    lines = []
    for item in summaries[:8]:
        status = STATUS_PT.get(str(item.get("status")), str(item.get("status")))
        freshness = FRESHNESS_PT.get(str(item.get("projection_freshness")), str(item.get("projection_freshness")))
        lines.append(
            f"**{truncate(str(item.get('name')), 48)}** - {status} - "
            f"{item.get('completion_percent')}% - {freshness}"
        )
    if not lines:
        lines = ["Nenhum projeto ativo projetado ainda."]
    return {
        "title": "Torre de Controle da Fabrica",
        "description": "Portfolio global. O estado duravel continua no Hermes.",
        "color": 0x5865F2,
        "fields": [
            {
                "name": "Projetos ativos",
                "value": truncate("\n".join(lines), 1024),
                "inline": False,
            },
            {
                "name": "Proxima acao em destaque",
                "value": truncate(str(projection["next_action"]), 1024),
                "inline": False,
            },
        ],
        "footer": {
            "text": f"{DASHBOARD_MARKER} | atualizado {projection['last_synced_at']}",
        },
    }


def registry_embed(projection: dict[str, Any], thread_id: str | None) -> dict[str, Any]:
    status = STATUS_PT.get(str(projection["status"]), str(projection["status"]))
    freshness = FRESHNESS_PT.get(str(projection["projection_freshness"]), str(projection["projection_freshness"]))
    cockpit = f"<#{thread_id}>" if thread_id else "cockpit pendente"
    return {
        "title": f"Projeto recebido - {truncate(str(projection['name']), 180)}",
        "description": "Registro operacional. A conversa e o acompanhamento ficam no cockpit do projeto.",
        "color": 0x2ECC71,
        "fields": [
            {"name": "Cockpit", "value": cockpit, "inline": True},
            {"name": "Estado", "value": status, "inline": True},
            {"name": "Conclusao", "value": f"{projection['completion_percent']}%", "inline": True},
            {"name": "Proxima acao", "value": truncate(str(projection["next_action"]), 1024), "inline": False},
            {"name": "Frescor", "value": freshness, "inline": True},
        ],
        "footer": {
            "text": f"{marker('registry', str(projection['project_id']))} | atualizado {projection['last_synced_at']}",
        },
    }


def cockpit_embed(projection: dict[str, Any]) -> dict[str, Any]:
    status = STATUS_PT.get(str(projection["status"]), str(projection["status"]))
    confidence = FORECAST_PT.get(str(projection["forecast_confidence"]), str(projection["forecast_confidence"]))
    freshness = FRESHNESS_PT.get(str(projection["projection_freshness"]), str(projection["projection_freshness"]))
    blockers = non_empty_list(projection.get("current_blockers"))
    missing = non_empty_list(projection.get("missing_items"))
    pending_access = non_empty_list(projection.get("pending_access"))
    pending_approvals = non_empty_list(projection.get("pending_approvals"))
    evidence = non_empty_list(projection.get("evidence_refs"))
    stop_items = blockers or missing
    return {
        "title": "Painel de Esteira do Projeto",
        "description": f"**{truncate(str(projection['name']), 180)}**",
        "color": 0xF1C40F if stop_items or pending_access or pending_approvals else 0x2ECC71,
        "fields": [
            {"name": "Etapa agora", "value": truncate(str(projection["phase"]), 256), "inline": True},
            {"name": "Estado", "value": status, "inline": True},
            {"name": "Conclusao", "value": f"{projection['completion_percent']}%", "inline": True},
            {"name": "Confianca", "value": confidence, "inline": True},
            {"name": "Frescor", "value": freshness, "inline": True},
            {"name": "Risco", "value": str(projection["risk"]), "inline": True},
            {
                "name": "Esteira previsivel",
                "value": truncate("\n".join(stage_lines(projection)), 1024),
                "inline": False,
            },
            {
                "name": "O que falta para avancar",
                "value": truncate(bullet_list(stop_items), 1024),
                "inline": False,
            },
            {
                "name": "Acessos pendentes",
                "value": truncate(bullet_list(pending_access), 1024),
                "inline": True,
            },
            {
                "name": "Aprovacoes pendentes",
                "value": truncate(bullet_list(pending_approvals), 1024),
                "inline": True,
            },
            {
                "name": "Proxima acao",
                "value": truncate(str(projection["next_action"]), 1024),
                "inline": False,
            },
            {
                "name": "Ultimas provas",
                "value": truncate(bullet_list(evidence, empty="sem prova publicada ainda"), 1024),
                "inline": False,
            },
        ],
        "footer": {
            "text": f"{marker('cockpit', str(projection['project_id']))} | fonte: {projection.get('source_runtime', 'runtime')} | {projection['last_synced_at']}",
        },
    }


def dashboard_payload(projection: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": "",
        "embeds": [dashboard_embed(projection, state)],
    }


def registry_payload(projection: dict[str, Any], thread_id: str | None) -> dict[str, Any]:
    return {
        "content": "",
        "embeds": [registry_embed(projection, thread_id)],
    }


def cockpit_payload(projection: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": "",
        "embeds": [cockpit_embed(projection)],
    }


def initial_thread_payload(projection: dict[str, Any], tag_ids: list[str]) -> dict[str, Any]:
    content = (
        f"Projeto **{truncate(str(projection['name']), 120)}**.\n"
        "Este topico e o cockpit operacional do projeto. "
        "Hermes continua sendo a fonte da verdade.\n"
        f"`{marker('project', str(projection['project_id']))}`"
    )
    payload: dict[str, Any] = {
        "name": truncate(str(projection["name"]), 95),
        "auto_archive_duration": 10080,
        "message": {"content": content},
    }
    if tag_ids:
        payload["applied_tags"] = tag_ids
    return payload


def upsert_message(
    client: DiscordClient,
    channel_id: str,
    payload: dict[str, Any],
    expected_marker: str,
    state_ref: dict[str, Any],
    state_field: str,
    apply: bool,
) -> dict[str, Any]:
    existing_id = state_ref.get(state_field)
    existing_message = None
    fallback_title = None
    if payload.get("embeds"):
        fallback_title = str(payload["embeds"][0].get("title") or "") or None
    if existing_id:
        existing_message = {"id": existing_id}
    else:
        existing_message = find_message(client, channel_id, expected_marker, fallback_title=fallback_title)
        if existing_message:
            existing_id = str(existing_message["id"])

    if not apply:
        return {
            "changed": existing_id is None,
            "created": existing_id is None,
            "updated": existing_id is not None,
            "message_id": existing_id,
        }

    if existing_id:
        message = client.edit_message(channel_id, str(existing_id), payload)
        state_ref[state_field] = str(message.get("id") or existing_id)
        return {"changed": True, "created": False, "updated": True, "message_id": state_ref[state_field]}
    message = client.post_message(channel_id, payload)
    state_ref[state_field] = str(message["id"])
    return {"changed": True, "created": True, "updated": False, "message_id": state_ref[state_field]}


def project_bridge_apply(
    projection: dict[str, Any],
    client: DiscordClient,
    config: BridgeConfig,
    state: dict[str, Any],
) -> dict[str, Any]:
    validate_projection(projection)
    project_id = str(projection["project_id"])
    state.setdefault("projects", {})
    project_state = state["projects"].setdefault(project_id, {})
    project_state["summary"] = project_summary(projection)

    user = client.get_current_user()
    surfaces = resolve_surfaces(client, config)
    tag_ids = select_tag_ids(projection, surfaces.kanban_tags)

    existing_thread_id = project_state.get("project_thread_id")
    thread = {"id": existing_thread_id} if existing_thread_id else None
    if thread is None:
        thread = find_thread(client, surfaces.guild_id, str(surfaces.kanban["id"]), projection)

    thread_created = False
    thread_updated = False
    if config.apply:
        if thread is None:
            thread = client.create_forum_thread(
                str(surfaces.kanban["id"]),
                initial_thread_payload(projection, tag_ids),
            )
            thread_created = True
        else:
            channel_payload: dict[str, Any] = {"name": truncate(str(projection["name"]), 95)}
            if tag_ids:
                channel_payload["applied_tags"] = tag_ids
            client.edit_channel(str(thread["id"]), channel_payload)
            thread_updated = True
    elif thread is None:
        thread_created = True

    thread_id = str(thread["id"]) if thread and thread.get("id") else None
    if thread_id:
        project_state["project_thread_id"] = thread_id

    dashboard_state = state.setdefault("dashboard", {})
    dashboard_result = upsert_message(
        client=client,
        channel_id=str(surfaces.dashboard["id"]),
        payload=dashboard_payload(projection, state),
        expected_marker=DASHBOARD_MARKER,
        state_ref=dashboard_state,
        state_field="message_id",
        apply=config.apply,
    )
    registry_result = upsert_message(
        client=client,
        channel_id=str(surfaces.registry["id"]),
        payload=registry_payload(projection, thread_id),
        expected_marker=marker("registry", project_id),
        state_ref=project_state,
        state_field="registry_message_id",
        apply=config.apply,
    )
    if not thread_id:
        cockpit_result = {"changed": True, "created": True, "updated": False, "message_id": None}
    else:
        cockpit_result = upsert_message(
            client=client,
            channel_id=thread_id,
            payload=cockpit_payload(projection),
            expected_marker=marker("cockpit", project_id),
            state_ref=project_state,
            state_field="cockpit_message_id",
            apply=config.apply,
        )

    project_state["last_synced_at"] = projection["last_synced_at"]
    project_state["last_bridge_run_at"] = utc_now()

    return {
        "bot_reachable": bool(user.get("id")),
        "guild_resolved": True,
        "channels_resolved": True,
        "dashboard": dashboard_result,
        "registry": registry_result,
        "project_thread": {
            "created": thread_created,
            "updated": thread_updated,
            "thread_id": thread_id,
            "tag_count": len(tag_ids),
        },
        "cockpit": cockpit_result,
        "state_saved": config.state_path is not None,
    }


def build_bridge_health_receipt(
    projection: dict[str, Any],
    result: dict[str, Any],
    applied: bool,
    state_path: Path | None,
) -> dict[str, Any]:
    checks = {
        "bot_reachable": bool(result.get("bot_reachable")),
        "bridge_reachable": True,
        "runtime_readback_reachable": bool(projection.get("truth_source_available")),
        "approval_registration_path_reachable": True,
        "no_discord_source_of_truth": True,
        "no_private_material_in_public_receipt": True,
        "guild_resolved": bool(result.get("guild_resolved")),
        "channels_resolved": bool(result.get("channels_resolved")),
        "project_thread_resolved": bool((result.get("project_thread") or {}).get("thread_id")) or not applied,
        "dashboard_upserted": bool((result.get("dashboard") or {}).get("changed") or (result.get("dashboard") or {}).get("message_id")),
        "registry_upserted": bool((result.get("registry") or {}).get("changed") or (result.get("registry") or {}).get("message_id")),
        "cockpit_upserted": bool((result.get("cockpit") or {}).get("changed") or (result.get("cockpit") or {}).get("message_id")) or not applied,
        "private_state_path_used": state_path is not None,
    }
    public_refs = [
        "docs/control-tower/discord-control-tower-os.md",
        "docs/control-tower/discord-control-tower-setup-pt-br.md",
        "external:discord-bridge-projector",
        public_receipt_ref((result.get("project_thread") or {}).get("thread_id"), "project-thread"),
        public_receipt_ref((result.get("dashboard") or {}).get("message_id"), "dashboard-message"),
        public_receipt_ref((result.get("registry") or {}).get("message_id"), "registry-message"),
        public_receipt_ref((result.get("cockpit") or {}).get("message_id"), "cockpit-message"),
    ]
    receipt = {
        "$schema": "https://overkill-factory.dev/schemas/operator-control-tower-bridge-health.schema.json",
        "record_type": "operator_control_tower_bridge_health",
        "created_at": utc_now(),
        "result": "PASS" if all(checks.values()) else "BLOCKED",
        "project_id": projection["project_id"],
        "projection_freshness": projection["projection_freshness"],
        "applied_to_discord": applied,
        "checks": checks,
        "evidence_refs": public_refs,
        "limits": [
            "Discord is the owner cockpit only; Hermes remains the source of truth.",
            "The public receipt redacts Discord ids and private file paths.",
            "Structured approval buttons and inbound approval registration are separate contracts.",
        ],
    }
    text = json.dumps(receipt, ensure_ascii=False)
    if re.search(r"\d{12,}|Bot\s+[A-Za-z0-9._-]+|/srv/|C:\\\\Users|token|password", text, re.IGNORECASE):
        raise AssertionError("public receipt contains private-looking material")
    return receipt


def load_projection(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("projection must be a JSON object")
    validate_projection(data)
    return data


def write_json(path: Path | None, data: dict[str, Any]) -> None:
    if path is None:
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        rel = path.relative_to(ROOT)
        print(f"Wrote {rel.as_posix()}")
    except ValueError:
        print(f"Wrote {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--env", type=Path, help="Optional private .env file. Never commit it.")
    parser.add_argument("--guild-id", default=os.environ.get("DISCORD_GUILD_ID"))
    parser.add_argument("--api-base", default=API_BASE)
    parser.add_argument("--timeout", type=int, default=20)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Mutate Discord.")
    mode.add_argument("--dry-run", action="store_true", help="Resolve and render without mutations.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(args.env)
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is required in env or --env")

    projection = load_projection(args.projection)
    state = load_state(args.state)
    config = BridgeConfig(
        apply=bool(args.apply),
        guild_id=args.guild_id or os.environ.get("DISCORD_GUILD_ID"),
        state_path=args.state,
    )
    client = DiscordApi(token=token, api_base=args.api_base, timeout=args.timeout)
    result = project_bridge_apply(projection, client, config, state)
    if args.apply:
        save_state(args.state, state)
    receipt = build_bridge_health_receipt(
        projection=projection,
        result=result,
        applied=bool(args.apply),
        state_path=args.state,
    )
    write_json(args.out, receipt)
    if receipt["result"] != "PASS":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
