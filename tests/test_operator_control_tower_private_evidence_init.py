from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INIT_PATH = ROOT / "scripts" / "operator_control_tower_private_evidence_init.py"
DOCTOR_PATH = ROOT / "scripts" / "operator_control_tower_private_evidence_doctor.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


init = load_module("operator_control_tower_private_evidence_init", INIT_PATH)
doctor = load_module("operator_control_tower_private_evidence_doctor_for_init_test", DOCTOR_PATH)


class OperatorControlTowerPrivateEvidenceInitTest(unittest.TestCase):
    def test_init_refuses_public_repo_destination(self) -> None:
        with self.assertRaises(ValueError):
            init.init_bundle(ROOT / "tmp-private-evidence", created_at="2026-06-10T00:00:00Z")

    def test_init_creates_private_placeholders_that_doctor_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "control-tower-evidence"
            summary = init.init_bundle(out_dir, created_at="2026-06-10T00:00:00Z")

            self.assertEqual(summary["result"], "initialized")
            self.assertTrue((out_dir / "discord-control-tower-mapping.json").exists())
            self.assertTrue((out_dir / "runtime-approval-event.json").exists())
            self.assertTrue((out_dir / "bridge-health.json").exists())

            report = doctor.build_doctor_report(
                mapping_path=out_dir / "discord-control-tower-mapping.json",
                runtime_event_path=out_dir / "runtime-approval-event.json",
                bridge_health_path=out_dir / "bridge-health.json",
                created_at="2026-06-10T00:00:00Z",
            )

        self.assertEqual(report["result"], "BLOCKED")
        self.assertIn("mapping_has_real_refs", report["blocking_items"])


if __name__ == "__main__":
    unittest.main()
