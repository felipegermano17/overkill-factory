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
    def generic_contract(self, tmpdir: str, lanes: list[dict]) -> dict:
        source_dir = Path(tmpdir) / "generic-api-product"
        source_dir.mkdir()
        (source_dir / "README.md").write_text("Generic API product source.\n", encoding="utf-8")
        return {
            "$schema": "https://overkill-factory.dev/schemas/production-full-product-graph-contract.schema.json",
            "record_type": "production_full_product_graph_contract",
            "product_id": "generic-api-product",
            "product_name": "Generic API product",
            "source_ref": source_dir.relative_to(ROOT).as_posix(),
            "product_sot_ref": "external:generic-api-product-sot",
            "selected_capability_pack_refs": ["capability-packs/api-data.json"],
            "product_delivery_quality_profile_ref": "quality-profiles/api-production.json",
            "risk_class": "R2",
            "promotion_ladder_ref": "promotion-ladders/api-production.json",
            "approval_scope": "Reusable full-product graph for a generic API product.",
            "environment_class": "production-readiness",
            "graph_kind": "production_full_product_worker_graph",
            "release_gate_upstream_excluded_lanes": ["human_gate", "release_ops"],
            "lanes": lanes,
        }

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

    def test_generic_non_qvg_contract_can_build_pass_graph(self) -> None:
        tmp_root = ROOT / ".tmp"
        tmp_root.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=tmp_root) as tmpdir:
            proof = Path(tmpdir) / "api-proof.json"
            proof.write_text(
                (
                    '{"record_type":"remote_proof_result","result":"PASS","evidence_kind":"real",'
                    '"reusable_for_product":true,"product_target":{"product_id":"generic-api-product"},'
                    '"evidence_refs":["external:api-proof"]}'
                ),
                encoding="utf-8",
            )
            lanes = [
                {
                    "lane_id": "api_proof",
                    "worker_id": "backend-api-builder",
                    "path": proof.relative_to(ROOT).as_posix(),
                    "record_type": "remote_proof_result",
                    "scope": "product",
                    "reusable_policy": "strict",
                }
            ]
            contract = self.generic_contract(tmpdir, lanes)

            result = module.build_graph(contract=contract)

        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["product_id"], "generic-api-product")
        self.assertEqual(result["product_target"]["product_id"], "generic-api-product")
        self.assertEqual(result["selected_capability_pack_refs"], ["capability-packs/api-data.json"])
        self.assertEqual(result["risk_class"], "R2")
        self.assertEqual(result["lanes_total"], 1)
        self.assertEqual(result["blocking_summary"], [])

    def test_generic_contract_rejects_strict_lane_for_wrong_product(self) -> None:
        tmp_root = ROOT / ".tmp"
        tmp_root.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=tmp_root) as tmpdir:
            proof = Path(tmpdir) / "api-proof.json"
            proof.write_text(
                (
                    '{"record_type":"remote_proof_result","result":"PASS","evidence_kind":"real",'
                    '"reusable_for_product":true,"product_target":{"product_id":"wrong-product"},'
                    '"evidence_refs":["external:api-proof"]}'
                ),
                encoding="utf-8",
            )
            lane = {
                "lane_id": "api_proof",
                "worker_id": "backend-api-builder",
                "path": proof.relative_to(ROOT).as_posix(),
                "record_type": "remote_proof_result",
                "scope": "product",
                "reusable_policy": "strict",
            }
            contract = self.generic_contract(tmpdir, [lane])

            result = module.validate_lane(lane, contract)

        self.assertEqual(result["status"], "FAIL")
        self.assertIn("strict lane product_id does not match", result["validation_errors"])

    def test_explicit_missing_graph_contract_does_not_fallback_to_qvg(self) -> None:
        with self.assertRaises(FileNotFoundError):
            module.load_graph_contract(ROOT / ".tmp" / "missing-production-graph-contract.json")


if __name__ == "__main__":
    unittest.main()
