from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_github_issue_pattern_audit.py"
REGISTRY_PATH = ROOT / "templates" / "factory-github-issue-pattern-audit-registry.json"
SNAPSHOT_PATH = ROOT / ".tmp" / "github-issues-snapshot.json"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_github_issue_pattern_audit", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryGithubIssuePatternAuditTest(unittest.TestCase):
    def test_audit_passes_and_preserves_known_failure_patterns(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        report = module.audit(registry)

        self.assertEqual("PASS", report["result"])
        self.assertEqual(100, report["score"])
        self.assertGreaterEqual(report["summary"]["source_issue_count"], 250)
        self.assertGreaterEqual(report["summary"]["theme_count"], 10)
        self.assertGreaterEqual(report["summary"]["anti_regression_requirement_count"], 12)
        self.assertIn("operator_ux_friction", report["theme_keys"])
        self.assertIn("autonomy_idle_stop", report["theme_keys"])
        self.assertIn("runtime_kanban_worker", report["theme_keys"])
        self.assertIn("evidence_truth_overclaim", report["theme_keys"])

    def test_open_issues_are_recorded_as_current_attention(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        report = module.audit(registry)
        open_numbers = {issue["number"] for issue in registry["issue_snapshot_summary"]["open_issues"]}

        self.assertEqual({419, 529, 531}, open_numbers)
        self.assertEqual(open_numbers, set(report["open_issue_numbers"]))
        self.assertIn("global language policy", " ".join(issue["title"] for issue in registry["issue_snapshot_summary"]["open_issues"]).lower())

    def test_operator_experience_theme_has_specific_non_regression_rules(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        theme = next(item for item in registry["issue_pattern_themes"] if item["theme_key"] == "operator_ux_friction")
        rules = "\n".join(theme["anti_regression_requirements"]).lower()

        self.assertIn("manager-only", rules)
        self.assertIn("artifact-first", rules)
        self.assertIn("pt-br", rules)
        self.assertIn("human gate", rules)
        self.assertGreaterEqual(len(theme["representative_issues"]), 5)

    def test_audit_fails_when_issue_count_or_required_theme_is_removed(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        broken = json.loads(json.dumps(registry))
        broken["issue_snapshot_summary"]["issue_count"] = 42
        broken["issue_pattern_themes"] = [
            item for item in broken["issue_pattern_themes"] if item["theme_key"] != "autonomy_idle_stop"
        ]

        report = module.audit(broken)

        self.assertEqual("FAIL", report["result"])
        self.assertTrue(any("issue_count" in error for error in report["errors"]), report["errors"])
        self.assertTrue(any("autonomy_idle_stop" in error for error in report["errors"]), report["errors"])

    def test_audit_can_cross_check_private_snapshot_without_committing_raw_bodies(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        if not SNAPSHOT_PATH.exists():
            self.skipTest("local GitHub issue snapshot not present")
        snapshot = module.load_json(SNAPSHOT_PATH)
        report = module.audit(registry, snapshot=snapshot)

        self.assertEqual("PASS", report["result"])
        self.assertEqual(snapshot["issue_count"], registry["issue_snapshot_summary"]["issue_count"])
        self.assertFalse(registry["source_policy"]["raw_issue_bodies_committed"])

    def test_cli_writes_json_and_markdown(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "audit.json"
            md = Path(tmpdir) / "audit.md"
            exit_code = module.main([
                "--registry",
                str(REGISTRY_PATH),
                "--out",
                str(out),
                "--markdown",
                str(md),
            ])
            self.assertEqual(0, exit_code)
            payload = json.loads(out.read_text())
            text = md.read_text()
            self.assertEqual("PASS", payload["result"])
            self.assertIn("GitHub Issue Pattern Audit", text)
            self.assertIn("operator_ux_friction", text)
            self.assertIn("autonomy_idle_stop", text)
            self.assertIn("master plan", text.lower())


if __name__ == "__main__":
    unittest.main()
