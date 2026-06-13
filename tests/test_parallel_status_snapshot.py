from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_factoryctl():
    spec = importlib.util.spec_from_file_location("factoryctl_parallel_status", ROOT / "scripts" / "factoryctl.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["factoryctl_parallel_status"] = module
    spec.loader.exec_module(module)
    return module


factoryctl = load_factoryctl()


def load_minimal_card() -> dict:
    return factoryctl.load_json_like(ROOT / "examples" / "minimal-hermes-project" / "card.md")


def load_lane_template() -> dict:
    return json.loads((ROOT / "templates" / "parallel-lane-contract.json").read_text(encoding="utf-8"))


class ParallelStatusSnapshotTest(unittest.TestCase):
    def test_parallel_execution_request_fails_closed_without_lane_contracts(self) -> None:
        card = load_minimal_card()
        card["parallel_execution_requested"] = True

        errors = factoryctl.validate_card(card)

        self.assertIn("parallel execution requested but parallel_lane_contracts is missing", errors)

    def test_editing_lane_requires_separate_worktree_ref(self) -> None:
        lane = load_lane_template()
        lane["lane_kind"] = "write"
        lane["write_scope"] = ["scripts/factoryctl.py"]
        lane["intended_write_scope"] = ["scripts/factoryctl.py"]
        lane["base_ref"] = "main"
        lane["worktree_ref"] = "main"

        errors = factoryctl.validate_parallel_lane_contract(lane)

        self.assertIn("parallel_lane_contract.worktree_ref must differ from base_ref for editing lanes", errors)

    def test_gate_report_warns_on_overlapping_parallel_write_scope(self) -> None:
        card = load_minimal_card()
        first = load_lane_template()
        first.update(
            {
                "lane_id": "lane-a",
                "lane_kind": "write",
                "write_scope": ["scripts"],
                "intended_write_scope": ["scripts"],
                "worktree_ref": "codex/lane-a",
            }
        )
        second = load_lane_template()
        second.update(
            {
                "lane_id": "lane-b",
                "lane_kind": "write",
                "write_scope": ["scripts"],
                "intended_write_scope": ["scripts"],
                "worktree_ref": "codex/lane-b",
            }
        )
        card["parallel_lane_contracts"] = [first, second]

        report = factoryctl.build_gate_report(card)

        self.assertIn("parallel lane write scope overlap: lane-a and lane-b both write scripts", report["card_validation_warnings"])

    def test_worker_packet_carries_parallel_lane_contracts(self) -> None:
        card = load_minimal_card()
        lane = load_lane_template()
        card["parallel_lane_contracts"] = [lane]

        packet = factoryctl.build_worker_packet("factory-orchestrator", card, ROOT / "examples" / "minimal-hermes-project" / "card.md")

        self.assertEqual(packet["input_contract"]["parallel_lane_contracts"][0]["lane_id"], lane["lane_id"])

    def test_status_snapshot_projects_gate_state_without_becoming_truth(self) -> None:
        card = load_minimal_card()
        lane = load_lane_template()
        card["parallel_lane_contracts"] = [lane]

        snapshot = factoryctl.build_status_snapshot(
            card,
            ROOT / "examples" / "minimal-hermes-project" / "card.md",
            evidence_refs=["external:operator-summary"],
        )

        self.assertEqual(snapshot["record_type"], "factory_status_snapshot")
        self.assertTrue(snapshot["public_private_boundary"]["projection_not_source_of_truth"])
        self.assertTrue(snapshot["source_refs"])
        self.assertEqual(snapshot["lanes"][0]["lane_id"], lane["lane_id"])
        self.assertEqual(factoryctl.validate_status_snapshot(snapshot), [])

    def test_status_snapshot_blocks_contradictory_stale_ready_state(self) -> None:
        snapshot = factoryctl.build_status_snapshot(
            load_minimal_card(),
            ROOT / "examples" / "minimal-hermes-project" / "card.md",
        )
        snapshot["current_state"] = "ready"
        snapshot["staleness"]["status"] = "stale"

        errors = factoryctl.validate_status_snapshot(snapshot)

        self.assertIn("stale snapshot cannot claim ready or released", errors)

    def test_status_snapshot_cli_writes_public_safe_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "snapshot.json"
            rc = factoryctl.main_with_args_for_test(
                [
                    "status-snapshot",
                    "--card",
                    str(ROOT / "examples" / "minimal-hermes-project" / "card.md"),
                    "--lane-contract",
                    str(ROOT / "templates" / "parallel-lane-contract.json"),
                    "--evidence-ref",
                    "external:operator-summary",
                    "--out",
                    str(out),
                ]
            )

            self.assertEqual(rc, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["record_type"], "factory_status_snapshot")
            self.assertEqual(payload["evidence"]["evidence_refs"], ["external:operator-summary"])


if __name__ == "__main__":
    unittest.main()
