from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_DIR = ROOT / "adapters" / "hermes"
MODULE_PATH = ADAPTER_DIR / "live_kanban_adapter.py"
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
            return subprocess.CompletedProcess(argv, 0, stdout=f'{{"id":"t_{self.counter:08x}"}}', stderr="")
        if len(argv) >= 5 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "link":
            return subprocess.CompletedProcess(argv, 0, stdout="linked", stderr="")
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="unexpected command")


class HermesLiveKanbanAdapterTest(unittest.TestCase):
    def test_materialize_creates_workers_as_parents_of_main_card(self) -> None:
        fake = FakeHermes()
        card = ROOT / "validation" / "cards" / "solana-quasar-r3.md"
        with tempfile.TemporaryDirectory() as tmp:
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    "overkill-factory-live-smoke",
                    "--ledger",
                    str(Path(tmp) / "ledger.json"),
                    "--ensure-board",
                    "--worker-ready",
                ]
            )
            result = adapter.materialize(args, runner=fake)

        self.assertEqual(result["main_task_id"], "t_00000001")
        self.assertIn("codex-security", result["worker_task_ids"])
        link_calls = [call for call in fake.calls if len(call) >= 7 and call[4] == "link"]
        self.assertTrue(link_calls)
        for call in link_calls:
            self.assertEqual(call[-1], "t_00000001")
            self.assertNotEqual(call[-2], "t_00000001")

    def test_materialize_dry_run_does_not_call_hermes_create(self) -> None:
        fake = FakeHermes()
        card = ROOT / "validation" / "cards" / "product-face-saas-r2.md"
        with tempfile.TemporaryDirectory() as tmp:
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    "overkill-factory-live-smoke",
                    "--ledger",
                    str(Path(tmp) / "ledger.json"),
                    "--dry-run",
                ]
            )
            result = adapter.materialize(args, runner=fake)

        self.assertTrue(result["dry_run"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))


if __name__ == "__main__":
    unittest.main()
