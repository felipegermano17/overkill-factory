from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize_hermes_profiles.py"


class MaterializeHermesProfilesTest(unittest.TestCase):
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
