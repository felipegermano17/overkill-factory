from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COVERAGE_PATH = ROOT / "validation" / "canonical-stage-coverage" / "canonical-stage-implementation-coverage.json"
STRONG_KINDS = {
    "schema",
    "template",
    "script",
    "test",
    "worker_registry",
    "worker_profile",
    "profile_binding",
    "validation_artifact",
    "runtime_adapter",
}
EXPECTED_REQUEST_TYPES = {
    "product_new",
    "slice",
    "feature",
    "bug",
    "incident",
    "release",
    "migration",
    "integration",
    "doc",
    "security",
    "ux_ui",
    "data_analytics",
    "agent_skill",
}


class CanonicalStageImplementationCoverageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))

    def test_every_canonical_process_stage_has_contract_backing(self) -> None:
        stages = self.coverage["stages"]

        self.assertEqual([stage["stage_number"] for stage in stages], list(range(1, 33)))
        for stage in stages:
            with self.subTest(stage=stage["stage_number"]):
                self.assertTrue(stage["canonical_promises"])
                self.assertIn(
                    stage["coverage_status"],
                    {"implemented_by_contract", "implemented_by_runtime", "bounded_public_proof"},
                )
                self.assertTrue(
                    any(ref["kind"] in STRONG_KINDS for ref in stage["implementation_refs"]),
                    "stage cannot be covered by documentation alone",
                )

    def test_all_repo_refs_exist(self) -> None:
        for stage in self.coverage["stages"]:
            for ref in stage["implementation_refs"]:
                path = ref["path"].split("#", 1)[0]
                if path.startswith("external:"):
                    continue
                with self.subTest(stage=stage["stage_number"], path=path):
                    self.assertTrue((ROOT / path).exists(), path)

    def test_key_canonical_promises_are_backed_by_enforced_contracts(self) -> None:
        by_stage = {stage["stage_number"]: stage for stage in self.coverage["stages"]}

        stage5_paths = {ref["path"] for ref in by_stage[5]["implementation_refs"]}
        self.assertIn("schemas/product-sot.schema.json", stage5_paths)
        self.assertIn("scripts/factoryctl.py", stage5_paths)

        stage15_paths = {ref["path"] for ref in by_stage[15]["implementation_refs"]}
        self.assertIn("schemas/spec-graph.schema.json", stage15_paths)
        self.assertIn("scripts/factoryctl.py", stage15_paths)

        stage21_paths = {ref["path"] for ref in by_stage[21]["implementation_refs"]}
        self.assertIn("schemas/worker-result.schema.json", stage21_paths)

        factory_card_schema = json.loads((ROOT / "schemas" / "factory-card.schema.json").read_text(encoding="utf-8"))
        request_types = set(factory_card_schema["properties"]["request_type"]["enum"])
        self.assertEqual(request_types, EXPECTED_REQUEST_TYPES)

        worker_result_schema = json.loads((ROOT / "schemas" / "worker-result.schema.json").read_text(encoding="utf-8"))
        self.assertIn("BLOCKED", worker_result_schema["properties"]["result"]["enum"])

        vfinal_template = json.loads((ROOT / "templates" / "vfinal-factory-card.json").read_text(encoding="utf-8"))
        self.assertIn("product_sot", vfinal_template)
        self.assertIn("spec_graph", vfinal_template)


if __name__ == "__main__":
    unittest.main()
