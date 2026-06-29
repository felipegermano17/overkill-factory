from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_operator_ui_ux_excellence_audit.py"
REGISTRY_PATH = ROOT / "templates" / "factory-operator-ui-ux-excellence-registry.json"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_operator_ui_ux_excellence_audit", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryOperatorUiUxExcellenceAuditTest(unittest.TestCase):
    def test_audit_passes_with_honest_partial_runtime_gaps(self) -> None:
        module = load_module()
        registry = module.load_registry(REGISTRY_PATH)
        result = module.audit(registry)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["score"], 100)
        self.assertGreaterEqual(result["summary"]["pillar_count"], 14)
        self.assertGreaterEqual(result["summary"]["partial_or_missing_count"], 8)
        self.assertIn("telegram", result["operator_channels"])
        self.assertIn("discord", result["operator_channels"])
        self.assertFalse(result["frontend_considered"])

    def test_manager_bridge_is_single_user_facing_concierge(self) -> None:
        module = load_module()
        registry = module.load_registry(REGISTRY_PATH)
        bridge = registry["manager_bridge"]
        self.assertEqual(bridge["manager_profile"], "overkill-factory-gerente")
        self.assertEqual(bridge["user_facing_role"], "single conversational bridge")
        self.assertIn("external_signal_intake", bridge["responsibilities"])
        self.assertIn("factory_start_and_kanban_projection", bridge["responsibilities"])
        self.assertIn("human_gate_delivery", bridge["responsibilities"])
        self.assertIn("progress_reporting", bridge["responsibilities"])
        self.assertFalse(bridge["direct_worker_chat_required"])
        self.assertFalse(bridge["operator_polling_required"])

    def test_progress_notification_contract_requires_context_not_noise(self) -> None:
        module = load_module()
        registry = module.load_registry(REGISTRY_PATH)
        progress = registry["progress_notification_contract"]
        required = set(progress["required_fields"])
        self.assertIn("percent_complete", required)
        self.assertIn("done_since_last_update", required)
        self.assertIn("currently_executing", required)
        self.assertIn("remaining_work", required)
        self.assertIn("blockers_or_waiting_on", required)
        self.assertIn("next_human_gate_if_any", required)
        self.assertLessEqual(progress["max_silent_minutes_when_running"], 30)
        self.assertTrue(progress["batch_internal_noise"])
        self.assertFalse(progress["notify_on_every_worker_event"])

    def test_human_gate_package_is_pdf_first_with_optional_video_explainer(self) -> None:
        module = load_module()
        registry = module.load_registry(REGISTRY_PATH)
        gate = registry["human_gate_experience_contract"]
        self.assertTrue(gate["human_gate_only_when_material_decision_required"])
        self.assertTrue(gate["material_before_question_required"])
        self.assertEqual(gate["primary_decision_artifact"], "beautiful_pdf")
        self.assertIn("pdf_document", gate["required_assets"])
        self.assertIn("short_plain_language_message", gate["required_assets"])
        self.assertIn("video_explainer_mp4", gate["optional_assets"])
        self.assertIn("manim_animation", gate["recommended_video_paths"])
        self.assertIn("hyperframes_html_video", gate["recommended_video_paths"])
        self.assertIn("json_dump_as_primary_decision_surface", gate["forbidden_patterns"])
        self.assertIn("raw_markdown_as_primary_decision_surface", gate["forbidden_patterns"])

    def test_audit_fails_if_pdf_or_progress_percent_is_removed(self) -> None:
        module = load_module()
        registry = module.load_registry(REGISTRY_PATH)
        broken = json.loads(json.dumps(registry))
        broken["human_gate_experience_contract"]["required_assets"].remove("pdf_document")
        broken["progress_notification_contract"]["required_fields"].remove("percent_complete")
        result = module.audit(broken)
        self.assertEqual(result["result"], "FAIL")
        self.assertTrue(any("pdf_document" in err for err in result["errors"]))
        self.assertTrue(any("percent_complete" in err for err in result["errors"]))

    def test_cli_writes_json_and_markdown(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "audit.json"
            md = Path(tmpdir) / "audit.md"
            exit_code = module.main([
                "--registry",
                str(REGISTRY_PATH),
                "--out",
                str(out),
                "--markdown",
                str(md),
            ])
            self.assertEqual(exit_code, 0)
            payload = json.loads(out.read_text())
            text = md.read_text()
            self.assertEqual(payload["result"], "PASS")
            self.assertIn("Operator UI/UX Excellence Audit", text)
            self.assertIn("beautiful_pdf", text)
            self.assertIn("overkill-factory-gerente", text)


if __name__ == "__main__":
    unittest.main()
