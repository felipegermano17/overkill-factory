from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factory_concierge_discord_bridge.py"
SPEC = importlib.util.spec_from_file_location("factory_concierge_discord_bridge", MODULE_PATH)
assert SPEC is not None
bridge = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factory_concierge_discord_bridge"] = bridge
SPEC.loader.exec_module(bridge)


class FakeDiscordClient:
    def __init__(self) -> None:
        self.channels = [
            {"id": "chan-dashboard", "name": "torre-de-controle", "type": 0},
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
                    {"id": "tag-aprovacao", "name": "Aprovacao pendente"},
                    {"id": "tag-dono", "name": "Acao do dono"},
                    {"id": "tag-executando", "name": "Executando"},
                    {"id": "tag-revisao", "name": "Revisao"},
                    {"id": "tag-producao", "name": "Producao"},
                    {"id": "tag-trabalhando", "name": "Fabrica trabalhando"},
                ],
            },
        ]
        self.threads: list[dict[str, Any]] = []
        self.messages: dict[str, list[dict[str, Any]]] = {
            "chan-dashboard": [],
            "chan-registry": [],
        }
        self.next_message = 1
        self.next_thread = 1

    def get_current_user(self) -> dict[str, Any]:
        return {"id": "bot-user", "username": "GERENTE"}

    def list_guilds(self) -> list[dict[str, Any]]:
        return [{"id": "guild-main", "name": "Overkill Factory Control Tower"}]

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
        self.messages.setdefault(channel_id, []).append(message)
        return message

    def edit_message(self, channel_id: str, message_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        for message in self.messages.setdefault(channel_id, []):
            if message["id"] == message_id:
                message.clear()
                message.update({"id": message_id, "channel_id": channel_id, **payload})
                return message
        raise AssertionError(f"missing message {message_id}")

    def create_forum_thread(self, channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        thread = {
            "id": f"thread-{self.next_thread}",
            "parent_id": channel_id,
            "name": payload["name"],
            "applied_tags": list(payload.get("applied_tags", [])),
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


def sample_projection() -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/project-projection.schema.json",
        "project_id": "pilot-front-jogo-fabrica",
        "name": "Piloto - Front jogo da fabrica",
        "phase": "Entrada",
        "status": "intake",
        "execution_started": False,
        "risk": "R2",
        "forecast_confidence": "medium",
        "completion_percent": 8,
        "pipeline_stages": [
            {"name": "Entrada", "status": "current", "summary": "Paper recebido"},
            {"name": "Fonte/SOT", "status": "pending", "summary": "Ainda vai consolidar verdade do produto"},
            {"name": "Execucao", "status": "pending", "summary": "Nao iniciou"},
        ],
        "next_action": "transformar paper em Product SOT",
        "projection_freshness": "runtime_fresh",
        "current_blockers": [],
        "pending_access": [],
        "pending_approvals": [],
        "next_steps": ["criar Product SOT", "fechar arquitetura", "rodar Ready Gate"],
        "evidence_refs": ["external:pilot-intake-message"],
        "source_runtime": "hermes",
        "source_board": "factory-pilot",
        "last_synced_at": "2026-06-11T08:00:00Z",
        "planned_summary": ["intake", "sot", "execution"],
        "missing_items": ["Product SOT"],
        "forecast_risks": ["escopo visual ainda aberto"],
        "human_decisions_required": [],
        "truth_source_available": True,
        "source_of_truth": {
            "runtime": "hermes",
            "ref": "factory-pilot",
            "owner": "factory-runtime",
            "freshness": "runtime_fresh",
            "discord_is_source_of_truth": False,
        },
    }


class FactoryConciergeDiscordBridgeTest(unittest.TestCase):
    def test_bridge_apply_is_idempotent_for_project_surfaces(self) -> None:
        client = FakeDiscordClient()
        state: dict[str, Any] = {"version": 1, "dashboard": {}, "projects": {}}
        config = bridge.BridgeConfig(apply=True, guild_id=None, state_path=Path("private-state.json"))
        projection = sample_projection()

        first = bridge.project_bridge_apply(projection, client, config, state)
        second = bridge.project_bridge_apply(projection, client, config, state)

        self.assertTrue(first["project_thread"]["created"])
        self.assertFalse(second["project_thread"]["created"])
        self.assertTrue(second["project_thread"]["updated"])
        self.assertEqual(len(client.threads), 1)
        self.assertEqual(len(client.messages["chan-dashboard"]), 1)
        self.assertEqual(len(client.messages["chan-registry"]), 1)
        self.assertEqual(len(client.messages["thread-1"]), 1)
        self.assertEqual(first["dashboard"]["message_id"], second["dashboard"]["message_id"])
        self.assertEqual(first["registry"]["message_id"], second["registry"]["message_id"])
        self.assertEqual(first["cockpit"]["message_id"], second["cockpit"]["message_id"])
        self.assertEqual(client.threads[0]["applied_tags"], ["tag-entrada"])

        cockpit_embed = client.messages["thread-1"][0]["embeds"][0]
        self.assertEqual(cockpit_embed["title"], "Painel de Esteira do Projeto")
        self.assertIn("transformar paper em Product SOT", json.dumps(cockpit_embed, ensure_ascii=False))

    def test_public_receipt_redacts_private_discord_identifiers(self) -> None:
        client = FakeDiscordClient()
        state: dict[str, Any] = {"version": 1, "dashboard": {}, "projects": {}}
        config = bridge.BridgeConfig(apply=True, guild_id=None, state_path=Path("private-state.json"))
        projection = sample_projection()

        result = bridge.project_bridge_apply(projection, client, config, state)
        receipt = bridge.build_bridge_health_receipt(projection, result, applied=True, state_path=config.state_path)
        text = json.dumps(receipt, ensure_ascii=False)

        self.assertEqual(receipt["result"], "PASS")
        self.assertTrue(receipt["checks"]["project_thread_resolved"])
        self.assertNotIn("thread-1", text)
        self.assertNotIn("chan-dashboard", text)
        self.assertIn("external:discord-project-thread-present", receipt["evidence_refs"])

    def test_bridge_reuses_existing_cockpit_embed_without_marker(self) -> None:
        client = FakeDiscordClient()
        projection = sample_projection()
        thread = client.create_forum_thread(
            "forum-kanban",
            {
                "name": projection["name"],
                "message": {"content": "manual cockpit starter"},
                "applied_tags": ["tag-entrada"],
            },
        )
        client.post_message(
            thread["id"],
            {
                "content": "",
                "embeds": [{"title": "Painel de Esteira do Projeto", "description": "manual"}],
            },
        )
        state: dict[str, Any] = {"version": 1, "dashboard": {}, "projects": {}}
        config = bridge.BridgeConfig(apply=True, guild_id=None, state_path=Path("private-state.json"))

        result = bridge.project_bridge_apply(projection, client, config, state)

        self.assertTrue(result["cockpit"]["updated"])
        self.assertEqual(len(client.messages[thread["id"]]), 1)
        self.assertIn("of-cockpit:pilot-front-jogo-fabrica", client.messages[thread["id"]][0]["embeds"][0]["footer"]["text"])

    def test_state_file_roundtrip_is_private_and_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "bridge-state.json"
            state = bridge.load_state(state_path)
            self.assertEqual(state["projects"], {})
            state["projects"]["p1"] = {"project_thread_id": "thread-private"}
            bridge.save_state(state_path, state)

            loaded = bridge.load_state(state_path)
            self.assertEqual(loaded["projects"]["p1"]["project_thread_id"], "thread-private")


if __name__ == "__main__":
    unittest.main()
