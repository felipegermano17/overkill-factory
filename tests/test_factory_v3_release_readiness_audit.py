from __future__ import annotations

import importlib.util
import json
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
    def test_release_readiness_requires_factory_perfect_run_gate_and_commands(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text())
        report = module.audit(registry)
        self.assertEqual(report["result"], "PASS", report.get("errors"))
        perfect = registry["factory_perfect_run_policy"]
        self.assertTrue(perfect["release_blocks_without_factory_perfect_run"])
        self.assertIn("command:factoryctl factory-perfect-run", perfect["required_commands"])
        self.assertIn("command:factoryctl v3-production-activation-check --live-hermes", perfect["required_commands"])
        w09 = next(track for track in registry["readiness_tracks"] if track["id"] == "W09-factory-perfect-run")
        self.assertIn("scripts/factory_perfect_run.py", w09["evidence_refs"])
        self.assertIn("scripts/factory_hermes_live_smoke.py", w09["evidence_refs"])

    def test_release_readiness_blocks_if_perfect_run_release_gate_removed(self) -> None:
        module = load_module()
        registry = json.loads(REGISTRY_PATH.read_text())
        registry["factory_perfect_run_policy"].pop("release_blocks_without_factory_perfect_run", None)
        report = module.audit(registry)
        self.assertEqual(report["result"], "FAIL")
        self.assertIn("factory_perfect_run_policy.release_blocks_without_factory_perfect_run must be true", report["errors"])


if __name__ == "__main__":
    unittest.main()
