from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AgentReferenceStudyExecutionTest(unittest.TestCase):
    def load_json(self, relative: str) -> dict:
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_new_operational_contract_templates_point_to_schemas(self) -> None:
        pairs = {
            "templates/work-unit-contract.json": "schemas/work-unit-contract.schema.json",
            "templates/reviewer-selection-plan.json": "schemas/reviewer-selection-plan.schema.json",
            "templates/qa-verification-plan.json": "schemas/qa-verification-plan.schema.json",
            "templates/agent-eval-result.json": "schemas/agent-eval-result.schema.json",
            "templates/full-product-sot-scope-coverage.json": "schemas/full-product-sot-scope-coverage.schema.json",
            "templates/specialist-research-plan.json": "schemas/specialist-research-plan.schema.json",
            "templates/specialist-decision-packet.json": "schemas/specialist-decision-packet.schema.json",
            "templates/production-promotion-ladder.json": "schemas/production-promotion-ladder.schema.json",
            "templates/product-creation-plan.json": "schemas/product-creation-plan.schema.json",
            "templates/product-context-packet.json": "schemas/product-context-packet.schema.json",
            "templates/product-implementation-readiness.json": "schemas/product-implementation-readiness.schema.json",
        }

        for template_path, schema_path in pairs.items():
            with self.subTest(template=template_path):
                template = self.load_json(template_path)
                schema = self.load_json(schema_path)
                self.assertEqual(template["$schema"], schema["$id"])

    def test_reference_study_contracts_are_bound_to_existing_agents(self) -> None:
        profiles = self.load_json("agents/worker-profiles.public.json")["profiles"]

        decomposition = profiles["decomposition-planner"]
        self.assertIn("loop_plan", decomposition["input_contract"]["required"])
        self.assertIn("software_development_plan", decomposition["input_contract"]["required"])
        self.assertIn("work unit contracts", decomposition["output_contract"]["required_sections"])
        self.assertIn("reviewer selection plan", decomposition["output_contract"]["required_sections"])

        reviewer = profiles["independent-reviewer"]
        self.assertIn("reviewer_selection_plan", reviewer["input_contract"]["required"])
        self.assertIn("reviewer-selection ref", reviewer["evidence_contract"]["required_refs"])

        qa = profiles["qa-verification-worker"]
        self.assertIn("qa modes", qa["activation"]["surfaces"])
        self.assertIn("mode coverage matrix", qa["evidence_contract"]["required_refs"])

        skill_eval = profiles["skill-eval-distiller"]
        self.assertIn("agent_eval_plan", skill_eval["input_contract"]["required"])
        self.assertIn("permission class", skill_eval["output_contract"]["required_sections"])

    def test_reference_study_execution_is_preserved_as_contracts_not_research_doc(self) -> None:
        self.assertFalse((ROOT / "docs" / "research").exists())
        self.assertTrue((ROOT / "templates" / "work-unit-contract.json").is_file())
        self.assertTrue((ROOT / "templates" / "reviewer-selection-plan.json").is_file())
        self.assertTrue((ROOT / "tests" / "test_agent_reference_study_execution.py").is_file())


if __name__ == "__main__":
    unittest.main()
