from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "control_tower_readonly_smoke.py"
SPEC = importlib.util.spec_from_file_location("control_tower_readonly_smoke", MODULE_PATH)
assert SPEC is not None
control_tower_readonly_smoke = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["control_tower_readonly_smoke"] = control_tower_readonly_smoke
SPEC.loader.exec_module(control_tower_readonly_smoke)


class ControlTowerReadOnlySmokeTest(unittest.TestCase):
    def test_smoke_receipt_is_readonly_and_schema_valid(self) -> None:
        receipt = control_tower_readonly_smoke.build_receipt("2026-06-10T00:00:00Z")

        self.assertEqual(receipt["result"], "PASS")
        self.assertTrue(receipt["readonly_checks"]["runtime_snapshot_unchanged"])
        self.assertTrue(receipt["readonly_checks"]["projection_derived_from_runtime"])
        self.assertTrue(receipt["readonly_checks"]["approval_pending_only"])
        self.assertTrue(receipt["readonly_checks"]["mapping_redacted"])
        self.assertEqual(receipt["projection"]["status"], "waiting_access")
        self.assertEqual(receipt["projection"]["completion_percent"], 35)
        self.assertEqual(receipt["projection"]["projection_freshness"], "runtime_fresh")
        self.assertEqual(receipt["projection"]["next_action"], "grant required access and record the approval in runtime")
        stage_statuses = {stage["name"]: stage["status"] for stage in receipt["projection"]["pipeline_stages"]}
        self.assertEqual(stage_statuses["Metodo/planejamento"], "current")
        self.assertEqual(stage_statuses["Acessos/gates"], "blocked")
        self.assertEqual(receipt["event"]["event_type"], "access_missing")
        self.assertEqual(receipt["approval_request"]["status"], "pending")


if __name__ == "__main__":
    unittest.main()
