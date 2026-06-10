from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "adapters" / "hermes" / "production_update_preflight.py"
SPEC = importlib.util.spec_from_file_location("hermes_production_update_preflight", MODULE_PATH)
assert SPEC is not None
hermes_production_update_preflight = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["hermes_production_update_preflight"] = hermes_production_update_preflight
SPEC.loader.exec_module(hermes_production_update_preflight)


class HermesProductionUpdatePreflightTest(unittest.TestCase):
    def test_missing_required_proofs_blocks_real_runtime_update(self) -> None:
        requirement = hermes_production_update_preflight.ProofRequirement(
            key="non_stub_worker_execution",
            arg_name="non_stub_worker_execution",
            description="non-stub proof",
        )

        receipt = hermes_production_update_preflight.evaluate_preflight(
            {},
            required_proofs=[requirement],
            created_at="2026-06-10T00:00:00Z",
        )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertEqual(receipt["decision"]["real_runtime_update"], "blocked")
        self.assertEqual(receipt["blocking_items"], ["non_stub_worker_execution"])

    def test_pass_receipt_satisfies_required_proof(self) -> None:
        requirement = hermes_production_update_preflight.ProofRequirement(
            key="non_stub_worker_execution",
            arg_name="non_stub_worker_execution",
            description="non-stub proof",
        )
        with tempfile.TemporaryDirectory() as tmp:
            proof = Path(tmp) / "proof.json"
            self._write_production_proof(proof, "non_stub_worker_execution")

            receipt = hermes_production_update_preflight.evaluate_preflight(
                {"non_stub_worker_execution": proof},
                required_proofs=[requirement],
                created_at="2026-06-10T00:00:00Z",
            )

            self.assertEqual(receipt["result"], "PASS")
            self.assertEqual(receipt["decision"]["real_runtime_update"], "allowed_for_explicit_operator_gate")
            self.assertEqual(receipt["blocking_items"], [])

    def test_generic_pass_json_does_not_satisfy_required_proof(self) -> None:
        requirement = hermes_production_update_preflight.ProofRequirement(
            key="non_stub_worker_execution",
            arg_name="non_stub_worker_execution",
            description="non-stub proof",
        )
        with tempfile.TemporaryDirectory() as tmp:
            proof = Path(tmp) / "proof.json"
            proof.write_text(json.dumps({"result": "PASS"}), encoding="utf-8")

            receipt = hermes_production_update_preflight.evaluate_preflight(
                {"non_stub_worker_execution": proof},
                required_proofs=[requirement],
                created_at="2026-06-10T00:00:00Z",
            )

            self.assertEqual(receipt["result"], "BLOCKED")
            self.assertEqual(receipt["required_proofs"][0]["reason"], "record_type must be 'hermes_production_proof'")

    def test_wrong_proof_type_does_not_satisfy_required_proof(self) -> None:
        requirement = hermes_production_update_preflight.ProofRequirement(
            key="non_stub_worker_execution",
            arg_name="non_stub_worker_execution",
            description="non-stub proof",
        )
        with tempfile.TemporaryDirectory() as tmp:
            proof = Path(tmp) / "proof.json"
            self._write_production_proof(proof, "real_tool_auth")

            receipt = hermes_production_update_preflight.evaluate_preflight(
                {"non_stub_worker_execution": proof},
                required_proofs=[requirement],
                created_at="2026-06-10T00:00:00Z",
            )

            self.assertEqual(receipt["result"], "BLOCKED")
            self.assertEqual(receipt["required_proofs"][0]["reason"], "proof_type must be 'non_stub_worker_execution'")

    def test_operator_control_tower_proof_requires_passing_readiness_ref(self) -> None:
        requirement = hermes_production_update_preflight.ProofRequirement(
            key="operator_control_tower",
            arg_name="operator_control_tower",
            description="operator proof",
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            readiness = tmp_path / "operator-control-tower-production-readiness.json"
            proof = tmp_path / "operator-proof.json"
            readiness.write_text(
                json.dumps(
                    {
                        "record_type": "operator_control_tower_production_readiness",
                        "result": "BLOCKED",
                        "blocking_items": ["bridge_health_present"],
                    }
                ),
                encoding="utf-8",
            )
            self._write_production_proof(
                proof,
                "operator_control_tower",
                evidence_refs=[readiness.relative_to(ROOT).as_posix()],
            )

            receipt = hermes_production_update_preflight.evaluate_preflight(
                {"operator_control_tower": proof},
                required_proofs=[requirement],
                created_at="2026-06-10T00:00:00Z",
            )

            self.assertEqual(receipt["result"], "BLOCKED")
            self.assertIn("expected 'PASS'", receipt["required_proofs"][0]["reason"])

    def test_operator_control_tower_proof_passes_with_passing_readiness_ref(self) -> None:
        requirement = hermes_production_update_preflight.ProofRequirement(
            key="operator_control_tower",
            arg_name="operator_control_tower",
            description="operator proof",
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            readiness = tmp_path / "operator-control-tower-production-readiness.json"
            proof = tmp_path / "operator-proof.json"
            readiness.write_text(
                json.dumps(
                    {
                        "record_type": "operator_control_tower_production_readiness",
                        "result": "PASS",
                        "blocking_items": [],
                    }
                ),
                encoding="utf-8",
            )
            self._write_production_proof(
                proof,
                "operator_control_tower",
                evidence_refs=[readiness.relative_to(ROOT).as_posix()],
            )

            receipt = hermes_production_update_preflight.evaluate_preflight(
                {"operator_control_tower": proof},
                required_proofs=[requirement],
                created_at="2026-06-10T00:00:00Z",
            )

            self.assertEqual(receipt["result"], "PASS")
            self.assertEqual(receipt["blocking_items"], [])

    def test_blocked_update_receipt_keeps_preflight_blocked(self) -> None:
        requirement = hermes_production_update_preflight.ProofRequirement(
            key="complete_update_receipt",
            arg_name="complete_update_receipt",
            description="update receipt",
        )
        with tempfile.TemporaryDirectory() as tmp:
            proof = Path(tmp) / "update-receipt.json"
            proof.write_text(
                json.dumps({"decision": {"real_runtime_update": "blocked_until_checked"}}),
                encoding="utf-8",
            )

            receipt = hermes_production_update_preflight.evaluate_preflight(
                {"complete_update_receipt": proof},
                required_proofs=[requirement],
                created_at="2026-06-10T00:00:00Z",
            )

            self.assertEqual(receipt["result"], "BLOCKED")
            self.assertEqual(receipt["blocking_items"], ["complete_update_receipt"])

    def test_complete_update_receipt_requires_all_checks_and_evidence(self) -> None:
        requirement = hermes_production_update_preflight.ProofRequirement(
            key="complete_update_receipt",
            arg_name="complete_update_receipt",
            description="update receipt",
        )
        with tempfile.TemporaryDirectory() as tmp:
            proof = Path(tmp) / "update-receipt.json"
            proof.write_text(
                json.dumps(
                    {
                        "record_type": "hermes_update_receipt",
                        "decision": {"real_runtime_update": "allowed_for_explicit_operator_gate"},
                        "checks": {"compatibility_check": "PASS"},
                        "evidence_refs": ["validation/evidence.json"],
                    }
                ),
                encoding="utf-8",
            )

            receipt = hermes_production_update_preflight.evaluate_preflight(
                {"complete_update_receipt": proof},
                required_proofs=[requirement],
                created_at="2026-06-10T00:00:00Z",
            )

            self.assertEqual(receipt["result"], "PASS")
            self.assertEqual(receipt["blocking_items"], [])

    def _write_production_proof(
        self,
        path: Path,
        proof_type: str,
        evidence_refs: list[str] | None = None,
    ) -> None:
        path.write_text(
            json.dumps(
                {
                    "record_type": "hermes_production_proof",
                    "proof_type": proof_type,
                    "result": "PASS",
                    "evidence_refs": evidence_refs or ["validation/evidence.json"],
                    "limits": ["bounded proof"],
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
