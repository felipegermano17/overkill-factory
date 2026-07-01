from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "worker_accountability.py"
SPEC = importlib.util.spec_from_file_location("worker_accountability", MODULE_PATH)
assert SPEC is not None
accountability = importlib.util.module_from_spec(SPEC)
sys.modules["worker_accountability"] = accountability
assert SPEC.loader is not None
SPEC.loader.exec_module(accountability)

VALIDATOR_PATH = ROOT / "scripts" / "validate_public_json_artifacts.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_public_json_artifacts", VALIDATOR_PATH)
assert VALIDATOR_SPEC is not None
public_json_validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
sys.modules["validate_public_json_artifacts_for_accountability"] = public_json_validator
assert VALIDATOR_SPEC.loader is not None
VALIDATOR_SPEC.loader.exec_module(public_json_validator)


class WorkerAccountabilityTest(unittest.TestCase):
    def test_repeated_shallow_output_routes_to_mandatory_independent_review(self) -> None:
        events = [
            {
                "worker_id": "product-face",
                "event_type": "shallow_artifact",
                "evidence_refs": ["external:sanitized/accountability/product-face-shallow-1"],
            },
            {
                "worker_id": "product-face",
                "event_type": "shallow_artifact",
                "evidence_refs": ["external:sanitized/accountability/product-face-shallow-2"],
            },
        ]

        ledger = accountability.build_accountability_ledger(events, generated_at="2026-07-01T00:00:00Z")
        row = ledger["worker_accountability"]["product-face"]

        self.assertEqual(row["shallow_artifact_count"], 2)
        self.assertEqual(row["routing_consequence"]["action"], "mandatory_independent_review")
        self.assertEqual(row["routing_consequence"]["required_reviewer"], "independent-reviewer")
        self.assertIn("block_downstream_consumption_until_review_pass", row["routing_consequence"]["allowed_actions"])
        self.assertEqual(ledger["routing_summary"]["strongest_action"], "mandatory_independent_review")
        self.assertEqual(accountability.validate_ledger(ledger), [])

    def test_repeated_failures_demote_worker_route(self) -> None:
        events = [
            {
                "worker_id": "implementation-worker",
                "event_type": "failed_run",
                "evidence_refs": ["external:sanitized/accountability/impl-failure-1"],
            },
            {
                "worker_id": "implementation-worker",
                "event_type": "failure",
                "evidence_refs": ["external:sanitized/accountability/impl-failure-2"],
            },
        ]

        ledger = accountability.build_accountability_ledger(events, generated_at="2026-07-01T00:00:00Z")
        consequence = ledger["worker_accountability"]["implementation-worker"]["routing_consequence"]

        self.assertEqual(consequence["action"], "demote_to_review_queue")
        self.assertEqual(consequence["accountability_state"], "demoted")
        self.assertEqual(consequence["queue_class"], "demoted-review-queue")
        self.assertIn("prefer_alternate_worker_when_available", consequence["allowed_actions"])

    def test_high_repeated_negative_count_escalates_for_profile_review(self) -> None:
        events = [
            {
                "worker_id": "product-sot-planner",
                "event_type": event_type,
                "evidence_refs": [f"external:sanitized/accountability/sot-{index}"],
            }
            for index, event_type in enumerate(
                ["bad_output", "rework_required", "shallow_artifact", "review_fail", "repair_loop"],
                start=1,
            )
        ]

        ledger = accountability.build_accountability_ledger(events, generated_at="2026-07-01T00:00:00Z")
        consequence = ledger["worker_accountability"]["product-sot-planner"]["routing_consequence"]

        self.assertEqual(consequence["action"], "escalate_for_profile_review")
        self.assertEqual(consequence["required_reviewer"], "skill-eval-distiller")
        self.assertIn("block_new_sensitive_assignments", consequence["allowed_actions"])
        self.assertEqual(ledger["routing_summary"]["strongest_action"], "escalate_for_profile_review")

    def test_positive_signal_does_not_erase_negative_accountability(self) -> None:
        events = [
            {
                "worker_id": "qa-verification-worker",
                "event_type": "bad_output",
                "evidence_refs": ["external:sanitized/accountability/qa-bad-output"],
            },
            {
                "worker_id": "qa-verification-worker",
                "event_type": "positive_review",
                "evidence_refs": ["external:sanitized/accountability/qa-positive-review"],
            },
        ]

        ledger = accountability.build_accountability_ledger(events, generated_at="2026-07-01T00:00:00Z")
        row = ledger["worker_accountability"]["qa-verification-worker"]

        self.assertEqual(row["positive_signal_count"], 1)
        self.assertEqual(row["negative_total"], 1)
        self.assertEqual(row["routing_consequence"]["action"], "watch")

    def test_raw_kanban_task_refs_are_rejected_from_public_ledger_inputs(self) -> None:
        events = [
            {
                "worker_id": "product-face",
                "event_type": "shallow_artifact",
                "evidence_refs": ["t_" + "123abc"],
            }
        ]

        errors = accountability.event_validation_errors(events)

        self.assertTrue(any("public-safe sanitized ref" in error for error in errors), errors)

    def test_template_worker_accountability_ledger_matches_public_schema(self) -> None:
        schema = json.loads((ROOT / "schemas" / "worker-accountability-ledger.schema.json").read_text(encoding="utf-8"))
        schemas = {"worker-accountability-ledger.schema.json": schema}
        template = json.loads((ROOT / "templates" / "worker-accountability-ledger.json").read_text(encoding="utf-8"))

        errors = public_json_validator.validate_node(
            schema,
            template,
            "$",
            schemas=schemas,
        )

        self.assertEqual(errors, [])
        self.assertEqual(accountability.validate_ledger(template), [])

    def test_cli_builds_valid_ledger_from_events(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            tmp_path = Path(tempdir)
            events_path = tmp_path / "events.json"
            out_path = tmp_path / "ledger.json"
            events_path.write_text(
                json.dumps(
                    {
                        "events": [
                            {
                                "worker_id": "frontend-builder",
                                "event_type": "rework_required",
                                "evidence_refs": ["external:sanitized/accountability/frontend-rework-1"],
                            },
                            {
                                "worker_id": "frontend-builder",
                                "event_type": "rework_required",
                                "evidence_refs": ["external:sanitized/accountability/frontend-rework-2"],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            exit_code = accountability.main(["build", str(events_path), "--out", str(out_path)])
            built = json.loads(out_path.read_text(encoding="utf-8"))

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                built["worker_accountability"]["frontend-builder"]["routing_consequence"]["action"],
                "mandatory_independent_review",
            )
            self.assertEqual(accountability.main(["validate", str(out_path)]), 0)


if __name__ == "__main__":
    unittest.main()
