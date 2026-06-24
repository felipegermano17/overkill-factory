import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import factory_completion_audit as audit


def sample_hermes_runtime_proof() -> dict:
    return {
        "$schema": "https://overkill-factory.dev/schemas/hermes-production-proof.schema.json",
        "record_type": "hermes_production_proof",
        "created_at": "2026-06-24T00:00:00Z",
        "proof_type": "non_stub_worker_execution",
        "result": "PASS",
        "summary": "Read-only Hermes runtime proof.",
        "scope": "redacted test runtime",
        "environment_ref": "external:redacted",
        "evidence_refs": ["external:redacted-hermes-status"],
        "runtime_summary": {
            "gateway_running": True,
            "openai_codex_logged_in": True,
            "telegram_configured": True,
            "profile_count": 42,
            "running_profile_count": 1,
            "manager_profile_running": True,
            "current_board_detected": True,
            "current_board_total_tasks": 8,
            "task_list_total": 8,
            "done_task_count": 7,
            "blocked_task_count": 1,
            "representative_done_run_count": 1,
            "representative_done_run_profiles": ["source-ledger-worker"],
            "live_worker_orchestration_proven": True,
            "human_gate_block_event_detected": True,
        },
        "operator_gate_boundary": {
            "human_gate_auto_approved": False,
            "human_gate_blocked_until_owner_decision": True,
            "bridge_or_manager_executed_gate": False,
        },
        "limits": ["Runtime proof only."],
    }


class FactoryCompletionAuditTests(unittest.TestCase):
    def test_current_public_factory_completion_state_is_consistent(self):
        result = audit.build_audit()

        if result["status"] == "COMPLETE":
            self.assertTrue(result["completion_claim_allowed"])
            self.assertEqual(result["score_estimate"], "10/10")
            self.assertEqual(result["requirements_blocking"], 0)
        else:
            self.assertEqual(result["status"], "NOT_COMPLETE")
            self.assertFalse(result["completion_claim_allowed"])
            self.assertEqual(result["score_estimate"], "9.992/10")
            self.assertGreater(result["requirements_blocking"], 0)
            self.assertEqual(len(result["blocker_economics"]), result["requirements_blocking"])

    def test_blocks_only_real_remaining_gaps_when_incomplete(self):
        result = audit.build_audit()
        blockers = set(result["blocking_summary"])
        blocker_ids = {item["blocker_id"] for item in result["blocker_economics"]}

        self.assertIn("production_product_face", blockers)
        self.assertIn("completion:production_product_face", blocker_ids)
        self.assertIn("production_quasar_auditor", blockers)
        self.assertIn("factory_operating_system_scorecard", blockers)
        if result["status"] == "COMPLETE":
            self.assertEqual(blockers, set())
        else:
            self.assertIn("full_product_specific_worker_graph", blockers)
            self.assertIn("managed_remote_proof", blockers)
            self.assertIn("production_release_human_gate", blockers)
            self.assertGreaterEqual(len(blockers), 9)

    def test_product_face_and_quasar_auditor_can_be_achieved_while_other_public_proofs_remain_bounded(self):
        result = audit.build_audit()
        by_id = {item["id"]: item for item in result["requirements"]}

        self.assertEqual(by_id["production_product_face"]["status"], "BLOCKED_MISSING_EVIDENCE")
        self.assertEqual(by_id["production_quasar_auditor"]["status"], "BLOCKED_MISSING_EVIDENCE")
        self.assertEqual(by_id["production_cu_svm_economic"]["status"], "BLOCKED_MISSING_EVIDENCE")
        self.assertEqual(by_id["managed_remote_proof"]["status"], "BLOCKED_MISSING_EVIDENCE")
        self.assertEqual(by_id["full_product_specific_worker_graph"]["status"], "BLOCKED_MISSING_EVIDENCE")
        self.assertEqual(by_id["factory_operating_system_scorecard"]["status"], "BLOCKED_MISSING_EVIDENCE")

    def test_runtime_proof_clears_only_runtime_backed_requirements(self):
        result = audit.build_audit(
            runtime_proofs=[sample_hermes_runtime_proof()],
            runtime_proof_refs=["external:redacted-hermes-runtime-proof"],
        )
        by_id = {item["id"]: item for item in result["requirements"]}

        self.assertEqual(by_id["hermes_real_worker_orchestration"]["status"], "ACHIEVED")
        self.assertEqual(by_id["live_agent_profile_layer"]["status"], "ACHIEVED")
        self.assertEqual(by_id["production_product_face"]["status"], "BLOCKED_MISSING_EVIDENCE")
        self.assertEqual(by_id["production_release_human_gate"]["status"], "BLOCKED_MISSING_EVIDENCE")
        self.assertEqual(result["status"], "NOT_COMPLETE")
        self.assertFalse(result["completion_claim_allowed"])

    def test_symbolic_cu_svm_result_cannot_clear_production_scope(self):
        symbolic = {
            "record_type": "cu_svm_economic_proof",
            "proof_kind": "production_quasar_cu_svm_economic",
            "source_target": "examples/minimal-hermes-project",
            "source_sha256": "a" * 64,
        }
        symbolic["product_target"] = {
            "product_id": "qvg-public-validation-product",
            "environment_class": "production-validation-quasar-svm",
            "source_ref": symbolic["source_target"],
            "source_sha256": symbolic["source_sha256"],
            "approval_scope": "Production-validation CU/SVM/economic lane",
        }
        symbolic["reusable_for_product"] = True

        self.assertFalse(audit.cu_svm_economic_scope_is_valid(symbolic))

    def test_remote_proof_scope_requires_crabbox_cleanup(self):
        proof = {
            "record_type": "remote_proof_result",
            "result": "PASS",
            "evidence_kind": "real",
            "reusable_for_product": True,
            "tool_or_profile": "crabbox local-container",
            "managed_by_crabbox": True,
            "provider_kind": "crabbox_ephemeral_container",
            "product_target": {
                "product_id": "qvg-public-validation-product",
                "source_ref": "fixtures/product-validation/qvg-public-validation-product",
                "source_sha256": "a" * 64,
                "approval_scope": "Reusable only for the QVG product-shaped validation fixture.",
            },
            "cleanup_evidence": {
                "lease_stopped": True,
                "active_local_container_leases_after": 0,
                "active_lease_count_known": True,
                "no_active_local_container_leases_after": True,
                "all_cleanup_confirmed": True,
            },
            "remote_command": {"exit_code": 0},
            "checks_executed": [
                "python3 scripts/validate_public_json_artifacts.py",
                "python3 scripts/secret_safety_scan.py",
                "python3 scripts/public_safety_scan.py",
                "python3 scripts/supply_chain_proof.py --check --no-write",
                "python3 scripts/full_product_worker_graph.py --require-pass",
            ],
            "proof_checks": {
                "required_markers": [
                    "public_json_artifacts",
                    "secret_safety",
                    "public_safety",
                    "supply_chain",
                    "full_product_worker_graph",
                ],
                "observed_markers": {
                    "public_json_artifacts": "PASS",
                    "secret_safety": "PASS",
                    "public_safety": "PASS",
                    "supply_chain": "PASS",
                    "full_product_worker_graph": "PASS",
                },
                "missing_markers": [],
                "failed_markers": [],
                "missing_commands": [],
                "all_required_passed": True,
            },
        }

        self.assertTrue(audit.remote_proof_scope_is_valid(proof))
        proof["cleanup_evidence"]["lease_stopped"] = False
        self.assertFalse(audit.remote_proof_scope_is_valid(proof))
        proof["cleanup_evidence"]["lease_stopped"] = True
        proof["cleanup_evidence"]["active_local_container_leases_after"] = None
        proof["cleanup_evidence"]["active_lease_count_known"] = False
        proof["cleanup_evidence"]["no_active_local_container_leases_after"] = False
        proof["cleanup_evidence"]["all_cleanup_confirmed"] = False
        self.assertFalse(audit.remote_proof_scope_is_valid(proof))

    def test_remote_proof_scope_requires_named_markers(self):
        proof = {
            "record_type": "remote_proof_result",
            "result": "PASS",
            "evidence_kind": "real",
            "reusable_for_product": True,
            "tool_or_profile": "crabbox local-container",
            "managed_by_crabbox": True,
            "provider_kind": "crabbox_ephemeral_container",
            "product_target": {
                "product_id": "qvg-public-validation-product",
                "source_ref": "fixtures/product-validation/qvg-public-validation-product",
                "source_sha256": "a" * 64,
                "approval_scope": "Reusable only for the QVG product-shaped validation fixture.",
            },
            "cleanup_evidence": {
                "lease_stopped": True,
                "active_local_container_leases_after": 0,
                "active_lease_count_known": True,
                "no_active_local_container_leases_after": True,
                "all_cleanup_confirmed": True,
            },
            "remote_command": {"exit_code": 0},
            "checks_executed": [
                "python3 scripts/validate_public_json_artifacts.py",
                "python3 scripts/secret_safety_scan.py",
                "python3 scripts/public_safety_scan.py",
                "python3 scripts/supply_chain_proof.py --check --no-write",
                "python3 scripts/full_product_worker_graph.py --require-pass",
            ],
            "proof_checks": {
                "required_markers": [
                    "public_json_artifacts",
                    "secret_safety",
                    "public_safety",
                    "supply_chain",
                    "full_product_worker_graph",
                ],
                "observed_markers": {
                    "public_json_artifacts": "PASS",
                    "secret_safety": "PASS",
                    "public_safety": "PASS",
                    "full_product_worker_graph": "PASS",
                },
                "missing_markers": ["supply_chain"],
                "failed_markers": [],
                "missing_commands": [],
                "all_required_passed": False,
            },
        }

        self.assertFalse(audit.remote_proof_scope_is_valid(proof))

    def test_shallow_auditor_result_cannot_clear_production_scope(self):
        shallow = {
            "record_type": "auditor_result",
            "result": "PASS",
            "evidence_kind": "real",
            "reusable_for_product": True,
            "product_target": {
                "product_id": "qvg-public-validation-product",
                "source_ref": "examples/minimal-hermes-project",
                "source_sha256": "a" * 64,
                "approval_scope": "shallow fixture",
            },
            "code_audit": {"coverage": "shallow"},
        }

        self.assertFalse(audit.reusable_product_scope_is_valid(shallow, record_type="auditor_result"))

    def test_require_complete_returns_nonzero_while_blocked(self):
        exit_code = audit.main(["--no-write", "--require-complete"])
        result = audit.build_audit()

        self.assertEqual(exit_code, 0 if result["status"] == "COMPLETE" else 1)

    def test_writes_schema_backed_json_and_markdown(self):
        with TemporaryDirectory() as tmpdir:
            exit_code = audit.main(["--out-dir", tmpdir])
            data_path = Path(tmpdir) / "factory-10-completion-audit.json"
            md_path = Path(tmpdir) / "factory-10-completion-audit.md"

            self.assertEqual(exit_code, 0)
            self.assertTrue(data_path.exists())
            self.assertTrue(md_path.exists())
            data = json.loads(data_path.read_text(encoding="utf-8"))
            self.assertEqual(data["$schema"], "https://overkill-factory.dev/schemas/factory-completion-audit.schema.json")


if __name__ == "__main__":
    unittest.main()
