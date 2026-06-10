from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "adapters" / "hermes" / "worker_route_readiness.py"
SPEC = importlib.util.spec_from_file_location("worker_route_readiness", MODULE_PATH)
assert SPEC is not None
worker_route_readiness = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["worker_route_readiness"] = worker_route_readiness
SPEC.loader.exec_module(worker_route_readiness)


def write_ledger(path: Path, worker_id: str = "factory-orchestrator") -> None:
    path.write_text(
        json.dumps(
            {
                "$schema": "https://overkill-factory.dev/schemas/hermes-worker-ledger.schema.json",
                "ledger_type": "overkill_factory_hermes_worker_ledger",
                "tasks": {
                    "ofw_test": {
                        "task_id": "ofw_test",
                        "card_id": "TEST-CARD",
                        "worker_id": worker_id,
                        "queue_class": "blocking-before-done",
                        "required_before": "done",
                        "expected_receipt_field": "worker_result",
                        "status": "requires_execution",
                        "packet": {},
                    }
                },
            }
        ),
        encoding="utf-8",
    )


class HermesWorkerRouteReadinessTest(unittest.TestCase):
    def test_blocks_missing_profile_and_config(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            ledger = tmp_path / "worker-ledger.json"
            hermes_home = tmp_path / "home"
            hermes_home.mkdir()
            write_ledger(ledger)

            receipt = worker_route_readiness.check_readiness(
                ledger_path=ledger,
                hermes_home=hermes_home,
            )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertEqual(receipt["blocked_workers"], ["factory-orchestrator"])
        self.assertIn("profile_missing", receipt["checks"][0]["blocked_reasons"])
        self.assertEqual(receipt["hermes_home_ref"], "redacted-hermes-home")

    def test_passes_explicit_reachable_local_provider_profile(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            ledger = tmp_path / "worker-ledger.json"
            hermes_home = tmp_path / "home"
            profile = hermes_home / "profiles" / "factory-orchestrator"
            profile.mkdir(parents=True)
            write_ledger(ledger)
            (profile / "config.yaml").write_text(
                "\n".join(
                    [
                        "model:",
                        "  default: local-test-model",
                        "  provider: lmstudio",
                        "  base_url: http://127.0.0.1:1234/v1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with mock.patch.object(worker_route_readiness, "_local_endpoint_model_status", return_value=(True, "local_endpoint_model_listed")):
                receipt = worker_route_readiness.check_readiness(
                    ledger_path=ledger,
                    hermes_home=hermes_home,
                )

        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["blocked_workers"], [])
        self.assertEqual(receipt["checks"][0]["status"], "ready")
        self.assertEqual(receipt["checks"][0]["credential_evidence"], ["local_endpoint_model_listed"])

    def test_blocks_unreachable_local_provider_profile(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            ledger = tmp_path / "worker-ledger.json"
            hermes_home = tmp_path / "home"
            profile = hermes_home / "profiles" / "factory-orchestrator"
            profile.mkdir(parents=True)
            write_ledger(ledger)
            (profile / "config.yaml").write_text(
                "\n".join(
                    [
                        "model:",
                        "  default: local-test-model",
                        "  provider: lmstudio",
                        "  base_url: http://127.0.0.1:1234/v1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with mock.patch.object(worker_route_readiness, "_local_endpoint_model_status", return_value=(False, "local_endpoint_unreachable")):
                receipt = worker_route_readiness.check_readiness(
                    ledger_path=ledger,
                    hermes_home=hermes_home,
                )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("local_endpoint_unreachable", receipt["checks"][0]["blocked_reasons"])

    def test_blocks_local_provider_when_model_is_not_listed(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            ledger = tmp_path / "worker-ledger.json"
            hermes_home = tmp_path / "home"
            profile = hermes_home / "profiles" / "factory-orchestrator"
            profile.mkdir(parents=True)
            write_ledger(ledger)
            (profile / "config.yaml").write_text(
                "\n".join(
                    [
                        "model:",
                        "  default: local-test-model",
                        "  provider: lmstudio",
                        "  base_url: http://127.0.0.1:1234/v1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with mock.patch.object(worker_route_readiness, "_local_endpoint_model_status", return_value=(False, "local_endpoint_model_missing")):
                receipt = worker_route_readiness.check_readiness(
                    ledger_path=ledger,
                    hermes_home=hermes_home,
                )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("local_endpoint_model_missing", receipt["checks"][0]["blocked_reasons"])

    def test_blocks_provider_auto_even_with_model(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            ledger = tmp_path / "worker-ledger.json"
            hermes_home = tmp_path / "home"
            profile = hermes_home / "profiles" / "factory-orchestrator"
            profile.mkdir(parents=True)
            write_ledger(ledger)
            (profile / "config.yaml").write_text(
                "\n".join(
                    [
                        "model:",
                        "  default: some-model",
                        "  provider: auto",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            receipt = worker_route_readiness.check_readiness(
                ledger_path=ledger,
                hermes_home=hermes_home,
            )

        self.assertEqual(receipt["result"], "BLOCKED")
        self.assertIn("provider_missing", receipt["checks"][0]["blocked_reasons"])

    def test_cli_requires_explicit_hermes_home_when_env_missing(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            ledger = Path(tmp) / "worker-ledger.json"
            write_ledger(ledger)
            with mock.patch.dict("os.environ", {}, clear=True):
                with self.assertRaises(SystemExit) as raised:
                    worker_route_readiness.main(["--ledger", str(ledger)])

        self.assertIn("--hermes-home is required", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
