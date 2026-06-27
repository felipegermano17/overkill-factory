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
    outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
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

    def test_product_creation_route_requires_operator_understanding_before_sot(self) -> None:
        intake = signal_intake()

        artifact_types = {artifact["artifact_type"] for artifact in intake["required_artifacts"]}

        self.assertTrue(intake["normalization"]["operator_understanding_confirmation_required"])
        self.assertIn("operator_understanding_confirmation", artifact_types)
        self.assertEqual(factoryctl.validate_universal_signal_intake(intake), [])

    def test_solana_product_signal_routes_to_solana_ai_kit_deterministically(self) -> None:
        intake = factoryctl.build_universal_signal_intake(
            route_class="product_creation",
            request_type="product_new",
            signal_type="mixed",
            summary_public_safe="Build an onchain Solana bank with Token-2022, vaults, wallet transactions and DevNet proof.",
            signal_ref_public_safe="external:sanitized-solana-bank-paper",
            target_surface="solana onchain product",
            owner="factory-orchestrator",
            source_class="operator_supplied",
            sensitivity_class="public_safe",
            freshness="fresh",
            risk_initial="R3",
            materiality="critical",
            created_at="2026-06-23T00:00:00+00:00",
            intake_id="intake-solana-bank",
        )

        domain = intake["domain_routing"]
        worker_ids = {worker["worker_id"] for worker in intake["required_workers"]}

        self.assertIn("solana", domain["detected_surfaces"])
        self.assertIn("solana-ai-kit-core", domain["capability_pack_ids"])
        self.assertTrue(domain["official_brain_provider_required"])
        self.assertTrue(domain["product_sot_must_include_domain_brain"])
        self.assertIn("product-sot-planner", worker_ids)
        self.assertIn("product-architect", worker_ids)
        self.assertIn("solana-quasar-auditor", worker_ids)
        self.assertEqual(factoryctl.validate_universal_signal_intake(intake), [])

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

    def test_intake_cli_accepts_operator_friendly_product_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "signal-intake.json"

            result = factoryctl.main_with_args_for_test(
                [
                    "intake",
                    "--route-class",
                    "product_creation",
                    "--request-type",
                    "new_product",
                    "--signal-type",
                    "product_brief",
                    "--summary",
                    "Operator supplied product brief for a full product start.",
                    "--signal-ref",
                    "external:source-card-product-brief",
                    "--out",
                    str(path),
                ]
            )
            intake = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(intake["classification"]["request_type"], "product_new")
        self.assertEqual(intake["signal"]["signal_type"], "product_paper")
        self.assertEqual(factoryctl.validate_universal_signal_intake(intake), [])

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
        self.assertEqual(ledger["handoff"]["next_artifact"], "operator_understanding_confirmation")
        self.assertEqual(ledger["handoff"]["next_worker"], "factory-orchestrator")
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

        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")

        self.assertEqual(factoryctl.validate_outcome_contract(outcome), [])
        self.assertEqual(public_json_validator.validate_domain_rules(outcome, "$"), [])
        self.assertEqual(outcome["record_type"], "outcome_contract")
        self.assertEqual(outcome["source_ledger_ref"], ledger["ledger_id"])
        self.assertEqual(outcome["handoff"]["next_artifact"], "product_sot")
        self.assertEqual(outcome["handoff"]["next_worker"], "product-sot-planner")
        self.assertFalse(outcome["acceptance"]["product_sot_generated"])
        self.assertFalse(outcome["acceptance"]["execution_allowed"])

    def test_pending_operator_understanding_blocks_outcome_and_product_sot(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )

        pending = factoryctl.build_operator_understanding_confirmation(ledger)
        outcome = factoryctl.build_outcome_contract(ledger)

        self.assertFalse(pending["confirmation_state"]["product_sot_allowed"])
        self.assertEqual(factoryctl.validate_operator_understanding_confirmation(pending), [])
        self.assertTrue(any("still pending" in error for error in factoryctl.validate_outcome_contract(outcome)))
        with self.assertRaisesRegex(ValueError, "operator_understanding_confirmation_ref is still pending"):
            factoryctl.build_product_sot(outcome)

    def test_confirmed_operator_understanding_allows_product_sot(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        confirmation = factoryctl.build_operator_understanding_confirmation(
            ledger,
            confirmed=True,
            operator_response_ref="external:operator-telegram-understanding-confirmed",
        )
        outcome = factoryctl.build_outcome_contract(
            ledger,
            operator_understanding_confirmation_ref=confirmation["confirmation_id"],
        )

        product_sot = factoryctl.build_product_sot(outcome)

        self.assertTrue(confirmation["confirmation_state"]["product_sot_allowed"])
        self.assertEqual(factoryctl.validate_operator_understanding_confirmation(confirmation), [])
        self.assertEqual(product_sot["operator_understanding_confirmation_ref"], confirmation["confirmation_id"])
        self.assertEqual(factoryctl.validate_product_sot(product_sot), [])

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
            factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")

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
                    "--operator-understanding-confirmation-ref",
                    "external:operator-understanding-confirmed",
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

        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")

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
        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")

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
        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
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
            outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
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
        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")

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
        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
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
        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
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
            outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
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
        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
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
        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
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
        expected_requirement_refs = [
            row["requirement_ref"]
            for row in coverage["requirement_coverage"]
            if row["status"] != "out_of_scope"
        ]
        self.assertEqual(method_contract["active_product_sot_requirement_refs"], expected_requirement_refs)
        self.assertFalse(
            any(ref.endswith("#all-active-product-sot-requirements") for ref in method_contract["active_product_sot_requirement_refs"])
        )

    def test_method_contract_requires_valid_full_scope_coverage(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
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
            outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
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
        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
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
        active_requirement_refs = set(method_contract["active_product_sot_requirement_refs"])
        coverage_requirement_refs = {row["requirement_ref"] for row in plan["requirement_execution_coverage"]}
        self.assertEqual(coverage_requirement_refs, active_requirement_refs)
        self.assertGreaterEqual(len(plan["work_units"]), len(active_requirement_refs) + 3)
        self.assertTrue(set(unit["unit_id"] for unit in plan["work_units"]).issubset(set(plan["execution_order"])))
        for unit in plan["work_units"]:
            self.assertFalse(
                any(ref.endswith("#all-active-product-sot-requirements") for ref in unit["product_sot_requirement_refs"]),
                unit,
            )
        for row in plan["requirement_execution_coverage"]:
            self.assertTrue(row["work_unit_refs"], row)
            self.assertTrue(row["proof_ids_required"], row)

    def test_product_creation_plan_rejects_aggregate_requirement_coverage(self) -> None:
        plan = build_valid_product_creation_plan()
        plan["work_units"][0]["product_sot_requirement_refs"] = [
            f"{plan['method_contract_ref']}#all-active-product-sot-requirements"
        ]
        plan["requirement_execution_coverage"] = [
            {
                "requirement_ref": f"{plan['method_contract_ref']}#all-active-product-sot-requirements",
                "coverage_status": "covered_for_execution",
                "work_unit_refs": [plan["work_units"][0]["unit_id"]],
                "proof_ids_required": ["generic.scope-fit"],
                "owner_worker": "decomposition-planner",
                "reviewer_role": "independent-reviewer",
                "source": "regression-test",
            }
        ]

        errors = factoryctl.validate_product_creation_plan(plan)

        self.assertTrue(any("aggregate all-active" in error for error in errors), errors)

    def test_product_creation_plan_rejects_missing_requirement_execution_coverage(self) -> None:
        plan = build_valid_product_creation_plan()
        plan.pop("requirement_execution_coverage")

        errors = factoryctl.validate_product_creation_plan(plan)

        self.assertTrue(any("requirement_execution_coverage" in error for error in errors), errors)

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
        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
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
        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
        product_sot = factoryctl.build_product_sot(outcome)
        coverage = factoryctl.build_full_scope_coverage(product_sot)
        coverage["requirement_coverage"][0]["status"] = "human_decision_required"
        coverage["requirement_coverage"][0]["blocker_id"] = "human-gate-method-scope-001"
        method_contract = factoryctl.build_method_contract(coverage)
        plan = factoryctl.build_product_creation_plan(method_contract)

        readiness = factoryctl.build_product_implementation_readiness(plan)

        self.assertEqual(readiness["artifact_alignment_result"], "BLOCKED")
        expected_blocked = [
            unit["unit_id"]
            for unit in plan["work_units"]
            if unit["status"] == "blocked"
        ]
        self.assertEqual(readiness["blocked_work_units"], expected_blocked)
        self.assertIn("work-unit-001-scope-reconciliation", readiness["blocked_work_units"])
        self.assertTrue(
            any(unit_id.startswith("work-unit-002-") for unit_id in readiness["blocked_work_units"]),
            readiness["blocked_work_units"],
        )
        self.assertEqual(readiness["ready_work_units"], [])
        self.assertIn("human-gate-method-scope-001", readiness["human_decisions_required"])
        self.assertFalse(readiness["acceptance"]["material_execution_allowed"])

    def test_ready_work_unit_packets_from_readiness_are_valid(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)

        manifest = factoryctl.build_ready_work_unit_packet_manifest(
            plan,
            readiness,
            product_creation_plan_ref="external:sanitized-product-creation-plan",
            product_implementation_readiness_ref="external:sanitized-product-implementation-readiness",
        )

        self.assertEqual(factoryctl.validate_ready_work_unit_packet_manifest(manifest), [])
        self.assertEqual(public_json_validator.validate_domain_rules(manifest, "$"), [])
        self.assertEqual(manifest["record_type"], "ready_work_unit_packet_manifest")
        self.assertEqual(manifest["readiness_result"], "CONCERNS")
        self.assertEqual(manifest["acceptance"]["allowed_execution_scope"], "ready_work_units_only")
        self.assertFalse(manifest["acceptance"]["complete_product_claim_allowed"])
        self.assertFalse(manifest["runtime_boundary"]["live_hermes_mutated"])
        self.assertEqual(
            [packet["work_unit_id"] for packet in manifest["packets"]],
            readiness["ready_work_units"],
        )
        self.assertTrue(all(packet["receipt_five_contract"]["must_attach_artifact_refs"] for packet in manifest["packets"]))
        for packet in manifest["packets"]:
            context_boundary = packet["context_boundary"]
            self.assertEqual(context_boundary["workspace_search_policy"], "bounded_refs_only")
            self.assertFalse(context_boundary["broad_repo_search_allowed"])
            self.assertEqual(context_boundary["missing_context_action"], "BLOCK_WITH_OWNER")
            self.assertEqual(context_boundary["context_drift_action"], "BLOCK_AND_REPORT")
            self.assertFalse(context_boundary["operator_action_required_for_missing_context"])
            self.assertIn("external:sanitized-product-creation-plan", context_boundary["allowed_context_refs"])
            self.assertIn("external:sanitized-product-implementation-readiness", context_boundary["allowed_context_refs"])
            self.assertIn("done_definition", packet)
            self.assertIn("phase", packet)
            self.assertIn("risk_effective", packet)
            self.assertIn("surfaces", packet)
            worker_contract = packet["worker_input_contract"]
            self.assertEqual(worker_contract["owner_worker"], packet["owner_worker"])
            self.assertEqual(worker_contract["inputs"]["done_definition"], packet["done_definition"])
            for required_input in factoryctl._ready_work_unit_required_inputs(packet["owner_worker"]):
                self.assertIn(required_input, worker_contract["required_inputs"])
                self.assertIn(required_input, worker_contract["inputs"])
            context_packet = packet["work_unit_context_packet"]
            self.assertEqual(context_packet["resolution_status"], "resolved_for_worker_execution")
            self.assertFalse(context_packet["dispatch_allowed_with_unresolved_context"])
            self.assertEqual(context_packet["worker_input_contract"], worker_contract)
            resolver_refs = [entry["ref"] for entry in context_packet["context_resolver"]]
            for allowed_ref in context_boundary["allowed_context_refs"]:
                self.assertIn(allowed_ref, resolver_refs)
            self.assertTrue(
                all(entry["required_before_dispatch"] is True for entry in context_packet["context_resolver"])
            )
            self.assertTrue(
                all(
                    entry["resolution_status"] in factoryctl.READY_WORK_UNIT_RESOLVED_CONTEXT_STATUSES
                    for entry in context_packet["context_resolver"]
                )
            )
            self.assertFalse(context_packet["context_repair_route"]["operator_action_required"])
            self.assertFalse(context_packet["context_repair_route"]["dispatch_allowed_when_missing_context"])
        release_packet = next(packet for packet in manifest["packets"] if packet["owner_worker"] == "release-ops-worker")
        self.assertIn("release_plan", release_packet["worker_input_contract"]["inputs"])
        self.assertIn("production_operations_plan", release_packet["worker_input_contract"]["inputs"])
        decomposition_packet = next(packet for packet in manifest["packets"] if packet["owner_worker"] == "decomposition-planner")
        self.assertIn("spec_graph", decomposition_packet["worker_input_contract"]["inputs"])
        self.assertIn("parallel_lane_contract", decomposition_packet["worker_input_contract"]["inputs"])

    def test_ready_work_unit_packets_reject_unbounded_context_boundary(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)
        manifest = factoryctl.build_ready_work_unit_packet_manifest(
            plan,
            readiness,
            product_creation_plan_ref="external:sanitized-product-creation-plan",
            product_implementation_readiness_ref="external:sanitized-product-implementation-readiness",
        )
        manifest["packets"][0]["context_boundary"]["broad_repo_search_allowed"] = True
        manifest["packets"][0]["context_boundary"]["workspace_search_policy"] = "search_entire_workspace"

        errors = factoryctl.validate_ready_work_unit_packet_manifest(manifest)

        self.assertTrue(any("broad_repo_search_allowed must be false" in error for error in errors), errors)
        self.assertTrue(any("workspace_search_policy must be bounded_refs_only" in error for error in errors), errors)

    def test_ready_work_unit_packets_reject_context_boundary_conflicts_and_bad_owner(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)
        manifest = factoryctl.build_ready_work_unit_packet_manifest(
            plan,
            readiness,
            product_creation_plan_ref="external:sanitized-product-creation-plan",
            product_implementation_readiness_ref="external:sanitized-product-implementation-readiness",
        )
        conflict_ref = manifest["packets"][0]["context_boundary"]["allowed_context_refs"][0]
        manifest["packets"][0]["context_boundary"]["forbidden_context_refs"].append(conflict_ref)
        manifest["packets"][0]["context_boundary"]["block_owner"] = "not-a-real-worker"

        errors = factoryctl.validate_ready_work_unit_packet_manifest(manifest)

        self.assertTrue(any("refs cannot be both allowed and forbidden" in error for error in errors), errors)
        self.assertTrue(any("block_owner must match owner_worker" in error for error in errors), errors)

    def test_ready_work_unit_packets_reject_missing_worker_context(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)
        manifest = factoryctl.build_ready_work_unit_packet_manifest(
            plan,
            readiness,
            product_creation_plan_ref="external:sanitized-product-creation-plan",
            product_implementation_readiness_ref="external:sanitized-product-implementation-readiness",
        )
        packet = manifest["packets"][0]
        packet["worker_input_contract"]["inputs"].pop("done_definition", None)

        errors = factoryctl.validate_ready_work_unit_packet_manifest(manifest)

        self.assertTrue(any("inputs.done_definition must be resolved before dispatch" in error for error in errors), errors)

    def test_ready_work_unit_packets_reject_unresolved_context_refs(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)
        manifest = factoryctl.build_ready_work_unit_packet_manifest(
            plan,
            readiness,
            product_creation_plan_ref="external:sanitized-product-creation-plan",
            product_implementation_readiness_ref="external:sanitized-product-implementation-readiness",
        )
        packet = manifest["packets"][0]
        packet["work_unit_context_packet"]["context_resolver"] = [
            entry
            for entry in packet["work_unit_context_packet"]["context_resolver"]
            if entry["ref"] != packet["context_boundary"]["allowed_context_refs"][0]
        ]
        packet["work_unit_context_packet"]["context_resolver"][0]["resolution_status"] = "external_ref_only"
        packet["work_unit_context_packet"]["context_resolver"][0]["payload_key"] = "missing_payload"

        errors = factoryctl.validate_ready_work_unit_packet_manifest(manifest)

        self.assertTrue(any("context_resolver missing refs" in error for error in errors), errors)
        self.assertTrue(any("resolution_status must be resolved" in error for error in errors), errors)
        self.assertTrue(any("payload_key must reference an embedded payload" in error for error in errors), errors)

    def test_ready_work_unit_packets_reject_context_contract_divergence(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)
        manifest = factoryctl.build_ready_work_unit_packet_manifest(
            plan,
            readiness,
            product_creation_plan_ref="external:sanitized-product-creation-plan",
            product_implementation_readiness_ref="external:sanitized-product-implementation-readiness",
        )
        packet = manifest["packets"][0]
        packet["work_unit_context_packet"]["worker_input_contract"]["inputs"]["done_definition"] = {
            "definition": "different"
        }

        errors = factoryctl.validate_ready_work_unit_packet_manifest(manifest)

        self.assertTrue(
            any("work_unit_context_packet.worker_input_contract must match packet.worker_input_contract" in error for error in errors),
            errors,
        )

    def test_ready_work_unit_packets_reject_blocked_readiness(self) -> None:
        source_resolution = factoryctl.build_source_resolution_packet(
            signal_intake(),
            intake_ref_public_safe="external:sanitized-universal-signal-intake",
        )
        ledger = factoryctl.build_product_source_ledger(
            source_resolution,
            source_ref_public_safe="external:sanitized-product-brief",
        )
        outcome = factoryctl.build_outcome_contract(ledger, operator_understanding_confirmation_ref="external:operator-understanding-confirmed")
        product_sot = factoryctl.build_product_sot(outcome)
        coverage = factoryctl.build_full_scope_coverage(product_sot)
        coverage["requirement_coverage"][0]["status"] = "human_decision_required"
        coverage["requirement_coverage"][0]["blocker_id"] = "human-gate-method-scope-001"
        method_contract = factoryctl.build_method_contract(coverage)
        plan = factoryctl.build_product_creation_plan(method_contract)
        readiness = factoryctl.build_product_implementation_readiness(plan)

        with self.assertRaisesRegex(ValueError, "does not allow ready work-unit packet materialization"):
            factoryctl.build_ready_work_unit_packet_manifest(plan, readiness)

    def test_ready_work_unit_packets_reject_unknown_ready_unit(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)
        readiness["ready_work_units"].append("missing-work-unit")

        with self.assertRaisesRegex(ValueError, "ready_work_units not found in Product Creation Plan"):
            factoryctl.build_ready_work_unit_packet_manifest(plan, readiness)

    def test_ready_work_unit_packets_cli_generates_manifest_and_requests(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "product-creation-plan.json"
            readiness_path = Path(tmpdir) / "product-implementation-readiness.json"
            out_dir = Path(tmpdir) / "ready-work-unit-packets"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            readiness_path.write_text(json.dumps(readiness), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(
                [
                    "ready-work-unit-packets",
                    "--product-creation-plan",
                    str(plan_path),
                    "--product-implementation-readiness",
                    str(readiness_path),
                    "--forbidden-context-ref",
                    "external:sanitized-off-limits-parallel-thread",
                    "--out",
                    str(out_dir),
                ]
            )
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))

            validate_result = factoryctl.main_with_args_for_test(
                ["validate-ready-work-unit-packets", str(out_dir / "manifest.json")]
            )

        self.assertEqual(result, 0)
        self.assertEqual(validate_result, 0)
        self.assertEqual(manifest["record_type"], "ready_work_unit_packet_manifest")
        self.assertEqual(len(manifest["packets"]), len(readiness["ready_work_units"]))
        self.assertTrue(
            all(
                "external:sanitized-off-limits-parallel-thread" in packet["context_boundary"]["forbidden_context_refs"]
                for packet in manifest["packets"]
            )
        )

    def test_ready_work_unit_hermes_plan_from_packets_is_valid_and_blocked_first(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)
        manifest = factoryctl.build_ready_work_unit_packet_manifest(
            plan,
            readiness,
            product_creation_plan_ref="external:sanitized-product-creation-plan",
            product_implementation_readiness_ref="external:sanitized-product-implementation-readiness",
        )

        materialization = factoryctl.build_ready_work_unit_hermes_materialization_plan(
            manifest,
            board="overkill-factory-live",
            ready_work_unit_packet_manifest_ref="external:sanitized-ready-work-unit-packets",
        )

        self.assertEqual(factoryctl.validate_ready_work_unit_hermes_materialization_plan(materialization), [])
        self.assertEqual(public_json_validator.validate_domain_rules(materialization, "$"), [])
        self.assertEqual(materialization["record_type"], "ready_work_unit_hermes_materialization_plan")
        self.assertFalse(materialization["runtime_boundary"]["live_hermes_mutated"])
        self.assertFalse(materialization["complete_product_claim_allowed"])
        self.assertEqual(len(materialization["tasks"]), len(manifest["packets"]))
        self.assertTrue(all(task["initial_status"] == "unassigned_pending_block" for task in materialization["tasks"]))
        self.assertTrue(all(task["create_policy"]["create_with_assignee"] is False for task in materialization["tasks"]))
        self.assertTrue(
            all(task["create_policy"]["assign_after_block_event_verified"] is True for task in materialization["tasks"])
        )
        self.assertTrue(
            all(task["block_policy"]["block_event_required_before_dispatch"] for task in materialization["tasks"])
        )
        self.assertTrue(
            all(
                task["dispatch_policy"]["dispatch_allowed_without_runtime_gate"] is False
                for task in materialization["tasks"]
            )
        )
        self.assertTrue(
            all(
                task["dispatch_policy"]["complete_product_claim_allowed"] is False
                for task in materialization["tasks"]
            )
        )
        self.assertTrue(
            all(task["context_boundary"] == task["body_contract"]["context_boundary"] for task in materialization["tasks"])
        )
        self.assertTrue(
            all(
                task["work_unit_context_packet"] == task["body_contract"]["work_unit_context_packet"]
                for task in materialization["tasks"]
            )
        )
        self.assertTrue(
            all(task["context_boundary"]["workspace_search_policy"] == "bounded_refs_only" for task in materialization["tasks"])
        )
        self.assertTrue(
            all(task["context_boundary"]["broad_repo_search_allowed"] is False for task in materialization["tasks"])
        )
        self.assertEqual(
            [task["work_unit_id"] for task in materialization["tasks"]],
            [packet["work_unit_id"] for packet in manifest["packets"]],
        )

    def test_ready_work_unit_hermes_plan_rejects_context_boundary_mismatch(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)
        manifest = factoryctl.build_ready_work_unit_packet_manifest(
            plan,
            readiness,
            product_creation_plan_ref="external:sanitized-product-creation-plan",
            product_implementation_readiness_ref="external:sanitized-product-implementation-readiness",
        )
        materialization = factoryctl.build_ready_work_unit_hermes_materialization_plan(
            manifest,
            board="overkill-factory-live",
            ready_work_unit_packet_manifest_ref="external:sanitized-ready-work-unit-packets",
        )

        materialization["tasks"][0]["context_boundary"]["broad_repo_search_allowed"] = True

        errors = factoryctl.validate_ready_work_unit_hermes_materialization_plan(materialization)

        self.assertTrue(any("context_boundary must match body_contract.context_boundary" in error for error in errors), errors)
        self.assertTrue(any("broad_repo_search_allowed must be false" in error for error in errors), errors)

    def test_ready_work_unit_hermes_plan_rejects_context_packet_mismatch(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)
        manifest = factoryctl.build_ready_work_unit_packet_manifest(
            plan,
            readiness,
            product_creation_plan_ref="external:sanitized-product-creation-plan",
            product_implementation_readiness_ref="external:sanitized-product-implementation-readiness",
        )
        materialization = factoryctl.build_ready_work_unit_hermes_materialization_plan(
            manifest,
            board="overkill-factory-live",
            ready_work_unit_packet_manifest_ref="external:sanitized-ready-work-unit-packets",
        )

        materialization["tasks"][0]["work_unit_context_packet"]["resolution_status"] = "stale"
        materialization["tasks"][0]["body_contract"]["work_unit_context_packet"]["context_resolver"][0]["resolution_status"] = "external_ref_only"

        errors = factoryctl.validate_ready_work_unit_hermes_materialization_plan(materialization)

        self.assertTrue(any("work_unit_context_packet must match body_contract.work_unit_context_packet" in error for error in errors), errors)
        self.assertTrue(any("resolution_status must be resolved" in error for error in errors), errors)

    def test_ready_work_unit_hermes_plan_schema_rejects_unresolved_context_packet(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)
        manifest = factoryctl.build_ready_work_unit_packet_manifest(
            plan,
            readiness,
            product_creation_plan_ref="external:sanitized-product-creation-plan",
            product_implementation_readiness_ref="external:sanitized-product-implementation-readiness",
        )
        materialization = factoryctl.build_ready_work_unit_hermes_materialization_plan(
            manifest,
            board="overkill-factory-live",
            ready_work_unit_packet_manifest_ref="external:sanitized-ready-work-unit-packets",
        )
        materialization["tasks"][0]["work_unit_context_packet"]["context_resolver"][0]["resolution_status"] = "external_ref_only"
        materialization["tasks"][0]["body_contract"]["work_unit_context_packet"]["context_resolver"][0]["resolution_status"] = "external_ref_only"
        schemas = public_json_validator.load_schemas()
        schema = schemas["ready-work-unit-hermes-materialization-plan.schema.json"]

        schema_errors = public_json_validator.validate_node(schema, materialization, "$", schemas=schemas, root_schema=schema)

        self.assertTrue(any("external_ref_only" in error or "resolution_status" in error for error in schema_errors), schema_errors)

    def test_ready_work_unit_hermes_plan_rejects_context_boundary_conflicts_and_bad_owner(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)
        manifest = factoryctl.build_ready_work_unit_packet_manifest(
            plan,
            readiness,
            product_creation_plan_ref="external:sanitized-product-creation-plan",
            product_implementation_readiness_ref="external:sanitized-product-implementation-readiness",
        )
        materialization = factoryctl.build_ready_work_unit_hermes_materialization_plan(
            manifest,
            board="overkill-factory-live",
            ready_work_unit_packet_manifest_ref="external:sanitized-ready-work-unit-packets",
        )
        conflict_ref = materialization["tasks"][0]["context_boundary"]["allowed_context_refs"][0]
        materialization["tasks"][0]["context_boundary"]["forbidden_context_refs"].append(conflict_ref)
        materialization["tasks"][0]["body_contract"]["context_boundary"]["forbidden_context_refs"].append(conflict_ref)
        materialization["tasks"][0]["context_boundary"]["block_owner"] = "not-a-real-worker"
        materialization["tasks"][0]["body_contract"]["context_boundary"]["block_owner"] = "not-a-real-worker"

        errors = factoryctl.validate_ready_work_unit_hermes_materialization_plan(materialization)

        self.assertTrue(any("refs cannot be both allowed and forbidden" in error for error in errors), errors)
        self.assertTrue(any("block_owner must match owner_worker" in error for error in errors), errors)

    def test_ready_work_unit_hermes_plan_rejects_dispatch_without_runtime_gate(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)
        manifest = factoryctl.build_ready_work_unit_packet_manifest(
            plan,
            readiness,
            product_creation_plan_ref="external:sanitized-product-creation-plan",
            product_implementation_readiness_ref="external:sanitized-product-implementation-readiness",
        )
        materialization = factoryctl.build_ready_work_unit_hermes_materialization_plan(
            manifest,
            board="overkill-factory-live",
            ready_work_unit_packet_manifest_ref="external:sanitized-ready-work-unit-packets",
        )

        materialization["tasks"][0]["dispatch_policy"]["dispatch_allowed_without_runtime_gate"] = True
        materialization["acceptance"]["dispatch_allowed_without_runtime_gate"] = True

        errors = factoryctl.validate_ready_work_unit_hermes_materialization_plan(materialization)

        self.assertTrue(any("dispatch_allowed_without_runtime_gate must be false" in error for error in errors), errors)

    def test_ready_work_unit_hermes_plan_cli_generates_and_validates_plan(self) -> None:
        plan = build_valid_product_creation_plan()
        readiness = factoryctl.build_product_implementation_readiness(plan)

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "product-creation-plan.json"
            readiness_path = Path(tmpdir) / "product-implementation-readiness.json"
            packets_dir = Path(tmpdir) / "ready-work-unit-packets"
            materialization_path = Path(tmpdir) / "ready-work-unit-hermes-plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            readiness_path.write_text(json.dumps(readiness), encoding="utf-8")

            packet_result = factoryctl.main_with_args_for_test(
                [
                    "ready-work-unit-packets",
                    "--product-creation-plan",
                    str(plan_path),
                    "--product-implementation-readiness",
                    str(readiness_path),
                    "--out",
                    str(packets_dir),
                ]
            )
            materialization_result = factoryctl.main_with_args_for_test(
                [
                    "ready-work-unit-hermes-plan",
                    "--ready-work-unit-packets",
                    str(packets_dir),
                    "--board",
                    "overkill-factory-live",
                    "--out",
                    str(materialization_path),
                ]
            )
            validate_result = factoryctl.main_with_args_for_test(
                ["validate-ready-work-unit-hermes-plan", str(materialization_path)]
            )
            materialization = json.loads(materialization_path.read_text(encoding="utf-8"))

        self.assertEqual(packet_result, 0)
        self.assertEqual(materialization_result, 0)
        self.assertEqual(validate_result, 0)
        self.assertEqual(materialization["record_type"], "ready_work_unit_hermes_materialization_plan")
        self.assertEqual(materialization["acceptance"]["task_count"], len(readiness["ready_work_units"]))


if __name__ == "__main__":
    unittest.main()
