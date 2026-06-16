from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FACTORYCTL_SPEC = importlib.util.spec_from_file_location("factoryctl", ROOT / "scripts" / "factoryctl.py")
assert FACTORYCTL_SPEC is not None
factoryctl = importlib.util.module_from_spec(FACTORYCTL_SPEC)
assert FACTORYCTL_SPEC.loader is not None
sys.modules["factoryctl"] = factoryctl
FACTORYCTL_SPEC.loader.exec_module(factoryctl)

SELF_SPEC = importlib.util.spec_from_file_location("factory_self_improvement", ROOT / "scripts" / "factory_self_improvement.py")
assert SELF_SPEC is not None
self_improvement = importlib.util.module_from_spec(SELF_SPEC)
assert SELF_SPEC.loader is not None
sys.modules["factory_self_improvement"] = self_improvement
SELF_SPEC.loader.exec_module(self_improvement)


def vfinal_card() -> dict:
    return json.loads((ROOT / "templates" / "vfinal-factory-card.json").read_text(encoding="utf-8"))


class FactorySelfImprovementTest(unittest.TestCase):
    def test_vfinal_card_requires_reasoning_policy(self) -> None:
        card = vfinal_card()
        card.pop("reasoning_policy")

        errors = factoryctl.validate_card(card)

        self.assertIn("reasoning_policy required for OVERKILL_VFINAL cards", errors)

    def test_vfinal_product_surface_requires_reference_quality_packet(self) -> None:
        card = vfinal_card()
        card["surfaces"] = ["frontend"]
        card["product_face_packet"]["surface"] = "web_app"
        card["product_face_packet"]["mode"] = "greenfield"
        card.pop("reference_quality_packet")

        errors = factoryctl.validate_card(card)

        self.assertIn("reference_quality_packet required for vFinal product-facing surfaces", errors)

    def test_vfinal_product_surface_requires_professional_design_process(self) -> None:
        card = vfinal_card()
        card["surfaces"] = ["frontend"]
        card.pop("professional_design_process")

        errors = factoryctl.validate_card(card)

        self.assertIn("professional_design_process required for vFinal product-facing surfaces", errors)

    def test_professional_design_process_rejects_nominal_reference_research(self) -> None:
        process = json.loads(json.dumps(vfinal_card()["professional_design_process"]))
        process["reference_research"]["sources"] = process["reference_research"]["sources"][:1]
        process["reference_research"]["sources"][0]["extracted_patterns"] = ["single pattern is too weak"]
        process["wireframe_gate"] = {
            "status": "BLOCKED",
            "basis": "Wireframe review found a product-specific blocker.",
        }

        errors = factoryctl.validate_professional_design_process(process)

        self.assertIn("professional_design_process.reference_research.sources requires at least 3 sources", errors)
        self.assertIn(
            "professional_design_process.reference_research.sources[0].extracted_patterns requires at least 2 items",
            errors,
        )
        self.assertIn("professional_design_process.wireframe_gate.blocker_id is required when status is BLOCKED", errors)
        self.assertIn("professional_design_process.wireframe_gate.owner is required when status is BLOCKED", errors)
        self.assertIn("professional_design_process.wireframe_gate.next_action is required when status is BLOCKED", errors)
        self.assertIn("professional_design_process.wireframe_gate.proof_refs must be a non-empty array when status is BLOCKED", errors)

    def test_professional_design_process_accepts_controlled_blocking_gates_as_records(self) -> None:
        process = json.loads(json.dumps(vfinal_card()["professional_design_process"]))
        process["wireframe_gate"] = {
            "status": "BLOCKED",
            "blocker_id": "wireframe-state-map-missing",
            "owner": "product-face",
            "next_action": "Add explicit blocked and error state wireframes.",
            "basis": "The current wireframe does not map blocked/error states.",
            "proof_refs": ["external:wireframe-review"],
        }
        process["prototype_gate"] = {
            "status": "NEEDS_REWORK",
            "blocker_id": "prototype-real-data-missing",
            "owner": "product-face",
            "next_action": "Replay prototype with dense and empty data states.",
            "basis": "Prototype review did not include realistic data states.",
            "proof_refs": ["external:prototype-review"],
        }
        process["comparative_review_gate"] = {
            "status": "PENDING",
            "blocker_id": "comparative-review-not-run",
            "owner": "independent-product-face-reviewer",
            "next_action": "Run side-by-side reference comparison.",
            "basis": "Comparative review has not executed yet.",
            "proof_refs": ["external:comparative-review-request"],
        }

        self.assertEqual(factoryctl.validate_professional_design_process(process), [])

    def test_controlled_design_gate_blocks_product_facing_implementation(self) -> None:
        card = vfinal_card()
        card["surfaces"] = ["frontend"]
        card["professional_design_process"]["wireframe_gate"] = {
            "status": "BLOCKED",
            "blocker_id": "wireframe-state-map-missing",
            "owner": "product-face",
            "next_action": "Add explicit blocked and error state wireframes.",
            "basis": "The current wireframe does not map blocked/error states.",
            "proof_refs": ["external:wireframe-review"],
        }

        errors = factoryctl.validate_card(card)

        self.assertIn(
            "professional_design_process.wireframe_gate.status BLOCKED blocks product-facing implementation: Add explicit blocked and error state wireframes.",
            errors,
        )

    def test_professional_design_process_requires_real_library_research(self) -> None:
        process = json.loads(json.dumps(vfinal_card()["professional_design_process"]))
        process["reference_research"].pop("library_searches")
        process["reference_research"].pop("rejected_references")
        process["reference_research"].pop("pattern_synthesis")
        process["reference_research"]["reference_evidence_policy"] = {
            "capture_required_before_implementation": False,
            "side_by_side_comparison_required_before_pass": False,
            "public_refs_only": True,
            "no_private_screenshots_in_repo": True,
        }
        process["comparative_review_gate"]["reviewer_role"] = "product-face"

        errors = factoryctl.validate_professional_design_process(process)

        self.assertIn("professional_design_process.reference_research.library_searches requires at least 2 library searches", errors)
        self.assertIn("professional_design_process.reference_research.rejected_references requires at least 2 rejected candidates", errors)
        self.assertIn("professional_design_process.reference_research.pattern_synthesis.layout_hierarchy is required", errors)
        self.assertIn(
            "professional_design_process.reference_research.reference_evidence_policy.capture_required_before_implementation must be true",
            errors,
        )
        self.assertIn(
            "professional_design_process.comparative_review_gate.reviewer_role must identify an independent design/Product Face reviewer",
            errors,
        )

    def test_reference_quality_rejects_copy_without_license_ref(self) -> None:
        packet = dict(vfinal_card()["reference_quality_packet"])
        packet["references"] = [
            {
                "source_id": "component-library",
                "source_url_or_ref": "https://example.invalid/component",
                "use_type": "licensed_component",
                "what_to_learn": ["button pattern"],
                "copy_policy": "copy_only_with_license_recorded",
            }
        ]

        errors = factoryctl.validate_reference_quality_packet(packet)

        self.assertIn("reference_quality_packet.references[0].license_or_terms_ref is required for copied code/assets", errors)

    def test_product_ui_reference_quality_rejects_single_weak_reference(self) -> None:
        packet = json.loads(json.dumps(vfinal_card()["reference_quality_packet"]))
        packet["references"] = packet["references"][:1]
        packet.pop("rejected_references")
        packet.pop("dimensional_synthesis")

        errors = factoryctl.validate_reference_quality_packet(packet)

        self.assertIn(
            "reference_quality_packet.single_reference_waiver is required for single-reference product/UI packets",
            errors,
        )
        self.assertIn("reference_quality_packet.references requires at least 3 sources for product/UI work", errors)
        self.assertIn(
            "reference_quality_packet.rejected_references requires at least 2 rejected candidates for product/UI work",
            errors,
        )
        self.assertIn("reference_quality_packet.dimensional_synthesis is required for product/UI work", errors)

    def test_product_ui_reference_quality_allows_bounded_single_reference_waiver(self) -> None:
        packet = json.loads(json.dumps(vfinal_card()["reference_quality_packet"]))
        packet["references"] = packet["references"][:1]
        packet.pop("rejected_references")
        packet.pop("dimensional_synthesis")
        packet["single_reference_waiver"] = {
            "owner": "product-owner",
            "reason": "Only one authoritative source exists for this bounded visual decision.",
            "expires_at": "before-product-face-pass",
            "forbidden_claims": ["full product quality benchmark", "best-in-class visual comparison"],
        }

        self.assertEqual(factoryctl.validate_reference_quality_packet(packet), [])

    def test_reference_quality_does_not_force_visual_bar_for_technical_domain(self) -> None:
        packet = json.loads(json.dumps(vfinal_card()["reference_quality_packet"]))
        packet["reference_domain"] = "technical_domain"
        packet["experience_category"] = "database migration safety"
        packet["references"] = packet["references"][:1]
        packet.pop("rejected_references")
        packet.pop("dimensional_synthesis")
        packet.pop("product_experience_fields_informed")

        self.assertEqual(factoryctl.validate_reference_quality_packet(packet), [])

    def test_worker_packet_carries_reasoning_and_reference_contracts(self) -> None:
        card_path = ROOT / "templates" / "vfinal-factory-card.json"
        card = vfinal_card()

        packet = factoryctl.build_worker_packet("implementation-worker", card, card_path)

        self.assertEqual(packet["input_contract"]["reasoning_policy"]["record_type"], "reasoning_policy")
        self.assertEqual(packet["input_contract"]["reference_quality_packet"]["record_type"], "reference_quality_packet")
        self.assertEqual(packet["input_contract"]["professional_design_process"]["record_type"], "professional_design_process")
        self.assertEqual(packet["input_contract"]["learning_proposal_refs"], ["templates/factory-learning-proposal.json"])

    def test_default_reference_registry_contains_post_sources_as_catalog_entries(self) -> None:
        registry = self_improvement.default_reference_source_registry()
        source_ids = {source["source_id"] for source in registry["sources"]}

        self.assertIn("motionsites", source_ids)
        self.assertIn("uiverse", source_ids)
        self.assertIn("21st-dev", source_ids)
        self.assertIn("mobbin", source_ids)
        self.assertIn("pageflows", source_ids)
        self.assertIn("sceneai", source_ids)
        self.assertIn("refero-styles", source_ids)

    def test_missing_capability_plan_blocks_sensitive_gap_for_human_gate(self) -> None:
        gate_report = {
            "card_id": "CARD-1",
            "blocked_workers": ["cloud-infra-security-specialist"],
            "workers": {
                "cloud-infra-security-specialist": {
                    "status": "blocked_missing_inputs",
                    "reason": "credential_status failed for production deploy",
                }
            },
            "card_validation_errors": [],
        }

        plan = self_improvement.build_missing_capability_plan(gate_report)

        self.assertTrue(plan["human_gate_required"])
        self.assertEqual(plan["status"], "blocked_needs_human_gate")
        self.assertFalse(plan["activation_policy"]["auto_activation_allowed"])
        self.assertEqual(plan["candidate_artifacts"][0]["status"], "inactive_candidate")
        self.assertIn("validation_gate", plan["candidate_artifacts"][0])

    def test_learnback_issue_candidates_redact_private_paths(self) -> None:
        private_users_path = "C:" + "\\" + "Users"
        private_ref = private_users_path + "\\owner\\private-card"
        learnback = {
            "record_type": "execution_learnback_record",
            "project_ref": private_ref,
            "method_version": "OVERKILL_VFINAL",
            "findings": [
                {
                    "summary": private_ref + " leaked into public packet",
                    "severity": "high",
                    "area": "public-safety",
                    "recommended_route": "public_issue",
                    "reproduction_condition": "worker packet used local path",
                    "acceptance_hint": "redact local path",
                }
            ],
            "public_safety_boundary": {
                "raw_private_evidence_forbidden": True,
                "public_issue_requires_redaction": True,
            },
        }

        result = self_improvement.build_issue_candidates(learnback)

        candidate = result["candidates"][0]
        self.assertNotIn(private_users_path, candidate["title"])
        self.assertNotIn(private_users_path, candidate["body"])
        self.assertTrue(candidate["public_safe"])

    def test_learning_proposals_classify_findings_and_stay_inactive(self) -> None:
        learnback = {
            "record_type": "execution_learnback_record",
            "project_ref": "external:factory-run",
            "method_version": "OVERKILL_VFINAL",
            "sdlc_feedback_loop_ref": "templates/factory-sdlc-feedback-loop.json",
            "findings": [
                {
                    "summary": "Repeated review correction should become a reusable skill.",
                    "severity": "medium",
                    "area": "skill-evolution",
                    "recommended_route": "eval_or_test",
                    "learning_classification": "skill",
                    "evidence_ref": "external:review-summary",
                    "acceptance_hint": "eval fixture proves the skill improves the workflow",
                }
            ],
            "public_safety_boundary": {
                "raw_private_evidence_forbidden": True,
                "public_issue_requires_redaction": True,
            },
        }

        result = self_improvement.build_learning_proposals(learnback)

        proposal = result["proposals"][0]
        self.assertEqual(proposal["classification"], "skill")
        self.assertEqual(proposal["proposed_artifact_type"], "skill")
        self.assertEqual(proposal["activation_policy"]["default_state"], "inactive_candidate")
        self.assertFalse(proposal["activation_policy"]["auto_activation_allowed"])
        self.assertTrue(proposal["validation_plan"]["independent_review_required"])
        self.assertIn("max_agents", proposal["activation_policy"]["budget"])
        self.assertEqual(proposal["sdlc_feedback_loop_refs"], ["templates/factory-sdlc-feedback-loop.json"])
        self.assertEqual(result["sdlc_feedback_loop_refs"], ["templates/factory-sdlc-feedback-loop.json"])

    def test_learnback_issue_candidates_preserve_sdlc_feedback_loop_ref(self) -> None:
        learnback = {
            "record_type": "execution_learnback_record",
            "project_ref": "external:factory-run",
            "method_version": "OVERKILL_VFINAL",
            "sdlc_feedback_loop_ref": "templates/factory-sdlc-feedback-loop.json",
            "findings": [
                {
                    "summary": "Repeated missing worker result should become a public issue.",
                    "severity": "medium",
                    "area": "runtime",
                    "recommended_route": "public_issue",
                    "reproduction_condition": "Receipt Five reconciliation blocked on missing result.",
                    "acceptance_hint": "Add fail-closed guidance and tests.",
                }
            ],
            "public_safety_boundary": {
                "raw_private_evidence_forbidden": True,
                "public_issue_requires_redaction": True,
            },
        }

        result = self_improvement.build_issue_candidates(learnback)

        self.assertEqual(result["sdlc_feedback_loop_refs"], ["templates/factory-sdlc-feedback-loop.json"])
        self.assertEqual(
            result["candidates"][0]["sdlc_feedback_loop_refs"],
            ["templates/factory-sdlc-feedback-loop.json"],
        )

    def test_execution_learnback_record_from_receipt_preserves_sdlc_refs(self) -> None:
        receipt = {
            "receipt_five": {
                "changed": "runtime gate tightened",
                "artifact_paths": ["scripts/factoryctl.py"],
                "verification_commands": ["python -m unittest tests.test_factory_self_improvement -q"],
                "verification_result": "BLOCKED",
                "reviewer_required": True,
                "sdlc_feedback_loop_refs": ["templates/factory-sdlc-feedback-loop.json"],
                "next_action": "rerun missing worker result",
            },
            "kanban_transition_event": {
                "from_status": "review",
                "to_status": "blocked",
                "actor": "factory",
                "worker": "evidence-reconciler",
                "receipt_refs": ["receipt_five"],
                "artifact_refs": ["scripts/factoryctl.py"],
            },
            "receipt_five_reconciliation_result": {
                "required_workers": ["qa-verification-worker"],
                "missing_blocking_workers": ["qa-verification-worker"],
                "sdlc_feedback_loop_refs": ["templates/factory-sdlc-feedback-loop.json"],
            },
        }
        evidence_graph = {
            "record_type": "evidence_graph",
            "result": "BLOCKED",
            "target": {"card_ref": "examples/cards/card.md"},
            "findings": [
                {
                    "severity": "high",
                    "node_id": "worker-result:qa_verification_result",
                    "message": "qa-verification-worker result is missing",
                }
            ],
        }

        record = self_improvement.build_execution_learnback_record(receipt, evidence_graph)

        self.assertEqual(record["project_ref"], "examples/cards/card.md")
        self.assertEqual(record["sdlc_feedback_loop_refs"], ["templates/factory-sdlc-feedback-loop.json"])
        self.assertEqual(record["findings"][0]["recommended_route"], "eval_or_test")
        self.assertIn("missing worker: qa-verification-worker", record["blockers"])

    def test_execution_learnback_record_requires_receipt_or_graph_sdlc_refs(self) -> None:
        receipt = {
            "receipt_five": {
                "changed": "runtime gate tightened",
                "artifact_paths": ["scripts/factoryctl.py"],
                "verification_commands": ["python -m unittest tests.test_factory_self_improvement -q"],
                "verification_result": "PASS",
                "reviewer_required": False,
                "next_action": "continue",
            },
            "kanban_transition_event": {
                "from_status": "review",
                "to_status": "done",
                "actor": "factory",
                "worker": "evidence-reconciler",
                "receipt_refs": ["receipt_five"],
                "artifact_refs": ["scripts/factoryctl.py"],
            },
        }

        with self.assertRaisesRegex(ValueError, "requires sdlc_feedback_loop_refs"):
            self_improvement.build_execution_learnback_record(receipt)

    def test_learning_proposal_domain_rules_fail_closed(self) -> None:
        validator_spec = importlib.util.spec_from_file_location(
            "validate_public_json_artifacts",
            ROOT / "scripts" / "validate_public_json_artifacts.py",
        )
        assert validator_spec is not None
        validator = importlib.util.module_from_spec(validator_spec)
        assert validator_spec.loader is not None
        sys.modules["validate_public_json_artifacts"] = validator
        validator_spec.loader.exec_module(validator)

        proposal = json.loads((ROOT / "templates" / "factory-learning-proposal.json").read_text(encoding="utf-8"))
        private_windows_path = "C:" + "\\" + "Users" + "\\owner\\private-run.json"
        proposal["source_evidence_refs"] = [private_windows_path]
        proposal["proposed_artifact_type"] = "mcp_or_tool"
        proposal["activation_policy"]["auto_activation_allowed"] = True
        proposal["activation_policy"]["active_tool_surfaces"] = ["third-party-mcp"]
        proposal["activation_policy"]["default_state"] = "active"
        proposal["tool_governance"]["third_party_trust_status"] = "unknown"
        proposal["source_trust"] = "external_untrusted"
        proposal["untrusted_input_handling"]["reader_actor_split"] = False
        proposal["sdlc_feedback_loop_refs"] = []

        errors = validator.validate_domain_rules(proposal, "$")

        self.assertIn("$: factory_learning_proposal source_evidence_refs must be public-safe", errors)
        self.assertIn("$: factory_learning_proposal requires sdlc_feedback_loop_refs for non-rejected learnback", errors)
        self.assertIn("$: sensitive factory learning artifacts must not auto-activate", errors)
        self.assertIn("$: factory_learning_proposal must land inactive before activation", errors)
        self.assertIn("$: untrusted learning input requires reader_actor_split", errors)
        self.assertIn("$: active tool surfaces require reviewed trust status", errors)

    def test_execution_learnback_domain_rules_require_public_sdlc_ref(self) -> None:
        validator_spec = importlib.util.spec_from_file_location(
            "validate_public_json_artifacts",
            ROOT / "scripts" / "validate_public_json_artifacts.py",
        )
        assert validator_spec is not None
        validator = importlib.util.module_from_spec(validator_spec)
        assert validator_spec.loader is not None
        sys.modules["validate_public_json_artifacts"] = validator
        validator_spec.loader.exec_module(validator)

        learnback = json.loads((ROOT / "templates" / "execution-learnback-record.json").read_text(encoding="utf-8"))
        learnback.pop("sdlc_feedback_loop_ref")
        learnback.pop("sdlc_feedback_loop_refs")

        errors = validator.validate_domain_rules(learnback, "$")

        self.assertIn(
            "$: execution_learnback_record requires sdlc_feedback_loop_ref(s) for OVERKILL_VFINAL learnback",
            errors,
        )

        private_windows_path = "C:" + "\\" + "Users" + "\\owner\\private-run.json"
        learnback["sdlc_feedback_loop_ref"] = private_windows_path

        errors = validator.validate_domain_rules(learnback, "$")

        self.assertIn("$: execution_learnback_record sdlc_feedback_loop_ref(s) must be public-safe", errors)

    def test_issue_candidate_domain_rules_require_public_sdlc_ref(self) -> None:
        validator_spec = importlib.util.spec_from_file_location(
            "validate_public_json_artifacts",
            ROOT / "scripts" / "validate_public_json_artifacts.py",
        )
        assert validator_spec is not None
        validator = importlib.util.module_from_spec(validator_spec)
        assert validator_spec.loader is not None
        sys.modules["validate_public_json_artifacts"] = validator
        validator_spec.loader.exec_module(validator)

        candidate = self_improvement.build_issue_candidate(
            {
                "summary": "Repeated missing worker result should become a public issue.",
                "severity": "medium",
                "area": "runtime",
                "recommended_route": "public_issue",
            },
            [],
        )
        assert candidate is not None

        errors = validator.validate_domain_rules(candidate, "$")

        self.assertIn(
            "$: factory_improvement_issue_candidate requires sdlc_feedback_loop_refs for public/actionable routes",
            errors,
        )

        private_windows_path = "C:" + "\\" + "Users" + "\\owner\\private-run.json"
        candidate["sdlc_feedback_loop_refs"] = [private_windows_path]

        errors = validator.validate_domain_rules(candidate, "$")

        self.assertIn("$: factory_improvement_issue_candidate sdlc_feedback_loop_refs must be public-safe", errors)

    def test_owner_issue_intake_routes_critical_factory_change_to_human_gate_path(self) -> None:
        config = json.loads((ROOT / "templates" / "owner-issue-intake-config.json").read_text(encoding="utf-8"))
        issues = [
            {
                "number": 101,
                "title": "Change worker registry authority",
                "body": "Update registry and release authority.",
                "labels": ["factory-improvement"],
            }
        ]

        report = self_improvement.build_issue_intake_report(config, issues)

        self.assertEqual(report["decisions"][0]["decision"], "critical_factory_change")
        self.assertEqual(report["decisions"][0]["card_status"], "blocked")
        candidate = report["decisions"][0]["factory_card_candidate"]
        self.assertEqual(candidate["record_type"], "owner_issue_factory_card_candidate")
        self.assertFalse(candidate["activation_policy"]["auto_dispatch_allowed"])
        self.assertTrue(candidate["activation_policy"]["human_gate_required"])

    def test_governance_report_declares_mandatory_public_checks(self) -> None:
        report = self_improvement.governance_report()
        checks = "\n".join(report["mandatory_checks"])

        self.assertIn("public_safety_scan.py", checks)
        self.assertIn("secret_safety_scan.py", checks)
        self.assertIn("supply_chain_proof.py", checks)


if __name__ == "__main__":
    unittest.main()
