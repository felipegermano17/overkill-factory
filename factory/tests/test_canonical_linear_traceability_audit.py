from __future__ import annotations

import importlib.util
import sys
import tempfile
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
    def test_default_outputs_are_generated_tmp_files(self) -> None:
        self.assertIn(".tmp", canonical_linear_traceability_audit.DEFAULT_OUT_JSON.parts)
        self.assertIn(".tmp", canonical_linear_traceability_audit.DEFAULT_CHECKPOINT_MANIFEST.parts)

    def test_checkpoint_manifest_extracts_headings_and_principles_without_committed_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            canonical = Path(tmpdir) / "canonical.md"
            canonical.write_text(
                "# Title\n\n"
                "## Source Resolution\n\n"
                "### Runtime Gate\n\n"
                "3.1 first principle\n"
                "3.2 second principle\n",
                encoding="utf-8",
            )

            manifest = canonical_linear_traceability_audit.checkpoint_manifest(canonical)

        self.assertEqual(manifest["record_type"], "canonical_checkpoint_manifest")
        self.assertEqual(manifest["checkpoint_count"], 3)
        self.assertEqual(manifest["headings_count"], 3)
        self.assertEqual(manifest["principles_count"], 0)
        self.assertEqual([item["sequence"] for item in manifest["checkpoints"]], [1, 2, 3])

    def test_validator_rejects_missing_repo_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            canonical = Path(tmpdir) / "canonical.md"
            canonical.write_text("## Runtime\n", encoding="utf-8")
            manifest = canonical_linear_traceability_audit.checkpoint_manifest(canonical)
            manifest_path = Path(tmpdir) / "manifest.json"
            import json

            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            audit = {
                "record_type": "canonical_linear_traceability_audit",
                "canonical_doc_ref": manifest["canonical_doc_ref"],
                "canonical_sha256": manifest["canonical_sha256"],
                "summary": {
                    "checkpoints_checked": 1,
                    "headings_checked": 1,
                    "principles_checked": 0,
                    "status_counts": {"implemented_by_runtime": 1},
                },
                "checkpoints": [
                    {
                        "sequence": 1,
                        "checkpoint_id": "checkpoint-001",
                        "checkpoint_type": "heading",
                        "canonical_line": 1,
                        "canonical_level": 2,
                        "canonical_heading": "Runtime",
                        "implementation_status": "implemented_by_runtime",
                        "implementation_refs": [{"kind": "script", "path": "docs/no-such-file.md"}],
                        "canonical_obligation": "Runtime check",
                        "boundary": None,
                        "next_action": "none",
                    }
                ],
                "completion_claim_allowed": False,
            }

            errors = canonical_linear_traceability_audit.validate_audit(
                audit,
                checkpoint_manifest_path=manifest_path,
            )

        self.assertTrue(any("ref does not exist: docs/no-such-file.md" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
