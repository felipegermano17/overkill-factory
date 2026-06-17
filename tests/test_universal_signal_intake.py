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
SPEC = importlib.util.spec_from_file_location("factoryctl_universal_signal_intake", MODULE_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl_universal_signal_intake"] = factoryctl
SPEC.loader.exec_module(factoryctl)

VALIDATOR_PATH = ROOT / "scripts" / "validate_public_json_artifacts.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_public_json_artifacts_signal", VALIDATOR_PATH)
assert VALIDATOR_SPEC is not None
public_json_validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
sys.modules["validate_public_json_artifacts_signal"] = public_json_validator
VALIDATOR_SPEC.loader.exec_module(public_json_validator)


def signal_intake() -> dict:
    return json.loads((ROOT / "templates" / "universal-signal-intake.json").read_text(encoding="utf-8"))


class UniversalSignalIntakeTest(unittest.TestCase):
    def test_public_template_validates(self) -> None:
        errors = factoryctl.validate_universal_signal_intake(signal_intake())

        self.assertEqual(errors, [])

    def test_private_signal_ref_is_rejected(self) -> None:
        intake = signal_intake()
        intake["signal"]["signal_ref_public_safe"] = "C:/Users/felip/private/paper.md"

        errors = factoryctl.validate_universal_signal_intake(intake)

        self.assertTrue(any("signal.signal_ref_public_safe" in error for error in errors), errors)

    def test_chat_only_state_is_rejected(self) -> None:
        intake = signal_intake()
        intake["normalization"]["no_chat_only_state"] = False

        errors = factoryctl.validate_universal_signal_intake(intake)

        self.assertTrue(any("no_chat_only_state must be true" in error for error in errors), errors)

    def test_product_creation_route_requires_complete_product_artifacts(self) -> None:
        intake = signal_intake()
        intake["required_artifacts"] = [
            artifact
            for artifact in intake["required_artifacts"]
            if artifact["artifact_type"] != "full_product_sot_scope_coverage"
        ]

        errors = factoryctl.validate_universal_signal_intake(intake)

        self.assertTrue(
            any("product_creation route missing required artifact types" in error for error in errors),
            errors,
        )

    def test_request_type_must_align_with_factory_card(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["request_type"] = "bug"

        errors = factoryctl.validate_card(card)

        self.assertIn(
            "universal_signal_intake.classification.request_type must match card.request_type",
            errors,
        )

    def test_vfinal_card_requires_universal_signal_intake_ref_or_inline_contract(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card.pop("universal_signal_intake_ref", None)
        card.pop("universal_signal_intake", None)

        errors = factoryctl.validate_card(card)

        self.assertIn(
            "universal_signal_intake or universal_signal_intake_ref required for OVERKILL_VFINAL intake routing",
            errors,
        )

    def test_public_validator_applies_signal_intake_domain_rules(self) -> None:
        schemas = public_json_validator.load_schemas()
        schema = schemas["universal-signal-intake.schema.json"]
        intake = signal_intake()
        bad = copy.deepcopy(intake)
        bad["route_decision"]["non_human_block_recovery"]["factory_owned_repair_allowed"] = False

        schema_errors = public_json_validator.validate_node(schema, intake, "$", schemas=schemas, root_schema=schema)
        domain_errors = public_json_validator.validate_domain_rules(intake, "$")
        bad_domain_errors = public_json_validator.validate_domain_rules(bad, "$")

        self.assertEqual(schema_errors + domain_errors, [])
        self.assertTrue(
            any("non-human block must return to a factory-owned repair route" in error for error in bad_domain_errors),
            bad_domain_errors,
        )

    def test_factoryctl_and_public_validator_route_artifact_matrix_stay_in_sync(self) -> None:
        self.assertEqual(
            factoryctl.UNIVERSAL_SIGNAL_ROUTE_REQUIRED_ARTIFACTS,
            public_json_validator.UNIVERSAL_SIGNAL_ROUTE_REQUIRED_ARTIFACTS,
        )

    def test_factoryctl_cli_validates_signal_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "signal-intake.json"
            path.write_text(json.dumps(signal_intake()), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(["validate-signal-intake", str(path)])

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
