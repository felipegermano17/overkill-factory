from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def load_script(name: str) -> Any:
    path = SCRIPT_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


kernel = load_script("factory_v2_kernel")
factoryctl = load_script("factoryctl")


def hashed_event(**overrides: Any) -> dict[str, Any]:
    event = {
        "$schema": "https://overkill-factory.dev/schemas/factory-run-event.schema.json",
        "record_type": "factory_run_event",
        "event_id": "event-001",
        "run_id": "run-001",
        "sequence": 1,
        "event_type": "run_started",
        "created_at": "2026-06-26T00:00:00+00:00",
        "previous_event_hash": None,
        "payload": {"summary": "Factory run started from explicit operator signal."},
    }
    event.update(overrides)
    event["event_hash"] = kernel.factory_event_hash(event)
    return event


def valid_command(command_type: str = "start_run", **payload: Any) -> dict[str, Any]:
    merged_payload = {"summary": "Start factory run from sealed source envelope."}
    merged_payload.update(payload)
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-command.schema.json",
        "record_type": "factory_command",
        "command_id": "cmd-001",
        "run_id": "run-001",
        "command_type": command_type,
        "expected_version": 0,
        "idempotency_key": "idem-0001",
        "created_at": "2026-06-26T00:00:00+00:00",
        "source": {"source_type": "operator", "source_ref": "external:operator:telegram"},
        "authority": {
            "reducer_must_accept": True,
            "bridge_may_execute": False,
            "bridge_may_approve_human_gate": False,
            "adapter_may_decide_business_rule": False,
        },
        "payload": merged_payload,
    }


def valid_decision_outbox() -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-decision-outbox.schema.json",
        "record_type": "factory_decision_outbox",
        "outbox_id": "outbox-001",
        "run_id": "run-001",
        "created_at": "2026-06-26T00:00:00+00:00",
        "pending_decisions": [],
        "authority": {
            "operator_decides": True,
            "bridge_records_only": True,
            "reducer_consumes_decision": True,
        },
    }


def valid_factory_run() -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-run.schema.json",
        "record_type": "factory_run",
        "run_id": "run-001",
        "state_version": 1,
        "status": "planning",
        "created_at": "2026-06-26T00:00:00+00:00",
        "current_phase_id": "F1",
        "runtime_target": {
            "runtime": "hermes_kanban",
            "runtime_target_ref": "hermes:board:example-product",
            "ambient_runtime_allowed": False,
        },
        "board_binding": {
            "binding_ref": "binding-001",
            "board_policy": "factory_must_create_new_board",
            "board_ref": None,
        },
        "command_inbox": [valid_command()],
        "event_log": [hashed_event()],
        "decision_outbox": valid_decision_outbox(),
        "promotion_packets": [],
        "authority": {
            "state_authority": "factory_event_log",
            "transition_authority": "transition_reducer",
            "bridge_may_mutate": False,
            "adapter_may_decide": False,
        },
    }


class FactoryV2KernelTests(unittest.TestCase):
    def test_workflow_compiler_keeps_early_phases_out_of_human_decision_outbox(self) -> None:
        catalog = json.loads((ROOT / "docs" / "factory-workflow.catalog.json").read_text(encoding="utf-8"))

        plan = kernel.compile_workflow_catalog(catalog, compiled_at="2026-06-26T00:00:00+00:00")

        self.assertEqual(kernel.validate_factory_workflow_compiled_plan(plan), [])
        phase_commands = {phase["phase_id"]: set(phase["allowed_commands"]) for phase in plan["phases"]}
        for phase_id in ("F1", "F2", "F3", "F4", "F5"):
            self.assertNotIn("request_decision", phase_commands[phase_id])
        self.assertIn("request_decision", phase_commands["F9"])
        self.assertIn("request_decision", phase_commands["F24"])

    def test_phase_graph_separates_product_phases_from_gates_and_projections(self) -> None:
        graph = json.loads((ROOT / "templates" / "factory-phase-graph.json").read_text(encoding="utf-8"))

        self.assertEqual(kernel.validate_factory_phase_graph(graph), [])
        product_phase_ids = {phase["phase_id"] for phase in graph["product_phases"]}
        self.assertIn("F0", product_phase_ids)
        self.assertNotIn("F8A", product_phase_ids)
        self.assertNotIn("F14", product_phase_ids)
        self.assertNotIn("F19", product_phase_ids)
        self.assertIn("human_gate_event", {event["event_id"] for event in graph["gate_events"]})
        self.assertIn("operator_projection", {projection["projection_id"] for projection in graph["projections"]})

    def test_phase_graph_rejects_legacy_gate_or_projection_as_product_phase(self) -> None:
        graph = json.loads((ROOT / "templates" / "factory-phase-graph.json").read_text(encoding="utf-8"))
        graph["product_phases"].append(
            {
                "phase_id": "F19",
                "phase_index": 19,
                "name": "Human Gate",
                "kind": "product_phase",
                "frontier": "human_gate",
                "entry_contract_refs": ["schemas/human-gate-packet.schema.json"],
                "exit_contract_refs": ["schemas/human-gate-record.schema.json"],
                "next_phase_id": "F20",
            }
        )

        errors = kernel.validate_factory_phase_graph(graph)

        self.assertTrue(any("legacy non-product phase ids" in error for error in errors), errors)

    def test_event_log_hash_chain_rejects_broken_previous_hash(self) -> None:
        first = hashed_event()
        second = hashed_event(
            event_id="event-002",
            sequence=2,
            event_type="phase_advanced",
            previous_event_hash="sha256:" + ("0" * 64),
            payload={"summary": "Advanced to source ledger.", "phase_id": "F2"},
        )

        errors = kernel.validate_factory_event_log([first, second])

        self.assertTrue(any("previous_event_hash" in error for error in errors), errors)

    def test_request_decision_command_requires_delivered_packet(self) -> None:
        command = valid_command("request_decision", phase_id="F9", decision_id="decision-001")

        errors = kernel.validate_factory_command(command)

        self.assertTrue(any("artifact_refs" in error for error in errors), errors)

    def test_factory_run_requires_explicit_non_ambient_hermes_target(self) -> None:
        run = valid_factory_run()
        run["runtime_target"]["ambient_runtime_allowed"] = True

        errors = kernel.validate_factory_run(run)

        self.assertTrue(any("ambient_runtime_allowed" in error for error in errors), errors)

    def test_valid_factory_run_contract_passes(self) -> None:
        self.assertEqual(kernel.validate_factory_run(valid_factory_run()), [])

    def test_factoryctl_v2_commands_validate_generated_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "compiled-plan.json"
            self.assertEqual(
                factoryctl.main_with_args_for_test(
                    [
                        "compile-workflow",
                        "--compiled-at",
                        "2026-06-26T00:00:00+00:00",
                        "--out",
                        str(out),
                    ]
                ),
                0,
            )
            self.assertEqual(factoryctl.main_with_args_for_test(["validate-workflow-compiled-plan", str(out)]), 0)

    def test_factoryctl_validates_phase_graph(self) -> None:
        self.assertEqual(
            factoryctl.main_with_args_for_test(["validate-phase-graph", "templates/factory-phase-graph.json"]),
            0,
        )

    def test_canonical_compiled_workflow_template_is_not_stub(self) -> None:
        plan = json.loads((ROOT / "templates" / "factory-workflow-compiled-plan.json").read_text(encoding="utf-8"))

        self.assertEqual(kernel.validate_factory_workflow_compiled_plan(plan), [])
        self.assertGreaterEqual(plan["phase_count"], 26)
        self.assertEqual(plan["phases"][0]["phase_id"], "F0")
        self.assertEqual(plan["phases"][0]["next_phase_id"], "F1")
        self.assertIn("F27", {phase["phase_id"] for phase in plan["phases"]})

    def test_v2_study_traceability_uses_bounded_truth_levels(self) -> None:
        packet = json.loads((ROOT / "templates" / "v2-study-traceability.json").read_text(encoding="utf-8"))

        self.assertEqual(factoryctl.validate_v2_study_traceability(packet), [])
        statuses = {claim["status"] for claim in packet["claims"]}
        self.assertNotIn("implemented", statuses)
        self.assertIn("kernel_implemented", statuses)
        self.assertIn("runtime_integrated", statuses)
        for claim in packet["claims"]:
            self.assertIn("claim_boundary", claim)
            self.assertGreater(len(claim["known_gaps"]), 0)
            self.assertGreater(len(claim["next_action"]), 10)
        self.assertEqual(
            factoryctl.main_with_args_for_test(
                ["validate-v2-study-traceability", "templates/v2-study-traceability.json"]
            ),
            0,
        )

    def test_v2_study_traceability_rejects_broad_implemented_status(self) -> None:
        packet = json.loads((ROOT / "templates" / "v2-study-traceability.json").read_text(encoding="utf-8"))
        packet["claims"][0]["status"] = "implemented"

        errors = factoryctl.validate_v2_study_traceability(packet)

        self.assertTrue(any("status 'implemented' is forbidden" in error for error in errors), errors)

    def test_v2_study_traceability_rejects_kernel_claim_without_tests_or_fixtures(self) -> None:
        packet = json.loads((ROOT / "templates" / "v2-study-traceability.json").read_text(encoding="utf-8"))
        packet["claims"][0]["test_refs"] = []
        packet["claims"][0]["negative_fixture_refs"] = []
        packet["claims"][0]["status"] = "kernel_implemented"

        errors = factoryctl.validate_v2_study_traceability(packet)

        self.assertTrue(any("kernel_implemented P0 claim requires test_refs" in error for error in errors), errors)
        self.assertTrue(
            any("kernel_implemented P0 claim requires negative_fixture_refs" in error for error in errors),
            errors,
        )

    def test_v2_study_traceability_rejects_runtime_proven_without_runtime_evidence(self) -> None:
        packet = json.loads((ROOT / "templates" / "v2-study-traceability.json").read_text(encoding="utf-8"))
        packet["claims"][0]["status"] = "runtime_proven"
        packet["claims"][0]["known_gaps"] = []
        packet["claims"][0]["runtime_refs"] = ["scripts/factoryctl.py"]
        packet["claims"][0]["test_refs"] = ["tests/test_factory_v2_kernel.py"]

        errors = factoryctl.validate_v2_study_traceability(packet)

        self.assertTrue(any("runtime_proven requires runtime proof refs" in error for error in errors), errors)

    def test_v2_doc_implementation_obligations_validate_and_cross_check_traceability(self) -> None:
        packet = json.loads(
            (ROOT / "templates" / "v2-doc-implementation-obligations.json").read_text(encoding="utf-8")
        )
        traceability = json.loads((ROOT / "templates" / "v2-study-traceability.json").read_text(encoding="utf-8"))

        self.assertEqual(factoryctl.validate_v2_doc_implementation_obligations(packet, traceability), [])
        self.assertEqual(
            factoryctl.main_with_args_for_test(
                [
                    "validate-v2-doc-implementation-obligations",
                    "templates/v2-doc-implementation-obligations.json",
                    "--traceability",
                    "templates/v2-study-traceability.json",
                ]
            ),
            0,
        )

    def test_v2_doc_implementation_obligations_reject_overclaim_without_artifacts(self) -> None:
        packet = json.loads(
            (ROOT / "templates" / "v2-doc-implementation-obligations.json").read_text(encoding="utf-8")
        )
        packet["obligations"][0]["current_truth_level"] = "kernel_implemented"
        packet["obligations"][0]["implemented_artifact_refs"] = []
        packet["obligations"][0]["validation_refs"] = []
        packet["obligations"][0]["negative_fixture_refs"] = []

        errors = factoryctl.validate_v2_doc_implementation_obligations(packet)

        self.assertTrue(any("kernel_implemented requires implemented_artifact_refs" in error for error in errors), errors)
        self.assertTrue(any("kernel_implemented requires validation_refs" in error for error in errors), errors)
        self.assertTrue(any("kernel_implemented requires negative_fixture_refs" in error for error in errors), errors)

    def test_product_experience_control_plane_is_validated_by_cli(self) -> None:
        self.assertEqual(
            factoryctl.main_with_args_for_test(
                ["validate-product-experience-control-plane", "templates/product-experience-control-plane.json"]
            ),
            0,
        )

    def test_readiness_claim_blocks_production_overclaim_without_release_evidence(self) -> None:
        claim = json.loads((ROOT / "templates" / "factory-v2-readiness-claim.json").read_text(encoding="utf-8"))
        self.assertEqual(factoryctl.validate_factory_v2_readiness_claim(claim), [])
        self.assertEqual(
            factoryctl.main_with_args_for_test(
                ["validate-readiness-claim", "templates/factory-v2-readiness-claim.json"]
            ),
            0,
        )

        claim["claimed_state"] = "PRODUCTION_PROVEN"
        claim["claim_scope"] = "production_release"

        errors = factoryctl.validate_factory_v2_readiness_claim(claim)

        self.assertTrue(any("release_proof" in error for error in errors), errors)
        self.assertTrue(any("monitoring_rollback" in error for error in errors), errors)
        self.assertTrue(any("operator_human_gate" in error for error in errors), errors)

    def test_worker_authority_contract_forbids_agent_route_authority(self) -> None:
        contract = json.loads((ROOT / "templates" / "worker-authority-contract.json").read_text(encoding="utf-8"))
        self.assertEqual(factoryctl.validate_worker_authority_contract(contract), [])
        self.assertEqual(
            factoryctl.main_with_args_for_test(
                ["validate-worker-authority-contract", "templates/worker-authority-contract.json"]
            ),
            0,
        )

        contract["forbidden_agent_authorities"].remove("choose_route")

        errors = factoryctl.validate_worker_authority_contract(contract)

        self.assertTrue(any("choose_route" in error for error in errors), errors)

    def test_hermes_reducer_mutation_proof_blocks_bridge_authority(self) -> None:
        proof = json.loads((ROOT / "templates" / "hermes-reducer-mutation-proof.json").read_text(encoding="utf-8"))
        self.assertEqual(factoryctl.validate_hermes_reducer_mutation_proof(proof), [])
        self.assertEqual(
            factoryctl.main_with_args_for_test(
                ["validate-hermes-reducer-mutation-proof", "templates/hermes-reducer-mutation-proof.json"]
            ),
            0,
        )

        proof["bridge_boundary"]["bridge_may_mutate_board"] = True

        errors = factoryctl.validate_hermes_reducer_mutation_proof(proof)

        self.assertTrue(any("bridge_may_mutate_board" in error for error in errors), errors)

    def test_capability_acquisition_contract_requires_search_before_block(self) -> None:
        contract = json.loads((ROOT / "templates" / "capability-acquisition-contract.json").read_text(encoding="utf-8"))
        self.assertEqual(factoryctl.validate_capability_acquisition_contract(contract), [])
        self.assertEqual(
            factoryctl.main_with_args_for_test(
                ["validate-capability-acquisition-contract", "templates/capability-acquisition-contract.json"]
            ),
            0,
        )

        contract["reference_search_policy"]["required_before_blocking"] = False

        errors = factoryctl.validate_capability_acquisition_contract(contract)

        self.assertTrue(any("required_before_blocking" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
