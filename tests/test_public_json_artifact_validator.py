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


if __name__ == "__main__":
    unittest.main()
