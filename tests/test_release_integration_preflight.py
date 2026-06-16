from __future__ import annotations

import importlib.util
import json
import subprocess
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
    def materialization(self) -> dict:
        return {
            "record_type": "release_preflight_materialization",
            "all_materializers_passed": True,
            "failed_materializers": [],
            "missing_evidence_refs": [],
            "runs": [
                {
                    "name": "fresh-fixture",
                    "result": "PASS",
                    "output_exists": True,
                }
            ],
        }

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
                materialization=self.materialization(),
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
                materialization=self.materialization(),
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
                materialization=self.materialization(),
            )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertFalse(receipt["release_candidate_plan"]["safe_to_prepare_candidate_branch"])

    def test_generated_receipts_do_not_count_as_unintegrated_release_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._fixtures(
                Path(tmp),
                worktree="PASS",
                head="PASS",
                origin="PASS",
                release_candidate_entries=0,
                generated_receipt_entries=4,
            )

            receipt = preflight.build_preflight(
                inventory_path=paths["inventory"],
                public_worktree_path=paths["worktree"],
                public_head_path=paths["head"],
                public_origin_path=paths["origin"],
                branch_name="codex/release",
                status_entries=4,
                generated_status_entries=4,
                created_at="2026-06-10T00:00:00Z",
                materialization=self.materialization(),
            )

        self.assertEqual(receipt["result"], "PASS")
        self.assertTrue(receipt["checks"]["release_ref_has_no_unintegrated_worktree_entries"])
        self.assertEqual(receipt["counts"]["generated_status_entries"], 4)
        self.assertEqual(receipt["counts"]["unintegrated_release_entries"], 0)
        self.assertEqual(receipt["attention_items"], [])

    def test_missing_preflight_evidence_is_not_reported_as_existing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {
                "inventory": root / "missing-inventory.json",
                "worktree": root / "missing-worktree.json",
                "head": root / "missing-head.json",
                "origin": root / "missing-origin.json",
            }

            receipt = preflight.build_preflight(
                inventory_path=paths["inventory"],
                public_worktree_path=paths["worktree"],
                public_head_path=paths["head"],
                public_origin_path=paths["origin"],
                branch_name="codex/release",
                status_entries=0,
                generated_status_entries=0,
                created_at="2026-06-10T00:00:00Z",
                materialization=self.materialization(),
            )

        self.assertEqual(receipt["evidence_refs"], [])
        self.assertEqual(len(receipt["missing_evidence_refs"]), 4)
        self.assertIn("preflight_evidence_refs_exist", receipt["blocking_items"])
        self.assertIn(
            "materialize missing preflight evidence summaries before release review",
            receipt["next_required_actions"],
        )

    def test_build_preflight_without_fresh_materialization_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._fixtures(Path(tmp), worktree="PASS", head="PASS", origin="PASS", release_candidate_entries=0)

            receipt = preflight.build_preflight(
                inventory_path=paths["inventory"],
                public_worktree_path=paths["worktree"],
                public_head_path=paths["head"],
                public_origin_path=paths["origin"],
                branch_name="codex/release",
                status_entries=0,
                generated_status_entries=0,
                created_at="2026-06-10T00:00:00Z",
            )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("fresh_preflight_materialization_provided", receipt["blocking_items"])
        self.assertIn(
            "rerun release preflight materializers in the current process before release review",
            receipt["next_required_actions"],
        )

    def test_materializer_creates_all_preflight_input_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {
                "inventory": root / "inventory.json",
                "worktree": root / "worktree.json",
                "head": root / "head.json",
                "origin": root / "origin.json",
            }

            def fake_runner(command, **_kwargs):
                if "--out" in command:
                    out = Path(command[command.index("--out") + 1])
                    payload = {"result": "ATTENTION", "cleanup_policy": {}}
                else:
                    out = Path(command[command.index("--summary-json") + 1])
                    payload = {"result": "PASS"}
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(payload), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0)

            materialization = preflight.materialize_preflight_inputs(
                inventory_path=paths["inventory"],
                public_worktree_path=paths["worktree"],
                public_head_path=paths["head"],
                public_origin_path=paths["origin"],
                runner=fake_runner,
            )

            self.assertEqual(materialization["missing_evidence_refs"], [])
            self.assertEqual(materialization["failed_materializers"], [])
            self.assertTrue(materialization["all_materializers_passed"])
            for path in paths.values():
                with self.subTest(path=path.name):
                    self.assertTrue(path.is_file())

    def test_materializer_failure_blocks_even_when_stale_pass_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = self._fixtures(root, worktree="PASS", head="PASS", origin="PASS", release_candidate_entries=0)
            for path in paths.values():
                path.write_text(
                    json.dumps(
                        {
                            "result": "PASS",
                            "cleanup_policy": {
                                "release_candidate_entries": 0,
                                "generated_receipt_entries": 0,
                                "needs_human_review_entries": 0,
                                "safe_cleanup_candidates": 0,
                            },
                        }
                    ),
                    encoding="utf-8",
                )

            def failing_runner(command, **_kwargs):
                return subprocess.CompletedProcess(
                    command,
                    7,
                    stdout="old PASS output should not count\n",
                    stderr=f"failed under {root}\n",
                )

            materialization = preflight.materialize_preflight_inputs(
                inventory_path=paths["inventory"],
                public_worktree_path=paths["worktree"],
                public_head_path=paths["head"],
                public_origin_path=paths["origin"],
                runner=failing_runner,
            )
            receipt = preflight.build_preflight(
                inventory_path=paths["inventory"],
                public_worktree_path=paths["worktree"],
                public_head_path=paths["head"],
                public_origin_path=paths["origin"],
                branch_name="codex/release",
                status_entries=0,
                generated_status_entries=0,
                created_at="2026-06-10T00:00:00Z",
                materialization=materialization,
            )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("preflight_materializers_passed", receipt["blocking_items"])
        self.assertIn("preflight_evidence_refs_exist", receipt["blocking_items"])
        self.assertFalse(receipt["materialization"]["all_materializers_passed"])
        self.assertEqual(len(receipt["materialization"]["failed_materializers"]), 4)
        self.assertEqual(len(receipt["missing_evidence_refs"]), 4)
        self.assertNotIn(str(root), json.dumps(receipt))

    def _fixtures(
        self,
        root: Path,
        *,
        worktree: str,
        head: str,
        origin: str,
        release_candidate_entries: int = 7,
        generated_receipt_entries: int = 0,
    ) -> dict[str, Path]:
        inventory = root / "inventory.json"
        inventory.write_text(
            json.dumps(
                {
                    "result": "ATTENTION",
                    "cleanup_policy": {
                        "release_candidate_entries": release_candidate_entries,
                        "generated_receipt_entries": generated_receipt_entries,
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
