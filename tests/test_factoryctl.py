from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factoryctl.py"
SPEC = importlib.util.spec_from_file_location("factoryctl", MODULE_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl"] = factoryctl
SPEC.loader.exec_module(factoryctl)


def load_card(name: str) -> dict:
    return factoryctl.load_json_like(ROOT / "examples" / "cards" / name)


class FactoryCtlTest(unittest.TestCase):
    def test_product_face_card_requires_product_face_and_review_workers(self) -> None:
        card = load_card("v35_valid_product_face.md")
        report = factoryctl.build_gate_report(card)

        self.assertEqual(report["card_validation_errors"], [])
        self.assertEqual(report["workers"]["product-face"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["independent-reviewer"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["solana-quasar-auditor"]["status"], "not_required_by_current_card")

    def test_onchain_r3_card_requires_security_auditor_review_and_human_gate(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        report = factoryctl.build_gate_report(card)

        self.assertEqual(report["card_validation_errors"], [])
        self.assertEqual(report["workers"]["codex-security"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["solana-quasar-auditor"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["independent-reviewer"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["human-gate-clerk"]["status"], "requires_execution")

    def test_r3_without_scan_and_human_packet_is_invalid(self) -> None:
        card = load_card("v35_invalid_security_no_scan.md")
        errors = factoryctl.validate_card(card)

        self.assertIn("security_scan_packet required for R3/R4 work", errors)
        self.assertIn("human_gate_packet required for R3/R4 work", errors)

    def test_self_review_is_invalid(self) -> None:
        card = load_card("v35_invalid_self_review.md")
        self.assertIn("executor_identity and reviewer_identity must differ", factoryctl.validate_card(card))

    def test_pass_worker_result_requires_evidence(self) -> None:
        card = load_card("v35_valid_security_with_scan.md")

        with self.assertRaisesRegex(ValueError, "require at least one evidence ref"):
            factoryctl.build_worker_result(
                "codex-security",
                card,
                result="PASS",
                tool_or_profile="codex-security:security-scan",
                executed_by="kaxis-cybersecurity",
                evidence_refs=[],
                blocking_findings=False,
                findings_summary="",
                next_action="",
            )

    def test_pass_worker_result_cannot_have_blocking_findings(self) -> None:
        card = load_card("v35_valid_security_with_scan.md")

        with self.assertRaisesRegex(ValueError, "PASS cannot have blocking_findings=true"):
            factoryctl.build_worker_result(
                "codex-security",
                card,
                result="PASS",
                tool_or_profile="codex-security:security-scan",
                executed_by="kaxis-cybersecurity",
                evidence_refs=["reports/security.md"],
                blocking_findings=True,
                findings_summary="blocking issue",
                next_action="fix",
            )

    def test_human_approval_requires_evidence(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")

        with self.assertRaisesRegex(ValueError, "approved human gates require"):
            factoryctl.build_human_gate_record(
                card,
                gate_type="R3",
                decision="approved",
                human_actor="Felipe",
                approved_scope=[],
                forbidden_scope=[],
                required_changes=[],
                risk_owner=None,
                security_owner=None,
                rollback_owner=None,
                evidence_refs=[],
                notes="",
            )
