import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import qvg_product_like_auditor_result as auditor_result
from scripts import qvg_quasar_cu_fuzz_property_proof as property_proof
from scripts import qvg_quasar_cu_svm_economic_proof as economic_proof
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

    def test_quasar_runtime_runners_pin_execution_inputs(self):
        for module in (container_proof, economic_proof):
            if module is economic_proof:
                script = module.docker_script("qvg-public-validation-product", 200_000)
            else:
                script = module.docker_script("qvg-public-validation-product")

            self.assertIn("@sha256:", module.RUST_CONTAINER_IMAGE)
            self.assertNotIn(":latest", module.RUST_CONTAINER_IMAGE)
            self.assertIn("/v4.0.2/install", module.SOLANA_INSTALL_URL)
            self.assertNotIn("/stable/", module.SOLANA_INSTALL_URL)
            self.assertIn('git fetch --depth 1 origin "$QUASAR_SOURCE_REF"', script)
            self.assertIn('test "$resolved_quasar_head" = "$QUASAR_SOURCE_HEAD"', script)
            self.assertNotIn("git clone --depth 1", script)
            self.assertNotIn("stable/install", script)

    def test_runtime_proof_fails_when_quasar_head_marker_does_not_match_declared_pin(self):
        with TemporaryDirectory() as source_tmp, TemporaryDirectory() as work_tmp:
            source_dir = Path(source_tmp)
            (source_dir / "lib.rs").write_text("pub fn qvg() {}\n", encoding="utf-8")
            work_dir = Path(work_tmp)
            (work_dir / "build_status.txt").write_text("PASS", encoding="utf-8")
            (work_dir / "test_status.txt").write_text("PASS", encoding="utf-8")
            (work_dir / "quasar_head.txt").write_text("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", encoding="utf-8")
            completed = subprocess.CompletedProcess(args=["docker"], returncode=0, stdout="", stderr="")

            result = container_proof.build_result(
                source_dir=source_dir,
                out=work_dir / "proof.json",
                work_dir=work_dir,
                completed=completed,
                started_at="2026-06-15T00:00:00+00:00",
                ended_at="2026-06-15T00:00:01+00:00",
                project_name="qvg-public-validation-product",
                proof_kind="containerized_product_like_quasar_build_test",
                evidence_boundary="test boundary",
                policy_decision="test decision",
            )

        self.assertEqual(result["result"], "FAIL")
        self.assertFalse(result["source_head_matches"])
        self.assertEqual(result["source_head_expected"], container_proof.QUASAR_SOURCE_HEAD)

    def test_auditor_result_does_not_pass_when_runtime_pin_did_not_match(self):
        with TemporaryDirectory() as auditor_tmp, TemporaryDirectory() as proof_tmp:
            auditor_dir = Path(auditor_tmp)
            (auditor_dir / "01-checklist.md").write_text("known vector coverage\n", encoding="utf-8")
            runtime_proof = {
                "result": "PASS",
                "source_head_matches": False,
                "source_ref": container_proof.QUASAR_SOURCE_REF,
                "source_head_expected": container_proof.QUASAR_SOURCE_HEAD,
                "source_head": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "container_image": container_proof.RUST_CONTAINER_IMAGE,
                "solana_release": container_proof.SOLANA_RELEASE,
                "solana_install_url": container_proof.SOLANA_INSTALL_URL,
                "install_source": container_proof.QUASAR_SOURCE,
                "source_target": "products/qvg-public-validation-product/onchain/quasar/src",
                "source_sha256": "1" * 64,
                "rustc": "rustc 1.91.0",
                "cargo": "cargo 1.91.0",
                "solana": "solana-cli 4.0.2",
                "quasar": "quasar 0.0.0",
                "init_command": "quasar init qvg-public-validation-product",
                "build_command": "quasar build",
                "test_command": "quasar test",
                "build_status": "PASS",
                "test_status": "PASS",
            }
            runtime_path = Path(proof_tmp) / "runtime.json"
            runtime_path.write_text(json.dumps(runtime_proof), encoding="utf-8")

            result = auditor_result.build_result(
                auditor_dir=auditor_dir,
                runtime_proof_path=runtime_path,
                property_proof_path=None,
                card_path=auditor_result.PUBLIC_QVG_CARD,
                report_path=Path(proof_tmp) / "report.md",
            )

        self.assertEqual(result["result"], "FAIL")
        self.assertTrue(result["blocking_findings"])
        self.assertFalse(result["quasar_toolchain_proof"]["source_head_matches"])


if __name__ == "__main__":
    unittest.main()
