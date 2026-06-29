from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "hermes_update_guard.py"
SPEC = importlib.util.spec_from_file_location("hermes_update_guard", MODULE_PATH)
assert SPEC is not None
guard = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["hermes_update_guard"] = guard
SPEC.loader.exec_module(guard)


class HermesUpdateGuardTest(unittest.TestCase):
    def test_running_kanban_tasks_block_gateway_restart(self) -> None:
        receipt = guard.evaluate_snapshot(
            gateway_status_text="Installed gateway service definition is outdated\nSystem gateway service is running\n",
            kanban_stats_text="By status:\n  running   2\n  blocked   1\n",
        )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("kanban_running_tasks_present", receipt["blocking_items"])
        self.assertIn("gateway_service_definition_outdated", receipt["attention_items"])
        self.assertFalse(receipt["checks"]["no_kanban_running_tasks"])

    def test_outdated_gateway_without_running_tasks_requires_operator_action(self) -> None:
        receipt = guard.evaluate_snapshot(
            doctor_text="Config version outdated (v29 -> v30)",
            gateway_status_text="Installed gateway service definition is outdated\nSystem gateway service is running\n",
            kanban_stats_text="By status:\n  running   0\n  todo      2\n",
            sudo_check_text="sudo-needs-password\nsudo: a password is required\n",
            board="factory-board",
        )

        self.assertEqual(receipt["result"], "ATTENTION")
        self.assertEqual(receipt["blocking_items"], [])
        self.assertIn("hermes_config_version_outdated", receipt["attention_items"])
        self.assertIn("gateway_service_definition_outdated", receipt["attention_items"])
        self.assertIn("operator_sudo_required", receipt["attention_items"])
        self.assertTrue(any("sudo" in action for action in receipt["next_required_actions"]))
        self.assertTrue(
            any("kanban --board factory-board stats" in command for command in receipt["command_plan"]["pre_update_readonly"])
        )

    def test_update_process_blocks_mutating_actions(self) -> None:
        receipt = guard.evaluate_snapshot(
            process_text="hermes update\n",
            kanban_stats_text="By status:\n  running   0\n",
        )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("hermes_update_process_still_running", receipt["blocking_items"])

    def test_clean_snapshot_passes_and_points_to_validation(self) -> None:
        receipt = guard.evaluate_snapshot(
            doctor_text="Python Environment\nVersion files consistent (0.17.0)",
            gateway_status_text="System gateway service is running",
            kanban_stats_text="By status:\n  running   0\n",
        )

        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["blocking_items"], [])
        self.assertEqual(receipt["attention_items"], [])
        self.assertIn("python adapters/hermes/compatibility-check.py", receipt["command_plan"]["factory_validation"])

    def test_cli_writes_receipt_and_returns_nonzero_only_when_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stats = root / "stats.txt"
            out = root / "receipt.json"
            stats.write_text("By status:\n  running   1\n", encoding="utf-8")

            exit_code = guard.main(["evaluate", "--kanban-stats", str(stats), "--out", str(out)])
            payload = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["result"], "BLOCKED")
        self.assertIn("kanban_running_tasks_present", payload["blocking_items"])


if __name__ == "__main__":
    unittest.main()
