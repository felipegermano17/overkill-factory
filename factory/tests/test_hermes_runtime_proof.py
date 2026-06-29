from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "hermes_runtime_proof.py"
SPEC = importlib.util.spec_from_file_location("hermes_runtime_proof", MODULE_PATH)
assert SPEC is not None
hermes_runtime_proof = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["hermes_runtime_proof"] = hermes_runtime_proof
SPEC.loader.exec_module(hermes_runtime_proof)


class HermesRuntimeProofTest(unittest.TestCase):
    def boards(self) -> list[dict]:
        return [
            {
                "slug": "redacted-current-board",
                "is_current": True,
                "counts": {"done": 2, "blocked": 1},
                "total": 3,
            }
        ]

    def profile_list(self) -> str:
        return """
 Profile          Model                        Gateway      Alias        Distribution
 default          gpt-5.5                      stopped      -            -
 overkill-factory-gerente gpt-5.5              running      -            -
 source-ledger-worker gpt-5.5                  stopped      source-ledger-worker -
 evidence-reconciler gpt-5.5                   stopped      evidence-reconciler -
 human-gate-clerk gpt-5.5                      stopped      human-gate-clerk -
 factory-orchestrator gpt-5.5                  stopped      factory-orchestrator -
"""

    def status_text(self) -> str:
        return """
OpenAI Codex  ✓ logged in
Telegram      ✓ configured
Gateway Service
  Status:       ✓ running
"""

    def task_list(self) -> list[dict]:
        return [
            {"id": "t_1", "status": "done", "assignee": "source-ledger-worker"},
            {"id": "t_2", "status": "done", "assignee": "evidence-reconciler"},
            {"id": "t_3", "status": "blocked", "assignee": "human-gate-clerk"},
        ]

    def done_runs(self) -> list[dict]:
        return [
            {
                "id": 1,
                "profile": "source-ledger-worker",
                "status": "done",
                "outcome": "completed",
                "summary": "Representative worker completed with artifact refs.",
            }
        ]

    def blocked_show(self) -> dict:
        return {
            "task": {"id": "t_3", "status": "blocked", "assignee": "human-gate-clerk"},
            "events": [
                {
                    "kind": "blocked",
                    "payload": {"reason": "Human decision required before gate can move."},
                }
            ],
        }

    def test_builds_public_safe_pass_proof_from_live_shapes(self) -> None:
        proof = hermes_runtime_proof.build_hermes_runtime_proof(
            boards=self.boards(),
            profile_list_text=self.profile_list(),
            status_text=self.status_text(),
            task_list=self.task_list(),
            done_task_runs=self.done_runs(),
            blocked_task_show=self.blocked_show(),
            created_at="2026-06-24T00:00:00Z",
        )

        self.assertEqual(proof["result"], "PASS")
        self.assertTrue(proof["runtime_summary"]["live_worker_orchestration_proven"])
        self.assertTrue(proof["runtime_summary"]["human_gate_block_event_detected"])
        self.assertFalse(proof["operator_gate_boundary"]["human_gate_auto_approved"])
        self.assertEqual([], hermes_runtime_proof.validate_hermes_runtime_proof(proof))

    def test_rejects_runtime_proof_without_real_human_gate_block_event(self) -> None:
        with self.assertRaisesRegex(ValueError, "human-gate blocked event"):
            hermes_runtime_proof.build_hermes_runtime_proof(
                boards=self.boards(),
                profile_list_text=self.profile_list(),
                status_text=self.status_text(),
                task_list=self.task_list(),
                done_task_runs=self.done_runs(),
                blocked_task_show={"task": {"status": "done"}, "events": []},
            )


if __name__ == "__main__":
    unittest.main()
