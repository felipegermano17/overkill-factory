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

EN_PAGES = {"index.md", "01-start-here.md", "02-factory-flow-and-hermes-architecture.md", "03-validation-and-repository-reference.md"}
PT_PAGES = {"index.md", "01-comecar-aqui.md", "02-fluxo-da-fabrica-e-arquitetura-hermes.md", "03-validacao-e-referencia-do-repositorio.md"}
REMOVED_SHALLOW_DOCS = {
    "02-product-problem.md", "03-how-a-request-moves.md", "04-operator-experience.md", "05-evidence-and-receipts.md",
    "06-human-decisions.md", "07-hermes-and-factory.md", "08-workers-and-work-units.md", "09-status-boundaries-and-proof.md",
    "10-local-validation.md", "11-repository-reference.md", "03-local-validation.md", "04-repository-reference.md", "12-glossary.md", "13-maintainer-guide.md",
    "02-o-problema-do-produto.md", "03-como-um-pedido-anda.md", "04-experiencia-do-operador.md", "05-prova-e-recibos.md",
    "06-decisoes-humanas.md", "07-hermes-e-factory.md", "08-workers-e-unidades-de-trabalho.md", "09-status-limites-e-prova.md",
    "10-validacao-local.md", "11-referencia-do-repositorio.md", "03-validacao-local.md", "04-referencia-do-repositorio.md", "12-glossario.md", "13-guia-de-manutencao.md",
}
OLD_CANONICAL_NAMES = {"manual.md", "operating-model.md", "lifecycle.md", "trust-and-evidence.md", "technical-model.md", "usage.md", "reference.md"}

class OpenSourceDocsTest(unittest.TestCase):
    def test_root_readmes_point_to_small_deep_docs(self) -> None:
        readme = read_text("README.md")
        readme_pt = read_text("README.pt-BR.md")
        for text in [readme, readme_pt]:
            self.assertIn("docs/en/index.md", text)
            self.assertIn("docs/pt-BR/index.md", text)
            self.assertIn("https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html", text)
            self.assertIn("factory/legacy-docs/", text)
            self.assertIn("python3 scripts/factoryctl.py doctor", text)
            self.assertIn("python3 scripts/factoryctl.py run minimal", text)
        self.assertIn("docs/en/02-factory-flow-and-hermes-architecture.md", readme)
        self.assertIn("docs/pt-BR/02-fluxo-da-fabrica-e-arquitetura-hermes.md", readme_pt)
        self.assertIn("A passing local proof means the public kernel is coherent", readme)
        self.assertIn("Um teste local passando significa que o kernel público está coerente", readme_pt)

    def test_docs_tree_is_small_and_not_theatrical(self) -> None:
        allowed_root_entries = {"assets", "en", "pt-BR", "index.md", "mkdocs.yml", "factory-workflow.catalog.json", "promise-implementation-map.public.json", "public-surface.manifest.json"}
        self.assertEqual({path.name for path in (ROOT / "docs").iterdir()}, allowed_root_entries)
        self.assertEqual({p.name for p in (ROOT / "docs" / "en").glob("*.md")}, EN_PAGES)
        self.assertEqual({p.name for p in (ROOT / "docs" / "pt-BR").glob("*.md")}, PT_PAGES)
        mkdocs = read_text("docs/mkdocs.yml")
        for forbidden in OLD_CANONICAL_NAMES | REMOVED_SHALLOW_DOCS:
            self.assertNotIn(f"en/{forbidden}", mkdocs)
            self.assertNotIn(f"pt-BR/{forbidden}", mkdocs)
        self.assertIn("en/02-factory-flow-and-hermes-architecture.md", mkdocs)
        self.assertIn("pt-BR/02-fluxo-da-fabrica-e-arquitetura-hermes.md", mkdocs)

    def test_legacy_docs_are_preserved_but_not_canonical(self) -> None:
        legacy = CODE_ROOT / "legacy-docs" / "public-docs-before-product-manual"
        self.assertTrue((legacy / "README.md").is_file())
        self.assertIn("not the canonical public documentation", (legacy / "README.md").read_text(encoding="utf-8"))
        self.assertIn("not the canonical public documentation", read_text("legacy-docs/README.md"))

    def test_dense_flow_doc_contains_real_factory_mechanics(self) -> None:
        workflow = json.loads(read_text("docs/factory-workflow.catalog.json"))
        workers = json.loads(read_text("agents/worker-registry.public.json"))
        routes = json.loads(read_text("templates/factory-route-registry.json"))
        methods = json.loads(read_text("templates/method-engine-registry.json"))
        operating_systems = json.loads(read_text("templates/factory-operating-system-registry.json"))
        en = read_text("docs/en/02-factory-flow-and-hermes-architecture.md")
        pt = read_text("docs/pt-BR/02-fluxo-da-fabrica-e-arquitetura-hermes.md")
        self.assertGreater(len(en.split()), 5000)
        self.assertGreater(len(pt.split()), 5000)
        for phase in workflow["phases"]:
            self.assertIn(f"### {phase['phase_id']} — {phase['phase_name']}", en)
            self.assertIn(f"### {phase['phase_id']} — {phase['phase_name']}", pt)
            for required in ["Required artifacts", "Required gates", "Required workers", "Blocked actions", "Completion detection"]:
                self.assertIn(required, en)
        self.assertIn(f"{len(workflow['phases'])} compiled phases", en)
        self.assertIn(f"{len(workers['workers'])} public workers", en)
        self.assertIn(f"{len(routes['routes'])} route classes", en)
        self.assertIn(f"{len(methods['engines'])} method engines", en)
        self.assertIn(f"{len(operating_systems['entries'])} operating-system areas", en)
        for phrase in [
            "Hermes is the live runtime source of truth", "Hermes profiles materialize worker roles", "Worker Packet", "Receipt Five",
            "Bad request", "Good request", "Weak proof", "Strong proof", "production, mainnet, funds, secrets",
            "status_bridge", "start_bridge", "question_bridge", "decision_bridge", "change_bridge", "exception_bridge", "handoff_bridge", "learnback_forwarding",
            "not allowed to execute factory work", "local tests prove checkout coherence", "Do not claim public documentation is runtime proof",
            "product_creation", "Route classes", "F0 — Pre-Start / Sealed Source Envelope",
            "Three end-to-end worked examples", "Build the customer onboarding flow", "Users cannot reset passwords", "Promote version 1.2.0", "Failure-pattern index",
        ]:
            self.assertIn(phrase, en)
        for phrase in ["Hermes é a fonte de verdade viva do runtime", "Worker Packet", "Receipt Five", "Pedido ruim", "Pedido bom", "Prova fraca", "Prova boa", "produção, mainnet, fundos, segredos", "Teste local prova coerência do checkout", "Não diga que docs públicas provam runtime", "Classes de rota", "Três exemplos ponta-a-ponta", "usuários não conseguem resetar senha", "Promover versão 1.2.0", "Índice de padrões de falha"]:
            self.assertIn(phrase, pt)

    def test_validation_and_reference_remain_practical(self) -> None:
        en_validation = read_text("docs/en/03-validation-and-repository-reference.md")
        pt_validation = read_text("docs/pt-BR/03-validacao-e-referencia-do-repositorio.md")
        reference = en_validation
        for text in [en_validation, pt_validation]:
            self.assertIn("python3 scripts/validate_public_surface_sync.py", text)
            self.assertIn("python3 scripts/validate_promise_implementation_map.py", text)
        self.assertIn("product_creation", reference)
        self.assertIn("Route classes", reference)

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
        self.assertIn('"share/overkill-factory/docs/en"', pyproject)
        self.assertIn('"share/overkill-factory/docs/pt-BR"', pyproject)
        self.assertIn('"share/overkill-factory/docs/assets/public-map"', pyproject)

if __name__ == "__main__":
    unittest.main()
