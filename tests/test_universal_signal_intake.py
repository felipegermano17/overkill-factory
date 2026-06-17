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


def build_valid_method_contract() -> dict:
    source_resolution = factoryctl.build_source_resolution_packet(
        signal_intake(),
        intake_ref_public_safe="external:sanitized-universal-signal-intake",
    )
    ledger = factoryctl.build_product_source_ledger(
        source_resolution,
        source_ref_public_safe="external:sanitized-product-brief",
    )
    outcome = factoryctl.build_outcome_contract(ledger)
    product_sot = factoryctl.build_product_sot(outcome)
    coverage = factoryctl.build_full_scope_coverage(product_sot)
    return factoryctl.build_method_contract(coverage)


def build_valid_product_creation_plan() -> dict:
    return factoryctl.build_product_creation_plan(build_valid_method_contract())


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

    def test_source_resolution_packet_from_intake_is_valid(self) -> None:
        intake = signal_intake()

        packet = factoryctl.build_source_resolution_packet(
            intake,
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )

        self.assertEqual(factoryctl.validate_source_resolution_packet(packet), [])
        self.assertEqual(public_json_validator.validate_domain_rules(packet, "$"), [])
        self.assertEqual(packet["record_type"], "source_resolution_packet")
        self.assertEqual(packet["source_signal"]["intake_id"], intake["intake_id"])
        self.assertEqual(packet["handoff"]["next_artifact"], "source_ledger")
        self.assertTrue(packet["handoff"]["factory_owned_next_step"])

    def test_source_resolution_packet_keeps_product_sot_uncreated(self) -> None:
        packet = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )

        self.assertFalse(packet["acceptance"]["product_sot_generated"])
        self.assertFalse(packet["acceptance"]["execution_allowed"])
        self.assertTrue(packet["blocking_rules"]["product_sot_worker_required"])
        product_sot_artifacts = [
            artifact for artifact in packet["next_artifacts"] if artifact["artifact_type"] == "product_sot"
        ]
        self.assertEqual(len(product_sot_artifacts), 1)
        self.assertEqual(product_sot_artifacts[0]["status"], "pending_factory_worker")

    def test_source_resolution_packet_does_not_require_product_sot_for_bug_route(self) -> None:
        intake = factoryctl.build_universal_signal_intake(
            route_class="bug_repair",
            request_type="bug",
            signal_type="bug_report",
            summary_public_safe="Representative bug signal should enter source resolution without Product SOT.",
            signal_ref_public_safe="external:sanitized-bug-signal",
            target_surface="bug-target",
            owner="factory-orchestrator",
            source_class="operator_supplied",
            sensitivity_class="public_safe",
            freshness="fresh",
            risk_initial="R2",
            materiality="material",
            created_at="2026-06-17T00:00:00+00:00",
            intake_id="intake-bug-repair",
        )

        packet = factoryctl.build_source_resolution_packet(
            intake,
            intake_ref_public_safe="external:sanitized-bug-intake",
        )

        self.assertFalse(packet["source_signal"]["needs_product_sot"])
        self.assertFalse(packet["blocking_rules"]["product_sot_worker_required"])
        self.assertFalse(any(artifact["artifact_type"] == "product_sot" for artifact in packet["next_artifacts"]))

    def test_source_resolution_packet_rejects_invalid_intake(self) -> None:
        intake = signal_intake()
        intake["normalization"]["source_resolution_required"] = False

        with self.assertRaisesRegex(ValueError, "source_resolution_required"):
            factoryctl.build_source_resolution_packet(
                intake,
                intake_ref_public_safe="external:sanitized-universal-signal-intake",
            )

    def test_source_resolution_cli_generates_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            intake_path = Path(tmpdir) / "signal-intake.json"
            out_path = Path(tmpdir) / "source-resolution-packet.json"
            intake_path.write_text(json.dumps(signal_intake()), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(
                [
                    "source-resolution",
                    "--intake",
                    str(intake_path),
                    "--intake-ref",
                    "external:sanitized-universal-signal-intake",
                    "--out",
                    str(out_path),
                ]
            )

            packet = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(packet["record_type"], "source_resolution_packet")
        self.assertEqual(factoryctl.validate_source_resolution_packet(packet), [])

    def test_source_resolution_runner_covers_representative_signal_routes(self) -> None:
        cases = [
            ("product_creation", "product_new", "product_paper"),
            ("ux_product_experience", "ux_ui", "ux_ui_request"),
            ("bug_repair", "bug", "bug_report"),
            ("incident_response", "incident", "incident"),
            ("feature_delivery", "feature", "feature_idea"),
        ]

        for route_class, request_type, signal_type in cases:
            with self.subTest(route_class=route_class):
                intake = factoryctl.build_universal_signal_intake(
                    route_class=route_class,
                    request_type=request_type,
                    signal_type=signal_type,
                    summary_public_safe=f"Representative {route_class} signal for source resolution runner coverage.",
                    signal_ref_public_safe=f"external:sanitized-{route_class}-signal",
                    target_surface=f"{route_class}-target",
                    owner="factory-orchestrator",
                    source_class="operator_supplied",
                    sensitivity_class="public_safe",
                    freshness="fresh",
                    risk_initial="R2",
                    materiality="material",
                    created_at="2026-06-17T00:00:00+00:00",
                    intake_id=f"intake-{route_class}",
                )

                packet = factoryctl.build_source_resolution_packet(
                    intake,
                    intake_ref_public_safe=f"external:sanitized-{route_class}-intake",
                )

                self.assertEqual(factoryctl.validate_source_resolution_packet(packet), [])
                self.assertTrue(packet["handoff"]["factory_owned_next_step"])
                self.assertFalse(packet["acceptance"]["execution_allowed"])
                self.assertEqual(packet["blocking_rules"]["source_resolution_required"], True)

    def test_product_source_ledger_from_source_resolution_is_valid(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )

        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )

        self.assertEqual(factoryctl.validate_product_source_ledger(ledger), [])
        self.assertEqual(public_json_validator.validate_domain_rules(ledger, "$"), [])
        self.assertEqual(ledger["record_type"], "product_source_ledger")
        self.assertEqual(ledger["source_resolution_ref"], source_resolution["packet_id"])
        self.assertEqual(ledger["handoff"]["next_artifact"], "outcome_contract")
        self.assertEqual(ledger["handoff"]["next_worker"], "product-sot-planner")
        self.assertFalse(ledger["acceptance"]["product_sot_generated"])
        self.assertFalse(ledger["acceptance"]["execution_allowed"])

    def test_product_source_ledger_requires_valid_source_resolution_packet(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        source_resolution["acceptance"]["execution_allowed"] = True

        with self.assertRaisesRegex(ValueError, "execution_allowed"):
            factoryctl.build_product_source_ledger(
                source_resolution,
                source_ref_public_safe="external:sanitized-product-brief",
            )

    def test_product_source_ledger_cli_generates_public_safe_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_resolution_path = Path(tmpdir) / "source-resolution-packet.json"
            out_path = Path(tmpdir) / "product-source-ledger.json"
            source_resolution = factoryctl.build_source_resolution_packet(
                signal_intake(),
                intake_ref_public_safe="external:sanitized-universal-signal-intake",
            )
            source_resolution_path.write_text(json.dumps(source_resolution), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(
                [
                    "source-ledger",
                    "--source-resolution",
                    str(source_resolution_path),
                    "--source-ref",
                    "external:sanitized-product-brief",
                    "--out",
                    str(out_path),
                ]
            )

            ledger = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(ledger["record_type"], "product_source_ledger")
        self.assertEqual(factoryctl.validate_product_source_ledger(ledger), [])

    def test_product_source_ledger_for_bug_route_does_not_route_to_product_sot(self) -> None:
        intake = factoryctl.build_universal_signal_intake(
            route_class="bug_repair",
            request_type="bug",
            signal_type="bug_report",
            summary_public_safe="Representative bug signal should create source ledger without Product SOT.",
            signal_ref_public_safe="external:sanitized-bug-signal",
            target_surface="bug-target",
            owner="factory-orchestrator",
            source_class="operator_supplied",
            sensitivity_class="public_safe",
            freshness="fresh",
            risk_initial="R2",
            materiality="material",
            created_at="2026-06-17T00:00:00+00:00",
            intake_id="intake-bug-repair",
        )
        source_resolution = factoryctl.build_source_resolution_packet(
            intake,
            intake_ref_public_safe="external:sanitized-bug-intake",
        )

        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-bug-report",
        )

        self.assertFalse(ledger["source_signal"]["needs_product_sot"])
        self.assertEqual(ledger["handoff"]["next_artifact"], "bug_reproduction")
        self.assertNotEqual(ledger["handoff"]["next_worker"], "product-sot-planner")

    def test_outcome_contract_from_product_source_ledger_is_valid(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )

        outcome = factoryctl.build_outcome_contract(ledger)

        self.assertEqual(factoryctl.validate_outcome_contract(outcome), [])
        self.assertEqual(public_json_validator.validate_domain_rules(outcome, "$"), [])
        self.assertEqual(outcome["record_type"], "outcome_contract")
        self.assertEqual(outcome["source_ledger_ref"], ledger["ledger_id"])
        self.assertEqual(outcome["handoff"]["next_artifact"], "product_sot")
        self.assertEqual(outcome["handoff"]["next_worker"], "product-sot-planner")
        self.assertFalse(outcome["acceptance"]["product_sot_generated"])
        self.assertFalse(outcome["acceptance"]["execution_allowed"])

    def test_outcome_contract_requires_valid_source_ledger(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        ledger["acceptance"]["execution_allowed"] = True

        with self.assertRaisesRegex(ValueError, "execution_allowed"):
            factoryctl.build_outcome_contract(ledger)

    def test_outcome_contract_cli_generates_public_safe_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "product-source-ledger.json"
            out_path = Path(tmpdir) / "outcome-contract.json"
            source_resolution = factoryctl.build_source_resolution_packet(
                signal_intake(),
                intake_ref_public_safe="external:sanitized-universal-signal-intake",
            )
            ledger = factoryctl.build_product_source_ledger(
                source_resolution,
                source_ref_public_safe="external:sanitized-product-brief",
            )
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(
                [
                    "outcome-contract",
                    "--source-ledger",
                    str(ledger_path),
                    "--out",
                    str(out_path),
                ]
            )

            outcome = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(outcome["record_type"], "outcome_contract")
        self.assertEqual(factoryctl.validate_outcome_contract(outcome), [])

    def test_outcome_contract_for_bug_route_does_not_generate_product_sot(self) -> None:
        intake = factoryctl.build_universal_signal_intake(
            route_class="bug_repair",
            request_type="bug",
            signal_type="bug_report",
            summary_public_safe="Representative bug signal should produce an outcome before reproduction.",
            signal_ref_public_safe="external:sanitized-bug-signal",
            target_surface="bug-target",
            owner="factory-orchestrator",
            source_class="operator_supplied",
            sensitivity_class="public_safe",
            freshness="fresh",
            risk_initial="R2",
            materiality="material",
            created_at="2026-06-17T00:00:00+00:00",
            intake_id="intake-bug-repair",
        )
        source_resolution = factoryctl.build_source_resolution_packet(
            intake,
            intake_ref_public_safe="external:sanitized-bug-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-bug-report",
        )

        outcome = factoryctl.build_outcome_contract(ledger)

        self.assertFalse(outcome["source_signal"]["needs_product_sot"])
        self.assertEqual(outcome["handoff"]["next_artifact"], "bug_reproduction")
        self.assertFalse(outcome["acceptance"]["product_sot_generated"])
        self.assertFalse(outcome["acceptance"]["execution_allowed"])

    def test_product_sot_from_outcome_contract_is_valid(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        outcome = factoryctl.build_outcome_contract(ledger)

        product_sot = factoryctl.build_product_sot(outcome)

        self.assertEqual(factoryctl.validate_product_sot(product_sot), [])
        self.assertEqual(public_json_validator.validate_domain_rules(product_sot, "$"), [])
        self.assertEqual(product_sot["record_type"], "product_sot")
        self.assertEqual(product_sot["outcome_contract_ref"], outcome["contract_id"])
        self.assertEqual(product_sot["handoff"]["next_artifact"], "full_product_sot_scope_coverage")
        self.assertEqual(product_sot["handoff"]["next_worker"], "product-sot-planner")
        self.assertFalse(product_sot["acceptance"]["execution_allowed"])
        self.assertTrue(product_sot["blocking_rules"]["full_scope_coverage_required"])

    def test_product_sot_requires_valid_outcome_contract(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        outcome = factoryctl.build_outcome_contract(ledger)
        outcome["acceptance"]["execution_allowed"] = True

        with self.assertRaisesRegex(ValueError, "execution_allowed"):
            factoryctl.build_product_sot(outcome)

    def test_product_sot_cli_generates_public_safe_sot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            outcome_path = Path(tmpdir) / "outcome-contract.json"
            material_path = Path(tmpdir) / "source-material.md"
            out_path = Path(tmpdir) / "product-sot.json"
            source_resolution = factoryctl.build_source_resolution_packet(
                signal_intake(),
                intake_ref_public_safe="external:sanitized-universal-signal-intake",
            )
            ledger = factoryctl.build_product_source_ledger(
                source_resolution,
                source_ref_public_safe="external:sanitized-product-brief",
            )
            outcome = factoryctl.build_outcome_contract(ledger)
            outcome_path.write_text(json.dumps(outcome), encoding="utf-8")
            material_path.write_text(
                "\n".join(
                    [
                        "# Saude da fabrica",
                        "- status de public/secret safety scans;",
                    ]
                ),
                encoding="utf-8",
            )

            result = factoryctl.main_with_args_for_test(
                [
                    "product-sot",
                    "--outcome-contract",
                    str(outcome_path),
                    "--source-material",
                    str(material_path),
                    "--out",
                    str(out_path),
                ]
            )

            product_sot = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(product_sot["record_type"], "product_sot")
        self.assertEqual(factoryctl.validate_product_sot(product_sot), [])
        self.assertIn("status de public and credential safety scans;", product_sot["scope_in"])
        self.assertNotIn("[redacted-private-marker]", json.dumps(product_sot))

    def test_product_sot_for_bug_route_is_rejected(self) -> None:
        intake = factoryctl.build_universal_signal_intake(
            route_class="bug_repair",
            request_type="bug",
            signal_type="bug_report",
            summary_public_safe="Representative bug signal should not produce Product SOT.",
            signal_ref_public_safe="external:sanitized-bug-signal",
            target_surface="bug-target",
            owner="factory-orchestrator",
            source_class="operator_supplied",
            sensitivity_class="public_safe",
            freshness="fresh",
            risk_initial="R2",
            materiality="material",
            created_at="2026-06-17T00:00:00+00:00",
            intake_id="intake-bug-repair",
        )
        source_resolution = factoryctl.build_source_resolution_packet(
            intake,
            intake_ref_public_safe="external:sanitized-bug-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-bug-report",
        )
        outcome = factoryctl.build_outcome_contract(ledger)

        with self.assertRaisesRegex(ValueError, "does not require Product SOT"):
            factoryctl.build_product_sot(outcome)

    def test_full_scope_coverage_from_product_sot_is_valid(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        outcome = factoryctl.build_outcome_contract(ledger)
        product_sot = factoryctl.build_product_sot(outcome)

        coverage = factoryctl.build_full_scope_coverage(product_sot)

        self.assertEqual(factoryctl.validate_full_scope_coverage(coverage), [])
        self.assertEqual(public_json_validator.validate_domain_rules(coverage, "$"), [])
        self.assertEqual(coverage["record_type"], "full_product_sot_scope_coverage")
        self.assertEqual(coverage["product_sot_ref"], product_sot["sot_id"])
        self.assertEqual(len(coverage["requirement_coverage"]), len(product_sot["requirement_graph"]))
        self.assertTrue(coverage["slice_policy"]["scope_reduction_forbidden"])
        self.assertTrue(coverage["slice_policy"]["slices_are_order_only"])
        self.assertEqual(coverage["handoff"]["next_artifact"], "method_contract")
        self.assertFalse(coverage["acceptance"]["execution_allowed"])

    def test_full_scope_coverage_requires_valid_product_sot(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        outcome = factoryctl.build_outcome_contract(ledger)
        product_sot = factoryctl.build_product_sot(outcome)
        product_sot["acceptance"]["execution_allowed"] = True

        with self.assertRaisesRegex(ValueError, "execution_allowed"):
            factoryctl.build_full_scope_coverage(product_sot)

    def test_full_scope_coverage_cli_generates_public_safe_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            product_sot_path = Path(tmpdir) / "product-sot.json"
            out_path = Path(tmpdir) / "full-scope-coverage.json"
            source_resolution = factoryctl.build_source_resolution_packet(
                signal_intake(),
                intake_ref_public_safe="external:sanitized-universal-signal-intake",
            )
            ledger = factoryctl.build_product_source_ledger(
                source_resolution,
                source_ref_public_safe="external:sanitized-product-brief",
            )
            outcome = factoryctl.build_outcome_contract(ledger)
            product_sot = factoryctl.build_product_sot(outcome)
            product_sot_path.write_text(json.dumps(product_sot), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(
                [
                    "full-scope-coverage",
                    "--product-sot",
                    str(product_sot_path),
                    "--out",
                    str(out_path),
                ]
            )

            coverage = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(coverage["record_type"], "full_product_sot_scope_coverage")
        self.assertEqual(factoryctl.validate_full_scope_coverage(coverage), [])

    def test_full_scope_coverage_preserves_open_decision_blocker(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        outcome = factoryctl.build_outcome_contract(ledger)
        product_sot = factoryctl.build_product_sot(outcome)
        product_sot["requirement_graph"][0]["decision_state"] = "open_decision"
        product_sot["requirement_graph"][0]["blocker_id"] = "human-gate-product-scope-001"

        coverage = factoryctl.build_full_scope_coverage(product_sot)

        first_requirement = coverage["requirement_coverage"][0]
        self.assertEqual(first_requirement["status"], "human_decision_required")
        self.assertEqual(first_requirement["blocker_id"], "human-gate-product-scope-001")
        self.assertIn("human-gate-product-scope-001", first_requirement["evidence_refs"])

    def test_method_contract_from_full_scope_coverage_is_valid(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        outcome = factoryctl.build_outcome_contract(ledger)
        product_sot = factoryctl.build_product_sot(outcome)
        coverage = factoryctl.build_full_scope_coverage(product_sot)

        method_contract = factoryctl.build_method_contract(coverage)

        self.assertEqual(factoryctl.validate_method_contract(method_contract), [])
        self.assertEqual(public_json_validator.validate_domain_rules(method_contract, "$"), [])
        self.assertEqual(method_contract["record_type"], "method_contract")
        self.assertEqual(method_contract["full_product_sot_scope_coverage_ref"], coverage["coverage_id"])
        self.assertEqual(method_contract["canonical_scope_source"], "approved Product SOT")
        self.assertIn("full_product_sot_scope_coverage", method_contract["required_factory_artifacts"])
        self.assertIn("product_creation_plan", method_contract["required_factory_artifacts"])
        self.assertEqual(method_contract["handoff"]["next_artifact"], "product_creation_plan")
        self.assertEqual(method_contract["handoff"]["next_worker"], "decomposition-planner")
        self.assertFalse(method_contract["acceptance"]["execution_allowed"])

    def test_method_contract_requires_valid_full_scope_coverage(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        outcome = factoryctl.build_outcome_contract(ledger)
        product_sot = factoryctl.build_product_sot(outcome)
        coverage = factoryctl.build_full_scope_coverage(product_sot)
        coverage["acceptance"]["execution_allowed"] = True

        with self.assertRaisesRegex(ValueError, "execution_allowed"):
            factoryctl.build_method_contract(coverage)

    def test_method_contract_cli_generates_public_safe_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_path = Path(tmpdir) / "full-scope-coverage.json"
            out_path = Path(tmpdir) / "method-contract.json"
            source_resolution = factoryctl.build_source_resolution_packet(
                signal_intake(),
                intake_ref_public_safe="external:sanitized-universal-signal-intake",
            )
            ledger = factoryctl.build_product_source_ledger(
                source_resolution,
                source_ref_public_safe="external:sanitized-product-brief",
            )
            outcome = factoryctl.build_outcome_contract(ledger)
            product_sot = factoryctl.build_product_sot(outcome)
            coverage = factoryctl.build_full_scope_coverage(product_sot)
            coverage_path.write_text(json.dumps(coverage), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(
                [
                    "method-contract",
                    "--full-scope-coverage",
                    str(coverage_path),
                    "--out",
                    str(out_path),
                ]
            )

            method_contract = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(method_contract["record_type"], "method_contract")
        self.assertEqual(factoryctl.validate_method_contract(method_contract), [])

    def test_method_contract_preserves_human_scope_gate(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        outcome = factoryctl.build_outcome_contract(ledger)
        product_sot = factoryctl.build_product_sot(outcome)
        coverage = factoryctl.build_full_scope_coverage(product_sot)
        coverage["requirement_coverage"][0]["status"] = "human_decision_required"
        coverage["requirement_coverage"][0]["blocker_id"] = "human-gate-method-scope-001"

        method_contract = factoryctl.build_method_contract(coverage)

        self.assertIn("Human Scope Gate", method_contract["required_gates"])
        self.assertTrue(method_contract["handoff"]["user_decision_required"])
        self.assertIn("human-gate-method-scope-001", method_contract["evidence_requirements"])

    def test_product_creation_plan_from_method_contract_is_valid(self) -> None:
        method_contract = build_valid_method_contract()

        plan = factoryctl.build_product_creation_plan(method_contract)

        self.assertEqual(factoryctl.validate_product_creation_plan(plan), [])
        self.assertEqual(public_json_validator.validate_domain_rules(plan, "$"), [])
        self.assertEqual(plan["record_type"], "product_creation_plan")
        self.assertEqual(plan["method_contract_ref"], method_contract["contract_id"])
        self.assertTrue(plan["complete_product_required"])
        self.assertIn("work-unit-001-scope-reconciliation", plan["execution_order"])
        self.assertEqual(plan["handoff"]["next_artifact"], "product_implementation_readiness")
        self.assertEqual(plan["handoff"]["next_worker"], "factory-orchestrator")
        self.assertFalse(plan["acceptance"]["execution_allowed"])

    def test_product_creation_plan_requires_valid_method_contract(self) -> None:
        method_contract = build_valid_method_contract()
        method_contract["acceptance"]["execution_allowed"] = True

        with self.assertRaisesRegex(ValueError, "execution_allowed"):
            factoryctl.build_product_creation_plan(method_contract)

    def test_product_creation_plan_cli_generates_public_safe_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            method_contract_path = Path(tmpdir) / "method-contract.json"
            out_path = Path(tmpdir) / "product-creation-plan.json"
            method_contract = build_valid_method_contract()
            method_contract_path.write_text(json.dumps(method_contract), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(
                [
                    "product-creation-plan",
                    "--method-contract",
                    str(method_contract_path),
                    "--out",
                    str(out_path),
                ]
            )

            plan = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(plan["record_type"], "product_creation_plan")
        self.assertEqual(factoryctl.validate_product_creation_plan(plan), [])
        self.assertEqual(public_json_validator.validate_domain_rules(plan, "$"), [])

    def test_product_creation_plan_preserves_human_scope_gate(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        outcome = factoryctl.build_outcome_contract(ledger)
        product_sot = factoryctl.build_product_sot(outcome)
        coverage = factoryctl.build_full_scope_coverage(product_sot)
        coverage["requirement_coverage"][0]["status"] = "human_decision_required"
        coverage["requirement_coverage"][0]["blocker_id"] = "human-gate-method-scope-001"
        method_contract = factoryctl.build_method_contract(coverage)

        plan = factoryctl.build_product_creation_plan(method_contract)

        scope_unit = plan["work_units"][0]
        self.assertTrue(plan["handoff"]["user_decision_required"])
        self.assertEqual(scope_unit["status"], "blocked")
        self.assertEqual(scope_unit["blocker_id"], "human-gate-method-scope-001")
        self.assertEqual(scope_unit["blocker_owner"], "human-gate-clerk")

    def test_product_implementation_readiness_from_product_creation_plan_is_valid(self) -> None:
        plan = build_valid_product_creation_plan()

        readiness = factoryctl.build_product_implementation_readiness(plan)

        self.assertEqual(factoryctl.validate_product_implementation_readiness(readiness), [])
        self.assertEqual(public_json_validator.validate_domain_rules(readiness, "$"), [])
        self.assertEqual(readiness["record_type"], "product_implementation_readiness")
        self.assertEqual(readiness["product_creation_plan_ref"], plan["plan_id"])
        self.assertEqual(readiness["artifact_alignment_result"], "CONCERNS")
        self.assertEqual(readiness["acceptance"]["allowed_execution_scope"], "ready_work_units_only")
        self.assertFalse(readiness["acceptance"]["complete_product_claim_allowed"])
        self.assertGreaterEqual(len(readiness["ready_work_units"]), 1)

    def test_product_implementation_readiness_requires_valid_product_creation_plan(self) -> None:
        plan = build_valid_product_creation_plan()
        plan["acceptance"]["execution_allowed"] = True

        with self.assertRaisesRegex(ValueError, "execution_allowed"):
            factoryctl.build_product_implementation_readiness(plan)

    def test_product_implementation_readiness_cli_generates_public_safe_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            product_creation_plan_path = Path(tmpdir) / "product-creation-plan.json"
            out_path = Path(tmpdir) / "product-implementation-readiness.json"
            plan = build_valid_product_creation_plan()
            product_creation_plan_path.write_text(json.dumps(plan), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(
                [
                    "product-implementation-readiness",
                    "--product-creation-plan",
                    str(product_creation_plan_path),
                    "--out",
                    str(out_path),
                ]
            )

            readiness = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(readiness["record_type"], "product_implementation_readiness")
        self.assertEqual(factoryctl.validate_product_implementation_readiness(readiness), [])
        self.assertEqual(public_json_validator.validate_domain_rules(readiness, "$"), [])

    def test_product_implementation_readiness_preserves_human_scope_gate(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        outcome = factoryctl.build_outcome_contract(ledger)
        product_sot = factoryctl.build_product_sot(outcome)
        coverage = factoryctl.build_full_scope_coverage(product_sot)
        coverage["requirement_coverage"][0]["status"] = "human_decision_required"
        coverage["requirement_coverage"][0]["blocker_id"] = "human-gate-method-scope-001"
        method_contract = factoryctl.build_method_contract(coverage)
        plan = factoryctl.build_product_creation_plan(method_contract)

        readiness = factoryctl.build_product_implementation_readiness(plan)

        self.assertEqual(readiness["artifact_alignment_result"], "BLOCKED")
        self.assertEqual(readiness["blocked_work_units"], ["work-unit-001-scope-reconciliation"])
        self.assertEqual(readiness["ready_work_units"], [])
        self.assertIn("human-gate-method-scope-001", readiness["human_decisions_required"])
        self.assertFalse(readiness["acceptance"]["material_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
