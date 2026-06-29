from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_v3_release_readiness_audit.py"
REGISTRY_PATH = ROOT / "templates" / "factory-v3-release-readiness.json"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_v3_release_readiness_audit", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryV3ReleaseReadinessAuditTest(unittest.TestCase):
    def test_v3_release_readiness_covers_waves_4_to_9(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        report = module.audit(registry)

        self.assertEqual("PASS", report["result"])
        self.assertEqual("V3", registry["release_target"])
        self.assertEqual(
            {
                "W04-human-gate-package",
                "W05-receipt-five-anti-overclaim",
                "W06-product-method-architecture",
                "W07-capability-security-release-authority",
                "W08-public-github-v3",
                "W09-factory-perfect-run",
            },
            {item["id"] for item in registry["readiness_tracks"]},
        )

    def test_human_gate_is_artifact_first_not_approval_prompt(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        human_gate = registry["human_gate_package"]
        report = module.audit(registry)

        self.assertEqual("PASS", report["result"])
        self.assertTrue(human_gate["artifact_first"])
        self.assertTrue(human_gate["pdf_or_plain_text_fallback_required"])
        self.assertTrue(human_gate["delivery_receipt_required"])
        self.assertFalse(human_gate["raw_json_primary_surface_allowed"])

    def test_receipt_five_blocks_overclaim(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        receipt = registry["receipt_five_policy"]
        report = module.audit(registry)

        self.assertEqual("PASS", report["result"])
        self.assertTrue(receipt["readback_required"])
        self.assertFalse(receipt["contract_pass_means_done"])
        self.assertFalse(receipt["scaffold_or_template_counts_as_evidence"])
        self.assertIn("release_pass", receipt["completion_classes"])

    def test_security_release_and_solana_authority_are_explicit(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        authority = registry["authority_policy"]
        report = module.audit(registry)

        self.assertEqual("PASS", report["result"])
        self.assertTrue(authority["solana_ai_kit_required_for_solana"])
        self.assertTrue(authority["release_gate_separate_from_tests"])
        self.assertIn("R4", authority["explicit_authority_required_for"])
        self.assertIn("mainnet", authority["explicit_authority_required_for"])

    def test_public_github_surface_is_v3_and_simple(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        public = registry["public_github_policy"]
        report = module.audit(registry)

        self.assertEqual("PASS", report["result"])
        self.assertEqual("V3", public["release_label"])
        self.assertTrue(public["public_map_must_be_simplified"])
        self.assertTrue(public["first_value_path_required"])
        self.assertFalse(public["private_context_allowed"])

    def test_breaks_when_release_is_not_v3(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        broken = json.loads(json.dumps(registry))
        broken["release_target"] = "V2"
        broken["public_github_policy"]["release_label"] = "V2"

        report = module.audit(broken)

        self.assertEqual("FAIL", report["result"])
        self.assertTrue(any("V3" in error for error in report["errors"]), report["errors"])

    def test_breaks_when_fake_human_gate_is_allowed(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        broken = json.loads(json.dumps(registry))
        broken["human_gate_package"]["fake_human_gate_allowed"] = True

        report = module.audit(broken)

        self.assertEqual("FAIL", report["result"])
        self.assertTrue(any("fake" in error.lower() for error in report["errors"]), report["errors"])

    def test_cli_writes_json_and_markdown(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "audit.json"
            md = Path(tmpdir) / "audit.md"
            exit_code = module.main([
                "--registry",
                str(REGISTRY_PATH),
                "--out",
                str(out),
                "--markdown",
                str(md),
            ])
            self.assertEqual(0, exit_code)
            payload = json.loads(out.read_text())
            text = md.read_text()
            self.assertEqual("PASS", payload["result"])
            self.assertIn("Factory V3 Release Readiness", text)
            self.assertIn("Public GitHub V3", text)
            self.assertIn("Factory Perfect Run", text)


if __name__ == "__main__":
    unittest.main()
