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
        self.assertIn("request_decision", phase_commands["F19"])

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
        command = valid_command("request_decision", phase_id="F19", decision_id="decision-001")

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


if __name__ == "__main__":
    unittest.main()
