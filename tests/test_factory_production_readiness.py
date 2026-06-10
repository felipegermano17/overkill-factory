from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factory_production_readiness.py"
SPEC = importlib.util.spec_from_file_location("factory_production_readiness", MODULE_PATH)
assert SPEC is not None
readiness = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factory_production_readiness"] = readiness
SPEC.loader.exec_module(readiness)


class FactoryProductionReadinessTest(unittest.TestCase):
    def test_blocked_components_make_overall_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pass_path = self._write(tmp_path / "pass.json", "PASS")
            blocked_path = self._write(tmp_path / "blocked.json", "BLOCKED")
            preflight_path = tmp_path / "preflight.json"
            preflight_path.write_text(
                json.dumps({"result": "BLOCKED", "blocking_items": ["operator_control_tower"]}),
                encoding="utf-8",
            )

            receipt = readiness.build_readiness(
                preflight_path=preflight_path,
                control_tower_path=blocked_path,
                control_tower_doctor_path=blocked_path,
                worktree_inventory_path=pass_path,
                release_integration_path=pass_path,
                public_worktree_path=pass_path,
                public_head_path=pass_path,
                public_origin_path=pass_path,
                created_at="2026-06-10T00:00:00Z",
            )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("operator_control_tower_production_readiness", receipt["blocking_items"])
        self.assertIn("preflight:operator_control_tower", receipt["blocking_items"])

    def test_attention_only_keeps_attention_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pass_path = self._write(tmp_path / "pass.json", "PASS")
            attention_path = self._write(tmp_path / "attention.json", "ATTENTION")

            receipt = readiness.build_readiness(
                preflight_path=pass_path,
                control_tower_path=pass_path,
                control_tower_doctor_path=pass_path,
                worktree_inventory_path=attention_path,
                release_integration_path=pass_path,
                public_worktree_path=pass_path,
                public_head_path=pass_path,
                public_origin_path=pass_path,
                created_at="2026-06-10T00:00:00Z",
            )

        self.assertEqual(receipt["result"], "ATTENTION")
        self.assertEqual(receipt["attention_items"], ["worktree_release_inventory"])

    def test_fail_receipt_is_blocked_with_raw_result_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pass_path = self._write(tmp_path / "pass.json", "PASS")
            fail_path = self._write(tmp_path / "fail.json", "FAIL")

            receipt = readiness.build_readiness(
                preflight_path=pass_path,
                control_tower_path=pass_path,
                control_tower_doctor_path=pass_path,
                worktree_inventory_path=pass_path,
                release_integration_path=pass_path,
                public_worktree_path=pass_path,
                public_head_path=fail_path,
                public_origin_path=pass_path,
                created_at="2026-06-10T00:00:00Z",
            )

        head = next(item for item in receipt["components"] if item["id"] == "public_safety_head")
        self.assertEqual(head["status"], "BLOCKED")
        self.assertEqual(head["raw_result"], "FAIL")
        self.assertEqual(head["reason"], "result is FAIL, expected PASS")

    def _write(self, path: Path, result: str) -> Path:
        path.write_text(json.dumps({"result": result}), encoding="utf-8")
        return path


if __name__ == "__main__":
    unittest.main()
