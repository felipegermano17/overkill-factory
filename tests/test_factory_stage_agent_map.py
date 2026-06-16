from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FactoryStageAgentMapTest(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = json.loads(
            (ROOT / "agents" / "worker-registry.public.json").read_text(encoding="utf-8")
        )
        self.stage_map = (ROOT / "docs" / "agents" / "factory-stage-agent-map.md").read_text(
            encoding="utf-8"
        )
        self.workflow_catalog = json.loads(
            (ROOT / "docs" / "factory-workflow.catalog.json").read_text(encoding="utf-8")
        )

    def test_stage_map_names_every_canonical_stage(self) -> None:
        for stage_number in range(1, 33):
            with self.subTest(stage=stage_number):
                self.assertRegex(self.stage_map, rf"\|\s*{stage_number}\.")

    def test_stage_map_worker_refs_are_registered_or_explicitly_non_worker_roles(self) -> None:
        registered = {worker["worker_id"] for worker in self.registry["workers"]}
        allowed_non_workers = {
            "Factory Concierge",
            "factory-critic",
            "overkill-factory-gerente",
        }
        worker_refs = {
            ref
            for ref in re.findall(r"`([^`]+)`", self.stage_map)
            if "/" not in ref and "." not in ref
        }

        for ref in sorted(worker_refs):
            if ref in allowed_non_workers:
                continue
            with self.subTest(ref=ref):
                self.assertIn(ref, registered)

    def test_key_stage_owners_are_not_left_generic(self) -> None:
        required_pairs = {
            "6. Agentic Method Router": "`factory-orchestrator`",
            "8. Product Pack & Surface Pack": "`factory-orchestrator`",
            "13. Data, Metrics & Analytics Plan": "`detection-monitoring-worker`",
            "14. Agent Quality & Evals Plan": "`skill-eval-distiller`",
            "27. Completion Audit": "`evidence-reconciler`",
            "32. Factory Maturity Audit": "`skill-eval-distiller`",
        }

        for stage, worker in required_pairs.items():
            with self.subTest(stage=stage):
                line = next(line for line in self.stage_map.splitlines() if stage in line)
                self.assertIn(worker, line)

    def test_product_experience_is_first_class_catalog_gate(self) -> None:
        phases = {row["phase_id"]: row for row in self.workflow_catalog["phases"]}
        product_experience = phases["F8A"]

        self.assertEqual(product_experience["phase_name"], "Product Experience And Surface Pack Gate")
        for artifact in [
            "product_experience_plan",
            "product_face_packet",
            "professional_design_process",
            "surface_evidence_profile",
            "product_delivery_quality_profile",
        ]:
            with self.subTest(artifact=artifact):
                self.assertIn(artifact, product_experience["required_artifacts"])
        self.assertIn("product-face", product_experience["required_workers"])
        self.assertIn("Product Experience Gate", product_experience["required_gates"])
        self.assertNotIn("product_experience_plan", phases["F11"]["optional_artifacts"])

    def test_executable_plan_catalog_marks_data_and_docs_as_schema_backed_conditionals(self) -> None:
        phases = {row["phase_id"]: row for row in self.workflow_catalog["phases"]}
        executable_plan = phases["F11"]

        self.assertNotIn("data_metrics_plan", executable_plan["optional_artifacts"])
        for artifact in ("data_metrics_plan", "user_docs_onboarding_plan"):
            with self.subTest(artifact=artifact):
                self.assertIn(artifact, executable_plan["conditional_artifacts"])
        self.assertIn("schemas/data-metrics-plan.schema.json", executable_plan["related_schema_refs"])
        self.assertIn("schemas/user-docs-onboarding-plan.schema.json", executable_plan["related_schema_refs"])
        self.assertTrue(
            any("schema-backed runtime validation" in item for item in executable_plan["completion_detection"])
        )


if __name__ == "__main__":
    unittest.main()
