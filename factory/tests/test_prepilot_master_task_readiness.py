from __future__ import annotations

import subprocess
import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import factory_production_readiness


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
FORBIDDEN_TRACKED_PREFIXES = (
    "validation/",
    "pilots/",
    "docs/illustrations/",
    "docs/maps/",
    "docs/methodology/",
    "docs/pilots/",
    "docs/planning/",
    "docs/research/",
    "docs/reviews/",
    "docs/roadmap/",
    "docs/validation/",
)


class PrepilotMasterTaskReadinessTest(unittest.TestCase):
    def test_historical_evidence_dirs_are_not_tracked(self) -> None:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        tracked = result.stdout.splitlines()

        for path in tracked:
            with self.subTest(path=path):
                self.assertFalse(path.startswith(FORBIDDEN_TRACKED_PREFIXES), path)

    def test_generated_outputs_are_ignored_not_public_source(self) -> None:
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

        for ignored in [".tmp/", "validation/", "pilots/"]:
            with self.subTest(ignored=ignored):
                self.assertIn(ignored, gitignore)

    def test_production_readiness_defaults_to_generated_tmp_outputs(self) -> None:
        self.assertIn(".tmp", factory_production_readiness.DEFAULT_OUT.parts)
        self.assertIn("factory-runs", factory_production_readiness.DEFAULT_OUT.parts)

        tmp_root = ROOT / ".tmp" / "factory-runs"
        tmp_root.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=tmp_root) as tmp:
            missing = Path(tmp) / "missing"
            receipt = factory_production_readiness.build_readiness(
                prepilot_master_path=missing / "prepilot.json",
                runtime_status_path=missing / "runtime.json",
                preflight_path=missing / "preflight.json",
                control_tower_path=missing / "control-tower.json",
                control_tower_doctor_path=missing / "control-tower-doctor.json",
                worktree_inventory_path=missing / "worktree.json",
                release_integration_path=missing / "release-integration.json",
                public_worktree_path=missing / "public-worktree.json",
                public_head_path=missing / "public-head.json",
                public_origin_path=missing / "public-origin.json",
                created_at="2026-06-12T00:00:00Z",
            )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertTrue(all(ref.startswith(".tmp/factory-runs/") for ref in receipt["evidence_refs"]))
        self.assertTrue(receipt["blocker_economics"])
        self.assertTrue(all("smallest_safe_next_action" in item for item in receipt["blocker_economics"]))

    def test_production_readiness_can_consume_evidence_graph_component(self) -> None:
        with TemporaryDirectory() as tmp:
            graph_path = Path(tmp) / "evidence-graph.json"
            graph_path.write_text(
                json.dumps(
                    {
                        "$schema": "https://overkill-factory.dev/schemas/evidence-graph.schema.json",
                        "record_type": "evidence_graph",
                        "result": "BLOCKED",
                    }
                ),
                encoding="utf-8",
            )

            receipt = factory_production_readiness.build_readiness(evidence_graph_path=graph_path)

        by_id = {item["id"]: item for item in receipt["components"]}
        self.assertIn("evidence_graph", by_id)
        self.assertEqual(by_id["evidence_graph"]["status"], "BLOCKED")

    def test_public_readme_rejects_narrative_history_as_onboarding(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        normalized = " ".join(readme.split())

        self.assertIn("documentação antiga preservada como histórico", normalized)
        self.assertIn("docs/pt-BR/linha-de-producao.md", readme)
        self.assertNotIn("docs/roadmap/", readme)
        self.assertNotIn("docs/en/", readme)


if __name__ == "__main__":
    unittest.main()
