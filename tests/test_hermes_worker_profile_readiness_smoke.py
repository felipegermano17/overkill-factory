from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
READINESS_PATH = ROOT / "adapters" / "hermes" / "worker_route_readiness.py"
READINESS_SPEC = importlib.util.spec_from_file_location("worker_route_readiness", READINESS_PATH)
assert READINESS_SPEC is not None
worker_route_readiness = importlib.util.module_from_spec(READINESS_SPEC)
assert READINESS_SPEC.loader is not None
sys.modules["worker_route_readiness"] = worker_route_readiness
READINESS_SPEC.loader.exec_module(worker_route_readiness)

MODULE_PATH = ROOT / "adapters" / "hermes" / "worker_profile_readiness_smoke.py"
SPEC = importlib.util.spec_from_file_location("worker_profile_readiness_smoke", MODULE_PATH)
assert SPEC is not None
worker_profile_readiness_smoke = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["worker_profile_readiness_smoke"] = worker_profile_readiness_smoke
SPEC.loader.exec_module(worker_profile_readiness_smoke)


def write_ledger(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "$schema": "https://overkill-factory.dev/schemas/hermes-worker-ledger.schema.json",
                "ledger_type": "overkill_factory_hermes_worker_ledger",
                "tasks": {
                    "ofw_a": {
                        "task_id": "ofw_a",
                        "card_id": "TEST",
                        "worker_id": "factory-orchestrator",
                        "queue_class": "blocking-before-ready",
                        "required_before": "ready",
                        "expected_receipt_field": "orchestrator_result",
                        "status": "requires_execution",
                        "packet": {},
                    },
                    "ofw_b": {
                        "task_id": "ofw_b",
                        "card_id": "TEST",
                        "worker_id": "qa-verification-worker",
                        "queue_class": "blocking-before-done",
                        "required_before": "done",
                        "expected_receipt_field": "qa_result",
                        "status": "requires_execution",
                        "packet": {},
                    },
                },
            }
        ),
        encoding="utf-8",
    )


class HermesWorkerProfileReadinessSmokeTest(unittest.TestCase):
    def test_smoke_provisions_profiles_and_passes_readiness_against_stub(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            ledger = tmp_path / "worker-ledger.json"
            hermes_home = tmp_path / "home"
            write_ledger(ledger)

            receipt = worker_profile_readiness_smoke.run_smoke(
                ledger_path=ledger,
                hermes_home=hermes_home,
                overwrite=True,
            )

            factory_config = hermes_home / "profiles" / "factory-orchestrator" / "config.yaml"
            qa_config = hermes_home / "profiles" / "qa-verification-worker" / "config.yaml"
            factory_config_exists = factory_config.exists()
            qa_config_exists = qa_config.exists()

        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["scope"], "disposable-local-openai-stub-only")
        self.assertEqual(receipt["worker_count"], 2)
        self.assertEqual(receipt["blocked_worker_count"], 0)
        self.assertTrue(factory_config_exists)
        self.assertTrue(qa_config_exists)
        self.assertTrue(any("does not prove real model quality" in item for item in receipt["production_limits"]))


if __name__ == "__main__":
    unittest.main()
