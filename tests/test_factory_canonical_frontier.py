from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_canonical_frontier_audit.py"
REGISTRY_PATH = ROOT / "templates" / "factory-canonical-frontier-policy.json"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_canonical_frontier_audit", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryCanonicalFrontierAuditTest(unittest.TestCase):
    def test_canonical_frontier_keeps_no_idle_as_recovery_not_runtime(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        report = module.audit(registry)

        self.assertEqual("PASS", report["result"])
        self.assertTrue(registry["authority_model"]["hermes_kanban_state_required"])
        self.assertEqual("integrity_auditor_and_recovery_path", registry["authority_model"]["no_idle_role"])
        self.assertFalse(registry["authority_model"]["no_idle_is_scheduler"])

    def test_recoverable_gaps_route_to_repair_before_human(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        report = module.audit(registry)
        policy = registry["recoverable_gap_policy"]

        self.assertEqual("PASS", report["result"])
        self.assertTrue(policy["repair_before_needs_input"])
        self.assertIn("missing_declared_artifact", policy["recoverable_gap_types"])
        self.assertIn("stale_review_superseded_by_new_pass", policy["recoverable_gap_types"])

    def test_budgets_are_gates_not_scheduler(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        budgets = registry["budget_policy"]
        report = module.audit(registry)

        self.assertEqual("PASS", report["result"])
        self.assertEqual("gate_rule", budgets["retry_budget"]["authority"])
        self.assertEqual("gate_rule", budgets["repair_budget"]["authority"])
        self.assertEqual("gate_rule", budgets["worker_budget"]["authority"])
        self.assertFalse(budgets["budgets_schedule_work"])

    def test_breaks_when_no_idle_becomes_scheduler(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        broken = json.loads(json.dumps(registry))
        broken["authority_model"]["no_idle_is_scheduler"] = True
        broken["authority_model"]["no_idle_role"] = "scheduler"

        report = module.audit(broken)

        self.assertEqual("FAIL", report["result"])
        self.assertTrue(any("scheduler" in error.lower() for error in report["errors"]), report["errors"])

    def test_breaks_when_human_input_precedes_repair(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        broken = json.loads(json.dumps(registry))
        broken["recoverable_gap_policy"]["repair_before_needs_input"] = False

        report = module.audit(broken)

        self.assertEqual("FAIL", report["result"])
        self.assertTrue(any("repair" in error.lower() for error in report["errors"]), report["errors"])

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
            self.assertIn("Canonical Frontier", text)
            self.assertIn("repair_before_needs_input", text)


if __name__ == "__main__":
    unittest.main()
