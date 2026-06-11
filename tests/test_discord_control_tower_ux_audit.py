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
        self.assertIn("free_response_channels", combined)
        self.assertIn("Factory Concierge Discord Bridge", combined)

    def test_ux_audit_records_live_fix_but_keeps_automation_attention(self) -> None:
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))

        self.assertEqual(audit["record_type"], "discord_control_tower_ux_audit")
        self.assertEqual(audit["result"], "ATTENTION")
        self.assertTrue(audit["checks"]["pilot_project_thread_created"])
        self.assertTrue(audit["checks"]["pilot_forum_card_created"])
        self.assertFalse(audit["checks"]["thread_first_project_intake_automated"])
        self.assertIn("created a project conversation thread", "\n".join(audit["live_corrections"]))

        findings = "\n".join(item["finding"] for item in audit["findings"])
        self.assertIn("loose messages", findings)


if __name__ == "__main__":
    unittest.main()
