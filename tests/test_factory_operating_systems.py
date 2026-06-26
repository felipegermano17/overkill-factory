from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factoryctl.py"
SPEC = importlib.util.spec_from_file_location("factoryctl", MODULE_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl"] = factoryctl
SPEC.loader.exec_module(factoryctl)


class FactoryOperatingSystemsTest(unittest.TestCase):
    def load_registry(self) -> dict:
        return factoryctl.load_json_like(ROOT / "templates" / "factory-operating-system-registry.json")

    def test_template_registry_validates(self) -> None:
        registry = self.load_registry()
        self.assertEqual([], factoryctl.validate_operating_system_registry(registry))

    def test_missing_p0_os_fails_closed(self) -> None:
        registry = self.load_registry()
        registry["entries"] = [
            entry
            for entry in registry["entries"]
            if entry["os_id"] != "hermes_worker_runtime_os"
        ]

        errors = factoryctl.validate_operating_system_registry(registry)

        self.assertTrue(any("hermes_worker_runtime_os" in error for error in errors), errors)

    def test_registry_cannot_claim_product_specific_production(self) -> None:
        registry = self.load_registry()
        registry["completion_claim_policy"]["product_specific_production_claim_allowed"] = True

        errors = factoryctl.validate_operating_system_registry(registry)

        self.assertTrue(any("product_specific_production_claim_allowed" in error for error in errors), errors)

    def test_scorecard_blocks_until_hermes_runtime_is_proven(self) -> None:
        registry = self.load_registry()
        scorecard = factoryctl.build_operating_system_scorecard(registry)

        self.assertEqual("BLOCKED", scorecard["result"])
        self.assertIn("hermes_worker_runtime_os", scorecard["p0_blocked"])
        self.assertNotIn("method_os", scorecard["p0_blocked"])
        self.assertEqual([], factoryctl.validate_operating_system_scorecard(scorecard))

    def test_scorecard_accepts_valid_hermes_runtime_proof(self) -> None:
        registry = self.load_registry()
        proof = {
            "record_type": "hermes_production_proof",
            "proof_type": "non_stub_worker_execution",
            "result": "PASS",
            "runtime_summary": {
                "gateway_running": True,
                "openai_codex_logged_in": True,
                "telegram_configured": True,
                "manager_profile_running": True,
                "current_board_detected": True,
                "live_worker_orchestration_proven": True,
                "human_gate_block_event_detected": True,
                "profile_count": 10,
                "current_board_total_tasks": 3,
            },
            "operator_gate_boundary": {
                "human_gate_auto_approved": False,
                "bridge_or_manager_executed_gate": False,
            },
        }

        scorecard = factoryctl.build_operating_system_scorecard(
            registry,
            runtime_proofs=[proof],
            runtime_proof_refs=["external:redacted-hermes-runtime-proof"],
        )
        hermes_result = next(item for item in scorecard["os_results"] if item["os_id"] == "hermes_worker_runtime_os")

        self.assertEqual("PASS", scorecard["result"])
        self.assertEqual([], scorecard["p0_blocked"])
        self.assertEqual("PROVEN", hermes_result["runtime_proof_state"])
        self.assertEqual([], factoryctl.validate_operating_system_scorecard(scorecard))

    def test_active_os_requires_existing_enforcement_commands_and_tests(self) -> None:
        registry = self.load_registry()
        entry = next(item for item in registry["entries"] if item["os_id"] == "operator_experience_os")
        entry["enforcement_command_refs"].append("factoryctl imaginary-command")
        entry["validation_test_refs"].append("tests/missing_operator_experience_test.py")

        errors = factoryctl.validate_operating_system_registry(registry)

        self.assertTrue(any("unknown factoryctl command" in error for error in errors), errors)
        self.assertTrue(any("missing_operator_experience_test.py" in error for error in errors), errors)

    def test_active_os_validation_tests_must_live_under_tests(self) -> None:
        registry = self.load_registry()
        entry = next(item for item in registry["entries"] if item["os_id"] == "method_os")
        entry["validation_test_refs"] = ["docs/not-a-test.md"]

        errors = factoryctl.validate_operating_system_registry(registry)

        self.assertTrue(any("must live under tests/" in error for error in errors), errors)

    def test_scorecard_maps_completion_audit_blockers_to_os(self) -> None:
        registry = self.load_registry()
        completion_audit = {
            "requirements": [
                {
                    "id": "hermes_real_worker_orchestration",
                    "blocking": True,
                    "status": "BLOCKED_MISSING_EVIDENCE",
                }
            ]
        }

        scorecard = factoryctl.build_operating_system_scorecard(registry, completion_audit=completion_audit)
        hermes_result = next(item for item in scorecard["os_results"] if item["os_id"] == "hermes_worker_runtime_os")

        self.assertIn("hermes_real_worker_orchestration", hermes_result["active_completion_audit_blockers"])

    def test_scorecard_cannot_claim_product_specific_production(self) -> None:
        registry = self.load_registry()
        scorecard = factoryctl.build_operating_system_scorecard(registry)
        scorecard["completion_claim_policy"]["product_specific_production_claim_allowed"] = True

        errors = factoryctl.validate_operating_system_scorecard(scorecard)

        self.assertTrue(any("product_specific_production_claim_allowed" in error for error in errors), errors)

    def test_cli_can_emit_single_operating_system(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "os.json"
            old_argv = sys.argv[:]
            sys.argv = [
                "factoryctl",
                "operating-systems",
                "--os-id",
                "method_os",
                "--out",
                str(out),
            ]
            try:
                code = factoryctl.main()
            finally:
                sys.argv = old_argv

            self.assertEqual(0, code)
            emitted = factoryctl.load_json_like(out)
            self.assertEqual("method_os", emitted["os_id"])
            self.assertEqual(402, emitted["issue_number"])

    def test_cli_rejects_unknown_operating_system(self) -> None:
        old_argv = sys.argv[:]
        sys.argv = ["factoryctl", "operating-systems", "--os-id", "unknown_os"]
        try:
            code = factoryctl.main()
        finally:
            sys.argv = old_argv

        self.assertEqual(1, code)

    def test_cli_scorecard_writes_blocked_artifact_and_returns_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "scorecard.json"
            old_argv = sys.argv[:]
            sys.argv = [
                "factoryctl",
                "operating-system-scorecard",
                "--out",
                str(out),
            ]
            try:
                code = factoryctl.main()
            finally:
                sys.argv = old_argv

            self.assertEqual(1, code)
            emitted = factoryctl.load_json_like(out)
            self.assertEqual("BLOCKED", emitted["result"])


if __name__ == "__main__":
    unittest.main()
