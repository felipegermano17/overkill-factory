from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_factoryctl(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/factoryctl.py", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


class OperatorExperienceTest(unittest.TestCase):
    def test_factoryctl_exposes_single_operator_entrypoint(self) -> None:
        help_text = run_factoryctl("--help").stdout
        run_help = run_factoryctl("run", "--help").stdout

        for command in ["doctor", "init", "run", "unblock-plan", "help-next"]:
            with self.subTest(command=command):
                self.assertIn(command, help_text)
        self.assertIn("minimal", run_help)

    def test_unblock_plan_is_read_only_operator_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "unblock-plan.json"
            run_factoryctl(
                "unblock-plan",
                "--card",
                "examples/cards/v35_valid_onchain_auditor_scan.md",
                "--out",
                str(out),
            )
            payload = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(payload["record_type"], "operator_unblock_plan")
        self.assertIn("next_safe_actions", payload)
        self.assertTrue(any("does not execute workers" in item for item in payload["limits"]))

    def test_doctor_reports_public_install_health_without_real_hermes_e2e(self) -> None:
        result = run_factoryctl("doctor", "--json")
        payload = json.loads(result.stdout)
        check_ids = {check["id"] for check in payload["checks"]}

        self.assertEqual(payload["result"], "PASS")
        self.assertTrue(
            {
                "python_version",
                "package_metadata",
                "repository_shape",
                "minimal_example",
                "public_cli",
                "hermes_runtime_optional",
                "hermes_e2e_deferred",
            }.issubset(check_ids)
        )
        self.assertFalse(any(check["status"] == "FAIL" for check in payload["checks"]))
        deferred = next(check for check in payload["checks"] if check["id"] == "hermes_e2e_deferred")
        self.assertEqual(deferred["status"], "INFO")

    def test_run_minimal_uses_factoryctl_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            out = tmp / "quickstart-result.json"
            packets = tmp / "packets"

            result = run_factoryctl("run", "minimal", "--out", str(out), "--packets-out", str(packets))
            payload = json.loads(out.read_text(encoding="utf-8"))

            self.assertIn("PASS", result.stdout)
            self.assertEqual(payload["result"], "PASS")
            self.assertGreater(payload["worker_packet_count"], 0)
            self.assertTrue(any(packets.glob("*.json")))

    def test_init_creates_hermes_friendly_operator_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "sample-project"
            result = run_factoryctl("init", "--out", str(target), "--project-name", "sample-project")

            self.assertIn("initialized", result.stdout.lower())
            self.assertTrue((target / "overkill.factory.json").is_file())
            self.assertTrue((target / "cards" / "minimal-card.md").is_file())
            self.assertTrue((target / "worker-packets" / ".gitkeep").is_file())
            self.assertTrue((target / "receipts" / ".gitkeep").is_file())
            self.assertTrue((target / "README.md").is_file())

            config = json.loads((target / "overkill.factory.json").read_text(encoding="utf-8"))
            readme = (target / "README.md").read_text(encoding="utf-8")
            self.assertEqual(config["project_name"], "sample-project")
            self.assertEqual(config["runtime"]["name"], "Hermes")
            self.assertIn("factoryctl doctor", readme)
            self.assertIn("factoryctl run minimal", readme)
            self.assertIn("Connect this workspace to your Hermes", readme)


if __name__ == "__main__":
    unittest.main()
