from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_production_gate_receipts.py"
VALIDATOR_PATH = ROOT / "scripts" / "validate_public_json_artifacts.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryProductionGateReceiptsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.receipts = load_module("factory_production_gate_receipts", SCRIPT_PATH)
        self.validator = load_module("validate_public_json_artifacts_for_gate_receipts", VALIDATOR_PATH)
        self.schemas = self.validator.load_schemas()

    def assert_schema_valid(self, payload: dict) -> None:
        schema_name = self.validator.schema_name(payload["$schema"])
        schema = self.schemas[schema_name]
        errors = self.validator.validate_node(schema, payload, "$", schemas=self.schemas, root_schema=schema)
        self.assertEqual(errors, [])

    def test_runtime_status_fails_closed_without_live_hermes_evidence(self) -> None:
        payload = self.receipts.build_runtime_status(created_at="2026-06-19T00:00:00Z")

        self.assertEqual(payload["result"], "BLOCKED")
        self.assertFalse(payload["checks"]["hermes_status_readonly_passed"])
        self.assertFalse(payload["checks"]["profile_list_readonly_passed"])
        self.assertTrue(payload["checks"]["raw_private_values_omitted"])
        self.assert_schema_valid(payload)

    def test_runtime_status_passes_with_public_safe_live_hermes_evidence(self) -> None:
        payload = self.receipts.build_runtime_status(
            created_at="2026-06-19T00:00:00Z",
            live_evidence=self._runtime_evidence(),
        )

        self.assertEqual(payload["result"], "PASS")
        self.assertTrue(all(payload["checks"].values()))
        self.assertIn(".tmp/factory-runs/hermes-live/hermes-runtime-readonly-evidence.json", payload["evidence_refs"])
        self.assert_schema_valid(payload)

    def test_runtime_status_blocks_private_looking_live_evidence(self) -> None:
        payload = self.receipts.build_runtime_status(
            created_at="2026-06-19T00:00:00Z",
            live_evidence={
                **self._runtime_evidence(),
                "raw_note": "token should never be copied into public receipts",
            },
        )

        self.assertEqual(payload["result"], "BLOCKED")
        self.assertFalse(payload["checks"]["raw_private_values_omitted"])
        self.assert_schema_valid(payload)

    def test_update_preflight_blocks_missing_required_proofs(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            paths = self.receipts.GatePaths(
                runtime_status=tmp_path / "runtime.json",
                control_tower_doctor=tmp_path / "doctor.json",
                control_tower=tmp_path / "tower.json",
                release_preflight=tmp_path / "release.json",
            )
            payload = self.receipts.build_update_preflight(paths, created_at="2026-06-19T00:00:00Z")

        self.assertEqual(payload["result"], "BLOCKED")
        self.assertEqual({proof["status"] for proof in payload["required_proofs"]}, {"BLOCKED"})
        self.assertEqual(payload["decision"]["real_runtime_update"], "blocked")
        self.assert_schema_valid(payload)

    def test_prepilot_master_tracks_nine_tasks_and_blocks_runtime_gaps(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            paths = self.receipts.GatePaths(
                prepilot_master=tmp_path / "prepilot.json",
                runtime_status=tmp_path / "runtime.json",
                update_preflight=tmp_path / "update.json",
                control_tower=tmp_path / "tower.json",
                control_tower_doctor=tmp_path / "doctor.json",
                release_preflight=tmp_path / "release.json",
                public_safety_worktree=tmp_path / "worktree.json",
                public_safety_head=tmp_path / "head.json",
                public_safety_origin=tmp_path / "origin.json",
            )
            payload = self.receipts.build_prepilot_master(paths, created_at="2026-06-19T00:00:00Z")

        self.assertEqual(payload["result"], "BLOCKED")
        self.assertEqual(payload["readiness_level"], "BLOCKED")
        self.assertEqual(len(payload["tasks"]), 9)
        by_id = {task["task_id"]: task for task in payload["tasks"]}
        self.assertEqual(by_id["hermes-runtime-status"]["status"], "BLOCKED")
        self.assertEqual(by_id["operator-control-tower-proof"]["status"], "BLOCKED")
        self.assert_schema_valid(payload)

    def test_materialization_success_is_not_production_approval(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            paths = self.receipts.GatePaths(
                prepilot_master=tmp_path / "prepilot.json",
                runtime_status=tmp_path / "runtime.json",
                update_preflight=tmp_path / "update.json",
                control_tower=tmp_path / "tower.json",
                control_tower_doctor=tmp_path / "doctor.json",
                release_preflight=tmp_path / "release.json",
            )
            summary = self.receipts.materialize(paths, no_write=True)

        self.assertEqual(summary["result"], "PASS")
        self.assertTrue(any("not that production gates passed" in limit for limit in summary["limits"]))
        self.assertIn("BLOCKED", {receipt["result"] for receipt in summary["receipts"]})

    def test_materialization_can_use_runtime_evidence_path(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            evidence_path = tmp_path / "runtime-evidence.json"
            evidence_path.write_text(json.dumps(self._runtime_evidence()), encoding="utf-8")
            paths = self.receipts.GatePaths(
                prepilot_master=tmp_path / "prepilot.json",
                runtime_status=tmp_path / "runtime.json",
                update_preflight=tmp_path / "update.json",
                control_tower=tmp_path / "tower.json",
                control_tower_doctor=tmp_path / "doctor.json",
                release_preflight=tmp_path / "release.json",
            )
            summary = self.receipts.materialize(
                paths,
                no_write=False,
                runtime_status_evidence=evidence_path,
            )

            runtime = json.loads(paths.runtime_status.read_text(encoding="utf-8"))

        self.assertEqual(summary["receipts"][0]["result"], "PASS")
        self.assertEqual(runtime["result"], "PASS")
        self.assert_schema_valid(runtime)

    def _runtime_evidence(self) -> dict[str, object]:
        return {
            "$schema": "https://overkill-factory.dev/schemas/hermes-runtime-readonly-evidence.schema.json",
            "record_type": "hermes_runtime_readonly_evidence",
            "checked_at": "2026-06-19T00:00:00Z",
            "target_ref": "tailscale:factory-runtime-peer",
            "hermes_status_readonly_passed": True,
            "profile_list_readonly_passed": True,
            "gateway_service_running": True,
            "discord_configured": True,
            "dedicated_gerente_gateway_running": True,
            "private_product_profile_not_factory_gateway": True,
            "factory_profile_set_has_no_conceptual_duplicates": True,
            "raw_private_values_omitted": True,
            "evidence_refs": [".tmp/factory-runs/hermes-live/hermes-runtime-readonly-evidence.json"],
        }


if __name__ == "__main__":
    unittest.main()
