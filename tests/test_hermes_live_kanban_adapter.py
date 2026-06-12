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
TEST_BOARD = "overkill-" + "factory-live-smoke"
MAIN_TASK_ID = "t_" + "00000001"
sys.path.insert(0, str(ADAPTER_DIR))
SPEC = importlib.util.spec_from_file_location("live_kanban_adapter", MODULE_PATH)
assert SPEC is not None
adapter = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["live_kanban_adapter"] = adapter
SPEC.loader.exec_module(adapter)


class FakeHermes:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.counter = 0

    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        if argv[:4] == ["hermes", "kanban", "boards", "list"]:
            return subprocess.CompletedProcess(argv, 0, stdout="[]", stderr="")
        if argv[:4] == ["hermes", "kanban", "boards", "create"]:
            return subprocess.CompletedProcess(argv, 0, stdout="created", stderr="")
        if len(argv) >= 5 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "create":
            self.counter += 1
            task_id = "t_" + f"{self.counter:08x}"
            return subprocess.CompletedProcess(argv, 0, stdout=f'{{"id":"{task_id}"}}', stderr="")
        if len(argv) >= 5 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "link":
            return subprocess.CompletedProcess(argv, 0, stdout="linked", stderr="")
        if len(argv) >= 5 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "block":
            return subprocess.CompletedProcess(argv, 0, stdout="blocked", stderr="")
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="unexpected command")


class HermesLiveKanbanAdapterTest(unittest.TestCase):
    def test_materialize_creates_workers_as_parents_of_main_card(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
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
                    "--ensure-board",
                    "--worker-ready",
                ]
            )
            result = adapter.materialize(args, runner=fake)

        self.assertEqual(result["main_task_id"], MAIN_TASK_ID)
        self.assertIn("codex-security", result["worker_task_ids"])
        block_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "block"]
        self.assertTrue(block_calls)
        link_calls = [call for call in fake.calls if len(call) >= 7 and call[4] == "link"]
        self.assertTrue(link_calls)
        for call in link_calls:
            self.assertEqual(call[-1], MAIN_TASK_ID)
            self.assertNotEqual(call[-2], MAIN_TASK_ID)

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
                    "--ensure-board",
                    "--dry-run",
                ]
            )
            result = adapter.materialize(args, runner=fake)

        self.assertTrue(result["dry_run"])
        self.assertTrue(result["board_created"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))

    def test_materialize_uses_card_workspace_by_default(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "product-workspace"
            cards = workspace / "cards"
            cards.mkdir(parents=True)
            source_card = ROOT / "examples" / "minimal-hermes-project" / "card.md"
            card = cards / "card.md"
            card.write_text(source_card.read_text(encoding="utf-8"), encoding="utf-8")
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(Path(tmp) / "ledger.json"),
                    "--worker-ready",
                ]
            )
            result = adapter.materialize(args, runner=fake)

        self.assertEqual(result["workspace"], str(workspace))
        create_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "create"]
        self.assertTrue(create_calls)
        self.assertTrue(any(f"dir:{workspace}" in call for call in create_calls))

    def test_materialize_links_before_done_workers_to_before_ready_parents(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "minimal-hermes-project" / "card.md"
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
                    "--worker-ready",
                ]
            )
            result = adapter.materialize(args, runner=fake)

        self.assertIn("evidence-reconciler", result["worker_task_ids"])
        evidence_id = result["worker_task_ids"]["evidence-reconciler"]
        create_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "create"]
        evidence_create = next(call for call in create_calls if f'"id": "evidence-reconciler"' in " ".join(call))
        parent_args = [
            evidence_create[index + 1]
            for index, value in enumerate(evidence_create)
            if value == "--parent" and index + 1 < len(evidence_create)
        ]
        self.assertTrue(parent_args)
        self.assertNotIn(MAIN_TASK_ID, parent_args)
        self.assertNotIn(evidence_id, parent_args)

    def test_complete_main_requires_materialized_live_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.json"
            ledger.write_text(json.dumps({"tasks": {}}), encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "missing live binding"):
                adapter.validate_live_binding(
                    ledger_path=ledger,
                    card_id="CARD-001",
                    board=TEST_BOARD,
                    main_task_id="t_" + "deadbeef",
                )


if __name__ == "__main__":
    unittest.main()
