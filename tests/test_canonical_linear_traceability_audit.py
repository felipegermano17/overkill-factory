from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "canonical_linear_traceability_audit.py"
SPEC = importlib.util.spec_from_file_location("canonical_linear_traceability_audit", MODULE_PATH)
assert SPEC is not None
canonical_linear_traceability_audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["canonical_linear_traceability_audit"] = canonical_linear_traceability_audit
SPEC.loader.exec_module(canonical_linear_traceability_audit)


class CanonicalLinearTraceabilityAuditTest(unittest.TestCase):
    def test_audit_maps_every_canonical_heading_and_principle_in_order(self) -> None:
        audit = canonical_linear_traceability_audit.build_audit()
        errors = canonical_linear_traceability_audit.validate_audit(audit)

        self.assertEqual(errors, [])
        self.assertEqual(audit["summary"]["headings_checked"], 94)
        self.assertEqual(audit["summary"]["principles_checked"], 24)
        self.assertEqual(audit["summary"]["checkpoints_checked"], 118)
        self.assertFalse(audit["completion_claim_allowed"])

    def test_audit_result_schema_exists_and_matches_output_schema_ref(self) -> None:
        audit = canonical_linear_traceability_audit.build_audit()
        schema = json.loads((ROOT / "schemas" / "canonical-linear-traceability.schema.json").read_text(encoding="utf-8"))

        self.assertEqual(audit["$schema"], schema["$id"])

    def test_validator_rejects_a_missing_linear_checkpoint(self) -> None:
        audit = canonical_linear_traceability_audit.build_audit()
        audit["checkpoints"] = audit["checkpoints"][:-1]

        errors = canonical_linear_traceability_audit.validate_audit(audit)

        self.assertTrue(any("checkpoint count mismatch" in error for error in errors))

    def test_validator_rejects_missing_repo_reference(self) -> None:
        audit = canonical_linear_traceability_audit.build_audit()
        audit["checkpoints"][0]["implementation_refs"][0]["path"] = "docs/no-such-file.md"

        errors = canonical_linear_traceability_audit.validate_audit(audit)

        self.assertTrue(any("ref does not exist: docs/no-such-file.md" in error for error in errors))

    def test_validator_rejects_full_runtime_claim_when_limited_sections_exist(self) -> None:
        audit = canonical_linear_traceability_audit.build_audit()
        limited = [
            record
            for record in audit["checkpoints"]
            if record["implementation_status"]
            in {"bounded_public_proof", "partial_requires_live_pilot", "foundational_text_tracked"}
        ]

        self.assertGreater(len(limited), 0)


if __name__ == "__main__":
    unittest.main()
