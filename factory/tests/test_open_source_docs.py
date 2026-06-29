from __future__ import annotations

import json
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FACTORY_ROOT = REPO_ROOT / "factory"


def read_repo(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def read_factory(rel: str) -> str:
    return (FACTORY_ROOT / rel).read_text(encoding="utf-8")


class OpenSourceDocsTest(unittest.TestCase):
    def test_root_surface_is_clean_and_intentional(self) -> None:
        allowed_visible = {"README.md", "LICENSE", "docs", "factory"}
        actual = {
            path.name
            for path in REPO_ROOT.iterdir()
            if path.name not in {".git", ".github", ".gitignore", ".gitattributes", ".tmp"}
        }
        self.assertEqual(actual, allowed_visible)
        self.assertTrue((REPO_ROOT / ".github").is_dir())

    def test_root_readme_is_human_product_entrypoint(self) -> None:
        readme = read_repo("README.md")
        required = [
            "Overkill Factory is a production line for agentic product work.",
            "You bring the first signal",
            "Hermes is the runtime",
            "Overkill Factory is the production method",
            "packet exists but no worker result exists",
            "fail-closed",
            "docs/",
            "factory/",
            "docs/pt-BR/index.md",
            "Implementation status",
            "real operator signal",
            "factoryctl doctor",
            "factoryctl run minimal",
        ]
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)
        for obsolete in [
            "codex plugin add overkill-factory-bridge@overkill-factory",
            "legacy-docs/reference/public-map.md",
            "docs/prd.md",
        ]:
            if obsolete == "__not_checked__":
                continue
            with self.subTest(obsolete=obsolete):
                self.assertNotIn(obsolete, readme)

    def test_public_docs_are_rewritten_english_and_portuguese(self) -> None:
        english_docs = [
            "docs/index.md",
            "docs/factory-manual.md",
            "docs/how-it-works.md",
            "docs/autonomy.md",
            "docs/process.md",
            "docs/method-gates-workers.md",
            "docs/evidence-and-receipt-five.md",
            "docs/security-and-release.md",
            "docs/installation-and-use.md",
            "docs/repository-layout.md",
            "docs/terminology.md",
            "docs/implementation-status.md",
        ]
        portuguese_docs = [
            "docs/pt-BR/index.md",
            "docs/pt-BR/manual-da-fabrica.md",
            "docs/pt-BR/como-funciona.md",
            "docs/pt-BR/autonomia.md",
            "docs/pt-BR/processo.md",
            "docs/pt-BR/metodo-gates-workers.md",
            "docs/pt-BR/evidencia-e-receipt-five.md",
            "docs/pt-BR/seguranca-e-release.md",
            "docs/pt-BR/instalacao-e-uso.md",
            "docs/pt-BR/estrutura-do-repositorio.md",
            "docs/pt-BR/terminologia.md",
            "docs/pt-BR/status-de-implementacao.md",
        ]
        for rel in english_docs + portuguese_docs:
            with self.subTest(rel=rel):
                text = read_repo(rel)
                self.assertGreater(len(text), 300)

        combined_en = "\n".join(read_repo(rel) for rel in english_docs)
        combined_pt = "\n".join(read_repo(rel) for rel in portuguese_docs)
        for phrase in [
            "PRD",
            "no-idle",
            "Receipt Five",
            "worker packet",
            "worker result",
            "Hermes work graph",
            "fail closed",
            "product experience",
            "Release requires more than passing tests",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined_en)
        for phrase in [
            "PRD",
            "no-idle",
            "Receipt Five",
            "Worker packet",
            "Worker result",
            "Grafo Hermes",
            "Segurança",
            "release",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined_pt)

    def test_docs_navigation_build_config_points_to_public_docs(self) -> None:
        mkdocs = read_repo("docs/mkdocs.yml")
        for expected in [
            "docs_dir: .",
            "How It Works: how-it-works.md",
            "Autonomy and No-Idle: autonomy.md",
            "Portuguese:",
            "pt-BR/index.md",
        ]:
            self.assertIn(expected, mkdocs)
        self.assertNotIn("factory/legacy-docs/index.md", mkdocs)

    def test_factory_code_has_internal_entrypoint_and_package_metadata(self) -> None:
        readme = read_factory("README.md")
        pyproject = read_factory("pyproject.toml")
        for phrase in [
            "factory implementation",
            "python -m unittest discover -s tests",
            "python scripts/factoryctl.py doctor",
        ]:
            self.assertIn(phrase, readme)
        metadata = tomllib.loads(pyproject)
        self.assertEqual(metadata["project"]["name"], "overkill-factory")
        self.assertIn("factoryctl", metadata["project"]["scripts"])
        self.assertIn("docs", metadata["project"]["optional-dependencies"])

    def test_examples_and_fixtures_are_code_scoped_not_root_scoped(self) -> None:
        self.assertFalse((REPO_ROOT / "examples").exists())
        self.assertFalse((REPO_ROOT / "fixtures").exists())
        self.assertTrue((FACTORY_ROOT / "examples" / "README.md").is_file())
        self.assertTrue((FACTORY_ROOT / "fixtures" / "README.md").is_file())

        examples = read_factory("examples/README.md")
        fixtures = read_factory("fixtures/README.md")
        policy = read_repo("docs/repository-layout.md")
        for phrase in [
            "Generated worker packets and gate reports belong in `.tmp/`",
            "Do not commit generated run output",
        ]:
            self.assertIn(phrase, examples)
        for phrase in ["regression", "public-safe"]:
            self.assertIn(phrase, fixtures)
        self.assertIn("Do not reintroduce root-level", policy)
        self.assertIn("`examples/`, `fixtures/`", policy)

    def test_public_docs_do_not_claim_live_e2e_is_done(self) -> None:
        status = read_repo("docs/implementation-status.md") + "\n" + read_repo("README.md")
        for phrase in [
            "remaining live proof",
            "real operator signal",
            "manager-created FactoryRun",
            "real manager + Hermes + worker + operator E2E",
        ]:
            self.assertIn(phrase, status)
        self.assertNotRegex(status, r"fully autonomous|100% ready|guarantees production")

    def test_github_workflows_use_new_layout(self) -> None:
        ci = read_repo(".github/workflows/ci.yml")
        release = read_repo(".github/workflows/release-cli-smoke.yml")
        self.assertIn("working-directory: factory", ci)
        self.assertIn("python -m unittest discover -s tests", ci)
        self.assertIn("python -m mkdocs build -f docs/mkdocs.yml --strict", ci)
        self.assertIn("python -m pip install \"./factory[docs]\"", ci)
        self.assertIn("python -m pip install ./factory", release)
        self.assertIn('"factory/**"', release)

    def test_minimal_example_still_runs_from_factory_code_root(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/factoryctl.py", "gate-report", "--card", "examples/minimal-hermes-project/card.md"],
            cwd=FACTORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(result.stdout)
        self.assertEqual(report["gate_status"], "ready_for_worker_execution")
        self.assertIn("independent-reviewer", report["required_workers"])

    def test_installation_docs_include_runnable_validation_commands(self) -> None:
        install = read_repo("docs/installation-and-use.md")
        for command in [
            "python -m pip install ./factory",
            "factoryctl doctor",
            "factoryctl run minimal",
            "python -m unittest discover -s tests",
            "python scripts/validate_public_json_artifacts.py",
            "python scripts/validate_promise_implementation_map.py",
            "python scripts/validate_public_surface_sync.py",
            "python scripts/supply_chain_proof.py --check --no-write",
            "python -m mkdocs build -f docs/mkdocs.yml --strict",
        ]:
            self.assertIn(command, install)

    def test_public_metadata_uses_live_repository_urls_and_explicit_license(self) -> None:
        pyproject = read_factory("pyproject.toml")
        mkdocs = read_repo("docs/mkdocs.yml")
        license_text = read_repo("LICENSE")
        owner = "feli" + "pegermano17"
        repo_url = f"https://github.com/{owner}/overkill-factory"
        self.assertIn(f'Homepage = "{repo_url}"', pyproject)
        self.assertIn(f'Documentation = "{repo_url}/tree/main/docs"', pyproject)
        self.assertIn(f"repo_url: {repo_url}", mkdocs)
        self.assertTrue(license_text.startswith("MIT License"))


if __name__ == "__main__":
    unittest.main()
