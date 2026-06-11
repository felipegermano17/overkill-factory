from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT_PATH = ROOT / "validation" / "prepilot" / "master-task-readiness.json"
STRONG_KINDS = {
    "schema",
    "template",
    "script",
    "test",
    "worker_registry",
    "worker_profile",
    "worker_roster",
    "profile_binding",
    "permission_matrix",
    "validation_artifact",
    "runtime_adapter",
}
EXPECTED_TASK_IDS = [
    "classify_vfinal_agents",
    "create_dedicated_discord_manager_gateway",
    "officialize_discord_control_tower_bridge",
    "remove_factory_gateway_from_private_project_profile",
    "lock_canonical_provider_model",
    "align_public_repo_hermes_and_canonical_docs",
    "separate_permissions_by_agent_class",
    "execute_reference_agent_skill_study",
    "run_complete_prepilot_battery",
]


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


class PrepilotMasterTaskReadinessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))

    def test_receipt_tracks_the_exact_nine_prepilot_tasks(self) -> None:
        self.assertEqual(self.receipt["record_type"], "prepilot_master_task_readiness")
        self.assertEqual(self.receipt["result"], "PASS")

        tasks = self.receipt["tasks"]
        self.assertEqual([task["task_number"] for task in tasks], list(range(1, 10)))
        self.assertEqual([task["task_id"] for task in tasks], EXPECTED_TASK_IDS)

        for task in tasks:
            with self.subTest(task=task["task_id"]):
                self.assertTrue(task["plain_goal"])
                self.assertTrue(task["implementation_summary"])
                self.assertNotEqual(task["status"], "BLOCKED")
                self.assertTrue(
                    any(ref["kind"] in STRONG_KINDS for ref in task["evidence_refs"]),
                    "task cannot be marked ready by documentation alone",
                )

    def test_all_public_repo_refs_exist(self) -> None:
        for task in self.receipt["tasks"]:
            for ref in task["evidence_refs"]:
                path = ref["path"].split("#", 1)[0]
                if path.startswith(("external:", "redacted:", "generated:")):
                    continue
                with self.subTest(task=task["task_id"], path=path):
                    self.assertTrue((ROOT / path).exists(), path)

    def test_critical_runtime_claims_are_backed_by_public_safe_receipts(self) -> None:
        permissions = load_json("agents/worker-permission-classes.public.json")
        provider_audit = load_json("validation/hermes-live/factory-vfinal-provider-model-audit.json")
        runtime_status = load_json("validation/hermes-live/factory-vfinal-runtime-status-check.json")
        bridge_readiness = load_json("validation/control-tower/operator-control-tower-production-readiness.json")
        battery = load_json("validation/battery/factory-battery-results.json")

        self.assertEqual(
            permissions["gateway_profile_assignments"]["overkill-factory-gerente"],
            "discord_interface",
        )
        self.assertEqual(permissions["worker_assignments"]["discord-control-tower-bridge"], "bridge")

        self.assertEqual(provider_audit["result"], "PASS")
        self.assertTrue(provider_audit["checks"]["dedicated_gateway_profile_present"])
        self.assertTrue(provider_audit["checks"]["private_product_profile_not_used_as_factory_gateway"])
        self.assertTrue(provider_audit["checks"]["factory_scope_uses_canonical_provider_model"])
        self.assertTrue(provider_audit["checks"]["factory_scope_auth_present"])
        self.assertTrue(provider_audit["checks"]["no_duplicate_conceptual_profiles_present"])
        self.assertEqual(provider_audit["counts"]["conceptual_duplicate_profiles_removed"], 17)
        self.assertEqual(provider_audit["counts"]["unexpected_factory_duplicate_profiles"], 0)

        self.assertEqual(runtime_status["result"], "PASS")
        self.assertTrue(runtime_status["checks"]["hermes_status_readonly_passed"])
        self.assertTrue(runtime_status["checks"]["profile_list_readonly_passed"])
        self.assertTrue(runtime_status["checks"]["gateway_service_running"])
        self.assertTrue(runtime_status["checks"]["discord_configured"])
        self.assertTrue(runtime_status["checks"]["dedicated_gerente_gateway_running"])
        self.assertTrue(runtime_status["checks"]["private_product_profile_not_factory_gateway"])
        self.assertTrue(runtime_status["checks"]["factory_profile_set_has_no_conceptual_duplicates"])
        self.assertTrue(runtime_status["checks"]["raw_private_values_omitted"])

        self.assertEqual(bridge_readiness["result"], "PASS")
        self.assertTrue(bridge_readiness["checks"]["real_discord_mapping_present"])
        self.assertTrue(bridge_readiness["checks"]["runtime_registration_event_present"])
        self.assertTrue(bridge_readiness["checks"]["bridge_health_uses_contract"])

        self.assertEqual(battery["failed_count"], 0)
        self.assertGreaterEqual(battery["scenario_count"], 12)

    def test_factory_production_readiness_includes_prepilot_master_receipt(self) -> None:
        readiness = load_json("validation/factory-production-readiness/current-readiness.json")
        component_ids = {component["id"] for component in readiness["components"]}
        evidence_refs = set(readiness["evidence_refs"])

        self.assertIn("prepilot_master_task_readiness", component_ids)
        self.assertIn("hermes_vfinal_runtime_status_check", component_ids)
        self.assertIn("validation/prepilot/master-task-readiness.json", evidence_refs)
        self.assertIn("validation/hermes-live/factory-vfinal-runtime-status-check.json", evidence_refs)

    def test_backlog_roadmap_stays_outside_the_canonical_document(self) -> None:
        roadmap = (ROOT / "docs" / "roadmap" / "factory-vfinal-prepilot-roadmap.md").read_text(
            encoding="utf-8"
        )
        task6_refs = {
            ref["path"]
            for task in self.receipt["tasks"]
            if task["task_id"] == "align_public_repo_hermes_and_canonical_docs"
            for ref in task["evidence_refs"]
        }

        self.assertIn("docs/roadmap/factory-vfinal-prepilot-roadmap.md", task6_refs)
        self.assertIn("This roadmap is not the canonical factory document.", roadmap)
        self.assertIn("Backlog That Must Not Pollute The Canonical Document", roadmap)
        self.assertIn("Before Starting A Real Pilot", roadmap)


if __name__ == "__main__":
    unittest.main()
