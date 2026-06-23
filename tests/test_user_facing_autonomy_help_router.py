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


def load_vfinal_card() -> dict:
    return factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")


class UserFacingAutonomyHelpRouterTest(unittest.TestCase):
    def test_vfinal_card_exposes_user_autonomy_contract_and_help(self) -> None:
        card = load_vfinal_card()

        errors = factoryctl.validate_card(card)
        self.assertEqual(errors, [])

        payload = factoryctl.build_factory_help(card, ROOT / "templates" / "vfinal-factory-card.json")

        self.assertEqual(payload["record_type"], "factory_help_next_action")
        self.assertEqual(payload["workflow_phase"]["phase_id"], "F11")
        self.assertEqual(payload["factory_next_action"]["owner"], "factory")
        self.assertIn("operator", " ".join(payload["limits"]).lower())
        self.assertIsInstance(payload["user_decision_required"], list)
        self.assertIsInstance(payload["factory_resolved_without_user"], list)

    def test_operator_interrupt_policy_is_required(self) -> None:
        card = load_vfinal_card()
        card["user_facing_autonomy_contract"].pop("operator_interrupt_policy")

        errors = factoryctl.validate_card(card)

        self.assertIn("user_facing_autonomy_contract.operator_interrupt_policy is required", errors)

    def test_late_r2_phase_does_not_request_human_gate_by_phase_alone(self) -> None:
        card = load_vfinal_card()
        card["phase"] = "F15"
        card["risk_initial"] = "R2"
        card["risk_effective"] = "R2"
        card["surfaces"] = ["code"]
        card["review"]["human_gate_required"] = False

        report = factoryctl.build_gate_report(card)
        payload = factoryctl.build_factory_help(card, ROOT / "templates" / "vfinal-factory-card.json")

        self.assertFalse(report["workers"]["human-gate-clerk"]["required"])
        self.assertNotIn("human-gate-clerk", report["required_workers"])
        self.assertFalse(
            any(decision["decision_type"] == "authority_required" for decision in payload["user_decision_required"]),
            payload["user_decision_required"],
        )
        self.assertGreater(len(payload["factory_resolved_without_user"]), 0)

    def test_r3_future_gate_packet_is_not_operator_interrupt_without_pending_authority(self) -> None:
        card = load_vfinal_card()
        card["risk_initial"] = "R3"
        card["risk_effective"] = "R3"
        card["surfaces"] = ["code"]
        card["review"]["human_gate_required"] = False
        card["review"]["CTO_gate_required"] = False
        card["human_gate_packet"] = {
            "decision_state": "not_required_for_current_step",
            "gate_type": "future_release_boundary",
        }

        required, reason = factoryctl.human_gate_required_for_card(card)

        self.assertFalse(required, reason)

    def test_missing_product_creation_plan_routes_to_planning_not_implementation(self) -> None:
        card = load_vfinal_card()
        card.pop("product_creation_plan_ref")
        card.pop("product_creation_plan", None)

        payload = factoryctl.build_factory_help(card, ROOT / "templates" / "vfinal-factory-card.json")

        self.assertEqual(payload["gate_status"], "blocked")
        self.assertIn("Product Creation Plan", payload["factory_next_action"]["action"])
        self.assertIn("execute before plans and stop criteria exist", payload["blocked_actions"])
        self.assertNotIn("dispatch required worker packets", payload["factory_next_action"]["action"])

    def test_internal_coordination_question_fails_validation(self) -> None:
        card = load_vfinal_card()
        card["user_facing_autonomy_contract"]["user_questions"] = [
            {
                "question": "Can you coordinate worker packets and schemas for the factory?",
                "class": "preference",
                "factory_resolution_path": "factory should prepare a bounded decision packet instead",
            }
        ]

        errors = factoryctl.validate_card(card)

        self.assertTrue(
            any("asks the user to perform internal factory coordination" in error for error in errors),
            errors,
        )

    def test_discoverable_question_must_be_resolved_by_factory(self) -> None:
        card = load_vfinal_card()
        card["user_facing_autonomy_contract"]["user_questions"] = [
            {
                "question": "Which required workers exist in the registry?",
                "class": "discoverable",
                "factory_resolution_path": "inspect agents/worker-registry.public.json",
            }
        ]

        errors = factoryctl.validate_card(card)

        self.assertTrue(
            any("is discoverable and must be resolved by the factory" in error for error in errors),
            errors,
        )

    def test_product_intent_confirmation_is_user_visible_without_execution_approval(self) -> None:
        card = load_vfinal_card()
        card["user_facing_autonomy_contract"]["user_questions"] = [
            {
                "question": "Confirma que esse entendimento descreve o produto certo antes do Product SOT?",
                "class": "product_intent_confirmation",
                "factory_resolution_path": "operator understanding confirmation packet",
            }
        ]

        errors = factoryctl.validate_card(card)
        payload = factoryctl.build_factory_help(card, ROOT / "templates" / "vfinal-factory-card.json")

        self.assertEqual(errors, [])
        decision = payload["user_decision_required"][0]
        self.assertEqual(decision["decision_type"], "product_intent_confirmation")
        self.assertIn("confirm, correct or reject", decision["user_action"])
        self.assertNotIn("approve", decision["user_action"].lower())


if __name__ == "__main__":
    unittest.main()
