from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_master_update_plan_audit.py"
REGISTRY_PATH = ROOT / "templates" / "factory-master-update-plan.json"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_master_update_plan_audit", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryMasterUpdatePlanTest(unittest.TestCase):
    def test_master_plan_covers_all_audits_and_waves(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        report = module.audit(registry)

        self.assertEqual("PASS", report["result"])
        self.assertEqual(100, report["score"])
        self.assertEqual(8, report["summary"]["audit_input_count"])
        self.assertGreaterEqual(report["summary"]["workstream_count"], 10)
        self.assertEqual("V3", report["release_target"])
        self.assertTrue(report["principles"]["hermes_first"])
        self.assertTrue(report["principles"]["kanban_first"])
        self.assertTrue(report["principles"]["no_mini_hermes"])

    def test_master_plan_has_no_mini_hermes_boundaries(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        report = module.audit(registry)

        forbidden = registry["runtime_boundary"]["factory_must_not_own"]
        allowed = registry["runtime_boundary"]["factory_may_own"]
        forbidden_text = "\n".join(forbidden).lower()
        allowed_text = "\n".join(allowed).lower()

        self.assertEqual("PASS", report["result"])
        for term in ("scheduler", "queue", "board", "dispatch", "task lifecycle"):
            self.assertIn(term, forbidden_text)
        for term in ("method", "gate", "rule", "audit", "contract"):
            self.assertIn(term, allowed_text)

    def test_manager_and_agent_freshness_is_first_order_workstream(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        workstream = next(item for item in registry["workstreams"] if item["id"] == "W03-manager-agent-freshness")
        requirements = "\n".join(workstream["requirements"]).lower()
        evidence = "\n".join(workstream["required_evidence"]).lower()

        self.assertEqual("P0", workstream["priority"])
        self.assertIn("gerente", requirements)
        self.assertIn("skills", requirements)
        self.assertIn("profiles", requirements)
        self.assertIn("bindings", requirements)
        self.assertIn("smoke", evidence)
        self.assertIn("factory code", evidence)

    def test_public_github_surface_and_v3_release_are_required(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        workstream = next(item for item in registry["workstreams"] if item["id"] == "W09-public-github-v3")
        requirements = "\n".join(workstream["requirements"]).lower()

        self.assertEqual("V3", registry["release_target"])
        self.assertIn("readme", requirements)
        self.assertIn("public map", requirements)
        self.assertIn("first-value", requirements)
        self.assertIn("release notes", requirements)
        self.assertIn("open source", requirements)

    def test_breaks_when_required_audit_or_workstream_is_missing(self) -> None:
        module = load_module()
        registry = module.load_json(REGISTRY_PATH)
        broken = json.loads(json.dumps(registry))
        broken["audit_inputs"] = [item for item in broken["audit_inputs"] if item["id"] != "github_issue_pattern_audit"]
        broken["workstreams"] = [item for item in broken["workstreams"] if item["id"] != "W01-runtime-truth-spine"]

        report = module.audit(broken)

        self.assertEqual("FAIL", report["result"])
        self.assertTrue(any("github_issue_pattern_audit" in err for err in report["errors"]), report["errors"])
        self.assertTrue(any("W01-runtime-truth-spine" in err for err in report["errors"]), report["errors"])

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
            self.assertIn("Factory Master Update Plan", text)
            self.assertIn("Hermes-first", text)
            self.assertIn("W09-public-github-v3", text)


if __name__ == "__main__":
    unittest.main()
