from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "issue-84" / "status-snapshot-v0"
SCHEMA = ROOT / "schemas" / "factory-status-snapshot.schema.json"
REQUIRED_CASES = ",".join(f"FX{i:02d}" for i in range(1, 19))


def load_module(name: str, rel_path: str):
    path = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


contract = load_module("issue84_status_snapshot_contract", "scripts/issue84/status_snapshot_contract.py")
fixture_validator = load_module("issue84_validate_status_snapshot_fixtures", "scripts/issue84/validate_status_snapshot_fixtures.py")
evidence_validator = load_module("issue84_validate_evidence_refs", "scripts/issue84/validate_evidence_refs.py")
fail_closed = load_module("issue84_assert_fail_closed", "scripts/issue84/assert_fail_closed.py")


class StatusSnapshotV0Test(unittest.TestCase):
    def test_fixture_inventory_contains_fx01_through_fx18_and_parses(self) -> None:
        fixture_ids = []
        for path in sorted(FIXTURES.glob("FX*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            fixture_ids.append(data["fixture_id"])
            self.assertEqual(data["$schema"], "https://overkill-factory.dev/schemas/factory-status-snapshot.schema.json")
            self.assertEqual(data["schema_version"], "status-snapshot-v0")
        self.assertEqual(fixture_ids, [f"FX{i:02d}" for i in range(1, 19)])

    def test_status_snapshot_fixture_validator_accepts_complete_inventory(self) -> None:
        rc = fixture_validator.main_with_args_for_test([
            str(FIXTURES),
            "--schema",
            str(SCHEMA),
            "--require-cases",
            REQUIRED_CASES,
            "--fail-closed",
        ])
        self.assertEqual(rc, 0)

    def test_fixture_validator_fails_closed_when_required_case_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shutil.copytree(FIXTURES, tmp_path / "status-snapshot-v0")
            (tmp_path / "status-snapshot-v0" / "FX18-mechanical_product_face_pass_but_visual_quality_fail.json").unlink()
            rc = fixture_validator.main_with_args_for_test([
                str(tmp_path / "status-snapshot-v0"),
                "--schema",
                str(SCHEMA),
                "--require-cases",
                REQUIRED_CASES,
                "--fail-closed",
            ])
        self.assertEqual(rc, 1)

    def test_fail_closed_validator_rejects_stale_release_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shutil.copytree(FIXTURES, tmp_path / "status-snapshot-v0")
            stale_path = tmp_path / "status-snapshot-v0" / "FX06-stale_observed_at_or_source_updated.json"
            data = json.loads(stale_path.read_text(encoding="utf-8"))
            data["next_safe_action"]["action_type"] = "release"
            data["next_safe_action"]["label"] = "release from stale snapshot"
            stale_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            rc = fail_closed.main_with_args_for_test([
                str(tmp_path / "status-snapshot-v0"),
                "--cases",
                "stale,missing,contradictory,private_unavailable,missing-gate",
            ])
        self.assertEqual(rc, 1)

    def test_fail_closed_validator_accepts_required_negative_states(self) -> None:
        rc = fail_closed.main_with_args_for_test([
            str(FIXTURES),
            "--cases",
            "stale,missing,contradictory,private_unavailable,missing-gate",
        ])
        self.assertEqual(rc, 0)

    def test_evidence_validator_accepts_public_safe_refs_and_rejects_expected_negative_fixture(self) -> None:
        summary = evidence_validator.validate_directory(FIXTURES)
        self.assertEqual(summary["unexpected_blocked_count"], 0)
        self.assertGreaterEqual(summary["expected_blocked_count"], 1)
        rc = evidence_validator.main_with_args_for_test([
            str(FIXTURES),
            "--allow-public-urls",
            "--allow-relative-artifacts",
            "--deny-raw-private",
            "--deny-local-paths",
            "--deny-chat-ids",
            "--deny-secrets",
        ])
        self.assertEqual(rc, 0)

    def test_evidence_validator_rejects_local_absolute_path_in_positive_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shutil.copytree(FIXTURES, tmp_path / "status-snapshot-v0")
            positive_path = tmp_path / "status-snapshot-v0" / "FX01-current_success_projection.json"
            data = json.loads(positive_path.read_text(encoding="utf-8"))
            data["evidence_refs"].append({
                "id": "EV-BAD-LOCAL-PATH",
                "kind": "worker_result",
                "ref": "/tmp/private-runtime/evidence.json",
                "source_refs": ["TEST"],
                "freshness_state": "current",
                "public_safety_state": "public_safe",
                "verification_status": "unverified",
                "raw_payload_included": False,
            })
            positive_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            rc = evidence_validator.main_with_args_for_test([str(tmp_path / "status-snapshot-v0")])
        self.assertEqual(rc, 1)

    def test_schema_contract_requires_receipt_five_and_gate_state_fields(self) -> None:
        valid = contract.load_json(FIXTURES / "FX01-current_success_projection.json")
        self.assertEqual(contract.validate_snapshot(valid), [])
        invalid = dict(valid)
        invalid.pop("receipt_five_status")
        errors = contract.validate_snapshot(invalid)
        self.assertTrue(any("receipt_five_status" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
