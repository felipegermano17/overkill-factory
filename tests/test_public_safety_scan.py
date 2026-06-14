from __future__ import annotations

import contextlib
import io
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "public_safety_scan.py"
SPEC = importlib.util.spec_from_file_location("public_safety_scan", MODULE_PATH)
assert SPEC is not None
public_safety_scan = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["public_safety_scan"] = public_safety_scan
SPEC.loader.exec_module(public_safety_scan)

PRIVATE_MARKER = "KA" + "XIS"


class PublicSafetyScanTest(unittest.TestCase):
    def test_scan_text_reports_private_marker(self) -> None:
        findings = public_safety_scan.scan_text("docs/example.md", f"private {PRIVATE_MARKER}")

        self.assertTrue(findings)
        self.assertIn("private_product_marker", findings[0])

    def test_negative_test_guard_allows_asserting_absence(self) -> None:
        line = 'self.assertNotIn("' + PRIVATE_MARKER + '", text)'

        self.assertEqual(public_safety_scan.scan_text("tests/example.py", line), [])

    def test_negative_fixture_guard_allows_declared_issue84_sample_only(self) -> None:
        blocked_ref = '  "ref": "' + "C:" + "\\\\Users\\\\operator\\\\raw-evidence.json" + '"'

        self.assertEqual(
            public_safety_scan.scan_text(
                "fixtures/issue-84/status-snapshot-v0/FX10-forbidden_evidence_ref_negative.json",
                blocked_ref,
            ),
            [],
        )
        self.assertTrue(public_safety_scan.scan_text("fixtures/issue-84/status-snapshot-v0/FX01-current_success_projection.json", blocked_ref))

    def test_blocks_literal_whimsical_board_id_in_public_command(self) -> None:
        board_id = "XV" + "vfzk"
        findings = public_safety_scan.scan_text(
            "docs/example.md",
            f"python scripts/whimsical_mcp.py snapshot --board-id {board_id}",
        )

        self.assertTrue(findings)
        self.assertIn("private_whimsical_board_marker", findings[0])

    def test_allows_placeholder_whimsical_board_id(self) -> None:
        findings = public_safety_scan.scan_text(
            "docs/example.md",
            "python scripts/whimsical_mcp.py snapshot --board-id <private-board-id>",
        )

        self.assertEqual(findings, [])


    def test_allows_canonical_public_repo_url_only_in_metadata(self) -> None:
        owner = "feli" + "pegermano17"
        repo_url = f"https://github.com/{owner}/overkill-factory"

        self.assertEqual(public_safety_scan.scan_text("pyproject.toml", f'Repository = "{repo_url}"'), [])
        self.assertEqual(public_safety_scan.scan_text("mkdocs.yml", f"repo_url: {repo_url}"), [])

        findings = public_safety_scan.scan_text("docs/example.md", f"See {repo_url}")
        self.assertTrue(findings)
        self.assertIn("private_owner_marker", findings[0])

        mixed_line = f"repo_url: {repo_url} C:" + "\\Users\\operator"
        findings = public_safety_scan.scan_text("mkdocs.yml", mixed_line)
        self.assertTrue(findings)
        self.assertIn("private_windows_path", findings[0])

    def test_generated_local_build_metadata_is_not_scanned(self) -> None:
        self.assertFalse(public_safety_scan.is_text_rel("overkill_factory.egg-info/PKG-INFO"))
        self.assertFalse(public_safety_scan.is_text_rel(".tmp/quickstart-result.json"))

    def test_git_ref_scan_checks_committed_tree(self) -> None:
        original_root = public_safety_scan.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "docs").mkdir()
            (repo / "docs" / "example.md").write_text(PRIVATE_MARKER, encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "-c",
                    "user.email=test@example.invalid",
                    "-c",
                    "user.name=Test",
                    "commit",
                    "-m",
                    "fixture",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            public_safety_scan.ROOT = repo
            try:
                findings = public_safety_scan.scan_git_ref("HEAD")
            finally:
                public_safety_scan.ROOT = original_root

        self.assertTrue(findings)

    def test_summary_does_not_expose_private_marker(self) -> None:
        findings = public_safety_scan.scan_text("docs/example.md", f"private {PRIVATE_MARKER}")
        summary = public_safety_scan.build_summary(
            findings,
            git_ref="HEAD",
            created_at="2026-06-10T00:00:00Z",
        )
        summary_text = json.dumps(summary)

        self.assertEqual(summary["result"], "FAIL")
        self.assertEqual(summary["finding_count"], 1)
        self.assertIn("private_product_marker", summary_text)
        self.assertNotIn(PRIVATE_MARKER, summary_text)

    def test_cli_writes_public_safe_summary_for_failing_git_ref_scan(self) -> None:
        original_root = public_safety_scan.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            summary = repo / "summary.json"
            (repo / "docs").mkdir()
            (repo / "docs" / "example.md").write_text(PRIVATE_MARKER, encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "-c",
                    "user.email=test@example.invalid",
                    "-c",
                    "user.name=Test",
                    "commit",
                    "-m",
                    "fixture",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            public_safety_scan.ROOT = repo
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    rc = public_safety_scan.main_with_args_for_test(
                        ["--git-ref", "HEAD", "--summary-json", str(summary)]
                    )
                summary_text = summary.read_text(encoding="utf-8")
            finally:
                public_safety_scan.ROOT = original_root

        summary_data = json.loads(summary_text)
        self.assertEqual(rc, 1)
        self.assertEqual(summary_data["result"], "FAIL")
        self.assertNotIn(PRIVATE_MARKER, summary_text)


if __name__ == "__main__":
    unittest.main()
