from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "crabbox_local_container_remote_proof.py"
SPEC = importlib.util.spec_from_file_location("crabbox_local_container_remote_proof", SCRIPT)
assert SPEC is not None
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["crabbox_local_container_remote_proof"] = module
SPEC.loader.exec_module(module)


class CrabboxLocalContainerRemoteProofTest(unittest.TestCase):
    def test_parse_timing_json_from_combined_output(self) -> None:
        stdout = "OK\n"
        runtime_path = "/srv/" + "hermes" + "/workspaces/overkill-factory"
        stderr = (
            'run details\n{"provider":"local-container","exitCode":0,'
            f'"leaseStopped":true,"repoPath":"{runtime_path}"}}\n'
        )

        timing = module.parse_timing_json(stdout, stderr)

        self.assertEqual(timing["provider"], "local-container")
        self.assertTrue(timing["leaseStopped"])
        self.assertNotIn("/srv/" + "hermes", str(timing))

    def test_build_result_requires_cleanup_and_zero_exit(self) -> None:
        completed = subprocess.CompletedProcess(
            ["crabbox"],
            0,
            stdout=(
                "OK\n"
                "OF_REMOTE_PROOF_CHECK public_json_artifacts PASS\n"
                "OF_REMOTE_PROOF_CHECK secret_safety PASS\n"
                "OF_REMOTE_PROOF_CHECK public_safety PASS\n"
                "OF_REMOTE_PROOF_CHECK supply_chain PASS\n"
                "OF_REMOTE_PROOF_CHECK full_product_worker_graph PASS\n"
            ),
            stderr="",
        )
        timing = {
            "provider": "local-container",
            "exitCode": 0,
            "leaseStopped": True,
            "leaseId": "cbx_test",
            "slug": "test",
            "totalMs": 1,
        }

        result = module.build_result(
            crabbox_version="0.26.0",
            command=module.DEFAULT_COMMAND,
            completed=completed,
            timing=timing,
            active_leases_after=0,
            lease_list_output="",
        )

        self.assertEqual(result["result"], "PASS")
        self.assertTrue(result["reusable_for_product"])
        self.assertEqual(result["provider"], "local-container")
        self.assertTrue(result["proof_checks"]["all_required_passed"])
        self.assertTrue(result["cleanup_evidence"]["all_cleanup_confirmed"])

    def test_build_result_fails_when_required_marker_is_missing(self) -> None:
        completed = subprocess.CompletedProcess(
            ["crabbox"],
            0,
            stdout=(
                "OK\nOK\nOK\nPASS\n"
                "OF_REMOTE_PROOF_CHECK public_json_artifacts PASS\n"
                "OF_REMOTE_PROOF_CHECK secret_safety PASS\n"
                "OF_REMOTE_PROOF_CHECK public_safety PASS\n"
                "OF_REMOTE_PROOF_CHECK full_product_worker_graph PASS\n"
            ),
            stderr="",
        )
        timing = {"provider": "local-container", "exitCode": 0, "leaseStopped": True}

        result = module.build_result(
            crabbox_version="0.26.0",
            command=module.DEFAULT_COMMAND,
            completed=completed,
            timing=timing,
            active_leases_after=0,
            lease_list_output="",
        )

        self.assertEqual(result["result"], "FAIL")
        self.assertIn("supply_chain", result["proof_checks"]["missing_markers"])
        self.assertFalse(result["reusable_for_product"])

    def test_build_result_fails_when_lease_is_not_stopped(self) -> None:
        completed = subprocess.CompletedProcess(
            ["crabbox"],
            0,
            stdout=(
                "OF_REMOTE_PROOF_CHECK public_json_artifacts PASS\n"
                "OF_REMOTE_PROOF_CHECK secret_safety PASS\n"
                "OF_REMOTE_PROOF_CHECK public_safety PASS\n"
                "OF_REMOTE_PROOF_CHECK supply_chain PASS\n"
                "OF_REMOTE_PROOF_CHECK full_product_worker_graph PASS\n"
            ),
            stderr="",
        )
        timing = {"provider": "local-container", "exitCode": 0, "leaseStopped": False}

        result = module.build_result(
            crabbox_version="0.26.0",
            command=module.DEFAULT_COMMAND,
            completed=completed,
            timing=timing,
            active_leases_after=0,
            lease_list_output="",
        )

        self.assertEqual(result["result"], "FAIL")
        self.assertFalse(result["reusable_for_product"])

    def test_build_result_fails_when_cleanup_count_is_unknown(self) -> None:
        completed = subprocess.CompletedProcess(
            ["crabbox"],
            0,
            stdout=(
                "OF_REMOTE_PROOF_CHECK public_json_artifacts PASS\n"
                "OF_REMOTE_PROOF_CHECK secret_safety PASS\n"
                "OF_REMOTE_PROOF_CHECK public_safety PASS\n"
                "OF_REMOTE_PROOF_CHECK supply_chain PASS\n"
                "OF_REMOTE_PROOF_CHECK full_product_worker_graph PASS\n"
            ),
            stderr="",
        )
        timing = {"provider": "local-container", "exitCode": 0, "leaseStopped": True}

        result = module.build_result(
            crabbox_version="0.26.0",
            command=module.DEFAULT_COMMAND,
            completed=completed,
            timing=timing,
            active_leases_after=None,
            lease_list_output="crabbox list failed",
        )

        self.assertEqual(result["result"], "FAIL")
        self.assertFalse(result["cleanup_evidence"]["active_lease_count_known"])
        self.assertFalse(result["cleanup_evidence"]["all_cleanup_confirmed"])
        self.assertFalse(result["reusable_for_product"])


if __name__ == "__main__":
    unittest.main()
