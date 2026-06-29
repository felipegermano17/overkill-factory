from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
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


def write_trace(tmpdir: str) -> Path:
    trace = {
        "canonical_doc_ref": "external:canonical.md",
        "canonical_sha256": "0" * 64,
        "checkpoints": [
            {
                "checkpoint_id": "runtime-001",
                "sequence": 1,
                "canonical_line": 10,
                "checkpoint_type": "heading",
                "canonical_heading": "Runtime gate",
                "implementation_status": "implemented_by_runtime",
                "implementation_refs": [{"kind": "script", "path": "scripts/factoryctl.py"}],
                "next_action": "none",
            },
            {
                "checkpoint_id": "framing-001",
                "sequence": 2,
                "canonical_line": 20,
                "checkpoint_type": "heading",
                "canonical_heading": "Definition",
                "implementation_status": "foundational_text_tracked",
                "implementation_refs": [{"kind": "documentation", "path": "README.md"}],
                "next_action": "none",
            },
        ],
    }
    path = Path(tmpdir) / "trace.json"
    path.write_text(json.dumps(trace), encoding="utf-8")
    return path


class CanonicalRealInfraAuditTest(unittest.TestCase):
    def test_build_audit_from_generated_trace(self) -> None:
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as tmpdir:
            audit = canonical_real_infra_audit.build_audit(write_trace(tmpdir))

        errors = canonical_real_infra_audit.validate_audit(audit)

        self.assertEqual(errors, [])
        self.assertEqual(audit["answer"], "yes")
        self.assertEqual(audit["result"], "PASS")
        self.assertEqual(audit["summary"]["checkpoints_checked"], 2)
        self.assertEqual(audit["summary"]["runtime_enforced"], 1)
        self.assertEqual(audit["summary"]["non_runtime_processes"], 1)

    def test_schema_ref_matches_output_schema_id(self) -> None:
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as tmpdir:
            audit = canonical_real_infra_audit.build_audit(write_trace(tmpdir))
        schema = json.loads((ROOT / "schemas" / "canonical-real-infra-audit.schema.json").read_text(encoding="utf-8"))

        self.assertEqual(audit["$schema"], schema["$id"])

    def test_validator_rejects_inconsistent_no_answer(self) -> None:
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as tmpdir:
            audit = canonical_real_infra_audit.build_audit(write_trace(tmpdir))
        audit["answer"] = "no"

        errors = canonical_real_infra_audit.validate_audit(audit)

        self.assertIn("answer does not match runtime implementation verdict", errors)


if __name__ == "__main__":
    unittest.main()
