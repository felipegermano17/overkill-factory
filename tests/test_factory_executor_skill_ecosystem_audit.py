from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_executor_skill_ecosystem_audit.py"
REGISTRY_PATH = ROOT / "templates" / "factory-executor-skill-ecosystem-registry.json"
WORKER_REGISTRY_PATH = ROOT / "agents" / "worker-registry.public.json"
SKILL_PROVIDER_PATH = ROOT / "agents" / "skill-provider-registry.public.json"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_executor_skill_ecosystem_audit", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryExecutorSkillEcosystemAuditTest(unittest.TestCase):
    def test_valid_registry_passes_and_finds_real_gaps(self) -> None:
        module = load_module()
        audit = module.build_executor_skill_ecosystem_audit(REGISTRY_PATH, WORKER_REGISTRY_PATH, SKILL_PROVIDER_PATH)
        demand_keys = {item["demand_key"] for item in audit["demand_coverage"]}

        self.assertEqual(audit["record_type"], "factory_executor_skill_ecosystem_audit")
        self.assertEqual(audit["result"], "PASS")
        self.assertGreaterEqual(audit["summary"]["missing_or_partial_executor_count"], 5)
        self.assertGreaterEqual(audit["summary"]["missing_or_partial_skill_count"], 5)
        self.assertIn("prd_grade_requirements", demand_keys)
        self.assertIn("system_design_review", demand_keys)
        self.assertIn("product_analytics", demand_keys)
        self.assertIn("go_to_market_distribution", demand_keys)
        self.assertTrue(audit["adaptive_capability_acquisition"]["enabled"])

    def test_all_demands_claiming_ready_fails(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        for item in registry["demand_coverage"]:
            item["executor_coverage_status"] = "ready"
            item["skill_coverage_status"] = "ready"
            item["recommendation"] = "keep_existing"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            audit = module.build_executor_skill_ecosystem_audit(path, WORKER_REGISTRY_PATH, SKILL_PROVIDER_PATH)

        self.assertEqual(audit["result"], "FAIL")
        self.assertTrue(any("must expose missing or partial executor coverage" in error for error in audit["errors"]))
        self.assertTrue(any("must expose missing or partial skill/provider coverage" in error for error in audit["errors"]))

    def test_missing_capability_acquisition_policy_fails(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        registry["adaptive_capability_acquisition"]["enabled"] = False
        registry["adaptive_capability_acquisition"]["trusted_provider_search_required"] = False
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            audit = module.build_executor_skill_ecosystem_audit(path, WORKER_REGISTRY_PATH, SKILL_PROVIDER_PATH)

        self.assertEqual(audit["result"], "FAIL")
        joined = "\n".join(audit["errors"])
        self.assertIn("adaptive_capability_acquisition.enabled", joined)
        self.assertIn("trusted_provider_search_required", joined)

    def test_registry_must_reference_real_workers_and_providers_or_mark_missing(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        registry["demand_coverage"][0]["current_worker_refs"] = ["nonexistent-worker"]
        registry["demand_coverage"][0]["executor_coverage_status"] = "ready"
        registry["demand_coverage"][0]["current_skill_provider_refs"] = ["nonexistent-skill"]
        registry["demand_coverage"][0]["skill_coverage_status"] = "ready"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            audit = module.build_executor_skill_ecosystem_audit(path, WORKER_REGISTRY_PATH, SKILL_PROVIDER_PATH)

        self.assertEqual(audit["result"], "FAIL")
        joined = "\n".join(audit["errors"])
        self.assertIn("unknown worker ref", joined)
        self.assertIn("unknown skill/provider ref", joined)

    def test_markdown_names_agents_skills_and_modular_adaptive_policy(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "audit.json"
            markdown = Path(tmp) / "audit.md"
            exit_code = module.main([
                "--registry", str(REGISTRY_PATH),
                "--worker-registry", str(WORKER_REGISTRY_PATH),
                "--skill-provider-registry", str(SKILL_PROVIDER_PATH),
                "--out", str(out),
                "--markdown", str(markdown),
            ])
            text = markdown.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn("Executor and Skill Ecosystem", text)
        self.assertIn("modular adaptive", text)
        self.assertIn("PRD-grade Requirements", text)
        self.assertIn("trusted provider search", text)
