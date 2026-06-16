from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_public_json_artifacts.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_public_json_artifacts", VALIDATOR_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["validate_public_json_artifacts"] = module
    spec.loader.exec_module(module)
    return module


class PublicJsonArtifactValidatorTest(unittest.TestCase):
    def test_enforces_numeric_bounds_used_by_public_schemas(self) -> None:
        validator = load_validator()
        schema = {"type": "integer", "minimum": 1, "maximum": 3}

        self.assertEqual(validator.validate_node(schema, 2, "$"), [])
        self.assertTrue(any("below minimum" in error for error in validator.validate_node(schema, 0, "$")))
        self.assertTrue(any("above maximum" in error for error in validator.validate_node(schema, 4, "$")))

    def test_enforces_string_pattern_used_by_public_schemas(self) -> None:
        validator = load_validator()
        schema = {"type": "string", "pattern": "^[a-f0-9]{64}$"}

        self.assertEqual(validator.validate_node(schema, "a" * 64, "$"), [])
        self.assertTrue(any("does not match pattern" in error for error in validator.validate_node(schema, "not-a-sha", "$")))

    def test_worker_result_schema_types_recovery_route_digests(self) -> None:
        validator = load_validator()
        schema = validator.load_schemas()["worker-result.schema.json"]["properties"]["reviewed_recovery_route_digests"]

        self.assertEqual(validator.validate_node(schema, ["sha256:" + ("a" * 64)], "$"), [])
        self.assertTrue(
            any("does not match pattern" in error for error in validator.validate_node(schema, ["not-a-sha"], "$"))
        )

    def test_enforces_conditional_required_fields_used_by_worker_result_schema(self) -> None:
        validator = load_validator()
        schema = {
            "allOf": [
                {
                    "if": {"properties": {"result": {"const": "BLOCKED"}}, "required": ["result"]},
                    "then": {"required": ["recovery_recommendation"]},
                }
            ]
        }

        self.assertEqual(validator.validate_node(schema, {"result": "PASS"}, "$"), [])
        errors = validator.validate_node(schema, {"result": "BLOCKED"}, "$")
        self.assertTrue(any("recovery_recommendation" in error for error in errors))

    def test_quasar_runtime_schema_requires_pinned_head_only_for_pass(self) -> None:
        validator = load_validator()
        schemas = validator.load_schemas()
        schema = schemas["quasar-runtime-proof.schema.json"]
        artifact = {
            "$schema": "https://overkill-factory.dev/schemas/quasar-runtime-proof.schema.json",
            "result": "FAIL",
            "proof_kind": "containerized_product_like_quasar_build_test",
            "install_source": "github:blueshift-gg/quasar",
            "source_ref": "a89a9329f05740a20520607608b2b3b78c74f7c4",
            "source_head_expected": "a89a9329f05740a20520607608b2b3b78c74f7c4",
            "source_head": "",
            "source_head_matches": False,
            "container_image": "rust:1.91.0-bookworm@sha256:e187887ec511b3d93e45c0231d2f0fd59f1347526c58aa86343aa83c74f3e1a9",
            "solana_release": "v4.0.2",
            "solana_install_url": "https://release.anza.xyz/v4.0.2/install",
            "policy_decision": "blocked until the pinned checkout resolves",
        }

        self.assertEqual(validator.validate_node(schema, artifact, "$", schemas=schemas, root_schema=schema), [])

        artifact["result"] = "PASS"
        errors = validator.validate_node(schema, artifact, "$", schemas=schemas, root_schema=schema)

        self.assertTrue(any("source_head_matches" in error and "expected const True" in error for error in errors))
        self.assertTrue(any("source_head" in error and "does not match pattern" in error for error in errors))

    def test_enforces_contains_used_by_review_authorization_schemas(self) -> None:
        validator = load_validator()
        schema = {"type": "array", "contains": {"const": "review"}}

        self.assertEqual(validator.validate_node(schema, ["implementation", "review"], "$"), [])
        errors = validator.validate_node(schema, ["implementation", "qa"], "$")

        self.assertTrue(any("does not contain" in error for error in errors))

    def test_enforces_one_of_used_by_reference_quality_schema(self) -> None:
        validator = load_validator()
        schema = {
            "oneOf": [
                {"required": ["strong_bar"], "properties": {"mode": {"const": "strong"}}},
                {"required": ["waiver"], "properties": {"mode": {"const": "waived"}}},
            ]
        }

        self.assertEqual(validator.validate_node(schema, {"mode": "strong", "strong_bar": True}, "$"), [])
        self.assertEqual(validator.validate_node(schema, {"mode": "waived", "waiver": True}, "$"), [])
        self.assertTrue(any("expected exactly one oneOf" in error for error in validator.validate_node(schema, {}, "$")))
        self.assertTrue(
            any(
                "expected exactly one oneOf" in error
                for error in validator.validate_node(schema, {"strong_bar": True, "waiver": True}, "$")
            )
        )

    def test_schema_keyword_audit_rejects_unsupported_validation_keywords(self) -> None:
        validator = load_validator()
        schema = {
            "type": "object",
            "properties": {
                "not": {"type": "string"},
                "gate": {"not": {"const": "bypass"}},
            },
        }

        errors = validator.validate_schema_keywords(schema)

        self.assertTrue(any("unsupported JSON Schema keyword 'not'" in error for error in errors))
        self.assertFalse(any("$/properties/not:" in error for error in errors))

    def test_current_public_schemas_use_only_enforced_keywords(self) -> None:
        validator = load_validator()
        schemas = validator.load_schemas()

        errors = []
        for name, schema in schemas.items():
            if name.endswith(".json"):
                errors.extend(f"{name}: {error}" for error in validator.validate_schema_keywords(schema))

        self.assertEqual(errors, [])

    def test_public_schema_discovery_includes_agent_contract_schema(self) -> None:
        validator = load_validator()
        schema_paths = {path.relative_to(ROOT).as_posix() for path in validator.iter_schema_files()}
        schemas = validator.load_schemas()

        self.assertIn("agents/worker-contract.schema.json", schema_paths)
        self.assertIn("worker-contract.schema.json", schemas)

    def test_factory_card_schema_rejects_absurd_required_field_shapes(self) -> None:
        validator = load_validator()
        schemas = validator.load_schemas()
        schema = schemas["factory-card.schema.json"]
        card = json.loads((ROOT / "templates" / "vfinal-factory-card.json").read_text(encoding="utf-8"))

        self.assertEqual(validator.validate_node(schema, card, "$", schemas=schemas, root_schema=schema), [])

        invalid = dict(card)
        invalid["source_refs"] = "source-ledger.md"
        invalid["done_definition"] = "ship it"
        invalid["transition_event_required"] = "yes"
        invalid["review"] = "self-review"
        invalid["owner_worker"] = []

        errors = validator.validate_node(schema, invalid, "$", schemas=schemas, root_schema=schema)

        self.assertTrue(any("$.source_refs" in error and "expected type array" in error for error in errors))
        self.assertTrue(any("$.done_definition" in error and "expected type array" in error for error in errors))
        self.assertTrue(any("$.transition_event_required" in error and "expected type boolean" in error for error in errors))
        self.assertTrue(any("$.review" in error and "expected type object" in error for error in errors))
        self.assertTrue(any("$.owner_worker" in error and "expected type string" in error for error in errors))

    def test_factory_card_schema_applies_data_metrics_and_docs_plan_refs(self) -> None:
        validator = load_validator()
        schemas = validator.load_schemas()
        schema = schemas["factory-card.schema.json"]
        card = json.loads((ROOT / "templates" / "vfinal-factory-card.json").read_text(encoding="utf-8"))

        invalid = json.loads(json.dumps(card))
        invalid["data_metrics_plan"] = {
            "success_metrics": ["activation"],
            "events": ["product.activated"],
            "owners": ["product"],
            "privacy_limits": ["no personal data"],
            "risk_metrics": ["dropoff"],
            "logs": ["activation logs"],
            "alerts": ["activation failed"],
            "personal_data": ["none"],
            "visibility": ["operator dashboard"],
            "instrumentation_proof": ["dashboard test"],
        }
        invalid["user_docs_onboarding_plan"] = {
            "audience": "operator",
            "first_success_path": "run the first command",
            "tasks_covered": ["install"],
            "proof_required": ["reader smoke"],
        }

        errors = validator.validate_node(schema, invalid, "$", schemas=schemas, root_schema=schema)

        self.assertTrue(any("$.data_metrics_plan: missing required field gate_enforcement" in error for error in errors))
        self.assertTrue(any("$.data_metrics_plan: missing required field dashboards" in error for error in errors))
        self.assertTrue(any("$.data_metrics_plan: missing required field evidence_refs" in error for error in errors))
        self.assertTrue(
            any("$.user_docs_onboarding_plan: missing required field gate_enforcement" in error for error in errors)
        )
        self.assertTrue(any("$.user_docs_onboarding_plan: missing required field evidence_refs" in error for error in errors))

    def test_receipt_five_schema_rejects_invalid_transition_event_shapes(self) -> None:
        validator = load_validator()
        schemas = validator.load_schemas()
        schema = schemas["receipt-five.schema.json"]
        receipt = json.loads((ROOT / "templates" / "receipt-five.json").read_text(encoding="utf-8"))

        self.assertEqual(validator.validate_node(schema, receipt, "$", schemas=schemas, root_schema=schema), [])

        invalid = json.loads(json.dumps(receipt))
        invalid["kanban_transition_event"]["from_status"] = ""
        invalid["kanban_transition_event"]["receipt_refs"] = "receipt_five"
        invalid["kanban_transition_event"]["artifact_refs"] = [""]
        invalid["kanban_transition_event"]["allowed"] = "yes"

        errors = validator.validate_node(schema, invalid, "$", schemas=schemas, root_schema=schema)

        self.assertTrue(any("$.kanban_transition_event.from_status" in error and "shorter" in error for error in errors))
        self.assertTrue(any("$.kanban_transition_event.receipt_refs" in error and "expected type array" in error for error in errors))
        self.assertTrue(any("$.kanban_transition_event.artifact_refs[0]" in error and "shorter" in error for error in errors))
        self.assertTrue(any("$.kanban_transition_event.allowed" in error and "expected type boolean" in error for error in errors))

    def test_resolves_schema_file_refs_used_by_factory_card(self) -> None:
        validator = load_validator()
        schemas = validator.load_schemas()
        schema = {"$ref": "product-face-packet.schema.json"}
        valid_packet = {
            "$schema": "https://overkill-factory.dev/schemas/product-face-packet.schema.json",
            "surface": "web_app",
            "mode": "greenfield",
            "user": "operator",
            "job_to_be_done": "understand current state",
            "main_flows": ["inspect status"],
            "required_states": ["ready"],
            "design_direction": {
                "visual_tone": "clear",
                "product_fit": "operator workflow",
                "density": "compact",
                "interaction_style": "direct",
            },
            "visual_quality_bar": {
                "reference_quality_bar": "operator-grade surface",
                "anti_generic_criteria": ["not generic"],
                "professional_review_required": True,
                "block_when": ["generic UI"],
            },
            "proof_required": ["screenshot"],
            "reviewers_required": ["independent-reviewer"],
            "done_definition": ["review passes"],
            "human_gate": {"required": False, "reason": "not material"},
        }
        invalid_packet = dict(valid_packet, surface="software_product")

        self.assertEqual(validator.validate_node(schema, valid_packet, "$", schemas=schemas), [])
        errors = validator.validate_node(schema, invalid_packet, "$", schemas=schemas)
        self.assertTrue(any("$.surface" in error and "not in enum" in error for error in errors))

    def test_product_implementation_readiness_schema_requires_concerns(self) -> None:
        validator = load_validator()
        schemas = validator.load_schemas()
        schema = schemas["product-implementation-readiness.schema.json"]
        readiness = json.loads((ROOT / "templates" / "product-implementation-readiness.json").read_text(encoding="utf-8"))

        self.assertEqual(validator.validate_node(schema, readiness, "$", schemas=schemas, root_schema=schema), [])

        invalid = json.loads(json.dumps(readiness))
        invalid.pop("concern_items")
        errors = validator.validate_node(schema, invalid, "$", schemas=schemas, root_schema=schema)

        self.assertTrue(any("concern_items" in error for error in errors), errors)

    def test_professional_design_process_schema_accepts_controlled_blocked_gate(self) -> None:
        validator = load_validator()
        schemas = validator.load_schemas()
        schema = schemas["professional-design-process.schema.json"]
        process = json.loads((ROOT / "templates" / "professional-design-process.json").read_text(encoding="utf-8"))

        self.assertEqual(validator.validate_node(schema, process, "$", schemas=schemas, root_schema=schema), [])

        invalid = json.loads(json.dumps(process))
        invalid["wireframe_gate"] = {
            "status": "BLOCKED",
            "basis": "Wireframe gate is blocked but lacks a controlled repair route.",
        }
        errors = validator.validate_node(schema, invalid, "$", schemas=schemas, root_schema=schema)

        self.assertTrue(any("$.wireframe_gate" in error and "blocker_id" in error for error in errors), errors)
        self.assertTrue(any("$.wireframe_gate" in error and "owner" in error for error in errors), errors)
        self.assertTrue(any("$.wireframe_gate" in error and "next_action" in error for error in errors), errors)
        self.assertTrue(any("$.wireframe_gate" in error and "proof_refs" in error for error in errors), errors)

    def test_resolves_internal_defs_refs(self) -> None:
        validator = load_validator()
        schema = {
            "$defs": {
                "non_empty_text": {"type": "string", "minLength": 3}
            },
            "type": "object",
            "properties": {
                "summary": {"$ref": "#/$defs/non_empty_text"}
            },
        }

        self.assertEqual(validator.validate_node(schema, {"summary": "ready"}, "$"), [])
        errors = validator.validate_node(schema, {"summary": ""}, "$")
        self.assertTrue(any("$.summary" in error and "shorter than minLength" in error for error in errors))

    def test_project_projection_blocks_impossible_runtime_fresh_state(self) -> None:
        validator = load_validator()
        schemas = validator.load_schemas()
        schema = schemas["project-projection.schema.json"]
        projection = json.loads((ROOT / "templates" / "project-projection.json").read_text(encoding="utf-8"))

        self.assertEqual(validator.validate_node(schema, projection, "$", schemas=schemas, root_schema=schema), [])

        impossible = dict(projection)
        impossible["status"] = "production"
        impossible["execution_started"] = False
        impossible["truth_source_available"] = False
        impossible["source_of_truth"] = dict(projection["source_of_truth"], freshness="stale")
        errors = validator.validate_node(schema, impossible, "$", schemas=schemas, root_schema=schema)

        self.assertTrue(any("execution_started" in error and "expected const True" in error for error in errors))
        self.assertTrue(any("truth_source_available" in error and "expected const True" in error for error in errors))
        self.assertTrue(any("source_of_truth.freshness" in error and "expected const 'runtime_fresh'" in error for error in errors))

    def test_public_ref_hygiene_blocks_raw_kanban_task_ids_recursively(self) -> None:
        validator = load_validator()
        raw_task = "t_" + "ready0001"

        errors = validator.validate_public_ref_hygiene(
            {"evidence_refs": [{"ref": f"Hermes task {raw_task}"}]},
            "$",
        )

        self.assertTrue(any("$.evidence_refs[0].ref" in error for error in errors))
        self.assertEqual(
            validator.validate_public_ref_hygiene({"ref": "kanban:<redacted>", "issue": "github-issue-84"}, "$"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
