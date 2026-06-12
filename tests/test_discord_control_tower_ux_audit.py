from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class DiscordControlTowerUxAuditTest(unittest.TestCase):
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
