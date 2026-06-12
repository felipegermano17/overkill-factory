import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import full_product_worker_graph as graph


class FullProductWorkerGraphTests(unittest.TestCase):
    def test_public_qvg_graph_passes_but_is_not_reusable_for_product(self):
        result = graph.build_graph()

        self.assertEqual(result["result"], "PASS")
        self.assertFalse(result["reusable_for_product"])
        self.assertFalse(result["completion_claim_allowed"])
        self.assertGreaterEqual(result["lanes_total"], 10)
        self.assertEqual(result["lanes_total"], result["lanes_passed"])
        self.assertIn("managed remote proof", " ".join(result["production_blockers"]))
        self.assertNotIn("production CU/SVM/economic proof", " ".join(result["production_blockers"]))
        self.assertEqual(result["reusable_for_product_lanes"], 2)

    def test_every_lane_has_existing_evidence_and_no_validation_errors(self):
        result = graph.build_graph()

        for lane in result["lanes"]:
            self.assertEqual(lane["status"], "PASS", lane)
            self.assertEqual(lane["validation_errors"], [], lane)
            self.assertTrue((graph.ROOT / lane["evidence_ref"]).exists(), lane)

    def test_stale_receipt_refs_are_visible_but_do_not_replace_current_worker_evidence(self):
        result = graph.build_graph()
        by_id = {lane["lane_id"]: lane for lane in result["lanes"]}

        self.assertFalse(by_id["product_face"]["reusable_for_product"])
        self.assertTrue(by_id["auditor"]["reusable_for_product"])
        self.assertTrue(by_id["cu_svm_economic"]["reusable_for_product"])
        self.assertGreater(len(by_id["receipt_five"]["stale_evidence_refs"]), 0)
        self.assertEqual(by_id["receipt_five"]["status"], "PASS")

    def test_writes_schema_backed_json_and_markdown(self):
        with TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "graph.json"
            md_out = Path(tmpdir) / "graph.md"
            exit_code = graph.main(["--out", str(out), "--md-out", str(md_out), "--require-pass"])

            self.assertEqual(exit_code, 0)
            self.assertTrue(out.exists())
            self.assertTrue(md_out.exists())
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(
                data["$schema"],
                "https://overkill-factory.dev/schemas/full-product-worker-graph.schema.json",
            )


if __name__ == "__main__":
    unittest.main()
