from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


factoryctl = load_module("factoryctl_for_profiles", ROOT / "scripts" / "factoryctl.py")
profile_validator = load_module("validate_worker_profiles", ROOT / "scripts" / "validate_worker_profiles.py")


class WorkerProfilesTest(unittest.TestCase):
    def test_worker_profiles_are_complete_and_bound_to_hermes(self) -> None:
        self.assertEqual(profile_validator.validate(), [])

    def test_worker_packet_carries_profile_binding(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_product_face.md"
        card = factoryctl.load_json_like(card_path)

        packet = factoryctl.build_worker_packet("product-face", card, card_path)

        self.assertEqual(packet["profile_binding"]["profile_id"], "product-face.profile.v1")
        self.assertEqual(packet["profile_binding"]["hermes_profile_name"], "product-face")
        self.assertEqual(packet["profile_binding"]["queue_class_source"], "worker_task.queue_class")
        self.assertEqual(packet["profile_binding"]["dispatch_queue_policy"]["source_of_truth"], "factoryctl.worker_queue_class")
        self.assertIn("overkill-factory", packet["profile_binding"]["skill_refs"])
        self.assertIn("hermes-kanban", packet["profile_binding"]["skill_refs"])
        self.assertFalse(packet["profile_binding"]["can_mutate_card_state"])
        self.assertEqual(packet["profile_binding"]["last_hermes_smoke_ref"], "validation/hermes-live/factory12-agent-profile-smoke.md")

    def test_transition_plan_exposes_profile_binding_on_worker_tasks(self) -> None:
        card_path = ROOT / "validation" / "cards" / "solana-quasar-r3.md"
        card = factoryctl.load_json_like(card_path)

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="draft",
            to_status="ready",
        )
        tasks = {task["worker_id"]: task for task in plan["worker_tasks"]}

        self.assertEqual(tasks["solana-quasar-auditor"]["profile_binding"]["profile_id"], "solana-quasar-auditor.profile.v1")
        self.assertEqual(tasks["codex-security"]["profile_binding"]["receipt_field"], "security_scan_result")
        self.assertEqual(tasks["supply-chain-gate"]["queue_class"], "blocking-before-ready")
        self.assertEqual(tasks["supply-chain-gate"]["profile_binding"]["queue_class_source"], "worker_task.queue_class")

    def test_profile_binding_queue_is_policy_not_second_runtime_source(self) -> None:
        card_path = ROOT / "validation" / "cards" / "solana-quasar-r3.md"
        card = factoryctl.load_json_like(card_path)

        task = factoryctl.build_worker_task("security-orchestrator", card, card_path)

        self.assertEqual(task["queue_class"], "blocking-before-ready")
        self.assertNotIn("dispatch_queue", task["profile_binding"])
        self.assertEqual(task["profile_binding"]["dispatch_queue_policy"]["source_of_truth"], "factoryctl.worker_queue_class")


if __name__ == "__main__":
    unittest.main()
