from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_hermes_live_smoke.py"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_hermes_live_smoke", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryHermesLiveSmokeTest(unittest.TestCase):
    def test_validate_smoke_accepts_live_kanban_event_sequence(self) -> None:
        module = load_module()
        blocked = {
            "task": {"status": "blocked"},
            "events": [{"kind": "created"}, {"kind": "blocked"}],
            "runs": [{"status": "blocked", "outcome": "blocked"}],
        }
        done = {
            "task": {"status": "done", "workspace_path": "/private/path"},
            "events": [
                {"kind": "created"},
                {"kind": "commented"},
                {"kind": "blocked"},
                {"kind": "unblocked"},
                {"kind": "completed"},
            ],
            "comments": [{"body": "Receipt Five readback"}],
            "runs": [
                {"status": "completed", "outcome": "completed", "metadata": {"receipt_five": "present", "runtime": "hermes_kanban"}}
            ],
        }
        self.assertEqual(module.validate_smoke(blocked, done), [])
        sanitized = module.sanitize_show_payload(done)
        self.assertEqual(sanitized["task"]["workspace_path"], "redacted:hermes-workspace")

    def test_validate_smoke_blocks_missing_receipt_metadata(self) -> None:
        module = load_module()
        blocked = {"task": {"status": "blocked"}, "events": [{"kind": "blocked"}], "runs": []}
        done = {"task": {"status": "done"}, "events": [{"kind": "created"}, {"kind": "commented"}, {"kind": "blocked"}, {"kind": "unblocked"}, {"kind": "completed"}], "runs": []}
        errors = module.validate_smoke(blocked, done)
        self.assertIn("missing Receipt Five runtime metadata on completed run", errors)


if __name__ == "__main__":
    unittest.main()
