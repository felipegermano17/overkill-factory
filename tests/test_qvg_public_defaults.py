import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import qvg_product_like_auditor_result as auditor_result
from scripts import qvg_quasar_cu_fuzz_property_proof as property_proof
from scripts import quasar_product_like_container_proof as container_proof


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_HISTORICAL_PILOT = "pilots/quasar-vault-guard-test"


class QvgPublicDefaultsTests(unittest.TestCase):
    def test_product_like_container_defaults_use_existing_public_source(self):
        args = container_proof.parse_args([])

        self.assertEqual(args.source_dir, container_proof.PUBLIC_QVG_SOURCE_DIR)
        self.assertTrue(args.source_dir.exists())
        self.assertEqual(args.source_dir.relative_to(ROOT).as_posix(), "products/qvg-public-validation-product/onchain/quasar/src")
        self.assertEqual(args.project_name, "qvg-public-validation-product")

    def test_cu_fuzz_property_defaults_use_existing_public_source(self):
        args = property_proof.parse_args([])

        self.assertEqual(args.source_dir, property_proof.PUBLIC_QVG_SOURCE_DIR)
        self.assertTrue(args.source_dir.exists())
        self.assertEqual(args.source_dir.relative_to(ROOT).as_posix(), "products/qvg-public-validation-product/onchain/quasar/src")

    def test_auditor_result_default_card_uses_existing_public_fixture(self):
        with TemporaryDirectory() as tmpdir:
            args = auditor_result.parse_args(["--auditor-dir", tmpdir])

        self.assertEqual(args.card, auditor_result.PUBLIC_QVG_CARD)
        self.assertTrue(args.card.exists())
        self.assertEqual(args.card.relative_to(ROOT).as_posix(), "examples/cards/v35_valid_onchain_auditor_scan.md")

    def test_qvg_public_default_scripts_do_not_reference_historical_pilot(self):
        for script in (
            "scripts/quasar_product_like_container_proof.py",
            "scripts/qvg_quasar_cu_fuzz_property_proof.py",
            "scripts/qvg_product_like_auditor_result.py",
        ):
            text = (ROOT / script).read_text(encoding="utf-8")
            self.assertNotIn(FORBIDDEN_HISTORICAL_PILOT, text, script)


if __name__ == "__main__":
    unittest.main()
