from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FACTORYCTL_PATH = ROOT / "scripts" / "factoryctl.py"
RECONCILER_PATH = ROOT / "scripts" / "evidence_reconciler.py"

FACTORYCTL_SPEC = importlib.util.spec_from_file_location("factoryctl", FACTORYCTL_PATH)
assert FACTORYCTL_SPEC is not None
factoryctl = importlib.util.module_from_spec(FACTORYCTL_SPEC)
assert FACTORYCTL_SPEC.loader is not None
sys.modules["factoryctl"] = factoryctl
FACTORYCTL_SPEC.loader.exec_module(factoryctl)

RECONCILER_SPEC = importlib.util.spec_from_file_location("evidence_reconciler", RECONCILER_PATH)
assert RECONCILER_SPEC is not None
evidence_reconciler = importlib.util.module_from_spec(RECONCILER_SPEC)
assert RECONCILER_SPEC.loader is not None
RECONCILER_SPEC.loader.exec_module(evidence_reconciler)


def closure_card() -> dict:
    return {
        "card_id": "TEST-CLOSURE-R2",
        "slice_id": "TEST-SLICE",
        "status": "review",
        "phase": "F13",
        "risk_effective": "R2",
        "surfaces": [
            "code"
        ],
        "source_refs": [
            "validation fixture"
        ],
        "target_repo_paths": [
            "README.md"
        ],
        "done_definition": "All required worker results are valid and reconciled.",
        "executor_identity": "implementation-worker",
        "reviewer_identity": "independent-reviewer",
        "review": {
            "independent_review_required": True
        },
        "security_scan_packet": {
            "scanner_agent": "codex-security",
            "scan_scope": [
                "README.md"
            ]
        },
    }


def required_before_done_workers(card: dict) -> list[str]:
    return [
        worker_id
        for worker_id in factoryctl.required_worker_ids(card)
        if worker_id != "evidence-reconciler"
        and factoryctl.worker_queue_class(worker_id, card) == "blocking-before-done"
    ]


def result_for(worker_id: str, card: dict, created_at: str) -> dict:
    payload = factoryctl.build_worker_result(
        worker_id,
        card,
        result="PASS",
        tool_or_profile="fixture",
        executed_by=worker_id,
        evidence_refs=["README.md"],
        blocking_findings=False,
        findings_summary="Fixture PASS.",
        next_action="none",
    )
    payload["created_at"] = created_at
    return payload


def mark_background_subagent(
    payload: dict,
    *,
    status: str = "completed",
    reconciliation_state: str = "pending",
    accepted: bool = False,
) -> dict:
    payload["tool_or_profile"] = "hermes_delegate_task_background"
    payload["executed_by"] = "background-subagent"
    payload["async_subagent"] = {
        "runtime": "hermes_delegate_task_background",
        "delegation_id": "external:delegation-fixture",
        "parent_card_id": "TEST-CLOSURE-R2",
        "parent_worker_id": payload["worker"]["id"],
        "status": status,
        "reconciliation_state": reconciliation_state,
        "reconciliation_owner": "factory-orchestrator",
        "candidate_evidence_refs": ["external:background-subagent-summary"],
        "accepted_by_worker_result_ref": "external:accepted-worker-result" if accepted else "",
    }
    return payload


def write_results(card: dict, results_dir: Path, *, skip_worker: str | None = None) -> None:
    for index, worker_id in enumerate(required_before_done_workers(card), start=1):
        if worker_id == skip_worker:
            continue
        payload = result_for(worker_id, card, f"2026-06-06T00:{index:02d}:00+00:00")
        results_dir.joinpath(f"{worker_id}.json").write_text(
            factoryctl.json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )


class EvidenceReconcilerTest(unittest.TestCase):
    def test_reconciles_all_required_current_results(self) -> None:
        card = closure_card()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)
            write_results(card, results_dir)

            index = evidence_reconciler.reconcile(card, results_dir)

        self.assertTrue(index["receipt_five_ready"])
        self.assertEqual(index["missing_required_fields"], [])
        self.assertEqual(index["blocking_current_results"], [])
        self.assertIn("security_scan_result", index["effective_results"])
        self.assertIn("independent_review_result", index["effective_results"])

    def test_unreconciled_background_subagent_result_does_not_satisfy_receipt_five(self) -> None:
        card = closure_card()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)
            write_results(card, results_dir)
            async_security = mark_background_subagent(
                result_for("codex-security", card, "2026-06-06T00:50:00+00:00"),
                status="completed",
                reconciliation_state="pending",
                accepted=False,
            )
            results_dir.joinpath("codex-security.json").write_text(
                factoryctl.json.dumps(async_security, indent=2) + "\n",
                encoding="utf-8",
            )

            index = evidence_reconciler.reconcile(card, results_dir)

        self.assertFalse(index["receipt_five_ready"])
        self.assertIn(
            "security_scan_result",
            {item["record_type"] for item in index["blocking_current_results"]},
        )
        security = index["effective_results"]["security_scan_result"]
        self.assertFalse(security["valid_for_closure"])
        self.assertIn(
            "Hermes background subagent output must set reconciliation_state=reconciled before closure",
            security["validation_errors"],
        )

    def test_reconciled_background_subagent_result_can_be_consumed(self) -> None:
        card = closure_card()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)
            write_results(card, results_dir)
            async_security = mark_background_subagent(
                result_for("codex-security", card, "2026-06-06T00:50:00+00:00"),
                status="reconciled",
                reconciliation_state="reconciled",
                accepted=True,
            )
            results_dir.joinpath("codex-security.json").write_text(
                factoryctl.json.dumps(async_security, indent=2) + "\n",
                encoding="utf-8",
            )

            index = evidence_reconciler.reconcile(card, results_dir)

        self.assertTrue(index["receipt_five_ready"])
        self.assertTrue(index["effective_results"]["security_scan_result"]["valid_for_closure"])

    def test_stale_background_subagent_result_blocks_receipt_five_even_with_acceptance_ref(self) -> None:
        card = closure_card()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)
            write_results(card, results_dir)
            async_security = mark_background_subagent(
                result_for("codex-security", card, "2026-06-06T00:50:00+00:00"),
                status="stale",
                reconciliation_state="reconciled",
                accepted=True,
            )
            results_dir.joinpath("codex-security.json").write_text(
                factoryctl.json.dumps(async_security, indent=2) + "\n",
                encoding="utf-8",
            )

            index = evidence_reconciler.reconcile(card, results_dir)

        self.assertFalse(index["receipt_five_ready"])
        security = index["effective_results"]["security_scan_result"]
        self.assertIn("terminal Hermes background subagent output cannot satisfy Receipt Five", security["validation_errors"])

    def test_newer_pass_supersedes_older_fail_for_same_receipt_field(self) -> None:
        card = closure_card()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)
            write_results(card, results_dir)
            fail_payload = result_for("independent-reviewer", card, "2026-06-06T00:01:00+00:00")
            fail_payload["result"] = "FAIL"
            fail_payload["blocking_findings"] = True
            fail_payload["findings_summary"] = "Old blocker."
            pass_payload = result_for("independent-reviewer", card, "2026-06-06T00:40:00+00:00")
            results_dir.joinpath("independent-reviewer-old-fail.json").write_text(
                factoryctl.json.dumps(fail_payload, indent=2) + "\n",
                encoding="utf-8",
            )
            results_dir.joinpath("independent-reviewer-new-pass.json").write_text(
                factoryctl.json.dumps(pass_payload, indent=2) + "\n",
                encoding="utf-8",
            )

            index = evidence_reconciler.reconcile(card, results_dir)

        self.assertTrue(index["receipt_five_ready"])
        self.assertEqual(
            index["effective_results"]["independent_review_result"]["result"],
            "PASS",
        )
        self.assertGreaterEqual(len(index["superseded_results"]), 1)
        self.assertIn(
            "independent_review_result",
            {item["record_type"] for item in index["superseded_results"]},
        )

    def test_top_level_inactive_result_does_not_satisfy_receipt_five(self) -> None:
        card = closure_card()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)
            write_results(card, results_dir)
            inactive_security = result_for("codex-security", card, "2026-06-06T00:50:00+00:00")
            inactive_security["active"] = False
            results_dir.joinpath("codex-security.json").write_text(
                factoryctl.json.dumps(inactive_security, indent=2) + "\n",
                encoding="utf-8",
            )

            index = evidence_reconciler.reconcile(card, results_dir)

        self.assertFalse(index["receipt_five_ready"])
        self.assertIn("security_scan_result", index["missing_required_fields"])
        self.assertIn(
            "security_scan_result",
            {item["record_type"] for item in index["superseded_results"]},
        )

    def test_missing_required_result_blocks_receipt_five(self) -> None:
        card = closure_card()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)
            write_results(card, results_dir, skip_worker="codex-security")

            index = evidence_reconciler.reconcile(card, results_dir)
            result = evidence_reconciler.build_reconciler_result(
                card,
                "reports/index.json",
                index,
            )

        self.assertFalse(index["receipt_five_ready"])
        self.assertIn("security_scan_result", index["missing_required_fields"])
        self.assertEqual(result["result"], "BLOCKED")
        self.assertTrue(result["blocking_findings"])

    def test_unreadable_effective_evidence_ref_blocks_receipt_five(self) -> None:
        card = closure_card()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            results_dir = tmp_path / "worker-results"
            results_dir.mkdir()
            write_results(card, results_dir)
            security = result_for("codex-security", card, "2026-06-06T00:50:00+00:00")
            security["evidence_refs"] = [
                "external:kanban-artifact:t_fixture/artifacts/missing-security-proof.json"
            ]
            results_dir.joinpath("codex-security.json").write_text(
                factoryctl.json.dumps(security, indent=2) + "\n",
                encoding="utf-8",
            )

            index = evidence_reconciler.reconcile(card, results_dir)

        self.assertFalse(index["receipt_five_ready"])
        self.assertIn(
            "security_scan_result",
            {item["record_type"] for item in index["blocking_current_results"]},
        )
        security_result = index["effective_results"]["security_scan_result"]
        self.assertFalse(security_result["valid_for_closure"])
        self.assertIn(
            "unreadable evidence refs: external:kanban-artifact:t_fixture/artifacts/missing-security-proof.json",
            security_result["validation_errors"],
        )

    def test_readable_kanban_artifact_refs_can_satisfy_receipt_five(self) -> None:
        card = closure_card()
        ref = "external:kanban-artifact:t_fixture/artifacts/security-proof.json"
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            results_dir = tmp_path / "worker-results"
            results_dir.mkdir()
            write_results(card, results_dir)
            security = result_for("codex-security", card, "2026-06-06T00:50:00+00:00")
            security["evidence_refs"] = [ref]
            security["artifact_readback"] = {
                "status": "PASS",
                "checked_from": "separate_worker_context",
                "refs": [
                    {
                        "ref": ref,
                        "readable": True,
                        "sha256": "sha256:" + "0" * 64,
                    }
                ],
            }
            results_dir.joinpath("codex-security.json").write_text(
                factoryctl.json.dumps(security, indent=2) + "\n",
                encoding="utf-8",
            )

            index = evidence_reconciler.reconcile(card, results_dir)

        self.assertTrue(index["receipt_five_ready"])
        self.assertEqual(
            index["effective_results"]["security_scan_result"]["validation_errors"],
            [],
        )

    def test_native_kanban_attachment_ref_requires_full_readback(self) -> None:
        card = closure_card()
        ref = "kanban-attachment:t_fixture/artifacts/security-proof.json"
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            results_dir = tmp_path / "worker-results"
            results_dir.mkdir()
            write_results(card, results_dir)
            security = result_for("codex-security", card, "2026-06-06T00:50:00+00:00")
            security["evidence_refs"] = [ref]
            security["artifact_readback"] = {
                "status": "PASS",
                "checked_from": "downstream_worker_context",
                "refs": [{"ref": ref, "readable": True, "sha256": "sha256:" + "0" * 64}],
            }
            results_dir.joinpath("codex-security.json").write_text(
                factoryctl.json.dumps(security, indent=2) + "\n",
                encoding="utf-8",
            )

            index = evidence_reconciler.reconcile(card, results_dir)

        security_result = index["effective_results"]["security_scan_result"]
        self.assertFalse(security_result["valid_for_closure"])
        self.assertIn(
            "artifact_readback.refs[kanban-attachment:t_fixture/artifacts/security-proof.json].attachment_row_seen must be true",
            security_result["validation_errors"],
        )

    def test_extra_result_path_is_indexed_with_worker_results(self) -> None:
        card = closure_card()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            results_dir = tmp_path / "worker-results"
            results_dir.mkdir()
            extra = tmp_path / "external-independent-review.json"
            extra.write_text(
                factoryctl.json.dumps(
                    result_for("independent-reviewer", card, "2026-06-06T00:10:00+00:00"),
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            index = evidence_reconciler.reconcile(card, results_dir, [extra])

        self.assertIn("independent_review_result", index["effective_results"])
        self.assertEqual(index["effective_results"]["independent_review_result"]["result"], "PASS")

    def test_receipt_draft_contains_required_transition_shape(self) -> None:
        card = closure_card()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)
            write_results(card, results_dir, skip_worker="codex-security")
            index = evidence_reconciler.reconcile(card, results_dir)

        draft = evidence_reconciler.build_receipt_draft(
            card,
            "reports/index.json",
            "reports/evidence-reconciler-result.json",
            index,
        )

        self.assertIn("next_action", draft["receipt_five"])
        self.assertIn("reviewer_required", draft["receipt_five"])
        self.assertIn("reviewer_result", draft["receipt_five"])
        self.assertEqual(draft["kanban_transition_event"]["from_status"], "review")
        self.assertEqual(draft["kanban_transition_event"]["actor"], "evidence-reconciler")
        self.assertEqual(draft["kanban_transition_event"]["worker"], "evidence-reconciler")
        self.assertIn("receipt_five_reconciliation_result", draft["kanban_transition_event"]["receipt_refs"])
        self.assertGreaterEqual(len(draft["kanban_transition_event"]["artifact_refs"]), 2)

        card_without_status = dict(card)
        card_without_status.pop("status", None)
        no_status_draft = evidence_reconciler.build_receipt_draft(
            card_without_status,
            "reports/index.json",
            "reports/evidence-reconciler-result.json",
            index,
        )
        self.assertEqual(no_status_draft["kanban_transition_event"]["from_status"], "receipt-five")

    def test_ready_receipt_draft_passes_completion_validation(self) -> None:
        card = closure_card()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)
            write_results(card, results_dir)
            index = evidence_reconciler.reconcile(card, results_dir)

        draft = evidence_reconciler.build_receipt_draft(
            card,
            "reports/index.json",
            "reports/evidence-reconciler-result.json",
            index,
        )

        self.assertTrue(index["receipt_five_ready"])
        self.assertFalse(draft["receipt_five"]["reviewer_required"])
        self.assertIn("independent_review_result", draft["worker_result_refs"])
        self.assertEqual(factoryctl.validate_completion(card, draft), [])

    def test_reconciler_preserves_sdlc_feedback_loop_refs(self) -> None:
        card = closure_card()
        card["sdlc_feedback_loop_ref"] = "templates/factory-sdlc-feedback-loop.json"
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)
            write_results(card, results_dir)
            index = evidence_reconciler.reconcile(card, results_dir)
            result = evidence_reconciler.build_reconciler_result(
                card,
                "reports/index.json",
                index,
            )

        draft = evidence_reconciler.build_receipt_draft(
            card,
            "reports/index.json",
            "reports/evidence-reconciler-result.json",
            index,
        )

        self.assertEqual(index["sdlc_feedback_loop_refs"], ["templates/factory-sdlc-feedback-loop.json"])
        self.assertEqual(result["sdlc_feedback_loop_refs"], ["templates/factory-sdlc-feedback-loop.json"])
        self.assertEqual(draft["sdlc_feedback_loop_refs"], ["templates/factory-sdlc-feedback-loop.json"])
        self.assertEqual(
            draft["receipt_five_reconciliation_result"]["sdlc_feedback_loop_refs"],
            ["templates/factory-sdlc-feedback-loop.json"],
        )
        self.assertEqual(
            draft["receipt_five"]["sdlc_feedback_loop_refs"],
            ["templates/factory-sdlc-feedback-loop.json"],
        )

    def test_receipt_five_schema_declares_sdlc_feedback_loop_refs(self) -> None:
        schema = json.loads((ROOT / "schemas" / "receipt-five.schema.json").read_text(encoding="utf-8"))

        self.assertIn("sdlc_feedback_loop_refs", schema["properties"])
        self.assertIn(
            "sdlc_feedback_loop_refs",
            schema["properties"]["receipt_five"]["properties"],
        )
        self.assertIn(
            "sdlc_feedback_loop_refs",
            schema["properties"]["receipt_five_reconciliation_result"]["properties"],
        )

    def test_worker_result_schema_declares_artifact_readback(self) -> None:
        schema = json.loads((ROOT / "schemas" / "worker-result.schema.json").read_text(encoding="utf-8"))

        self.assertIn("artifact_readback", schema["properties"])
        artifact_readback = schema["properties"]["artifact_readback"]
        self.assertIn("status", artifact_readback["required"])
        self.assertIn("checked_from", artifact_readback["required"])
        self.assertIn("refs", artifact_readback["required"])


if __name__ == "__main__":
    unittest.main()
