from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factoryctl.py"
SPEC = importlib.util.spec_from_file_location("factoryctl_incident_replay", MODULE_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl_incident_replay"] = factoryctl
SPEC.loader.exec_module(factoryctl)


def deep_update(target: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_update(target[key], value)
        else:
            target[key] = value
    return target


def materialize_snapshot(spec: dict[str, Any]) -> dict[str, Any]:
    snapshot = copy.deepcopy(spec["snapshot"])
    rows = snapshot.get("rows") if isinstance(snapshot.get("rows"), dict) else {}
    for tasks in rows.values():
        if not isinstance(tasks, list):
            continue
        for task in tasks:
            if not isinstance(task, dict):
                continue
            if task.get("body_template") == "vfinal":
                card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
                deep_update(card, task.pop("body_patch", {}) or {})
                for field in task.pop("body_remove", []) or []:
                    card.pop(str(field), None)
                task.pop("body_template", None)
                task["body"] = json.dumps(card)
            elif isinstance(task.get("body"), dict):
                task["body"] = json.dumps(task["body"])
    return snapshot


class FactoryIncidentReplayTest(unittest.TestCase):
    def test_incident_fixtures_replay_to_expected_reducer_action(self) -> None:
        for path in sorted((ROOT / "fixtures" / "incidents").glob("*.json")):
            spec = json.loads(path.read_text(encoding="utf-8"))
            snapshot = materialize_snapshot(spec)

            with self.subTest(incident=spec["incident_id"]):
                plan = factoryctl.build_board_reconcile_plan(snapshot, board=spec["board"])
                expected = spec["expect"]

                self.assertEqual(factoryctl.validate_board_reconcile_plan(plan), [])
                for key in [
                    "plan_action",
                    "native_dispatch_required_next",
                    "create_task_allowed",
                    "human_gate_required",
                    "user_decision_required",
                ]:
                    self.assertEqual(plan[key], expected[key], key)

                required_output = expected.get("create_task_required_output")
                if required_output:
                    self.assertEqual(
                        plan["create_task_contract"]["body"]["required_output"],
                        required_output,
                    )

                fragments = expected.get("blocked_reason_contains") or []
                if fragments:
                    reason_text = "\n".join(plan["blocked_reasons"] + [plan["reason"]])
                    for fragment in fragments:
                        self.assertIn(fragment, reason_text)


if __name__ == "__main__":
    unittest.main()
