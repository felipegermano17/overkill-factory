from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_method_excellence_audit.py"
REGISTRY_PATH = ROOT / "templates" / "factory-method-excellence-registry.json"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_method_excellence_audit", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryMethodExcellenceAuditTest(unittest.TestCase):
    def test_valid_registry_materializes_world_class_method_scorecard(self) -> None:
        module = load_module()
        audit = module.build_method_excellence_audit(REGISTRY_PATH)

        self.assertEqual(audit["record_type"], "factory_method_excellence_audit")
        self.assertEqual(audit["result"], "PASS")
        self.assertGreaterEqual(audit["score"], 95)
        self.assertIn("Hermes", audit["runtime_boundary"])
        self.assertIn("Overkill Factory", audit["method_boundary"])
        self.assertGreaterEqual(len(audit["method_families"]), 11)
        family_ids = {family["family_id"] for family in audit["method_families"]}
        for required in module.REQUIRED_METHOD_FAMILY_IDS:
            with self.subTest(required=required):
                self.assertIn(required, family_ids)
        self.assertFalse(audit["errors"])

    def test_audit_writes_json_and_markdown_for_context_proof_handoff(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "method-excellence.json"
            markdown = Path(tmp) / "method-excellence.md"
            exit_code = module.main(["--registry", str(REGISTRY_PATH), "--out", str(out), "--markdown", str(markdown)])
            self.assertEqual(exit_code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            text = markdown.read_text(encoding="utf-8")

        self.assertEqual(data["result"], "PASS")
        self.assertIn("Factory Method Excellence Audit", text)
        self.assertIn("not a mini-Hermes", text)
        self.assertIn("reference-quality product methodology", text)
        self.assertIn("method labels cannot authorize execution", text)

    def test_missing_core_method_family_fails_closed(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        registry["method_families"] = [
            family for family in registry["method_families"] if family["family_id"] != "security_privacy_safety"
        ]
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "broken.json"
            broken.write_text(json.dumps(registry), encoding="utf-8")
            audit = module.build_method_excellence_audit(broken)

        self.assertEqual(audit["result"], "FAIL")
        self.assertTrue(any("security_privacy_safety" in error for error in audit["errors"]))

    def test_shallow_method_family_without_proof_workers_or_gates_fails(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        registry["method_families"][0]["proof_requirements"] = []
        registry["method_families"][0]["required_workers"] = []
        registry["method_families"][0]["required_gates"] = []
        registry["method_families"][0]["forbidden_shortcuts"] = []
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "broken.json"
            broken.write_text(json.dumps(registry), encoding="utf-8")
            audit = module.build_method_excellence_audit(broken)

        self.assertEqual(audit["result"], "FAIL")
        joined = "\n".join(audit["errors"])
        self.assertIn("proof_requirements", joined)
        self.assertIn("required_workers", joined)
        self.assertIn("required_gates", joined)
        self.assertIn("forbidden_shortcuts", joined)

    def test_method_label_policy_and_hermes_boundary_are_required(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        registry["coverage_policy"]["method_label_cannot_authorize_execution"] = False
        registry["runtime_boundary"]["hermes_owns_runtime_floor"] = False
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "broken.json"
            broken.write_text(json.dumps(registry), encoding="utf-8")
            audit = module.build_method_excellence_audit(broken)

        self.assertEqual(audit["result"], "FAIL")
        joined = "\n".join(audit["errors"])
        self.assertIn("method_label_cannot_authorize_execution", joined)
        self.assertIn("hermes_owns_runtime_floor", joined)

    def test_existing_method_engine_ids_are_covered_by_excellence_registry(self) -> None:
        module = load_module()
        audit = module.build_method_excellence_audit(REGISTRY_PATH)
        covered = set(audit["covered_method_engine_ids"])
        for engine_id in module.REQUIRED_LEGACY_ENGINE_IDS:
            with self.subTest(engine_id=engine_id):
                self.assertIn(engine_id, covered)
