from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "production_release_gate.py"
SPEC = importlib.util.spec_from_file_location("production_release_gate", SCRIPT)
assert SPEC is not None
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["production_release_gate"] = module
SPEC.loader.exec_module(module)


class ProductionReleaseGateTest(unittest.TestCase):
    def test_human_gate_is_product_scoped_and_public_safe(self) -> None:
        gate = module.build_human_gate(
            approval_ref="external:redacted-maintainer-authorization",
            approved_by="project-maintainer",
            created_at="2026-06-06T00:00:00+00:00",
        )

        self.assertEqual(gate["record_type"], "human_gate_record")
        self.assertTrue(gate["reusable_for_product"])
        self.assertEqual(gate["human_actor"], "project-maintainer")
        self.assertIn("public repository", " ".join(gate["approved_scope"]).lower())
        self.assertNotIn("KAXIS", str(gate))

    def test_release_ops_fails_when_any_validation_command_fails(self) -> None:
        validation = [
            {"command": "ok", "exit_code": 0},
            {"command": "bad", "exit_code": 1},
        ]
        with mock.patch.object(module, "git_value", return_value="git-value"):
            result = module.build_release_ops(created_at="2026-06-06T00:00:00+00:00", validation=validation)

        self.assertEqual(result["result"], "FAIL")
        self.assertFalse(result["reusable_for_product"])

    def test_release_ops_passes_with_validation_and_rollback_plan(self) -> None:
        validation = [{"command": "ok", "exit_code": 0}]
        with mock.patch.object(module, "git_value", return_value="git-value"):
            result = module.build_release_ops(created_at="2026-06-06T00:00:00+00:00", validation=validation)

        self.assertEqual(result["result"], "PASS")
        self.assertTrue(result["reusable_for_product"])
        self.assertIn("git revert", result["rollback_plan"]["rollback_command"])


if __name__ == "__main__":
    unittest.main()
