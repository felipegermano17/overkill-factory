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


if __name__ == "__main__":
    unittest.main()
