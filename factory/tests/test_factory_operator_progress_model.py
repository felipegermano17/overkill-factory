from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factory_operator_progress_card.py"
SPEC = importlib.util.spec_from_file_location("factory_operator_progress_card", MODULE_PATH)
assert SPEC is not None
progress_card = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factory_operator_progress_card"] = progress_card
SPEC.loader.exec_module(progress_card)


def sample_progress_model() -> dict:
    return {
        "record_type": "factory_operator_progress_model",
        "manager_profile": "overkill-factory-gerente",
        "process_counts": {"done": 96, "total": 100},
        "gates": [
            {
                "id": "discovery",
                "label": "Discovery",
                "weight": 15,
                "readiness": "ready",
                "gate_ref": "gate:product-understanding-confirmed",
                "evidence_refs": ["reports/discovery/product-understanding-packet.json"],
                "artifacts": [
                    {"id": "product_understanding_packet", "status": "usable", "evidence_ref": "reports/discovery/product-understanding-packet.json"}
                ],
            },
            {
                "id": "architecture",
                "label": "Architecture",
                "weight": 25,
                "readiness": "blocked",
                "critical": True,
                "gate_ref": "gate:architecture-approved",
                "evidence_refs": ["reports/architecture/package-draft.json"],
                "artifacts": [
                    {"id": "architecture_package", "status": "partial", "evidence_ref": "reports/architecture/package-draft.json"}
                ],
                "blockers": [
                    {
                        "id": "arch-approval",
                        "kind": "human_gate",
                        "summary": "Architecture package has not been approved by the operator.",
                        "owner": "overkill-factory-gerente",
                    }
                ],
            },
            {
                "id": "execution",
                "label": "Execution",
                "weight": 30,
                "readiness": "not_started",
                "critical": True,
                "gate_ref": "gate:material-execution-complete",
                "artifacts": [{"id": "working_product", "status": "missing"}],
            },
            {
                "id": "proof",
                "label": "Proof",
                "weight": 20,
                "readiness": "not_started",
                "critical": True,
                "gate_ref": "gate:receipt-five-ready",
                "artifacts": [{"id": "receipt_five", "status": "missing"}],
            },
            {
                "id": "release",
                "label": "Release",
                "weight": 10,
                "readiness": "not_started",
                "critical": True,
                "gate_ref": "gate:release-ready",
                "artifacts": [{"id": "release_packet", "status": "missing"}],
            },
        ],
        "uncertainty": {
            "confidence": 0.72,
            "range_percent": [12, 18],
            "unknowns": ["Proof artifacts have not been audited yet."],
        },
    }


class OperatorProgressModelTest(unittest.TestCase):
    def test_product_percent_uses_weighted_gates_not_raw_done_counts(self) -> None:
        card = progress_card.build_card_from_model(sample_progress_model())

        self.assertEqual(card["record_type"], "operator_progress_card")
        self.assertEqual(card["progress_basis"], "weighted_gates_artifacts_readiness")
        self.assertEqual(card["progress_percent"], 15)
        self.assertEqual(card["process_counts"], {"done": 96, "total": 100})
        self.assertEqual(card["process_done_percent"], 96)
        self.assertFalse(card["process_counts_used_for_product_percent"])
        self.assertLess(card["progress_percent"], card["process_done_percent"])
        self.assertEqual(card["gate_progress"]["discovery"]["percent"], 100)
        self.assertEqual(card["gate_progress"]["architecture"]["percent"], 0)

    def test_critical_path_blockers_and_uncertainty_are_operator_visible(self) -> None:
        card = progress_card.build_card_from_model(sample_progress_model())

        self.assertEqual([item["gate_id"] for item in card["critical_path"]], ["architecture", "execution", "proof", "release"])
        self.assertEqual(card["blockers"][0]["id"], "arch-approval")
        self.assertEqual(card["uncertainty"]["confidence"], 0.72)
        self.assertEqual(card["uncertainty"]["range_percent"], [12, 18])
        self.assertIn("Architecture", card["human_text"])
        self.assertIn("Execution", card["human_text"])
        self.assertIn("Proof", card["human_text"])
        self.assertIn("Release", card["human_text"])
        self.assertIn("15%", card["human_text"])
        self.assertIn("incerteza", card["human_text"].lower())
        self.assertIn("Architecture package has not been approved", card["human_text"])

    def test_cli_accepts_progress_model_and_factoryctl_passes_it_through(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            model = tmp / "progress-model.json"
            out = tmp / "operator-progress-card.json"
            text_out = tmp / "operator-progress-card.txt"
            model.write_text(json.dumps(sample_progress_model(), indent=2) + "\n", encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    "scripts/factoryctl.py",
                    "operator-progress-card",
                    "--model",
                    str(model),
                    "--out",
                    str(out),
                    "--text-out",
                    str(text_out),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(out.read_text(encoding="utf-8"))
            text = text_out.read_text(encoding="utf-8")

        self.assertEqual(payload["progress_percent"], 15)
        self.assertEqual(payload["next_critical_gate"], "architecture")
        self.assertIn("Caminho crítico", text)
        self.assertIn("Discovery: 100%", text)
        self.assertIn("Release: 0%", text)


if __name__ == "__main__":
    unittest.main()
