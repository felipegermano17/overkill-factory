from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "adapters" / "hermes" / "kanban_event_bridge.py"
SPEC = importlib.util.spec_from_file_location("kanban_event_bridge", MODULE_PATH)
assert SPEC is not None
kanban_event_bridge = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["kanban_event_bridge"] = kanban_event_bridge
SPEC.loader.exec_module(kanban_event_bridge)


class HermesKanbanEventBridgeTest(unittest.TestCase):
    def test_bridge_routes_task_body_to_transition_hook(self) -> None:
        card_body = (ROOT / "validation" / "cards" / "vfinal-r3-ready.md").read_text(encoding="utf-8")
        payload = {
            "id": "t_public_fixture",
            "title": "OF-VFINAL-BRIDGE-SMOKE",
            "status": "blocked",
            "body": card_body,
            "assignee": "factory-orchestrator",
        }
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            ledger = Path(tmp) / "worker-ledger.json"
            result = kanban_event_bridge.build_from_task_payload(
                payload,
                from_status="blocked",
                to_status="ready",
                ledger_path=ledger,
            )

        worker_ids = {task["worker_id"] for task in result["plan"]["worker_tasks"]}
        self.assertEqual(result["transition_action"], "allow_and_create_worker_tasks")
        self.assertIn("agentic-method-router", worker_ids)
        self.assertIn("security-architect-worker", worker_ids)
        self.assertEqual(result["bridge"]["bridge_type"], "overkill_factory_hermes_kanban_event_bridge")
        self.assertEqual(result["bridge"]["task_id"], "redacted")
        self.assertFalse(result["bridge"]["worker_spawned"])

    def test_bridge_can_keep_private_task_id_when_requested(self) -> None:
        card_body = (ROOT / "validation" / "cards" / "vfinal-r3-ready.md").read_text(encoding="utf-8")
        payload = {
            "id": "t_private_fixture",
            "title": "OF-VFINAL-BRIDGE-SMOKE",
            "status": "blocked",
            "body": card_body,
        }
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            result = kanban_event_bridge.build_from_task_payload(
                payload,
                from_status="blocked",
                to_status="ready",
                ledger_path=Path(tmp) / "worker-ledger.json",
                include_task_id=True,
            )

        self.assertEqual(result["bridge"]["task_id"], "t_private_fixture")

    def test_bridge_rejects_task_without_card_body(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            with self.assertRaises(ValueError):
                kanban_event_bridge.build_from_task_payload(
                    {"id": "t_missing", "body": ""},
                    from_status="blocked",
                    to_status="ready",
                    ledger_path=Path(tmp) / "worker-ledger.json",
                )

    def test_cli_writes_hook_result(self) -> None:
        card_body = (ROOT / "validation" / "cards" / "vfinal-r3-ready.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            task_json = tmp_path / "task.json"
            out = tmp_path / "result.json"
            ledger = tmp_path / "worker-ledger.json"
            task_json.write_text(
                json.dumps({"id": "t_cli_fixture", "title": "fixture", "status": "blocked", "body": card_body}),
                encoding="utf-8",
            )
            result = kanban_event_bridge.build_from_task_payload(
                json.loads(task_json.read_text(encoding="utf-8")),
                from_status="blocked",
                to_status="ready",
                ledger_path=ledger,
            )
            out.write_text(json.dumps(result, indent=2), encoding="utf-8")
            self.assertEqual(
                json.loads(out.read_text(encoding="utf-8"))["transition_action"],
                "allow_and_create_worker_tasks",
            )


if __name__ == "__main__":
    unittest.main()
