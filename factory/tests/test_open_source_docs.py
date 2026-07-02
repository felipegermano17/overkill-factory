from __future__ import annotations

import json
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
ROOT = CODE_ROOT.parent


def project_path(rel: str) -> Path:
    code_prefixes = ("adapters/", "agents/", "examples/", "fixtures/", "schemas/", "scripts/", "skills/", "templates/", "tests/")
    code_names = {"pyproject.toml", ".env.example"}
    return CODE_ROOT / rel if rel in code_names or rel.startswith(code_prefixes) else ROOT / rel


def read_text(rel: str) -> str:
    return project_path(rel).read_text(encoding="utf-8")


class OpenSourceDocsTest(unittest.TestCase):
    def test_root_readmes_are_simple_bilingual_product_entries(self) -> None:
        readme = read_text("README.md")
        readme_pt = read_text("README.pt-BR.md")

        for text in [readme, readme_pt]:
            self.assertIn("docs/en/factory-manual.md", text)
            self.assertIn("docs/en/technical-reference.md", text)
            self.assertIn("docs/pt-BR/factory-manual.md", text)
            self.assertIn("https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html", text)
            self.assertIn("python3 scripts/factoryctl.py doctor", text)
            self.assertIn("python3 scripts/factoryctl.py run minimal", text)
            self.assertIn("40 public workers" if text is readme else "40 workers publicos", text)
            self.assertNotIn("factory/legacy-docs/", text)
            self.assertNotIn("docs/en/index.md", text)
            self.assertNotIn("docs/en/manual.md", text)
        self.assertIn("Overkill Factory is a product factory", readme)
        self.assertIn("A Overkill Factory e uma fabrica de produto", readme_pt)
        self.assertIn("A passing local proof means the public kernel is coherent", readme)
        self.assertIn("Um teste local passando significa que o kernel publico esta coerente", readme_pt)
        self.assertIn("`docs/`", readme)
        self.assertIn("`factory/`", readme)

    def test_docs_tree_is_small_bilingual_and_canonical(self) -> None:
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

        page_names = {"factory-manual.md", "technical-reference.md"}
        self.assertEqual({p.name for p in (ROOT / "docs" / "en").glob("*.md")}, page_names)
        self.assertEqual({p.name for p in (ROOT / "docs" / "pt-BR").glob("*.md")}, page_names)
        self.assertFalse((CODE_ROOT / "legacy-docs").exists())

        mkdocs = read_text("docs/mkdocs.yml")
        self.assertIn("en/factory-manual.md", mkdocs)
        self.assertIn("en/technical-reference.md", mkdocs)
        self.assertIn("pt-BR/factory-manual.md", mkdocs)
        self.assertIn("pt-BR/technical-reference.md", mkdocs)
        self.assertIn("assets/public-map/overkill-factory-map-v1.0.3.html", mkdocs)
        self.assertNotIn("en/index.md", mkdocs)
        self.assertNotIn("en/manual.md", mkdocs)
        self.assertNotIn("architecture/", mkdocs)
        self.assertNotIn("maintenance/", mkdocs)

    def test_bilingual_pages_are_complete_not_summaries(self) -> None:
        pairs = [
            ("factory-manual.md", "The Factory tries to make AI work controllable", "A Factory tenta tornar o trabalho com IA controlavel"),
            ("factory-manual.md", "Hermes Kanban remains the runtime source of truth", "Hermes Kanban continua sendo a fonte de verdade"),
            ("factory-manual.md", "Receipt Five", "Receipt Five"),
            ("technical-reference.md", "factoryctl", "factoryctl"),
            ("technical-reference.md", "Route Classes", "Classes De Rota"),
            ("technical-reference.md", "Hermes owns runtime state", "Hermes controla estado de runtime"),
        ]
        for file_name, en_phrase, pt_phrase in pairs:
            en = read_text(f"docs/en/{file_name}")
            pt = read_text(f"docs/pt-BR/{file_name}")
            with self.subTest(file=file_name, phrase=en_phrase):
                self.assertIn(en_phrase, en)
                self.assertIn(pt_phrase, pt)
                self.assertGreater(len(en.split()), 900)
                self.assertGreater(len(pt.split()), 900)

    def test_docs_are_grounded_in_executable_factory_facts(self) -> None:
        version = tomllib.loads(read_text("pyproject.toml"))["project"]["version"]
        workflow = json.loads(read_text("docs/factory-workflow.catalog.json"))
        workers = json.loads(read_text("agents/worker-registry.public.json"))
        routes = json.loads(read_text("templates/factory-route-registry.json"))
        methods = json.loads(read_text("templates/method-engine-registry.json"))
        operating_systems = json.loads(read_text("templates/factory-operating-system-registry.json"))

        readme = read_text("README.md")
        technical = read_text("docs/en/technical-reference.md")

        self.assertIn(f"version `{version}`", technical)
        self.assertIn(f"{len(workflow['phases'])} compiled phases", readme)
        self.assertIn(f"{len(workers['workers'])} public workers", readme)
        self.assertIn(f"{len(routes['routes'])} route classes", technical)
        self.assertIn(f"{len(methods['engines'])} method engines", technical)
        self.assertIn(f"{len(operating_systems['entries'])} operating-system areas", technical)
        self.assertIn("F27 - Factory Maturity Audit", technical)
        self.assertIn("product_creation", technical)

    def test_public_validators_and_docs_build_pass(self) -> None:
        commands = [
            ([sys.executable, "scripts/validate_public_json_artifacts.py"], CODE_ROOT),
            ([sys.executable, "scripts/validate_public_surface_sync.py"], CODE_ROOT),
            ([sys.executable, "scripts/validate_promise_implementation_map.py"], CODE_ROOT),
            ([sys.executable, "-m", "mkdocs", "build", "-f", "docs/mkdocs.yml", "--strict", "--site-dir", str(ROOT / ".tmp" / "overkill-test-docs-site")], ROOT),
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
