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
    def test_builds_runtime_rules_for_every_actionable_canonical_checkpoint(self) -> None:
        trace = json.loads(
            (ROOT / "validation" / "canonical-linear-traceability" / "canonical-linear-traceability.json").read_text(
                encoding="utf-8"
            )
        )

        rulebook = canonical_runtime_enforcement.build_rulebook(trace)

        self.assertEqual(rulebook["summary"]["checkpoints_checked"], 118)
        self.assertEqual(rulebook["summary"]["runtime_rules"], 113)
        self.assertEqual(rulebook["summary"]["non_runtime_processes"], 5)
        self.assertEqual(rulebook["summary"]["unmapped_actionable_checkpoints"], 0)

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
