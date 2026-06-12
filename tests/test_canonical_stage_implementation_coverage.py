from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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
    def test_core_canonical_contracts_are_versioned_as_source(self) -> None:
        required_paths = [
            "schemas/product-sot.schema.json",
            "schemas/spec-graph.schema.json",
            "schemas/product-experience-plan.schema.json",
            "schemas/product-face-packet.schema.json",
            "schemas/product-face-result.schema.json",
            "schemas/worker-result.schema.json",
            "scripts/factoryctl.py",
            "templates/vfinal-factory-card.json",
        ]

        for rel in required_paths:
            with self.subTest(path=rel):
                self.assertTrue((ROOT / rel).exists(), rel)

    def test_factory_card_request_types_are_locked(self) -> None:
        factory_card_schema = json.loads((ROOT / "schemas" / "factory-card.schema.json").read_text(encoding="utf-8"))
        request_types = set(factory_card_schema["properties"]["request_type"]["enum"])

        self.assertEqual(request_types, EXPECTED_REQUEST_TYPES)

    def test_vfinal_template_contains_runtime_contract_surfaces(self) -> None:
        vfinal_template = json.loads((ROOT / "templates" / "vfinal-factory-card.json").read_text(encoding="utf-8"))

        for field in ["product_sot", "spec_graph", "runtime_contract", "receipt_five", "completion_audit"]:
            with self.subTest(field=field):
                self.assertIn(field, vfinal_template)


if __name__ == "__main__":
    unittest.main()
