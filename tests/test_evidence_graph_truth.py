from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FACTORYCTL_PATH = ROOT / "scripts" / "factoryctl.py"
SPEC = importlib.util.spec_from_file_location("factoryctl_evidence_truth", FACTORYCTL_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl_evidence_truth"] = factoryctl
SPEC.loader.exec_module(factoryctl)


class EvidenceGraphTruthTest(unittest.TestCase):
    def minimal_card_path(self) -> Path:
        return ROOT / "examples" / "minimal-hermes-project" / "card.md"

    def minimal_card(self) -> dict:
        return factoryctl.load_json_like(self.minimal_card_path())

    def test_evidence_graph_blocks_missing_worker_results_without_private_leakage(self) -> None:
        graph = factoryctl.build_evidence_graph(self.minimal_card(), self.minimal_card_path())
        serialized = json.dumps(graph, sort_keys=True)

        self.assertEqual(graph["record_type"], "evidence_graph")
        self.assertEqual(graph["result"], "BLOCKED")
        self.assertIn("blocked_missing_evidence", serialized)
        self.assertNotIn("webhook-marker", serialized)
        self.assertTrue(graph["public_private_boundary"]["public_safe_summary_only"])

    def test_evidence_graph_redacts_private_artifact_refs_fail_closed(self) -> None:
        card = self.minimal_card()
        worker_id = factoryctl.required_worker_ids(card)[0]
        worker = factoryctl.WORKERS[worker_id]
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)
            result = factoryctl.build_worker_result(
                worker_id,
                card,
                result="PASS",
                tool_or_profile="fixture",
                executed_by=worker_id,
                evidence_refs=["webhook-marker"],
                blocking_findings=False,
                findings_summary="fixture",
                next_action="continue",
            )
            (results_dir / f"{worker_id}.json").write_text(json.dumps(result), encoding="utf-8")

            graph = factoryctl.build_evidence_graph(card, self.minimal_card_path(), worker_results_dir=results_dir)

        serialized = json.dumps(graph, sort_keys=True)
        self.assertEqual(graph["result"], "BLOCKED")
        self.assertIn(f"worker-result:{worker.output_field}", serialized)
        self.assertIn("redacted:private-runtime-ref", serialized)
        self.assertNotIn("webhook-marker", serialized)

    def test_hermes_evidence_exporter_redacts_record_names_and_private_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "operator-hermes"
            workspace.mkdir()
            private_named = workspace / "sensitive-board.json"
            private_named.write_text(
                json.dumps(
                    {
                        "record_type": "security_scan_result",
                        "result": "PASS",
                        "worker": {"id": "codex-security"},
                        "evidence_refs": ["external:untrusted-proof"],
                    }
                ),
                encoding="utf-8",
            )

            package = factoryctl.build_hermes_evidence_package(board="operator board", workspace=workspace)

        serialized = json.dumps(package, sort_keys=True)
        self.assertEqual(package["result"], "BLOCKED")
        self.assertEqual(package["records"][0]["record_ref"], "external:hermes-record-1")
        self.assertIn("redacted:private-runtime-ref", serialized)
        self.assertNotIn("sensitive-board", serialized)
        self.assertNotIn("untrusted-proof", serialized)

    def test_hermes_evidence_exporter_accepts_sanitized_operator_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "operator-hermes"
            workspace.mkdir()
            (workspace / "worker-result.json").write_text(
                json.dumps(
                    {
                        "record_type": "security_scan_result",
                        "result": "PASS",
                        "worker": {"id": "codex-security"},
                        "evidence_refs": ["external:operator-summary"],
                    }
                ),
                encoding="utf-8",
            )

            package = factoryctl.build_hermes_evidence_package(board="operator board", workspace=workspace)

        self.assertEqual(package["result"], "PASS")
        self.assertEqual(package["state"], "partially_executed")
        self.assertEqual(package["records"][0]["evidence_refs"], ["external:operator-summary"])

    def test_evidence_graph_can_link_sanitized_hermes_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_path = Path(tmp) / "hermes-package.json"
            package_path.write_text(
                json.dumps(
                    {
                        "$schema": "https://overkill-factory.dev/schemas/hermes-evidence-package.schema.json",
                        "record_type": "hermes_evidence_package",
                        "result": "PASS",
                    }
                ),
                encoding="utf-8",
            )

            graph = factoryctl.build_evidence_graph(
                self.minimal_card(),
                self.minimal_card_path(),
                hermes_evidence_path=package_path,
            )

        hermes_nodes = [node for node in graph["nodes"] if node["id"] == "hermes-evidence"]
        self.assertEqual(hermes_nodes[0]["status"], "PASS")

    def test_readiness_ledger_never_promotes_bounded_graph_to_production_ready(self) -> None:
        graph = factoryctl.build_evidence_graph(self.minimal_card(), self.minimal_card_path())
        ledger = factoryctl.build_readiness_truth_ledger(self.minimal_card(), self.minimal_card_path(), evidence_graph=graph)

        self.assertFalse(ledger["production_ready"])
        self.assertNotEqual(ledger["overall_truth_level"], "production_ready")
        self.assertTrue(ledger["blocker_economics"])

    def test_truth_cli_writes_repo_only_degraded_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "truth.json"
            rc = factoryctl.main_with_args_for_test(
                [
                    "truth",
                    "--target",
                    "issue-94",
                    "--card",
                    str(self.minimal_card_path()),
                    "--out",
                    str(out),
                ]
            )
            packet = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(rc, 1)
        self.assertEqual(packet["record_type"], "factory_truth_packet")
        self.assertEqual(packet["hermes"]["mode"], "repo_only_degraded")
        self.assertFalse(packet["production_ready"])
        self.assertTrue(packet["current_blockers"])

    def test_prepilot_checklist_requires_graph_and_truth_ledger(self) -> None:
        checklist = factoryctl.build_prepilot_loose_end_checklist(
            evidence_graph=None,
            readiness_ledger=None,
            hermes_evidence=None,
        )

        self.assertEqual(checklist["result"], "BLOCKED")
        self.assertIn("evidence_graph_path", checklist["blocking_items"])
        self.assertFalse(checklist["pilot_completion_claim_allowed"])


if __name__ == "__main__":
    unittest.main()
