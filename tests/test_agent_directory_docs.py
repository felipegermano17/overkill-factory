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
            "docs/agents/worker-profiles.md",
            "docs/agents/factory-stage-agent-map.md",
            "docs/agents/capability-packs.md",
            "docs/agents/permission-model.md",
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

        self.assertNotIn("agents/critical-workers", readme)
        self.assertNotIn("critical-workers/README.md", readme)

        for phrase in [
            "Worker Operability Rule",
            "Quality Bar",
            "Anti-Theater Rules",
            "Validation",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)

    def test_agent_directory_does_not_keep_partial_worker_mirrors(self) -> None:
        self.assertFalse((ROOT / "agents" / "critical-workers").exists())
        readme = read_text("agents/README.md")
        self.assertIn("Do not add hand-written per-worker mirrors", readme)

    def test_worker_roster_references_every_registered_worker(self) -> None:
        registry = json.loads(read_text("agents/worker-registry.public.json"))
        registered = {worker["worker_id"] for worker in registry["workers"]}
        roster = read_text("agents/worker-roster.md")

        for worker_id in sorted(registered):
            with self.subTest(worker_id=worker_id):
                self.assertIn(f"`{worker_id}`", roster)


if __name__ == "__main__":
    unittest.main()
