from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_manager_agent_freshness_audit.py"
REGISTRY_PATH = ROOT / "templates" / "factory-manager-agent-freshness-policy.json"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_manager_agent_freshness_audit", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryManagerAgentFreshnessAuditTest(unittest.TestCase):
    def test_manager_and_agents_must_be_updated_with_factory_changes(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        report = module.audit(registry)

        self.assertEqual("PASS", report["result"])
        self.assertTrue(registry["freshness_gate"]["required_for_every_factory_change"])
        self.assertIn("manager_profile", registry["freshness_gate"]["required_layers"])
        self.assertIn("agent_bindings", registry["freshness_gate"]["required_layers"])
        self.assertIn("skills", registry["freshness_gate"]["required_layers"])
        self.assertIn("configs", registry["freshness_gate"]["required_layers"])

    def test_manager_must_operate_factory_not_be_factory(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        manager = registry["manager_contract"]
        report = module.audit(registry)

        self.assertEqual("PASS", report["result"])
        self.assertFalse(manager["manager_may_replace_factory_code"])
        self.assertTrue(manager["must_call_current_factory_contracts"])
        self.assertIn("factory_master_update_plan_audit", manager["required_factory_audits"])
        self.assertIn("factory_runtime_truth_spine_audit", manager["required_factory_audits"])
        self.assertIn("factory_canonical_frontier_audit", manager["required_factory_audits"])

    def test_manager_only_operator_bridge_is_enforced(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        operator = registry["operator_bridge_policy"]
        report = module.audit(registry)

        self.assertEqual("PASS", report["result"])
        self.assertEqual("overkill-factory-gerente", operator["single_human_facing_profile"])
        self.assertFalse(operator["direct_worker_operator_contact_allowed"])
        self.assertFalse(operator["operator_polling_kanban_required"])

    def test_breaks_when_manager_can_replace_factory_code(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        broken = json.loads(json.dumps(registry))
        broken["manager_contract"]["manager_may_replace_factory_code"] = True

        report = module.audit(broken)

        self.assertEqual("FAIL", report["result"])
        self.assertTrue(any("manager" in error.lower() and "factory code" in error.lower() for error in report["errors"]), report["errors"])

    def test_breaks_without_freshness_smoke(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        broken = json.loads(json.dumps(registry))
        broken["freshness_smoke"]["required"] = False

        report = module.audit(broken)

        self.assertEqual("FAIL", report["result"])
        self.assertTrue(any("smoke" in error.lower() for error in report["errors"]), report["errors"])

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
            self.assertIn("Manager/Agent Freshness", text)
            self.assertIn("overkill-factory-gerente", text)


if __name__ == "__main__":
    unittest.main()
