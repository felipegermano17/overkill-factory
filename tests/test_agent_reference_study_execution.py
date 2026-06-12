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
        self.assertIn("create public-safe factory improvement issues", skill_eval["authority"]["may"])
        self.assertIn("mutate critical factory contracts without explicit human gate", skill_eval["authority"]["must_not"])
        self.assertIn("factory improvement issue or rejection rationale", skill_eval["output_contract"]["required_sections"])
        self.assertIn("critical factory contract change", skill_eval["authority"]["human_gate_required_when"])
        self.assertIn("project-specific maintenance loops", " ".join(skill_eval["authority"]["must_not"]))

    def test_reference_study_execution_is_preserved_as_contracts_not_research_doc(self) -> None:
        self.assertFalse((ROOT / "docs" / "research").exists())
        self.assertTrue((ROOT / "templates" / "work-unit-contract.json").is_file())
        self.assertTrue((ROOT / "templates" / "reviewer-selection-plan.json").is_file())
        self.assertTrue((ROOT / "tests" / "test_agent_reference_study_execution.py").is_file())


if __name__ == "__main__":
    unittest.main()
