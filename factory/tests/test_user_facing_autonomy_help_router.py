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
        self.assertEqual(payload["workflow_phase"]["phase_id"], "F13")
        self.assertEqual(payload["phase_engine"]["computed_phase_id"], "F13")
        self.assertFalse(payload["phase_engine"]["agent_route_authority"])
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

    def test_f9_planning_only_card_is_not_human_gate_by_phase_name(self) -> None:
        card = load_vfinal_card()
        card["phase"] = "F9"
        card["autonomy_mode"] = "planning_only"
        card["risk_initial"] = "R2"
        card["risk_effective"] = "R2"
        card["surfaces"] = ["planning", "source_resolution", "method_routing", "specialist_routing"]
        card["review"]["human_gate_required"] = False
        card["review"]["CTO_gate_required"] = False
        card.pop("human_gate_packet", None)

        required, reason = factoryctl.human_gate_required_for_card(card)
        report = factoryctl.build_gate_report(card)
        payload = factoryctl.build_factory_help(card, ROOT / "templates" / "vfinal-factory-card.json")

        self.assertFalse(required, reason)
        self.assertFalse(report["workers"]["human-gate-clerk"]["required"])
        self.assertFalse(
            any(decision["decision_type"] == "authority_required" for decision in payload["user_decision_required"]),
            payload["user_decision_required"],
        )

    def test_planning_only_contract_rejects_fake_human_gate_request(self) -> None:
        card = load_vfinal_card()
        card["user_facing_autonomy_contract"]["human_gate_triggers"].append("planning-only specialist routing approval")
        card["user_facing_autonomy_contract"]["approval_points"].append("source resolution approval")
        card["user_facing_autonomy_contract"]["user_questions"] = [
            {
                "question": "Can you approve method routing so the factory can continue planning?",
                "class": "authority_required",
                "factory_resolution_path": "factory should route methods without user approval",
            }
        ]

        errors = factoryctl.validate_card(card)

        self.assertTrue(
            any("planning-only factory work into a human gate" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("misclassifies planning-only factory work" in error for error in errors),
            errors,
        )

    def test_planning_only_explicit_human_gate_fails_without_authority_surface(self) -> None:
        card = load_vfinal_card()
        card["autonomy_mode"] = "planning_only"
        card["phase"] = "F9"
        card["surfaces"] = ["planning", "source_resolution", "specialist_routing"]
        card["review"]["human_gate_required"] = True
        card["review"]["CTO_gate_required"] = False

        errors = factoryctl.validate_card(card)

        self.assertIn(
            "planning-only cards must not require a human gate without authority, access, risk, release, funds, secrets or irreversible scope",
            errors,
        )

    def test_approval_request_schema_rejects_understanding_or_plan_approval_types(self) -> None:
        schemas = factoryctl.bundled_schemas()
        schema = schemas["approval-request.schema.json"]
        request = {
            "$schema": "https://overkill-factory.dev/schemas/approval-request.schema.json",
            "approval_id": "appr-fake-plan",
            "project_id": "example-project",
            "approval_type": "plan",
            "status": "pending",
            "risk": "R2",
            "scope": "approve planning-only continuation",
            "requested_by": "factory-concierge",
            "created_at": "2026-06-24T00:00:00Z",
        }

        errors = factoryctl.validate_node(schema, request, "approval_request", schemas=schemas, root_schema=schema)

        self.assertTrue(any("approval_type" in error for error in errors), errors)

    def test_pending_human_gate_requires_full_decision_package_not_markdown_only(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md")
        packet = card["human_gate_packet"]
        for field in (
            "operator_briefing_package_ref",
            "approval_request_ref",
            "evidence_index_ref",
            "owner_review_ref",
        ):
            packet.pop(field, None)
        packet["required_decision_assets"] = ["markdown_document"]
        packet["optional_explainer_assets"] = []
        packet["decision_package_delivery"] = {
            "operator_interface": "telegram",
            "push_required": True,
            "summary_only_forbidden": False,
            "material_before_question": False,
            "attachment_order": ["markdown_document"],
        }

        errors = factoryctl.validate_card(card)

        self.assertIn(
            "human_gate_packet.operator_briefing_package_ref is required before asking a human for a gate decision",
            errors,
        )
        self.assertTrue(any("required_decision_assets must include" in error for error in errors), errors)
        self.assertIn("human_gate_packet.decision_package_delivery.summary_only_forbidden must be true", errors)
        self.assertIn("human_gate_packet.decision_package_delivery.material_before_question must be true", errors)
        self.assertIn(
            "human_gate_packet.decision_package_delivery.attachment_order must include pdf_document",
            errors,
        )
        self.assertIn(
            "human_gate_packet.optional_explainer_assets must expose at least one diagram/video/audio explainer slot",
            errors,
        )

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
        schemas = factoryctl.bundled_schemas()
        help_schema = schemas["factory-help.schema.json"]

        self.assertEqual(errors, [])
        self.assertEqual(
            factoryctl.validate_node(help_schema, payload, "factory_help", schemas=schemas, root_schema=help_schema),
            [],
        )
        decision = payload["user_decision_required"][0]
        self.assertEqual(decision["decision_type"], "product_intent_confirmation")
        self.assertIn("confirm, correct or reject", decision["user_action"])
        self.assertNotIn("approve", decision["user_action"].lower())

    def test_phase_lock_blocks_architecture_when_product_sot_packet_was_not_delivered(self) -> None:
        card = load_vfinal_card()
        card["phase"] = "F9"
        card["surfaces"] = ["architecture", "repo-cleanup"]
        card.pop("operator_briefing_package_ref", None)
        card["factory_phase_lock"] = {
            "$schema": "https://overkill-factory.dev/schemas/factory-phase-lock.schema.json",
            "record_type": "factory_phase_lock",
            "current_phase_id": "F5",
            "active_frontier": "product_sot",
            "single_active_frontier": True,
            "downstream_freeze_active": True,
            "owner_surface_first": {
                "product_sot_review_packet_delivered": False,
                "summary_only_forbidden": True,
                "material_before_question": True,
            },
            "materialized_artifact_refs": {
                "product_sot_ref": "templates/product-sot.json",
                "full_product_sot_scope_coverage_ref": "templates/full-product-sot-scope-coverage.json",
                "method_contract_ref": "templates/method-contract.json",
            },
            "frozen_phase_ids": ["F8", "F9", "F10", "F11", "F12", "F13", "F15"],
            "frozen_worker_ids": ["product-architect", "handoff-packer", "human-gate-clerk"],
            "allowed_current_worker_ids": ["product-sot-planner", "factory-orchestrator"],
            "next_required_artifact": "operator_briefing_package",
            "operator_decision_required": False,
            "freeze_reason": "Product SOT owner review packet has not been delivered.",
        }

        errors = factoryctl.validate_card(card)
        payload = factoryctl.build_factory_help(card, ROOT / "templates" / "vfinal-factory-card.json")

        self.assertIn(
            "factory_phase_lock blocks downstream card phase F9 while active frontier is product_sot",
            errors,
        )
        self.assertIn(
            "factory_phase_lock owner-surface-first requires an owner-readable Product SOT review packet before architecture, repo cleanup, human gates, worker packets or execution",
            errors,
        )
        self.assertEqual(payload["gate_status"], "blocked")
        self.assertEqual(payload["phase_lock"]["active_frontier"], "product_sot")
        self.assertEqual(payload["phase_lock"]["next_required_artifact"], "operator_briefing_package")
        self.assertIn("operator_briefing_package", payload["factory_next_action"]["action"])
        self.assertEqual(payload["factory_next_action"]["owner"], "factory")
        self.assertEqual(payload["user_decision_required"], [])

    def test_phase_engine_blocks_declared_f9_without_owner_package_even_without_phase_lock(self) -> None:
        card = load_vfinal_card()
        card["phase"] = "F9"
        card["surfaces"] = ["architecture"]
        card.pop("factory_phase_lock", None)
        card.pop("operator_briefing_package_ref", None)

        errors = factoryctl.validate_card(card)
        payload = factoryctl.build_factory_help(card, ROOT / "templates" / "vfinal-factory-card.json")

        self.assertTrue(
            any("factory_phase_engine blocks declared card phase F9 while computed phase is F5" in error for error in errors),
            errors,
        )
        self.assertEqual(payload["phase_engine"]["computed_frontier"], "product_sot")
        self.assertEqual(payload["phase_engine"]["next_required_artifact"], "operator_briefing_package")
        self.assertEqual(payload["user_decision_required"], [])

    def test_phase_engine_walks_source_resolution_before_product_sot_without_agent_shortcuts(self) -> None:
        card = {
            "factory_method_version": "OVERKILL_VFINAL",
            "phase": "F5",
            "surfaces": ["planning"],
            "complete_product_required": True,
            "universal_signal_intake_ref": "external:sanitized-intake",
        }

        state = factoryctl.factory_phase_engine_state(card)
        self.assertEqual(state["computed_phase_id"], "F2")
        self.assertEqual(state["next_required_artifact"], "product_source_ledger")

        card["product_source_ledger_ref"] = "external:sanitized-source-ledger"
        state = factoryctl.factory_phase_engine_state(card)
        self.assertEqual(state["computed_phase_id"], "F2")
        self.assertEqual(state["next_required_artifact"], "operator_understanding_confirmation")

        card["operator_understanding_confirmation_ref"] = "external:sanitized-understanding"
        state = factoryctl.factory_phase_engine_state(card)
        self.assertEqual(state["computed_phase_id"], "F3")
        self.assertEqual(state["next_required_artifact"], "discovery_brief")

        card["discovery_brief_ref"] = "external:sanitized-discovery"
        state = factoryctl.factory_phase_engine_state(card)
        self.assertEqual(state["computed_phase_id"], "F4")
        self.assertEqual(state["next_required_artifact"], "outcome_contract")

        card["outcome_contract_ref"] = "external:sanitized-outcome"
        state = factoryctl.factory_phase_engine_state(card)
        self.assertEqual(state["computed_phase_id"], "F5")
        self.assertEqual(state["next_required_artifact"], "product_sot")

    def test_phase_engine_does_not_skip_pack_selection_or_authority_before_architecture(self) -> None:
        card = load_vfinal_card()
        card["phase"] = "F10"
        card["surfaces"] = ["architecture"]
        card.pop("capability_pack_contract", None)

        state = factoryctl.factory_phase_engine_state(card)
        self.assertEqual(state["computed_phase_id"], "F8")
        self.assertEqual(state["computed_frontier"], "pack_selection")
        self.assertEqual(state["next_required_artifact"], "capability_pack_contract")

        card = load_vfinal_card()
        card["phase"] = "F10"
        card["surfaces"] = ["architecture"]
        card.pop("access_capability", None)

        state = factoryctl.factory_phase_engine_state(card)
        self.assertEqual(state["computed_phase_id"], "F9")
        self.assertEqual(state["computed_frontier"], "authority")
        self.assertEqual(state["next_required_artifact"], "access_capability")

    def test_workflow_step_key_uses_concrete_phase_before_frontier_fallback(self) -> None:
        self.assertEqual(
            factoryctl.factory_workflow_step_key({"computed_phase_id": "F4", "computed_frontier": "product_sot"}),
            "F4-product-outcome-and-discovery",
        )
        self.assertEqual(
            factoryctl.factory_workflow_step_key({"computed_phase_id": "F8", "computed_frontier": "pack_selection"}),
            "F8-pack-and-product-experience-selection",
        )
        self.assertEqual(
            factoryctl.factory_workflow_step_key({"computed_phase_id": "F9", "computed_frontier": "authority"}),
            "F9-risk-and-authority-gates",
        )
        self.assertEqual(
            factoryctl.factory_workflow_step_key({"computed_phase_id": "F10", "computed_frontier": "architecture"}),
            "F10-security-architecture",
        )

    def test_repo_cleanup_is_frozen_until_ready_gate(self) -> None:
        card = load_vfinal_card()
        card["phase"] = "F11"
        card["surfaces"] = ["repo-cleanup"]
        card.pop("product_implementation_readiness_ref", None)
        card.pop("product_implementation_readiness", None)
        card["factory_phase_lock"] = dict(card["factory_phase_lock"])
        card["factory_phase_lock"]["current_phase_id"] = "F11"
        card["factory_phase_lock"]["active_phase_id"] = "F11"
        card["factory_phase_lock"]["active_frontier"] = "architecture"
        card["factory_phase_lock"]["next_required_artifact"] = "architecture_packet"
        card["factory_phase_lock"]["materialized_artifact_refs"] = dict(
            card["factory_phase_lock"]["materialized_artifact_refs"]
        )
        card["factory_phase_lock"]["materialized_artifact_refs"].pop("ready_gate_ref", None)

        errors = factoryctl.validate_card(card)
        payload = factoryctl.build_factory_help(card, ROOT / "templates" / "vfinal-factory-card.json")

        self.assertIn(
            "factory_phase_lock freezes repo cleanup, rebuild, reset and destructive cleanup until Ready Gate is materialized",
            errors,
        )
        self.assertEqual(payload["gate_status"], "blocked")
        self.assertEqual(payload["user_decision_required"], [])

    def test_factory_help_schema_accepts_phase_lock_projection(self) -> None:
        card = load_vfinal_card()
        payload = factoryctl.build_factory_help(card, ROOT / "templates" / "vfinal-factory-card.json")
        schemas = factoryctl.bundled_schemas()
        schema = schemas["factory-help.schema.json"]

        errors = factoryctl.validate_node(schema, payload, "factory_help", schemas=schemas, root_schema=schema)

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
