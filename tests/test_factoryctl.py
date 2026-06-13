from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factoryctl.py"
SPEC = importlib.util.spec_from_file_location("factoryctl", MODULE_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl"] = factoryctl
SPEC.loader.exec_module(factoryctl)


def load_card(name: str) -> dict:
    return factoryctl.load_json_like(ROOT / "examples" / "cards" / name)


def worker_result(record_type: str, *, result: str = "PASS", source_card: dict | None = None) -> dict:
    worker_id = {
        "security_scan_result": "codex-security",
        "auditor_result": "solana-quasar-auditor",
        "independent_review_result": "independent-reviewer",
        "receipt_five_reconciliation_result": "evidence-reconciler",
        "qa_verification_result": "qa-verification-worker",
        "autoreview_result": "autoreview-gate",
        "orchestration_result": "factory-orchestrator",
        "source_ledger_result": "source-ledger-worker",
        "security_orchestration_result": "security-orchestrator",
        "crypto_key_management_result": "crypto-key-management-specialist",
        "remote_proof_result": "remote-proof-runner",
        "handoff_packet_result": "handoff-packer",
        "solana_quasar_build_result": "solana-quasar-builder",
        "solana_quasar_qa_result": "solana-quasar-qa-engineer",
        "supply_chain_result": "supply-chain-gate",
    }.get(record_type, "fixture-worker")
    card_id = str((source_card or {}).get("card_id") or "VAL-SOLANA-QUASAR-R3")
    slice_id = str((source_card or {}).get("slice_id") or "VAL_FACTORY_HEAVY_03")
    phase = str((source_card or {}).get("phase") or "F13")
    risk_effective = str((source_card or {}).get("risk_effective") or "R3")
    surfaces = (source_card or {}).get("surfaces") or ["solana-quasar"]
    payload = {
        "$schema": factoryctl.worker_result_schema_url(worker_id) if worker_id in factoryctl.WORKERS else "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": record_type,
        "created_at": "2026-06-06T00:00:00+00:00",
        "worker": {"id": worker_id, "name": "Fixture Worker", "factory_phase": "F13"},
        "card_ref": {
            "card_id": card_id,
            "slice_id": slice_id,
            "phase": phase,
            "risk_effective": risk_effective,
            "surfaces": surfaces,
        },
        "result": result,
        "blocking_findings": False,
        "findings_summary": "Synthetic passing fixture.",
        "tool_or_profile": "fixture-tool",
        "executed_by": "fixture-runner",
        "evidence_refs": ["README.md"],
        "artifact_contract": factoryctl.artifact_contract_for_refs(["README.md"]),
        "artifact_classifications": factoryctl.artifact_contract_for_refs(["README.md"])["classifications"],
        "evidence_kind": "synthetic",
        "reusable_for_product": False,
        "next_action": "none",
        "promotion_authority": {
            "result": "PASS" if result in {"PASS", "WAIVED"} else "BLOCK",
            "predicate": "synthetic fixture authority",
            "allowed_transition_scopes": ["done"] if result in {"PASS", "WAIVED"} else [],
            "active": True,
        },
    }
    if record_type == "security_scan_result":
        payload["scanner_agent"] = "codex-security-runner"
        payload["tool"] = "codex-security:security-scan"
        payload["scope"] = ["fixture"]
    if record_type == "auditor_result":
        payload["audit_mode"] = "preflight"
        payload["preflight_only"] = True
        payload["findings_summary"] = "Auditor preflight only; no code audit is claimed."
    if record_type == "autoreview_result":
        payload["reviewed_diff"] = "synthetic fixture"
    if record_type == "remote_proof_result":
        payload["runtime"] = "synthetic-smoke"
        payload["ttl"] = "synthetic"
        payload["cleanup"] = {"status": "not_applicable"}
        payload["artifact_refs"] = ["reports/fixture.md"]
    if record_type == "handoff_packet_result":
        payload["handoff_packet_ref"] = "reports/fixture.md"
    if record_type == "receipt_five_reconciliation_result":
        payload["valid"] = result == "PASS"
    if result == "WAIVED":
        payload["waiver"] = {
            "owner": "fixture-owner",
            "reason": "Synthetic fixture boundary.",
            "expires_at": "2026-12-31T00:00:00+00:00",
            "reviewer_or_human_gate_ref": "README.md",
            "compensating_controls": ["run real worker before production"],
            "evidence_refs": ["README.md"],
        }
    return payload


def human_gate_record(source_card: dict | None = None) -> dict:
    card_id = str((source_card or {}).get("card_id") or "VAL-SOLANA-QUASAR-R3")
    slice_id = str((source_card or {}).get("slice_id") or "VAL_FACTORY_HEAVY_03")
    return {
        "record_type": "human_gate_record",
        "gate_type": "R3",
        "card_id": card_id,
        "card_ref": {
            "card_id": card_id,
            "slice_id": slice_id,
        },
        "decision": "approved",
        "human_actor": "product-owner",
        "decision_at": "2026-06-06T00:00:00+00:00",
        "approval_event_id": "evt_fixture_human_approval",
        "approved_scope": ["dry validation"],
        "forbidden_scope": ["deploy"],
        "risk_owner": "product-owner",
        "security_owner": "security-owner",
        "rollback_owner": "release-owner",
        "evidence_refs": ["README.md"],
        "evidence_kind": "synthetic",
        "reusable_for_product": False,
    }


PRIVATE_NAME = "KA" + "XIS"
PRIVATE_ENV = "V" + "M"
PRIVATE_USERS_PATH = "C:" + "\\\\" + "Users"
PRIVATE_SYNC_ROOT = "One" + "Drive"
PRIVATE_PATH_RE = re.compile(
    PRIVATE_USERS_PATH + r"|" + PRIVATE_SYNC_ROOT + r"|" + PRIVATE_NAME + r" " + PRIVATE_ENV + r"|" + PRIVATE_NAME,
    re.IGNORECASE,
)


class FactoryCtlTest(unittest.TestCase):
    def test_product_face_card_requires_product_face_and_review_workers(self) -> None:
        card = load_card("v35_valid_product_face.md")
        report = factoryctl.build_gate_report(card)

        self.assertEqual(report["card_validation_errors"], [])
        self.assertEqual(report["gate_status"], "ready_for_worker_execution")
        self.assertIn("product-face", report["required_workers"])
        self.assertEqual(report["workers"]["product-face"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["independent-reviewer"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["solana-quasar-auditor"]["status"], "not_required_by_current_card")

    def test_onchain_r3_card_requires_security_auditor_review_and_human_gate(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        report = factoryctl.build_gate_report(card)

        self.assertEqual(report["card_validation_errors"], [])
        self.assertEqual(report["gate_status"], "ready_for_worker_execution")
        self.assertIn("codex-security", report["required_workers"])
        self.assertTrue(report["workers"]["codex-security"]["required"])
        self.assertEqual(report["workers"]["codex-security"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["solana-quasar-auditor"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["independent-reviewer"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["human-gate-clerk"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["autoreview-gate"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["remote-proof-runner"]["status"], "not_required_by_current_card")
        self.assertEqual(report["workers"]["supply-chain-gate"]["status"], "requires_execution")

    def test_required_only_worker_packets_generate_only_triggered_workers(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        required_ids = factoryctl.required_worker_ids(card)

        with tempfile.TemporaryDirectory() as tmp:
            args = type(
                "Args",
                (),
                {
                    "worker": "all",
                    "card": card_path,
                    "out": Path(tmp),
                    "required_only": True,
                },
            )
            self.assertEqual(factoryctl.command_worker_packet(args), 0)
            generated = sorted(path.name for path in Path(tmp).glob("*.json"))

        self.assertEqual(generated, sorted(f"{worker_id}-request.json" for worker_id in required_ids))
        self.assertLess(len(generated), len(factoryctl.WORKERS))

    def test_worker_packet_fails_closed_without_profile_binding_manifest(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        original_path = factoryctl.PROFILE_BINDINGS_PATH
        try:
            factoryctl.PROFILE_BINDINGS_PATH = ROOT / "agents" / "missing-bindings-for-test.json"
            with self.assertRaises(FileNotFoundError):
                factoryctl.build_worker_packet("codex-security", card, card_path)
        finally:
            factoryctl.PROFILE_BINDINGS_PATH = original_path

    def test_worker_packet_schema_allows_every_registered_worker(self) -> None:
        schema = json.loads((ROOT / "schemas" / "worker-packet.schema.json").read_text(encoding="utf-8"))
        allowed = set(schema["properties"]["worker"]["properties"]["id"]["enum"])

        self.assertEqual(allowed, set(factoryctl.WORKERS))

    def test_public_artifact_card_triggers_public_safety_gate(self) -> None:
        card = dict(load_card("v35_valid_product_face.md"))
        card["phase"] = "F16"
        card["surfaces"] = ["public", "docs", "code", "ci", "supply-chain"]
        card["target_repo_paths"] = ["README.md", "docs"]
        card["product_face_result_ref"] = "reports/product-face.md"
        card.pop("security_scan_packet", None)
        report = factoryctl.build_gate_report(card)

        self.assertTrue(report["workers"]["codex-security"]["required"])
        self.assertEqual(report["workers"]["codex-security"]["status"], "blocked_missing_inputs")
        self.assertEqual(report["gate_status"], "blocked")
        self.assertIn("codex-security", report["blocked_workers"])
        self.assertEqual(report["workers"]["public-safety-gate"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["release-ops-worker"]["status"], "blocked_missing_inputs")

    def test_security_scan_packet_can_require_codex_security_on_r2_product_face(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")

        report = factoryctl.build_gate_report(card)

        self.assertTrue(report["workers"]["codex-security"]["required"])
        self.assertEqual(report["workers"]["codex-security"]["status"], "requires_execution")
        self.assertIn("codex-security", report["required_workers"])

    def test_worker_packet_source_card_ref_is_public_safe(self) -> None:
        card_path = ROOT / "examples" / "minimal-hermes-project" / "card.md"
        card = factoryctl.load_json_like(card_path)

        packet = factoryctl.build_worker_packet("handoff-packer", card, card_path)

        self.assertEqual(packet["source_card_path"], "examples/minimal-hermes-project/card.md")
        self.assertIsNone(PRIVATE_PATH_RE.search(packet["source_card_path"]))

    def test_external_worker_packet_source_card_ref_is_redacted(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md")
        external_path = Path("C:/Users/private/secret-product-card.md")

        packet = factoryctl.build_worker_packet("handoff-packer", card, external_path)

        self.assertEqual(packet["source_card_path"], "external:secret-product-card.md")
        self.assertIsNone(PRIVATE_PATH_RE.search(packet["source_card_path"]))

    def test_memory_style_source_card_ref_cannot_preserve_paths(self) -> None:
        self.assertEqual(factoryctl.source_card_ref(Path("<memory>")), "external:memory")
        self.assertEqual(factoryctl.source_card_ref(Path("<C:/Users/private/card.md>")), "external:source-card")
        self.assertEqual(factoryctl.source_card_ref(Path("<private/path/card.md>")), "external:source-card")

    def test_public_worker_registry_matches_factoryctl_workers(self) -> None:
        registry = json.loads((ROOT / "agents" / "worker-registry.public.json").read_text(encoding="utf-8"))
        registered = {worker["worker_id"] for worker in registry["workers"]}

        self.assertEqual(registered, set(factoryctl.WORKERS))

    def test_worker_result_schema_allows_every_registered_output(self) -> None:
        schema = json.loads((ROOT / "schemas" / "worker-result.schema.json").read_text(encoding="utf-8"))
        allowed = set(schema["properties"]["record_type"]["enum"])
        outputs = {worker.output_field for worker in factoryctl.WORKERS.values()}

        self.assertEqual(allowed, outputs | {"human_gate_record"})

    def test_minimal_example_card_matches_hermes_ready_gate_constraints(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "minimal-hermes-project" / "card.md")
        self.assertEqual(factoryctl.validate_card(card), [])

    def test_vfinal_card_requires_core_canonical_contracts(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        self.assertEqual(factoryctl.validate_card(card), [])

        incomplete = dict(card)
        incomplete.pop("product_sot")
        incomplete.pop("spec_graph")

        errors = factoryctl.validate_card(incomplete)

        self.assertIn("OVERKILL_VFINAL card missing core contracts: product_sot, spec_graph", errors)

    def test_vfinal_method_contract_requires_named_plan_fields(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["method_contract"] = dict(card["method_contract"])
        card["method_contract"]["required_plans"] = ["software_development_plan", "agent_eval_plan"]
        card.pop("agent_eval_plan", None)

        self.assertIn(
            "method_contract required plan agent_eval_plan is missing from card",
            factoryctl.validate_card(card),
        )

    def test_product_face_decomposition_requires_result_ref(self) -> None:
        card = dict(factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md"))
        card["phase"] = "F11"
        card.pop("product_face_result_ref", None)
        card.pop("product_face_result", None)

        self.assertIn(
            "product_face_result or product_face_result_ref required before decomposition/release",
            factoryctl.validate_card(card),
        )

    def test_vfinal_product_surface_requires_product_experience_os_contract(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["surfaces"] = ["frontend", "product-face"]
        card["capability_pack_contract"] = dict(card["capability_pack_contract"])
        card["capability_pack_contract"]["covered_surfaces"] = ["frontend", "product-face"]
        card.pop("product_experience_plan", None)
        card["product_face_packet"] = {"screen_inventory": ["dashboard"]}

        errors = factoryctl.validate_card(card)

        self.assertIn("product_experience_plan required for vFinal product-facing surfaces", errors)
        self.assertIn("product_face_packet.surface is required", errors)
        self.assertIn("product_face_packet.design_direction is required", errors)

    def test_vfinal_product_surface_accepts_product_experience_os_contract(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["surfaces"] = ["frontend", "product-face"]
        card["capability_pack_contract"] = dict(card["capability_pack_contract"])
        card["capability_pack_contract"]["covered_surfaces"] = ["frontend", "product-face"]
        card["method_contract"] = dict(card["method_contract"])
        card["method_contract"]["required_plans"] = ["software_development_plan", "product_experience_plan"]
        card["product_experience_plan"] = factoryctl.load_json_like(ROOT / "templates" / "product-experience-plan.json")
        card["product_face_packet"] = factoryctl.load_json_like(ROOT / "templates" / "product-face-packet.json")
        card["product_face_result_ref"] = ".tmp/factory-runs/product-face/product-face-result.json"

        self.assertEqual(factoryctl.validate_card(card), [])

    def test_product_face_completion_requires_visual_result(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_face_result_required"] = True
        receipt = {
            "receipt_five": {
                "changed": "validated visible SaaS scenario",
                "artifact_paths": ["examples/cards/v35_valid_product_face.md"],
                "verification_commands": ["python scripts/factoryctl.py validate-card examples/cards/v35_valid_product_face.md"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "pending",
                "next_action": "attach Product Face proof",
            },
            "kanban_transition_event": {
                "from_status": "review",
                "to_status": "done",
                "actor": "qa-verification-worker",
                "worker": "product-face",
                "receipt_refs": ["receipt_five"],
                "artifact_refs": ["examples/cards/v35_valid_product_face.md"],
            },
        }

        self.assertIn(
            "product_face_result metadata is required for product-facing completion",
            factoryctl.validate_completion(card, receipt),
        )

    def test_product_face_completion_accepts_visual_result(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_face_result_required"] = True
        receipt = {
            "receipt_five": {
                "changed": "validated visible SaaS scenario",
                "artifact_paths": ["examples/cards/v35_valid_product_face.md"],
                "verification_commands": ["python scripts/factoryctl.py validate-card examples/cards/v35_valid_product_face.md"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "PASS",
                "next_action": "ready for independent review",
            },
            "kanban_transition_event": {
                "from_status": "review",
                "to_status": "done",
                "actor": "qa-verification-worker",
                "worker": "product-face",
                "receipt_refs": ["receipt_five", "product_face_result"],
                "artifact_refs": ["examples/cards/v35_valid_product_face.md", "reports/product-face.md"],
                "allowed": True,
            },
            "independent_review_result": worker_result("independent_review_result", source_card=card),
            "product_face_result": {
                "result": "PASS",
                "tool_or_profile": "browser-proof-runner",
                "executed_by": "product-face-validator",
                "screenshots": ["reports/product-face/desktop.png", "reports/product-face/mobile.png"],
                "viewports": ["1440x900", "390x844"],
                "checked_states": ["empty", "loading", "pending", "success", "error"],
                "user_journeys_checked": ["dashboard to detail", "settings save"],
                "a11y": {"status": "pass", "keyboard": "pass", "labels": "pass", "contrast": "pass"},
                "overlap_check": {"status": "pass", "desktop": "pass", "mobile": "pass"},
                "performance_note": "static validation scenario only",
                "packet_ref": "examples/cards/v35_valid_product_face.md#product_face_packet",
                "packet_comparison": {
                    "status": "pass",
                    "basis": "All planned screens, states and viewports are covered."
                },
                "source_promise_coverage": {
                    "status": "pass",
                    "basis": "The result covers the visible SaaS validation promise in the card."
                },
                "design_fit_review": {
                    "status": "pass",
                    "basis": "The validator confirmed this bounded SaaS surface matches the Product Face packet."
                },
                "visual_quality_result": {
                    "status": "PASS",
                    "reviewer": "product-face-reviewer",
                    "basis": "The surface meets the Product Face packet quality bar and does not show AI-generic UI symptoms.",
                    "reference_quality_bar_checked": True,
                    "ai_generic_symptoms": [],
                },
                "blocking_findings": False,
                "evidence_refs": ["reports/product-face.md"],
                "next_action": "independent review",
            },
        }

        self.assertEqual(factoryctl.validate_completion(card, receipt), [])

    def test_product_face_completion_rejects_screenshot_without_plan_alignment(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_face_result_required"] = True
        receipt = {
            "receipt_five": {
                "changed": "validated visible SaaS scenario",
                "artifact_paths": ["examples/cards/v35_valid_product_face.md"],
                "verification_commands": ["python scripts/factoryctl.py validate-card examples/cards/v35_valid_product_face.md"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "PASS",
                "next_action": "ready for independent review",
            },
            "kanban_transition_event": {
                "from_status": "review",
                "to_status": "done",
                "actor": "qa-verification-worker",
                "worker": "product-face",
                "receipt_refs": ["receipt_five", "product_face_result"],
                "artifact_refs": ["examples/cards/v35_valid_product_face.md", "reports/product-face.md"],
            },
            "product_face_result": {
                "result": "PASS",
                "tool_or_profile": "browser-proof-runner",
                "executed_by": "product-face-validator",
                "screenshots": ["reports/product-face/desktop.png", "reports/product-face/mobile.png"],
                "viewports": ["desktop 1440x900", "mobile 390x844"],
                "checked_states": ["empty", "loading", "success", "error"],
                "user_journeys_checked": ["dashboard to detail", "settings save"],
                "a11y": {"status": "pass"},
                "overlap_check": {"status": "pass"},
                "console": {"status": "pass"},
                "performance_note": "static validation scenario only",
                "blocking_findings": False,
                "evidence_refs": ["reports/product-face.md"],
                "next_action": "independent review",
            },
        }

        errors = factoryctl.validate_completion(card, receipt)

        self.assertIn("product_face_result.packet_comparison is required for product-facing completion", errors)
        self.assertIn("product_face_result.source_promise_coverage is required for product-facing completion", errors)
        self.assertIn("product_face_result.design_fit_review is required for product-facing completion", errors)
        self.assertIn("product_face_result.visual_quality_result is required", errors)

    def test_product_face_completion_blocks_mechanically_ok_but_ai_generic_ui(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_face_result_required"] = True
        receipt = {
            "receipt_five": {
                "changed": "validated visible SaaS scenario",
                "artifact_paths": ["examples/cards/v35_valid_product_face.md"],
                "verification_commands": ["python scripts/factoryctl.py validate-card examples/cards/v35_valid_product_face.md"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "PASS",
                "next_action": "ready for independent review",
            },
            "kanban_transition_event": {
                "from_status": "review",
                "to_status": "done",
                "actor": "qa-verification-worker",
                "worker": "product-face",
                "receipt_refs": ["receipt_five", "product_face_result"],
                "artifact_refs": ["examples/cards/v35_valid_product_face.md", "reports/product-face.md"],
            },
            "product_face_result": {
                "result": "PASS",
                "tool_or_profile": "browser-proof-runner",
                "executed_by": "product-face-validator",
                "screenshots": ["reports/product-face/desktop.png", "reports/product-face/mobile.png"],
                "viewports": ["desktop 1440x900", "mobile 390x844"],
                "checked_states": ["empty", "loading", "success", "error"],
                "user_journeys_checked": ["dashboard to detail", "settings save"],
                "a11y": {"status": "pass"},
                "overlap_check": {"status": "pass"},
                "console": {"status": "pass"},
                "performance_note": "static validation scenario only",
                "packet_ref": "examples/cards/v35_valid_product_face.md#product_face_packet",
                "packet_comparison": {
                    "status": "pass",
                    "basis": "All planned screens, states and viewports are covered."
                },
                "source_promise_coverage": {
                    "status": "pass",
                    "basis": "The checked journey covers the product promise."
                },
                "design_fit_review": {
                    "status": "pass",
                    "basis": "Mechanical layout and state checks passed."
                },
                "visual_quality_result": {
                    "status": "BLOCK",
                    "reviewer": "product-face-reviewer",
                    "basis": "The UI uses a generic dashboard composition with excessive explanatory copy and no product-specific visual direction.",
                    "reference_quality_bar_checked": True,
                    "ai_generic_symptoms": ["generic dashboard composition", "excessive explanatory copy"],
                },
                "blocking_findings": False,
                "evidence_refs": ["reports/product-face.md"],
                "next_action": "redesign visual system",
            },
        }

        errors = factoryctl.validate_completion(card, receipt)

        self.assertIn("product_face_result visual_quality_result BLOCK prevents Product Face PASS", errors)
        self.assertIn("product_face_result PASS requires visual_quality_result.status PASS or PASS_WITH_RESIDUALS", errors)

    def test_product_face_pass_rejects_blocking_or_warning_result(self) -> None:
        result = {
            "result": "PASS",
            "tool_or_profile": "browser-proof-runner",
            "executed_by": "product-face-validator",
            "screenshots": ["not-captured: fake"],
            "viewports": ["1440x900"],
            "checked_states": ["initial-render"],
            "user_journeys_checked": ["open target"],
            "a11y": {"status": "warn", "issues": ["missing label"]},
            "overlap_check": {"status": "warn", "issues": ["overlap"]},
            "performance_note": "static validation scenario only",
            "blocking_findings": True,
            "evidence_refs": ["reports/product-face.md"],
            "next_action": "fix UI",
        }

        errors = factoryctl.validate_product_face_result(result)

        self.assertIn("product_face_result PASS requires blocking_findings=false", errors)
        self.assertIn("product_face_result screenshots must reference captured artifacts", errors)
        self.assertIn("product_face_result PASS requires a11y.status=pass", errors)
        self.assertIn("product_face_result PASS requires overlap_check.status=pass", errors)
        self.assertIn("product_face_result.visual_quality_result is required", errors)

    def test_auditor_preflight_cannot_claim_pass(self) -> None:
        bad = {
            "audit_mode": "preflight",
            "preflight_only": True,
            "result": "PASS",
            "findings_summary": "Auditor preflight only; no code audit claimed.",
            "evidence_refs": ["reports/auditor-preflight.md"],
        }

        self.assertIn(
            "auditor_result preflight must not use PASS; use WAIVED or PENDING with explicit boundary",
            factoryctl.validate_auditor_result(bad),
        )

    def test_auditor_code_audit_requires_deep_coverage_fields(self) -> None:
        incomplete = {
            "audit_mode": "code_audit",
            "result": "PASS",
            "findings_summary": "Real code audit claimed.",
            "evidence_refs": ["reports/auditor.md"],
        }

        errors = factoryctl.validate_auditor_result(incomplete)

        self.assertTrue(any(error.startswith("auditor_result code_audit missing") for error in errors))

    def test_auditor_code_audit_requires_sufficient_corpus_and_coverage(self) -> None:
        shallow = {
            "audit_mode": "code_audit",
            "result": "PASS",
            "findings_summary": "Real code audit claimed.",
            "evidence_refs": ["reports/auditor.md"],
            "auditor_head": "abc123",
            "corpus_files_loaded": ["README.md"],
            "checklist_coverage": {"01-program-account-validation": {"status": "done"}},
            "known_vectors_coverage": {"total": 2},
            "instruction_matrix": [{"instruction": "deposit"}],
            "state_model": {"accounts": ["vault"]},
            "quasar_toolchain_proof": {
                "install_source": "github:blueshift-gg/quasar",
                "source_head": "a89a9329f05740a20520607608b2b3b78c74f7c4",
                "rustc": "rustc 1.96.0",
                "cargo": "cargo 1.96.0",
                "solana": "solana-cli 4.0.1",
                "quasar": "quasar 0.0.0",
                "init_command": "quasar init factory-quasar-proof --yes --toolchain solana --test-language rust --rust-framework quasar-svm --template minimal --no-git",
                "build_command": "quasar build",
                "test_command": "quasar test",
                "build_status": "PASS",
                "test_status": "PASS",
                "evidence_refs": [".tmp/factory-runs/quasar-real-proof/quasar-source-proof-result.json"],
            },
            "findings": [],
            "waivers": [],
        }

        errors = factoryctl.validate_auditor_result(shallow)

        self.assertIn("auditor_result code_audit corpus_files_loaded must include at least 120 files", errors)
        self.assertIn("auditor_result code_audit missing program checklist coverage 02, 03, 04, 05, 06, 07", errors)
        self.assertIn("auditor_result code_audit known_vectors_coverage must cover at least 100 vectors", errors)

    def test_auditor_code_audit_allows_empty_findings_when_coverage_is_complete(self) -> None:
        complete = {
            "audit_mode": "code_audit",
            "result": "PASS",
            "findings_summary": "Real code audit claimed with no blocking finding.",
            "evidence_refs": ["reports/auditor.md"],
            "auditor_head": "abc123",
            "corpus_files_loaded": [f"auditor/file-{index}.md" for index in range(120)],
            "checklist_coverage": {
                "01-program-account-validation": {"status": "done"},
                "02-program-access-control": {"status": "done"},
                "03-program-arithmetic-safety": {"status": "done"},
                "04-program-cpi-pda": {"status": "done"},
                "05-program-state-machine": {"status": "done"},
                "06-program-economic-logic": {"status": "done"},
                "07-program-opsec-governance": {"status": "done"},
            },
            "known_vectors_coverage": {"total": 100},
            "instruction_matrix": [{"instruction": "deposit"}],
            "state_model": {"accounts": ["vault"], "pdas": ["vault"]},
            "quasar_toolchain_proof": {
                "install_source": "github:blueshift-gg/quasar",
                "source_head": "a89a9329f05740a20520607608b2b3b78c74f7c4",
                "rustc": "rustc 1.96.0",
                "cargo": "cargo 1.96.0",
                "solana": "solana-cli 4.0.1",
                "quasar": "quasar 0.0.0",
                "init_command": "quasar init factory-quasar-proof --yes --toolchain solana --test-language rust --rust-framework quasar-svm --template minimal --no-git",
                "build_command": "quasar build",
                "test_command": "quasar test",
                "build_status": "PASS",
                "test_status": "PASS",
                "evidence_refs": [".tmp/factory-runs/quasar-real-proof/quasar-source-proof-result.json"],
            },
            "findings": [],
            "waivers": [],
        }

        self.assertEqual(factoryctl.validate_auditor_result(complete), [])

    def test_auditor_code_audit_rejects_unpinned_quasar_crates_io_proof(self) -> None:
        proof = {
            "install_source": "crates.io:quasar-cli",
            "source_head": "",
            "rustc": "rustc 1.96.0",
            "cargo": "cargo 1.96.0",
            "solana": "solana-cli 4.0.1",
            "quasar": "quasar 0.0.0",
            "init_command": "quasar init factory-quasar-proof --toolchain solana --framework quasarsvm-rust --template minimal",
            "build_command": "quasar build",
            "test_command": "quasar test",
            "build_status": "PASS",
            "test_status": "PASS",
            "evidence_refs": [".tmp/factory-runs/quasar-real-proof/quasar-crates-proof-result.json"],
        }

        errors = factoryctl.validate_quasar_toolchain_proof(proof)

        self.assertIn(
            "auditor_result quasar_toolchain_proof cannot rely on crates.io quasar-cli without a source_head pin",
            errors,
        )

    def test_real_auditor_worker_result_uses_deep_validation(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        result = factoryctl.build_worker_result(
            "solana-quasar-auditor",
            card,
            result="PASS",
            tool_or_profile="solanabr/Auditor",
            executed_by="solana-quasar-auditor",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Real code audit claimed.",
            next_action="continue",
            evidence_kind="real",
        )

        errors = factoryctl.validate_worker_result_record(result, expected_field="auditor_result", expected_worker_id="solana-quasar-auditor", card=card, evidence_root=ROOT)

        self.assertTrue(any(error.startswith("auditor_result code_audit missing") for error in errors))

    def test_r3_without_scan_and_human_packet_is_invalid(self) -> None:
        card = load_card("v35_invalid_security_no_scan.md")
        errors = factoryctl.validate_card(card)

        self.assertIn("security_scan_packet required for R3/R4 work", errors)
        self.assertIn("human_gate_packet required for R3/R4 work", errors)

    def test_self_review_is_invalid(self) -> None:
        card = load_card("v35_invalid_self_review.md")
        self.assertIn("executor_identity and reviewer_identity must differ", factoryctl.validate_card(card))

    def test_pass_worker_result_requires_evidence(self) -> None:
        card = load_card("v35_valid_security_with_scan.md")

        with self.assertRaisesRegex(ValueError, "require at least one evidence ref"):
            factoryctl.build_worker_result(
                "codex-security",
                card,
                result="PASS",
                tool_or_profile="codex-security:security-scan",
                executed_by="security-runner",
                evidence_refs=[],
                blocking_findings=False,
                findings_summary="",
                next_action="",
            )

    def test_pass_worker_result_cannot_have_blocking_findings(self) -> None:
        card = load_card("v35_valid_security_with_scan.md")

        with self.assertRaisesRegex(ValueError, "PASS cannot have blocking_findings=true"):
            factoryctl.build_worker_result(
                "codex-security",
                card,
                result="PASS",
                tool_or_profile="codex-security:security-scan",
                executed_by="security-runner",
                evidence_refs=["reports/security.md"],
                blocking_findings=True,
                findings_summary="blocking issue",
                next_action="fix",
            )

    def test_real_specialist_result_requires_domain_contract_fields(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md")
        result = worker_result("appsec_owasp_result")
        result["evidence_kind"] = "real"
        result["reusable_for_product"] = True

        errors = factoryctl.validate_worker_result_record(
            result,
            expected_field="appsec_owasp_result",
            expected_worker_id="appsec-owasp-specialist",
            card=card,
            evidence_root=ROOT,
        )

        self.assertIn("covered_controls is required for real appsec_owasp_result", errors)
        self.assertIn("control_coverage is required for real appsec_owasp_result", errors)

    def test_codex_security_result_matches_hermes_completion_gate_fields(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md")
        result = factoryctl.build_worker_result(
            "codex-security",
            card,
            result="PASS",
            tool_or_profile="codex-security:scoped-security-scan",
            executed_by="codex-security-runner",
            evidence_refs=[".tmp/security-scan-report.md"],
            blocking_findings=False,
            findings_summary="No blocking dry-pilot finding.",
            next_action="Run full scan before production.",
        )

        self.assertEqual(result["scanner_agent"], "security-runner")
        self.assertEqual(result["tool"], "codex-security:scoped-security-scan")
        self.assertIn("PDA", " ".join(result["scope"]))

    def test_duplicate_worker_result_records_choose_latest_active_result(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md")
        result = factoryctl.build_worker_result(
            "codex-security",
            card,
            result="PASS",
            tool_or_profile="codex-security:security-scan",
            executed_by="codex-security-runner",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="No blocking finding.",
            next_action="continue",
        )

        with tempfile.TemporaryDirectory() as tmp:
            results_dir = Path(tmp)
            (results_dir / "a-security.json").write_text(json.dumps(result), encoding="utf-8")
            (results_dir / "z-security.json").write_text(json.dumps(result), encoding="utf-8")

            records = factoryctl.collect_worker_result_fields(card, results_dir)

        self.assertTrue(records["security_scan_result"]["valid"])
        self.assertEqual(records["security_scan_result"]["result"], "PASS")

    def test_inline_worker_result_requires_existing_evidence_ref_for_done(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        receipt = {
            "receipt_five": {
                "changed": "validated onchain gate",
                "artifact_paths": ["examples/minimal-hermes-project/card.md"],
                "verification_commands": ["python scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md"],
                "verification_result": "PASS",
                "reviewer_required": False,
                "next_action": "continue",
            },
            "kanban_transition_event": {
                "from_status": "ready",
                "to_status": "done",
                "actor": "factory-orchestrator",
                "worker": "factory-orchestrator",
                "receipt_refs": ["receipt_five", "security_scan_result"],
                "artifact_refs": ["examples/minimal-hermes-project/card.md"],
            },
            "security_scan_result": worker_result("security_scan_result"),
            "auditor_result": worker_result("auditor_result", result="WAIVED"),
            "independent_review_result": worker_result("independent_review_result"),
            "human_gate_record": human_gate_record(),
            "qa_verification_result": worker_result("qa_verification_result"),
            "autoreview_result": worker_result("autoreview_result"),
            "security_orchestration_result": worker_result("security_orchestration_result"),
            "remote_proof_result": worker_result("remote_proof_result"),
            "handoff_packet_result": worker_result("handoff_packet_result"),
            "supply_chain_result": worker_result("supply_chain_result"),
        }

        plan = factoryctl.build_transition_plan(
            card,
            ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md",
            from_status="ready",
            to_status="done",
            receipt=receipt,
        )

        self.assertEqual(plan["transition_action"], "block_transition")
        self.assertTrue(any("codex-security result is invalid before done" in reason for reason in plan["blocked_reasons"]))

    def test_receipt_security_result_requires_hermes_completion_gate_fields(self) -> None:
        bad_receipt = {
            "receipt_five": {
                "changed": "x",
                "artifact_paths": ["artifact"],
                "verification_commands": ["verify"],
                "verification_result": "PASS",
                "reviewer_required": False,
                "next_action": "none",
            },
            "kanban_transition_event": {},
            "security_scan_result": {
                "record_type": "security_scan_result",
                "result": "PASS",
                "evidence_refs": ["security.md"],
            },
        }

        errors = factoryctl.validate_receipt(bad_receipt)
        self.assertIn("security_scan_result missing scanner_agent, tool, findings_summary", errors)
        self.assertIn("security_scan_result scope must be a non-empty string array", errors)

    def test_minimal_example_receipt_matches_hermes_completion_gates(self) -> None:
        receipt = factoryctl.load_json_like(ROOT / "examples" / "minimal-hermes-project" / "expected-receipt-five.json")
        self.assertEqual(factoryctl.validate_receipt(receipt), [])
        self.assertTrue(receipt["public_safe"])
        self.assertIn("cto_gate", receipt["approvals"])

    def test_worker_result_builder_uses_specialized_bound_schema(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")

        auditor_result = factoryctl.build_worker_result(
            "solana-quasar-auditor",
            card,
            result="WAIVED",
            tool_or_profile="solanabr/Auditor-preflight",
            executed_by="solana-quasar-auditor",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Preflight only; no code audit is claimed.",
            next_action="run real Auditor code audit before promotion",
            evidence_kind="synthetic",
            reusable_for_product=False,
        )
        product_face_result = factoryctl.build_worker_result(
            "product-face",
            card,
            result="PASS",
            tool_or_profile="product-face-proof",
            executed_by="product-face",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Synthetic Product Face smoke.",
            next_action="run browser proof for real product",
            evidence_kind="synthetic",
            reusable_for_product=False,
        )

        self.assertEqual(auditor_result["$schema"], "https://overkill-factory.dev/schemas/auditor-result.schema.json")
        self.assertEqual(auditor_result["audit_mode"], "preflight")
        self.assertEqual(product_face_result["$schema"], "https://overkill-factory.dev/schemas/product-face-result.schema.json")
        self.assertIn("user_journeys_checked", product_face_result)
        self.assertIn("a11y", product_face_result)
        self.assertIn("overlap_check", product_face_result)

    def test_human_approval_requires_evidence(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")

        with self.assertRaisesRegex(ValueError, "approved human gates require"):
            factoryctl.build_human_gate_record(
                card,
                gate_type="R3",
                decision="approved",
                human_actor="product-owner",
                approved_scope=[],
                forbidden_scope=[],
                required_changes=[],
                risk_owner=None,
                security_owner=None,
                rollback_owner=None,
                evidence_refs=[],
                notes="",
            )

    def test_transition_plan_ready_creates_queued_worker_tasks(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="draft",
            to_status="ready",
        )
        queues = {task["worker_id"]: task["queue_class"] for task in plan["worker_tasks"]}

        self.assertEqual(plan["transition_action"], "block_and_create_before_ready_tasks")
        self.assertIn("factory-orchestrator result is required before ready", plan["blocked_reasons"])
        self.assertIn("supply-chain-gate result is required before ready", plan["blocked_reasons"])
        self.assertEqual(plan["gate_report"]["gate_status"], "ready_for_worker_execution")
        self.assertEqual(queues["factory-orchestrator"], "blocking-before-ready")
        self.assertEqual(queues["supply-chain-gate"], "blocking-before-ready")
        self.assertEqual(queues["codex-security"], "blocking-before-done")
        self.assertEqual(queues["solana-quasar-auditor"], "blocking-before-done")

    def test_hermes_schemas_allow_before_ready_block_action(self) -> None:
        action = "block_and_create_before_ready_tasks"
        transition_plan_schema = json.loads((ROOT / "schemas" / "hermes-transition-plan.schema.json").read_text(encoding="utf-8"))
        transition_hook_schema = json.loads((ROOT / "schemas" / "hermes-transition-hook.schema.json").read_text(encoding="utf-8"))
        worker_ledger_schema = json.loads((ROOT / "schemas" / "hermes-worker-ledger.schema.json").read_text(encoding="utf-8"))

        self.assertIn(action, transition_plan_schema["properties"]["transition_action"]["enum"])
        self.assertIn(action, transition_hook_schema["properties"]["transition_action"]["enum"])
        self.assertIn(action, worker_ledger_schema["properties"]["last_action"]["enum"])

    def test_transition_plan_enforce_blocks_before_ready_action(self) -> None:
        args = Namespace(
            card=ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md",
            receipt=None,
            from_status="draft",
            to_status="ready",
            worker_results_dir=None,
            out=None,
            enforce=True,
        )

        self.assertEqual(factoryctl.command_transition_plan(args), 1)

    def test_transition_plan_ready_blocks_missing_worker_inputs(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_product_face.md"
        card = factoryctl.load_json_like(card_path)
        card.pop("security_scan_packet", None)

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="draft",
            to_status="ready",
        )

        self.assertEqual(plan["transition_action"], "block_and_create_before_ready_tasks")
        self.assertIn("security-orchestrator missing inputs for blocking-before-ready", plan["blocked_reasons"])
        self.assertIn("appsec-owasp-specialist missing inputs for blocking-before-done", plan["blocked_reasons"])
        self.assertIn("factory-orchestrator result is required before ready", plan["blocked_reasons"])

    def test_transition_plan_done_blocks_missing_required_worker_results(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        receipt = {
            "receipt_five": {
                "changed": "x",
                "artifact_paths": ["artifact"],
                "verification_commands": ["verify"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "PASS",
                "next_action": "none",
            },
            "kanban_transition_event": {
                "from_status": "ready",
                "to_status": "done",
                "actor": "implementation-worker",
                "worker": "implementation-worker",
                "receipt_refs": ["receipt_five"],
                "artifact_refs": ["artifact"],
                "allowed": True,
            },
        }

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="ready",
            to_status="done",
            receipt=receipt,
        )

        self.assertEqual(plan["transition_action"], "block_transition")
        self.assertIn("codex-security result is required before done", plan["blocked_reasons"])
        self.assertIn("solana-quasar-auditor result is required before done", plan["blocked_reasons"])

    def test_transition_plan_done_allows_when_blocking_worker_results_exist(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        receipt = {
            "receipt_five": {
                "changed": "x",
                "artifact_paths": ["artifact"],
                "verification_commands": ["verify"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "PASS",
                "next_action": "none",
            },
            "kanban_transition_event": {
                "from_status": "ready",
                "to_status": "done",
                "actor": "implementation-worker",
                "worker": "implementation-worker",
                "receipt_refs": ["receipt_five"],
                "artifact_refs": ["artifact"],
                "allowed": True,
            },
            "security_scan_result": worker_result("security_scan_result", source_card=card),
            "auditor_result": worker_result("auditor_result", result="WAIVED", source_card=card),
            "independent_review_result": worker_result("independent_review_result", source_card=card),
            "human_gate_record": human_gate_record(source_card=card),
            "qa_verification_result": worker_result("qa_verification_result", source_card=card),
            "autoreview_result": worker_result("autoreview_result", source_card=card),
            "security_orchestration_result": worker_result("security_orchestration_result", source_card=card),
            "crypto_key_management_result": worker_result("crypto_key_management_result", source_card=card),
            "remote_proof_result": worker_result("remote_proof_result", source_card=card),
            "handoff_packet_result": worker_result("handoff_packet_result", source_card=card),
            "solana_quasar_build_result": worker_result("solana_quasar_build_result", source_card=card),
            "solana_quasar_qa_result": worker_result("solana_quasar_qa_result", source_card=card),
            "receipt_five_reconciliation_result": worker_result("receipt_five_reconciliation_result", source_card=card),
            "orchestration_result": worker_result("orchestration_result", source_card=card),
            "source_ledger_result": worker_result("source_ledger_result", source_card=card),
            "supply_chain_result": worker_result("supply_chain_result", source_card=card),
        }

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="ready",
            to_status="done",
            receipt=receipt,
        )

        self.assertEqual(plan["transition_action"], "allow_done")
        self.assertEqual(plan["blocked_reasons"], [])

    def test_transition_plan_done_blocks_weak_worker_result_shape(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        receipt = {
            "receipt_five": {
                "changed": "x",
                "artifact_paths": ["artifact"],
                "verification_commands": ["verify"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "PASS",
                "next_action": "none",
            },
            "kanban_transition_event": {
                "from_status": "ready",
                "to_status": "done",
                "actor": "implementation-worker",
                "worker": "implementation-worker",
                "receipt_refs": ["receipt_five"],
                "artifact_refs": ["artifact"],
            },
            "security_scan_result": {"record_type": "security_scan_result", "result": "PASS"},
            "auditor_result": worker_result("auditor_result", result="WAIVED"),
            "independent_review_result": worker_result("independent_review_result"),
            "human_gate_record": human_gate_record(),
            "qa_verification_result": worker_result("qa_verification_result"),
            "autoreview_result": worker_result("autoreview_result"),
            "security_orchestration_result": worker_result("security_orchestration_result"),
            "crypto_key_management_result": worker_result("crypto_key_management_result"),
            "remote_proof_result": worker_result("remote_proof_result"),
            "handoff_packet_result": worker_result("handoff_packet_result"),
            "receipt_five_reconciliation_result": worker_result("receipt_five_reconciliation_result"),
        }

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="ready",
            to_status="done",
            receipt=receipt,
        )

        self.assertEqual(plan["transition_action"], "block_transition")
        self.assertIn("codex-security result is invalid before done", plan["blocked_reasons"])
