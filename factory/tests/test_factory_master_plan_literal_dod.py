from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "factory_master_plan_literal_dod_audit.py"
MATRIX = ROOT / "templates" / "factory-master-plan-literal-dod.json"

REQUIRED_IDS = {
    "01-telegram-natural-language-start",
    "02-manager-intake-factoryrun",
    "03-factoryrun-real-graph",
    "04-hermes-dispatch-or-typed-block",
    "05-packet-not-execution",
    "06-no-idle-safe-resume",
    "07-user-progress-without-kanban",
    "08-human-decision-readable-package",
    "09-human-gate-exception",
    "10-done-receipt-five-product-proof",
    "11-product-face-screenshots-ux-proof",
    "12-explicit-authority-sensitive-actions",
    "13-solana-ai-kit-required",
    "14-learnback-reviewable-proposal",
    "15-manager-agent-freshness",
    "16-public-github-v3-surface",
    "17-final-validation-agent-manager-e2e",
}

REQUIRED_NEW_COMMANDS = {
    "literal-dod-audit",
    "manager-intake-smoke",
    "manager-profile-live-smoke",
    "operator-progress-card",
    "operator-delivery-receipt",
    "product-face-result",
    "learnback-proposal",
    "telegram-start-smoke",
}


def load_audit_module():
    spec = importlib.util.spec_from_file_location("factory_master_plan_literal_dod_audit", AUDIT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactoryMasterPlanLiteralDodTest(unittest.TestCase):
    def test_literal_dod_matrix_covers_all_17_items_without_overclaim(self) -> None:
        self.assertTrue(AUDIT.exists(), "literal DoD audit script must exist")
        self.assertTrue(MATRIX.exists(), "literal DoD matrix template must exist")
        module = load_audit_module()
        matrix = json.loads(MATRIX.read_text())
        report = module.audit(matrix, root=ROOT)
        self.assertIn(report["result"], {"PASS", "PARTIAL_EXTERNAL"}, report.get("errors"))
        self.assertEqual(set(report["criteria"].keys()), REQUIRED_IDS)
        self.assertEqual(report["summary"]["criterion_count"], 17)
        self.assertEqual(report["summary"]["locally_implemented"], 17)
        self.assertEqual(report["summary"]["errors"], 0)
        self.assertGreaterEqual(report["summary"]["external_live_pending"], 1)
        for criterion_id, criterion in report["criteria"].items():
            with self.subTest(criterion=criterion_id):
                self.assertTrue(criterion["local_support"], criterion)
                self.assertTrue(criterion["evidence_refs"], criterion)
                self.assertTrue(criterion["command_refs"], criterion)

    def test_literal_dod_cli_writes_report_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "literal-dod.json"
            md = Path(tmp) / "literal-dod.md"
            proc = subprocess.run(
                [sys.executable, str(AUDIT), "--matrix", str(MATRIX), "--out", str(out), "--markdown", str(md)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertIn(proc.returncode, {0, 2}, proc.stdout + proc.stderr)
            report = json.loads(out.read_text())
            self.assertIn(report["result"], {"PASS", "PARTIAL_EXTERNAL"})
            self.assertIn("Definition of Done literal", md.read_text())

    def test_factoryctl_exposes_literal_dod_operator_commands(self) -> None:
        proc = subprocess.run([sys.executable, "scripts/factoryctl.py", "--help"], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for command in REQUIRED_NEW_COMMANDS:
            with self.subTest(command=command):
                self.assertIn(command, proc.stdout)

    def test_artifact_generators_produce_operator_safe_outputs(self) -> None:
        commands = [
            [sys.executable, "scripts/factory_manager_intake_smoke.py", "--out", ".tmp/test-manager-intake-smoke.json"],
            [sys.executable, "scripts/factory_manager_profile_live_smoke.py", "--out", ".tmp/test-manager-profile-live-smoke.json", "--dry-run"],
            [sys.executable, "scripts/factory_operator_progress_card.py", "--out", ".tmp/test-progress-card.json", "--text-out", ".tmp/test-progress-card.txt"],
            [sys.executable, "scripts/factory_operator_delivery_receipt.py", "--out", ".tmp/test-delivery-receipt.json"],
            [sys.executable, "scripts/factory_product_face_result.py", "--out", ".tmp/test-product-face-result.json"],
            [sys.executable, "scripts/factory_learnback_proposal.py", "--out", ".tmp/test-learnback-proposal.json"],
            [sys.executable, "scripts/factory_telegram_start_smoke.py", "--out", ".tmp/test-telegram-start-smoke.json", "--dry-run"],
            [sys.executable, "scripts/render_human_gate_pdf.py", "--out", ".tmp/test-human-gate-package.txt", "--pdf-out", ".tmp/test-human-gate-package.pdf"],
        ]
        for command in commands:
            with self.subTest(command=" ".join(command)):
                proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        progress_text = (ROOT / ".tmp/test-progress-card.txt").read_text()
        self.assertIn("Progresso", progress_text)
        self.assertIn("Próxima ação", progress_text)
        face = json.loads((ROOT / ".tmp/test-product-face-result.json").read_text())
        self.assertEqual(face["result"], "PASS")
        self.assertTrue(face["screenshots"])
        self.assertTrue(face["ux_proof"])
        pdf = ROOT / ".tmp/test-human-gate-package.pdf"
        self.assertTrue(pdf.exists())
        self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
