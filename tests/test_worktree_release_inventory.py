from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "worktree_release_inventory.py"
SPEC = importlib.util.spec_from_file_location("worktree_release_inventory", MODULE_PATH)
assert SPEC is not None
inventory = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["worktree_release_inventory"] = inventory
SPEC.loader.exec_module(inventory)


class WorktreeReleaseInventoryTest(unittest.TestCase):
    def test_release_material_is_attention_not_cleanup(self) -> None:
        report = inventory.build_inventory(
            [
                (" M", "README.md"),
                ("??", "schemas/example.schema.json"),
                ("??", "scripts/example.py"),
            ],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(report["result"], "ATTENTION")
        self.assertEqual(report["cleanup_policy"]["release_candidate_entries"], 3)
        self.assertEqual(report["cleanup_policy"]["safe_cleanup_candidates"], 0)
        self.assertFalse(report["cleanup_policy"]["broad_cleanup_allowed"])

    def test_unknown_untracked_blocks_broad_release(self) -> None:
        report = inventory.build_inventory(
            [
                ("??", "scratch/private-note.txt"),
            ],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(report["result"], "BLOCKED")
        self.assertIn("needs_human_review_entries_present", report["blocking_items"])

    def test_cache_files_are_cleanup_candidates(self) -> None:
        report = inventory.build_inventory(
            [
                ("??", "tests/__pycache__/example.pyc"),
            ],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(report["cleanup_policy"]["safe_cleanup_candidates"], 1)
        self.assertIn("safe_cleanup_candidates_present", report["blocking_items"])

    def test_generated_validation_receipts_are_not_release_material(self) -> None:
        report = inventory.build_inventory(
            [
                (" M", "validation/release/worktree-release-inventory.json"),
                (" M", "validation/public-safety/head-summary.json"),
            ],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(report["classification_counts"]["generated_receipt"], 2)
        self.assertEqual(report["cleanup_policy"]["generated_receipt_entries"], 2)
        self.assertEqual(report["cleanup_policy"]["release_candidate_entries"], 0)
        self.assertEqual(report["blocking_items"], [])


if __name__ == "__main__":
    unittest.main()
