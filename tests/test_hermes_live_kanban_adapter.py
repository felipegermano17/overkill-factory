from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_DIR = ROOT / "adapters" / "hermes"
MODULE_PATH = ADAPTER_DIR / "live_kanban_adapter.py"
FACTORYCTL_PATH = ROOT / "scripts" / "factoryctl.py"
TEST_BOARD = "overkill-" + "factory-live-smoke"
MAIN_TASK_ID = "t_" + "00000001"
READY_TASK_ID = "t_" + "ready0001"
sys.path.insert(0, str(ADAPTER_DIR))
SPEC = importlib.util.spec_from_file_location("live_kanban_adapter", MODULE_PATH)
assert SPEC is not None
adapter = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["live_kanban_adapter"] = adapter
SPEC.loader.exec_module(adapter)
FACTORYCTL_SPEC = importlib.util.spec_from_file_location("factoryctl_live_test", FACTORYCTL_PATH)
assert FACTORYCTL_SPEC is not None
factoryctl = importlib.util.module_from_spec(FACTORYCTL_SPEC)
assert FACTORYCTL_SPEC.loader is not None
sys.modules["factoryctl_live_test"] = factoryctl
FACTORYCTL_SPEC.loader.exec_module(factoryctl)


class FakeHermes:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.counter = 0
        self.tasks: dict[str, dict[str, object]] = {}

    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        if argv == ["hermes", "kanban", "boards", "list", "--json"]:
            return subprocess.CompletedProcess(argv, 0, stdout="[]", stderr="")
        if argv[:4] == ["hermes", "kanban", "boards", "create"]:
            return subprocess.CompletedProcess(argv, 0, stdout="created", stderr="")
        if len(argv) >= 5 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "create":
            self.counter += 1
            task_id = "t_" + f"{self.counter:08x}"
            initial_status = "blocked" if "--initial-status" in argv and "blocked" in argv else "ready"
            self.tasks[task_id] = {"status": initial_status, "events": []}
            return subprocess.CompletedProcess(argv, 0, stdout=f'{{"id":"{task_id}"}}', stderr="")
        if len(argv) == 7 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "block":
            task = self.tasks.setdefault(argv[5], {"status": "ready", "events": []})
            task["status"] = "blocked"
            task.setdefault("events", []).append({"type": "blocked", "reason": argv[6]})
            return subprocess.CompletedProcess(argv, 0, stdout='{"status":"blocked"}', stderr="")
        if len(argv) == 7 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "unblock":
            task = self.tasks.setdefault(argv[5], {"status": "blocked", "events": []})
            task["status"] = "ready"
            task.setdefault("events", []).append({"type": "unblocked", "reason": argv[6]})
            return subprocess.CompletedProcess(argv, 0, stdout='{"status":"ready"}', stderr="")
        if len(argv) >= 5 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "show":
            payload = self.tasks.get(argv[5], {"status": "blocked", "events": [{"type": "blocked", "reason": "gate"}]})
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload), stderr="")
        if len(argv) >= 5 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "link":
            return subprocess.CompletedProcess(argv, 0, stdout="linked", stderr="")
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="unexpected command")


def private_windows_workspace_ref() -> str:
    return "dir:" + "C" + ":" + "\\private-workspace"


class FakeDispatchHermes:
    def __init__(self, *, native_spawned: bool = False) -> None:
        self.calls: list[list[str]] = []
        self.native_spawned = native_spawned
        self.running_list_calls = 0

    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        if len(argv) >= 8 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "list":
            status = argv[argv.index("--status") + 1]
            if status == "ready":
                return subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout=json.dumps(
                        [
                            {
                                "id": READY_TASK_ID,
                                "assignee": "implementation-worker",
                                "workspace": private_windows_workspace_ref(),
                            }
                        ]
                    ),
                    stderr="",
                )
            if status == "running":
                self.running_list_calls += 1
                if self.running_list_calls == 1:
                    return subprocess.CompletedProcess(argv, 0, stdout="[]", stderr="")
                return subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout=json.dumps(
                        [
                            {
                                "id": READY_TASK_ID,
                                "assignee": "implementation-worker",
                                "current_run_id": 42,
                                "worker_pid": 12345,
                                "workspace": private_windows_workspace_ref(),
                            }
                        ]
                    ),
                    stderr="",
                )
        if len(argv) >= 6 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "dispatch":
            spawned = (
                [
                    {
                        "task_id": READY_TASK_ID,
                        "assignee": "implementation-worker",
                        "workspace": private_windows_workspace_ref(),
                    }
                ]
                if self.native_spawned
                else []
            )
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout=json.dumps(
                    {
                        "reclaimed": 0,
                        "crashed": [],
                        "timed_out": [],
                        "stale": [],
                        "auto_blocked": [],
                        "promoted": 0,
                        "spawned": spawned,
                    }
                ),
                stderr="",
            )
        if len(argv) >= 7 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "show":
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout=json.dumps(
                    {
                        "id": argv[5],
                        "status": "running",
                        "assignee": "implementation-worker",
                        "current_run_id": 42,
                        "worker_pid": 12345,
                        "workspace": private_windows_workspace_ref(),
                    }
                ),
                stderr="",
            )
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="unexpected command")


def write_route_readiness(path: Path) -> None:
    workers = [
        "codex-security",
        "solana-quasar-auditor",
        "independent-reviewer",
        "evidence-reconciler",
        "human-gate-clerk",
        "factory-orchestrator",
        "source-ledger-worker",
        "qa-verification-worker",
        "autoreview-gate",
        "security-orchestrator",
        "handoff-packer",
        "supply-chain-gate",
    ]
    path.write_text(
        json.dumps(
            {
                "$schema": "https://overkill-factory.dev/schemas/hermes-worker-route-readiness.schema.json",
                "schema": "overkill_factory_hermes_worker_route_readiness.v1",
                "ledger_ref": "external:test-route-ledger",
                "hermes_home_ref": "redacted-hermes-home",
                "result": "PASS",
                "worker_count": len(workers),
                "blocked_worker_count": 0,
                "blocked_workers": [],
                "checks": [
                    {
                        "worker_id": worker,
                        "task_id": f"route:{worker}",
                        "required_before": "done",
                        "queue_class": "blocking-before-done",
                        "status": "ready",
                        "profile_exists": True,
                        "provider_configured": True,
                        "model_configured": True,
                        "credential_status": "pass",
                        "credential_evidence": ["external:test-credential-evidence"],
                        "blocked_reasons": [],
                    }
                    for worker in workers
                ],
                "production_rule": "Do not dispatch unless every required worker route is ready.",
            }
        ),
        encoding="utf-8",
    )


class HermesLiveKanbanAdapterTest(unittest.TestCase):
    def test_dispatch_reports_tasks_that_entered_running_even_when_native_spawned_is_empty(self) -> None:
        fake = FakeDispatchHermes(native_spawned=False)
        args = adapter.build_parser().parse_args(["dispatch", "--board", TEST_BOARD])

        result = adapter.dispatch(args, runner=fake)

        self.assertEqual(result["mode"], "dispatch")
        self.assertEqual(result["spawned"][0]["task_id"], adapter.PUBLIC_SAFE_KANBAN_REF)
        self.assertEqual(result["spawned"][0]["run_id"], 42)
        self.assertEqual(result["spawned"][0]["worker_pid"], 12345)
        self.assertEqual(result["spawned"][0]["workspace"], "redacted:absolute-hermes-workspace")
        self.assertEqual(
            result["spawned"][0]["dispatch_observation"],
            "already_running_after_native_dispatch",
        )
        self.assertEqual(result["spawned_by_this_command"], [])
        self.assertEqual(len(result["already_running_after_dispatch"]), 1)
        self.assertEqual(result["native_dispatch"]["spawned"], [])
        self.assertTrue(result["hook"]["no_shadow_dispatcher"])
        self.assertFalse(result["hook"]["local_state_authority"])

    def test_dispatch_enriches_native_spawned_with_run_id_and_pid(self) -> None:
        fake = FakeDispatchHermes(native_spawned=True)
        args = adapter.build_parser().parse_args(["dispatch", "--board", TEST_BOARD])

        result = adapter.dispatch(args, runner=fake)

        self.assertEqual(len(result["spawned_by_this_command"]), 1)
        spawned = result["spawned_by_this_command"][0]
        self.assertEqual(spawned["task_id"], adapter.PUBLIC_SAFE_KANBAN_REF)
        self.assertEqual(spawned["run_id"], 42)
        self.assertEqual(spawned["worker_pid"], 12345)
        self.assertEqual(spawned["dispatch_observation"], "native_dispatch_spawned")
        self.assertEqual(spawned["workspace"], "redacted:absolute-hermes-workspace")
        self.assertEqual(result["already_running_after_dispatch"], [])

    def test_materialize_creates_workers_as_parents_of_main_card(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        with tempfile.TemporaryDirectory() as tmp:
            readiness = Path(tmp) / "route-readiness.json"
            write_route_readiness(readiness)
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(Path(tmp) / "ledger.json"),
                    "--route-readiness",
                    str(readiness),
                    "--ensure-board",
                    "--worker-ready",
                ]
            )
            result = adapter.materialize(args, runner=fake)
            ledger_data = json.loads((Path(tmp) / "ledger.json").read_text(encoding="utf-8"))

        self.assertEqual(result["main_task_id"], adapter.PUBLIC_SAFE_KANBAN_REF)
        self.assertIn("codex-security", result["worker_task_ids"])
        self.assertEqual(result["worker_task_ids"]["codex-security"], adapter.PUBLIC_SAFE_KANBAN_REF)
        binding = ledger_data["live_bindings"]["KFP-V35-POS-ONCHAIN-AUDITOR"]
        self.assertEqual(binding["binding_role"], "hermes_ref_projection")
        self.assertEqual(binding["runtime_authority"], "hermes_kanban")
        self.assertFalse(binding["local_state_authority"])
        materialized_tasks = [
            task for task in ledger_data["tasks"].values()
            if task["worker_id"] == "codex-security" and task["materialization_state"] == "materialized_in_hermes"
        ]
        self.assertEqual(len(materialized_tasks), 1)
        self.assertEqual(materialized_tasks[0]["runtime_refs"]["hermes_board_ref"], f"hermes:{TEST_BOARD}")
        self.assertTrue(materialized_tasks[0]["runtime_refs"]["hermes_task_ref"].startswith("t_"))
        link_calls = [call for call in fake.calls if len(call) >= 7 and call[4] == "link"]
        self.assertTrue(link_calls)
        for call in link_calls:
            self.assertEqual(call[-1], MAIN_TASK_ID)
            self.assertNotEqual(call[-2], MAIN_TASK_ID)

    def test_materialize_promotes_only_authorized_review_child(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card_data = factoryctl.load_json_like(card)
        handoff = factoryctl.build_worker_result(
            "handoff-packer",
            card_data,
            result="PASS",
            tool_or_profile="handoff-pack-smoke",
            executed_by="handoff-packer",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Handoff packet declares an independent review gate.",
            next_action="continue after review",
            reviewer_required=True,
            reviewer_result="PENDING",
        )
        receipt_payload = {
            "handoff_packet_result": handoff,
            "orchestration_result": factoryctl.build_worker_result(
                "factory-orchestrator",
                card_data,
                result="PASS",
                tool_or_profile="orchestration-smoke",
                executed_by="factory-orchestrator",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Orchestration precondition passed.",
                next_action="continue",
            ),
            "source_ledger_result": factoryctl.build_worker_result(
                "source-ledger-worker",
                card_data,
                result="PASS",
                tool_or_profile="source-ledger-smoke",
                executed_by="source-ledger-worker",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Source ledger precondition passed.",
                next_action="continue",
            ),
            "security_orchestration_result": factoryctl.build_worker_result(
                "security-orchestrator",
                card_data,
                result="PASS",
                tool_or_profile="security-orchestration-smoke",
                executed_by="security-orchestrator",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Security orchestration precondition passed.",
                next_action="continue",
            ),
            "supply_chain_result": factoryctl.build_worker_result(
                "supply-chain-gate",
                card_data,
                result="PASS",
                tool_or_profile="supply-chain-smoke",
                executed_by="supply-chain-gate",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Supply chain precondition passed.",
                next_action="continue",
            ),
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            readiness = tmp_path / "route-readiness.json"
            receipt = tmp_path / "receipt.json"
            ledger = tmp_path / "ledger.json"
            write_route_readiness(readiness)
            receipt.write_text(json.dumps(receipt_payload), encoding="utf-8")
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(ledger),
                    "--receipt",
                    str(receipt),
                    "--from-status",
                    "doing",
                    "--to-status",
                    "implementation-ready-for-review",
                    "--route-readiness",
                    str(readiness),
                ]
            )
            result = adapter.materialize(args, runner=fake)
            ledger_data = json.loads(ledger.read_text(encoding="utf-8"))

        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        review_tasks = [
            task for task in ledger_data["tasks"].values()
            if task["worker_id"] == "independent-reviewer" and task["materialization_state"] == "materialized_in_hermes"
        ]
        self.assertEqual(len(review_tasks), 1)
        review_task_id = review_tasks[0]["runtime_refs"]["hermes_task_ref"]
        self.assertEqual(len(unblock_calls), 1)
        self.assertEqual(unblock_calls[0][5], review_task_id)
        self.assertEqual(result["worker_task_ids"]["independent-reviewer"], adapter.PUBLIC_SAFE_KANBAN_REF)
        self.assertEqual(
            result["review_promoted_worker_task_ids"],
            {"independent-reviewer": adapter.PUBLIC_SAFE_KANBAN_REF},
        )
        self.assertNotIn("handoff-packer", result["review_promoted_worker_task_ids"])

    def test_materialize_promotes_factory_owned_recovery_repair_task(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card_data = factoryctl.load_json_like(card)
        handoff = factoryctl.build_worker_result(
            "handoff-packer",
            card_data,
            result="PASS",
            tool_or_profile="handoff-pack-smoke",
            executed_by="handoff-packer",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Handoff packet declares an independent review gate.",
            next_action="continue after review",
            reviewer_required=True,
            reviewer_result="PENDING",
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            readiness = tmp_path / "route-readiness.json"
            worker_results = tmp_path / "worker-results"
            worker_results.mkdir()
            ledger = tmp_path / "ledger.json"
            handoff_path = worker_results / "handoff.json"
            review_path = worker_results / "review.json"
            write_route_readiness(readiness)
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            requirement = factoryctl.declared_graph_requirements(
                "handoff_packet_result",
                handoff,
                evidence_ref=factoryctl.source_card_ref(handoff_path),
            )[0]
            blocked_review = factoryctl.build_worker_result(
                "independent-reviewer",
                card_data,
                result="BLOCKED",
                tool_or_profile="independent-review-smoke",
                executed_by="independent-reviewer",
                evidence_refs=["README.md"],
                blocking_findings=True,
                findings_summary="Review found the handoff packet incomplete.",
                next_action="repair handoff packet and rerun independent review",
                reusable_for_product=False,
            )
            blocked_review["graph_requirement_refs"] = [requirement["requirement_id"]]
            review_path.write_text(json.dumps(blocked_review), encoding="utf-8")
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(ledger),
                    "--worker-results-dir",
                    str(worker_results),
                    "--route-readiness",
                    str(readiness),
                ]
            )
            result = adapter.materialize(args, runner=fake)
            ledger_data = json.loads(ledger.read_text(encoding="utf-8"))

        self.assertEqual(result["recovery_promoted_worker_task_ids"], {"handoff-packer": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(result["review_promoted_worker_task_ids"], {"independent-reviewer": adapter.PUBLIC_SAFE_KANBAN_REF})
        handoff_task = next(task for task in ledger_data["tasks"].values() if task["worker_id"] == "handoff-packer")
        handoff_task_id = handoff_task["runtime_refs"]["hermes_task_ref"]
        self.assertTrue(handoff_task["recovery_route_refs"])
        self.assertEqual(fake.tasks[handoff_task_id]["status"], "ready")
        self.assertEqual(fake.tasks[MAIN_TASK_ID]["status"], "blocked")
        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertTrue(any(call[5] == handoff_task_id and "downstream remains gated" in call[6] for call in unblock_calls))

    def test_materialize_dry_run_does_not_call_hermes_create(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_product_face.md"
        with tempfile.TemporaryDirectory() as tmp:
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(Path(tmp) / "ledger.json"),
                    "--dry-run",
                ]
            )
            result = adapter.materialize(args, runner=fake)

        self.assertTrue(result["dry_run"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))

    def test_materialize_dry_run_with_ensure_board_does_not_touch_hermes(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_product_face.md"
        with tempfile.TemporaryDirectory() as tmp:
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(Path(tmp) / "ledger.json"),
                    "--dry-run",
                    "--ensure-board",
                ]
            )
            result = adapter.materialize(args, runner=fake)

        self.assertTrue(result["dry_run"])
        self.assertTrue(result["board_create_requested"])
        self.assertFalse(result["board_create_checked"])
        self.assertEqual(fake.calls, [])

    def test_block_command_matches_real_hermes_cli_shape(self) -> None:
        fake = FakeHermes()

        adapter.ensure_blocked_event(
            hermes_bin="hermes",
            board=TEST_BOARD,
            task_id=MAIN_TASK_ID,
            reason="gate",
            runner=fake,
        )

        self.assertEqual(
            fake.calls[0],
            ["hermes", "kanban", "--board", TEST_BOARD, "block", MAIN_TASK_ID, "gate"],
        )
        self.assertNotIn("--reason", fake.calls[0])
        self.assertNotIn("--json", fake.calls[0])

    def test_complete_main_requires_materialized_live_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.json"
            ledger.write_text(
                json.dumps(
                    {
                        "ledger_type": "overkill_factory_hermes_worker_ledger",
                        "ledger_scope": "projection_idempotency_only",
                        "runtime_authority": "hermes_kanban",
                        "local_state_authority": False,
                        "tasks": {},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "missing live binding"):
                adapter.validate_live_binding(
                    ledger_path=ledger,
                    card_id="CARD-001",
                    board=TEST_BOARD,
                    main_task_id="fixture-main-task",
                )

    def test_complete_main_rejects_local_authority_live_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.json"
            ledger.write_text(
                json.dumps(
                    {
                        "ledger_type": "overkill_factory_hermes_worker_ledger",
                        "ledger_scope": "projection_idempotency_only",
                        "runtime_authority": "hermes_kanban",
                        "local_state_authority": False,
                        "tasks": {},
                        "live_bindings": {
                            "CARD-001": {
                                "binding_role": "local_state",
                                "runtime_authority": "local-file",
                                "local_state_authority": True,
                                "board": TEST_BOARD,
                                "main_task_id": "fixture-main-task",
                                "worker_task_ids": {},
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "not a Hermes-authoritative projection"):
                adapter.validate_live_binding(
                    ledger_path=ledger,
                    card_id="CARD-001",
                    board=TEST_BOARD,
                    main_task_id="fixture-main-task",
                )


if __name__ == "__main__":
    unittest.main()
