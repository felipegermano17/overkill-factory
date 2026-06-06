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
        stderr = 'run details\n{"provider":"local-container","exitCode":0,"leaseStopped":true}\n'

        timing = module.parse_timing_json(stdout, stderr)

        self.assertEqual(timing["provider"], "local-container")
        self.assertTrue(timing["leaseStopped"])

    def test_build_result_requires_cleanup_and_zero_exit(self) -> None:
        completed = subprocess.CompletedProcess(
            ["crabbox"],
            0,
            stdout=(
                "OK\nOK\nOK\n"
                "python3 scripts/validate_public_json_artifacts.py\n"
                "python3 scripts/full_product_worker_graph.py --require-pass\n"
                "PASS\n"
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

    def test_build_result_fails_when_lease_is_not_stopped(self) -> None:
        completed = subprocess.CompletedProcess(
            ["crabbox"],
            0,
            stdout=(
                "OK\nOK\nOK\n"
                "python3 scripts/validate_public_json_artifacts.py\n"
                "python3 scripts/full_product_worker_graph.py --require-pass\n"
                "PASS\n"
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


if __name__ == "__main__":
    unittest.main()
