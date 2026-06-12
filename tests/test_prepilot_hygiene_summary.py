from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PrepilotHygieneSummaryTest(unittest.TestCase):
    def test_generated_hygiene_receipts_are_not_tracked_release_material(self) -> None:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        tracked = result.stdout.splitlines()

        self.assertNotIn(".tmp/factory-runs/hygiene/prepilot-hygiene-summary.json", tracked)
        self.assertFalse(any(path.startswith("validation/hygiene/") for path in tracked))

    def test_release_docs_tell_operators_not_to_commit_generated_outputs(self) -> None:
        operations = (ROOT / "docs" / "operations" / "validation-and-release.md").read_text(encoding="utf-8")

        self.assertIn(".tmp", operations)
        self.assertIn("must not be committed", operations)


if __name__ == "__main__":
    unittest.main()
