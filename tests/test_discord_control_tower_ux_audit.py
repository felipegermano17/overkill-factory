from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class DiscordControlTowerUxAuditTest(unittest.TestCase):
    def test_discord_ux_study_gate_is_a_real_contract_not_placeholder(self) -> None:
        template = json.loads(read_text("templates/discord-control-tower-ux-audit.json"))

        self.assertEqual(template["record_type"], "discord_control_tower_ux_audit")
        self.assertEqual(template["result"], "ATTENTION")
        self.assertFalse(template["study_gate"]["discord_is_source_of_truth"])
        self.assertTrue(template["study_gate"]["ux_study_required_before_implementation"])
        self.assertTrue(template["study_gate"]["proof_pack_required_before_acceptance"])
        self.assertEqual(template["study_gate"]["recommended_role"], "secondary_operator_cockpit")
        self.assertEqual(template["study_gate"]["web_cockpit_boundary"], "required_for_dense_state")
        self.assertIn("#80", template["study_gate"]["status_snapshot_dependency"])
        self.assertIn("#82", template["study_gate"]["product_face_dependency"])
        self.assertGreaterEqual(len(template["discord_mastery_matrix"]["official_source_refs"]), 5)
        self.assertGreaterEqual(len(template["discord_mastery_matrix"]["primitives_reviewed"]), 8)
        self.assertGreaterEqual(len(template["proof_pack_contract"]["must_include_negative_tests"]), 5)
        self.assertNotIn("todo", json.dumps(template).lower())

    def test_discord_study_gate_doc_covers_platform_limits_and_web_boundary(self) -> None:
        study = read_text("docs/control-tower/discord-cockpit-ux-study-gate.md")
        os_doc = read_text("docs/control-tower/discord-control-tower-os.md")
        combined = f"{study}\n{os_doc}"

        for expected in [
            "https://docs.discord.com/developers/interactions/overview",
            "https://docs.discord.com/developers/interactions/receiving-and-responding",
            "https://docs.discord.com/developers/components/reference",
            "https://docs.discord.com/developers/topics/threads",
            "https://docs.discord.com/developers/topics/permissions",
            "https://docs.discord.com/developers/topics/rate-limits",
            "first 5 seconds",
            "first 30 seconds",
            "first 5 minutes",
            "rate limits",
            "web cockpit",
            "#80",
            "#82",
            "#84",
            "Discord is optional projection",
            "not the source of truth",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, combined)

    def test_project_intake_is_thread_first_in_docs(self) -> None:
        setup_guide = read_text("docs/control-tower/discord-control-tower-setup-pt-br.md")
        os_doc = read_text("docs/control-tower/discord-control-tower-os.md")
        combined = "\n".join([setup_guide, os_doc])

        self.assertIn("mensagem no #falar-com-gerente com mencao ao GERENTE -> thread de atendimento", setup_guide)
        self.assertIn("owner mentions GERENTE in #falar-com-gerente -> Discord opens an attendance thread", os_doc)
        self.assertIn("raw project-like messages left directly in the", os_doc)
        self.assertIn("env vars override `config.yaml`", os_doc)
        self.assertIn("variaveis do `.env` ganham do", setup_guide)
        self.assertIn("the formal approval request itself must be rendered", os_doc)
        self.assertIn("aprovacao formal nasce em `#aprovacoes-formais`", setup_guide)
        self.assertIn("#projetos-recebidos", combined)
        self.assertIn("not a second owner intake", os_doc)
        self.assertIn("project cockpit", os_doc)
        self.assertIn("global portfolio", os_doc)
        self.assertIn("project index", os_doc)
        self.assertIn("factory_concierge_discord_bridge.py", os_doc)
        self.assertIn("--projection /private/path/to/project-projection.json", os_doc)
        self.assertIn("mensagem do bot que convida conversa ou acao deve", setup_guide)
        self.assertIn("DISCORD_FREE_RESPONSE_CHANNELS", combined)
        self.assertIn("Factory Concierge Discord Bridge", combined)
        self.assertIn("Bridge de projecao do projeto", setup_guide)
        self.assertIn("factory_concierge_discord_automation.py", combined)
        self.assertIn("Automacao viva da Control Tower", setup_guide)

    def test_live_audit_outputs_are_generated_not_versioned(self) -> None:
        setup_guide = read_text("docs/control-tower/discord-control-tower-setup-pt-br.md")
        os_doc = read_text("docs/control-tower/discord-control-tower-os.md")
        automation = read_text("scripts/factory_concierge_discord_automation.py")

        self.assertIn(".tmp/factory-runs/control-tower", setup_guide)
        self.assertIn(".tmp/factory-runs/control-tower", os_doc)
        self.assertIn("approval", automation.lower())
        self.assertFalse((ROOT / "validation" / "control-tower").exists())


if __name__ == "__main__":
    unittest.main()
