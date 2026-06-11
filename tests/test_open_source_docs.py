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
            "Current Status",
            "Documentation Map",
        ]

        for heading in required_headings:
            with self.subTest(heading=heading):
                self.assertIn(f"## {heading}", readme)

        for rel in [
            "docs/getting-started/quickstart-hermes.md",
            "docs/concepts/factory-flow.md",
            "docs/agents/worker-profiles.md",
            "docs/agents/factory-stage-agent-map.md",
            "docs/agents/capability-packs.md",
            "docs/control-tower/open-source-setup.md",
            "docs/operations/validation-and-release.md",
            "docs/architecture/hermes-integration.md",
            "docs/roadmap/factory-vfinal-prepilot-roadmap.md",
            "examples/minimal-hermes-project/README.md",
            ".env.example",
        ]:
            with self.subTest(link=rel):
                self.assertIn(rel.replace("\\", "/"), readme)

    def test_public_docs_skeleton_exists(self) -> None:
        required_paths = [
            "docs/getting-started/quickstart-hermes.md",
            "docs/concepts/factory-flow.md",
            "docs/agents/worker-profiles.md",
            "docs/agents/factory-stage-agent-map.md",
            "docs/agents/capability-packs.md",
            "docs/control-tower/open-source-setup.md",
            "docs/operations/validation-and-release.md",
            "docs/operations/troubleshooting.md",
            "docs/architecture/hermes-integration.md",
            "docs/roadmap/factory-vfinal-prepilot-roadmap.md",
            "examples/minimal-hermes-project/README.md",
            "examples/minimal-hermes-project/input-paper.md",
            "examples/minimal-hermes-project/expected-flow.md",
            "examples/minimal-hermes-project/expected-receipt-five.json",
            ".env.example",
        ]

        for rel in required_paths:
            with self.subTest(path=rel):
                self.assertTrue((ROOT / rel).is_file())

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
            "python -m unittest discover -s tests",
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


if __name__ == "__main__":
    unittest.main()
