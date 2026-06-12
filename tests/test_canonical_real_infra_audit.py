from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "canonical_real_infra_audit.py"
SPEC = importlib.util.spec_from_file_location("canonical_real_infra_audit", MODULE_PATH)
assert SPEC is not None
canonical_real_infra_audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["canonical_real_infra_audit"] = canonical_real_infra_audit
SPEC.loader.exec_module(canonical_real_infra_audit)


class CanonicalRealInfraAuditTest(unittest.TestCase):
    def test_answer_is_yes_for_all_actionable_runtime_processes(self) -> None:
        audit = canonical_real_infra_audit.build_audit()
        errors = canonical_real_infra_audit.validate_audit(audit)

        self.assertEqual(errors, [])
        self.assertEqual(audit["answer"], "yes")
        self.assertEqual(audit["result"], "PASS")
        self.assertTrue(audit["all_actionable_canonical_processes_runtime_implemented"])
        self.assertEqual(audit["summary"]["checkpoints_checked"], 118)
        self.assertEqual(audit["summary"]["runtime_enforced"], 113)
        self.assertEqual(audit["summary"]["non_runtime_processes"], 5)
        self.assertEqual(audit["summary"]["not_runtime_enforced"], 0)

    def test_contract_only_requires_runtime_rule_to_count_as_enforced(self) -> None:
        audit = canonical_real_infra_audit.build_audit()
        promoted = [
            checkpoint
            for checkpoint in audit["checkpoints"]
            if checkpoint["linear_status"] == "implemented_by_contract"
            and checkpoint["real_infra_status"] == "runtime_enforced"
        ]

        self.assertGreater(len(promoted), 0)
        self.assertTrue(all(checkpoint["runtime_rule_ref"] for checkpoint in promoted))

    def test_schema_ref_matches_output_schema_id(self) -> None:
        audit = canonical_real_infra_audit.build_audit()
        schema = json.loads((ROOT / "schemas" / "canonical-real-infra-audit.schema.json").read_text(encoding="utf-8"))

        self.assertEqual(audit["$schema"], schema["$id"])

    def test_validator_rejects_inconsistent_no_answer(self) -> None:
        audit = canonical_real_infra_audit.build_audit()
        audit["answer"] = "no"

        errors = canonical_real_infra_audit.validate_audit(audit)

        self.assertIn("answer does not match runtime implementation verdict", errors)


if __name__ == "__main__":
    unittest.main()
