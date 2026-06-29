import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]

FACTORYCTL_PATH = ROOT / "scripts" / "factoryctl.py"
FACTORYCTL_SPEC = importlib.util.spec_from_file_location("factoryctl_route_registry", FACTORYCTL_PATH)
assert FACTORYCTL_SPEC is not None
factoryctl = importlib.util.module_from_spec(FACTORYCTL_SPEC)
assert FACTORYCTL_SPEC.loader is not None
sys.modules["factoryctl_route_registry"] = factoryctl
FACTORYCTL_SPEC.loader.exec_module(factoryctl)

import factory_route_registry as route_registry_module  # noqa: E402

VALIDATOR_PATH = ROOT / "scripts" / "validate_public_json_artifacts.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_public_json_artifacts_routes", VALIDATOR_PATH)
assert VALIDATOR_SPEC is not None
public_json_validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
sys.modules["validate_public_json_artifacts_routes"] = public_json_validator
VALIDATOR_SPEC.loader.exec_module(public_json_validator)

ROUTE_REGISTRY_PATH = ROOT / "templates" / "factory-route-registry.json"
GOLDEN_CORPUS_PATH = ROOT / "templates" / "universal-signal-golden-corpus.json"


def route_registry() -> dict:
    return json.loads(ROUTE_REGISTRY_PATH.read_text(encoding="utf-8"))


def golden_corpus() -> dict:
    return json.loads(GOLDEN_CORPUS_PATH.read_text(encoding="utf-8"))


class FactoryRouteRegistryTest(unittest.TestCase):
    def test_route_registry_template_validates_against_schema(self) -> None:
        schemas = public_json_validator.load_schemas()
        schema = schemas["factory-route-registry.schema.json"]

        errors = public_json_validator.validate_node(schema, route_registry(), "$", schemas=schemas, root_schema=schema)

        self.assertEqual(errors, [])

    def test_route_registry_loader_finds_installed_data_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            installed_data = temp_root / "install-root"
            installed_registry = installed_data / "share" / "overkill-factory" / "templates" / "factory-route-registry.json"
            installed_registry.parent.mkdir(parents=True)
            installed_registry.write_text(ROUTE_REGISTRY_PATH.read_text(encoding="utf-8"), encoding="utf-8")

            with mock.patch.object(route_registry_module, "DEFAULT_ROUTE_REGISTRY_PATH", temp_root / "missing.json"):
                with mock.patch.object(route_registry_module, "ROOT", temp_root / "site-packages"):
                    with mock.patch.object(route_registry_module.sysconfig, "get_path", return_value=str(installed_data)):
                        loaded = route_registry_module.load_route_registry()

        self.assertEqual(loaded["record_type"], "factory_route_registry")
        self.assertEqual(
            {route["route_class"] for route in loaded["routes"]},
            {route["route_class"] for route in route_registry()["routes"]},
        )

    def test_route_registry_is_single_source_for_factoryctl_and_public_validator(self) -> None:
        expected_artifacts = factoryctl.route_required_artifacts()
        expected_request_types = factoryctl.route_request_types()

        self.assertEqual(factoryctl.UNIVERSAL_SIGNAL_ROUTE_REQUIRED_ARTIFACTS, expected_artifacts)
        self.assertEqual(public_json_validator.UNIVERSAL_SIGNAL_ROUTE_REQUIRED_ARTIFACTS, expected_artifacts)
        self.assertEqual(factoryctl.UNIVERSAL_SIGNAL_ROUTE_REQUEST_TYPES, expected_request_types)
        self.assertEqual(public_json_validator.UNIVERSAL_SIGNAL_ROUTE_REQUEST_TYPES, expected_request_types)

    def test_route_classes_match_universal_signal_intake_schema(self) -> None:
        schemas = public_json_validator.load_schemas()
        intake_schema = schemas["universal-signal-intake.schema.json"]
        route_enum = set(intake_schema["properties"]["classification"]["properties"]["route_class"]["enum"])
        registry_route_classes = {route["route_class"] for route in route_registry()["routes"]}

        self.assertEqual(registry_route_classes, route_enum)

    def test_registry_workers_exist_in_public_worker_registry(self) -> None:
        worker_registry = json.loads((ROOT / "agents" / "worker-registry.public.json").read_text(encoding="utf-8"))
        worker_ids = {worker["worker_id"] for worker in worker_registry["workers"]}

        missing = sorted(
            worker_id
            for route in route_registry()["routes"]
            for worker_id in route["required_workers"]
            if worker_id not in worker_ids
        )

        self.assertEqual(missing, [])

    def test_all_routes_keep_hermes_as_runtime_authority(self) -> None:
        for route in route_registry()["routes"]:
            with self.subTest(route_class=route["route_class"]):
                self.assertEqual(route["hermes_boundary"]["runtime_authority"], "hermes_kanban")
                self.assertTrue(route["hermes_boundary"]["uses_native_kanban_primitives"])
                self.assertFalse(route["hermes_boundary"]["local_state_authority"])
                self.assertEqual(route["recovery_policy"]["runtime_authority"], "hermes_kanban")
                self.assertFalse(route["recovery_policy"]["local_state_authority"])

    def test_signal_intake_rejects_route_registry_mismatch(self) -> None:
        intake = json.loads((ROOT / "templates" / "universal-signal-intake.json").read_text(encoding="utf-8"))
        intake["signal"]["signal_type"] = "bug_report"
        intake["route_decision"]["selected_method_family"] = "test_first"
        intake["required_workers"] = []

        errors = factoryctl.validate_universal_signal_intake(intake)

        self.assertIn(
            "universal_signal_intake.signal.signal_type is not valid for route_class product_creation: bug_report",
            errors,
        )
        self.assertIn(
            "universal_signal_intake.route_decision.selected_method_family must match route registry for product_creation: spec_first",
            errors,
        )
        self.assertTrue(any("product_creation route missing required workers" in error for error in errors), errors)

    def test_route_registry_cli_outputs_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "route.json"

            result = factoryctl.main_with_args_for_test(["route-registry", "--route-class", "bug_repair", "--out", str(out)])
            route = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(route["route_class"], "bug_repair")

    def test_intake_cli_generates_valid_signal_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "bug-intake.json"

            result = factoryctl.main_with_args_for_test(
                [
                    "intake",
                    "--route-class",
                    "bug_repair",
                    "--request-type",
                    "bug",
                    "--signal-type",
                    "bug_report",
                    "--summary",
                    "Public-safe bug report must enter the factory through reproduction and regression gates.",
                    "--source-ref",
                    "external:source-card-bug-report-001",
                    "--target-surface",
                    "existing-product",
                    "--created-at",
                    "2026-06-17T00:00:00+00:00",
                    "--out",
                    str(out),
                ]
            )

            generated = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(factoryctl.validate_universal_signal_intake(generated), [])
        self.assertEqual(generated["classification"]["route_class"], "bug_repair")
        self.assertFalse(generated["acceptance"]["execution_allowed"])

    def test_golden_corpus_validates_and_covers_all_routes(self) -> None:
        errors = factoryctl.validate_universal_signal_golden_corpus(golden_corpus())
        scorecard = factoryctl.build_factory_signal_coverage_scorecard(golden_corpus())

        self.assertEqual(errors, [])
        self.assertEqual(scorecard["result"], "PASS")
        self.assertEqual(scorecard["route_count"], scorecard["covered_route_count"])
        self.assertEqual(scorecard["missing_route_classes"], [])
        self.assertEqual(factoryctl.validate_factory_signal_coverage_scorecard(scorecard), [])

    def test_golden_corpus_rejects_missing_recovery_invariant(self) -> None:
        corpus = golden_corpus()
        corpus["cases"][0]["expected_recovery_policy"]["factory_owned_repair_allowed"] = False

        errors = factoryctl.validate_universal_signal_golden_corpus(corpus)
        scorecard = factoryctl.build_factory_signal_coverage_scorecard(corpus)

        self.assertTrue(any("recovery invariant must be factory-owned" in error for error in errors), errors)
        self.assertEqual(scorecard["result"], "BLOCKED")

    def test_signal_coverage_cli_writes_pass_scorecard(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "signal-coverage.json"

            result = factoryctl.main_with_args_for_test(["signal-coverage", "--out", str(out)])
            scorecard = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(scorecard["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
