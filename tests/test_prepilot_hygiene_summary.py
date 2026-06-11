from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "validation" / "hygiene" / "prepilot-hygiene-summary.json"


class PrepilotHygieneSummaryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    def test_hygiene_summary_separates_trash_from_release_material(self) -> None:
        self.assertEqual(self.summary["record_type"], "prepilot_hygiene_summary")
        self.assertIn(self.summary["result"], {"PASS", "ATTENTION"})
        self.assertTrue(self.summary["checks"]["repo_ignored_junk_removed"])
        self.assertTrue(self.summary["checks"]["repo_inventory_has_no_unknown_entries"])
        self.assertTrue(self.summary["checks"]["repo_inventory_has_no_cleanup_candidates"])
        self.assertTrue(self.summary["checks"]["minimal_example_ready"])
        self.assertTrue(self.summary["checks"]["hermes_gateway_readonly_passed"])
        self.assertTrue(self.summary["checks"]["kanban_has_no_ready_or_running_factory_tasks"])
        inventory = self.summary["repo_inventory_summary"]
        self.assertGreater(inventory["release_candidate_entries"], 0)
        self.assertEqual(inventory["needs_human_review_entries"], 0)
        self.assertEqual(inventory["safe_cleanup_candidates"], 0)
        self.assertEqual(inventory["blocking_items"], [])

        must_not_clean = "\n".join(self.summary["must_not_clean_automatically"])
        self.assertIn("release material, not trash", must_not_clean)
        self.assertIn("blocked Hermes/Kanban tasks", must_not_clean)

    def test_evidence_refs_exist_when_repo_local(self) -> None:
        for ref in self.summary["evidence_refs"]:
            if ref.startswith(("external:", "redacted:")):
                continue
            with self.subTest(ref=ref):
                self.assertTrue((ROOT / ref).exists(), ref)


if __name__ == "__main__":
    unittest.main()
