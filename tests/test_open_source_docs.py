from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class OpenSourceDocsTest(unittest.TestCase):
    def test_readme_is_external_user_entrypoint(self) -> None:
        readme = read_text("README.md")
        required_headings = [
            "What It Is",
            "Factory Map",
            "Who It Is For",
            "What It Does",
            "What It Does Not Do",
            "How Hermes Fits",
            "Operator Path",
            "Quickstart",
            "First Value In 10 Minutes",
            "Repository Shape",
            "Current Status",
            "Documentation Map",
        ]

        for heading in required_headings:
            with self.subTest(heading=heading):
                self.assertIn(f"## {heading}", readme)

        for rel in [
            "docs/getting-started/quickstart-hermes.md",
            "docs/governance/document-governance.md",
            "docs/concepts/factory-flow.md",
            "docs/concepts/overkill-factory-method.md",
            "docs/concepts/operator-journey.md",
            "docs/visuals/README.md",
            "docs/visuals/overkill-factory-map-v0.1.0.svg",
            "docs/visuals/overkill-factory-map-v0.1.0.html",
            "docs/agents/worker-profiles.md",
            "agents/README.md",
            "docs/agents/factory-stage-agent-map.md",
            "docs/agents/capability-packs.md",
            "docs/control-tower/open-source-setup.md",
            "docs/operations/validation-and-release.md",
            "docs/operations/release-policy.md",
            "docs/architecture/hermes-integration.md",
            "docs/getting-started/install-in-hermes.md",
            "docs/reference/cli.md",
            "docs/examples/gallery.md",
            "docs/security/oss-security.md",
            "docs/maintenance/repo-surface.md",
            "docs/visuals/README.md",
            "docs/visuals/overkill-factory-map-v0.1.0.svg",
            "docs/visuals/overkill-factory-map-v0.1.0.html",
            "examples/minimal-hermes-project/README.md",
            ".env.example",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
        ]:
            with self.subTest(link=rel):
                self.assertIn(rel.replace("\\", "/"), readme)

        for command in ["factoryctl doctor", "factoryctl init", "factoryctl run minimal"]:
            with self.subTest(command=command):
                self.assertIn(command, readme)

    def test_public_docs_skeleton_exists(self) -> None:
        required_paths = [
            "docs/getting-started/quickstart-hermes.md",
            "docs/governance/document-governance.md",
            "docs/concepts/factory-flow.md",
            "docs/concepts/overkill-factory-method.md",
            "docs/concepts/operator-journey.md",
            "docs/agents/worker-profiles.md",
            "agents/README.md",
            "docs/agents/factory-stage-agent-map.md",
            "docs/agents/capability-packs.md",
            "docs/control-tower/open-source-setup.md",
            "docs/operations/validation-and-release.md",
            "docs/operations/release-policy.md",
            "docs/operations/troubleshooting.md",
            "docs/architecture/hermes-integration.md",
            "docs/index.md",
            "docs/getting-started/install-in-hermes.md",
            "docs/reference/cli.md",
            "docs/examples/gallery.md",
            "docs/security/oss-security.md",
            "docs/maintenance/repo-surface.md",
            "examples/minimal-hermes-project/README.md",
            "examples/minimal-hermes-project/input-paper.md",
            "examples/minimal-hermes-project/expected-flow.md",
            "examples/minimal-hermes-project/expected-receipt-five.json",
            ".env.example",
            "pyproject.toml",
            "CHANGELOG.md",
            "mkdocs.yml",
            "CONTRIBUTING.md",
            "SECURITY.md",
            ".github/dependabot.yml",
            ".github/PROJECT_SURFACE.md",
            ".github/workflows/codeql.yml",
            ".github/workflows/dependency-review.yml",
            ".github/workflows/security.yml",
            ".github/ISSUE_TEMPLATE/bug_report.yml",
            ".github/ISSUE_TEMPLATE/feature_request.yml",
            ".github/ISSUE_TEMPLATE/config.yml",
            ".github/pull_request_template.md",
        ]

        for rel in required_paths:
            with self.subTest(path=rel):
                self.assertTrue((ROOT / rel).is_file())

    def test_public_repo_does_not_commit_generated_example_outputs(self) -> None:
        generated_paths = [
            ROOT / "examples" / "worker-packets",
            ROOT / "examples" / "gate-reports",
        ]

        for path in generated_paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertFalse(path.exists())

        automation_doc = read_text("docs/automation/worker-automation-v0.md")
        self.assertIn("--out .tmp/worker-packets/onchain-card", automation_doc)
        self.assertNotIn("--out examples/worker-packets", automation_doc)

    def test_repository_shape_explains_every_public_top_level_folder(self) -> None:
        readme = read_text("README.md")
        expected_public_dirs = [
            ".github/",
            "adapters/",
            "agents/",
            "docs/",
            "examples/",
            "products/",
            "schemas/",
            "scripts/",
            "skills/",
            "templates/",
            "tests/",
        ]

        for rel in expected_public_dirs:
            with self.subTest(rel=rel):
                self.assertIn(f"`{rel}`", readme)

        self.assertIn("Generated worker packets and gate reports belong in `.tmp/`", readme)

    def test_high_noise_public_directories_have_entrypoint_guides(self) -> None:
        required_entrypoints = {
            "adapters/README.md": ["runtime integrations", "Hermes"],
            ".github/PROJECT_SURFACE.md": ["GitHub project surface", "Dependabot"],
            "agents/README.md": ["worker registry", "Hermes bindings"],
            "docs/README.md": ["human guides", "public onboarding"],
            "examples/README.md": ["source examples", ".tmp/"],
            "products/README.md": ["public validation products", "not production approval"],
            "schemas/README.md": ["machine contracts", "JSON Schema"],
            "scripts/README.md": ["CLI", "validation"],
            "skills/README.md": ["Codex skill", "public-safe"],
            "templates/README.md": ["templates", "schemas"],
            "tests/README.md": ["regression", "public path"],
        }

        for rel, expected_phrases in required_entrypoints.items():
            with self.subTest(path=rel):
                path = ROOT / rel
                self.assertTrue(path.is_file())
                text = read_text(rel)
                for heading in [
                    "## What Belongs Here",
                    "## What Does Not Belong Here",
                    "## Source Of Truth",
                    "## How It Is Validated",
                ]:
                    self.assertIn(heading, text)
                normalized = text.lower()
                for phrase in expected_phrases:
                    self.assertIn(phrase.lower(), normalized)

    def test_examples_readme_keeps_generated_outputs_out_of_repo(self) -> None:
        examples = read_text("examples/README.md")

        self.assertIn("Generated worker packets and gate reports belong in `.tmp/`", examples)
        self.assertIn("Do not commit generated run output", examples)
        self.assertIn("examples/minimal-hermes-project/", examples)

    def test_products_readme_sets_public_validation_boundary(self) -> None:
        products = read_text("products/README.md")

        self.assertIn("public validation products", products)
        self.assertIn("not production approval", products)
        self.assertIn("No private product material", products)

    def test_public_codex_skill_covers_open_source_stewardship(self) -> None:
        skill = read_text("skills/codex/overkill-factory/SKILL.md")
        open_source_ref = ROOT / "skills" / "codex" / "overkill-factory" / "references" / "open-source-github.md"
        documentation_ref = (
            ROOT
            / "skills"
            / "codex"
            / "overkill-factory"
            / "references"
            / "documentation-standard.md"
        )

        self.assertTrue(open_source_ref.is_file())
        self.assertTrue(documentation_ref.is_file())
        self.assertIn("professional open-source GitHub stewardship", skill)
        self.assertIn("Product Experience OS/Product Face", skill)
        self.assertIn("Use this vFinal sequence", skill)
        self.assertIn("references/open-source-github.md", skill)
        self.assertIn("references/documentation-standard.md", skill)
        self.assertIn("Every public folder needs a burden-of-proof decision", skill)

    def test_docs_site_navigation_and_maintenance_boundaries_exist(self) -> None:
        docs_index = read_text("docs/index.md")
        mkdocs = read_text("mkdocs.yml")
        cli = read_text("docs/reference/cli.md")
        repo_surface = read_text("docs/maintenance/repo-surface.md")

        for phrase in [
            "Operator Path",
            "Install In Your Hermes",
            "CLI Reference",
            "Examples",
            "Visuals",
            "Security",
            "Release",
            "Maintainer Internals",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, docs_index)
                self.assertIn(phrase, mkdocs)

        for command in ["factoryctl doctor", "factoryctl init", "factoryctl run minimal"]:
            with self.subTest(command=command):
                self.assertIn(command, cli)

        self.assertIn("Operator surface", repo_surface)
        self.assertIn("Maintainer internals", repo_surface)
        self.assertIn("Generated output", repo_surface)

    def test_visual_map_is_visible_without_becoming_source_authority(self) -> None:
        readme = read_text("README.md")
        visuals = read_text("docs/visuals/README.md")
        svg = read_text("docs/visuals/overkill-factory-map-v0.1.0.svg")
        html = read_text("docs/visuals/overkill-factory-map-v0.1.0.html")

        self.assertIn("![Overkill Factory visual map]", readme)
        self.assertIn("docs/visuals/overkill-factory-map-v0.1.0.svg", readme)
        self.assertIn("docs/visuals/overkill-factory-map-v0.1.0.html", readme)
        self.assertIn("onboarding aid, not runtime evidence or source authority", readme)
        self.assertIn("Static README preview", visuals)
        self.assertIn("Interactive map", visuals)
        self.assertIn("Readable GitHub README preview", svg)
        self.assertIn("Preview only", svg)
        self.assertIn("Open the interactive map", svg)
        self.assertIn("Overkill Factory", html)

    def test_release_security_and_example_gallery_are_professional_surfaces(self) -> None:
        changelog = read_text("CHANGELOG.md")
        release_policy = read_text("docs/operations/release-policy.md")
        oss_security = read_text("docs/security/oss-security.md")
        gallery = read_text("docs/examples/gallery.md")
        pyproject = read_text("pyproject.toml")

        self.assertIn("Unreleased", changelog)
        self.assertIn("semantic versioning", release_policy)
        self.assertIn("CodeQL", oss_security)
        self.assertIn("Dependency Review", oss_security)
        self.assertIn("SBOM", oss_security)
        self.assertIn("Point 5 is intentionally deferred", release_policy)
        for example in [
            "minimal-hermes-project",
            "v35_valid_product_face.md",
            "v35_valid_security_with_scan.md",
            "v35_valid_onchain_auditor_scan.md",
        ]:
            with self.subTest(example=example):
                self.assertIn(example, gallery)

        self.assertNotIn("OWNER", pyproject)

    def test_public_metadata_uses_live_repository_urls_and_explicit_license(self) -> None:
        pyproject = read_text("pyproject.toml")
        mkdocs = read_text("mkdocs.yml")
        license_text = read_text("LICENSE")
        owner = "feli" + "pegermano17"
        repo_url = f"https://github.com/{owner}/overkill-factory"

        dead_placeholder_domain = "overkill-factory.dev"
        self.assertNotIn(dead_placeholder_domain, pyproject)
        self.assertNotIn(dead_placeholder_domain, mkdocs)

        for expected in [
            f'Homepage = "{repo_url}"',
            f'Documentation = "{repo_url}/tree/main/docs"',
            f'Repository = "{repo_url}"',
            f'Issues = "{repo_url}/issues"',
            'license = "MIT"',
            'license-files = ["LICENSE"]',
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, pyproject)

        self.assertIn(f"repo_url: {repo_url}", mkdocs)
        self.assertTrue(license_text.startswith("MIT License"))
        self.assertIn("Permission is hereby granted", license_text)

    def test_agent_public_doc_covers_every_registered_worker(self) -> None:
        registry = json.loads(read_text("agents/worker-registry.public.json"))
        agent_doc = read_text("docs/agents/worker-profiles.md")
        registered_workers = [worker["worker_id"] for worker in registry["workers"]]

        for worker_id in registered_workers:
            with self.subTest(worker_id=worker_id):
                self.assertIn(f"`{worker_id}`", agent_doc)

        required_agent_topics = [
            "responsibility",
            "when it enters",
            "receives",
            "delivers",
            "must not",
            "evidence",
            "tooling",
            "coverage",
        ]
        normalized = agent_doc.lower()
        for topic in required_agent_topics:
            with self.subTest(topic=topic):
                self.assertIn(topic, normalized)

    def test_quickstart_and_operations_docs_include_runnable_validation_commands(self) -> None:
        quickstart = read_text("docs/getting-started/quickstart-hermes.md")
        operations = read_text("docs/operations/validation-and-release.md")
        combined = f"{quickstart}\n{operations}"
        required_commands = [
            "factoryctl doctor",
            "factoryctl run minimal",
            "python -m unittest discover -s tests",
            "python scripts/validate_document_governance.py",
            "python scripts/validate_public_json_artifacts.py",
            "python scripts/validate_worker_profiles.py",
            "python scripts/secret_safety_scan.py",
            "python scripts/public_safety_scan.py",
            "python scripts/supply_chain_proof.py --check --no-write",
            "python scripts/release_integration_preflight.py",
            "python scripts/factory_production_readiness.py",
            "python scripts/worktree_release_inventory.py",
            "factoryctl gate-report",
            "factoryctl worker-packet",
        ]

        for command in required_commands:
            with self.subTest(command=command):
                self.assertIn(command, combined)

    def test_minimal_example_is_public_safe_and_reproducible(self) -> None:
        example = read_text("examples/minimal-hermes-project/README.md")
        expected_flow = read_text("examples/minimal-hermes-project/expected-flow.md")
        receipt = json.loads(read_text("examples/minimal-hermes-project/expected-receipt-five.json"))

        for rel in ["input-paper.md", "expected-flow.md", "expected-receipt-five.json"]:
            with self.subTest(rel=rel):
                self.assertIn(rel, example)

        self.assertIn("Hermes", expected_flow)
        self.assertIn("Control Tower is optional", expected_flow)
        self.assertEqual(receipt["record_type"], "receipt_five_example")
        self.assertEqual(receipt["result"], "PASS")
        self.assertTrue(receipt["public_safe"])

    def test_minimal_example_gate_report_is_ready_for_worker_execution(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/factoryctl.py",
                "gate-report",
                "--card",
                "examples/minimal-hermes-project/card.md",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(result.stdout)

        self.assertEqual(report["gate_status"], "ready_for_worker_execution")
        self.assertEqual(report["blocked_workers"], [])
        self.assertIn("independent-reviewer", report["required_workers"])
        self.assertEqual(report["workers"]["independent-reviewer"]["status"], "requires_execution")

    def test_quickstart_smoke_writes_small_json_result(self) -> None:
        out = ROOT / ".tmp" / "test-quickstart-result.json"
        packets = ROOT / ".tmp" / "test-minimal-worker-packets"
        result = subprocess.run(
            [
                sys.executable,
                "scripts/quickstart_smoke.py",
                "--out",
                str(out),
                "--packets-out",
                str(packets),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(out.read_text(encoding="utf-8"))

        self.assertIn("PASS", result.stdout)
        self.assertEqual(payload["result"], "PASS")
        self.assertEqual(payload["card"], "examples/minimal-hermes-project/card.md")
        self.assertGreater(payload["worker_packet_count"], 0)

    def test_ci_uses_public_example_not_historical_pilot_evidence(self) -> None:
        workflow = read_text(".github/workflows/ci.yml")

        self.assertIn("examples/minimal-hermes-project/card.md", workflow)
        self.assertNotIn("pilots/quasar-vault-guard-test", workflow)
        self.assertNotIn(".tmp/factory-runs/cards/solana-quasar-r3.md", workflow)

    def test_document_governance_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_document_governance.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
