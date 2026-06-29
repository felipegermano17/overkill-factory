from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_world_class_process_gap_audit.py"
REGISTRY_PATH = ROOT / "templates" / "factory-world-class-process-registry.json"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_world_class_process_gap_audit", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryWorldClassProcessGapAuditTest(unittest.TestCase):
    def test_valid_registry_passes_and_contains_new_processes(self) -> None:
        module = load_module()
        audit = module.build_world_class_process_gap_audit(REGISTRY_PATH)
        process_keys = {process["process_key"] for process in audit["processes"]}

        self.assertEqual(audit["record_type"], "factory_world_class_process_gap_audit")
        self.assertEqual(audit["result"], "PASS")
        self.assertGreaterEqual(audit["summary"]["new_or_partial_process_count"], 8)
        self.assertIn("prd_grade_product_requirements", process_keys)
        self.assertIn("system_design_review", process_keys)
        self.assertIn("go_to_market_distribution_review", process_keys)
        self.assertIn("product_analytics_plan", process_keys)

    def test_all_existing_or_reordered_only_fails(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        for process in registry["processes"]:
            process["coverage_status"] = "existing_core"
            process["integration_decision"] = "keep_existing"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            audit = module.build_world_class_process_gap_audit(path)

        self.assertEqual(audit["result"], "FAIL")
        self.assertTrue(any("must identify missing or partial world-class processes" in error for error in audit["errors"]))
        self.assertTrue(any("must not be only a reordering" in error for error in audit["errors"]))

    def test_missing_prd_or_system_design_fails(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        registry["processes"] = [
            process for process in registry["processes"]
            if process["process_key"] not in {"prd_grade_product_requirements", "system_design_review"}
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            audit = module.build_world_class_process_gap_audit(path)

        self.assertEqual(audit["result"], "FAIL")
        joined = "\n".join(audit["errors"])
        self.assertIn("prd_grade_product_requirements", joined)
        self.assertIn("system_design_review", joined)

    def test_processes_require_artifacts_gates_proofs_and_factory_shape(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        registry["processes"][0]["required_artifacts"] = []
        registry["processes"][0]["required_gates"] = []
        registry["processes"][0]["proof_requirements"] = []
        registry["processes"][0]["factory_shape"] = "phase"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            audit = module.build_world_class_process_gap_audit(path)

        self.assertEqual(audit["result"], "FAIL")
        joined = "\n".join(audit["errors"])
        self.assertIn("required_artifacts", joined)
        self.assertIn("required_gates", joined)
        self.assertIn("proof_requirements", joined)
        self.assertIn("factory_shape", joined)

    def test_markdown_names_prd_system_design_and_missing_processes(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "audit.json"
            markdown = Path(tmp) / "audit.md"
            exit_code = module.main(["--registry", str(REGISTRY_PATH), "--out", str(out), "--markdown", str(markdown)])
            text = markdown.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn("PRD-grade Product Requirements", text)
        self.assertIn("System Design Review", text)
        self.assertIn("missing_or_partial", text)
        self.assertIn("not just reorder", text)
