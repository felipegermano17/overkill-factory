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


def solana_ai_kit_usage_receipt() -> dict:
    return {
        "provider_id": "solana-ai-kit",
        "source": "https://github.com/solanabr/solana-ai-kit",
        "pinned_ref": "v2.0.2",
        "loaded": True,
        "loaded_components": ["agents", "skills", "commands"],
        "evidence_refs": ["README.md"],
    }


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
        receipt_payload["security_orchestration_result"]["solana_ai_kit_usage_receipt"] = solana_ai_kit_usage_receipt()

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

    def test_hook_persists_recovery_routes_from_blocked_review_results(self) -> None:
        factoryctl = transition_hook.load_factoryctl()
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card_data = factoryctl.load_json_like(card)
        card_data["source_refs"] = [*card_data.get("source_refs", []), "synthetic validation fixture"]
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
            results_dir = tmp_path / "worker-results"
            results_dir.mkdir()
            handoff_path = results_dir / "handoff.json"
            review_path = results_dir / "review.json"
            ledger = tmp_path / "worker-ledger.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            requirement = factoryctl.declared_graph_requirements(
                "handoff_packet_result",
                handoff,
                evidence_ref=factoryctl.source_card_ref(handoff_path),
            )[0]
            blocked_review = factoryctl.build_worker_result(
                "independent-reviewer",
                card_data,
                result="BLOCKED",
                tool_or_profile="independent-review-smoke",
                executed_by="independent-reviewer",
                evidence_refs=["README.md"],
                blocking_findings=True,
                findings_summary="Review found the handoff packet incomplete.",
                next_action="repair handoff packet and rerun independent review",
                reusable_for_product=False,
            )
            blocked_review["graph_requirement_refs"] = [requirement["requirement_id"]]
            review_path.write_text(json.dumps(blocked_review), encoding="utf-8")

            result = transition_hook.build_hook_result(
                card_path=card,
                from_status="draft",
                to_status="ready",
                receipt_path=None,
                worker_results_dir=results_dir,
                ledger_path=ledger,
            )
            ledger_data = json.loads(ledger.read_text(encoding="utf-8"))

        self.assertTrue(result["plan"]["recovery_routes"])
        route_id = result["plan"]["recovery_routes"][0]["recovery_route_id"]
        task = next(task for task in ledger_data["tasks"].values() if task["worker_id"] == "handoff-packer")
        self.assertIn(route_id, task["recovery_route_refs"])
        self.assertIn(route_id, task["packet"]["input_contract"]["recovery_route_refs"])

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

    def test_hook_can_emit_operator_bridge_event_without_gate_authority(self) -> None:
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            inbox = tmp_path / "operator-inbox"
            result = transition_hook.build_hook_result(
                card_path=card,
                from_status="draft",
                to_status="ready",
                receipt_path=None,
                worker_results_dir=None,
                ledger_path=tmp_path / "worker-ledger.json",
                operator_inbox_dir=inbox,
                operator_run_id="run-alpha",
            )
            events = [json.loads(line) for line in (inbox / "events.jsonl").read_text(encoding="utf-8").splitlines()]

        self.assertEqual(result["operator_bridge"]["inbox_ref"], "external:operator:inbox")
        self.assertEqual(result["operator_bridge"]["event_type"], "transition_blocked")
        self.assertFalse(result["operator_bridge"]["factory_authority"]["can_close_gate"])
        self.assertFalse(result["operator_bridge"]["factory_authority"]["can_execute_factory_work"])
        self.assertEqual(events[0]["event_type"], "transition_blocked")
        self.assertEqual(events[0]["source"], "hermes_transition_hook")
        self.assertFalse(events[0]["requires_user"])
        self.assertEqual(events[0]["payload"]["block_kind"], "transient")

    def test_transition_hook_dependency_block_does_not_require_user(self) -> None:
        event_type, severity, requires_user, block_kind = transition_hook.operator_event_type_for_action(
            "block_transition",
            ["dependency parent is not complete"],
        )

        self.assertEqual(event_type, "transition_blocked")
        self.assertEqual(severity, "warning")
        self.assertFalse(requires_user)
        self.assertEqual(block_kind, "dependency")

    def test_transition_hook_human_gate_text_does_not_page_user_without_structured_block_kind(self) -> None:
        event_type, severity, requires_user, block_kind = transition_hook.operator_event_type_for_action(
            "block_transition",
            ["human gate decision package is required"],
        )

        self.assertEqual(event_type, "transition_blocked")
        self.assertEqual(severity, "warning")
        self.assertFalse(requires_user)
        self.assertEqual(block_kind, "transient")

    def test_transition_hook_structured_needs_input_pages_user(self) -> None:
        event_type, severity, requires_user, block_kind = transition_hook.operator_event_type_for_action(
            "block_transition",
            [{"typed_block_kind": "needs_input", "decision_package_ref": "kanban-artifact:decision-package"}],
        )

        self.assertEqual(event_type, "decision_requested")
        self.assertEqual(severity, "requires_user")
        self.assertTrue(requires_user)
        self.assertEqual(block_kind, "needs_input")


if __name__ == "__main__":
    unittest.main()
