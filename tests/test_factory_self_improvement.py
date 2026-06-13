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

    def test_worker_packet_carries_reasoning_and_reference_contracts(self) -> None:
        card_path = ROOT / "templates" / "vfinal-factory-card.json"
        card = vfinal_card()

        packet = factoryctl.build_worker_packet("implementation-worker", card, card_path)

        self.assertEqual(packet["input_contract"]["reasoning_policy"]["record_type"], "reasoning_policy")
        self.assertEqual(packet["input_contract"]["reference_quality_packet"]["record_type"], "reference_quality_packet")
        self.assertEqual(packet["input_contract"]["learning_proposal_refs"], ["templates/factory-learning-proposal.json"])

    def test_default_reference_registry_contains_post_sources_as_catalog_entries(self) -> None:
        registry = self_improvement.default_reference_source_registry()
        source_ids = {source["source_id"] for source in registry["sources"]}

        self.assertIn("motionsites", source_ids)
        self.assertIn("uiverse", source_ids)
        self.assertIn("21st-dev", source_ids)
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

        errors = validator.validate_domain_rules(proposal, "$")

        self.assertIn("$: factory_learning_proposal source_evidence_refs must be public-safe", errors)
        self.assertIn("$: sensitive factory learning artifacts must not auto-activate", errors)
        self.assertIn("$: factory_learning_proposal must land inactive before activation", errors)
        self.assertIn("$: untrusted learning input requires reader_actor_split", errors)
        self.assertIn("$: active tool surfaces require reviewed trust status", errors)

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
