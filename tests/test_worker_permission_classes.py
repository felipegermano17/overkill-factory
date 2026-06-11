import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class WorkerPermissionClassesTest(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(
            (ROOT / "agents" / "worker-registry.public.json").read_text(encoding="utf-8")
        )
        self.matrix = json.loads(
            (ROOT / "agents" / "worker-permission-classes.public.json").read_text(encoding="utf-8")
        )

    def test_every_public_worker_has_permission_class(self):
        worker_ids = {worker["worker_id"] for worker in self.registry["workers"]}
        assignments = set(self.matrix["worker_assignments"])

        self.assertEqual(worker_ids, assignments)

    def test_assignments_reference_existing_classes(self):
        classes = set(self.matrix["classes"])

        for worker_id, class_id in self.matrix["worker_assignments"].items():
            self.assertIn(class_id, classes, worker_id)

        for profile_id, class_id in self.matrix["gateway_profile_assignments"].items():
            self.assertIn(class_id, classes, profile_id)

    def test_no_class_can_mutate_card_state_or_approve_final_gate(self):
        for class_id, spec in self.matrix["classes"].items():
            self.assertIs(spec["can_mutate_card_state"], False, class_id)
            self.assertIs(spec["can_approve_final_gate"], False, class_id)

    def test_each_class_has_plain_boundaries_and_evidence(self):
        for class_id, spec in self.matrix["classes"].items():
            self.assertTrue(spec["plain_purpose"].strip(), class_id)
            self.assertGreaterEqual(len(spec["must_not"]), 1, class_id)
            self.assertGreaterEqual(len(spec["evidence_required"]), 1, class_id)


if __name__ == "__main__":
    unittest.main()
