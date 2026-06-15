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
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
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
        self.assertEqual(ledger_data["ledger_scope"], "projection_idempotency_only")
        self.assertEqual(ledger_data["runtime_authority"], "hermes_kanban")
        self.assertFalse(ledger_data["local_state_authority"])
        self.assertEqual(len(ledger_data["tasks"]), first["ledger"]["task_count"])
        task = next(iter(ledger_data["tasks"].values()))
        self.assertEqual(task["materialization_state"], "pending_hermes_materialization")
        self.assertEqual(task["local_record_role"], "idempotency_projection")
        self.assertIn("runtime_refs", task)
        self.assertIn("hermes_task_ref", task["runtime_refs"])

    def test_done_hook_blocks_missing_worker_results(self) -> None:
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        receipt = ROOT / "examples" / "minimal-hermes-project" / "expected-receipt-five.json"
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            result = transition_hook.build_hook_result(
                card_path=card,
                from_status="ready",
                to_status="done",
                receipt_path=receipt,
                worker_results_dir=None,
                ledger_path=Path(tmp) / "worker-ledger.json",
            )

        self.assertEqual(result["transition_action"], "block_transition")
        self.assertTrue(any("result is required before done" in reason for reason in result["blocked_reasons"]))

    def test_hook_persists_declared_graph_review_requirements(self) -> None:
        factoryctl = transition_hook.load_factoryctl()
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card_data = factoryctl.load_json_like(card)
        handoff = factoryctl.build_worker_result(
            "handoff-packer",
            card_data,
            result="PASS",
            tool_or_profile="handoff-pack-smoke",
            executed_by="handoff-packer",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Handoff packet declares an independent review gate.",
            next_action="independent review required before implementation consumption",
            reviewer_required=True,
            reviewer_result="PENDING",
        )

        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            receipt = tmp_path / "receipt.json"
            ledger = tmp_path / "worker-ledger.json"
            receipt.write_text(json.dumps({"handoff_packet_result": handoff}), encoding="utf-8")

            result = transition_hook.build_hook_result(
                card_path=card,
                from_status="draft",
                to_status="ready",
                receipt_path=receipt,
                worker_results_dir=None,
                ledger_path=ledger,
            )
            ledger_data = json.loads(ledger.read_text(encoding="utf-8"))

        requirement = result["plan"]["graph_requirements"][0]
        self.assertEqual(requirement["status"], "pending")
        self.assertIn(requirement["requirement_id"], ledger_data["graph_requirements"])
        self.assertEqual(
            ledger_data["graph_requirements"][requirement["requirement_id"]]["materialization_state"],
            "pending_hermes_materialization",
        )
        self.assertTrue(
            any(
                requirement["requirement_id"] in task.get("graph_requirement_refs", [])
                for task in ledger_data["tasks"].values()
            )
        )

    def test_hook_persists_review_ready_authorizations(self) -> None:
        factoryctl = transition_hook.load_factoryctl()
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card_data = factoryctl.load_json_like(card)
        handoff = factoryctl.build_worker_result(
            "handoff-packer",
            card_data,
            result="PASS",
            tool_or_profile="handoff-pack-smoke",
            executed_by="handoff-packer",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Handoff packet declares an independent review gate.",
            next_action="independent review required before implementation consumption",
            reviewer_required=True,
            reviewer_result="PENDING",
        )
        receipt_payload = {
            "handoff_packet_result": handoff,
            "orchestration_result": factoryctl.build_worker_result(
                "factory-orchestrator",
                card_data,
                result="PASS",
                tool_or_profile="orchestration-smoke",
                executed_by="factory-orchestrator",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Orchestration precondition passed.",
                next_action="continue",
            ),
            "source_ledger_result": factoryctl.build_worker_result(
                "source-ledger-worker",
                card_data,
                result="PASS",
                tool_or_profile="source-ledger-smoke",
                executed_by="source-ledger-worker",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Source ledger precondition passed.",
                next_action="continue",
            ),
            "security_orchestration_result": factoryctl.build_worker_result(
                "security-orchestrator",
                card_data,
                result="PASS",
                tool_or_profile="security-orchestration-smoke",
                executed_by="security-orchestrator",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Security orchestration precondition passed.",
                next_action="continue",
            ),
            "supply_chain_result": factoryctl.build_worker_result(
                "supply-chain-gate",
                card_data,
                result="PASS",
                tool_or_profile="supply-chain-smoke",
                executed_by="supply-chain-gate",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Supply chain precondition passed.",
                next_action="continue",
            ),
        }

        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            receipt = tmp_path / "receipt.json"
            ledger = tmp_path / "worker-ledger.json"
            receipt.write_text(json.dumps(receipt_payload), encoding="utf-8")

            result = transition_hook.build_hook_result(
                card_path=card,
                from_status="doing",
                to_status="implementation-ready-for-review",
                receipt_path=receipt,
                worker_results_dir=None,
                ledger_path=ledger,
            )
            ledger_data = json.loads(ledger.read_text(encoding="utf-8"))

        self.assertEqual(result["transition_action"], "allow_review_ready")
        self.assertEqual(result["blocked_reasons"], [])
        self.assertTrue(ledger_data["review_task_authorizations"])
        task = next(task for task in ledger_data["tasks"].values() if task["worker_id"] == "independent-reviewer")
        self.assertEqual(task["dependency_authorization_state"], "review_ready")
        self.assertEqual(task["review_task_authorizations"][0]["authorized_scope"], ["review"])

    def test_cli_is_fail_closed_for_before_ready_blocks(self) -> None:
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
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
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
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
