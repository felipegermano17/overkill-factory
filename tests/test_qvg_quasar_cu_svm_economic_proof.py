import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import qvg_quasar_cu_svm_economic_proof as proof


class QvgQuasarCuSvmEconomicProofTests(unittest.TestCase):
    def test_parse_svm_markers_requires_real_cu_and_flows(self):
        markers = proof.parse_svm_markers(
            "\n".join(
                [
                    "OF_SVM_CU review_vault_instruction 1410",
                    "OF_SVM_FLOW review_vault_instruction PASS",
                    "OF_SVM_CU record_audit_receipt 1330",
                    "OF_SVM_FLOW record_audit_receipt PASS",
                    "OF_SVM_CU block_instruction 1180",
                    "OF_SVM_FLOW block_instruction PASS",
                    "OF_SVM_NEGATIVE review_zero_hash PASS",
                    "OF_SVM_ECONOMIC lamports_unchanged PASS",
                ]
            ),
            200_000,
        )

        self.assertTrue(markers["required_markers_present"])
        self.assertTrue(markers["all_cu_within_budget"])
        self.assertEqual(markers["instruction_profile"]["review_vault_instruction"]["compute_units_consumed"], 1410)

    def test_parse_svm_markers_fails_without_cu(self):
        markers = proof.parse_svm_markers("OF_SVM_FLOW review_vault_instruction PASS", 200_000)

        self.assertFalse(markers["required_markers_present"])
        self.assertFalse(markers["all_cu_within_budget"])

    def test_current_product_source_has_no_economic_mutation_surface(self):
        surface = proof.scan_source_economic_surface(
            proof.ROOT / "products" / "qvg-public-validation-product" / "onchain" / "quasar" / "src"
        )

        self.assertEqual(surface["cpi_markers_found"], [])
        self.assertEqual(surface["funds_markers_found"], [])
        self.assertEqual(surface["persistent_write_markers_found"], [])
        self.assertEqual(surface["authority_markers_found"], [])

    def test_svm_harness_is_public_and_json_serializable(self):
        harness = proof.svm_test_module("qvg-public-validation-product", 200_000)

        self.assertIn("production_svm_success_and_failure_matrix", harness)
        self.assertIn("OF_SVM_CU review_vault_instruction", harness)
        json.dumps({"harness_sha256": proof.sha256_text(harness)})

    def test_build_result_blocks_when_runtime_proof_source_hash_is_stale(self):
        with TemporaryDirectory() as source_tmp, TemporaryDirectory() as work_tmp:
            source_dir = Path(source_tmp)
            (source_dir / "lib.rs").write_text("pub fn review() {}\n", encoding="utf-8")
            runtime_proof = Path(work_tmp) / "runtime-proof.json"
            runtime_proof.write_text(
                json.dumps({"source_sha256": "0" * 64}),
                encoding="utf-8",
            )
            work_dir = Path(work_tmp)
            (work_dir / "build_status.txt").write_text("PASS", encoding="utf-8")
            (work_dir / "svm_test_status.txt").write_text("PASS", encoding="utf-8")
            (work_dir / "quasar_head.txt").write_text(proof.QUASAR_SOURCE_HEAD, encoding="utf-8")
            (work_dir / "quasar_ref.txt").write_text(proof.QUASAR_SOURCE_REF, encoding="utf-8")
            (work_dir / "svm-test.log").write_text(
                "\n".join(
                    [
                        "OF_SVM_CU review_vault_instruction 1410",
                        "OF_SVM_FLOW review_vault_instruction PASS",
                        "OF_SVM_CU record_audit_receipt 1330",
                        "OF_SVM_FLOW record_audit_receipt PASS",
                        "OF_SVM_CU block_instruction 1180",
                        "OF_SVM_FLOW block_instruction PASS",
                        "OF_SVM_FLOW sequential_review_record_block PASS",
                        "OF_SVM_NEGATIVE review_zero_hash PASS",
                        "OF_SVM_NEGATIVE record_zero_hash PASS",
                        "OF_SVM_NEGATIVE block_zero_reason PASS",
                        "OF_SVM_ECONOMIC lamports_unchanged PASS",
                        "OF_SVM_ECONOMIC pda_data_unchanged PASS",
                    ]
                ),
                encoding="utf-8",
            )
            completed = subprocess.CompletedProcess(args=["docker"], returncode=0, stdout="", stderr="")

            result = proof.build_result(
                source_dir=source_dir,
                runtime_proof_path=runtime_proof,
                work_dir=work_dir,
                completed=completed,
                started_at="2026-06-15T00:00:00+00:00",
                ended_at="2026-06-15T00:00:01+00:00",
                project_name="qvg-public-validation-product",
                compute_budget=200_000,
            )

        self.assertEqual(result["result"], "FAIL")
        self.assertFalse(result["runtime_source_match"]["matches"])
        self.assertTrue(result["runtime_source_match"]["blocking_for_this_proof"])


if __name__ == "__main__":
    unittest.main()
