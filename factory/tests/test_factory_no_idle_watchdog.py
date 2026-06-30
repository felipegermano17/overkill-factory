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

    def test_all_nonempty_boards_is_audit_only_even_when_mutation_flags_are_requested(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": None,
            "no_idle_state": {
                "status": "remediation_required",
                "classification": "unfinished_work_without_ready_running_or_human_gate_only_block",
                "native_dispatch_required_next": True,
                "state": {"todo": {"count": 3}, "blocked": {"count": 2}},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.json"
            with redirect_stdout(io.StringIO()):
                result = watchdog.main(
                    [
                        "--all-nonempty-boards",
                        "--create-remediation",
                        "--dispatch",
                        "--state-file",
                        str(state_file),
                    ],
                    runner=fake,
                )

            state = json.loads(state_file.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        no_idle_call = next(call for call in fake.calls if len(call) > 2 and call[2] == "no-idle")
        self.assertNotIn("--create-remediation", no_idle_call)
        self.assertFalse(any(len(call) > 2 and call[2] == "dispatch" for call in fake.calls))
        self.assertTrue(state["boards"]["product-alpha"]["mutation_suppressed"])

    def test_all_nonempty_board_mutation_requires_explicit_allow_flag(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": "kanban:redacted",
            "no_idle_state": {
                "status": "remediation_required",
                "classification": "unfinished_work_without_ready_running_or_human_gate_only_block",
                "native_dispatch_required_next": True,
                "state": {"todo": {"count": 3}, "blocked": {"count": 2}},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            with redirect_stdout(io.StringIO()):
                result = watchdog.main(
                    [
                        "--all-nonempty-boards",
                        "--create-remediation",
                        "--dispatch",
                        "--allow-discovered-board-mutation",
                        "--state-file",
                        str(Path(tmp) / "state.json"),
                    ],
                    runner=fake,
                )

        self.assertEqual(result, 0)
        no_idle_call = next(call for call in fake.calls if len(call) > 2 and call[2] == "no-idle")
        dispatch_call = next(call for call in fake.calls if len(call) > 2 and call[2] == "dispatch")
        self.assertIn("--create-remediation", no_idle_call)
        self.assertEqual(dispatch_call[2], "dispatch")

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

    def test_watchdog_names_review_repair_and_calls_native_dispatch(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": "kanban:redacted",
            "no_idle_state": {
                "status": "remediation_required",
                "classification": "deterministic_targeted_review_repair_task_created",
                "remediation_strategy": "create_targeted_review_repair_task",
                "remediation_task_created": True,
                "remediation_task_status": "ready",
                "review_repair_task_refs": ["kanban:redacted-review"],
                "native_dispatch_required_next": True,
                "state": {
                    "todo": {"count": 0},
                    "blocked": {"count": 1},
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
        self.assertIn("review interno bloqueou", buffer.getvalue())
        dispatch_call = next(call for call in fake.calls if len(call) > 2 and call[2] == "dispatch")
        self.assertEqual(dispatch_call[2], "dispatch")

    def test_watchdog_names_post_review_owner_gate_package_and_dispatches(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": "kanban:redacted",
            "no_idle_state": {
                "status": "remediation_required",
                "classification": "deterministic_post_review_owner_gate_package_task_created",
                "remediation_strategy": "create_post_review_owner_gate_package_task",
                "remediation_task_created": True,
                "remediation_task_status": "ready",
                "post_review_task_refs": ["kanban:redacted-review"],
                "native_dispatch_required_next": True,
                "state": {
                    "todo": {"count": 0},
                    "blocked": {"count": 1},
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
        self.assertIn("review PASS exige pacote de decisão Product SOT", buffer.getvalue())
        dispatch_call = next(call for call in fake.calls if len(call) > 2 and call[2] == "dispatch")
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

    def test_watchdog_does_not_call_stale_remediation_id_created(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": "kanban:redacted-stale",
            "no_idle_state": {
                "status": "remediation_required",
                "classification": "repair_board_contract",
                "remediation_task_stale": True,
                "remediation_task_status": "done",
                "native_dispatch_required_next": False,
                "state": {
                    "todo": {"count": 3},
                    "blocked": {"count": 1},
                    "ready": {"count": 0},
                    "running": {"count": 0},
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                result = watchdog.main(
                    [
                        "--board",
                        "product-alpha",
                        "--dispatch",
                        "--state-file",
                        str(Path(tmp) / "state.json"),
                    ],
                    runner=fake,
                )

        output = buffer.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("já está concluída e não destravou", output)
        self.assertNotIn("remediação segura criada", output)
        self.assertFalse(any(len(call) > 2 and call[2] == "dispatch" for call in fake.calls))

    def test_watchdog_alerts_after_repeated_unchanged_no_progress_signature(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": None,
            "no_idle_state": {
                "status": "remediation_required",
                "classification": "unfinished_work_without_ready_running_or_human_gate_only_block",
                "native_dispatch_required_next": True,
                "state": {
                    "todo": {"count": 3},
                    "blocked": {"count": 1},
                    "ready": {"count": 0},
                    "running": {"count": 0},
                },
            },
        }
        fake.dispatch_payloads["product-alpha"] = {
            "mode": "dispatch",
            "board": "product-alpha",
            "spawned": [],
            "dispatch_observed_state": {
                "ready_before_count": 0,
                "running_before_count": 0,
                "running_after_count": 0,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.json"
            first = io.StringIO()
            second = io.StringIO()
            with redirect_stdout(first):
                watchdog.main(
                    [
                        "--board",
                        "product-alpha",
                        "--dispatch",
                        "--state-file",
                        str(state_file),
                        "--max-unchanged-no-progress",
                        "2",
                    ],
                    runner=fake,
                )
            with redirect_stdout(second):
                watchdog.main(
                    [
                        "--board",
                        "product-alpha",
                        "--dispatch",
                        "--state-file",
                        str(state_file),
                        "--max-unchanged-no-progress",
                        "2",
                    ],
                    runner=fake,
                )
            self.assertIn("no-idle detectado", first.getvalue())
            self.assertIn("sem progresso material repetido", second.getvalue())
            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(state["board_watch"]["product-alpha"]["unchanged_no_progress_count"], 2)

    def test_watchdog_alerts_repeated_phase_invariant_even_with_running_worker(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": None,
            "no_idle_state": {
                "status": "blocked",
                "classification": "factory_phase_invariant_violation",
                "human_gate_required": False,
                "operator_input_required": False,
                "native_dispatch_required_next": False,
                "state": {
                    "todo": {"count": 2},
                    "blocked": {"count": 1},
                    "ready": {"count": 0},
                    "running": {"count": 1},
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.json"
            first = io.StringIO()
            second = io.StringIO()
            with redirect_stdout(first):
                watchdog.main(
                    [
                        "--board",
                        "product-alpha",
                        "--state-file",
                        str(state_file),
                        "--max-unchanged-no-progress",
                        "2",
                    ],
                    runner=fake,
                )
            with redirect_stdout(second):
                watchdog.main(
                    [
                        "--board",
                        "product-alpha",
                        "--state-file",
                        str(state_file),
                        "--max-unchanged-no-progress",
                        "2",
                    ],
                    runner=fake,
                )
            self.assertIn("estado blocked", first.getvalue())
            self.assertIn("sem progresso material repetido", second.getvalue())
            self.assertIn("running=1", second.getvalue())

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

    def test_watchdog_native_dependency_wait_emits_dependency_event_without_user(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": None,
            "no_idle_state": {
                "status": "dependency_gated",
                "classification": "hermes_native_dependency_wait",
                "typed_block_kind": "dependency",
                "hermes_native_dependency_wait": True,
                "dependency_gated_task_refs": {"kanban:redacted-child": ["kanban:redacted-parent"]},
                "state": {
                    "todo": {"count": 1},
                    "blocked": {"count": 0},
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
                        "--emit-events",
                        "--state-file",
                        str(Path(tmp) / "state.json"),
                        "--inbox-dir",
                        str(Path(tmp) / "inbox"),
                    ],
                    runner=fake,
                )

        self.assertIn("aguardando dependência nativa do Hermes", buffer.getvalue())
        emit_call = next(call for call in fake.calls if len(call) > 2 and call[2] == "emit-event")
        self.assertIn("dependency_wait", emit_call)
        self.assertNotIn("--requires-user", emit_call)

    def test_watchdog_block_loop_detected_emits_triage_event_without_user(self) -> None:
        fake = FakeRunner()
        fake.no_idle_payloads["product-alpha"] = {
            "mode": "no-idle",
            "board": "product-alpha",
            "remediation_task_id": None,
            "no_idle_state": {
                "status": "remediation_required",
                "classification": "hermes_typed_block_loop_detected",
                "typed_block_kind": "transient",
                "block_loop_detected": True,
                "block_loop_task_refs": ["kanban:redacted-loop"],
                "state": {"blocked": {"count": 0}, "todo": {"count": 0}, "triage": {"count": 1}},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                watchdog.main(
                    [
                        "--board",
                        "product-alpha",
                        "--emit-events",
                        "--state-file",
                        str(Path(tmp) / "state.json"),
                        "--inbox-dir",
                        str(Path(tmp) / "inbox"),
                    ],
                    runner=fake,
                )

        self.assertIn("loop de bloqueio", buffer.getvalue())
        self.assertIn("triage=1", buffer.getvalue())
        emit_call = next(call for call in fake.calls if len(call) > 2 and call[2] == "emit-event")
        self.assertIn("block_loop_detected", emit_call)
        self.assertNotIn("--requires-user", emit_call)

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
        payload = json.loads(emit_call[emit_call.index("--payload-json") + 1])
        self.assertEqual(payload["signature"]["operator_input_task_refs"], ["kanban:redacted-blocker"])
        self.assertTrue(payload["requires_user"])

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
        payload = json.loads(emit_call[emit_call.index("--payload-json") + 1])
        self.assertEqual(payload["signature"]["operator_input_request"]["request_type"], "operator_understanding_confirmation")

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
                "human_gate_task_refs": ["kanban:redacted-gate"],
                "human_decision_request": {
                    "request_type": "factory_human_gate_decision",
                    "required_response": "approve, reject or request changes",
                },
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
        payload = json.loads(emit_call[emit_call.index("--payload-json") + 1])
        self.assertEqual(payload["signature"]["human_gate_task_refs"], ["kanban:redacted-gate"])
        self.assertEqual(payload["signature"]["human_decision_request"]["request_type"], "factory_human_gate_decision")


if __name__ == "__main__":
    unittest.main()
