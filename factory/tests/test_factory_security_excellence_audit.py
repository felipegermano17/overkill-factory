from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_security_excellence_audit.py"
REGISTRY_PATH = ROOT / "templates" / "factory-security-excellence-registry.json"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_security_excellence_audit", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactorySecurityExcellenceAuditTest(unittest.TestCase):
    def test_valid_registry_passes_and_exposes_security_gaps(self) -> None:
        module = load_module()
        audit = module.build_security_excellence_audit(REGISTRY_PATH)
        pillar_keys = {item["pillar_key"] for item in audit["pillar_coverage"]}

        self.assertEqual(audit["record_type"], "factory_security_excellence_audit")
        self.assertEqual(audit["result"], "PASS")
        self.assertGreaterEqual(audit["summary"]["partial_or_missing_count"], 6)
        self.assertIn("secure_by_design_culture", pillar_keys)
        self.assertIn("threat_modeling_abuse_cases", pillar_keys)
        self.assertIn("ai_agentic_security", pillar_keys)
        self.assertIn("solana_onchain_security", pillar_keys)
        self.assertIn("observability_detection_incident", pillar_keys)

    def test_late_security_posture_fails(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        registry["security_culture_policy"]["security_before_implementation"] = False
        registry["security_culture_policy"]["security_is_culture_not_checklist"] = False
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            audit = module.build_security_excellence_audit(path)

        self.assertEqual(audit["result"], "FAIL")
        joined = "\n".join(audit["errors"])
        self.assertIn("security_before_implementation", joined)
        self.assertIn("security_is_culture_not_checklist", joined)

    def test_false_perfection_claim_fails(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        registry["security_culture_policy"]["forbid_unqualified_perfection_claims"] = False
        registry["security_culture_policy"]["allowed_security_claim_language"] = "architecturally perfect security"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            audit = module.build_security_excellence_audit(path)

        self.assertEqual(audit["result"], "FAIL")
        joined = "\n".join(audit["errors"])
        self.assertIn("unqualified perfection", joined)

    def test_missing_required_pillar_fails(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        registry["pillar_coverage"] = [
            item for item in registry["pillar_coverage"] if item["pillar_key"] != "ai_agentic_security"
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            audit = module.build_security_excellence_audit(path)

        self.assertEqual(audit["result"], "FAIL")
        self.assertTrue(any("ai_agentic_security" in error for error in audit["errors"]))

    def test_solana_security_requires_solana_ai_kit(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        solana = next(item for item in registry["pillar_coverage"] if item["pillar_key"] == "solana_onchain_security")
        solana["required_artifacts"] = ["generic onchain review"]
        solana["existing_controls"] = ["generic external Solana agent"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            audit = module.build_security_excellence_audit(path)

        self.assertEqual(audit["result"], "FAIL")
        joined = "\n".join(audit["errors"])
        self.assertIn("Solana AI Kit", joined)

    def test_markdown_names_security_culture_and_architecture_first(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "audit.json"
            markdown = Path(tmp) / "audit.md"
            exit_code = module.main([
                "--registry", str(REGISTRY_PATH),
                "--out", str(out),
                "--markdown", str(markdown),
            ])
            text = markdown.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn("Security Excellence", text)
        self.assertIn("security is culture", text)
        self.assertIn("architecture-first", text)
        self.assertIn("best possible with evidence", text)
