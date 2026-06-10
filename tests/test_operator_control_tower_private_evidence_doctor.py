from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "operator_control_tower_private_evidence_doctor.py"
SPEC = importlib.util.spec_from_file_location("operator_control_tower_private_evidence_doctor", MODULE_PATH)
assert SPEC is not None
doctor = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["operator_control_tower_private_evidence_doctor"] = doctor
SPEC.loader.exec_module(doctor)


class OperatorControlTowerPrivateEvidenceDoctorTest(unittest.TestCase):
    def test_missing_private_evidence_blocks_without_private_paths(self) -> None:
        report = doctor.build_doctor_report(created_at="2026-06-10T00:00:00Z")

        self.assertEqual(report["result"], "BLOCKED")
        self.assertEqual(
            report["decision"]["operator_control_tower_production_proof_input"],
            "blocked",
        )
        self.assertIn("mapping_file_present", report["blocking_items"])
        self.assertIn("missing:mapping", report["evidence_refs"])

    def test_valid_private_evidence_passes_with_redacted_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            mapping = tmp_path / "discord-control-tower-mapping.json"
            runtime_event = tmp_path / "runtime-approval-event.json"
            bridge_health = tmp_path / "bridge-health.json"

            mapping.write_text(
                json.dumps(
                    {
                        "$schema": "https://overkill-factory.dev/schemas/discord-control-tower-mapping.schema.json",
                        "project_id": "prod-project-1",
                        "runtime": "hermes",
                        "board_ref": "runtime-board-1",
                        "guild_ref": "guild-1",
                        "dashboard_channel_ref": "dashboard-channel-1",
                        "dashboard_message_ref": "dashboard-message-1",
                        "approval_channel_ref": "approval-channel-1",
                        "project_thread_ref": "project-thread-1",
                        "evidence_channel_ref": "evidence-channel-1",
                        "bot_health_channel_ref": "bot-health-channel-1",
                        "last_synced_at": "2026-06-10T00:00:00Z",
                    }
                ),
                encoding="utf-8",
            )
            runtime_event.write_text(
                json.dumps(
                    {
                        "$schema": "https://overkill-factory.dev/schemas/control-tower-event.schema.json",
                        "event_id": "evt-prod-approval-1",
                        "event_type": "approval_recorded",
                        "severity": "P2",
                        "project_id": "prod-project-1",
                        "source": "bridge",
                        "summary": "Structured owner approval registered.",
                        "details": "Private production evidence fixture.",
                        "action_required": False,
                        "owner_role": "Factory Owner",
                        "evidence_refs": ["external:private-runtime-registration"],
                        "discord_target": "approval-channel-1",
                        "created_at": "2026-06-10T00:00:00Z",
                    }
                ),
                encoding="utf-8",
            )
            bridge_health.write_text(
                json.dumps(
                    {
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
                        "evidence_refs": ["external:private-bridge-health-evidence"],
                        "limits": ["Private fixture; raw ids stay outside public receipts."],
                    }
                ),
                encoding="utf-8",
            )

            report = doctor.build_doctor_report(
                mapping_path=mapping,
                runtime_event_path=runtime_event,
                bridge_health_path=bridge_health,
                created_at="2026-06-10T00:00:00Z",
            )

        self.assertEqual(report["result"], "PASS")
        self.assertEqual(report["blocking_items"], [])
        self.assertEqual(report["input_errors"], [])
        self.assertIn("external:discord-control-tower-mapping", report["evidence_refs"])
        self.assertNotIn(str(tmp_path), json.dumps(report))


if __name__ == "__main__":
    unittest.main()
