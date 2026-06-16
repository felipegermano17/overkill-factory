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

    def activated_game_contract(self) -> dict:
        return {
            "record_type": "capability_pack_contract",
            "pack_id": "game-product-pack",
            "status": "activated",
            "lifecycle_state": "activated",
            "covered_surfaces": ["game", "3d", "asset-pipeline"],
            "specialist_workers": ["game-runtime-builder", "game-design-specialist", "game-qa-specialist"],
            "activation_evidence_refs": ["external:game-pack-activation"],
            "tool_refs": ["external:game-runtime-tool"],
            "local_smoke_path": "external:playable-game-smoke-command",
            "eval_path": "external:game-eval-command",
            "smoke_evidence_ref": "external:playable-game-smoke",
            "eval_evidence_ref": "external:game-eval",
            "profile_binding_refs": {
                "game-runtime-builder": "external:game-runtime-profile-binding",
                "game-design-specialist": "external:game-design-profile-binding",
                "game-qa-specialist": "external:game-qa-profile-binding",
            },
            "permission_class": "bounded-worker",
            "missing_capabilities": [],
            "execution_rule": "Game execution is allowed only after playable smoke, performance budget and game QA proof exist.",
            "structured_proofs_required": [
                "game.design-packet",
                "game.performance-budget",
                "game.playable-smoke",
                "game.playtest-review",
                "game.runtime-choice",
            ],
            "worker_mapping": {
                "runtime": ["game-runtime-builder"],
                "design": ["game-design-specialist"],
                "qa": ["game-qa-specialist"],
            },
        }

    def activated_registry_pack_contract(self, pack_id: str, surfaces: list[str]) -> dict:
        proofs = factoryctl.load_capability_packs()[pack_id]["structured_proofs_required"]
        return {
            "record_type": "capability_pack_contract",
            "pack_id": pack_id,
            "status": "activated",
            "lifecycle_state": "activated",
            "covered_surfaces": surfaces,
            "specialist_workers": ["domain-builder", "domain-qa-specialist"],
            "activation_evidence_refs": [f"external:{pack_id}-activation"],
            "tool_refs": [f"external:{pack_id}-tool"],
            "local_smoke_path": f"external:{pack_id}-smoke-command",
            "eval_path": f"external:{pack_id}-eval-command",
            "smoke_evidence_ref": f"external:{pack_id}-smoke",
            "eval_evidence_ref": f"external:{pack_id}-eval",
            "profile_binding_refs": {
                "domain-builder": f"external:{pack_id}-builder-profile",
                "domain-qa-specialist": f"external:{pack_id}-qa-profile",
            },
            "permission_class": "bounded-worker",
            "missing_capabilities": [],
            "execution_rule": f"{pack_id} execution is allowed only after its structured proofs exist.",
            "structured_proofs_required": proofs,
            "worker_mapping": {
                "build": ["domain-builder"],
                "qa": ["domain-qa-specialist"],
            },
        }

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

    def test_product_delivery_quality_profile_requires_readiness_proof_coverage(self) -> None:
        card = self.vfinal_card()
        card["product_delivery_quality_profile"] = factoryctl.load_json_like(
            ROOT / "templates" / "product-delivery-quality-profile.json"
        )
        card["product_creation_plan"] = factoryctl.load_json_like(ROOT / "templates" / "product-creation-plan.json")
        card["product_implementation_readiness"] = factoryctl.load_json_like(
            ROOT / "templates" / "product-implementation-readiness.json"
        )
        card["product_implementation_readiness"].pop("delivery_profile_proof_coverage")

        self.assertIn(
            "product_implementation_readiness.delivery_profile_proof_coverage missing product delivery proof coverage for required proof ids: generic.scope-fit",
            factoryctl.validate_card(card),
        )

    def test_product_delivery_quality_profile_ref_requires_readiness_proof_coverage(self) -> None:
        card = self.vfinal_card()
        card["product_creation_plan"] = factoryctl.load_json_like(ROOT / "templates" / "product-creation-plan.json")
        card["product_implementation_readiness"] = factoryctl.load_json_like(
            ROOT / "templates" / "product-implementation-readiness.json"
        )
        card["product_implementation_readiness"].pop("delivery_profile_proof_coverage")

        self.assertIn(
            "product_implementation_readiness.delivery_profile_proof_coverage missing product delivery proof coverage for required proof ids: generic.scope-fit",
            factoryctl.validate_card(card),
        )

    def test_product_delivery_before_promotion_proofs_block_done_promotion_when_missing(self) -> None:
        card = self.vfinal_card()
        profile = factoryctl.load_json_like(ROOT / "templates" / "product-delivery-quality-profile.json")
        profile["required_proofs"].append(
            {
                "proof_id": "generic.release-readiness",
                "name": "Release readiness proof",
                "required_at": ["before_promotion"],
                "owner_worker": "release-ops-worker",
                "reviewer_role": "independent-reviewer",
                "evidence_kind": "review",
                "human_gate_required": False,
            }
        )
        card["product_delivery_quality_profile"] = profile
        metadata = {
            "kanban_transition_event": {
                "allowed": True,
                "from_status": "review",
                "to_status": "done",
            },
            "receipt_five_reconciliation_result": {
                "result": "PASS",
                "valid": True,
                "promotion_authority": {"result": "PASS"},
            },
        }

        errors = factoryctl.done_promotion_errors(metadata, card=card)

        self.assertIn(
            "product_delivery_promotion_proof_coverage missing product delivery proof coverage for required proof ids: generic.release-readiness",
            errors,
        )

    def test_product_delivery_before_promotion_proofs_accept_valid_coverage(self) -> None:
        card = self.vfinal_card()
        profile = factoryctl.load_json_like(ROOT / "templates" / "product-delivery-quality-profile.json")
        profile["required_proofs"].append(
            {
                "proof_id": "generic.release-readiness",
                "name": "Release readiness proof",
                "required_at": ["before_promotion"],
                "owner_worker": "release-ops-worker",
                "reviewer_role": "independent-reviewer",
                "evidence_kind": "review",
                "human_gate_required": False,
            }
        )
        card["product_delivery_quality_profile"] = profile
        metadata = {
            "kanban_transition_event": {
                "allowed": True,
                "from_status": "review",
                "to_status": "done",
            },
            "receipt_five_reconciliation_result": {
                "result": "PASS",
                "valid": True,
                "promotion_authority": {"result": "PASS"},
            },
            "product_delivery_promotion_proof_coverage": [
                {
                    "proof_id": "generic.release-readiness",
                    "status": "PASS",
                    "evidence_refs": ["external:release-readiness-review"],
                    "basis": "Independent release readiness review passed.",
                    "reviewer_role": "independent-reviewer",
                    "evidence_kind": "review",
                }
            ],
        }

        self.assertEqual(factoryctl.done_promotion_errors(metadata, card=card), [])

    def test_missing_repo_local_product_delivery_quality_profile_ref_fails_closed(self) -> None:
        card = self.vfinal_card()
        card["product_delivery_quality_profile_ref"] = "templates/missing-product-delivery-quality-profile.json"
        card["product_creation_plan"] = factoryctl.load_json_like(ROOT / "templates" / "product-creation-plan.json")
        card["product_implementation_readiness"] = factoryctl.load_json_like(
            ROOT / "templates" / "product-implementation-readiness.json"
        )

        self.assertIn(
            "card.product_delivery_quality_profile_ref does not resolve to a repo-local file: templates/missing-product-delivery-quality-profile.json",
            factoryctl.validate_card(card),
        )

    def test_product_implementation_concerns_require_structured_items(self) -> None:
        card = self.vfinal_card()
        card["product_creation_plan"] = factoryctl.load_json_like(ROOT / "templates" / "product-creation-plan.json")
        card["product_implementation_readiness"] = factoryctl.load_json_like(
            ROOT / "templates" / "product-implementation-readiness.json"
        )
        card["product_implementation_readiness"].pop("concern_items")

        self.assertIn(
            "product_implementation_readiness.CONCERNS requires concern_items",
            factoryctl.validate_card(card),
        )

    def test_product_implementation_concerns_must_cover_ready_work_units(self) -> None:
        card = self.vfinal_card()
        card["product_creation_plan"] = factoryctl.load_json_like(ROOT / "templates" / "product-creation-plan.json")
        card["product_implementation_readiness"] = factoryctl.load_json_like(
            ROOT / "templates" / "product-implementation-readiness.json"
        )
        card["product_implementation_readiness"]["concern_items"][0]["allowed_ready_work_units"] = ["other-unit"]

        self.assertIn(
            "product_implementation_readiness.CONCERNS ready_work_units must be covered by concern_items[0].allowed_ready_work_units: work-unit-001",
            factoryctl.validate_card(card),
        )

    def test_product_implementation_concerns_accept_controlled_ready_units(self) -> None:
        card = self.vfinal_card()
        card["product_creation_plan"] = factoryctl.load_json_like(ROOT / "templates" / "product-creation-plan.json")
        card["product_implementation_readiness"] = factoryctl.load_json_like(
            ROOT / "templates" / "product-implementation-readiness.json"
        )

        errors = factoryctl.validate_card(card)

        self.assertNotIn("product_implementation_readiness.CONCERNS requires concern_items", errors)
        self.assertFalse(any("allowed_ready_work_units" in error for error in errors), errors)

    def test_activated_capability_pack_proofs_block_readiness_when_missing(self) -> None:
        card = self.vfinal_card()
        card["surfaces"] = ["game", "3d", "asset-pipeline"]
        card["capability_pack_contract"] = self.activated_game_contract()
        card["product_creation_plan"] = factoryctl.load_json_like(ROOT / "templates" / "product-creation-plan.json")
        card["product_implementation_readiness"] = factoryctl.load_json_like(
            ROOT / "templates" / "product-implementation-readiness.json"
        )

        errors = factoryctl.validate_card(card)

        self.assertIn(
            "product_implementation_readiness.delivery_profile_proof_coverage missing required product delivery proof ids: game.design-packet, game.performance-budget, game.playable-smoke, game.playtest-review, game.runtime-choice",
            errors,
        )

    def test_specialized_pack_proofs_block_readiness_across_product_domains(self) -> None:
        cases = [
            ("game-product-pack", ["game"], "game.playable-smoke"),
            ("mobile-app-pack", ["ios"], "mobile.device-smoke"),
            ("data-analytics-pack", ["analytics"], "analytics.lineage"),
            ("fintech-payments-pack", ["payment"], "fintech.reconciliation-proof"),
            ("browser-extension-pack", ["extension"], "extension.service-worker-content-script"),
        ]
        for pack_id, surfaces, expected_proof in cases:
            with self.subTest(pack_id=pack_id):
                card = self.vfinal_card()
                card["surfaces"] = surfaces
                card["capability_pack_contract"] = self.activated_registry_pack_contract(pack_id, surfaces)
                card["product_creation_plan"] = factoryctl.load_json_like(ROOT / "templates" / "product-creation-plan.json")
                card["product_implementation_readiness"] = factoryctl.load_json_like(
                    ROOT / "templates" / "product-implementation-readiness.json"
                )

                errors = factoryctl.validate_card(card)

                self.assertIn(expected_proof, "\n".join(errors))

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
