import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import factory_completion_audit as audit


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
            self.assertEqual(result["score_estimate"], "9.996/10")
            self.assertGreater(result["requirements_blocking"], 0)

    def test_blocks_only_real_remaining_gaps_when_incomplete(self):
        result = audit.build_audit()
        blockers = set(result["blocking_summary"])

        self.assertNotIn("production_product_face", blockers)
        self.assertNotIn("production_quasar_auditor", blockers)
        if result["status"] == "COMPLETE":
            self.assertEqual(blockers, set())
        else:
            self.assertIn("managed_remote_proof", blockers)
            self.assertIn("production_release_human_gate", blockers)
            self.assertIn("full_product_specific_worker_graph", blockers)
            self.assertEqual(len(blockers), 3)

    def test_product_face_and_quasar_auditor_can_be_achieved_while_other_public_proofs_remain_bounded(self):
        result = audit.build_audit()
        by_id = {item["id"]: item for item in result["requirements"]}

        self.assertEqual(by_id["production_product_face"]["status"], "ACHIEVED")
        self.assertEqual(by_id["production_quasar_auditor"]["status"], "ACHIEVED")
        self.assertEqual(by_id["production_cu_svm_economic"]["status"], "ACHIEVED")
        self.assertIn(by_id["managed_remote_proof"]["status"], {"ACHIEVED", "BOUNDED_PUBLIC_PROOF"})
        self.assertIn(by_id["full_product_specific_worker_graph"]["status"], {"ACHIEVED", "BOUNDED_PUBLIC_PROOF"})

    def test_symbolic_cu_svm_result_cannot_clear_production_scope(self):
        proof_path = audit.ROOT / "validation" / "production" / "quasar" / "qvg-quasar-cu-fuzz-property-proof.json"
        symbolic = json.loads(proof_path.read_text(encoding="utf-8"))
        symbolic["record_type"] = "cu_svm_economic_proof"
        symbolic["proof_kind"] = "production_quasar_cu_svm_economic"
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
                "source_ref": "products/qvg-public-validation-product",
                "source_sha256": "a" * 64,
                "approval_scope": "Reusable only for the public validation product.",
            },
            "cleanup_evidence": {
                "lease_stopped": True,
                "active_local_container_leases_after": 0,
            },
            "remote_command": {"exit_code": 0},
            "checks_executed": [
                "python3 scripts/validate_public_json_artifacts.py",
                "python3 scripts/secret_safety_scan.py",
                "python3 scripts/public_safety_scan.py",
                "python3 scripts/full_product_worker_graph.py --require-pass",
            ],
        }

        self.assertTrue(audit.remote_proof_scope_is_valid(proof))
        proof["cleanup_evidence"]["lease_stopped"] = False
        self.assertFalse(audit.remote_proof_scope_is_valid(proof))

    def test_shallow_auditor_result_cannot_clear_production_scope(self):
        proof_path = audit.ROOT / "validation" / "production" / "quasar" / "auditor-result.json"
        shallow = json.loads(proof_path.read_text(encoding="utf-8"))
        shallow["product_target"]["source_ref"] = "pilots/quasar-vault-guard-test/onchain/qvg-product-like/src"

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
