from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factoryctl.py"
SPEC = importlib.util.spec_from_file_location("factoryctl_product_method_sot", MODULE_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl_product_method_sot"] = factoryctl
SPEC.loader.exec_module(factoryctl)


class ProductMethodSotPlanningTest(unittest.TestCase):
    def vfinal_card(self) -> dict:
        return factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")

    def test_vfinal_template_passes_complete_product_planning_gate(self) -> None:
        self.assertEqual(factoryctl.validate_card(self.vfinal_card()), [])

    def test_complete_product_blocks_without_scope_coverage_and_creation_plan(self) -> None:
        card = self.vfinal_card()
        card.pop("full_product_sot_scope_coverage_ref")
        card.pop("product_creation_plan_ref")
        card["product_sot"].pop("full_product_sot_scope_coverage_ref")

        errors = factoryctl.validate_card(card)

        self.assertIn(
            "full_product_sot_scope_coverage or full_product_sot_scope_coverage_ref is required for complete Product SOT planning",
            errors,
        )
        self.assertIn("product_sot.full_product_sot_scope_coverage_ref is required", errors)
        self.assertIn(
            "product_creation_plan or product_creation_plan_ref is required before material product implementation",
            errors,
        )

    def test_slice_plan_cannot_replace_full_product_plan(self) -> None:
        card = self.vfinal_card()
        card["software_development_plan"].pop("full_product_plan")

        errors = factoryctl.validate_card(card)

        self.assertIn("software_development_plan.full_product_plan is required before slice execution", errors)
        self.assertIn("software_development_plan.slice_plan cannot stand in for full_product_plan", errors)

    def test_method_contract_separates_scope_route_and_engineering_methods(self) -> None:
        card = self.vfinal_card()
        card["method_contract"].pop("engineering_method_matrix")
        card["method_contract"]["canonical_scope_source"] = "raw paper"

        errors = factoryctl.validate_card(card)

        self.assertIn("method_contract.canonical_scope_source must be approved Product SOT", errors)
        self.assertIn("method_contract.engineering_method_matrix is required", errors)

    def test_research_required_requires_specialist_research_plan(self) -> None:
        card = self.vfinal_card()
        card["outcome_contract"]["discovery_depth"] = "research_required"
        card.pop("specialist_research_plan_ref")

        errors = factoryctl.validate_card(card)

        self.assertIn(
            "specialist_research_plan or specialist_research_plan_ref is required when research_required is active",
            errors,
        )

    def test_onchain_production_ladder_requires_devnet_mainnet_and_human_authority_policy(self) -> None:
        card = self.vfinal_card()
        card["surfaces"] = ["solana", "production"]
        card["production_promotion_ladder"] = {
            "record_type": "production_promotion_ladder",
            "environments": [
                {"environment": "local"},
                {"environment": "production"},
            ],
            "promotion_policy": {
                "preproduction_proof_cannot_claim_production": True,
                "retest_after_promotion": True,
            },
            "onchain_policy": {
                "mainnet_authority_requires_human_gate": False,
                "post_mainnet_smoke_required": False,
            },
        }

        errors = factoryctl.validate_card(card)

        self.assertIn("onchain_work_package required for onchain surfaces", errors)
        self.assertIn("onchain production ladder must include devnet", errors)
        self.assertIn("onchain production ladder must include mainnet", errors)
        self.assertIn("onchain production ladder requires human mainnet authority policy", errors)
        self.assertIn("onchain production ladder requires post-mainnet smoke policy", errors)

    def test_stale_product_context_blocks_implementation(self) -> None:
        card = self.vfinal_card()
        card["product_context_packet"] = {
            "record_type": "product_context_packet",
            "stale": True,
        }

        self.assertIn(
            "product_context_packet is stale and must be refreshed before implementation",
            factoryctl.validate_card(card),
        )

    def test_worker_packet_carries_product_context_and_research_refs(self) -> None:
        card = self.vfinal_card()

        packet = factoryctl.build_worker_packet("implementation-worker", card, ROOT / "templates" / "vfinal-factory-card.json")
        contract = packet["input_contract"]

        self.assertEqual(contract["product_context_packet_ref"], "templates/product-context-packet.json")
        self.assertEqual(contract["product_creation_plan_ref"], "templates/product-creation-plan.json")
        self.assertEqual(contract["specialist_research_plan_ref"], "templates/specialist-research-plan.json")
        self.assertEqual(contract["specialist_decision_packet_ref"], "templates/specialist-decision-packet.json")

    def test_complete_product_completion_requires_claim_and_method_results(self) -> None:
        card = self.vfinal_card()
        metadata = {
            "receipt_five": {
                "changed": "completed one slice",
                "artifact_paths": ["templates/vfinal-factory-card.json"],
                "verification_commands": ["python scripts/factoryctl.py validate-card templates/vfinal-factory-card.json"],
                "verification_result": "PASS",
                "reviewer_required": False,
                "next_action": "reconcile full product",
            },
            "kanban_transition_event": {
                "from_status": "review",
                "to_status": "done",
                "actor": "qa-verification-worker",
                "worker": "qa-verification-worker",
                "receipt_refs": ["receipt_five"],
                "artifact_refs": ["templates/vfinal-factory-card.json"],
                "allowed": True,
            },
        }

        self.assertIn(
            "completion_audit is required for complete-product done promotion",
            factoryctl.validate_completion(card, copy.deepcopy(metadata)),
        )

        metadata["completion_audit"] = {
            "sot_claim_results": [
                {"claim_ref": "product-sot#scope-in-001", "status": "DONE", "owner": "product-owner"}
            ],
            "method_execution_results": [
                {"method": "spec-first", "status": "EXECUTED", "evidence_refs": ["templates/spec-graph.json"]}
            ],
        }

        errors = factoryctl.validate_completion(card, metadata)

        self.assertIn("completion_audit missing method_execution_result for selected method test-first", errors)


if __name__ == "__main__":
    unittest.main()
