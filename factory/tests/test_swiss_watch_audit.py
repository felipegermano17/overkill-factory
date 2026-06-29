from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("swiss_watch_audit", ROOT / "scripts" / "swiss_watch_audit.py")
assert SPEC is not None
swiss_watch_audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(swiss_watch_audit)


class SwissWatchAuditTests(unittest.TestCase):
    def test_audit_materializes_reliability_scorecard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "swiss-watch-audit.json"
            md = Path(tmp) / "swiss-watch-audit.md"
            self.assertEqual(
                swiss_watch_audit.main(
                    [
                        "--created-at",
                        "2026-06-28T00:00:00+00:00",
                        "--out",
                        str(out),
                        "--markdown",
                        str(md),
                    ]
                ),
                0,
            )
            audit = json.loads(out.read_text(encoding="utf-8"))
            markdown_text = md.read_text(encoding="utf-8")

        self.assertEqual(audit["record_type"], "swiss_watch_reliability_audit")
        self.assertEqual(audit["result"], "PASS")
        self.assertTrue(audit["rule_zero"]["factory_must_not_become_mini_hermes"])
        self.assertIn("kanban", audit["rule_zero"]["prefer_hermes_native_primitives"])
        self.assertEqual(audit["summary"]["runtime_authority"], "hermes_kanban")
        self.assertEqual(audit["summary"]["failing_phase_count"], 0)
        self.assertIn("mini-Hermes", markdown_text)

    def test_audit_rejects_missing_rule_zero(self) -> None:
        audit = swiss_watch_audit.build_audit(
            swiss_watch_audit.factoryctl.load_json_like(ROOT / "templates" / "factory-workflow-compiled-plan.json"),
            swiss_watch_audit.factoryctl.load_json_like(ROOT / "templates" / "hermes-typed-block-policy.json"),
            swiss_watch_audit.factoryctl.load_json_like(ROOT / "agents" / "worker-registry.public.json"),
            created_at="2026-06-28T00:00:00+00:00",
        )
        audit["rule_zero"]["factory_must_not_become_mini_hermes"] = False

        errors = swiss_watch_audit.validate_audit(audit)

        self.assertIn("rule_zero.factory_must_not_become_mini_hermes must be true", errors)


if __name__ == "__main__":
    unittest.main()
