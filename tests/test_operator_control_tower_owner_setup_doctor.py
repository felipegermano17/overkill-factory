from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "operator_control_tower_owner_setup_doctor.py"
SPEC = importlib.util.spec_from_file_location("operator_control_tower_owner_setup_doctor", MODULE_PATH)
assert SPEC is not None
doctor = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["operator_control_tower_owner_setup_doctor"] = doctor
SPEC.loader.exec_module(doctor)


class OperatorControlTowerOwnerSetupDoctorTest(unittest.TestCase):
    def test_missing_owner_setup_blocks_without_private_paths(self) -> None:
        report = doctor.build_doctor_report(created_at="2026-06-10T00:00:00Z")

        self.assertEqual(report["result"], "BLOCKED")
        self.assertIn("owner_setup_file_present", report["blocking_items"])
        self.assertIn("missing:discord-owner-setup", report["evidence_refs"])

    def test_valid_owner_setup_passes_with_redacted_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            owner_setup = tmp_path / "discord-owner-setup.json"
            owner_setup.write_text(
                json.dumps(
                    {
                        "$schema": "https://overkill-factory.dev/schemas/discord-control-tower-owner-setup.schema.json",
                        "record_type": "discord_control_tower_owner_setup",
                        "created_at": "2026-06-10T00:00:00Z",
                        "result": "PASS",
                        "project_id": "project-1",
                        "checks": {
                            "server_exists": True,
                            "bot_application_created": True,
                            "bot_invited_to_server": True,
                            "message_content_intent_enabled": True,
                            "server_members_intent_enabled": True,
                            "owner_user_allowlisted": True,
                            "approval_button_interaction_path_configured": True,
                            "approval_button_interaction_auth_validated": True,
                            "required_channels_exist": True,
                            "owner_approval_channel_restricted": True,
                            "bot_health_channel_available": True,
                            "least_privilege_permissions_reviewed": True,
                            "token_stored_outside_public_repo": True,
                            "offboarding_plan_ready": True,
                        },
                        "required_channels": {
                            "dashboard": "dashboard-channel-1",
                            "intake": "intake-channel-1",
                            "owner_approvals": "approval-channel-1",
                            "access_requests": "access-channel-1",
                            "blockers": "blockers-channel-1",
                            "evidence_feed": "evidence-channel-1",
                            "release_room": "release-channel-1",
                            "bot_health": "health-channel-1",
                            "projects_area": "projects-area-1",
                        },
                        "evidence_refs": ["discord-api:private-owner-setup-readback"],
                        "limits": ["Private fixture; raw ids stay outside public receipts."],
                    }
                ),
                encoding="utf-8",
            )

            report = doctor.build_doctor_report(
                owner_setup_path=owner_setup,
                created_at="2026-06-10T00:00:00Z",
            )

        self.assertEqual(report["result"], "PASS")
        self.assertEqual(report["blocking_items"], [])
        self.assertEqual(report["input_errors"], [])
        self.assertIn("external:discord-owner-setup", report["evidence_refs"])
        self.assertNotIn(str(tmp_path), json.dumps(report))

    def test_owner_setup_requires_discord_interactions_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            owner_setup = tmp_path / "discord-owner-setup.json"
            owner_setup.write_text(
                json.dumps(
                    {
                        "$schema": "https://overkill-factory.dev/schemas/discord-control-tower-owner-setup.schema.json",
                        "record_type": "discord_control_tower_owner_setup",
                        "created_at": "2026-06-10T00:00:00Z",
                        "result": "PASS",
                        "project_id": "project-1",
                        "checks": {
                            "server_exists": True,
                            "bot_application_created": True,
                            "bot_invited_to_server": True,
                            "message_content_intent_enabled": True,
                            "server_members_intent_enabled": True,
                            "owner_user_allowlisted": True,
                            "required_channels_exist": True,
                            "owner_approval_channel_restricted": True,
                            "bot_health_channel_available": True,
                            "least_privilege_permissions_reviewed": True,
                            "token_stored_outside_public_repo": True,
                            "offboarding_plan_ready": True,
                        },
                        "required_channels": {
                            "dashboard": "dashboard-channel-1",
                            "intake": "intake-channel-1",
                            "owner_approvals": "approval-channel-1",
                            "access_requests": "access-channel-1",
                            "blockers": "blockers-channel-1",
                            "evidence_feed": "evidence-channel-1",
                            "release_room": "release-channel-1",
                            "bot_health": "health-channel-1",
                            "projects_area": "projects-area-1",
                        },
                        "evidence_refs": ["discord-api:private-owner-setup-readback"],
                        "limits": ["Private fixture; raw ids stay outside public receipts."],
                    }
                ),
                encoding="utf-8",
            )

            report = doctor.build_doctor_report(
                owner_setup_path=owner_setup,
                created_at="2026-06-10T00:00:00Z",
            )

        self.assertEqual(report["result"], "BLOCKED")
        self.assertIn("required_owner_checks_passed", report["blocking_items"])
        self.assertTrue(
            any("approval_button_interaction_path_configured" in error for error in report["input_errors"])
        )


if __name__ == "__main__":
    unittest.main()
