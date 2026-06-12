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
            "Who It Is For",
            "What It Does",
            "What It Does Not Do",
            "How Hermes Fits",
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
            "docs/agents/worker-profiles.md",
            "agents/README.md",
            "docs/agents/factory-stage-agent-map.md",
            "docs/agents/capability-packs.md",
            "docs/control-tower/open-source-setup.md",
            "docs/operations/validation-and-release.md",
            "docs/architecture/hermes-integration.md",
            "examples/minimal-hermes-project/README.md",
            ".env.example",
            "CONTRIBUTING.md",
            "SECURITY.md",
        ]:
            with self.subTest(link=rel):
                self.assertIn(rel.replace("\\", "/"), readme)

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
            "docs/operations/troubleshooting.md",
            "docs/architecture/hermes-integration.md",
            "examples/minimal-hermes-project/README.md",
            "examples/minimal-hermes-project/input-paper.md",
            "examples/minimal-hermes-project/expected-flow.md",
            "examples/minimal-hermes-project/expected-receipt-five.json",
            ".env.example",
            "pyproject.toml",
            "CONTRIBUTING.md",
            "SECURITY.md",
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

    def test_public_codex_skill_covers_open_source_stewardship(self) -> None:
        skill = read_text("skills/codex/overkill-factory/SKILL.md")
        open_source_ref = ROOT / "skills" / "codex" / "overkill-factory" / "references" / "open-source-github.md"

        self.assertTrue(open_source_ref.is_file())
        self.assertIn("professional open-source GitHub stewardship", skill)
        self.assertIn("references/open-source-github.md", skill)

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
            "python scripts/quickstart_smoke.py",
            "python -m unittest discover -s tests",
            "python scripts/validate_document_governance.py",
            "python scripts/validate_public_json_artifacts.py",
            "python scripts/secret_safety_scan.py",
            "python scripts/public_safety_scan.py",
            "python scripts/release_integration_preflight.py",
            "python scripts/factory_production_readiness.py",
            "python scripts/worktree_release_inventory.py",
            "python scripts/factoryctl.py gate-report",
            "python scripts/factoryctl.py worker-packet",
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
