from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factoryctl.py"
SPEC = importlib.util.spec_from_file_location("factoryctl_method_engines", MODULE_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl_method_engines"] = factoryctl
SPEC.loader.exec_module(factoryctl)


def signal_intake() -> dict:
    return json.loads((ROOT / "templates" / "universal-signal-intake.json").read_text(encoding="utf-8"))


def build_valid_method_contract() -> dict:
    source_resolution = factoryctl.build_source_resolution_packet(
        signal_intake(),
        intake_ref_public_safe="external:sanitized-universal-signal-intake",
    )
    ledger = factoryctl.build_product_source_ledger(
        source_resolution,
        source_ref_public_safe="external:sanitized-product-brief",
    )
    outcome = factoryctl.build_outcome_contract(
        ledger,
        operator_understanding_confirmation_ref="external:operator-understanding-confirmed",
    )
    product_sot = factoryctl.build_product_sot(outcome)
    coverage = factoryctl.build_full_scope_coverage(product_sot)
    return factoryctl.build_method_contract(coverage)


class MethodEnginesTest(unittest.TestCase):
    def test_method_engine_registry_template_validates(self) -> None:
        registry = factoryctl.load_json_like(ROOT / "templates" / "method-engine-registry.json")

        self.assertEqual([], factoryctl.validate_method_engine_registry(registry))

    def test_method_contract_materializes_selected_engines(self) -> None:
        contract = build_valid_method_contract()
        engine_ids = {engine["engine_id"] for engine in contract["selected_method_engines"]}

        self.assertEqual([], factoryctl.validate_method_contract(contract))
        self.assertIn("spec_first_sdd", engine_ids)
        self.assertIn("test_first_tdd", engine_ids)
        self.assertFalse(any(engine["execution_allowed_by_engine_selection"] for engine in contract["selected_method_engines"]))

    def test_method_contract_rejects_selected_method_without_engine(self) -> None:
        contract = build_valid_method_contract()
        contract["selected_method_engines"] = [
            engine
            for engine in contract["selected_method_engines"]
            if engine["method"] != "test-first"
        ]

        errors = factoryctl.validate_method_contract(contract)

        self.assertTrue(any("test-first" in error and "selected_method_engine" in error for error in errors), errors)

    def test_method_engine_selection_does_not_allow_execution(self) -> None:
        contract = build_valid_method_contract()
        contract["selected_method_engines"][0]["execution_allowed_by_engine_selection"] = True

        errors = factoryctl.validate_method_contract(contract)

        self.assertTrue(any("execution_allowed_by_engine_selection" in error for error in errors), errors)

    def test_method_engines_cli_emits_single_engine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "engine.json"
            old_argv = sys.argv[:]
            sys.argv = [
                "factoryctl",
                "method-engines",
                "--engine-id",
                "spec_first_sdd",
                "--out",
                str(out),
            ]
            try:
                code = factoryctl.main()
            finally:
                sys.argv = old_argv

            self.assertEqual(0, code)
            emitted = factoryctl.load_json_like(out)
            self.assertEqual("spec_first_sdd", emitted["engine_id"])


if __name__ == "__main__":
    unittest.main()
