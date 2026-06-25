from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import factory_no_idle_watchdog as watchdog  # noqa: E402


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.boards = [
            {"slug": "default", "archived": False, "total": 0},
            {"slug": "product-alpha", "archived": False, "total": 12},
            {"slug": "old-archived", "archived": True, "total": 9},
        ]
        self.no_idle_payloads: dict[str, dict] = {}
        self.dispatch_payloads: dict[str, dict] = {}

    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        if argv == ["hermes", "kanban", "boards", "list", "--json"]:
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(self.boards), stderr="")
        if len(argv) >= 4 and argv[1].endswith("live_kanban_adapter.py") and argv[2] == "no-idle":
            board = argv[argv.index("--board") + 1]
            payload = self.no_idle_payloads.get(board) or {
                "mode": "no-idle",
                "board": board,
                "remediation_task_id": None,
                "no_idle_state": {
                    "status": "empty_or_complete",
                    "classification": "no_unfinished_work_seen",
                    "state": {},
                },
            }
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload), stderr="")
        if len(argv) >= 4 and argv[1].endswith("live_kanban_adapter.py") and argv[2] == "dispatch":
            board = argv[argv.index("--board") + 1]
            payload = self.dispatch_payloads.get(board) or {
                "mode": "dispatch",
                "board": board,
                "spawned": [{"task_id": "kanban:redacted"}],
                "dispatch_observed_state": {
                    "ready_before_count": 1,
                    "running_before_count": 0,
                    "running_after_count": 1,
                },
            }
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload), stderr="")
        if len(argv) >= 4 and argv[1].endswith("factory_bridge.py") and argv[2] == "emit-event":
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps({"ok": True}), stderr="")
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="unexpected command")


class FactoryNoIdleWatchdogTest(unittest.TestCase):
    def test_discovers_only_nonempty_nonarchived_nondefault_boards(self) -> None:
        fake = FakeRunner()

        boards = watchdog.discover_boards(
            hermes_bin="hermes",
            excluded_boards={"default"},
            runner=fake,
        )

        self.assertEqual(boards, ["product-alpha"])

    def test_watchdog_creates_remediation_then_calls_native_dispatch(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": "kanban:redacted",
            "no_idle_state": {
                "status": "remediation_required",
                "classification": "unfinished_work_without_ready_running_or_human_gate_only_block",
                "native_dispatch_required_next": True,
                "state": {
                    "todo": {"count": 3},
                    "blocked": {"count": 2},
                    "ready": {"count": 0},
                    "running": {"count": 0},
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.json"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = watchdog.main(
                    [
                        "--board",
                        "product-alpha",
                        "--create-remediation",
                        "--dispatch",
                        "--state-file",
                        str(state_file),
                    ],
                    runner=fake,
                )

        self.assertEqual(result, 0)
        self.assertIn("no-idle detectado", buffer.getvalue())
        no_idle_call = next(call for call in fake.calls if len(call) > 2 and call[2] == "no-idle")
        dispatch_call = next(call for call in fake.calls if len(call) > 2 and call[2] == "dispatch")
        self.assertIn("--create-remediation", no_idle_call)
        self.assertEqual(dispatch_call[2], "dispatch")

    def test_watchdog_does_not_repeat_same_message(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": None,
            "no_idle_state": {
                "status": "active",
                "classification": "running_work_exists",
                "state": {"running": {"count": 1}},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.json"
            first = io.StringIO()
            second = io.StringIO()
            with redirect_stdout(first):
                watchdog.main(["--board", "product-alpha", "--state-file", str(state_file)], runner=fake)
            with redirect_stdout(second):
                watchdog.main(["--board", "product-alpha", "--state-file", str(state_file)], runner=fake)

        self.assertIn("workers em execução", first.getvalue())
        self.assertEqual(second.getvalue(), "")

    def test_watchdog_dedupes_same_remediation_state_with_different_task_id(self) -> None:
        fake = FakeRunner()
        payload = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": "kanban:redacted-a",
            "no_idle_state": {
                "status": "remediation_required",
                "classification": "unfinished_work_without_ready_running_or_human_gate_only_block",
                "state": {
                    "todo": {"count": 3},
                    "blocked": {"count": 2},
                    "ready": {"count": 0},
                    "running": {"count": 0},
                },
            },
        }
        fake.no_idle_payloads["product-alpha"] = payload
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.json"
            first = io.StringIO()
            second = io.StringIO()
            with redirect_stdout(first):
                watchdog.main(["--board", "product-alpha", "--state-file", str(state_file)], runner=fake)
            payload["remediation_task_id"] = "kanban:redacted-b"
            with redirect_stdout(second):
                watchdog.main(["--board", "product-alpha", "--state-file", str(state_file)], runner=fake)

        self.assertIn("no-idle detectado", first.getvalue())
        self.assertEqual(second.getvalue(), "")

    def test_watchdog_summarizes_dependency_gated_without_remediation_language(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": None,
            "no_idle_state": {
                "status": "dependency_gated",
                "classification": "todo_dependency_gated_by_blocked_ancestors",
                "state": {
                    "todo": {"count": 3},
                    "blocked": {"count": 2},
                    "ready": {"count": 0},
                    "running": {"count": 0},
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                watchdog.main(["--board", "product-alpha", "--state-file", str(Path(tmp) / "state.json")], runner=fake)

        output = buffer.getvalue()
        self.assertIn("fila presa por dependências bloqueadas", output)
        self.assertNotIn("remediação segura criada", output)

    def test_watchdog_input_required_emits_user_decision_event_without_dispatch(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": None,
            "no_idle_state": {
                "status": "input_required",
                "classification": "todo_dependency_gated_by_missing_operator_inputs",
                "operator_input_required": True,
                "operator_input_task_refs": ["kanban:redacted-blocker"],
                "state": {
                    "todo": {"count": 3},
                    "blocked": {"count": 2},
                    "ready": {"count": 0},
                    "running": {"count": 0},
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                watchdog.main(
                    [
                        "--board",
                        "product-alpha",
                        "--dispatch",
                        "--emit-events",
                        "--state-file",
                        str(Path(tmp) / "state.json"),
                        "--inbox-dir",
                        str(Path(tmp) / "inbox"),
                    ],
                    runner=fake,
                )

        output = buffer.getvalue()
        self.assertIn("fila presa por insumos faltantes", output)
        self.assertFalse(any(len(call) > 2 and call[2] == "dispatch" for call in fake.calls))
        emit_call = next(call for call in fake.calls if len(call) > 2 and call[2] == "emit-event")
        self.assertIn("--requires-user", emit_call)
        self.assertIn("decision_requested", emit_call)

    def test_watchdog_names_operator_understanding_confirmation(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": None,
            "no_idle_state": {
                "status": "input_required",
                "classification": "only_operator_input_blockers_seen",
                "operator_input_required": True,
                "operator_input_task_refs": ["kanban:redacted-blocker"],
                "operator_input_request": {
                    "request_type": "operator_understanding_confirmation",
                    "required_response": "confirm the understanding or send corrections before Product SOT",
                },
                "state": {
                    "todo": {"count": 0},
                    "blocked": {"count": 1},
                    "ready": {"count": 0},
                    "running": {"count": 0},
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                watchdog.main(
                    [
                        "--board",
                        "product-alpha",
                        "--dispatch",
                        "--emit-events",
                        "--state-file",
                        str(Path(tmp) / "state.json"),
                        "--inbox-dir",
                        str(Path(tmp) / "inbox"),
                    ],
                    runner=fake,
                )

        output = buffer.getvalue()
        self.assertIn("aguardando sua confirmação/correção do entendimento", output)
        self.assertFalse(any(len(call) > 2 and call[2] == "dispatch" for call in fake.calls))
        emit_call = next(call for call in fake.calls if len(call) > 2 and call[2] == "emit-event")
        self.assertIn("--requires-user", emit_call)

    def test_human_gate_emits_event_without_dispatch(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": None,
            "no_idle_state": {
                "status": "human_gate_required",
                "classification": "only_human_gate_blockers_seen",
                "human_gate_required": True,
                "state": {"blocked": {"count": 1}},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            with redirect_stdout(io.StringIO()):
                watchdog.main(
                    [
                        "--board",
                        "product-alpha",
                        "--dispatch",
                        "--emit-events",
                        "--state-file",
                        str(Path(tmp) / "state.json"),
                        "--inbox-dir",
                        str(Path(tmp) / "inbox"),
                    ],
                    runner=fake,
                )

        self.assertFalse(any(len(call) > 2 and call[2] == "dispatch" for call in fake.calls))
        emit_call = next(call for call in fake.calls if len(call) > 2 and call[2] == "emit-event")
        self.assertIn("--requires-user", emit_call)
        self.assertIn("human_gate_required", emit_call)


if __name__ == "__main__":
    unittest.main()
