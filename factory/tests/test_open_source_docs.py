from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
ROOT = CODE_ROOT.parent


def project_path(rel: str) -> Path:
    code_prefixes = (
        "adapters/",
        "agents/",
        "examples/",
        "fixtures/",
        "schemas/",
        "scripts/",
        "skills/",
        "templates/",
        "tests/",
        "legacy-docs/",
    )
    code_names = {"pyproject.toml", ".env.example"}
    return CODE_ROOT / rel if rel in code_names or rel.startswith(code_prefixes) else ROOT / rel


def read_text(rel: str) -> str:
    return project_path(rel).read_text(encoding="utf-8")


EN_PAGES = {
    "index.md",
    "01-start-here.md",
    "02-product-problem.md",
    "03-how-a-request-moves.md",
    "04-operator-experience.md",
    "05-evidence-and-receipts.md",
    "06-human-decisions.md",
    "07-hermes-and-factory.md",
    "08-workers-and-work-units.md",
    "09-status-boundaries-and-proof.md",
    "10-local-validation.md",
    "11-repository-reference.md",
    "12-glossary.md",
    "13-maintainer-guide.md",
}

PT_PAGES = {
    "index.md",
    "01-comecar-aqui.md",
    "02-o-problema-do-produto.md",
    "03-como-um-pedido-anda.md",
    "04-experiencia-do-operador.md",
    "05-prova-e-recibos.md",
    "06-decisoes-humanas.md",
    "07-hermes-e-factory.md",
    "08-workers-e-unidades-de-trabalho.md",
    "09-status-limites-e-prova.md",
    "10-validacao-local.md",
    "11-referencia-do-repositorio.md",
    "12-glossario.md",
    "13-guia-de-manutencao.md",
}

OLD_CANONICAL_NAMES = {
    "manual.md",
    "operating-model.md",
    "lifecycle.md",
    "trust-and-evidence.md",
    "technical-model.md",
    "usage.md",
    "reference.md",
}


class OpenSourceDocsTest(unittest.TestCase):
    def test_root_readmes_are_product_entries_not_inventory(self) -> None:
        readme = read_text("README.md")
        readme_pt = read_text("README.pt-BR.md")

        for text in [readme, readme_pt]:
            self.assertIn("docs/en/index.md", text)
            self.assertIn("docs/pt-BR/index.md", text)
            self.assertIn(
                "https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html",
                text,
            )
            self.assertIn("factory/legacy-docs/", text)
            self.assertIn("python3 scripts/factoryctl.py doctor", text)
            self.assertIn("python3 scripts/factoryctl.py run minimal", text)
            self.assertNotIn("docs/architecture/", text)
            self.assertNotIn("docs/operations/", text)

        self.assertIn("Agents are useful. They are also very good at looking done before the work is proven.", readme)
        self.assertIn("Agente ajuda. Mas agente também sabe parecer pronto antes de estar provado.", readme_pt)
        self.assertIn("A passing local proof means the public kernel is coherent", readme)
        self.assertIn("Um teste local passando significa que o kernel público está coerente", readme_pt)
        self.assertIn("40 public workers", readme)
        self.assertIn("40 workers públicos", readme_pt)
        self.assertNotIn("source intake, source ledger, product truth, method contract", readme)
        self.assertNotIn("intake de fonte, source ledger, verdade de produto", readme_pt)

    def test_docs_tree_is_rebuilt_around_reader_questions(self) -> None:
        allowed_root_entries = {
            "assets",
            "en",
            "pt-BR",
            "index.md",
            "mkdocs.yml",
            "factory-workflow.catalog.json",
            "promise-implementation-map.public.json",
            "public-surface.manifest.json",
        }
        actual = {path.name for path in (ROOT / "docs").iterdir()}
        self.assertEqual(actual, allowed_root_entries)
        self.assertEqual({p.name for p in (ROOT / "docs" / "en").glob("*.md")}, EN_PAGES)
        self.assertEqual({p.name for p in (ROOT / "docs" / "pt-BR").glob("*.md")}, PT_PAGES)

        mkdocs = read_text("docs/mkdocs.yml")
        for forbidden in OLD_CANONICAL_NAMES:
            self.assertNotIn(f"en/{forbidden}", mkdocs)
            self.assertNotIn(f"pt-BR/{forbidden}", mkdocs)
        for expected in [
            "en/01-start-here.md",
            "en/04-operator-experience.md",
            "en/06-human-decisions.md",
            "en/08-workers-and-work-units.md",
            "en/09-status-boundaries-and-proof.md",
            "pt-BR/01-comecar-aqui.md",
            "pt-BR/04-experiencia-do-operador.md",
            "pt-BR/06-decisoes-humanas.md",
            "pt-BR/08-workers-e-unidades-de-trabalho.md",
            "pt-BR/09-status-limites-e-prova.md",
        ]:
            self.assertIn(expected, mkdocs)

    def test_legacy_docs_are_preserved_but_not_canonical(self) -> None:
        legacy = CODE_ROOT / "legacy-docs" / "public-docs-before-product-manual"
        self.assertTrue((legacy / "README.md").is_file())
        self.assertTrue((legacy / "architecture" / "deterministic-control-plane.md").is_file())
        self.assertTrue((legacy / "operations" / "validation-and-release.md").is_file())
        self.assertIn("not the canonical public documentation", (legacy / "README.md").read_text(encoding="utf-8"))
        self.assertIn("not the canonical public documentation", read_text("legacy-docs/README.md"))
        self.assertFalse((ROOT / "docs" / "architecture").exists())
        self.assertFalse((ROOT / "docs" / "operations").exists())

    def test_bilingual_pages_are_deep_and_have_distinct_jobs(self) -> None:
        pairs = [
            ("01-start-here.md", "01-comecar-aqui.md", "controlled production", "produção controlada"),
            ("02-product-problem.md", "02-o-problema-do-produto.md", "False progress", "Progresso falso"),
            ("03-how-a-request-moves.md", "03-como-um-pedido-anda.md", "Hermes Kanban remains the runtime source of truth", "Hermes Kanban continua sendo a fonte de verdade"),
            ("04-operator-experience.md", "04-experiencia-do-operador.md", "Durable Operator Inbox", "Durable Operator Inbox"),
            ("05-evidence-and-receipts.md", "05-prova-e-recibos.md", "Receipt Five", "Receipt Five"),
            ("06-human-decisions.md", "06-decisoes-humanas.md", "production, mainnet, funds, secrets", "produção, mainnet, fundos, segredos"),
            ("07-hermes-and-factory.md", "07-hermes-e-factory.md", "Hermes is the live runtime", "Hermes é o runtime vivo"),
            ("08-workers-and-work-units.md", "08-workers-e-unidades-de-trabalho.md", "Worker Packet", "Worker Packet"),
            ("09-status-boundaries-and-proof.md", "09-status-limites-e-prova.md", "local tests prove checkout coherence", "Teste local prova coerência do checkout"),
            ("10-local-validation.md", "10-validacao-local.md", "Local validation is not live Hermes E2E proof", "validação local não é prova E2E Hermes viva"),
            ("11-repository-reference.md", "11-referencia-do-repositorio.md", "Route classes", "Classes de rota"),
            ("12-glossary.md", "12-glossario.md", "Product SOT", "Product SOT"),
            ("13-maintainer-guide.md", "13-guia-de-manutencao.md", "Do not reintroduce `manual.md`", "Não reintroduza `manual.md`"),
        ]
        for en_file, pt_file, en_phrase, pt_phrase in pairs:
            en = read_text(f"docs/en/{en_file}")
            pt = read_text(f"docs/pt-BR/{pt_file}")
            with self.subTest(file=en_file):
                self.assertIn(en_phrase, en)
                self.assertIn(pt_phrase, pt)
                self.assertGreater(len(en.split()), 180)
                self.assertGreater(len(pt.split()), 180)

    def test_core_docs_include_required_examples_and_boundaries(self) -> None:
        en_operator = read_text("docs/en/04-operator-experience.md")
        pt_operator = read_text("docs/pt-BR/04-experiencia-do-operador.md")
        en_evidence = read_text("docs/en/05-evidence-and-receipts.md")
        pt_evidence = read_text("docs/pt-BR/05-prova-e-recibos.md")
        en_human = read_text("docs/en/06-human-decisions.md")
        pt_human = read_text("docs/pt-BR/06-decisoes-humanas.md")
        en_status = read_text("docs/en/09-status-boundaries-and-proof.md")
        pt_status = read_text("docs/pt-BR/09-status-limites-e-prova.md")

        for text in [en_operator, pt_operator]:
            self.assertIn("Bad response", text) if text is en_operator else self.assertIn("Resposta ruim", text)
            self.assertIn("Good response", text) if text is en_operator else self.assertIn("Resposta boa", text)
        for text in [en_evidence, pt_evidence]:
            self.assertIn("Weak proof", text) if text is en_evidence else self.assertIn("Prova fraca", text)
            self.assertIn("Strong proof", text) if text is en_evidence else self.assertIn("Prova boa", text)
        for text in [en_human, pt_human]:
            self.assertIn("Bad request", text) if text is en_human else self.assertIn("Pedido ruim", text)
            self.assertIn("Good request", text) if text is en_human else self.assertIn("Pedido bom", text)
        for text in [en_status, pt_status]:
            self.assertIn("The visual map", text) if text is en_status else self.assertIn("O mapa visual", text)
            self.assertIn("Do not claim public documentation is runtime proof", text) if text is en_status else self.assertIn("Não diga que docs públicas provam runtime", text)

    def test_docs_are_grounded_in_executable_factory_facts(self) -> None:
        workflow = json.loads(read_text("docs/factory-workflow.catalog.json"))
        workers = json.loads(read_text("agents/worker-registry.public.json"))
        routes = json.loads(read_text("templates/factory-route-registry.json"))
        methods = json.loads(read_text("templates/method-engine-registry.json"))
        operating_systems = json.loads(read_text("templates/factory-operating-system-registry.json"))

        status = read_text("docs/en/09-status-boundaries-and-proof.md")
        hermes = read_text("docs/en/07-hermes-and-factory.md")
        reference = read_text("docs/en/11-repository-reference.md")
        glossary = read_text("docs/en/12-glossary.md")

        self.assertIn(f"{len(workflow['phases'])} compiled phases", status)
        self.assertIn(f"{len(workers['workers'])} public workers", status)
        self.assertIn(f"{len(routes['routes'])} route classes", status)
        self.assertIn(f"{len(methods['engines'])} method engines", status)
        self.assertIn(f"{len(operating_systems['entries'])} operating-system areas", status)
        self.assertIn("Hermes profiles materialize worker roles", hermes)
        self.assertIn("product_creation", reference)
        self.assertIn("F0 — Pre-Start / Sealed Source Envelope", read_text("docs/en/03-how-a-request-moves.md"))
        self.assertIn("Product SOT", glossary)

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
        self.assertNotIn('"share/overkill-factory/docs/operator"', pyproject)
        self.assertNotIn('"share/overkill-factory/docs/architecture"', pyproject)

    def test_public_docs_do_not_reintroduce_removed_bridge_plugin_surface(self) -> None:
        for path in [ROOT / "README.md", ROOT / "README.pt-BR.md", ROOT / "docs" / "en", ROOT / "docs" / "pt-BR"]:
            texts = []
            if path.is_dir():
                texts = [p.read_text(encoding="utf-8") for p in path.glob("*.md")]
            else:
                texts = [path.read_text(encoding="utf-8")]
            for text in texts:
                self.assertNotIn("codex plugin add overkill-factory-bridge@overkill-factory", text)
                self.assertNotIn("docs/operator/overkill-factory-bridge-plugin.md", text)


if __name__ == "__main__":
    unittest.main()
