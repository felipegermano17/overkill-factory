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


def run_factoryctl_blocking_ok(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/factoryctl.py", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def write_card_without_security_packet(tmp: Path) -> Path:
    source = (ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md").read_text(encoding="utf-8")
    data = json.loads(source[source.find("{") : source.rfind("}") + 1])
    data.pop("security_scan_packet", None)
    path = tmp / "blocked-card.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def write_product_card_missing_experience(tmp: Path) -> Path:
    data = json.loads((ROOT / "templates" / "vfinal-factory-card.json").read_text(encoding="utf-8"))
    data["card_id"] = "TEST-MISSING-PRODUCT-EXPERIENCE"
    data["phase"] = "F11"
    data["surfaces"] = ["frontend", "product-face"]
    data["capability_pack_contract"]["covered_surfaces"] = ["frontend", "product-face"]
    data.pop("product_experience_plan", None)
    data.pop("product_face_packet", None)
    data.pop("professional_design_process", None)
    path = tmp / "missing-product-experience.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


class OperatorExperienceTest(unittest.TestCase):
    def test_factoryctl_exposes_single_operator_entrypoint(self) -> None:
        help_text = run_factoryctl("--help").stdout
        run_help = run_factoryctl("run", "--help").stdout

        for command in ["doctor", "init", "run", "unblock-plan", "recovery-plan", "help-next"]:
            with self.subTest(command=command):
                self.assertIn(command, help_text)
        self.assertIn("minimal", run_help)

    def test_unblock_plan_emits_semantic_recovery_contract(self) -> None:
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

        self.assertEqual(payload["record_type"], "factory_recovery_plan")
        self.assertIn("next_safe_actions", payload)
        self.assertIn("recovery_routes", payload)
        self.assertEqual(payload["gate_predicate_result"], "PASS")
        self.assertEqual(payload["recovery_routes"], [])
        self.assertEqual(payload["hermes_runtime_boundary"]["runtime_authority"], "hermes_kanban")
        self.assertFalse(payload["hermes_runtime_boundary"]["local_state_authority"])
        self.assertTrue(payload["hermes_runtime_boundary"]["no_shadow_dispatcher"])
        self.assertTrue(any("does not execute workers" in item for item in payload["limits"]))

    def test_recovery_plan_names_hermes_native_materialization(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            card = write_card_without_security_packet(tmp)
            out = tmp / "recovery-plan.json"
            result = run_factoryctl_blocking_ok(
                "recovery-plan",
                "--card",
                str(card),
                "--out",
                str(out),
            )
            payload = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["$schema"], "https://overkill-factory.dev/schemas/factory-recovery-plan.schema.json")
        self.assertGreater(len(payload["recovery_routes"]), 0)
        route = payload["recovery_routes"][0]
        self.assertEqual(route["hermes_materialization"]["runtime_authority"], "hermes_kanban")
        self.assertFalse(route["hermes_materialization"]["local_state_authority"])
        self.assertIn("kanban_task", route["hermes_materialization"]["native_primitives"])

    def test_help_next_routes_missing_product_surface_planning_to_product_experience_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            card = write_product_card_missing_experience(Path(tmpdir))
            result = run_factoryctl("help-next", "--card", str(card))
            payload = json.loads(result.stdout)

        self.assertEqual(payload["workflow_phase"]["phase_id"], "F8A")
        self.assertEqual(payload["workflow_phase"]["phase_name"], "Product Experience And Surface Pack Gate")
        self.assertIn("Product Experience Plan", payload["factory_next_action"]["action"])
        self.assertIn("surface pack", payload["factory_next_action"]["why"].lower())
        self.assertIn("product_experience_plan required for vFinal product-facing surfaces", payload["blocked_because"])
        self.assertIn(
            "populate card.product_experience_plan with public-safe contract data or attach the required worker evidence",
            payload["evidence_needed"],
        )

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
