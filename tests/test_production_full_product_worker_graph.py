from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "production_full_product_worker_graph.py"
SPEC = importlib.util.spec_from_file_location("production_full_product_worker_graph", SCRIPT)
assert SPEC is not None
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["production_full_product_worker_graph"] = module
SPEC.loader.exec_module(module)


class ProductionFullProductWorkerGraphTest(unittest.TestCase):
    def test_graph_blocks_missing_strict_lane_from_explicit_fixture(self) -> None:
        lane = {
            "lane_id": "remote_proof",
            "worker_id": "remote-proof-runner",
            "path": ".tmp/test-production-graph/missing-remote-proof.json",
            "record_type": "remote_proof_result",
            "scope": "supporting",
            "reusable_policy": "strict",
        }

        graph = module.build_graph((lane,))

        self.assertEqual(graph["result"], "FAIL")
        self.assertFalse(graph["reusable_for_product"])
        self.assertEqual(graph["lanes_total"], 1)
        self.assertIn("remote_proof: evidence file is missing", graph["blocking_summary"])

    def test_strict_lane_requires_reusable_product_target(self) -> None:
        tmp_root = ROOT / ".tmp"
        tmp_root.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=tmp_root) as tmpdir:
            proof = Path(tmpdir) / "remote-proof.json"
            proof.write_text(
                '{"record_type":"remote_proof_result","result":"PASS","evidence_kind":"real","reusable_for_product":false,"product_target":{"product_id":"qvg-public-validation-product"}}',
                encoding="utf-8",
            )
            lane = {
                "lane_id": "remote_proof",
                "worker_id": "remote-proof-runner",
                "path": proof.relative_to(ROOT).as_posix(),
                "record_type": "remote_proof_result",
                "scope": "supporting",
                "reusable_policy": "strict",
            }

            result = module.validate_lane(lane)
            expected_size = proof.stat().st_size

        self.assertEqual(result["status"], "FAIL")
        self.assertIn("strict lane must be reusable", " ".join(result["validation_errors"]))
        self.assertEqual(result["evidence_provenance"]["ref"], lane["path"])
        self.assertEqual(result["evidence_provenance"]["size_bytes"], expected_size)
        self.assertEqual(len(result["evidence_provenance"]["sha256"]), 64)

    def test_lane_provenance_records_loaded_schema_and_product(self) -> None:
        tmp_root = ROOT / ".tmp"
        tmp_root.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=tmp_root) as tmpdir:
            proof = Path(tmpdir) / "proof.json"
            proof.write_text(
                (
                    '{"$schema":"https://overkill-factory.dev/schemas/worker-result.schema.json",'
                    '"record_type":"remote_proof_result","result":"PASS","evidence_kind":"real",'
                    '"reusable_for_product":true,"product_target":{"product_id":"qvg-public-validation-product"}}'
                ),
                encoding="utf-8",
            )
            lane = {
                "lane_id": "remote_proof",
                "worker_id": "remote-proof-runner",
                "path": proof.relative_to(ROOT).as_posix(),
                "record_type": "remote_proof_result",
                "scope": "supporting",
                "reusable_policy": "strict",
            }

            result = module.validate_lane(lane)

        provenance = result["evidence_provenance"]
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(provenance["record_type"], "remote_proof_result")
        self.assertEqual(provenance["product_id"], "qvg-public-validation-product")
        self.assertEqual(provenance["$schema"], "https://overkill-factory.dev/schemas/worker-result.schema.json")

    def test_release_gate_upstream_mode_excludes_gate_owned_lanes(self) -> None:
        tmp_root = ROOT / ".tmp"
        tmp_root.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=tmp_root) as tmpdir:
            proof = Path(tmpdir) / "remote-proof.json"
            proof.write_text(
                (
                    '{"record_type":"remote_proof_result","result":"PASS","evidence_kind":"real",'
                    '"reusable_for_product":true,"product_target":{"product_id":"qvg-public-validation-product"}}'
                ),
                encoding="utf-8",
            )
            upstream_lane = {
                "lane_id": "remote_proof",
                "worker_id": "remote-proof-runner",
                "path": proof.relative_to(ROOT).as_posix(),
                "record_type": "remote_proof_result",
                "scope": "supporting",
                "reusable_policy": "strict",
            }
            human_gate_lane = {
                "lane_id": "human_gate",
                "worker_id": "human-gate-clerk",
                "path": (Path(tmpdir) / "human-gate-record.json").relative_to(ROOT).as_posix(),
                "record_type": "human_gate_record",
                "scope": "supporting",
                "reusable_policy": "strict",
            }
            release_lane = {
                "lane_id": "release_ops",
                "worker_id": "release-ops-worker",
                "path": (Path(tmpdir) / "release-ops-result.json").relative_to(ROOT).as_posix(),
                "record_type": "release_ops_result",
                "scope": "supporting",
                "reusable_policy": "strict",
            }

            lanes = (upstream_lane, human_gate_lane, release_lane)
            full_graph = module.build_graph(lanes)
            upstream_graph = module.build_graph(lanes, graph_mode="release_gate_upstream")

        self.assertEqual(full_graph["result"], "FAIL")
        self.assertIn("human_gate: evidence file is missing", full_graph["blocking_summary"])
        self.assertIn("release_ops: evidence file is missing", full_graph["blocking_summary"])
        self.assertEqual(upstream_graph["result"], "PASS")
        self.assertEqual(upstream_graph["omitted_lanes"], ["human_gate", "release_ops"])
        self.assertFalse(upstream_graph["completion_claim_allowed"])
        self.assertEqual(upstream_graph["lanes_total"], 1)
        self.assertNotIn(human_gate_lane["path"], upstream_graph["evidence_refs"])
        self.assertNotIn(release_lane["path"], upstream_graph["evidence_refs"])
        self.assertEqual(upstream_graph["blocking_summary"], [])


if __name__ == "__main__":
    unittest.main()
