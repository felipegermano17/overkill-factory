from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "adapters" / "hermes" / "transition_hook.py"
SPEC = importlib.util.spec_from_file_location("transition_hook", MODULE_PATH)
assert SPEC is not None
transition_hook = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["transition_hook"] = transition_hook
SPEC.loader.exec_module(transition_hook)

SMOKE_PATH = ROOT / "adapters" / "hermes" / "vfinal-smoke.py"
SMOKE_SPEC = importlib.util.spec_from_file_location("vfinal_smoke", SMOKE_PATH)
assert SMOKE_SPEC is not None
vfinal_smoke = importlib.util.module_from_spec(SMOKE_SPEC)
assert SMOKE_SPEC.loader is not None
sys.modules["vfinal_smoke"] = vfinal_smoke
SMOKE_SPEC.loader.exec_module(vfinal_smoke)

DISPOSABLE_SMOKE_PATH = ROOT / "adapters" / "hermes" / "disposable_runtime_smoke.py"
DISPOSABLE_SMOKE_SPEC = importlib.util.spec_from_file_location("disposable_runtime_smoke", DISPOSABLE_SMOKE_PATH)
assert DISPOSABLE_SMOKE_SPEC is not None
disposable_runtime_smoke = importlib.util.module_from_spec(DISPOSABLE_SMOKE_SPEC)
assert DISPOSABLE_SMOKE_SPEC.loader is not None
sys.modules["disposable_runtime_smoke"] = disposable_runtime_smoke
DISPOSABLE_SMOKE_SPEC.loader.exec_module(disposable_runtime_smoke)


class HermesTransitionHookTest(unittest.TestCase):
    def test_ready_hook_persists_worker_tasks_idempotently(self) -> None:
        card = ROOT / "validation" / "cards" / "solana-quasar-r3.md"
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            ledger = Path(tmp) / "worker-ledger.json"
            first = transition_hook.build_hook_result(
                card_path=card,
                from_status="draft",
                to_status="ready",
                receipt_path=None,
                worker_results_dir=None,
                ledger_path=ledger,
            )
            second = transition_hook.build_hook_result(
                card_path=card,
                from_status="draft",
                to_status="ready",
                receipt_path=None,
                worker_results_dir=None,
                ledger_path=ledger,
            )
            ledger_data = json.loads(ledger.read_text(encoding="utf-8"))

        self.assertEqual(first["transition_action"], "allow_and_create_worker_tasks")
        self.assertGreater(first["ledger"]["created"], [])
        self.assertEqual(second["ledger"]["created"], [])
        self.assertEqual(first["ledger"]["task_count"], second["ledger"]["task_count"])
        self.assertEqual(len(ledger_data["tasks"]), first["ledger"]["task_count"])

    def test_done_hook_blocks_missing_worker_results(self) -> None:
        card = ROOT / "validation" / "cards" / "solana-quasar-r3.md"
        receipt = ROOT / "pilots" / "quasar-vault-guard-test" / "evidence" / "receipt-five-first-slice.json"
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            result = transition_hook.build_hook_result(
                card_path=card,
                from_status="ready",
                to_status="done",
                receipt_path=receipt,
                worker_results_dir=ROOT / "pilots" / "quasar-vault-guard-test" / "worker-results",
                ledger_path=Path(tmp) / "worker-ledger.json",
            )

        self.assertEqual(result["transition_action"], "block_transition")
        self.assertTrue(any("result is required before done" in reason for reason in result["blocked_reasons"]))

    def test_vfinal_ready_hook_persists_vfinal_workers(self) -> None:
        card = ROOT / "validation" / "cards" / "vfinal-r3-ready.md"
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            result = transition_hook.build_hook_result(
                card_path=card,
                from_status="draft",
                to_status="ready",
                receipt_path=None,
                worker_results_dir=None,
                ledger_path=Path(tmp) / "worker-ledger.json",
            )

        worker_ids = {task["worker_id"] for task in result["plan"]["worker_tasks"]}
        self.assertEqual(result["transition_action"], "allow_and_create_worker_tasks")
        self.assertIn("security-architect-worker", worker_ids)
        self.assertIn("access-capability-worker", worker_ids)
        self.assertIn("factory-maturity-auditor", worker_ids)

    def test_vfinal_blocked_hook_reports_security_and_access_reasons(self) -> None:
        card = ROOT / "validation" / "cards" / "vfinal-r3-missing-security-access.md"
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            result = transition_hook.build_hook_result(
                card_path=card,
                from_status="draft",
                to_status="ready",
                receipt_path=None,
                worker_results_dir=None,
                ledger_path=Path(tmp) / "worker-ledger.json",
            )

        self.assertEqual(result["transition_action"], "block_transition")
        self.assertTrue(any("security_architecture_plan required" in reason for reason in result["blocked_reasons"]))
        self.assertTrue(any("access_capability required" in reason for reason in result["blocked_reasons"]))
        self.assertTrue(any("autonomy_readiness_packet required" in reason for reason in result["blocked_reasons"]))

    def test_vfinal_smoke_passes(self) -> None:
        receipt = vfinal_smoke.run_smoke()

        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["ready_transition_action"], "allow_and_create_worker_tasks")
        self.assertEqual(receipt["blocked_transition_action"], "block_transition")
        self.assertEqual(receipt["bridge_transition_action"], "allow_and_create_worker_tasks")
        self.assertFalse(receipt["bridge_worker_spawned"])
        self.assertEqual(receipt["missing_ready_workers"], [])
        self.assertEqual(receipt["missing_block_reasons"], [])

    def test_disposable_runtime_smoke_passes(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            receipt = disposable_runtime_smoke.run_smoke(Path(tmp))

        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["ready_transition_action"], "allow_and_create_worker_tasks")
        self.assertEqual(receipt["ready_retry_created"], [])
        self.assertEqual(receipt["done_missing_transition_action"], "block_transition")
        self.assertEqual(receipt["done_satisfied_transition_action"], "allow_done")
        self.assertEqual(receipt["bridge_ready_transition_action"], "allow_and_create_worker_tasks")
        self.assertEqual(receipt["bridge_done_transition_action"], "allow_done")
        self.assertIn("factory-concierge", receipt["control_tower_blocked_workers"])
        self.assertIn("discord-control-tower-bridge", receipt["control_tower_blocked_workers"])
        self.assertIn("control-tower-projection-worker", receipt["control_tower_blocked_workers"])
        self.assertEqual(receipt["failures"], [])


if __name__ == "__main__":
    unittest.main()
