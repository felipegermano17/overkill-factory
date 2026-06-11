from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FactoryStageAgentMapTest(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = json.loads(
            (ROOT / "agents" / "worker-registry.public.json").read_text(encoding="utf-8")
        )
        self.stage_map = (ROOT / "docs" / "agents" / "factory-stage-agent-map.md").read_text(
            encoding="utf-8"
        )

    def test_stage_map_names_every_canonical_stage(self) -> None:
        for stage_number in range(1, 33):
            with self.subTest(stage=stage_number):
                self.assertRegex(self.stage_map, rf"\|\s*{stage_number}\.")

    def test_stage_map_worker_refs_are_registered_or_explicitly_non_worker_roles(self) -> None:
        registered = {worker["worker_id"] for worker in self.registry["workers"]}
        allowed_non_workers = {
            "Factory Concierge",
            "factory-critic",
            "overkill-factory-gerente",
        }
        worker_refs = {
            ref
            for ref in re.findall(r"`([^`]+)`", self.stage_map)
            if "/" not in ref and "." not in ref
        }

        for ref in sorted(worker_refs):
            if ref in allowed_non_workers:
                continue
            with self.subTest(ref=ref):
                self.assertIn(ref, registered)

    def test_key_stage_owners_are_not_left_generic(self) -> None:
        required_pairs = {
            "6. Agentic Method Router": "`factory-orchestrator`",
            "8. Product Pack & Surface Pack": "`factory-orchestrator`",
            "13. Data, Metrics & Analytics Plan": "`detection-monitoring-worker`",
            "14. Agent Quality & Evals Plan": "`skill-eval-distiller`",
            "27. Completion Audit": "`evidence-reconciler`",
            "32. Factory Maturity Audit": "`skill-eval-distiller`",
        }

        for stage, worker in required_pairs.items():
            with self.subTest(stage=stage):
                line = next(line for line in self.stage_map.splitlines() if stage in line)
                self.assertIn(worker, line)


if __name__ == "__main__":
    unittest.main()
