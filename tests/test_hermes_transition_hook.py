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

        self.assertEqual(first["transition_action"], "block_and_create_before_ready_tasks")
        self.assertTrue(any("result is required before ready" in reason for reason in first["blocked_reasons"]))
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

    def test_cli_is_fail_closed_for_before_ready_blocks(self) -> None:
        card = ROOT / "validation" / "cards" / "solana-quasar-r3.md"
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            argv = [
                "transition_hook.py",
                "--card",
                str(card),
                "--from-status",
                "draft",
                "--to-status",
                "ready",
                "--ledger",
                str(Path(tmp) / "worker-ledger.json"),
                "--out",
                str(Path(tmp) / "hook-result.json"),
            ]
            previous = sys.argv
            try:
                sys.argv = argv
                exit_code = transition_hook.main()
            finally:
                sys.argv = previous

        self.assertEqual(exit_code, 1)

    def test_cli_report_only_allows_blocked_result_for_ci_observation(self) -> None:
        card = ROOT / "validation" / "cards" / "solana-quasar-r3.md"
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            argv = [
                "transition_hook.py",
                "--card",
                str(card),
                "--from-status",
                "draft",
                "--to-status",
                "ready",
                "--ledger",
                str(Path(tmp) / "worker-ledger.json"),
                "--out",
                str(Path(tmp) / "hook-result.json"),
                "--report-only",
            ]
            previous = sys.argv
            try:
                sys.argv = argv
                exit_code = transition_hook.main()
            finally:
                sys.argv = previous

        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
