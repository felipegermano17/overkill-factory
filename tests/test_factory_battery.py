from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import factory_battery


class FactoryBatteryTest(unittest.TestCase):
    def test_solana_bank_r4_scenarios_cover_start_and_implementation_gates(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            result = factory_battery.run_battery(Path(tmp))

        scenarios = {item["name"]: item for item in result["scenarios"]}
        architecture = scenarios["solana-bank-r4-architecture"]
        implementation = scenarios["solana-bank-r4-implementation-blocked-without-product-face-result"]

        self.assertEqual(result["failed_count"], 0)
        self.assertTrue(architecture["passed"], architecture)
        self.assertEqual(architecture["observed"]["gate_status"], "ready_for_worker_execution")
        for worker in (
            "codex-security",
            "solana-quasar-auditor",
            "human-gate-clerk",
            "crypto-key-management-specialist",
            "remote-proof-runner",
            "release-ops-worker",
            "supply-chain-gate",
        ):
            self.assertIn(worker, architecture["observed"]["required_workers"])

        self.assertTrue(implementation["passed"], implementation)
        self.assertEqual(implementation["observed"]["gate_status"], "blocked")
        self.assertIn(
            "product_face_result or product_face_result_ref required before decomposition/release",
            implementation["observed"]["blocked_reasons"],
        )
        for worker in (
            "frontend-builder",
            "solana-quasar-builder",
            "solana-quasar-qa-engineer",
            "wallet-transaction-builder",
            "remote-proof-runner",
        ):
            self.assertIn(worker, implementation["observed"]["required_workers"])


if __name__ == "__main__":
    unittest.main()
