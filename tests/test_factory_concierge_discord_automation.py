from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "scripts" / "factory_concierge_discord_bridge.py"
BRIDGE_SPEC = importlib.util.spec_from_file_location("factory_concierge_discord_bridge", BRIDGE_PATH)
assert BRIDGE_SPEC is not None
bridge = importlib.util.module_from_spec(BRIDGE_SPEC)
assert BRIDGE_SPEC.loader is not None
sys.modules["factory_concierge_discord_bridge"] = bridge
BRIDGE_SPEC.loader.exec_module(bridge)

MODULE_PATH = ROOT / "scripts" / "factory_concierge_discord_automation.py"
SPEC = importlib.util.spec_from_file_location("factory_concierge_discord_automation", MODULE_PATH)
assert SPEC is not None
automation = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factory_concierge_discord_automation"] = automation
SPEC.loader.exec_module(automation)


class FakeDiscordClient:
    def __init__(self) -> None:
        self.channels = [
            {"id": "chan-dashboard", "name": "torre-de-controle", "type": 0},
            {"id": "chan-manager", "name": "falar-com-gerente", "type": 0},
            {"id": "chan-health", "name": "saude-do-bot", "type": 0},
            {"id": "chan-registry", "name": "projetos-recebidos", "type": 0},
            {
                "id": "forum-kanban",
                "name": "kanban-da-fabrica",
                "type": 15,
                "available_tags": [
                    {"id": "tag-entrada", "name": "Entrada"},
                    {"id": "tag-planejamento", "name": "Planejamento"},
                    {"id": "tag-bloqueado", "name": "Bloqueado"},
                    {"id": "tag-acesso", "name": "Acesso pendente"},
                    {"id": "tag-dono", "name": "Acao do dono"},
                ],
            },
            {"id": "chan-approvals", "name": "aprovacoes-formais", "type": 0},
            {"id": "chan-access", "name": "acessos-pendentes", "type": 0},
            {"id": "chan-blockers", "name": "bloqueios-reais", "type": 0},
            {"id": "chan-evidence", "name": "provas-e-evidencias", "type": 0},
            {"id": "chan-production", "name": "producao-e-releases", "type": 0},
        ]
        self.messages: dict[str, list[dict[str, Any]]] = {channel["id"]: [] for channel in self.channels}
        self.threads: list[dict[str, Any]] = []
        self.next_message = 1
        self.next_thread = 1

    def seed_manager_message(self, content: str) -> dict[str, Any]:
        return self.post_message(
            "chan-manager",
            {"content": content, "author": {"id": "owner", "bot": False}, "attachments": []},
        )

    def seed_manager_thread_message(
        self,
        content: str,
        thread_name: str = "atendimento-gerente",
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        starter = self.seed_manager_message("@GERENTE iniciar atendimento")
        thread = self.create_thread_from_message(
            "chan-manager",
            starter["id"],
            {"name": thread_name, "auto_archive_duration": 10080},
        )
        message = self.post_message(
            thread["id"],
            {"content": content, "author": {"id": "owner", "bot": False}, "attachments": []},
        )
        return thread, message

    def get_current_user(self) -> dict[str, Any]:
        return {"id": "bot-user", "username": "GERENTE"}

    def list_guilds(self) -> list[dict[str, Any]]:
        return [{"id": "guild-main", "name": "Overkill Factory"}]

    def list_channels(self, guild_id: str) -> list[dict[str, Any]]:
        assert guild_id == "guild-main"
        return list(self.channels)

    def list_active_threads(self, guild_id: str) -> list[dict[str, Any]]:
        assert guild_id == "guild-main"
        return list(self.threads)

    def list_messages(self, channel_id: str, limit: int = 50) -> list[dict[str, Any]]:
        return list(reversed(self.messages.get(channel_id, [])))[:limit]

    def post_message(self, channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        message = {"id": f"msg-{self.next_message}", "channel_id": channel_id, **payload}
        self.next_message += 1
        message.setdefault("author", {"id": "bot-user", "bot": True})
        message.setdefault("attachments", [])
        self.messages.setdefault(channel_id, []).append(message)
        return message

    def edit_message(self, channel_id: str, message_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        for message in self.messages.setdefault(channel_id, []):
            if message["id"] == message_id:
                message.clear()
                message.update({"id": message_id, "channel_id": channel_id, **payload})
                message.setdefault("author", {"id": "bot-user", "bot": True})
                message.setdefault("attachments", [])
                return message
        raise AssertionError(f"missing message {message_id}")

    def create_forum_thread(self, channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._create_thread(channel_id, payload["name"], payload.get("applied_tags", []))

    def create_thread_from_message(self, channel_id: str, message_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        assert any(message["id"] == message_id for message in self.messages.get(channel_id, []))
        return self._create_thread(channel_id, payload["name"], [])

    def _create_thread(self, parent_id: str, name: str, tags: list[str]) -> dict[str, Any]:
        thread = {
            "id": f"thread-{self.next_thread}",
            "parent_id": parent_id,
            "name": name,
            "applied_tags": list(tags),
        }
        self.next_thread += 1
        self.threads.append(thread)
        self.messages[thread["id"]] = []
        return thread

    def edit_channel(self, channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        for thread in self.threads:
            if thread["id"] == channel_id:
                thread.update(payload)
                return thread
        raise AssertionError(f"missing channel {channel_id}")

    def list_guild_roles(self, guild_id: str) -> list[dict[str, Any]]:
        return [{"id": "role-owner", "name": "Factory Owner"}]


def approval_request() -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/approval-request.schema.json",
        "approval_id": "appr-pilot-plan",
        "project_id": "pilot-front-jogo-fabrica",
        "approval_type": "plan",
        "status": "pending",
        "risk": "R2",
        "scope": "aprovar plano de piloto sem autorizar producao",
        "consequence": "A fabrica pode registrar a decisao, mas ainda precisa do Ready Gate.",
        "not_authorized": ["deploy em producao", "gasto sem limite"],
        "requested_by": "factory-concierge",
        "evidence_refs": ["external:pilot-cockpit"],
        "expires_at": "2026-06-12T00:00:00Z",
        "created_at": "2026-06-11T08:00:00Z",
    }


class FactoryConciergeDiscordAutomationTest(unittest.TestCase):
    def test_intake_scan_uses_existing_manager_thread_and_project_surfaces(self) -> None:
        client = FakeDiscordClient()
        intake_thread, _ = client.seed_manager_thread_message(
            "Paper do projeto: quero criar o front jogo da fabrica. "
            "Este piloto precisa acompanhar a esteira da Overkill Factory com UX visual."
        )
        state: dict[str, Any] = {"version": 1, "dashboard": {}, "projects": {}}
        config = bridge.BridgeConfig(apply=True, guild_id=None, state_path=Path("private.json"))

        result = automation.process_intake_messages(client, config, state, apply=True)

        self.assertEqual(result["processed"], 1)
        item = result["results"][0]
        self.assertTrue(item["thread_first"])
        self.assertFalse(item["intake_thread_created"])
        self.assertTrue(item["intake_thread_resolved"])
        self.assertTrue(item["project_surface_resolved"])
        self.assertEqual(len([t for t in client.threads if t["parent_id"] == "chan-manager"]), 1)
        self.assertEqual(state["projects"]["pilot-front-jogo-fabrica"]["intake_thread_id"], intake_thread["id"])
        self.assertEqual(len([t for t in client.threads if t["parent_id"] == "forum-kanban"]), 1)
        self.assertIn("pilot-front-jogo-fabrica", state["projects"])

    def test_intake_scan_ignores_reception_messages_without_thread(self) -> None:
        client = FakeDiscordClient()
        client.seed_manager_message(
            "Paper do projeto: quero criar o front jogo da fabrica. "
            "Este piloto precisa acompanhar a esteira da Overkill Factory com UX visual."
        )
        state: dict[str, Any] = {"version": 1, "dashboard": {}, "projects": {}}
        config = bridge.BridgeConfig(apply=True, guild_id=None, state_path=Path("private.json"))

        result = automation.process_intake_messages(client, config, state, apply=True)

        self.assertEqual(result["processed"], 0)
        self.assertEqual(result["ignored_reception_messages"], 1)
        self.assertEqual(len([t for t in client.threads if t["parent_id"] == "chan-manager"]), 0)
        self.assertEqual(state["projects"], {})

    def test_intake_scan_rejects_operational_discord_repair_request(self) -> None:
        client = FakeDiscordClient()
        client.seed_manager_thread_message(
            "preciso que voce recrie o projeto/produto nesses dois canais",
            thread_name="ajuste-discord",
        )
        state: dict[str, Any] = {"version": 1, "dashboard": {}, "projects": {}}
        config = bridge.BridgeConfig(apply=True, guild_id=None, state_path=Path("private.json"))

        result = automation.process_intake_messages(client, config, state, apply=True)

        self.assertEqual(result["processed"], 0)
        self.assertEqual(state["projects"], {})
        self.assertEqual(len([t for t in client.threads if t["parent_id"] == "forum-kanban"]), 0)

    def test_project_intake_accepts_explicit_product_briefing(self) -> None:
        message = {
            "author": {"id": "owner", "bot": False},
            "attachments": [],
            "content": (
                "Briefing do projeto: quero construir um produto local para acompanhar "
                "a fabrica, com etapas, aprovacoes e progresso visual."
            ),
        }

        self.assertTrue(automation.looks_like_project_intake(message))

    def test_active_event_sync_posts_lane_message_and_thread(self) -> None:
        client = FakeDiscordClient()
        state: dict[str, Any] = {"version": 1, "dashboard": {}, "projects": {"p1": {}}}
        config = bridge.BridgeConfig(apply=True, guild_id=None, state_path=Path("private.json"))
        event = {
            "$schema": "https://overkill-factory.dev/schemas/control-tower-event.schema.json",
            "event_id": "evt-access-missing",
            "event_type": "access_missing",
            "severity": "P1",
            "project_id": "p1",
            "source": "hermes",
            "summary": "Falta acesso ao repositorio.",
            "details": "Sem esse acesso, execucao material nao inicia.",
            "action_required": True,
            "created_at": "2026-06-11T08:00:00Z",
        }

        result = automation.sync_event(event, client, config, state, apply=True)

        self.assertEqual(result["target"], "access")
        self.assertTrue(result["message_resolved"])
        self.assertTrue(result["thread_resolved"])
        self.assertEqual(len(client.messages["chan-access"]), 1)
        self.assertEqual(len([t for t in client.threads if t["parent_id"] == "chan-access"]), 1)

    def test_approval_request_has_buttons_and_decision_registers_event(self) -> None:
        client = FakeDiscordClient()
        state: dict[str, Any] = {"version": 1, "dashboard": {}, "projects": {}}
        config = bridge.BridgeConfig(apply=True, guild_id=None, state_path=Path("private.json"))
        approval = approval_request()

        result = automation.post_approval_request(approval, client, config, state, apply=True)
        registered, event = automation.register_approval_decision(
            approval,
            {
                "approval_id": approval["approval_id"],
                "actor_role": "Factory Owner",
                "decision": "needs_changes",
                "scope": approval["scope"],
            },
            now="2026-06-11T09:00:00Z",
        )

        self.assertTrue(result["components_rendered"])
        self.assertTrue(result["thread_resolved"])
        components = client.messages["chan-approvals"][0]["components"][0]["components"]
        self.assertEqual([button["label"] for button in components], ["Aprovar", "Rejeitar", "Pedir ajuste"])
        fallback_field = client.messages["chan-approvals"][0]["embeds"][0]["fields"][5]
        self.assertEqual(fallback_field["name"], "Se o botao falhar")
        self.assertEqual(registered["status"], "needs_changes")
        self.assertEqual(event["event_type"], "approval_recorded")

    def test_approval_text_fallback_registers_owner_decision(self) -> None:
        client = FakeDiscordClient()
        state: dict[str, Any] = {"version": 1, "dashboard": {}, "projects": {}}
        config = bridge.BridgeConfig(apply=True, guild_id=None, state_path=Path("private.json"))
        approval = approval_request()
        automation.post_approval_request(approval, client, config, state, apply=True)
        thread_id = state["approvals"][approval["approval_id"]]["thread_id"]
        client.messages[thread_id].append(
            {
                "id": "owner-decision",
                "content": "aprovado",
                "author": {"id": "owner", "bot": False},
            }
        )

        result = automation.sync_approval_text_decision(
            approval,
            client,
            config,
            state,
            apply=True,
            now="2026-06-11T09:00:00Z",
        )

        self.assertTrue(result["accepted"])
        self.assertEqual(result["decision"], "approved")
        self.assertEqual(state["approval_events"][approval["approval_id"]]["status"], "approved")
        self.assertEqual(client.messages["chan-approvals"][0]["embeds"][0]["fields"][2]["value"], "approved")

    def test_health_and_public_receipt_cover_remaining_discord_fronts(self) -> None:
        client = FakeDiscordClient()
        state: dict[str, Any] = {"version": 1, "dashboard": {}, "projects": {}}
        config = bridge.BridgeConfig(apply=True, guild_id=None, state_path=Path("private.json"))

        health = automation.post_health(
            client,
            config,
            state,
            apply=True,
            extra_checks={
                "threading_rule_ready": True,
                "approval_components_ready": True,
                "projection_ready": True,
            },
        )
        receipt = automation.build_public_receipt(
            {
                "bot_reachable": True,
                "runtime_readback_reachable": True,
                "approval_registration_path_reachable": True,
                "thread_first_project_intake_automated": True,
                "active_bot_messages_threaded_or_linked": True,
                "structured_approval_interactions_automated": True,
                "live_runtime_projection_automated": True,
                "operational_channels_projected": True,
                "health_anti_stale_posted": health["message_resolved"],
            },
            applied=True,
        )

        self.assertTrue(health["message_resolved"])
        self.assertEqual(receipt["result"], "PASS")
        self.assertNotIn("chan-health", json.dumps(receipt))

    def test_run_automation_empty_inboxes_posts_idle_health_receipt(self) -> None:
        client = FakeDiscordClient()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("projections", "events", "approvals"):
                (root / name).mkdir()
            args = argparse.Namespace(
                projection=None,
                projection_dir=root / "projections",
                event=None,
                event_dir=root / "events",
                approval=None,
                approval_dir=root / "approvals",
                decision=None,
                decision_time=None,
                scan_intake=True,
                post_health=True,
                max_messages=20,
                state=root / "state.json",
                out=root / "receipt.json",
                env=None,
                guild_id=None,
                api_base="https://discord.test/api",
                timeout=1.0,
                apply=True,
            )
            with patch.dict(automation.os.environ, {"DISCORD_BOT_TOKEN": "test-token"}), patch.object(
                automation.bridge, "DiscordApi", return_value=client
            ):
                receipt = automation.run_automation(args)

        self.assertEqual(receipt["result"], "PASS")
        self.assertTrue(receipt["checks"]["thread_first_project_intake_automated"])
        self.assertTrue(receipt["checks"]["active_bot_messages_threaded_or_linked"])
        self.assertTrue(receipt["checks"]["structured_approval_interactions_automated"])
        self.assertTrue(receipt["checks"]["live_runtime_projection_automated"])
        self.assertTrue(receipt["checks"]["operational_channels_projected"])
        self.assertTrue(receipt["checks"]["health_anti_stale_posted"])


if __name__ == "__main__":
    unittest.main()
