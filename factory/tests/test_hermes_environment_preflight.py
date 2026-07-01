from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factoryctl.py"
SPEC = importlib.util.spec_from_file_location("factoryctl_for_hermes_environment_preflight", MODULE_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl_for_hermes_environment_preflight"] = factoryctl
SPEC.loader.exec_module(factoryctl)

VALIDATOR_PATH = ROOT / "scripts" / "validate_public_json_artifacts.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_public_json_artifacts_hermes_preflight", VALIDATOR_PATH)
assert VALIDATOR_SPEC is not None
public_json_validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
sys.modules["validate_public_json_artifacts_hermes_preflight"] = public_json_validator
VALIDATOR_SPEC.loader.exec_module(public_json_validator)


class HermesEnvironmentPreflightTest(unittest.TestCase):
    def test_ready_when_required_contracts_and_runtime_tools_resolve(self) -> None:
        report = factoryctl.build_hermes_environment_preflight_report(
            command_resolver=lambda name: f"/usr/bin/{name}" if name in {"python", "git"} else None,
            created_at="2026-07-01T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "READY")
        check_ids = {check["id"] for check in report["checks"]}
        for required in [
            "profiles",
            "worker_bindings",
            "skill_refs",
            "toolsets",
            "terminal_file_web",
            "domain_providers",
            "credentials_access_readiness",
        ]:
            self.assertIn(required, check_ids)
        self.assertEqual(report["human_input_requests"], [])
        self.assertEqual(report["capability_acquisition_routes"], [])

    def test_deferred_factory_acquirable_capabilities_route_to_acquisition(self) -> None:
        report = factoryctl.build_hermes_environment_preflight_report(
            require=["browser", "pdf", "video"],
            capability_overrides={
                "browser": False,
                "pdf": False,
                "video": False,
            },
            command_resolver=lambda _name: "/usr/bin/tool",
            created_at="2026-07-01T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "READY_WITH_DEFERRED")
        route_ids = {route["capability_id"] for route in report["capability_acquisition_routes"]}
        self.assertEqual(route_ids, {"browser", "pdf", "video"})
        self.assertTrue(all(route["next_action"] == "capability-acquisition-run" for route in report["capability_acquisition_routes"]))
        self.assertEqual(report["human_input_requests"], [])

    def test_missing_required_credentials_block_with_exact_human_input(self) -> None:
        report = factoryctl.build_hermes_environment_preflight_report(
            require=["credentials"],
            credential_refs=[],
            access_refs=[],
            command_resolver=lambda _name: "/usr/bin/tool",
            created_at="2026-07-01T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "BLOCKED_WITH_EXACT_HUMAN_INPUT")
        self.assertEqual(report["capability_acquisition_routes"], [])
        self.assertEqual(
            report["human_input_requests"],
            [
                {
                    "input_id": "credentials_access_readiness",
                    "exact_request": "Provide public-safe credential/access readiness refs; do not paste secrets or private tokens.",
                }
            ],
        )

    def test_command_writes_json_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "preflight.json"
            rc = factoryctl.command_hermes_environment_preflight(
                Namespace(
                    json=False,
                    out=out,
                    require=[],
                    credential_ref=["external:operator-confirmed-credentials"],
                    access_ref=["external:operator-confirmed-access"],
                    hermes_home=None,
                    profile_bindings=factoryctl.PROFILE_BINDINGS_PATH,
                    profile_readiness=factoryctl.PROFILE_READINESS_PATH,
                    skill_provider_registry=factoryctl.SKILL_PROVIDER_REGISTRY_PATH,
                    capability_packs=factoryctl.CAPABILITY_PACKS_PATH,
                )
            )

            self.assertEqual(rc, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["record_type"], "hermes_environment_preflight")
            self.assertIn(payload["status"], {"READY", "READY_WITH_DEFERRED"})

    def test_cli_exposes_hermes_environment_preflight(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(MODULE_PATH), "hermes-environment-preflight", "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["record_type"], "hermes_environment_preflight")
        self.assertIn(payload["status"], {"READY", "READY_WITH_DEFERRED", "BLOCKED_WITH_EXACT_HUMAN_INPUT"})

    def test_template_and_generated_report_validate_against_schema(self) -> None:
        schemas = public_json_validator.load_schemas()
        schema = json.loads((ROOT / "schemas" / "hermes-environment-preflight.schema.json").read_text(encoding="utf-8"))
        schemas["hermes-environment-preflight.schema.json"] = schema
        template = json.loads((ROOT / "templates" / "hermes-environment-preflight.json").read_text(encoding="utf-8"))
        generated = factoryctl.build_hermes_environment_preflight_report(
            command_resolver=lambda _name: "/usr/bin/tool",
            created_at="2026-07-01T00:00:00+00:00",
        )

        self.assertEqual(public_json_validator.validate_node(schema, template, "template", schemas=schemas, root_schema=schema), [])
        self.assertEqual(public_json_validator.validate_node(schema, generated, "generated", schemas=schemas, root_schema=schema), [])


if __name__ == "__main__":
    unittest.main()
