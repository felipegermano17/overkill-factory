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


def materialize_product_sot_frontier(card: dict) -> dict:
    card["universal_signal_intake"] = {
        "record_type": "universal_signal_intake",
        "intake_id": "runtime-intake-001",
        "source_ref_public_safe": "external:operator:source-envelope",
    }
    card["product_source_ledger"] = {
        "record_type": "product_source_ledger",
        "ledger_id": "runtime-source-ledger-001",
        "claim_table": [
            {
                "claim_id": "claim-001",
                "claim": "Product Alpha is an operations product with web and admin surfaces.",
                "claim_class": "fact",
                "status": "promoted",
                "source_refs": ["external:operator:source-envelope"],
            }
        ],
    }
    card["outcome_contract"] = {
        "record_type": "outcome_contract",
        "outcome": "Produce the complete product planning baseline before architecture.",
        "users_or_actors": ["Brazilian web3 user", "operator"],
        "success_signals": ["scope is covered", "open risks are named"],
    }
    card["product_sot"] = {
        "record_type": "product_sot",
        "what_it_is": "Product Alpha is an operations product with onboarding and operator surfaces.",
        "scope_in": ["onboarding", "operator administration"],
        "scope_out": ["production deploy", "credential transfer"],
        "evidence_refs": ["external:operator:source-envelope"],
    }
    card["full_product_sot_scope_coverage"] = {
        "record_type": "full_product_sot_scope_coverage",
        "coverage_state": "covered_for_owner_review",
        "covered_requirement_ids": ["REQ-001", "REQ-002"],
        "evidence_refs": ["external:operator:source-envelope"],
    }
    return card


def sot_without_owner_packet_card() -> dict:
    card = load_vfinal_card()
    materialize_product_sot_frontier(card)
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
        self.assertEqual(plan["create_task_contract"]["workflow_template_id"], "overkill-vfinal")
        self.assertEqual(plan["create_task_contract"]["current_step_key"], "F5-product-sot")
        task_body = plan["create_task_contract"]["body"]
        self.assertEqual(task_body["kanban_workflow_binding"]["workflow_template_id"], "overkill-vfinal")
        self.assertEqual(task_body["kanban_workflow_binding"]["current_step_key"], "F5-product-sot")
        self.assertFalse(task_body["agent_may_choose_phase"])
        self.assertEqual(task_body["required_output"], "operator_briefing_package")
        self.assertIn("ask for a human gate when phase_engine.human_gate_allowed is false", task_body["forbidden_actions"])

    def test_template_scaffold_does_not_count_as_runtime_artifacts(self) -> None:
        card = load_vfinal_card()
        card["phase"] = "F13"
        snapshot = {
            "rows": {
                "todo": [
                    {
                        "id": "task-template-copy",
                        "status": "todo",
                        "title": "Copied public template",
                        "assignee": "factory-orchestrator",
                        "body": json.dumps(card),
                    }
                ]
            }
        }

        plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha-runtime")

        self.assertEqual(factoryctl.validate_board_reconcile_plan(plan), [])
        self.assertEqual(plan["phase_engine"]["computed_phase_id"], "F1")
        self.assertEqual(plan["phase_engine"]["next_required_artifact"], "universal_signal_intake")
        self.assertFalse(plan["phase_engine"]["artifacts"]["source_input"])
        self.assertEqual(plan["create_task_contract"]["body"]["required_output"], "universal_signal_intake")

    def test_runtime_reconciler_does_not_count_template_method_after_real_sot(self) -> None:
        card = sot_without_owner_packet_card()
        card["phase"] = "F10"
        card["operator_briefing_package"] = {
            "record_type": "operator_briefing_package",
            "artifact_ref": "external:operator:product-sot-briefing",
            "formats": ["markdown", "pdf"],
        }
        snapshot = {
            "rows": {
                "todo": [
                    {
                        "id": "task-template-method",
                        "status": "todo",
                        "title": "Architecture from copied template",
                        "assignee": "product-architect",
                        "body": json.dumps(card),
                    }
                ]
            }
        }

        plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha")

        self.assertEqual(plan["phase_engine"]["computed_phase_id"], "F6")
        self.assertEqual(plan["phase_engine"]["next_required_artifact"], "method_contract")
        self.assertFalse(plan["phase_engine"]["artifacts"]["method_contract"])
        self.assertEqual(plan["create_task_contract"]["body"]["required_output"], "method_contract")

    def test_runtime_reconciler_does_not_count_template_architecture_after_real_method(self) -> None:
        card = sot_without_owner_packet_card()
        card["phase"] = "F11"
        card["operator_briefing_package"] = {
            "record_type": "operator_briefing_package",
            "artifact_ref": "external:operator:product-sot-briefing",
            "formats": ["markdown", "pdf"],
        }
        card["method_contract"] = {
            "record_type": "method_contract",
            "selected_method": "spec-first",
            "canonical_scope_source": "external:operator:product-sot",
            "required_artifacts": ["architecture_packet", "product_creation_plan"],
        }
        card["capability_pack_contract_ref"] = "external:sanitized-capability-pack-contract"
        card["product_experience_plan_ref"] = "external:sanitized-product-experience-plan"
        card["product_face_packet_ref"] = "external:sanitized-product-face-packet"
        card["project_design_system_ref"] = "external:sanitized-project-design-system"
        card["professional_design_process_ref"] = "external:sanitized-professional-design-process"
        card["access_capability_ref"] = "external:sanitized-access-capability"
        card["budget_contract_ref"] = "external:sanitized-budget-contract"
        snapshot = {
            "rows": {
                "todo": [
                    {
                        "id": "task-template-architecture",
                        "status": "todo",
                        "title": "Execution plan from copied template",
                        "assignee": "decomposition-planner",
                        "body": json.dumps(card),
                    }
                ]
            }
        }

        plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha")

        self.assertEqual(plan["phase_engine"]["computed_phase_id"], "F10")
        self.assertEqual(plan["phase_engine"]["next_required_artifact"], "architecture_packet")
        self.assertFalse(plan["phase_engine"]["artifacts"]["architecture_packet"])
        self.assertEqual(plan["create_task_contract"]["body"]["required_output"], "architecture_packet")

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
        self.assertEqual(plan["create_task_contract"]["workflow_template_id"], "overkill-vfinal")
        self.assertEqual(plan["create_task_contract"]["current_step_key"], "F1-intake")
        self.assertEqual(plan["create_task_contract"]["body"]["required_output"], "canonical_factory_card")
        self.assertFalse(plan["create_task_contract"]["body"]["agent_may_choose_phase"])
        self.assertFalse(plan["human_gate_required"])

    def test_reconciled_blocked_frontier_resumes_existing_task_instead_of_repairing_contract(self) -> None:
        frontier_task_id = "t_f8canonical"
        snapshot = {
            "rows": {
                "blocked": [
                    {
                        "id": frontier_task_id,
                        "status": "blocked",
                        "title": "F8 - Product Experience / Capability Pack selection",
                        "assignee": "factory-orchestrator",
                        "current_step_key": "F8-capability-and-product-experience-selection",
                        "body": json.dumps(
                            {
                                "packet_type": "factory_deterministic_reconcile_task",
                                "kanban_workflow_binding": {
                                    "workflow_template_id": "overkill-vfinal",
                                    "current_step_key": "F8-capability-and-product-experience-selection",
                                    "runtime_field_required": True,
                                },
                                "blocked_until_reducer_adapter_authorizes_resume_or_rerun": True,
                            }
                        ),
                        "comments": [
                            {
                                "body": (
                                    "FRONTIER_RECONCILIATION_RESULT: this is the single canonical "
                                    "frontier; resume_or_rerun only through reducer/adapter."
                                )
                            }
                        ],
                    },
                    {
                        "id": "t_oldf7",
                        "status": "blocked",
                        "title": "F7 - superseded stale branch",
                        "current_step_key": "F7-method-contract",
                        "body": json.dumps({"stale_non_consumable": True}),
                    },
                ],
                "done": [
                    {
                        "id": "t_reconcile",
                        "status": "done",
                        "title": "F7/F8 deterministic frontier reconciliation",
                        "completed_at": "2026-06-28T18:00:00Z",
                        "metadata": json.dumps(
                            {
                                "orchestration_result": {
                                    "frontier_reconciliation_result": "selected_single_canonical_frontier",
                                    "canonical_frontier_task_id": frontier_task_id,
                                    "canonical_frontier_status": (
                                        "blocked_until_reducer_adapter_authorizes_resume_or_rerun"
                                    ),
                                    "stale_non_consumable_tasks": ["t_oldf7"],
                                }
                            }
                        ),
                    }
                ],
            }
        }

        plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha")

        self.assertEqual(factoryctl.validate_board_reconcile_plan(plan), [])
        self.assertEqual(plan["plan_action"], "resume_canonical_frontier_task")
        self.assertFalse(plan["create_task_allowed"])
        self.assertIsNone(plan["create_task_contract"])
        self.assertTrue(plan["native_dispatch_required_next"])
        self.assertFalse(plan["human_gate_required"])
        self.assertEqual(plan["phase_engine"]["computed_phase_id"], "F8")
        self.assertIn("resume the existing Hermes task", plan["selected_card"]["selection_reason"])

    def test_manual_factory_start_card_without_run_graph_repairs_contract(self) -> None:
        snapshot = {
            "rows": {
                "blocked": [
                    {
                        "id": "task-manual-start",
                        "status": "blocked",
                        "title": "F1 - Product Alpha source resolution + Product SOT start",
                        "assignee": "factory-orchestrator",
                        "created_by": "overkill-factory-gerente",
                        "skills": ["overkill-factory-product-intake"],
                        "parents": [],
                        "children": [],
                        "body": json.dumps({"objective": "manual start card"}),
                    }
                ]
            }
        }

        plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha")

        self.assertEqual(factoryctl.validate_board_reconcile_plan(plan), [])
        self.assertEqual(plan["plan_action"], "repair_board_contract")
        self.assertTrue(plan["create_task_allowed"])
        self.assertFalse(plan["human_gate_required"])
        self.assertFalse(plan["user_decision_required"])
        self.assertEqual(plan["create_task_contract"]["body"]["required_output"], "canonical_factory_card")
        self.assertTrue(any("bypassed Kanban-first adapter" in item for item in plan["blocked_reasons"]))
        self.assertTrue(any("no native phase children" in item for item in plan["blocked_reasons"]))
        self.assertTrue(any("overkill-factory-product-intake" in item for item in plan["blocked_reasons"]))

    def test_ready_work_uses_native_dispatch_not_reconcile_task(self) -> None:
        snapshot = {
            "rows": {
                "ready": [
                    {
                        "id": "task-ready",
                        "status": "ready",
                        "title": "Worker task",
                        "current_step_key": "F15-runtime-execution",
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

    def test_ready_work_without_structured_phase_binding_repairs_contract_instead_of_dispatching(self) -> None:
        snapshot = {
            "rows": {
                "ready": [
                    {
                        "id": "task-ready-unbound",
                        "status": "ready",
                        "title": "Worker task without phase binding",
                        "body": "{}",
                    }
                ]
            }
        }

        plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha")

        self.assertEqual(factoryctl.validate_board_reconcile_plan(plan), [])
        self.assertEqual(plan["plan_action"], "repair_board_contract")
        self.assertFalse(plan["native_dispatch_required_next"])
        self.assertTrue(plan["create_task_allowed"])
        self.assertTrue(any("without structured phase binding" in item for item in plan["blocked_reasons"]))

    def test_ready_future_phase_does_not_dispatch_when_prior_phase_blocked(self) -> None:
        snapshot = {
            "rows": {
                "ready": [
                    {
                        "id": "task-f4-ready",
                        "status": "ready",
                        "title": "F4 outcome planning",
                        "current_step_key": "F4-product-outcome-and-discovery",
                        "body": json.dumps(
                            {
                                "packet_type": "factory_deterministic_reconcile_task",
                                "kanban_workflow_binding": {
                                    "workflow_template_id": "overkill-vfinal",
                                    "current_step_key": "F4-product-outcome-and-discovery",
                                },
                            }
                        ),
                    }
                ],
                "blocked": [
                    {
                        "id": "task-f3-blocked",
                        "status": "blocked",
                        "title": "F3 source resolution blocked",
                        "current_step_key": "F3-source-resolution",
                        "body": json.dumps(
                            {
                                "packet_type": "factory_deterministic_reconcile_task",
                                "kanban_workflow_binding": {
                                    "workflow_template_id": "overkill-vfinal",
                                    "current_step_key": "F3-source-resolution",
                                },
                            }
                        ),
                    }
                ],
            }
        }

        plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha")

        self.assertEqual(factoryctl.validate_board_reconcile_plan(plan), [])
        self.assertEqual(plan["plan_action"], "block_invariant_violation")
        self.assertFalse(plan["native_dispatch_required_next"])
        self.assertFalse(plan["create_task_allowed"])
        self.assertTrue(any("F4" in item and "F3" in item for item in plan["blocked_reasons"]))

    def test_running_future_phase_is_marked_inconsistent_when_prior_phase_blocked(self) -> None:
        snapshot = {
            "rows": {
                "running": [
                    {
                        "id": "task-f4-running",
                        "status": "running",
                        "title": "F4 outcome planning",
                        "current_step_key": "F4-product-outcome-and-discovery",
                    }
                ],
                "blocked": [
                    {
                        "id": "task-f2-blocked",
                        "status": "blocked",
                        "title": "F2 source ledger blocked",
                        "current_step_key": "F2-source-ledger",
                    }
                ],
            }
        }

        plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha")

        self.assertEqual(factoryctl.validate_board_reconcile_plan(plan), [])
        self.assertEqual(plan["plan_action"], "block_invariant_violation")
        self.assertFalse(plan["native_dispatch_required_next"])
        self.assertTrue(any("running" in item and "F4" in item and "F2" in item for item in plan["blocked_reasons"]))

    def test_phase_engine_runtime_strict_rejects_template_scaffold_artifacts(self) -> None:
        card = load_vfinal_card()

        strict_state = factoryctl.factory_phase_engine_state(card, allow_scaffold_artifacts=False)
        permissive_state = factoryctl.factory_phase_engine_state(card, allow_scaffold_artifacts=True)

        self.assertEqual(strict_state["computed_phase_id"], "F1")
        self.assertNotEqual(permissive_state["computed_phase_id"], strict_state["computed_phase_id"])

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

    def test_solana_route_gap_reconciles_to_domain_brain_repair_not_human_gate(self) -> None:
        card = load_vfinal_card()
        card["phase"] = "F10"
        card["surfaces"] = ["architecture", "solana", "onchain"]
        card.pop("capability_pack_contract", None)
        card.pop("domain_brain_provider", None)
        card.pop("solana_domain_brain_provider", None)
        card.pop("solana_ai_kit_usage_receipt", None)
        snapshot = {
            "rows": {
                "todo": [
                    {
                        "id": "task-solana-route",
                        "status": "todo",
                        "title": "Solana architecture candidate",
                        "assignee": "product-architect",
                        "body": json.dumps(card),
                    }
                ]
            }
        }

        plan = factoryctl.build_board_reconcile_plan(snapshot, board="product-alpha")

        self.assertEqual(factoryctl.validate_board_reconcile_plan(plan), [])
        self.assertEqual(plan["plan_action"], "repair_domain_brain_route")
        self.assertTrue(plan["create_task_allowed"])
        self.assertFalse(plan["human_gate_required"])
        self.assertFalse(plan["user_decision_required"])
        self.assertEqual(plan["create_task_contract"]["body"]["required_output"], "solana_ai_kit_domain_brain_route")
        self.assertIn("Solana AI Kit", plan["reason"])


if __name__ == "__main__":
    unittest.main()
