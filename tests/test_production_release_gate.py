from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "production_release_gate.py"
SPEC = importlib.util.spec_from_file_location("production_release_gate", SCRIPT)
assert SPEC is not None
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["production_release_gate"] = module
SPEC.loader.exec_module(module)


class ProductionReleaseGateTest(unittest.TestCase):
    def valid_human_gate(self) -> dict:
        return {
            "record_type": "human_gate_record",
            "gate_type": "release_r4",
            "decision": "approved",
            "decision_at": "2026-06-06T00:00:00+00:00",
            "approval_event_id": "external:maintainer-authorization-event-2026-06-06",
            "human_actor": "project-maintainer",
            "approved_scope": ["public repository release-control lane"],
            "forbidden_scope": ["mainnet write", "wallet signing", "secret disclosure"],
            "risk_owner": "project-maintainer",
            "security_owner": "security-reviewer",
            "rollback_owner": "release-ops-worker",
            "evidence_refs": ["external:maintainer-authorization-event-2026-06-06"],
            "evidence_kind": "real",
            "reusable_for_product": True,
            "product_target": {"product_id": "qvg-public-validation-product"},
            "evidence_provenance": {
                "producer": "human-gate-clerk",
                "captured_at": "2026-06-06T00:00:00+00:00",
                "source_refs": ["external:maintainer-authorization-event-2026-06-06"],
                "artifact_refs": ["external:maintainer-authorization-event-2026-06-06"],
                "integrity": {"approval_event": "external"},
            },
        }

    def test_human_gate_record_must_be_preexisting_real_product_scoped_input(self) -> None:
        gate = self.valid_human_gate()

        self.assertEqual(module.human_gate_errors(gate), [])
        self.assertNotIn("KAXIS", str(gate))

    def test_generated_human_gate_record_is_rejected_for_release(self) -> None:
        gate = self.valid_human_gate()
        gate["approval_event_id"] = "evt_fixture_human_approval"

        errors = module.human_gate_errors(gate)

        self.assertIn("production human gate cannot use generated, fixture, synthetic or placeholder approval evidence", errors)

    def test_release_ops_fails_when_any_validation_command_fails(self) -> None:
        validation = [
            {"command": "ok", "exit_code": 0},
            {"command": "bad", "exit_code": 1},
        ]
        with mock.patch.object(module, "git_value", return_value="git-value"):
            result = module.build_release_ops(created_at="2026-06-06T00:00:00+00:00", validation=validation)

        self.assertEqual(result["result"], "FAIL")
        self.assertFalse(result["reusable_for_product"])

    def test_release_ops_passes_with_validation_and_rollback_plan(self) -> None:
        validation = [{"command": "ok", "exit_code": 0}]
        with mock.patch.object(module, "git_value", return_value="git-value"):
            result = module.build_release_ops(created_at="2026-06-06T00:00:00+00:00", validation=validation)

        self.assertEqual(result["result"], "PASS")
        self.assertTrue(result["reusable_for_product"])
        self.assertIn("git revert", result["rollback_plan"]["rollback_command"])
        self.assertIn("evidence_provenance", result)
        self.assertIn("product_source_sha256", result["evidence_provenance"]["integrity"])
        self.assertIn(".tmp/factory-runs/production/release/upstream-worker-graph.json", result["evidence_refs"])
        self.assertNotIn(".tmp/factory-runs/production/full-product-worker-graph.json", result["evidence_refs"])

    def test_release_gate_uses_production_strict_worker_graph(self) -> None:
        commands = [" ".join(command) for command in module.VALIDATION_COMMANDS]

        self.assertTrue(any("production_full_product_worker_graph.py --release-gate-upstream --require-pass" in command for command in commands))
        self.assertFalse(any("scripts/full_product_worker_graph.py --require-pass" in command for command in commands))

    def test_no_write_release_gate_propagates_to_upstream_graph(self) -> None:
        commands = module.validation_commands(no_write=True)
        graph_commands = [command for command in commands if "scripts/production_full_product_worker_graph.py" in command]

        self.assertEqual(len(graph_commands), 1)
        self.assertIn("--no-write", graph_commands[0])

    def test_cli_requires_human_gate_record_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate_path = Path(tmp) / "human-gate.json"
            gate_path.write_text(json.dumps(self.valid_human_gate()), encoding="utf-8")
            with mock.patch.object(module, "run_command", return_value={"command": "ok", "exit_code": 1}):
                result = module.main(["--human-gate-record", str(gate_path), "--no-write"])

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
