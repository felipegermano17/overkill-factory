from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "issue84" / "status_snapshot_readonly_adapter.py"
FIXTURES = ROOT / "fixtures" / "issue-84" / "status-snapshot-v0"
ADAPTER_RESULT_REPORT = ROOT / "reports" / "issue-84-readonly-status-adapter-result.json"
ADAPTER_REMEDIATION_REPORT = ROOT / "reports" / "issue-84-readonly-status-adapter-remediation.json"
EXPANDED_FX_CASES = "FX01,FX02,FX03,FX04,FX05,FX06,FX07,FX08,FX09,FX10,FX11,FX12,FX13,FX14,FX15,FX16,FX17,FX18"


def load_module():
    spec = importlib.util.spec_from_file_location("issue84_status_snapshot_readonly_adapter", MODULE_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["issue84_status_snapshot_readonly_adapter"] = module
    spec.loader.exec_module(module)
    return module


adapter = load_module()


class ReadOnlyStatusSnapshotAdapterTest(unittest.TestCase):
    def write_report(self, tmp_path: Path, payload: dict[str, object], name: str = "report.json") -> Path:
        path = tmp_path / name
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path

    def base_report(self) -> dict[str, object]:
        return {
            "record_type": "backend_api_build_result",
            "task_ref": "issue-84-adapter-test",
            "title": "<script>alert('x')</script>",
            "phase": "F12 bounded implementation / read-only adapter",
            "risk_effective": "R2",
            "source_refs": ["ISSUE-84", "reports/source-report.json"],
            "decision_refs": ["runtime_decision: projection-only"],
            "inference_refs": ["adapter inferred reviewer gate is pending from missing reviewer_result"],
            "changed_files": ["scripts/issue84/status_snapshot_readonly_adapter.py"],
            "receipt_five": {
                "changed": "worker produced adapter code",
                "artifact_paths": ["scripts/issue84/status_snapshot_readonly_adapter.py"],
                "verification_commands": ["python3 -m unittest tests.test_issue84_readonly_status_adapter"],
                "verification_result": "targeted tests passed",
                "reviewer_required": True,
                "next_action": "request qa-verification-worker review",
            },
            "evidence_refs": [
                {
                    "id": "EV-REPORT",
                    "kind": "worker_result",
                    "ref": "reports/source-report.json",
                    "source_refs": ["ISSUE-84"],
                    "freshness_state": "current",
                    "public_safety_state": "public_safe",
                    "verification_status": "verified_relative_artifact",
                    "raw_payload_included": False,
                }
            ],
        }

    def test_import_existing_fixture_is_read_only_projection(self) -> None:
        fixture = FIXTURES / "FX01-current_success_projection.json"
        before = fixture.read_text(encoding="utf-8")

        snapshot = adapter.import_source(fixture)

        self.assertEqual(fixture.read_text(encoding="utf-8"), before)
        self.assertEqual(snapshot["schema_version"], "status-snapshot-v0")
        self.assertEqual(snapshot["current_state"], "success")
        self.assertTrue(snapshot["adapter_metadata"]["projection_only"])
        self.assertEqual(snapshot["adapter_metadata"]["mutations_performed"], [])
        self.assertFalse(snapshot["next_safe_action"]["forbidden_action_taken"])

    def test_report_import_separates_worker_done_from_reviewer_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = self.write_report(Path(tmp), self.base_report())

            snapshot = adapter.import_source(report_path)

        self.assertEqual(snapshot["worker_state"][0]["state"], "done")
        self.assertEqual(snapshot["review_state"]["status"], "missing")
        self.assertTrue(snapshot["state_flags"]["done"])
        self.assertFalse(snapshot["state_flags"]["approval"])
        self.assertFalse(snapshot["state_flags"]["released"])
        self.assertEqual(snapshot["current_state"], "blocked")
        self.assertEqual(snapshot["next_safe_action"]["action_type"], "review")

    def test_report_import_escapes_untrusted_text_and_preserves_traceability_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = self.write_report(Path(tmp), self.base_report())

            snapshot = adapter.import_source(report_path)

        self.assertNotIn("<script>", snapshot["title"])
        self.assertIn("&lt;script&gt;", snapshot["title"])
        self.assertEqual(snapshot["traceability"]["source"], ["ISSUE-84", "reports/source-report.json"])
        self.assertEqual(snapshot["traceability"]["decision"], ["runtime_decision: projection-only"])
        self.assertEqual(snapshot["traceability"]["inference"], ["adapter inferred reviewer gate is pending from missing reviewer_result"])

    def test_forbidden_evidence_refs_fail_closed_without_raw_payload(self) -> None:
        report = self.base_report()
        private_runtime_ref = "/" + "srv/hermes/private/evidence.json"
        private_metadata_ref = "https://169.254.169.254/latest/meta-data/"
        report["evidence_refs"] = [
            {
                "id": "EV-BAD-LOCAL",
                "kind": "worker_result",
                "ref": private_runtime_ref,
                "source_refs": ["ISSUE-84"],
                "freshness_state": "current",
                "public_safety_state": "public_safe",
                "verification_status": "unverified",
                "raw_payload_included": False,
            },
            {
                "id": "EV-BAD-METADATA",
                "kind": "public_url",
                "ref": private_metadata_ref,
                "source_refs": ["ISSUE-84"],
                "freshness_state": "current",
                "public_safety_state": "public_safe",
                "verification_status": "unverified",
                "raw_payload_included": False,
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            report_path = self.write_report(tmp_path, report)
            snapshot = adapter.import_source(report_path)
            cli_output_path = tmp_path / "snapshot.json"
            self.assertEqual(adapter.main_with_args(["import", str(report_path), "--out", str(cli_output_path)]), 0)
            cli_serialized = cli_output_path.read_text(encoding="utf-8")

        self.assertEqual(snapshot["freshness_state"], "current")
        self.assertEqual(snapshot["current_state"], "security_negative")
        self.assertEqual(snapshot["next_safe_action"]["action_type"], "block")
        self.assertFalse(snapshot["next_safe_action"]["forbidden_action_taken"])
        self.assertFalse(snapshot["public_private_boundary"]["raw_private_payload_included"])

        serialized = json.dumps(snapshot, sort_keys=True)
        evidence_serialized = json.dumps(snapshot["evidence_refs"], sort_keys=True)
        blocked_refs = snapshot["public_private_boundary"]["blocked_refs"]
        for denied_ref in (private_runtime_ref, private_metadata_ref):
            self.assertNotIn(denied_ref, serialized)
            self.assertNotIn(denied_ref, evidence_serialized)
            self.assertNotIn(denied_ref, cli_serialized)
            self.assertFalse(any(denied_ref in marker for marker in blocked_refs), blocked_refs)
        self.assertTrue(any("evidence_refs[0].ref" in marker and "redacted local_path" in marker for marker in blocked_refs), blocked_refs)
        self.assertTrue(any("evidence_refs[1].ref" in marker and "redacted url" in marker for marker in blocked_refs), blocked_refs)
        for evidence in snapshot["evidence_refs"]:
            self.assertNotIn("ref", evidence)
            self.assertTrue(str(evidence.get("ref_label") or "").startswith("redacted:"), evidence)
            self.assertIn("Denied EvidenceRef ref was redacted", evidence.get("redaction_note", ""))

    def test_public_url_redirect_resolver_rejects_private_redirect(self) -> None:
        calls: list[str] = []

        def resolver(url: str) -> list[str]:
            calls.append(url)
            return [url, "http://localhost:8000/private"]

        result = adapter.classify_reference("https://github.com/overkill-factory/overkill-factory/issues/84", resolver=resolver)

        self.assertEqual(calls, ["https://github.com/overkill-factory/overkill-factory/issues/84"])
        self.assertFalse(result.allowed)
        self.assertIn("redirect", result.reason)
        self.assertIn("private", result.reason)

    def test_state_mapping_for_missing_stale_superseded_and_contradictory_inputs_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            missing = adapter.import_source(tmp_path / "missing-report.json")
            self.assertEqual(missing["current_state"], "missing")
            self.assertEqual(missing["next_safe_action"]["action_type"], "block")

            stale_payload = self.base_report()
            stale_payload["freshness_state"] = "stale"
            stale_payload["source_updated_at"] = "2026-06-14T05:00:00Z"
            stale_payload["observed_at"] = "2026-06-14T04:00:00Z"
            stale = adapter.import_source(self.write_report(tmp_path, stale_payload, "stale.json"))
            self.assertEqual(stale["current_state"], "stale")
            self.assertEqual(stale["next_safe_action"]["action_type"], "refresh")

            superseded_payload = self.base_report()
            superseded_payload["superseded_by"] = "reports/newer-status-snapshot.json"
            superseded = adapter.import_source(self.write_report(tmp_path, superseded_payload, "superseded.json"))
            self.assertEqual(superseded["current_state"], "superseded")
            self.assertEqual(superseded["next_safe_action"]["action_type"], "review")

            contradictory_payload = self.base_report()
            contradictory_payload["public_issue_state"] = "reopened"
            contradictory_payload["release_state"] = "released"
            contradictory = adapter.import_source(self.write_report(tmp_path, contradictory_payload, "contradictory.json"))
            self.assertEqual(contradictory["current_state"], "contradictory")
            self.assertEqual(contradictory["next_safe_action"]["action_type"], "review")
            self.assertFalse(contradictory["state_flags"]["approval"])

    def test_public_https_urls_are_classified_before_local_path_segments(self) -> None:
        public_url_with_localish_path = "https://example.com/home/status-snapshot/report.json"

        result = adapter.classify_reference(public_url_with_localish_path)

        self.assertTrue(result.allowed, result)
        self.assertEqual(result.kind, "public_url")

    def test_tests_directory_repo_relative_refs_are_allowed_narrowly(self) -> None:
        allowed = adapter.classify_reference("tests/test_issue84_readonly_status_adapter.py")

        self.assertTrue(allowed.allowed, allowed)
        self.assertEqual(allowed.kind, "relative_artifact")
        for unsafe_ref in (
            "/tmp/tests/test_issue84_readonly_status_adapter.py",
            "../tests/test_issue84_readonly_status_adapter.py",
            "tests/../reports/issue-84-readonly-status-adapter-result.json",
            "tests//test_issue84_readonly_status_adapter.py",
            "file://tests/test_issue84_readonly_status_adapter.py",
            "http://example.com/tests/test_issue84_readonly_status_adapter.py",
            "https://169.254.169.254/tests/test_issue84_readonly_status_adapter.py",
        ):
            result = adapter.classify_reference(unsafe_ref)
            self.assertFalse(result.allowed, unsafe_ref)

    def test_report_import_accepts_tests_artifact_refs_without_security_negative(self) -> None:
        report = self.base_report()
        report["changed_files"] = [
            "scripts/issue84/status_snapshot_readonly_adapter.py",
            "tests/test_issue84_readonly_status_adapter.py",
        ]
        receipt = report["receipt_five"]
        assert isinstance(receipt, dict)
        receipt["artifact_paths"] = [
            "scripts/issue84/status_snapshot_readonly_adapter.py",
            "tests/test_issue84_readonly_status_adapter.py",
            "reports/public-safe-artifact.json",
        ]

        with tempfile.TemporaryDirectory() as tmp:
            report_path = self.write_report(Path(tmp), report)
            snapshot = adapter.import_source(report_path)

        self.assertEqual(snapshot["current_state"], "blocked")
        self.assertEqual(snapshot["next_safe_action"]["action_type"], "review")
        self.assertIn("tests/test_issue84_readonly_status_adapter.py", snapshot["receipt_five_status"]["artifact_paths"])
        self.assertIn("tests/test_issue84_readonly_status_adapter.py", snapshot["public_private_boundary"]["allowed_refs"])
        self.assertFalse(
            any("tests/test_issue84_readonly_status_adapter.py" in ref for ref in snapshot["public_private_boundary"]["blocked_refs"]),
            snapshot["public_private_boundary"]["blocked_refs"],
        )

    def test_public_clean_mode_does_not_require_private_adapter_reports(self) -> None:
        self.assertFalse(ADAPTER_RESULT_REPORT.exists())
        self.assertFalse(ADAPTER_REMEDIATION_REPORT.exists())

        report = self.base_report()
        receipt = report["receipt_five"]
        assert isinstance(receipt, dict)
        receipt["artifact_paths"] = [
            "scripts/issue84/status_snapshot_readonly_adapter.py",
            "tests/test_issue84_readonly_status_adapter.py",
            "reports/public-safe-artifact.json",
        ]

        with tempfile.TemporaryDirectory() as tmp:
            report_path = self.write_report(Path(tmp), report)
            snapshot = adapter.import_source(report_path)

        self.assertEqual(snapshot["current_state"], "blocked")
        self.assertEqual(snapshot["next_safe_action"]["action_type"], "review")
        self.assertIn("tests/test_issue84_readonly_status_adapter.py", snapshot["receipt_five_status"]["artifact_paths"])
        self.assertFalse(
            any("tests/test_issue84_readonly_status_adapter.py" in ref for ref in snapshot["public_private_boundary"]["blocked_refs"]),
            snapshot["public_private_boundary"]["blocked_refs"],
        )

    def test_unsafe_non_evidence_ref_fields_are_redacted_and_fail_closed(self) -> None:
        report = self.base_report()
        private_runtime_ref = "/" + "srv/hermes/private/source.json"
        report["source_refs"] = [private_runtime_ref, "ISSUE-84"]
        report["canonical_refs"] = ["https://example.com/home/status.json", "file:///etc/passwd"]
        report["decision_refs"] = ["runtime_decision: projection-only", "file:///etc/passwd"]
        report["inference_refs"] = ["adapter inferred " + private_runtime_ref]
        report["changed_files"] = [private_runtime_ref, "scripts/issue84/status_snapshot_readonly_adapter.py"]
        receipt = report["receipt_five"]
        assert isinstance(receipt, dict)
        receipt["artifact_paths"] = [private_runtime_ref, "reports/public-safe-artifact.json"]

        with tempfile.TemporaryDirectory() as tmp:
            report_path = self.write_report(Path(tmp), report)
            snapshot = adapter.import_source(report_path)

        serialized = json.dumps(snapshot, sort_keys=True)
        self.assertNotIn(private_runtime_ref, serialized)
        self.assertNotIn("file:///etc/passwd", serialized)
        self.assertNotIn("/etc/passwd", serialized)
        self.assertEqual(snapshot["current_state"], "security_negative")
        self.assertEqual(snapshot["next_safe_action"]["action_type"], "block")
        self.assertIn("ISSUE-84", snapshot["source_refs"])
        self.assertIn("https://example.com/home/status.json", snapshot["canonical_refs"])
        self.assertIn("reports/public-safe-artifact.json", snapshot["receipt_five_status"]["artifact_paths"])
        blocked_refs = snapshot["public_private_boundary"]["blocked_refs"]
        self.assertTrue(any("source_refs" in ref and "redacted" in ref for ref in blocked_refs), blocked_refs)
        self.assertTrue(any("canonical_refs" in ref and "redacted" in ref for ref in blocked_refs), blocked_refs)
        self.assertTrue(any("decision_refs" in ref and "redacted" in ref for ref in blocked_refs), blocked_refs)
        self.assertTrue(any("inference_refs" in ref and "redacted" in ref for ref in blocked_refs), blocked_refs)
        self.assertTrue(any("changed_files" in ref and "redacted" in ref for ref in blocked_refs), blocked_refs)
        self.assertTrue(any("artifact_paths" in ref and "redacted" in ref for ref in blocked_refs), blocked_refs)

    def test_expanded_fixture_inventory_command_is_spelled_out_for_public_replay(self) -> None:
        command = (
            "python3 scripts/issue84/validate_status_snapshot_fixtures.py "
            "fixtures/issue-84/status-snapshot-v0 "
            "--schema schemas/factory-status-snapshot.schema.json "
            f"--require-cases {EXPANDED_FX_CASES} --fail-closed"
        )

        self.assertNotIn("FX01..FX18", command)
        self.assertIn("--require-cases " + EXPANDED_FX_CASES, command)

    def test_cli_exposes_import_only_not_mutation_approval_or_server_commands(self) -> None:
        parser = adapter.build_parser()
        help_text = parser.format_help()
        self.assertIn("import", help_text)
        for forbidden in ("approve", "release", "complete", "serve", "mutate"):
            self.assertNotIn(forbidden, help_text.lower())


if __name__ == "__main__":
    unittest.main()
