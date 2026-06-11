from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "validation" / "control-tower" / "discord-control-tower-ux-audit-2026-06-11.json"


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class DiscordControlTowerUxAuditTest(unittest.TestCase):
    def test_project_intake_is_thread_first_in_docs(self) -> None:
        dynamic_study = read_text("docs/control-tower/discord-dynamic-control-tower-study-pt-br.md")
        setup_guide = read_text("docs/control-tower/discord-control-tower-setup-pt-br.md")
        os_doc = read_text("docs/control-tower/discord-control-tower-os.md")
        combined = "\n".join([dynamic_study, setup_guide, os_doc])

        self.assertIn("paper, briefing ou projeto novo -> abre topico do projeto", dynamic_study)
        self.assertIn("paper/projeto/piloto -> topico do projeto + cartao no forum", setup_guide)
        self.assertIn("paper, long brief, new product or pilot -> create project thread and forum card", os_doc)
        self.assertIn("#projetos-recebidos", combined)
        self.assertIn("not a second owner intake", os_doc)
        self.assertIn("project cockpit", os_doc)
        self.assertIn("global portfolio", os_doc)
        self.assertIn("project index", os_doc)
        self.assertIn("factory_concierge_discord_bridge.py", os_doc)
        self.assertIn("--projection /private/path/to/project-projection.json", os_doc)
        self.assertIn("Painel de Esteira do Projeto", dynamic_study)
        self.assertIn("mensagem do bot que convida conversa ou acao deve", setup_guide)
        self.assertIn("free_response_channels", combined)
        self.assertIn("Factory Concierge Discord Bridge", combined)
        self.assertIn("Bridge de projecao do projeto", setup_guide)
        self.assertIn("factory_concierge_discord_automation.py", combined)
        self.assertIn("Automacao viva da Control Tower", setup_guide)

    def test_ux_audit_records_live_fix_but_keeps_automation_attention(self) -> None:
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))

        self.assertEqual(audit["record_type"], "discord_control_tower_ux_audit")
        self.assertEqual(audit["result"], "PASS")
        self.assertTrue(audit["checks"]["pilot_project_thread_created"])
        self.assertTrue(audit["checks"]["pilot_forum_card_created"])
        self.assertTrue(audit["checks"]["single_owner_intake_door"])
        self.assertTrue(audit["checks"]["global_portfolio_view_defined"])
        self.assertTrue(audit["checks"]["project_index_not_detail_dump"])
        self.assertTrue(audit["checks"]["multi_project_kanban_shape_ready"])
        self.assertTrue(audit["checks"]["project_cockpit_pipeline_panel_required"])
        self.assertTrue(audit["checks"]["pilot_project_cockpit_pipeline_panel_created"])
        self.assertTrue(audit["checks"]["project_pipeline_progress_visible"])
        self.assertTrue(audit["checks"]["multi_project_kanban_idempotence_automated"])
        self.assertTrue(audit["checks"]["project_pipeline_projection_automated"])
        self.assertTrue(audit["checks"]["active_bot_messages_threaded_or_linked"])
        self.assertTrue(audit["checks"]["thread_first_project_intake_automated"])
        self.assertTrue(audit["checks"]["structured_approval_interactions_automated"])
        self.assertTrue(audit["checks"]["live_runtime_projection_automated"])
        self.assertIn("created a project conversation thread", "\n".join(audit["live_corrections"]))
        self.assertIn("retry-safe project mapping", "\n".join(audit["live_corrections"]))
        self.assertIn(
            "validation/control-tower/discord-bridge-projector-live-2026-06-11.json",
            audit["evidence_refs"],
        )
        self.assertIn(
            "validation/control-tower/discord-control-tower-automation-live-2026-06-11.json",
            audit["evidence_refs"],
        )

        findings = "\n".join(item["finding"] for item in audit["findings"])
        self.assertIn("Structured approval buttons", findings)


if __name__ == "__main__":
    unittest.main()
