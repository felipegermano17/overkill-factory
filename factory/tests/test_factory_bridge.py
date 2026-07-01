from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
MODULE_PATH = ROOT / "scripts" / "factory_bridge.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location("factory_bridge", MODULE_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["factory_bridge"] = module
    spec.loader.exec_module(module)
    return module


class FactoryBridgeTest(unittest.TestCase):
    def test_operator_inbox_deduplicates_pending_events_and_acks_them(self) -> None:
        bridge = load_bridge()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            inbox = Path(tmp) / "operator-inbox"
            first = bridge.emit_event(
                inbox_dir=inbox,
                run_id="run-alpha",
                event_type="human_gate_required",
                severity="requires_user",
                source="hermes_transition_hook",
                summary="R3 owner decision is required before done.",
                refs=["docs/pt-BR/manual.md"],
                requires_user=True,
                payload={"gate_type": "R3"},
            )
            second = bridge.emit_event(
                inbox_dir=inbox,
                run_id="run-alpha",
                event_type="human_gate_required",
                severity="requires_user",
                source="hermes_transition_hook",
                summary="R3 owner decision is required before done.",
                refs=["docs/pt-BR/manual.md"],
                requires_user=True,
                payload={"gate_type": "R3"},
            )
            summary = bridge.summarize_inbox(inbox_dir=inbox)

            bridge.ack_event(
                inbox_dir=inbox,
                event_id=first["event_id"],
                actor="external_operator",
                response="decision captured in human gate record",
                evidence_ref="external:operator:human-gate-record",
            )
            acked_summary = bridge.summarize_inbox(inbox_dir=inbox)
            events = [json.loads(line) for line in (inbox / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            pending = [json.loads(line) for line in (inbox / "pending.jsonl").read_text(encoding="utf-8").splitlines()]
            acks = [json.loads(line) for line in (inbox / "acks.jsonl").read_text(encoding="utf-8").splitlines()]

        self.assertEqual(first["event_id"], second["event_id"])
        self.assertEqual(len(events), 1)
        self.assertEqual(len(pending), 1)
        self.assertEqual(summary["pending_count"], 1)
        self.assertEqual(summary["pending_events"][0]["event_type"], "human_gate_required")
        self.assertEqual(acked_summary["pending_count"], 0)
        self.assertEqual(acks[0]["event_id"], first["event_id"])
        self.assertFalse(first["factory_authority"]["can_close_gate"])
        self.assertFalse(first["factory_authority"]["can_execute_factory_work"])

    def test_prompt_classification_covers_status_question_decision_change_and_learnback(self) -> None:
        bridge = load_bridge()

        cases = {
            "como esta a fabrica?": "status_bridge",
            "por que ficou bloqueado no done?": "question_bridge",
            "aprovo o gate R3 para esse escopo": "decision_bridge",
            "mude o escopo para incluir teste de release": "change_bridge",
            "aprenda com esse erro e melhore a fabrica": "learnback_forwarding",
            "quero iniciar uma nova fabrica para um produto": "intake_bridge",
            "agora pode iniciar a fabrica com esse material": "start_bridge",
        }

        for prompt, expected_mode in cases.items():
            with self.subTest(prompt=prompt):
                result = bridge.classify_prompt(prompt)
                self.assertEqual(result["bridge_mode"], expected_mode)
                self.assertFalse(result["authority"]["bridge_may_execute_factory_work"])
                self.assertFalse(result["authority"]["bridge_may_auto_approve_human_gate"])

    def test_operator_bridge_context_adds_context_without_claiming_watchdog_authority(self) -> None:
        bridge = load_bridge()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            inbox = Path(tmp) / "operator-inbox"
            bridge.emit_event(
                inbox_dir=inbox,
                run_id="run-alpha",
                event_type="transition_blocked",
                severity="blocked",
                source="hermes_transition_hook",
                summary="Done transition blocked by missing worker result.",
                refs=["adapters/hermes/transition_hook.py"],
                requires_user=True,
            )

            session_context = bridge.format_hook_context(bridge.summarize_inbox(inbox_dir=inbox))
            prompt_context = bridge.format_hook_context(
                bridge.summarize_inbox(inbox_dir=inbox),
                bridge.classify_prompt("status da fabrica"),
            )

        self.assertIn("transition_blocked", session_context)
        self.assertIn("Durable Operator Inbox", session_context)
        self.assertIn("Operator bridge hooks are wake-up/context hooks", session_context)
        self.assertIn("factory_bridge_start_request", session_context)
        self.assertIn("the bridge must not create Hermes boards or cards", session_context)
        self.assertIn("status_bridge", prompt_context)
        self.assertIn("explicit factory runtime target", prompt_context)
        self.assertIn("ambient/default Hermes store", prompt_context)

    def test_new_project_bridge_contract_addresses_factory_without_creating_board(self) -> None:
        bridge = load_bridge()

        envelope = bridge.build_source_envelope(
            run_id="run-alpha",
            operator_goal="Start a new product project from source material.",
            project_mode="new_project",
            source_refs=["external:operator:brief", "C:/private/source.xlsx"],
        )
        start = bridge.build_start_request(
            run_id="run-alpha",
            operator_goal="Start a new product project from source material.",
            project_mode="new_project",
            source_envelope_ref="external:operator:source-envelope",
            run_record_ref="external:operator:bridge-run",
        )
        run = bridge.build_run_record(
            run_id="run-alpha",
            goal="Start a new product project from source material.",
            project_mode="new_project",
            source_envelope_ref="external:operator:source-envelope",
            start_request_ref="external:operator:start-request",
        )

        self.assertEqual(envelope["record_type"], "factory_bridge_source_envelope")
        self.assertEqual(envelope["source_items"][0]["received_as"], "opaque_ref")
        self.assertFalse(envelope["source_items"][0]["bridge_summary_created"])
        self.assertFalse(envelope["source_items"][0]["bridge_interpretation_created"])
        self.assertEqual(envelope["target_board_policy"]["policy"], "factory_must_create_new_board")
        self.assertIsNone(envelope["target_board_policy"]["existing_board_ref"])
        self.assertFalse(envelope["handoff_to_factory"]["bridge_may_create_hermes_board"])
        self.assertEqual(envelope["handoff_to_factory"]["gateway_profile"], "overkill-factory-gerente")
        self.assertEqual(envelope["handoff_to_factory"]["orchestrator_worker"], "factory-orchestrator")
        self.assertEqual(envelope["operator_language_policy"]["primary_language"], "pt-BR")
        self.assertTrue(envelope["operator_language_policy"]["kanban_cards_follow_primary_language"])
        self.assertEqual(start["operator_language_policy"]["primary_language"], "pt-BR")
        self.assertTrue(start["operator_language_policy"]["decision_packages_follow_primary_language"])
        self.assertTrue(start["bridge_limits"]["bridge_must_not_create_hermes_board"])
        self.assertTrue(start["bridge_limits"]["bridge_must_not_create_hermes_cards"])
        self.assertEqual(start["requested_factory_action"]["owner"], "factory-orchestrator")
        self.assertEqual(run["target_board_policy"]["board_creation_owner"], "factory_start_path")

        with self.assertRaises(ValueError):
            bridge.build_start_request(
                run_id="run-alpha",
                operator_goal="Start a new product project from source material.",
                project_mode="new_project",
                source_envelope_ref="external:operator:source-envelope",
                existing_board_ref="kanban:old-board",
            )

    def test_existing_project_requires_explicit_board_reference(self) -> None:
        bridge = load_bridge()

        with self.assertRaises(ValueError):
            bridge.build_run_record(
                run_id="run-beta",
                goal="Continue existing factory run.",
                project_mode="existing_project",
            )

        run = bridge.build_run_record(
            run_id="run-beta",
            goal="Continue existing factory run.",
            project_mode="existing_project",
            existing_board_ref="kanban:existing-board",
        )

        self.assertEqual(run["target_board_policy"]["policy"], "use_explicit_existing_board")
        self.assertEqual(run["target_board_policy"]["existing_board_ref"], "kanban:existing-board")
        self.assertFalse(run["target_board_policy"]["requires_new_hermes_board"])

        with self.assertRaises(ValueError):
            bridge.build_run_record(
                run_id="run-gamma",
                goal="Continue existing factory run.",
                project_mode="existing_project",
                existing_board_ref="existing-board",
            )

    def test_source_envelope_and_start_request_cli_emit_bridge_only_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            envelope_path = Path(tmp) / "source-envelope.json"
            start_path = Path(tmp) / "start-request.json"
            subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "source-envelope",
                    "--run-id",
                    "run-cli",
                    "--project-mode",
                    "new_project",
                    "--operator-goal",
                    "Start a new product project.",
                    "--source-ref",
                    "external:operator:brief",
                    "--out",
                    str(envelope_path),
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "start-request",
                    "--run-id",
                    "run-cli",
                    "--project-mode",
                    "new_project",
                    "--operator-goal",
                    "Start a new product project.",
                    "--source-envelope-ref",
                    "external:operator:source-envelope",
                    "--out",
                    str(start_path),
                ],
                check=True,
                text=True,
                capture_output=True,
            )

            envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
            start = json.loads(start_path.read_text(encoding="utf-8"))

        self.assertEqual(envelope["record_type"], "factory_bridge_source_envelope")
        self.assertEqual(start["record_type"], "factory_bridge_start_request")
        self.assertEqual(envelope["operator_language_policy"]["primary_language"], "pt-BR")
        self.assertEqual(start["operator_language_policy"]["primary_language"], "pt-BR")
        self.assertTrue(start["bridge_limits"]["bridge_must_not_create_hermes_board"])
        self.assertEqual(start["handoff_to_factory"]["gateway_profile"], "overkill-factory-gerente")

    def test_decision_and_handoff_packets_preserve_operator_boundary(self) -> None:
        bridge = load_bridge()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            inbox = Path(tmp) / "operator-inbox"
            event = bridge.emit_event(
                inbox_dir=inbox,
                run_id="run-alpha",
                event_type="human_gate_required",
                severity="requires_user",
                source="factoryctl",
                summary="Release owner decision is required.",
                refs=["docs/pt-BR/linha-de-producao.md"],
                requires_user=True,
            )
            decision = bridge.build_decision_record(
                run_id="run-alpha",
                event_id=event["event_id"],
                decision_type="human_gate_response",
                decision="changes_requested",
                actor="product_owner",
                summary="Release waits for rollback evidence.",
                evidence_refs=["external:operator:release-decision"],
                human_gate_record_ref="external:operator:human-gate-record",
            )
            handoff = bridge.build_handoff_packet(run_id="run-alpha", inbox_dir=inbox)

            self.assertEqual(decision["record_type"], "factory_bridge_decision")
            self.assertEqual(decision["decision"], "changes_requested")
            self.assertEqual(decision["human_gate_record_ref"], "external:operator:human-gate-record")
            self.assertIn("external:operator:human-gate-record", decision["evidence_refs"])
            self.assertFalse(decision["authority"]["closes_factory_gate"])
            self.assertIn("record structured response", handoff["safe_next_actions"])
            self.assertIn("close Hermes card without Receipt Five", handoff["forbidden_actions"])
            self.assertEqual(handoff["pending_operator_events"][0]["event_id"], event["event_id"])

            with self.assertRaises(ValueError):
                bridge.build_decision_record(
                    run_id="run-alpha",
                    event_id=event["event_id"],
                    decision_type="human_gate_response",
                    decision="approved",
                    actor="product_owner",
                    summary="Approved in chat only.",
                )

    def test_corrupt_or_missing_inbox_is_reported_in_bridge_context(self) -> None:
        bridge = load_bridge()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            missing_context = bridge.format_hook_context(
                bridge.summarize_inbox(inbox_dir=Path(tmp) / "missing-inbox"),
                bridge.classify_prompt("status da fabrica"),
            )
            inbox = Path(tmp) / "operator-inbox"
            inbox.mkdir()
            (inbox / "pending.jsonl").write_text("{bad json\n", encoding="utf-8")
            corrupt_context = bridge.format_hook_context(
                bridge.summarize_inbox(inbox_dir=inbox),
                bridge.classify_prompt("status da fabrica"),
            )

        self.assertIn("Inbox health: warning", missing_context)
        self.assertIn("operator inbox directory does not exist yet", missing_context)
        self.assertIn("Runtime target: explicit board/run ref required", missing_context)
        self.assertIn("invalid JSONL record", corrupt_context)

    def test_operator_bridge_architecture_documents_the_bridge_modes(self) -> None:
        architecture = (REPO_ROOT / "docs" / "pt-BR" / "linha-de-producao.md").read_text(encoding="utf-8")

        for expected in [
            "Pedido", "Fonte", "Entendimento", "Verdade do produto", "Hermes", "Evidência", "Decisão", "Recibo"
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, architecture)

        self.assertIn("A fábrica não simula autoridade humana", architecture)
        self.assertIn("No Hermes", architecture)
        self.assertIn("card", architecture)
        self.assertIn("worker", architecture)
        self.assertIn("bloqueio", architecture)
        self.assertIn("retomada", architecture)
        self.assertNotIn("Codex plugin", architecture)
        self.assertNotIn("Codex hooks", architecture)


if __name__ == "__main__":
    unittest.main()
