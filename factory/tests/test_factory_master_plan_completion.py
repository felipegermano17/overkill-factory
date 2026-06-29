from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_master_plan_completion_audit.py"
COMPLETION_PATH = ROOT / "templates" / "factory-master-plan-completion.json"


REQUIRED_WAVES = set(range(10))
REQUIRED_CATEGORIES = {
    "code_refs",
    "test_refs",
    "command_refs",
    "runtime_refs",
    "agent_refs",
    "operator_refs",
    "evidence_refs",
}


def load_module():
    spec = importlib.util.spec_from_file_location("factory_master_plan_completion_audit", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryMasterPlanCompletionTest(unittest.TestCase):
    def test_completion_record_covers_every_wave_with_operational_evidence(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), "completion audit script must exist")
        self.assertTrue(COMPLETION_PATH.exists(), "completion template must exist")
        module = load_module()
        record = json.loads(COMPLETION_PATH.read_text())
        report = module.audit(record, root=ROOT)
        self.assertEqual(report["result"], "PASS", report.get("errors"))
        self.assertEqual(report["score"], 100)
        self.assertEqual(set(report["waves"].keys()), {str(w) for w in REQUIRED_WAVES})
        for wave_id, wave in report["waves"].items():
            with self.subTest(wave=wave_id):
                self.assertEqual(wave["result"], "PASS")
                self.assertEqual(wave["score"], 100)
                self.assertTrue(REQUIRED_CATEGORIES.issubset(set(wave["evidence_categories"])))
                self.assertGreaterEqual(wave["evidence_ref_count"], 5)

    def test_completion_audit_cli_writes_pass_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "completion.json"
            md = Path(tmp) / "completion.md"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--record",
                    str(COMPLETION_PATH),
                    "--out",
                    str(out),
                    "--markdown",
                    str(md),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads(out.read_text())
            self.assertEqual(report["result"], "PASS")
            self.assertIn("Wave 9", md.read_text())

    def test_agents_and_bindings_are_marked_for_v3_production_activation(self) -> None:
        profiles = json.loads((ROOT / "agents" / "worker-profiles.public.json").read_text())
        bindings = json.loads((ROOT / "agents" / "hermes-profile-bindings.public.json").read_text())
        registry = json.loads((ROOT / "agents" / "worker-registry.public.json").read_text())

        self.assertEqual(profiles.get("production_activation_version"), "v3.0.0-master-plan-100")
        self.assertEqual(bindings.get("production_activation_version"), "v3.0.0-master-plan-100")
        self.assertEqual(registry.get("production_activation_version"), "v3.0.0-master-plan-100")

        for worker_id, profile in profiles["profiles"].items():
            with self.subTest(profile=worker_id):
                activation = profile.get("v3_master_plan_activation")
                self.assertIsInstance(activation, dict)
                self.assertTrue(activation.get("manager_only_operator_contact"))
                self.assertTrue(activation.get("uses_factory_code_not_prompt_runtime"))
                self.assertIn("factory_perfect_run", activation.get("required_checks", []))
                self.assertIn("receipt_five_readback", activation.get("evidence_policy", []))

        for worker_id, binding in bindings["bindings"].items():
            with self.subTest(binding=worker_id):
                activation = binding.get("v3_production_activation")
                self.assertIsInstance(activation, dict)
                self.assertEqual(activation.get("runtime_authority"), "hermes_kanban")
                self.assertFalse(activation.get("can_contact_operator_directly"))
                self.assertIn("factory-master-plan-completion", activation.get("required_release_checks", []))

        for worker in registry["workers"]:
            with self.subTest(worker=worker["worker_id"]):
                self.assertIn("v3_master_plan_activation", worker)
                self.assertIn("Receipt Five readback", "\n".join(worker.get("evidence_required", [])))

    def test_factoryctl_exposes_master_plan_activation_commands(self) -> None:
        proc = subprocess.run(
            [sys.executable, "scripts/factoryctl.py", "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        help_text = proc.stdout
        for command in [
            "master-plan-completion",
            "factory-perfect-run",
            "hermes-live-smoke",
            "v3-production-activation-check",
            "human-gate-package",
            "validate-human-gate-package",
            "receipt-five-classify",
        ]:
            with self.subTest(command=command):
                self.assertIn(command, help_text)


if __name__ == "__main__":
    unittest.main()
