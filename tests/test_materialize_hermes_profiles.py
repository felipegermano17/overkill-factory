from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize_hermes_profiles.py"
SPEC = importlib.util.spec_from_file_location("materialize_hermes_profiles", SCRIPT)
assert SPEC is not None
materialize = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(materialize)


class MaterializeHermesProfilesTest(unittest.TestCase):
    def test_rendered_profile_uses_gate_timing_not_queue_source_of_truth(self) -> None:
        workers = materialize.load_json(ROOT / "agents" / "worker-profiles.public.json")["profiles"]
        bindings = materialize.load_json(ROOT / "agents" / "hermes-profile-bindings.public.json")["bindings"]

        soul = materialize.render_soul(workers["frontend-builder"], bindings["frontend-builder"])

        self.assertIn("Gate timing policy basis: factoryctl.worker_gate_timing_class", soul)
        self.assertIn("Runtime authority: hermes_kanban", soul)
        self.assertNotIn("Queue source of truth", soul)

    def test_dry_run_does_not_require_existing_source_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(ROOT),
                    "--profiles-dir",
                    tmp,
                    "--workers",
                    "frontend-builder",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DRY-RUN note", result.stdout)
        self.assertIn("frontend-builder", result.stdout)

    def test_apply_without_source_profile_fails_closed_without_hermes_bin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(ROOT),
                    "--profiles-dir",
                    tmp,
                    "--workers",
                    "frontend-builder",
                    "--apply",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("source profile not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
