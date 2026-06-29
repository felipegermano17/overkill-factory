from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "adapters" / "hermes" / "live_kanban_adapter.py"


def load_adapter():
    adapter_dir = str(ADAPTER_PATH.parent)
    if adapter_dir not in sys.path:
        sys.path.insert(0, adapter_dir)
    spec = importlib.util.spec_from_file_location("live_kanban_adapter", ADAPTER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class HermesAdapterV3ProductionActivationTest(unittest.TestCase):
    def test_adapter_passes_current_v3_activation_material(self) -> None:
        adapter = load_adapter()
        report = adapter.v3_production_activation_guard(ROOT)
        self.assertEqual(report["result"], "PASS", report.get("blockers"))
        self.assertEqual(report["runtime_authority"], "hermes_kanban")
        self.assertTrue(report["checks"]["master_plan_completion"])
        self.assertTrue(report["checks"]["agent_activation"])
        self.assertTrue(report["checks"]["factory_perfect_run_script"])

    def test_adapter_blocks_missing_agent_activation_version(self) -> None:
        adapter = load_adapter()
        profiles = json.loads((ROOT / "agents" / "worker-profiles.public.json").read_text())
        profiles.pop("production_activation_version", None)
        report = adapter.v3_production_activation_guard(ROOT, worker_profiles=profiles)
        self.assertEqual(report["result"], "BLOCKED")
        self.assertIn("worker profiles activation version", "\n".join(report["blockers"]))
    def test_adapter_enforces_v3_runtime_gate_contracts(self) -> None:
        adapter = load_adapter()
        report = adapter.v3_production_activation_guard(ROOT)
        for check in [
            "runtime_truth_spine",
            "canonical_frontier",
            "manager_agent_freshness_policy",
            "human_gate_artifact_first",
            "receipt_five_readback",
        ]:
            with self.subTest(check=check):
                self.assertTrue(report["checks"][check], report.get("blockers"))

    def test_adapter_blocks_when_runtime_truth_spine_allows_mini_hermes(self) -> None:
        adapter = load_adapter()
        runtime_truth = json.loads((ROOT / "templates" / "factory-runtime-truth-spine.json").read_text())
        runtime_truth["runtime_authority"]["factory_owns_queue"] = True
        runtime_truth["acceptance"]["no_mini_hermes"] = False
        report = adapter.v3_production_activation_guard(ROOT, runtime_truth=runtime_truth)
        self.assertEqual(report["result"], "BLOCKED")
        self.assertFalse(report["checks"]["runtime_truth_spine"])
        self.assertIn("runtime truth spine", "\n".join(report["blockers"]))

    def test_adapter_blocks_when_human_gate_is_not_artifact_first(self) -> None:
        adapter = load_adapter()
        readiness = json.loads((ROOT / "templates" / "factory-v3-release-readiness.json").read_text())
        readiness["human_gate_package"]["artifact_first"] = False
        report = adapter.v3_production_activation_guard(ROOT, release_readiness=readiness)
        self.assertEqual(report["result"], "BLOCKED")
        self.assertFalse(report["checks"]["human_gate_artifact_first"])


if __name__ == "__main__":
    unittest.main()
