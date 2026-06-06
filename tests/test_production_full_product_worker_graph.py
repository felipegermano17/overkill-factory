from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "production_full_product_worker_graph.py"
SPEC = importlib.util.spec_from_file_location("production_full_product_worker_graph", SCRIPT)
assert SPEC is not None
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["production_full_product_worker_graph"] = module
SPEC.loader.exec_module(module)


class ProductionFullProductWorkerGraphTest(unittest.TestCase):
    def test_current_graph_stays_blocked_until_production_lanes_exist(self) -> None:
        graph = module.build_graph()
        blockers = "\n".join(graph["blocking_summary"])

        self.assertEqual(graph["result"], "FAIL")
        self.assertFalse(graph["reusable_for_product"])
        self.assertIn("remote_proof", blockers)
        self.assertIn("human_gate", blockers)
        self.assertIn("release_ops", blockers)

    def test_strict_lane_requires_reusable_product_target(self) -> None:
        lane = {
            "lane_id": "remote_proof",
            "worker_id": "remote-proof-runner",
            "path": "validation/remote-proof/crabbox-static-ssh-proof-2026-06-06.json",
            "record_type": "remote_proof_result",
            "reusable_policy": "strict",
        }

        result = module.validate_lane(lane)

        self.assertEqual(result["status"], "FAIL")
        self.assertIn("strict lane must be reusable", " ".join(result["validation_errors"]))


if __name__ == "__main__":
    unittest.main()
