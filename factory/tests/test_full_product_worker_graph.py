import json
import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import full_product_worker_graph as graph


def lane_payload(lane: dict, evidence_ref: str) -> dict:
    if lane.get("receipt_type") == "receipt_five":
        return {
            "receipt_five": {
                "artifact_paths": [evidence_ref],
                "verification_result": "PASS",
            }
        }
    payload = {
        "record_type": lane.get("record_type"),
        "result": "PASS",
        "blocking_findings": False,
        "evidence_kind": "real",
        "reusable_for_product": lane["lane_id"] in {"security", "auditor", "cu_svm_economic", "independent_review"},
        "evidence_refs": [evidence_ref],
        "card_ref": {"card_id": "FIXTURE-CARD"},
    }
    if lane.get("proof_kind"):
        payload["proof_kind"] = lane["proof_kind"]
    return payload


@contextmanager
def generated_lanes():
    tmp_root = graph.ROOT / ".tmp"
    tmp_root.mkdir(exist_ok=True)
    original = graph.LANES
    with TemporaryDirectory(dir=tmp_root) as tmpdir:
        tmp = Path(tmpdir)
        evidence = tmp / "evidence.md"
        evidence.write_text("temporary graph fixture\n", encoding="utf-8")
        lanes = []
        for lane in original:
            rel = (tmp / f"{lane['lane_id']}.json").relative_to(graph.ROOT).as_posix()
            payload = lane_payload(lane, evidence.relative_to(graph.ROOT).as_posix())
            (graph.ROOT / rel).write_text(json.dumps(payload), encoding="utf-8")
            updated = dict(lane)
            updated["path"] = rel
            lanes.append(updated)
        graph.LANES = tuple(lanes)
        try:
            yield
        finally:
            graph.LANES = original


class FullProductWorkerGraphTests(unittest.TestCase):
    def test_public_qvg_graph_passes_but_is_not_reusable_for_product(self):
        with generated_lanes():
            result = graph.build_graph()

        self.assertEqual(result["result"], "PASS")
        self.assertFalse(result["reusable_for_product"])
        self.assertFalse(result["completion_claim_allowed"])
        self.assertGreaterEqual(result["lanes_total"], 10)
        self.assertEqual(result["lanes_total"], result["lanes_passed"])
        self.assertIn("managed remote proof", " ".join(result["production_blockers"]))
        self.assertNotIn("production CU/SVM/economic proof", " ".join(result["production_blockers"]))
        self.assertEqual(result["reusable_for_product_lanes"], 4)

    def test_every_lane_has_existing_evidence_and_no_validation_errors(self):
        with generated_lanes():
            result = graph.build_graph()

            for lane in result["lanes"]:
                self.assertEqual(lane["status"], "PASS", lane)
                self.assertEqual(lane["validation_errors"], [], lane)
                self.assertTrue((graph.ROOT / lane["evidence_ref"]).exists(), lane)

    def test_stale_receipt_refs_are_visible_but_do_not_replace_current_worker_evidence(self):
        with generated_lanes():
            result = graph.build_graph()
        by_id = {lane["lane_id"]: lane for lane in result["lanes"]}

        self.assertFalse(by_id["product_face"]["reusable_for_product"])
        self.assertTrue(by_id["auditor"]["reusable_for_product"])
        self.assertTrue(by_id["cu_svm_economic"]["reusable_for_product"])
        self.assertEqual(by_id["receipt_five"]["stale_evidence_refs"], [])
        self.assertEqual(by_id["receipt_five"]["status"], "PASS")

    def test_writes_schema_backed_json_and_markdown(self):
        with generated_lanes():
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
