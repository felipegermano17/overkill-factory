from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "operator_control_tower_proof.py"
SPEC = importlib.util.spec_from_file_location("operator_control_tower_proof", MODULE_PATH)
assert SPEC is not None
operator_control_tower_proof = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["operator_control_tower_proof"] = operator_control_tower_proof
SPEC.loader.exec_module(operator_control_tower_proof)


class OperatorControlTowerProofTest(unittest.TestCase):
    def test_readiness_blocks_without_real_mapping_and_bridge(self) -> None:
        readonly = self._readonly_smoke()
        approval = self._approval_smoke()

        receipt = operator_control_tower_proof.build_readiness(
            readonly=readonly,
            approval=approval,
            mapping=None,
            runtime_event=None,
            bridge_health=None,
            evidence_refs=[".tmp/factory-runs/control-tower/control-tower-readonly-smoke.json"],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("real_discord_mapping_present", receipt["blocking_items"])
        self.assertIn("runtime_registration_event_present", receipt["blocking_items"])
        self.assertIn("bridge_health_present", receipt["blocking_items"])

    def test_readiness_pass_creates_public_safe_proof_shape(self) -> None:
        readonly = self._readonly_smoke()
        approval = self._approval_smoke()
        mapping = self._real_mapping()
        runtime_event = self._runtime_event()
        bridge_health = self._bridge_health()

        receipt = operator_control_tower_proof.build_readiness(
            readonly=readonly,
            approval=approval,
            mapping=mapping,
            runtime_event=runtime_event,
            bridge_health=bridge_health,
            evidence_refs=["external:discord-control-tower-mapping"],
            created_at="2026-06-10T00:00:00Z",
        )
        proof = operator_control_tower_proof.build_production_proof(
            ".tmp/factory-runs/control-tower/operator-control-tower-production-readiness.json",
            ["external:discord-control-tower-mapping"],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["blocking_items"], [])
        self.assertEqual(proof["proof_type"], "operator_control_tower")
        self.assertEqual(proof["result"], "PASS")
        self.assertNotIn("real-guild-123", json.dumps(proof))
        operator_control_tower_proof.assert_public_safe(proof)

    def test_placeholder_mapping_does_not_pass(self) -> None:
        receipt = operator_control_tower_proof.build_readiness(
            readonly=self._readonly_smoke(),
            approval=self._approval_smoke(),
            mapping={
                **self._real_mapping(),
                "guild_ref": "redacted-guild",
            },
            runtime_event=self._runtime_event(),
            bridge_health=self._bridge_health(),
            evidence_refs=["external:discord-control-tower-mapping"],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("real_discord_mapping_has_non_placeholder_refs", receipt["blocking_items"])

    def test_placeholder_board_ref_does_not_pass(self) -> None:
        receipt = operator_control_tower_proof.build_readiness(
            readonly=self._readonly_smoke(),
            approval=self._approval_smoke(),
            mapping={
                **self._real_mapping(),
                "board_ref": "redacted-board",
            },
            runtime_event=self._runtime_event(),
            bridge_health=self._bridge_health(),
            evidence_refs=["external:discord-control-tower-mapping"],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("real_discord_mapping_has_non_placeholder_refs", receipt["blocking_items"])

    def test_runtime_event_project_must_match_mapping_project(self) -> None:
        receipt = operator_control_tower_proof.build_readiness(
            readonly=self._readonly_smoke(),
            approval=self._approval_smoke(),
            mapping=self._real_mapping(),
            runtime_event={
                **self._runtime_event(),
                "project_id": "different-project",
            },
            bridge_health=self._bridge_health(),
            evidence_refs=["external:discord-control-tower-mapping"],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("mapping_runtime_project_matches", receipt["blocking_items"])

    def test_runtime_event_requires_real_event_id(self) -> None:
        receipt = operator_control_tower_proof.build_readiness(
            readonly=self._readonly_smoke(),
            approval=self._approval_smoke(),
            mapping=self._real_mapping(),
            runtime_event={
                **self._runtime_event(),
                "event_id": "redacted-event",
            },
            bridge_health=self._bridge_health(),
            evidence_refs=["external:discord-control-tower-mapping"],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("runtime_registration_event_registers_owner_decision", receipt["blocking_items"])

    def test_weak_bridge_health_does_not_pass(self) -> None:
        receipt = operator_control_tower_proof.build_readiness(
            readonly=self._readonly_smoke(),
            approval=self._approval_smoke(),
            mapping=self._real_mapping(),
            runtime_event=self._runtime_event(),
            bridge_health={
                "result": "PASS",
                "checks": {
                    "bot_reachable": True,
                    "bridge_reachable": True,
                    "runtime_readback_reachable": True,
                    "approval_registration_path_reachable": True,
                    "no_discord_source_of_truth": True,
                },
            },
            evidence_refs=["external:discord-control-tower-mapping"],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("bridge_health_uses_contract", receipt["blocking_items"])
        self.assertIn("bridge_health_checks_passed", receipt["blocking_items"])

    def test_bridge_health_without_real_evidence_refs_does_not_pass(self) -> None:
        receipt = operator_control_tower_proof.build_readiness(
            readonly=self._readonly_smoke(),
            approval=self._approval_smoke(),
            mapping=self._real_mapping(),
            runtime_event=self._runtime_event(),
            bridge_health={
                **self._bridge_health(),
                "evidence_refs": ["redacted-bridge-health"],
            },
            evidence_refs=["external:discord-control-tower-mapping"],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("bridge_health_has_real_evidence_refs", receipt["blocking_items"])

    def test_schemas_reject_incomplete_readiness_and_empty_bridge_evidence(self) -> None:
        schemas = operator_control_tower_proof.validator.load_schemas()
        readiness_errors = operator_control_tower_proof.validate_artifact(
            schemas,
            {
                "$schema": "https://overkill-factory.dev/schemas/operator-control-tower-production-readiness.schema.json",
                "record_type": "operator_control_tower_production_readiness",
                "created_at": "2026-06-10T00:00:00Z",
                "result": "PASS",
                "checks": {"control_tower_readonly_contract_passed": True},
                "blocking_items": [],
                "evidence_refs": [".tmp/factory-runs/control-tower/readiness.json"],
                "limits": ["bounded"],
            },
        )
        bridge_errors = operator_control_tower_proof.validate_artifact(
            schemas,
            {
                **self._bridge_health(),
                "evidence_refs": [],
            },
        )

        self.assertTrue(readiness_errors)
        self.assertTrue(bridge_errors)

    def test_cli_blocked_mode_writes_readiness_without_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            readonly = tmp_path / "readonly.json"
            approval = tmp_path / "approval.json"
            out = tmp_path / "readiness.json"
            proof = tmp_path / "proof.json"
            readonly.write_text(json.dumps(self._readonly_smoke()), encoding="utf-8")
            approval.write_text(json.dumps(self._approval_smoke()), encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                rc = operator_control_tower_proof.main_with_args_for_test(
                    [
                        "--readonly-smoke",
                        str(readonly),
                        "--approval-smoke",
                        str(approval),
                        "--out",
                        str(out),
                        "--production-proof-out",
                        str(proof),
                    ]
                )

            self.assertEqual(rc, 1)
            self.assertTrue(out.exists())
            self.assertFalse(proof.exists())

    def test_cli_pass_mode_writes_public_safe_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            readonly = tmp_path / "readonly.json"
            approval = tmp_path / "approval.json"
            mapping = tmp_path / "mapping.json"
            runtime_event = tmp_path / "runtime-event.json"
            bridge_health = tmp_path / "bridge-health.json"
            out = tmp_path / "readiness.json"
            proof = tmp_path / "proof.json"
            readonly.write_text(json.dumps(self._readonly_smoke()), encoding="utf-8")
            approval.write_text(json.dumps(self._approval_smoke()), encoding="utf-8")
            mapping.write_text(json.dumps(self._real_mapping()), encoding="utf-8")
            runtime_event.write_text(json.dumps(self._runtime_event()), encoding="utf-8")
            bridge_health.write_text(json.dumps(self._bridge_health()), encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                rc = operator_control_tower_proof.main_with_args_for_test(
                    [
                        "--readonly-smoke",
                        str(readonly),
                        "--approval-smoke",
                        str(approval),
                        "--mapping",
                        str(mapping),
                        "--runtime-registration-event",
                        str(runtime_event),
                        "--bridge-health",
                        str(bridge_health),
                        "--out",
                        str(out),
                        "--production-proof-out",
                        str(proof),
                    ]
                )

            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())
            self.assertTrue(proof.exists())
            written_proof = json.loads(proof.read_text(encoding="utf-8"))
            operator_control_tower_proof.assert_public_safe(written_proof)
            self.assertNotIn("real-guild-123", json.dumps(written_proof))

    def test_cli_rejects_private_evidence_inside_public_repo(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            readonly = tmp_path / "readonly.json"
            approval = tmp_path / "approval.json"
            mapping = tmp_path / "mapping.json"
            runtime_event = tmp_path / "runtime-event.json"
            bridge_health = tmp_path / "bridge-health.json"
            out = tmp_path / "readiness.json"
            proof = tmp_path / "proof.json"
            readonly.write_text(json.dumps(self._readonly_smoke()), encoding="utf-8")
            approval.write_text(json.dumps(self._approval_smoke()), encoding="utf-8")
            mapping.write_text(json.dumps(self._real_mapping()), encoding="utf-8")
            runtime_event.write_text(json.dumps(self._runtime_event()), encoding="utf-8")
            bridge_health.write_text(json.dumps(self._bridge_health()), encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                rc = operator_control_tower_proof.main_with_args_for_test(
                    [
                        "--readonly-smoke",
                        str(readonly),
                        "--approval-smoke",
                        str(approval),
                        "--mapping",
                        str(mapping),
                        "--runtime-registration-event",
                        str(runtime_event),
                        "--bridge-health",
                        str(bridge_health),
                        "--out",
                        str(out),
                        "--production-proof-out",
                        str(proof),
                    ]
                )

            readiness = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(rc, 1)
            self.assertEqual(readiness["result"], "FAIL")
            self.assertIn("invalid_input_artifact", readiness["blocking_items"])
            self.assertFalse(proof.exists())

    def test_cli_blocked_run_removes_stale_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            readonly = tmp_path / "readonly.json"
            approval = tmp_path / "approval.json"
            out = tmp_path / "readiness.json"
            proof = tmp_path / "proof.json"
            readonly.write_text(json.dumps(self._readonly_smoke()), encoding="utf-8")
            approval.write_text(json.dumps(self._approval_smoke()), encoding="utf-8")
            proof.write_text(json.dumps({"result": "PASS"}), encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                rc = operator_control_tower_proof.main_with_args_for_test(
                    [
                        "--readonly-smoke",
                        str(readonly),
                        "--approval-smoke",
                        str(approval),
                        "--out",
                        str(out),
                        "--production-proof-out",
                        str(proof),
                    ]
                )

            self.assertEqual(rc, 1)
            self.assertTrue(out.exists())
            self.assertFalse(proof.exists())

    def _readonly_smoke(self) -> dict[str, object]:
        return {
            "$schema": "https://overkill-factory.dev/schemas/control-tower-readonly-smoke.schema.json",
            "smoke_id": "control-tower-readonly-smoke",
            "result": "PASS",
            "projection": {},
            "event": {},
            "approval_request": {},
            "mapping": {},
            "readonly_checks": {
                "runtime_snapshot_unchanged": True,
                "projection_derived_from_runtime": True,
                "approval_pending_only": True,
                "mapping_redacted": True,
                "no_discord_mutation_claim": True,
            },
        }

    def _approval_smoke(self) -> dict[str, object]:
        return {
            "$schema": "https://overkill-factory.dev/schemas/control-tower-approval-registration-smoke.schema.json",
            "smoke_id": "control-tower-approval-registration-smoke",
            "result": "PASS",
            "pending_approval": {},
            "registered_approval": {},
            "approval_event": {},
            "negative_cases": [
                {
                    "case": "wrong_role",
                    "accepted": False,
                }
            ],
            "registration_checks": {
                "valid_decision_records_event": True,
                "wrong_role_rejected": True,
                "expired_decision_rejected": True,
                "scope_expansion_rejected": True,
                "unknown_approval_rejected": True,
                "ambiguous_decision_rejected": True,
                "runtime_mutation_not_claimed": True,
            },
        }

    def _real_mapping(self) -> dict[str, object]:
        return {
            "$schema": "https://overkill-factory.dev/schemas/discord-control-tower-mapping.schema.json",
            "project_id": "prod-control-tower-project",
            "runtime": "hermes",
            "board_ref": "real-board-ref",
            "guild_ref": "real-guild-123",
            "dashboard_message_ref": "real-message-123",
            "approval_channel_ref": "real-approval-channel-123",
            "bot_health_channel_ref": "real-bot-health-channel-123",
            "last_synced_at": "2026-06-10T00:00:00Z",
        }

    def _runtime_event(self) -> dict[str, object]:
        return {
            "$schema": "https://overkill-factory.dev/schemas/control-tower-event.schema.json",
            "event_id": "evt-real-approval-registered",
            "event_type": "approval_recorded",
            "severity": "P2",
            "project_id": "prod-control-tower-project",
            "source": "bridge",
            "summary": "Owner approval registered in runtime.",
            "created_at": "2026-06-10T00:00:00Z",
        }

    def _bridge_health(self) -> dict[str, object]:
        return {
            "$schema": "https://overkill-factory.dev/schemas/operator-control-tower-bridge-health.schema.json",
            "record_type": "operator_control_tower_bridge_health",
            "created_at": "2026-06-10T00:00:00Z",
            "result": "PASS",
            "checks": {
                "bot_reachable": True,
                "bridge_reachable": True,
                "runtime_readback_reachable": True,
                "approval_registration_path_reachable": True,
                "no_discord_source_of_truth": True,
                "no_private_material_in_public_receipt": True,
            },
            "evidence_refs": ["external:bridge-health"],
            "limits": [
                "This private health receipt is represented publicly only through redacted refs."
            ],
        }


if __name__ == "__main__":
    unittest.main()
