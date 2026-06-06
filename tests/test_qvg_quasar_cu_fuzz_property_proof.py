import json
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from scripts import qvg_quasar_cu_fuzz_property_proof as proof


class QvgQuasarCuFuzzPropertyProofTests(unittest.TestCase):
    def test_mirror_property_cases_cover_expected_boundaries(self):
        cases = proof.mirror_property_cases()

        self.assertEqual(cases["hash_cases"]["total"], 256)
        self.assertEqual(cases["hash_cases"]["rejected"], 1)
        self.assertEqual(cases["reason_code_cases"]["accepted"], 255)
        self.assertEqual(cases["client_flow_cases"]["verdict"], "PASS")

    def test_compute_profile_is_explicitly_not_real_cu(self):
        profile = proof.build_compute_profile()

        self.assertEqual(profile["profile_kind"], "static_symbolic_upper_bound")
        self.assertFalse(profile["real_solana_cu_measured"])
        self.assertEqual(profile["instruction_profile"]["review_vault_instruction"]["cpi_calls"], 0)

    def test_source_contract_fails_when_required_property_tests_are_missing(self):
        with TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir)
            (source_dir / "tests.rs").write_text("#[test]\nfn tiny() {}\n", encoding="utf-8")

            result = proof.assert_source_contains_required_tests(source_dir)

            self.assertEqual(result["verdict"], "FAIL")
            self.assertIn("property_nonzero_hashes_are_accepted_for_deterministic_cases", result["missing"])

    def test_build_result_passes_with_current_public_source_and_runtime_proof(self):
        result = proof.build_result(
            proof.ROOT / "pilots" / "quasar-vault-guard-test" / "onchain" / "qvg-product-like" / "src",
            proof.ROOT / "validation" / "quasar-product-like-proof" / "qvg-quasar-runtime-proof.json",
        )

        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["property_fuzz_coverage"]["total_cases"], 513)
        self.assertFalse(result["reusable_for_product"])
        json.dumps(result)


if __name__ == "__main__":
    unittest.main()
