from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_os_excellence_audit.py"
REGISTRY_PATH = ROOT / "templates" / "factory-os-excellence-audit-registry.json"
OS_REGISTRY_PATH = ROOT / "templates" / "factory-operating-system-registry.json"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_os_excellence_audit", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryOsExcellenceAuditTest(unittest.TestCase):
    def test_audit_covers_every_existing_operating_system(self) -> None:
        module = load_module()
        os_registry = module.load_json(OS_REGISTRY_PATH)
        audit_registry = module.load_json(REGISTRY_PATH)
        report = module.audit(audit_registry, os_registry)
        existing_os_ids = {entry["os_id"] for entry in os_registry["entries"]}
        audited_os_ids = {entry["os_id"] for entry in report["os_results"]}

        self.assertEqual("PASS", report["result"])
        self.assertEqual(100, report["score"])
        self.assertEqual(existing_os_ids, audited_os_ids)
        self.assertEqual(17, report["summary"]["os_count"])
        self.assertEqual(14, report["summary"]["p0_count"])
        self.assertGreaterEqual(report["summary"]["partial_or_blocked_count"], 12)

    def test_audit_separates_contract_runtime_and_product_specific_proof(self) -> None:
        module = load_module()
        os_registry = module.load_json(OS_REGISTRY_PATH)
        audit_registry = module.load_json(REGISTRY_PATH)
        report = module.audit(audit_registry, os_registry)

        hermes = next(entry for entry in report["os_results"] if entry["os_id"] == "hermes_worker_runtime_os")
        evidence = next(entry for entry in report["os_results"] if entry["os_id"] == "evidence_receipt_os")
        operator = next(entry for entry in report["os_results"] if entry["os_id"] == "operator_experience_os")

        self.assertEqual("runtime_blocked", hermes["audit_state"])
        self.assertIn("live_hermes_worker_orchestration", hermes["missing_or_partial_proofs"])
        self.assertEqual("contract_active_product_proof_needed", evidence["audit_state"])
        self.assertIn("product_specific_proof_bundle", evidence["missing_or_partial_proofs"])
        self.assertEqual("contract_active_product_proof_needed", operator["audit_state"])
        self.assertIn("proactive_status_event", operator["missing_or_partial_proofs"])

    def test_prior_audit_rounds_are_mapped_to_os_owners(self) -> None:
        module = load_module()
        audit_registry = module.load_json(REGISTRY_PATH)
        mapping = audit_registry["prior_audit_mapping"]

        self.assertIn("method_excellence_audit", mapping)
        self.assertIn("method_os", mapping["method_excellence_audit"]["primary_os"])
        self.assertIn("security_os", mapping["security_excellence_audit"]["primary_os"])
        self.assertIn("operator_experience_os", mapping["operator_ui_ux_excellence_audit"]["primary_os"])
        self.assertIn("capability_provider_os", mapping["solana_ai_kit_mandatory_routing"]["primary_os"])

    def test_audit_fails_if_an_existing_os_is_missing_from_findings(self) -> None:
        module = load_module()
        os_registry = module.load_json(OS_REGISTRY_PATH)
        audit_registry = module.load_json(REGISTRY_PATH)
        broken = json.loads(json.dumps(audit_registry))
        broken["os_findings"] = [
            entry for entry in broken["os_findings"] if entry["os_id"] != "security_os"
        ]

        report = module.audit(broken, os_registry)

        self.assertEqual("FAIL", report["result"])
        self.assertTrue(any("security_os" in error for error in report["errors"]), report["errors"])

    def test_audit_fails_if_registry_claims_os_is_implementation_complete(self) -> None:
        module = load_module()
        os_registry = module.load_json(OS_REGISTRY_PATH)
        audit_registry = module.load_json(REGISTRY_PATH)
        broken = json.loads(json.dumps(audit_registry))
        broken["completion_claim_policy"]["audit_allows_master_plan_to_claim_implementation_complete"] = True

        report = module.audit(broken, os_registry)

        self.assertEqual("FAIL", report["result"])
        self.assertTrue(any("implementation_complete" in error for error in report["errors"]), report["errors"])

    def test_cli_writes_json_and_markdown(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "audit.json"
            md = Path(tmpdir) / "audit.md"
            exit_code = module.main([
                "--registry",
                str(REGISTRY_PATH),
                "--os-registry",
                str(OS_REGISTRY_PATH),
                "--out",
                str(out),
                "--markdown",
                str(md),
            ])
            self.assertEqual(0, exit_code)
            payload = json.loads(out.read_text())
            text = md.read_text()
            self.assertEqual("PASS", payload["result"])
            self.assertIn("Factory OS Excellence Audit", text)
            self.assertIn("deterministic_control_plane_os", text)
            self.assertIn("operator_experience_os", text)
            self.assertIn("master plan", text.lower())


if __name__ == "__main__":
    unittest.main()
