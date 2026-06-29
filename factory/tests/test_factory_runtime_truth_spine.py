from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_runtime_truth_spine_audit.py"
REGISTRY_PATH = ROOT / "templates" / "factory-runtime-truth-spine.json"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_runtime_truth_spine_audit", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryRuntimeTruthSpineTest(unittest.TestCase):
    def test_runtime_truth_spine_is_hermes_kanban_first(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        report = module.audit(registry)

        self.assertEqual("PASS", report["result"])
        self.assertTrue(report["runtime_authority"]["hermes_kanban_owns_runtime"])
        self.assertFalse(report["runtime_authority"]["factory_owns_scheduler"])
        self.assertFalse(report["runtime_authority"]["factory_owns_queue"])
        self.assertFalse(report["runtime_authority"]["factory_owns_dispatch"])

    def test_packet_dispatch_execution_and_result_are_distinct(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        lifecycle_ids = {state["id"] for state in registry["worker_lifecycle_states"]}

        self.assertIn("worker_packet_created", lifecycle_ids)
        self.assertIn("hermes_dispatch_requested", lifecycle_ids)
        self.assertIn("hermes_task_running", lifecycle_ids)
        self.assertIn("worker_result_consumable", lifecycle_ids)
        self.assertNotEqual(
            registry["state_equivalence_policy"]["worker_packet_created"],
            registry["state_equivalence_policy"]["worker_result_consumable"],
        )

    def test_parent_resume_requires_durable_dependency_edges(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        report = module.audit(registry)
        resume = registry["parent_resume_policy"]

        self.assertEqual("PASS", report["result"])
        self.assertTrue(resume["requires_durable_dependency_edges"])
        self.assertTrue(resume["requires_child_result_consumable"])
        self.assertIn("Hermes/Kanban dependency edge readback", resume["required_readbacks"])

    def test_breaks_when_packet_is_treated_as_execution(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        broken = json.loads(json.dumps(registry))
        broken["state_equivalence_policy"]["worker_packet_created"] = "worker_result_consumable"

        report = module.audit(broken)

        self.assertEqual("FAIL", report["result"])
        self.assertTrue(any("packet" in error.lower() for error in report["errors"]), report["errors"])

    def test_breaks_when_runtime_boundary_reimplements_hermes(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        broken = json.loads(json.dumps(registry))
        broken["runtime_authority"]["factory_owns_scheduler"] = True

        report = module.audit(broken)

        self.assertEqual("FAIL", report["result"])
        self.assertTrue(any("mini-Hermes" in error or "scheduler" in error for error in report["errors"]), report["errors"])

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
            self.assertIn("Runtime Truth Spine", text)
            self.assertIn("worker_packet_created", text)
            self.assertIn("Hermes/Kanban", text)


if __name__ == "__main__":
    unittest.main()
