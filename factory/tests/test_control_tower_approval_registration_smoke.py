from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "control_tower_approval_registration_smoke.py"
SPEC = importlib.util.spec_from_file_location("control_tower_approval_registration_smoke", MODULE_PATH)
assert SPEC is not None
control_tower_approval_registration_smoke = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["control_tower_approval_registration_smoke"] = control_tower_approval_registration_smoke
SPEC.loader.exec_module(control_tower_approval_registration_smoke)


class ControlTowerApprovalRegistrationSmokeTest(unittest.TestCase):
    def test_valid_structured_approval_and_negative_cases(self) -> None:
        receipt = control_tower_approval_registration_smoke.build_receipt("2026-06-10T00:00:00Z")

        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["registered_approval"]["status"], "approved")
        self.assertEqual(receipt["approval_event"]["event_type"], "approval_recorded")
        for value in receipt["registration_checks"].values():
            self.assertTrue(value)
        self.assertTrue(all(not case["accepted"] for case in receipt["negative_cases"]))


if __name__ == "__main__":
    unittest.main()
