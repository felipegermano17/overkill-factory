from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import sys
import tempfile
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
                (" M", "README.pt-BR.md"),
                (" M", "CHANGELOG.md"),
                (" M", "pyproject.toml"),
                ("??", ".env.example"),
                ("??", "schemas/example.schema.json"),
                ("??", "scripts/example.py"),
            ],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(report["result"], "ATTENTION")
        self.assertEqual(report["cleanup_policy"]["release_candidate_entries"], 7)
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
                (" M", ".tmp/factory-runs/release/worktree-release-inventory.json"),
                (" M", ".tmp/factory-runs/public-safety/head-summary.json"),
            ],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(report["classification_counts"]["generated_receipt"], 2)
        self.assertEqual(report["cleanup_policy"]["generated_receipt_entries"], 2)
        self.assertEqual(report["cleanup_policy"]["release_candidate_entries"], 0)
        self.assertEqual(report["blocking_items"], [])
        self.assertEqual(report["result"], "PASS")

    def test_git_hygiene_blocks_non_main_state(self) -> None:
        report = inventory.build_inventory(
            [],
            created_at="2026-06-10T00:00:00Z",
            git_hygiene={
                "primary_branch": "main",
                "current_branch": "codex/old-work",
                "blocking_items": [
                    "current_branch_is_not_main",
                    "extra_git_worktrees_present",
                    "local_non_main_branches_present",
                ],
            },
        )

        self.assertEqual(report["result"], "BLOCKED")
        self.assertIn("current_branch_is_not_main", report["blocking_items"])
        self.assertIn("extra_git_worktrees_present", report["blocking_items"])
        self.assertIn("local_non_main_branches_present", report["blocking_items"])

    def test_parse_worktree_porcelain_redacts_paths_to_branch_state(self) -> None:
        parsed = inventory.parse_worktree_porcelain(
            "worktree C:/repo\n"
            "HEAD abc\n"
            "branch refs/heads/main\n"
            "\n"
            "worktree C:/tmp/repo-feature\n"
            "HEAD def\n"
            "detached\n"
            "\n"
        )

        self.assertEqual(parsed[0]["branch"], "main")
        self.assertEqual(parsed[1]["detached"], "true")

    def test_external_out_path_reports_redacted_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "inventory.json"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = inventory.main(["--out", str(out)])

            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())
            printed = json.loads(stdout.getvalue())
            self.assertEqual(printed["out"], "external:inventory.json")


if __name__ == "__main__":
    unittest.main()
