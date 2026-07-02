from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent


class FactoryWorkflowCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = json.loads(
            (ROOT / "agents" / "worker-registry.public.json").read_text(encoding="utf-8")
        )
        self.workflow_catalog = json.loads(
            (REPO_ROOT / "docs" / "factory-workflow.catalog.json").read_text(encoding="utf-8")
        )
        self.worker_profiles = json.loads(
            (ROOT / "agents" / "worker-profiles.public.json").read_text(encoding="utf-8")
        )

    def test_workflow_catalog_names_every_public_phase(self) -> None:
        phases = self.workflow_catalog["phases"]
        phase_ids = [phase["phase_id"] for phase in phases]

        self.assertEqual(len(phases), 26)
        self.assertEqual(phase_ids[0], "F0")
        self.assertEqual(phase_ids[-1], "F27")
        self.assertEqual(len(phase_ids), len(set(phase_ids)))
        for phase in phases:
            with self.subTest(phase=phase["phase_id"]):
                self.assertTrue(phase["phase_name"])

    def test_workflow_worker_refs_are_registered(self) -> None:
        registered = {worker["worker_id"] for worker in self.registry["workers"]}
        allowed_runtime_roles = {"overkill-factory-gerente"}
        for phase in self.workflow_catalog["phases"]:
            for worker_id in phase.get("required_workers", []):
                if worker_id in allowed_runtime_roles:
                    continue
                with self.subTest(phase=phase["phase_id"], worker=worker_id):
                    self.assertIn(worker_id, registered)

    def test_key_phase_owners_are_not_left_generic(self) -> None:
        phases = {row["phase_id"]: row for row in self.workflow_catalog["phases"]}
        required_pairs = {
            "F6": "factory-orchestrator",
            "F8": "product-face",
            "F10": "security-orchestrator",
            "F17": "qa-verification-worker",
            "F18": "independent-reviewer",
            "F21": "evidence-reconciler",
            "F27": "skill-eval-distiller",
        }

        for phase_id, worker_id in required_pairs.items():
            with self.subTest(phase=phase_id):
                self.assertIn(worker_id, phases[phase_id].get("required_workers", []))

    def test_product_experience_is_first_class_catalog_gate(self) -> None:
        phases = {row["phase_id"]: row for row in self.workflow_catalog["phases"]}
        product_experience = phases["F8"]

        self.assertEqual(product_experience["phase_name"], "Pack And Product Experience Selection")
        for artifact in [
            "product_experience_plan",
            "product_face_packet",
            "project_design_system",
            "professional_design_process",
            "surface_evidence_profile",
            "product_delivery_quality_profile",
        ]:
            with self.subTest(artifact=artifact):
                self.assertIn(artifact, product_experience["required_artifacts"])
        self.assertIn("product-face", product_experience["required_workers"])
        self.assertIn("Product Experience Gate", product_experience["required_gates"])
        self.assertNotIn("F8A", phases)
        self.assertNotIn("product_experience_plan", phases["F11"]["optional_artifacts"])

    def test_executable_plan_catalog_marks_data_and_docs_as_schema_backed_conditionals(self) -> None:
        phases = {row["phase_id"]: row for row in self.workflow_catalog["phases"]}
        executable_plan = phases["F11"]

        self.assertNotIn("data_metrics_plan", executable_plan["optional_artifacts"])
        for artifact in ("data_metrics_plan", "user_docs_onboarding_plan"):
            with self.subTest(artifact=artifact):
                self.assertIn(artifact, executable_plan["conditional_artifacts"])
        self.assertIn("factory/schemas/data-metrics-plan.schema.json", executable_plan["related_schema_refs"])
        self.assertIn("factory/schemas/user-docs-onboarding-plan.schema.json", executable_plan["related_schema_refs"])
        self.assertTrue(
            any("schema-backed runtime validation" in item for item in executable_plan["completion_detection"])
        )

    def test_agent_contract_language_does_not_grant_free_route_authority(self) -> None:
        checked_text = "\n".join(
            [
                json.dumps(self.workflow_catalog, sort_keys=True),
                json.dumps(self.registry, sort_keys=True),
                json.dumps(self.worker_profiles, sort_keys=True),
                (REPO_ROOT / "docs" / "en" / "technical-reference.md").read_text(encoding="utf-8"),
                (ROOT / "agents" / "worker-roster.md").read_text(encoding="utf-8"),
                (REPO_ROOT / "docs" / "en" / "factory-manual.md").read_text(encoding="utf-8"),
            ]
        )
        forbidden_phrases = [
            "Choose method weight",
            "Select product/surface capability coverage",
            "Decide if the line is allowed",
            "surface builder selected by `factory-orchestrator`",
            "Decide released, release candidate",
            "The worker profile still decides authority",
            "route workers",
            "routing decision",
            "routes and points",
            "Chooses Security Architecture Plan routes",
            "Selects current worker results",
            "Select QA modes",
        ]

        for phrase in forbidden_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, checked_text)


if __name__ == "__main__":
    unittest.main()
