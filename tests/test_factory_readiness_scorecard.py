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


def scorecard() -> dict:
    return json.loads((ROOT / "templates" / "factory-readiness-scorecard.json").read_text(encoding="utf-8"))


def make_all_pass(card: dict) -> dict:
    card = copy.deepcopy(card)
    card["verdict"] = "ready_for_autonomy"
    card["maturity_level"]["level"] = 5
    card["remediation_loop"]["required"] = False
    card["autonomy_boundary"]["autonomous_execution_allowed"] = True
    card["autonomy_boundary"]["allowed_scope"] = "material_execution"
    card["autonomy_boundary"]["bounded_remediation_allowed"] = False
    card["autonomy_boundary"]["material_autonomous_execution_allowed"] = True
    for dimension in card["dimensions"]:
        dimension["status"] = "PASS"
        dimension["severity"] = "none"
        dimension["blocks_autonomous_execution"] = False
        dimension["remediation_target_ref"] = "not_required"
    return card


def make_blocked(card: dict) -> dict:
    card = copy.deepcopy(card)
    card["verdict"] = "blocked"
    card["remediation_loop"]["required"] = True
    card["autonomy_boundary"]["autonomous_execution_allowed"] = False
    card["autonomy_boundary"]["allowed_scope"] = "none"
    card["autonomy_boundary"]["bounded_remediation_allowed"] = False
    card["autonomy_boundary"]["material_autonomous_execution_allowed"] = False
    dimension = card["dimensions"][0]
    dimension["status"] = "BLOCKED"
    dimension["severity"] = "high"
    dimension["blocks_autonomous_execution"] = True
    dimension["remediation_target_ref"] = "templates/platform-devex-plan.json"
    return card


class FactoryReadinessScorecardTest(unittest.TestCase):
    def test_public_template_validates_as_bounded(self) -> None:
        errors = factoryctl.validate_factory_readiness_scorecard(scorecard())

        self.assertEqual(errors, [])

    def test_green_scorecard_validates(self) -> None:
        errors = factoryctl.validate_factory_readiness_scorecard(make_all_pass(scorecard()))

        self.assertEqual(errors, [])

    def test_remediation_required_scorecard_validates(self) -> None:
        card = scorecard()
        card["verdict"] = "remediation_required"
        card["autonomy_boundary"]["allowed_scope"] = "bounded_remediation"
        card["autonomy_boundary"]["material_autonomous_execution_allowed"] = False

        errors = factoryctl.validate_factory_readiness_scorecard(card)

        self.assertEqual(errors, [])

    def test_blocked_scorecard_validates(self) -> None:
        errors = factoryctl.validate_factory_readiness_scorecard(make_blocked(scorecard()))

        self.assertEqual(errors, [])

    def test_missing_required_dimension_is_rejected(self) -> None:
        card = scorecard()
        card["dimensions"] = [dimension for dimension in card["dimensions"] if dimension["dimension_id"] != "build_install_health"]

        errors = factoryctl.validate_factory_readiness_scorecard(card)

        self.assertTrue(any("missing required dimension build_install_health" in error for error in errors), errors)

    def test_duplicate_dimension_is_rejected(self) -> None:
        card = scorecard()
        card["dimensions"].append(copy.deepcopy(card["dimensions"][0]))

        errors = factoryctl.validate_factory_readiness_scorecard(card)

        self.assertTrue(any("duplicate dimension build_install_health" in error for error in errors), errors)

    def test_private_evidence_ref_is_rejected(self) -> None:
        card = scorecard()
        card["dimensions"][0]["evidence_refs"] = ["C:/Users/felip/private/proof.json"]

        errors = factoryctl.validate_factory_readiness_scorecard(card)

        self.assertTrue(any("dimensions[0].evidence_refs" in error for error in errors), errors)

    def test_ready_for_autonomy_requires_all_dimensions_pass(self) -> None:
        card = scorecard()
        card["verdict"] = "ready_for_autonomy"
        card["autonomy_boundary"]["allowed_scope"] = "material_execution"
        card["autonomy_boundary"]["material_autonomous_execution_allowed"] = True

        errors = factoryctl.validate_factory_readiness_scorecard(card)

        self.assertTrue(any("ready_for_autonomy requires all dimensions PASS" in error for error in errors), errors)

    def test_blocking_dimension_requires_blocked_verdict(self) -> None:
        card = scorecard()
        card["dimensions"][0]["status"] = "BLOCKED"
        card["dimensions"][0]["severity"] = "high"
        card["dimensions"][0]["blocks_autonomous_execution"] = True
        card["dimensions"][0]["remediation_target_ref"] = "templates/platform-devex-plan.json"

        errors = factoryctl.validate_factory_readiness_scorecard(card)

        self.assertTrue(any("blocking dimensions require verdict=blocked" in error for error in errors), errors)

    def test_blocked_verdict_requires_blocking_dimension(self) -> None:
        card = scorecard()
        card["verdict"] = "blocked"
        card["autonomy_boundary"]["autonomous_execution_allowed"] = False
        card["autonomy_boundary"]["allowed_scope"] = "none"
        card["autonomy_boundary"]["bounded_remediation_allowed"] = False
        card["autonomy_boundary"]["material_autonomous_execution_allowed"] = False

        errors = factoryctl.validate_factory_readiness_scorecard(card)

        self.assertTrue(any("verdict=blocked requires at least one blocking dimension" in error for error in errors), errors)

    def test_non_pass_requires_remediation_loop(self) -> None:
        card = scorecard()
        card["remediation_loop"]["required"] = False

        errors = factoryctl.validate_factory_readiness_scorecard(card)

        self.assertTrue(any("non-PASS dimensions require remediation_loop.required=true" in error for error in errors), errors)

    def test_public_validator_applies_scorecard_domain_rules(self) -> None:
        schemas = public_json_validator.load_schemas()
        schema = schemas["factory-readiness-scorecard.schema.json"]
        card = scorecard()
        bad = copy.deepcopy(card)
        bad["verdict"] = "ready_for_autonomy"
        bad["autonomy_boundary"]["allowed_scope"] = "material_execution"
        bad["autonomy_boundary"]["material_autonomous_execution_allowed"] = True

        schema_errors = public_json_validator.validate_node(schema, card, "$", schemas=schemas, root_schema=schema)
        domain_errors = public_json_validator.validate_domain_rules(card, "$")
        bad_domain_errors = public_json_validator.validate_domain_rules(bad, "$")

        self.assertEqual(schema_errors + domain_errors, [])
        self.assertTrue(any("ready_for_autonomy requires all dimensions PASS" in error for error in bad_domain_errors), bad_domain_errors)

    def test_ready_with_bounds_with_remediation_cannot_allow_material_autonomy(self) -> None:
        card = scorecard()
        card["autonomy_boundary"]["allowed_scope"] = "material_execution"
        card["autonomy_boundary"]["bounded_remediation_allowed"] = False
        card["autonomy_boundary"]["material_autonomous_execution_allowed"] = True

        errors = factoryctl.validate_factory_readiness_scorecard(card)

        self.assertIn(
            "factory_readiness_scorecard ready_with_bounds with remediation cannot allow material autonomous execution",
            errors,
        )
        self.assertIn(
            "factory_readiness_scorecard ready_with_bounds with remediation cannot use allowed_scope=material_execution",
            errors,
        )
        self.assertIn(
            "factory_readiness_scorecard ready_with_bounds with remediation requires bounded_remediation_allowed=true",
            errors,
        )

    def test_remediation_loop_requires_finite_budget_when_required(self) -> None:
        card = scorecard()
        card["remediation_loop"].pop("max_remediation_attempts", None)
        card["remediation_loop"].pop("timeout_minutes", None)
        card["remediation_loop"].pop("stop_condition", None)

        errors = factoryctl.validate_factory_readiness_scorecard(card)

        self.assertIn(
            "factory_readiness_scorecard remediation_loop.required=true requires max_remediation_attempts",
            errors,
        )
        self.assertIn(
            "factory_readiness_scorecard remediation_loop.required=true requires timeout_minutes",
            errors,
        )
        self.assertIn(
            "factory_readiness_scorecard remediation_loop.required=true requires stop_condition",
            errors,
        )

    def test_factoryctl_cli_validates_scorecard(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scorecard.json"
            path.write_text(json.dumps(scorecard()), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(["validate-readiness-scorecard", str(path)])

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
