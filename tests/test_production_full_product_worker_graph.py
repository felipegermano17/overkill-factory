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
    def test_current_graph_matches_available_production_lanes(self) -> None:
        graph = module.build_graph()
        all_lane_files_exist = all((ROOT / lane["path"]).exists() for lane in module.LANES)

        if all_lane_files_exist:
            self.assertEqual(graph["result"], "FAIL")
            self.assertFalse(graph["reusable_for_product"])
            self.assertTrue(any(item.startswith("product_face:") for item in graph["blocking_summary"]))
        else:
            self.assertEqual(graph["result"], "FAIL")
            self.assertFalse(graph["reusable_for_product"])
            self.assertGreater(len(graph["blocking_summary"]), 0)

    def test_strict_lane_requires_reusable_product_target(self) -> None:
        lane = {
            "lane_id": "remote_proof",
            "worker_id": "remote-proof-runner",
            "path": "validation/remote-proof/crabbox-static-ssh-proof-2026-06-06.json",
            "record_type": "remote_proof_result",
            "scope": "supporting",
            "reusable_policy": "strict",
        }

        result = module.validate_lane(lane)

        self.assertEqual(result["status"], "FAIL")
        self.assertIn("strict lane must be reusable", " ".join(result["validation_errors"]))


if __name__ == "__main__":
    unittest.main()
