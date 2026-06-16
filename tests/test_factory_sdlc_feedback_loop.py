from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
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

VALIDATOR_PATH = ROOT / "scripts" / "validate_public_json_artifacts.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_public_json_artifacts", VALIDATOR_PATH)
assert VALIDATOR_SPEC is not None
public_json_validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
sys.modules["validate_public_json_artifacts"] = public_json_validator
VALIDATOR_SPEC.loader.exec_module(public_json_validator)


def feedback_loop() -> dict:
    return json.loads((ROOT / "templates" / "factory-sdlc-feedback-loop.json").read_text(encoding="utf-8"))


class FactorySdlcFeedbackLoopTest(unittest.TestCase):
    def test_public_template_validates(self) -> None:
        loop = feedback_loop()

        errors = factoryctl.validate_factory_sdlc_feedback_loop(loop)

        self.assertEqual(errors, [])

    def test_missing_route_is_rejected_by_schema(self) -> None:
        loop = feedback_loop()
        del loop["triage_decision"]["route_ref"]

        errors = factoryctl.validate_factory_sdlc_feedback_loop(loop)

        self.assertTrue(any("route_ref" in error for error in errors), errors)

    def test_private_signal_ref_is_rejected(self) -> None:
        loop = feedback_loop()
        loop["source_signal"]["signal_ref_public_safe"] = "C:/Users/felip/private/signal.json"

        errors = factoryctl.validate_factory_sdlc_feedback_loop(loop)

        self.assertTrue(any("source_signal.signal_ref_public_safe" in error for error in errors), errors)

    def test_secret_class_signal_is_rejected(self) -> None:
        loop = feedback_loop()
        loop["source_signal"]["sensitivity_class"] = "secret"

        errors = factoryctl.validate_factory_sdlc_feedback_loop(loop)

        self.assertTrue(any("secret-class" in error for error in errors), errors)

    def test_single_provider_routing_is_rejected(self) -> None:
        loop = feedback_loop()
        loop["routing_decision"]["model_independence_preserved"] = False
        loop["routing_decision"]["single_provider_assumption"] = True

        errors = factoryctl.validate_factory_sdlc_feedback_loop(loop)

        self.assertTrue(any("preserve model independence" in error for error in errors), errors)
        self.assertTrue(any("single provider" in error for error in errors), errors)

    def test_failed_outputs_cannot_be_consumable_as_success(self) -> None:
        loop = feedback_loop()
        loop["execution_evidence"]["failed_outputs_consumable_as_success"] = True

        errors = factoryctl.validate_factory_sdlc_feedback_loop(loop)

        self.assertTrue(any("failed outputs cannot be consumed" in error for error in errors), errors)

    def test_non_rejected_learnback_requires_actionable_target(self) -> None:
        loop = feedback_loop()
        loop["learnback_decision"]["target_artifact_type"] = "none"

        errors = factoryctl.validate_factory_sdlc_feedback_loop(loop)

        self.assertTrue(any("learnback requires an actionable target" in error for error in errors), errors)

    def test_rejected_learnback_must_not_target_artifact(self) -> None:
        loop = feedback_loop()
        loop["learnback_decision"]["classification"] = "reject"
        loop["learnback_decision"]["promotion_boundary"] = "rejected"
        loop["learnback_decision"]["target_artifact_type"] = "schema"

        errors = factoryctl.validate_factory_sdlc_feedback_loop(loop)

        self.assertTrue(any("rejected learnback must use target_artifact_type=none" in error for error in errors), errors)

    def test_public_validator_applies_feedback_loop_domain_rules(self) -> None:
        schemas = public_json_validator.load_schemas()
        schema = schemas["factory-sdlc-feedback-loop.schema.json"]
        loop = feedback_loop()
        bad = copy.deepcopy(loop)
        bad["learnback_decision"]["target_artifact_type"] = "none"

        schema_errors = public_json_validator.validate_node(schema, loop, "$", schemas=schemas, root_schema=schema)
        domain_errors = public_json_validator.validate_domain_rules(loop, "$")
        bad_domain_errors = public_json_validator.validate_domain_rules(bad, "$")

        self.assertEqual(schema_errors + domain_errors, [])
        self.assertTrue(any("learnback requires an actionable target" in error for error in bad_domain_errors), bad_domain_errors)

    def test_factoryctl_cli_validates_feedback_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "feedback-loop.json"
            path.write_text(json.dumps(feedback_loop()), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(["validate-sdlc-feedback-loop", str(path)])

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
