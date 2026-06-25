from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factoryctl.py"
SPEC = importlib.util.spec_from_file_location("factoryctl_board_reconciler", MODULE_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl_board_reconciler"] = factoryctl
SPEC.loader.exec_module(factoryctl)


def load_vfinal_card() -> dict:
    return factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")


def sot_without_owner_packet_card() -> dict:
    card = load_vfinal_card()
    card["phase"] = "F9"
    card["surfaces"] = ["architecture", "planning"]
    card["autonomy_mode"] = "planning_only"
    card["risk_initial"] = "R2"
    card["risk_effective"] = "R2"
    card.pop("factory_phase_lock", None)
    card.pop("operator_briefing_package_ref", None)
    card.pop("owner_review_ref", None)
    card["review"]["human_gate_required"] = False
    card["review"]["CTO_gate_required"] = False
    return card


class FactoryBoardReconcilerTest(unittest.TestCase):
    def test_declared_f9_without_owner_material_reconciles_to_f5_artifact_not_human_gate(self) -> None:
        card = sot_without_owner_packet_card()
        snapshot = {
            "rows": {
                "todo": [
                    {
                        "id": "task-phasejump",
                        "status": "todo",
                        "title": "Architecture gate",
                        "assignee": "human-gate-clerk",
                        "body": json.dumps(card),
                    }
                ]
            }
        }

        plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha")

        self.assertEqual(factoryctl.validate_board_reconcile_plan(plan), [])
        self.assertEqual(plan["plan_action"], "create_next_artifact_task")
        self.assertEqual(plan["phase_engine"]["computed_phase_id"], "F5")
        self.assertEqual(plan["phase_engine"]["next_required_artifact"], "operator_briefing_package")
        self.assertFalse(plan["human_gate_required"])
        self.assertFalse(plan["user_decision_required"])
        self.assertTrue(plan["create_task_allowed"])
        task_body = plan["create_task_contract"]["body"]
        self.assertFalse(task_body["agent_may_choose_phase"])
        self.assertEqual(task_body["required_output"], "operator_briefing_package")
        self.assertIn("ask for a human gate when phase_engine.human_gate_allowed is false", task_body["forbidden_actions"])

    def test_premature_human_gate_request_is_suppressed_until_phase_engine_allows_it(self) -> None:
        card = sot_without_owner_packet_card()
        card["phase"] = "F5"
        card["review"]["human_gate_required"] = True
        snapshot = {
            "rows": {
                "blocked": [
                    {
                        "id": "task-earlygate",
                        "status": "blocked",
                        "title": "Human architecture gate",
                        "assignee": "human-gate-clerk",
                        "body": json.dumps(card),
                    }
                ]
            }
        }

        misleading_help = {
            "gate_status": "blocked",
            "factory_next_action": {
                "owner": "human-gate-clerk",
                "action": "ask operator for architecture approval",
                "why": "legacy helper requested authority too early",
            },
            "user_decision_required": [
                {
                    "decision_type": "authority_required",
                    "reason": "legacy helper requested authority too early",
                    "user_action": "approve or reject",
                    "factory_prepares": "human gate packet",
                }
            ],
            "blocked_because": [],
        }
        with mock.patch.object(factoryctl, "build_factory_help", return_value=misleading_help):
            plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha")

        self.assertEqual(factoryctl.validate_board_reconcile_plan(plan), [])
        self.assertEqual(plan["plan_action"], "create_next_artifact_task")
        self.assertEqual(plan["phase_engine"]["computed_phase_id"], "F5")
        self.assertFalse(plan["human_gate_required"])
        self.assertFalse(plan["user_decision_required"])
        self.assertEqual(plan["create_task_contract"]["body"]["required_output"], "operator_briefing_package")
        self.assertTrue(
            any("premature human gate request suppressed" in item for item in plan["blocked_reasons"])
        )

    def test_unfinished_board_without_canonical_card_repairs_contract_instead_of_guessing_phase(self) -> None:
        snapshot = {
            "rows": {
                "todo": [
                    {
                        "id": "task-nocard",
                        "status": "todo",
                        "title": "Continue planning",
                        "body": json.dumps({"objective": "continue planning"}),
                    }
                ]
            }
        }

        plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha")

        self.assertEqual(factoryctl.validate_board_reconcile_plan(plan), [])
        self.assertEqual(plan["plan_action"], "repair_board_contract")
        self.assertTrue(plan["create_task_allowed"])
        self.assertEqual(plan["create_task_contract"]["body"]["required_output"], "canonical_factory_card")
        self.assertFalse(plan["create_task_contract"]["body"]["agent_may_choose_phase"])
        self.assertFalse(plan["human_gate_required"])

    def test_ready_work_uses_native_dispatch_not_reconcile_task(self) -> None:
        snapshot = {
            "rows": {
                "ready": [
                    {
                        "id": "task-ready",
                        "status": "ready",
                        "title": "Worker task",
                        "body": "{}",
                    }
                ]
            }
        }

        plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha")

        self.assertEqual(plan["plan_action"], "dispatch_ready")
        self.assertFalse(plan["create_task_allowed"])
        self.assertTrue(plan["native_dispatch_required_next"])
        self.assertIsNone(plan["create_task_contract"])

    def test_multiple_active_cards_block_instead_of_selecting_from_context(self) -> None:
        card_a = sot_without_owner_packet_card()
        card_b = copy.deepcopy(card_a)
        card_b["card_id"] = "OF-VFINAL-002"
        snapshot = {
            "rows": {
                "todo": [
                    {"id": "task-carda", "status": "todo", "body": json.dumps(card_a)},
                    {"id": "task-cardb", "status": "todo", "body": json.dumps(card_b)},
                ]
            }
        }

        plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha")

        self.assertEqual(plan["plan_action"], "block_invariant_violation")
        self.assertFalse(plan["create_task_allowed"])
        self.assertTrue(any("multiple active canonical factory cards" in item for item in plan["blocked_reasons"]))


if __name__ == "__main__":
    unittest.main()
