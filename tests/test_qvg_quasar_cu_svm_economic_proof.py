import json
import unittest

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


if __name__ == "__main__":
    unittest.main()
