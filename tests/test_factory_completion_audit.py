import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import factory_completion_audit as audit


class FactoryCompletionAuditTests(unittest.TestCase):
    def test_current_public_factory_is_not_complete(self):
        result = audit.build_audit()

        self.assertEqual(result["status"], "NOT_COMPLETE")
        self.assertFalse(result["completion_claim_allowed"])
        self.assertEqual(result["score_estimate"], "9.994/10")
        self.assertGreater(result["requirements_blocking"], 0)

    def test_blocks_product_specific_and_provider_backed_gaps(self):
        result = audit.build_audit()
        blockers = set(result["blocking_summary"])

        self.assertNotIn("production_product_face", blockers)
        self.assertIn("production_quasar_auditor", blockers)
        self.assertIn("production_cu_svm_economic", blockers)
        self.assertIn("managed_remote_proof", blockers)
        self.assertIn("production_release_human_gate", blockers)
        self.assertIn("full_product_specific_worker_graph", blockers)
        self.assertEqual(len(blockers), 5)

    def test_product_face_can_be_achieved_while_other_public_proofs_remain_bounded(self):
        result = audit.build_audit()
        by_id = {item["id"]: item for item in result["requirements"]}

        self.assertEqual(by_id["production_product_face"]["status"], "ACHIEVED")
        self.assertEqual(by_id["production_quasar_auditor"]["status"], "BOUNDED_PUBLIC_PROOF")
        self.assertEqual(by_id["managed_remote_proof"]["status"], "BOUNDED_PUBLIC_PROOF")
        self.assertEqual(by_id["full_product_specific_worker_graph"]["status"], "BOUNDED_PUBLIC_PROOF")

    def test_require_complete_returns_nonzero_while_blocked(self):
        exit_code = audit.main(["--no-write", "--require-complete"])

        self.assertEqual(exit_code, 1)

    def test_writes_schema_backed_json_and_markdown(self):
        with TemporaryDirectory() as tmpdir:
            exit_code = audit.main(["--out-dir", tmpdir])
            data_path = Path(tmpdir) / "factory-10-completion-audit.json"
            md_path = Path(tmpdir) / "factory-10-completion-audit.md"

            self.assertEqual(exit_code, 0)
            self.assertTrue(data_path.exists())
            self.assertTrue(md_path.exists())
            data = json.loads(data_path.read_text(encoding="utf-8"))
            self.assertEqual(data["$schema"], "https://overkill-factory.dev/schemas/factory-completion-audit.schema.json")


if __name__ == "__main__":
    unittest.main()
