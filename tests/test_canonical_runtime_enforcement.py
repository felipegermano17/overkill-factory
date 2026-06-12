from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "canonical_runtime_enforcement.py"
SPEC = importlib.util.spec_from_file_location("canonical_runtime_enforcement", MODULE_PATH)
assert SPEC is not None
canonical_runtime_enforcement = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["canonical_runtime_enforcement"] = canonical_runtime_enforcement
SPEC.loader.exec_module(canonical_runtime_enforcement)


class CanonicalRuntimeEnforcementTest(unittest.TestCase):
    def test_default_rulebook_falls_back_without_committed_trace(self) -> None:
        rulebook = canonical_runtime_enforcement.default_rulebook()

        self.assertEqual(rulebook["record_type"], "canonical_runtime_rulebook")
        self.assertEqual(rulebook["summary"]["runtime_rules"], 1)
        self.assertEqual(rulebook["source_trace_ref"], "generated:fallback-vfinal-runtime-rulebook")

    def test_strict_vfinal_runtime_gate_blocks_missing_canonical_contracts(self) -> None:
        card = json.loads((ROOT / "templates" / "vfinal-factory-card.json").read_text(encoding="utf-8"))
        for field in (
            "data_metrics_plan",
            "agent_eval_plan",
            "dependency_map",
            "access_capability",
            "budget_contract",
            "privacy_compliance_plan",
            "autonomy_readiness_packet",
            "factory_maturity_scorecard",
        ):
            card.pop(field, None)

        blockers = canonical_runtime_enforcement.validate_card_runtime_rules(card)
        blocker_fields = {field for blocker in blockers for field in blocker["missing_fields"]}

        self.assertIn("data_metrics_plan", blocker_fields)
        self.assertIn("agent_eval_plan", blocker_fields)
        self.assertIn("dependency_map", blocker_fields)
        self.assertIn("access_capability", blocker_fields)
        self.assertIn("budget_contract", blocker_fields)
        self.assertIn("privacy_compliance_plan", blocker_fields)
        self.assertIn("autonomy_readiness_packet", blocker_fields)
        self.assertIn("factory_maturity_scorecard", blocker_fields)

    def test_full_template_satisfies_canonical_runtime_gate(self) -> None:
        card = json.loads((ROOT / "templates" / "vfinal-factory-card.json").read_text(encoding="utf-8"))

        blockers = canonical_runtime_enforcement.validate_card_runtime_rules(card)

        self.assertEqual(blockers, [])


if __name__ == "__main__":
    unittest.main()
