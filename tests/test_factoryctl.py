from __future__ import annotations

import importlib.util
import json
import re
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


def load_card(name: str) -> dict:
    return factoryctl.load_json_like(ROOT / "examples" / "cards" / name)


def worker_result(record_type: str, *, result: str = "PASS") -> dict:
    worker_id = {
        "security_scan_result": "codex-security",
        "auditor_result": "solana-quasar-auditor",
        "independent_review_result": "independent-reviewer",
        "qa_verification_result": "qa-verification-worker",
        "autoreview_result": "autoreview-gate",
        "security_orchestration_result": "security-orchestrator",
        "crypto_key_management_result": "crypto-key-management-specialist",
        "remote_proof_result": "remote-proof-runner",
        "handoff_packet_result": "handoff-packer",
    }.get(record_type, "fixture-worker")
    payload = {
        "record_type": record_type,
        "created_at": "2026-06-06T00:00:00+00:00",
        "worker": {"id": worker_id, "name": "Fixture Worker", "factory_phase": "F13"},
        "card_ref": {
            "card_id": "VAL-SOLANA-QUASAR-R3",
            "slice_id": "VAL_FACTORY_HEAVY_03",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["solana-quasar"],
        },
        "result": result,
        "blocking_findings": False,
        "findings_summary": "Synthetic passing fixture.",
        "tool_or_profile": "fixture-tool",
        "executed_by": "fixture-runner",
        "evidence_refs": ["reports/fixture.md"],
        "evidence_kind": "synthetic",
        "reusable_for_product": False,
        "next_action": "none",
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
    if result == "WAIVED":
        payload["waiver"] = {
            "owner": "fixture-owner",
            "reason": "Synthetic fixture boundary.",
            "expires_at": "2026-12-31T00:00:00+00:00",
            "reviewer_or_human_gate_ref": "reports/fixture.md",
            "compensating_controls": ["run real worker before production"],
            "evidence_refs": ["reports/fixture.md"],
        }
    return payload


def human_gate_record() -> dict:
    return {
        "record_type": "human_gate_record",
        "gate_type": "R3",
        "card_id": "VAL-SOLANA-QUASAR-R3",
        "card_ref": {
            "card_id": "VAL-SOLANA-QUASAR-R3",
            "slice_id": "VAL_FACTORY_HEAVY_03",
        },
        "decision": "approved",
        "human_actor": "product-owner",
        "decision_at": "2026-06-06T00:00:00+00:00",
        "approved_scope": ["dry validation"],
        "forbidden_scope": ["deploy"],
        "risk_owner": "product-owner",
        "security_owner": "security-owner",
        "rollback_owner": "release-owner",
        "evidence_refs": ["decisions/r3.md"],
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
        self.assertEqual(report["workers"]["remote-proof-runner"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["supply-chain-gate"]["status"], "requires_execution")

    def test_required_only_worker_packets_generate_only_triggered_workers(self) -> None:
        card_path = ROOT / "validation" / "cards" / "solana-quasar-r3.md"
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

    def test_worker_packet_source_card_ref_is_public_safe(self) -> None:
        card_path = ROOT / "validation" / "cards" / "solana-quasar-r3.md"
        card = factoryctl.load_json_like(card_path)

        packet = factoryctl.build_worker_packet("handoff-packer", card, card_path)

        self.assertEqual(packet["source_card_path"], "validation/cards/solana-quasar-r3.md")
        self.assertIsNone(PRIVATE_PATH_RE.search(packet["source_card_path"]))

    def test_external_worker_packet_source_card_ref_is_redacted(self) -> None:
        card = factoryctl.load_json_like(ROOT / "validation" / "cards" / "solana-quasar-r3.md")
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

    def test_pilot_card_matches_hermes_ready_gate_constraints(self) -> None:
        card = factoryctl.load_json_like(ROOT / "pilots" / "quasar-vault-guard-test" / "cards" / "qvg-first-slice.md")
        self.assertEqual(factoryctl.validate_card(card), [])

    def test_product_face_decomposition_requires_result_ref(self) -> None:
        card = dict(factoryctl.load_json_like(ROOT / "validation" / "cards" / "product-face-saas-r2.md"))
        card["phase"] = "F11"
        card.pop("product_face_result_ref", None)
        card.pop("product_face_result", None)

        self.assertIn(
            "product_face_result or product_face_result_ref required before decomposition/release",
            factoryctl.validate_card(card),
        )

    def test_product_face_completion_requires_visual_result(self) -> None:
        card = factoryctl.load_json_like(ROOT / "validation" / "cards" / "product-face-saas-r2.md")
        receipt = {
            "receipt_five": {
                "changed": "validated visible SaaS scenario",
                "artifact_paths": ["validation/cards/product-face-saas-r2.md"],
                "verification_commands": ["python scripts/factoryctl.py validate-card validation/cards/product-face-saas-r2.md"],
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
                "artifact_refs": ["validation/cards/product-face-saas-r2.md"],
            },
        }

        self.assertIn(
            "product_face_result metadata is required for product-facing completion",
            factoryctl.validate_completion(card, receipt),
        )

    def test_product_face_completion_accepts_visual_result(self) -> None:
        card = factoryctl.load_json_like(ROOT / "validation" / "cards" / "product-face-saas-r2.md")
        receipt = {
            "receipt_five": {
                "changed": "validated visible SaaS scenario",
                "artifact_paths": ["validation/cards/product-face-saas-r2.md"],
                "verification_commands": ["python scripts/factoryctl.py validate-card validation/cards/product-face-saas-r2.md"],
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
                "artifact_refs": ["validation/cards/product-face-saas-r2.md", "reports/product-face.md"],
            },
            "product_face_result": {
                "result": "PASS",
                "tool_or_profile": "browser-proof-runner",
                "executed_by": "product-face-validator",
                "screenshots": ["reports/product-face/desktop.png", "reports/product-face/mobile.png"],
                "viewports": ["1440x900", "390x844"],
                "checked_states": ["empty", "loading", "success", "error"],
                "user_journeys_checked": ["dashboard to detail", "settings save"],
                "a11y": {"keyboard": "pass", "labels": "pass", "contrast": "pass"},
                "overlap_check": {"desktop": "pass", "mobile": "pass"},
                "performance_note": "static validation scenario only",
                "blocking_findings": False,
                "evidence_refs": ["reports/product-face.md"],
                "next_action": "independent review",
            },
        }

        self.assertEqual(factoryctl.validate_completion(card, receipt), [])

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

    def test_codex_security_result_matches_hermes_completion_gate_fields(self) -> None:
        card = factoryctl.load_json_like(ROOT / "pilots" / "quasar-vault-guard-test" / "cards" / "qvg-first-slice.md")
        result = factoryctl.build_worker_result(
            "codex-security",
            card,
            result="PASS",
            tool_or_profile="codex-security:scoped-security-scan",
            executed_by="codex-security-runner",
            evidence_refs=["pilots/quasar-vault-guard-test/evidence/security-scan-report.md"],
            blocking_findings=False,
            findings_summary="No blocking dry-pilot finding.",
            next_action="Run full scan before production.",
        )

        self.assertEqual(result["scanner_agent"], "codex-security-runner")
        self.assertEqual(result["tool"], "codex-security:scoped-security-scan")
        self.assertIn("Product SOT", result["scope"])

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

    def test_pilot_receipt_matches_hermes_completion_gates(self) -> None:
        receipt = factoryctl.load_json_like(ROOT / "pilots" / "quasar-vault-guard-test" / "evidence" / "receipt-five-first-slice.json")
        self.assertEqual(factoryctl.validate_receipt(receipt), [])
        self.assertTrue(receipt["hermes_legacy_completion_required"])
        self.assertIn("cto_gate", receipt["approvals"])

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
        card_path = ROOT / "validation" / "cards" / "solana-quasar-r3.md"
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

    def test_transition_plan_ready_blocks_missing_worker_inputs(self) -> None:
        card_path = ROOT / "validation" / "cards" / "product-face-saas-r2.md"
        card = factoryctl.load_json_like(card_path)
        card.pop("security_scan_packet", None)

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="draft",
            to_status="ready",
        )

        self.assertEqual(plan["transition_action"], "block_and_create_before_ready_tasks")
        self.assertIn("security-orchestrator missing inputs for blocking-before-done", plan["blocked_reasons"])
        self.assertIn("appsec-owasp-specialist missing inputs for blocking-before-done", plan["blocked_reasons"])
        self.assertIn("factory-orchestrator result is required before ready", plan["blocked_reasons"])

    def test_transition_plan_done_blocks_missing_required_worker_results(self) -> None:
        card_path = ROOT / "validation" / "cards" / "solana-quasar-r3.md"
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
        card_path = ROOT / "validation" / "cards" / "solana-quasar-r3.md"
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
            "security_scan_result": worker_result("security_scan_result"),
            "auditor_result": worker_result("auditor_result", result="WAIVED"),
            "independent_review_result": worker_result("independent_review_result"),
            "human_gate_record": human_gate_record(),
            "qa_verification_result": worker_result("qa_verification_result"),
            "autoreview_result": worker_result("autoreview_result"),
            "security_orchestration_result": worker_result("security_orchestration_result"),
            "crypto_key_management_result": worker_result("crypto_key_management_result"),
            "remote_proof_result": worker_result("remote_proof_result"),
            "handoff_packet_result": worker_result("handoff_packet_result"),
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
        card_path = ROOT / "validation" / "cards" / "solana-quasar-r3.md"
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
