from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
ROOT = CODE_ROOT.parent


def project_path(rel: str) -> Path:
    code_prefixes = ("adapters/", "agents/", "examples/", "fixtures/", "schemas/", "scripts/", "skills/", "templates/", "tests/", "legacy-docs/")
    code_names = {"pyproject.toml", ".env.example"}
    return CODE_ROOT / rel if rel in code_names or rel.startswith(code_prefixes) else ROOT / rel


def read_text(rel: str) -> str:
    return project_path(rel).read_text(encoding="utf-8")


PT_PAGES = {"index.md", "manual.md", "linha-de-producao.md", "uso.md", "para-mantenedores.md"}
OLD_CANONICAL_NAMES = {
    "01-start-here.md", "02-factory-flow-and-hermes-architecture.md", "03-validation-and-repository-reference.md",
    "01-comecar-aqui.md", "02-fluxo-da-fabrica-e-arquitetura-hermes.md", "03-validacao-e-referencia-do-repositorio.md",
    "trust-and-evidence.md", "technical-model.md", "usage.md", "reference.md", "operating-model.md", "lifecycle.md",
}
FORBIDDEN_COPY_PHRASES = [
    "## O problema", "## A solução", "Por que isso importa", "Por que a fábrica é diferente",
    "O que agentes soltos", "Benefícios", "futuro do trabalho", "garante qualidade",
    "aumenta eficiência", "traz confiança", "orquestra agentes para garantir",
]


class OpenSourceDocsTest(unittest.TestCase):
    def test_public_tree_matches_briefing(self) -> None:
        allowed_root_entries = {"assets", "pt-BR", "index.md", "mkdocs.yml", "factory-workflow.catalog.json", "promise-implementation-map.public.json", "public-surface.manifest.json"}
        self.assertEqual({path.name for path in (ROOT / "docs").iterdir()}, allowed_root_entries)
        self.assertEqual({p.name for p in (ROOT / "docs" / "pt-BR").glob("*.md")}, PT_PAGES)
        self.assertFalse((ROOT / "docs" / "en").exists())
        mkdocs = read_text("docs/mkdocs.yml")
        for page in PT_PAGES:
            self.assertIn(f"pt-BR/{page}", mkdocs)
        for old in OLD_CANONICAL_NAMES:
            self.assertNotIn(old, mkdocs)

    def test_root_readmes_point_to_new_pt_br_docs(self) -> None:
        for rel in ["README.md", "README.pt-BR.md"]:
            text = read_text(rel)
            for ref in ["docs/pt-BR/index.md", "docs/pt-BR/manual.md", "docs/pt-BR/linha-de-producao.md", "docs/pt-BR/uso.md", "docs/pt-BR/para-mantenedores.md"]:
                self.assertIn(ref, text)
            self.assertIn("Um teste local passando significa que o checkout e o kernel público estão coerentes", text)
            self.assertIn("factory/legacy-docs/", text)
            self.assertNotIn("docs/en/", text)

    def test_docs_are_not_product_copy(self) -> None:
        for path in (ROOT / "docs" / "pt-BR").glob("*.md"):
            text = path.read_text(encoding="utf-8")
            for phrase in FORBIDDEN_COPY_PHRASES:
                self.assertNotIn(phrase, text, path.name)

    def test_manual_contains_system_parts_and_boundaries(self) -> None:
        manual = read_text("docs/pt-BR/manual.md")
        self.assertGreater(len(manual.split()), 1800)
        for heading in ["## Definição", "## Hermes", "## Papéis", "## Estado", "## Artefatos", "## Ciclo", "## Limites"]:
            self.assertIn(heading, manual)
        for phrase in [
            "Hermes é o chão onde o trabalho fica visível",
            "cards, status, comentários, anexos, dependências, workers, bloqueios, transições",
            "verdade do produto",
            "Product SOT",
            "worker packet",
            "Receipt Five",
            "Prova local mostra coerência local",
            "Card criado mostra registro",
            "Evidência anexada mostra material disponível",
            "Decisão humana não deve ser simulada pela fábrica",
        ]:
            self.assertIn(phrase, manual)

    def test_linha_de_producao_shows_internal_mechanism(self) -> None:
        doc = read_text("docs/pt-BR/linha-de-producao.md")
        self.assertGreater(len(doc.split()), 4200)
        headings = ["Pedido", "Fonte", "Entendimento", "Verdade do produto", "Rota", "Método", "Capacidade", "Trabalho", "Hermes", "Execução", "Evidência", "Revisão", "Decisão", "Recibo", "Fechamento"]
        for h in headings:
            self.assertIn(f"## {h}", doc)
        for phrase in [
            "entrada recebida e fonte a preservar",
            "fatos, afirmações do pedido, decisões já tomadas, restrições, dependências, dúvidas, lacunas, conflitos, inferências",
            "fonte lida e do entendimento registrado",
            "rotas comuns incluem documentação, bug, feature, interface, CLI, integração, release, incidente, segurança, blockchain/Solana",
            "worker disponível, permissão, acesso, segredo, ambiente, ferramenta, repositório",
            "unidade de trabalho -> card Hermes -> resultado do worker -> revisão -> decisão/fechamento",
            "A revisão consome o que o worker devolveu",
            "A fábrica não simula autoridade humana",
            "o que foi pedido, o que foi produzido, que evidência sustenta, quem revisou ou decidiu",
            "entregue, bloqueado, parcial, reaberto, aprendido, arquivado e aguardando decisão",
        ]:
            self.assertIn(phrase, doc)

    def test_uso_contains_commands_and_claim_boundaries(self) -> None:
        uso = read_text("docs/pt-BR/uso.md")
        for command in [
            "python3 scripts/factoryctl.py doctor",
            "python3 scripts/factoryctl.py run minimal",
            "python3 scripts/factoryctl.py route-registry",
            "python3 scripts/factoryctl.py method-engines",
            "python3 scripts/factoryctl.py operating-systems",
            "python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json",
            "python3 scripts/factoryctl.py validate-card examples/minimal-hermes-project/card.md",
            "python3 scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md",
            "python3 scripts/factoryctl.py worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets",
        ]:
            self.assertIn(command, uso)
        for phrase in ["prova local", "contrato válido", "worker packet gerado", "execução viva no Hermes", "evidência consumida", "entrega fechada"]:
            self.assertIn(phrase, uso)

    def test_maintainer_doc_keeps_technical_details_out_of_main_path(self) -> None:
        doc = read_text("docs/pt-BR/para-mantenedores.md")
        for phrase in ["## Mapa", "## Documentação", "## Factory", "## Contratos", "## Comandos", "## Testes", "## Geração", "## Mudanças", "## Fronteiras"]:
            self.assertIn(phrase, doc)
        self.assertIn("explicação humana", doc)
        self.assertIn("contrato executável", doc)
        self.assertIn("teste, validador ou prova local", doc)
        self.assertIn("Não crie `trust-and-evidence.md`", doc)
        self.assertIn("Não crie `technical-model.md`", doc)

    def test_public_validators_and_docs_build_pass(self) -> None:
        commands = [
            ([sys.executable, "scripts/validate_public_json_artifacts.py"], CODE_ROOT),
            ([sys.executable, "scripts/validate_public_surface_sync.py"], CODE_ROOT),
            ([sys.executable, "scripts/validate_promise_implementation_map.py"], CODE_ROOT),
            ([sys.executable, "scripts/generate_factory_reference_docs.py", "--check"], CODE_ROOT),
            ([sys.executable, "-m", "mkdocs", "build", "-f", "docs/mkdocs.yml", "--strict", "--site-dir", "/tmp/overkill-test-docs-site"], ROOT),
        ]
        for command, cwd in commands:
            with self.subTest(command=" ".join(command)):
                result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_package_metadata_matches_doc_surface(self) -> None:
        pyproject = read_text("pyproject.toml")
        self.assertNotIn('"share/overkill-factory/docs/en"', pyproject)
        self.assertIn('"share/overkill-factory/docs/pt-BR"', pyproject)
        self.assertIn('"share/overkill-factory/docs/assets/public-map"', pyproject)


if __name__ == "__main__":
    unittest.main()
