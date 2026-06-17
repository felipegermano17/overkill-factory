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


if __name__ == "__main__":
    unittest.main()
