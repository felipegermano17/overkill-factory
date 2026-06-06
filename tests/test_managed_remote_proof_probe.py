import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import managed_remote_proof_probe as probe


class ManagedRemoteProofProbeTests(unittest.TestCase):
    def test_probe_does_not_claim_product_reuse_or_completion(self):
        result = probe.build_probe()

        self.assertEqual(result["record_type"], "remote_proof_result")
        self.assertFalse(result["reusable_for_product"])
        self.assertIn(result["result"], {"PASS", "PENDING"})
        self.assertIn("static_ssh_is_not_managed", result["provider_capabilities_from_sources"])
        self.assertIn("does not lease", result["production_boundary"])

    def test_ready_requires_crabbox_and_broker_or_blacksmith_config(self):
        with patch.object(probe, "run_probe_command") as run_command, patch.object(probe, "crabbox_config_presence") as config:
            run_command.side_effect = [
                {"available": True, "exit_code": 0, "stdout_tail": "crabbox v0.26.0", "stderr_tail": ""},
                {"available": True, "exit_code": 0, "stdout_tail": "doctor ok", "stderr_tail": ""},
                {"available": False, "exit_code": None, "stdout_tail": "", "stderr_tail": ""},
            ]
            config.return_value = {
                "user_config_present": True,
                "broker_url_present": True,
                "broker_token_present": True,
                "provider_present": True,
                "blacksmith_config_present": False,
            }
            with patch.dict(probe.os.environ, {}, clear=True):
                result = probe.build_probe()

        self.assertEqual(result["result"], "PASS")
        self.assertTrue(result["managed_remote_proof_ready"])
        self.assertFalse(result["reusable_for_product"])

    def test_writes_public_safe_probe_files(self):
        with TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "probe.json"
            md_out = Path(tmpdir) / "probe.md"
            exit_code = probe.main(["--out", str(out), "--md-out", str(md_out)])

            self.assertEqual(exit_code, 0)
            self.assertTrue(out.exists())
            self.assertTrue(md_out.exists())


if __name__ == "__main__":
    unittest.main()
