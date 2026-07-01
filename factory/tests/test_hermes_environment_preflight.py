from __future__ import annotations

import importlib.util
import json
import os
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


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _write_valid_runtime_registry_fixture(root: Path) -> dict[str, Path]:
    profile_readiness = _write_json(
        root / "worker-profile-readiness.json",
        {
            "worker_readiness": {
                "worker-a": {
                    "profile_id": "worker-a.profile.v1",
                    "hermes_profile_name": "worker-a",
                }
            }
        },
    )
    bindings = _write_json(
        root / "bindings.json",
        {
            "bindings": {
                "worker-a": {
                    "worker_id": "worker-a",
                    "profile_id": "worker-a.profile.v1",
                    "hermes_profile_name": "worker-a",
                    "skill_refs": ["overkill-factory"],
                    "result_schema": "schemas/worker-result.schema.json",
                    "receipt_field": "agent_runtime_result",
                }
            }
        },
    )
    providers = _write_json(
        root / "providers.json",
        {
            "providers": [
                {
                    "provider_id": "overkill-factory",
                    "status": "active",
                    "capability_surfaces": ["factory", "runtime"],
                }
            ]
        },
    )
    packs = _write_json(
        root / "packs.json",
        {"packs": {"runtime": {"covers_surfaces": ["runtime", "terminal", "agent", "profile", "adapter"]}}},
    )
    return {
        "profile_readiness": profile_readiness,
        "bindings": bindings,
        "providers": providers,
        "packs": packs,
    }


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
                    "exact_request": "Provide public-safe credential/access readiness refs, valid secret binding refs, non-placeholder env var bindings, least-privilege scope proof, and reachable token/access proof; do not paste secrets or private tokens.",
                }
            ],
        )

    def test_credential_checks_block_placeholder_expired_and_broad_access_without_disclosure(self) -> None:
        missing_env = "HERMES_PREFLIGHT_TEST_MISSING_SECRET"
        os.environ.pop(missing_env, None)
        report = factoryctl.build_hermes_environment_preflight_report(
            require=["credentials"],
            credential_refs=["external:placeholder-secret-ref"],
            credential_env_vars=[missing_env],
            access_refs=["external:operator-access-readiness"],
            required_access_scopes=["repo:read"],
            granted_access_scopes=["admin"],
            token_status_refs=["external:expired-token-status"],
            command_resolver=lambda _name: "/usr/bin/tool",
            created_at="2026-07-01T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "BLOCKED_WITH_EXACT_HUMAN_INPUT")
        credential_check = next(check for check in report["checks"] if check["id"] == "credentials_access_readiness")
        self.assertEqual(credential_check["status"], "BLOCKED")
        self.assertEqual(credential_check["detail"]["placeholder_credential_ref_count"], 1)
        self.assertEqual(credential_check["detail"]["missing_env_var_count"], 1)
        self.assertEqual(credential_check["detail"]["broad_scope_count"], 1)
        self.assertEqual(credential_check["detail"]["inaccessible_token_status_ref_count"], 1)
        public_payload = json.dumps(report, sort_keys=True)
        self.assertNotIn("external:placeholder-secret-ref", public_payload)
        self.assertNotIn(missing_env, public_payload)
        self.assertFalse(report["public_safety"]["credential_values_published"])
        self.assertFalse(report["public_safety"]["secrets_inspected"])

    def test_credential_checks_pass_with_secret_binding_scoped_access_and_active_token_status(self) -> None:
        report = factoryctl.build_hermes_environment_preflight_report(
            require=["credentials"],
            secret_binding_refs=["external:vault-binding-ready"],
            access_refs=["external:operator-access-ready"],
            required_access_scopes=["repo:read"],
            granted_access_scopes=["repo:read"],
            token_status_refs=["external:active-token-status"],
            command_resolver=lambda _name: "/usr/bin/tool",
            created_at="2026-07-01T00:00:00+00:00",
        )

        credential_check = next(check for check in report["checks"] if check["id"] == "credentials_access_readiness")
        self.assertEqual(credential_check["status"], "PASS")
        self.assertEqual(report["human_input_requests"], [])


    def test_unavailable_browser_and_terminal_tools_defer_to_acquisition_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _write_valid_runtime_registry_fixture(Path(tmp))

            report = factoryctl.build_hermes_environment_preflight_report(
                profile_readiness_path=paths["profile_readiness"],
                profile_bindings_path=paths["bindings"],
                skill_provider_registry_path=paths["providers"],
                capability_packs_path=paths["packs"],
                require=["browser"],
                capability_overrides={"browser": False},
                command_resolver=lambda _name: None,
                created_at="2026-07-01T00:00:00+00:00",
            )

        checks = {check["id"]: check for check in report["checks"]}
        self.assertEqual(report["status"], "READY_WITH_DEFERRED")
        self.assertEqual(checks["terminal_file_web"]["status"], "DEFERRED")
        self.assertEqual(checks["browser"]["status"], "DEFERRED")
        self.assertFalse(checks["terminal_file_web"]["detail"]["git_command"])
        routes = {route["capability_id"]: route for route in report["capability_acquisition_routes"]}
        self.assertIn("terminal_file_web", routes)
        self.assertIn("browser", routes)
        self.assertEqual(routes["browser"]["next_action"], "capability-acquisition-run")
        self.assertIn("capability-acquisition-run --capability-gap browser", routes["browser"]["command"])

    def test_disabled_cron_gateway_and_computer_use_capabilities_warn_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _write_valid_runtime_registry_fixture(Path(tmp))

            report = factoryctl.build_hermes_environment_preflight_report(
                profile_readiness_path=paths["profile_readiness"],
                profile_bindings_path=paths["bindings"],
                skill_provider_registry_path=paths["providers"],
                capability_packs_path=paths["packs"],
                require=["cron", "gateway", "computer_use"],
                capability_overrides={"cron": False, "gateway": False, "computer_use": False},
                command_resolver=lambda name: f"/usr/bin/{name}" if name == "git" else None,
                created_at="2026-07-01T00:00:00+00:00",
            )

        checks = {check["id"]: check for check in report["checks"]}
        self.assertEqual(report["status"], "READY_WITH_DEFERRED")
        for capability_id in ["cron", "gateway", "computer_use"]:
            self.assertEqual(checks[capability_id]["status"], "DEFERRED")
            self.assertTrue(checks[capability_id]["required"])
            self.assertTrue(checks[capability_id]["detail"]["factory_acquirable"])
            self.assertFalse(checks[capability_id]["detail"]["available"])
        route_ids = {route["capability_id"] for route in report["capability_acquisition_routes"]}
        self.assertTrue({"cron", "gateway", "computer_use"}.issubset(route_ids))
        self.assertEqual(report["human_input_requests"], [])

    def test_required_domain_provider_access_is_deferred_and_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _write_valid_runtime_registry_fixture(Path(tmp))

            report = factoryctl.build_hermes_environment_preflight_report(
                profile_readiness_path=paths["profile_readiness"],
                profile_bindings_path=paths["bindings"],
                skill_provider_registry_path=paths["providers"],
                capability_packs_path=paths["packs"],
                required_domain_providers=["cloud-infra-security"],
                command_resolver=lambda name: f"/usr/bin/{name}" if name == "git" else None,
                created_at="2026-07-01T00:00:00+00:00",
            )

        checks = {check["id"]: check for check in report["checks"]}
        self.assertEqual(report["status"], "READY_WITH_DEFERRED")
        self.assertEqual(checks["required_domain_provider_access"]["status"], "DEFERRED")
        self.assertEqual(checks["required_domain_provider_access"]["detail"]["missing_domain_provider_count"], 1)
        route = next(route for route in report["capability_acquisition_routes"] if route["capability_id"] == "domain_providers")
        self.assertEqual(route["next_action"], "capability-acquisition-run")
        self.assertIn("domain provider", route["reason"].lower())

    def test_sensitive_credential_values_never_appear_in_report(self) -> None:
        secret_credential = "sensitive-credential-value-must-not-appear"
        secret_access = "sensitive-access-value-must-not-appear"

        report = factoryctl.build_hermes_environment_preflight_report(
            require=["credentials"],
            credential_refs=[secret_credential],
            access_refs=[secret_access],
            command_resolver=lambda name: f"/usr/bin/{name}" if name == "git" else None,
            created_at="2026-07-01T00:00:00+00:00",
        )

        report_text = json.dumps(report, sort_keys=True)
        checks = {check["id"]: check for check in report["checks"]}
        self.assertEqual(checks["credentials_access_readiness"]["status"], "PASS")
        self.assertEqual(checks["credentials_access_readiness"]["detail"]["credential_ref_count"], 1)
        self.assertEqual(checks["credentials_access_readiness"]["detail"]["access_ref_count"], 1)
        self.assertFalse(checks["credentials_access_readiness"]["detail"]["secrets_inspected"])
        self.assertFalse(report["public_safety"]["credential_values_published"])
        self.assertNotIn(secret_credential, report_text)
        self.assertNotIn(secret_access, report_text)

    def test_command_exits_one_for_invalid_registry_and_preserves_remediation_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "preflight.json"
            profile_readiness = _write_json(root / "worker-profile-readiness.json", {"worker_readiness": {}})
            bindings = _write_json(root / "bindings.json", {"bindings": {"worker-a": "malformed-binding-entry"}})
            providers = _write_json(root / "providers.json", {"providers": []})
            packs = _write_json(root / "packs.json", {"packs": {}})

            rc = factoryctl.command_hermes_environment_preflight(
                Namespace(
                    json=False,
                    out=out,
                    require=[],
                    credential_ref=[],
                    credential_env=[],
                    secret_binding_ref=[],
                    access_ref=[],
                    required_access_scope=[],
                    granted_access_scope=[],
                    required_domain_provider=[],
                    token_status_ref=[],
                    hermes_home=None,
                    profile_bindings=bindings,
                    profile_readiness=profile_readiness,
                    skill_provider_registry=providers,
                    capability_packs=packs,
                )
            )

            payload = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(rc, 1)
        self.assertEqual(payload["status"], "BLOCKED_WITH_EXACT_HUMAN_INPUT")
        self.assertEqual(payload["record_type"], "hermes_environment_preflight")
        self.assertFalse(payload["public_safety"]["credential_values_published"])
        checks = {check["id"]: check for check in payload["checks"]}
        self.assertEqual(checks["profiles"]["status"], "FAIL")
        self.assertEqual(checks["worker_bindings"]["status"], "FAIL")
        self.assertEqual(
            payload["human_input_requests"],
            [
                {
                    "input_id": "preflight_contract_failure",
                    "exact_request": "Repair failing public factory preflight contracts, then rerun factoryctl hermes-environment-preflight.",
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
