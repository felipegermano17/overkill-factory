from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class AgentDirectoryDocsTest(unittest.TestCase):
    def test_agent_directory_has_human_entrypoint(self) -> None:
        readme = read_text("agents/README.md")
        required_refs = [
            "agents/worker-roster.md",
            "agents/critical-workers/README.md",
            "docs/agents/worker-profiles.md",
            "docs/agents/factory-stage-agent-map.md",
            "agents/worker-registry.public.json",
            "agents/worker-profiles.public.json",
            "agents/hermes-profile-bindings.public.json",
            "agents/worker-permission-classes.public.json",
            "agents/capability-packs.public.json",
            "scripts/factoryctl.py",
        ]

        for ref in required_refs:
            with self.subTest(ref=ref):
                self.assertIn(ref, readme)

        for phrase in [
            "Worker Operability Rule",
            "Quality Bar",
            "Anti-Theater Rules",
            "Validation",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)

    def test_critical_worker_cards_have_operational_shape(self) -> None:
        critical_dir = ROOT / "agents" / "critical-workers"
        cards = sorted(path for path in critical_dir.glob("*.md") if path.name != "README.md")
        expected_cards = {
            "codex-security-runner.md",
            "evidence-reconciler.md",
            "factory-orchestrator.md",
            "human-gate-clerk.md",
            "independent-reviewer.md",
            "product-face-validator.md",
            "product-sot-planner.md",
            "public-safety-gate.md",
            "release-ops-worker.md",
            "security-orchestrator.md",
            "solana-quasar-auditor-runner.md",
            "source-ledger-worker.md",
        }

        self.assertEqual({path.name for path in cards}, expected_cards)

        required_headings = [
            "Runtime Identity",
            "When It Enters",
            "Required Inputs",
            "Required Result",
            "Blocking Rule",
            "Refusal Rule",
            "Evidence Quality",
            "Handoff",
        ]
        for path in cards:
            text = path.read_text(encoding="utf-8")
            with self.subTest(card=path.name):
                for heading in required_headings:
                    self.assertIn(f"## {heading}", text)

    def test_critical_cards_reference_registered_workers(self) -> None:
        registry = json.loads(read_text("agents/worker-registry.public.json"))
        registered = {worker["worker_id"] for worker in registry["workers"]}
        critical_readme = read_text("agents/critical-workers/README.md")

        for worker_id in [
            "factory-orchestrator",
            "source-ledger-worker",
            "product-sot-planner",
            "product-face",
            "security-orchestrator",
            "codex-security",
            "solana-quasar-auditor",
            "independent-reviewer",
            "human-gate-clerk",
            "evidence-reconciler",
            "release-ops-worker",
            "public-safety-gate",
        ]:
            with self.subTest(worker_id=worker_id):
                self.assertIn(worker_id, registered)
                self.assertIn(f"`{worker_id}`", critical_readme)


if __name__ == "__main__":
    unittest.main()
