from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factoryctl.py"
SPEC = importlib.util.spec_from_file_location("factoryctl_operator_experience", MODULE_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl_operator_experience"] = factoryctl
SPEC.loader.exec_module(factoryctl)


def run_factoryctl(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/factoryctl.py", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def run_factoryctl_blocking_ok(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/factoryctl.py", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def write_card_without_security_packet(tmp: Path) -> Path:
    source = (ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md").read_text(encoding="utf-8")
    data = json.loads(source[source.find("{") : source.rfind("}") + 1])
    data.pop("security_scan_packet", None)
    path = tmp / "blocked-card.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def write_product_card_missing_experience(tmp: Path) -> Path:
    data = json.loads((ROOT / "templates" / "vfinal-factory-card.json").read_text(encoding="utf-8"))
    data["card_id"] = "TEST-MISSING-PRODUCT-EXPERIENCE"
    data["phase"] = "F11"
    data["surfaces"] = ["frontend", "product-face"]
    data["capability_pack_contract"]["covered_surfaces"] = ["frontend", "product-face"]
    data.pop("product_experience_plan", None)
    data.pop("product_face_packet", None)
    data.pop("professional_design_process", None)
    path = tmp / "missing-product-experience.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def write_blocked_worker_result(tmp: Path, *, human_gate: bool = False) -> Path:
    worker_id = "human-gate-clerk" if human_gate else "handoff-packer"
    record_type = "human_gate_record" if human_gate else "handoff_packet_result"
    blocker_type = "human_gate" if human_gate else "orchestration"
    route_id = "recovery:test-card:human-gate" if human_gate else "recovery:test-card:handoff-repair"
    recovery = {
        "blocker_type": blocker_type,
        "factory_owned_repair_allowed": not human_gate,
        "human_gate_required": human_gate,
        "recovery_route_id": route_id,
        "repair_owner_worker": worker_id,
        "repair_task_ref": f"hermes:intent:{route_id}",
        "invalidates_refs": ["worker-result:stale-output"],
        "supersedes_refs": ["worker-result:fresh-output"],
        "fresh_review_required": not human_gate,
        "fresh_review_result_ref": "worker-result:independent-reviewer:fresh-pass",
        "unblock_authority_ref": "human_gate_record" if human_gate else "graph-requirement:fresh-review-pass",
        "retry_policy": {
            "max_attempts": 3,
            "attempt_number": 1,
            "attempt_number_role": "planner_seed_not_runtime_counter",
            "runtime_attempt_source": "hermes_task_history",
            "runtime_attempt_marker": "factory_recovery_attempt",
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "stop_classes": ["human_gate_required", "repeated_failure"],
            "escalation_reason": "only after bounded recovery fails",
        },
        "hermes_runtime_boundary": {
            "runtime_authority": "hermes_kanban",
            "uses_native_kanban_primitives": True,
            "local_state_authority": False,
        },
        "automatic_repair_loop": {
            "required": not human_gate,
            "factory_owned_repair_allowed": not human_gate,
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "route_ref": route_id,
            "stage_order": ["repair", "audit", "rerun", "reconcile"],
            "stages": [
                {"stage": "repair", "owner_worker": worker_id, "expected_output_ref": "worker-result:fresh-repair"},
                {"stage": "audit", "owner_worker": "independent-reviewer", "expected_output_ref": "worker-result:fresh-review-pass"},
                {"stage": "rerun", "owner_worker": worker_id, "expected_output_ref": "worker-result:fresh-pass-or-waiver"},
                {"stage": "reconcile", "owner_worker": "evidence-reconciler", "command_or_route": "reconcile-ready-work-units"},
            ],
            "post_repair_reconciliation_required": not human_gate,
            "stop_classes": ["human_gate", "repeated_failed_recovery"],
        },
        "downstream_freeze_scope": ["next worker", "done promotion"],
    }
    if human_gate:
        recovery["fresh_review_result_ref"] = "human_gate_record"
    result = {
        "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": record_type,
        "created_at": "2026-06-16T00:00:00+00:00",
        "worker": {"id": worker_id, "name": "Fixture Worker", "factory_phase": "F13"},
        "card_ref": {
            "card_id": "VAL-SOLANA-QUASAR-R3",
            "slice_id": "VAL_FACTORY_HEAVY_03",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["solana-quasar"],
        },
        "result": "BLOCKED",
        "blocking_findings": True,
        "findings_summary": "Synthetic blocked fixture.",
        "tool_or_profile": "fixture-tool",
        "executed_by": "fixture-runner",
        "evidence_refs": ["README.md"],
        "evidence_kind": "synthetic",
        "reusable_for_product": False,
        "next_action": "follow the recovery route",
        "recovery_recommendation": recovery,
    }
    path = tmp / ("human-gate-block.json" if human_gate else "recoverable-block.json")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return path


class OperatorExperienceTest(unittest.TestCase):
    def test_factoryctl_exposes_single_operator_entrypoint(self) -> None:
        help_text = run_factoryctl("--help").stdout
        run_help = run_factoryctl("run", "--help").stdout

        for command in [
            "doctor",
            "init",
            "run",
            "operator-interface",
            "start-conversation",
            "briefing-package",
            "unblock-plan",
            "recovery-plan",
            "help-next",
        ]:
            with self.subTest(command=command):
                self.assertIn(command, help_text)
        self.assertIn("minimal", run_help)

    def test_telegram_interface_contract_requires_proactive_deep_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "operator-interface.json"
            run_factoryctl(
                "operator-interface",
                "--primary-interface",
                "telegram",
                "--out",
                str(out),
            )
            profile = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(profile["primary_interface"], "telegram")
        self.assertEqual(profile["primary_language"], "pt-BR")
        self.assertTrue(profile["language_policy"]["user_facing_surfaces_follow_primary_language"])
        self.assertTrue(profile["language_policy"]["kanban_cards_follow_primary_language"])
        self.assertTrue(profile["language_policy"]["decision_packages_follow_primary_language"])
        self.assertTrue(profile["language_policy"]["internal_factory_surfaces_may_use_english"])
        self.assertIn("kanban_card_titles", profile["language_policy"]["user_facing_surfaces"])
        self.assertEqual(profile["interface_capabilities"]["message_rendering_mode"], "plain_text")
        self.assertFalse(profile["interface_capabilities"]["rich_bot_messages_allowed"])
        self.assertTrue(profile["interface_capabilities"]["standard_file_attachments_only"])
        self.assertFalse(profile["conversation_policy"]["status_polling_required"])
        self.assertTrue(profile["conversation_policy"]["operator_not_required_to_poll"])
        self.assertEqual(profile["proactive_notification_policy"]["contact_mode"], "manager_report_only")
        self.assertEqual(profile["proactive_notification_policy"]["manager_profile"], "overkill-factory-gerente")
        self.assertFalse(profile["proactive_notification_policy"]["direct_runtime_notifications_allowed"])
        self.assertFalse(profile["proactive_notification_policy"]["direct_worker_notifications_allowed"])
        self.assertFalse(profile["proactive_notification_policy"]["direct_artifact_dump_notifications_allowed"])
        self.assertFalse(profile["proactive_notification_policy"]["notify_subscribe_allowed"])
        self.assertNotIn("worker_batch_completed", profile["proactive_notification_policy"]["notify_on"])
        self.assertIn("worker_batch_completed", profile["proactive_notification_policy"]["batch_without_waking_for"])
        self.assertIn("decision_required", profile["proactive_notification_policy"]["notify_on"])
        self.assertIn("manager_report_required", profile["proactive_notification_policy"]["notify_on"])
        self.assertIn("idle_timeout_detected", profile["proactive_notification_policy"]["notify_on"])
        self.assertEqual(profile["artifact_delivery_policy"]["required_attachment_formats"], ["markdown", "pdf"])
        self.assertIn("product_sot", profile["artifact_delivery_policy"]["send_for_artifact_types"])

    def test_start_conversation_blocks_factory_start_until_understanding_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            interface = tmp / "operator-interface.json"
            pending = tmp / "start-pending.json"
            confirmed = tmp / "start-confirmed.json"
            run_factoryctl("operator-interface", "--primary-interface", "telegram", "--out", str(interface))
            run_factoryctl(
                "start-conversation",
                "--operator-interface",
                str(interface),
                "--source-envelope-ref",
                "external:operator-source-envelope",
                "--out",
                str(pending),
            )
            run_factoryctl(
                "start-conversation",
                "--operator-interface",
                str(interface),
                "--source-envelope-ref",
                "external:operator-source-envelope",
                "--confirmed",
                "--confirmed-understanding-ref",
                "external:sanitized-operator-understanding-confirmed",
                "--factory-start-request-ref",
                "external:operator-factory-start-request",
                "--out",
                str(confirmed),
            )
            missing_start_request = run_factoryctl_blocking_ok(
                "start-conversation",
                "--operator-interface",
                str(interface),
                "--source-envelope-ref",
                "external:operator-source-envelope",
                "--confirmed",
                "--confirmed-understanding-ref",
                "external:sanitized-operator-understanding-confirmed",
                "--out",
                str(tmp / "missing-start-request.json"),
            )
            pending_payload = json.loads(pending.read_text(encoding="utf-8"))
            confirmed_payload = json.loads(confirmed.read_text(encoding="utf-8"))

        self.assertFalse(pending_payload["acceptance"]["factory_start_allowed"])
        self.assertTrue(pending_payload["handoff"]["user_decision_required"])
        self.assertTrue(confirmed_payload["acceptance"]["factory_start_allowed"])
        self.assertEqual(confirmed_payload["handoff"]["next_artifact"], "factory_bridge_start_request")
        self.assertFalse(confirmed_payload["acceptance"]["execution_allowed"])
        self.assertGreaterEqual(
            pending_payload["product_understanding_loop"]["minimum_questions_before_confirmation"],
            3,
        )
        self.assertTrue(pending_payload["product_understanding_loop"]["rich_material_requires_source_inventory"])
        self.assertTrue(pending_payload["product_understanding_loop"]["brownfield_input_requires_brownfield_plan"])
        self.assertGreaterEqual(len(pending_payload["conversation_state"]["open_questions"]), 3)
        self.assertNotEqual(missing_start_request.returncode, 0)
        self.assertIn("factory_start_request_ref is required", missing_start_request.stderr)

    def test_start_conversation_rejects_shallow_pending_understanding(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            interface = tmp / "operator-interface.json"
            pending = tmp / "start-pending.json"
            run_factoryctl("operator-interface", "--primary-interface", "telegram", "--out", str(interface))
            run_factoryctl(
                "start-conversation",
                "--operator-interface",
                str(interface),
                "--source-envelope-ref",
                "external:operator-source-envelope",
                "--out",
                str(pending),
            )
            payload = json.loads(pending.read_text(encoding="utf-8"))

        payload["conversation_state"]["open_questions"] = ["Confirma?"]

        errors = factoryctl.validate_factory_start_conversation(payload)

        self.assertTrue(any("enough product understanding questions" in error for error in errors), errors)

        payload["product_understanding_loop"]["minimum_questions_before_confirmation"] = 1
        errors = factoryctl.validate_factory_start_conversation(payload)

        self.assertTrue(any("at least 3 understanding questions" in error for error in errors), errors)

    def test_briefing_package_requires_pdf_markdown_and_push_delivery_for_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            interface = tmp / "operator-interface.json"
            briefing = tmp / "briefing.json"
            run_factoryctl("operator-interface", "--primary-interface", "telegram", "--out", str(interface))
            run_factoryctl(
                "briefing-package",
                "--operator-interface",
                str(interface),
                "--artifact-type",
                "architecture_candidate",
                "--artifact-ref",
                "external:sanitized-architecture-candidate",
                "--decision-required",
                "--out",
                str(briefing),
            )
            payload = json.loads(briefing.read_text(encoding="utf-8"))

        required_assets = {
            asset["kind"]
            for asset in payload["delivery_assets"]
            if asset["required_for_operator_decision"]
        }
        self.assertTrue({"markdown_document", "pdf_document"}.issubset(required_assets))
        self.assertTrue(payload["proactive_delivery"]["push_required"])
        self.assertFalse(payload["proactive_delivery"]["operator_polling_required"])
        self.assertFalse(payload["acceptance"]["summary_only"])

    def test_unblock_plan_emits_semantic_recovery_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "unblock-plan.json"
            run_factoryctl(
                "unblock-plan",
                "--card",
                "examples/cards/v35_valid_onchain_auditor_scan.md",
                "--out",
                str(out),
            )
            payload = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(payload["record_type"], "factory_recovery_plan")
        self.assertIn("next_safe_actions", payload)
        self.assertIn("recovery_routes", payload)
        self.assertEqual(payload["gate_predicate_result"], "PASS")
        self.assertEqual(payload["recovery_routes"], [])
        self.assertEqual(payload["hermes_runtime_boundary"]["runtime_authority"], "hermes_kanban")
        self.assertFalse(payload["hermes_runtime_boundary"]["local_state_authority"])
        self.assertTrue(payload["hermes_runtime_boundary"]["no_shadow_dispatcher"])
        self.assertTrue(any("does not execute workers" in item for item in payload["limits"]))

    def test_recovery_plan_names_hermes_native_materialization(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            card = write_card_without_security_packet(tmp)
            out = tmp / "recovery-plan.json"
            result = run_factoryctl_blocking_ok(
                "recovery-plan",
                "--card",
                str(card),
                "--out",
                str(out),
            )
            payload = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["$schema"], "https://overkill-factory.dev/schemas/factory-recovery-plan.schema.json")
        self.assertGreater(len(payload["recovery_routes"]), 0)
        route = payload["recovery_routes"][0]
        self.assertEqual(route["hermes_materialization"]["runtime_authority"], "hermes_kanban")
        self.assertFalse(route["hermes_materialization"]["local_state_authority"])
        self.assertIn("kanban_task", route["hermes_materialization"]["native_primitives"])

    def test_help_next_routes_missing_product_surface_planning_to_product_experience_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            card = write_product_card_missing_experience(Path(tmpdir))
            result = run_factoryctl("help-next", "--card", str(card))
            payload = json.loads(result.stdout)

        self.assertEqual(payload["workflow_phase"]["phase_id"], "F8")
        self.assertEqual(payload["workflow_phase"]["phase_name"], "Pack And Product Experience Selection")
        self.assertIn("Product Experience Plan", payload["factory_next_action"]["action"])
        self.assertIn("surface pack", payload["factory_next_action"]["why"].lower())
        self.assertIn("product_experience_plan required for vFinal product-facing surfaces", payload["blocked_because"])
        self.assertIn(
            "populate card.product_experience_plan with public-safe contract data or attach the required worker evidence",
            payload["evidence_needed"],
        )

    def test_help_next_exposes_recoverable_block_as_factory_recovery_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            write_blocked_worker_result(tmp)
            result = run_factoryctl(
                "help-next",
                "--card",
                "examples/cards/v35_valid_onchain_auditor_scan.md",
                "--worker-results-dir",
                str(tmp),
            )
            payload = json.loads(result.stdout)

        self.assertEqual(len(payload["active_recovery_routes"]), 1)
        route = payload["active_recovery_routes"][0]
        self.assertEqual(route["recovery_route_id"], "recovery:test-card:handoff-repair")
        self.assertTrue(route["factory_owned_repair_allowed"])
        self.assertFalse(route["human_gate_required"])
        self.assertEqual(route["repair_owner_worker"], "handoff-packer")
        self.assertTrue(route["automatic_repair_loop"]["required"])
        self.assertEqual(route["automatic_repair_loop"]["stage_order"], ["repair", "audit", "rerun", "reconcile"])
        self.assertEqual(route["automatic_repair_loop"]["stages"][-1]["command_or_route"], "reconcile-ready-work-units")
        self.assertIn("next worker", route["downstream_freeze_scope"])
        self.assertIn("factoryctl recovery-plan", payload["factory_next_action"]["command_refs"])
        self.assertIn("recovery route recovery:test-card:handoff-repair", payload["factory_next_action"]["action"])

    def test_help_next_keeps_human_gate_recovery_as_user_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            write_blocked_worker_result(tmp, human_gate=True)
            result = run_factoryctl(
                "help-next",
                "--card",
                "examples/cards/v35_valid_onchain_auditor_scan.md",
                "--worker-results-dir",
                str(tmp),
            )
            payload = json.loads(result.stdout)

        self.assertEqual(len(payload["active_recovery_routes"]), 1)
        route = payload["active_recovery_routes"][0]
        self.assertEqual(route["recovery_route_id"], "recovery:test-card:human-gate")
        self.assertFalse(route["factory_owned_repair_allowed"])
        self.assertTrue(route["human_gate_required"])
        self.assertFalse(route["automatic_repair_loop"]["required"])
        self.assertIn("human gate record", route["operator_visible_next_action"])
        self.assertTrue(
            any(decision["decision_type"] == "authority_required" for decision in payload["user_decision_required"])
        )

    def test_doctor_reports_public_install_health_without_real_hermes_e2e(self) -> None:
        result = run_factoryctl("doctor", "--json")
        payload = json.loads(result.stdout)
        check_ids = {check["id"] for check in payload["checks"]}

        self.assertEqual(payload["result"], "PASS")
        self.assertTrue(
            {
                "python_version",
                "package_metadata",
                "repository_shape",
                "minimal_example",
                "public_cli",
                "hermes_runtime_optional",
                "hermes_e2e_deferred",
            }.issubset(check_ids)
        )
        self.assertFalse(any(check["status"] == "FAIL" for check in payload["checks"]))
        deferred = next(check for check in payload["checks"] if check["id"] == "hermes_e2e_deferred")
        self.assertEqual(deferred["status"], "INFO")

    def test_run_minimal_uses_factoryctl_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            out = tmp / "quickstart-result.json"
            packets = tmp / "packets"

            result = run_factoryctl("run", "minimal", "--out", str(out), "--packets-out", str(packets))
            payload = json.loads(out.read_text(encoding="utf-8"))

            self.assertIn("PASS", result.stdout)
            self.assertEqual(payload["result"], "PASS")
            self.assertGreater(payload["worker_packet_count"], 0)
            self.assertTrue(any(packets.glob("*.json")))

    def test_init_creates_hermes_friendly_operator_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "sample-project"
            result = run_factoryctl("init", "--out", str(target), "--project-name", "sample-project")

            self.assertIn("initialized", result.stdout.lower())
            self.assertTrue((target / "overkill.factory.json").is_file())
            self.assertTrue((target / "cards" / "minimal-card.md").is_file())
            self.assertTrue((target / "worker-packets" / ".gitkeep").is_file())
            self.assertTrue((target / "receipts" / ".gitkeep").is_file())
            self.assertTrue((target / "README.md").is_file())

            config = json.loads((target / "overkill.factory.json").read_text(encoding="utf-8"))
            readme = (target / "README.md").read_text(encoding="utf-8")
            self.assertEqual(config["project_name"], "sample-project")
            self.assertEqual(config["runtime"]["name"], "Hermes")
            self.assertIn("factoryctl doctor", readme)
            self.assertIn("factoryctl run minimal", readme)
            self.assertIn("Connect this workspace to your Hermes", readme)


if __name__ == "__main__":
    unittest.main()
