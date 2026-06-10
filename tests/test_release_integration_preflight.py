from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "release_integration_preflight.py"
SPEC = importlib.util.spec_from_file_location("release_integration_preflight", MODULE_PATH)
assert SPEC is not None
preflight = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["release_integration_preflight"] = preflight
SPEC.loader.exec_module(preflight)


class ReleaseIntegrationPreflightTest(unittest.TestCase):
    def test_dirty_main_blocks_release_integration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._fixtures(Path(tmp), worktree="PASS", head="FAIL", origin="FAIL")

            receipt = preflight.build_preflight(
                inventory_path=paths["inventory"],
                public_worktree_path=paths["worktree"],
                public_head_path=paths["head"],
                public_origin_path=paths["origin"],
                branch_name="main",
                status_entries=10,
                created_at="2026-06-10T00:00:00Z",
            )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("current_branch_is_not_dirty_main", receipt["blocking_items"])
        self.assertIn("head_public_safety_passed", receipt["blocking_items"])
        self.assertTrue(receipt["release_candidate_plan"]["safe_to_prepare_candidate_branch"])
        self.assertEqual(
            receipt["release_candidate_plan"]["recommended_branch"],
            "codex/vfinal-release-candidate",
        )

    def test_clean_release_branch_with_safe_refs_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._fixtures(Path(tmp), worktree="PASS", head="PASS", origin="PASS")

            receipt = preflight.build_preflight(
                inventory_path=paths["inventory"],
                public_worktree_path=paths["worktree"],
                public_head_path=paths["head"],
                public_origin_path=paths["origin"],
                branch_name="codex/release",
                status_entries=0,
                created_at="2026-06-10T00:00:00Z",
            )

        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["blocking_items"], [])
        self.assertTrue(receipt["release_candidate_plan"]["safe_to_prepare_candidate_branch"])

    def test_candidate_branch_is_not_safe_when_worktree_scan_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._fixtures(Path(tmp), worktree="FAIL", head="PASS", origin="PASS")

            receipt = preflight.build_preflight(
                inventory_path=paths["inventory"],
                public_worktree_path=paths["worktree"],
                public_head_path=paths["head"],
                public_origin_path=paths["origin"],
                branch_name="main",
                status_entries=10,
                created_at="2026-06-10T00:00:00Z",
            )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertFalse(receipt["release_candidate_plan"]["safe_to_prepare_candidate_branch"])

    def _fixtures(self, root: Path, *, worktree: str, head: str, origin: str) -> dict[str, Path]:
        inventory = root / "inventory.json"
        inventory.write_text(
            json.dumps(
                {
                    "result": "ATTENTION",
                    "cleanup_policy": {
                        "release_candidate_entries": 7,
                        "needs_human_review_entries": 0,
                        "safe_cleanup_candidates": 0,
                    },
                }
            ),
            encoding="utf-8",
        )
        paths = {
            "inventory": inventory,
            "worktree": root / "worktree.json",
            "head": root / "head.json",
            "origin": root / "origin.json",
        }
        paths["worktree"].write_text(json.dumps({"result": worktree}), encoding="utf-8")
        paths["head"].write_text(json.dumps({"result": head}), encoding="utf-8")
        paths["origin"].write_text(json.dumps({"result": origin}), encoding="utf-8")
        return paths


if __name__ == "__main__":
    unittest.main()
