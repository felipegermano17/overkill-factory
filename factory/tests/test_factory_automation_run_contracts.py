from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factoryctl.py"
SPEC = importlib.util.spec_from_file_location("factoryctl", MODULE_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl"] = factoryctl
SPEC.loader.exec_module(factoryctl)

VALIDATOR_PATH = ROOT / "scripts" / "validate_public_json_artifacts.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_public_json_artifacts", VALIDATOR_PATH)
assert VALIDATOR_SPEC is not None
public_json_validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
sys.modules["validate_public_json_artifacts"] = public_json_validator
VALIDATOR_SPEC.loader.exec_module(public_json_validator)


def automation_target(**overrides: object) -> dict:
    target = {
        "$schema": "https://overkill-factory.dev/schemas/factory-automation-run-target.schema.json",
        "record_type": "factory_automation_run_target",
        "automation_id": "automation-fixture",
        "created_at": "2026-06-16T00:00:00+00:00",
        "trigger": {
            "trigger_type": "heartbeat",
            "trigger_ref_public_safe": "external:public-heartbeat-trigger",
            "trigger_contract": "Heartbeat must name the target before execution."
        },
        "target": {
            "target_kind": "repo",
            "target_ref": "external:public-overkill-repo",
            "scope_summary": "Read-only public repository audit fixture."
        },
        "owner_worker": "factory-mechanic",
        "runtime_target_ref": "external:public-hermes-runtime",
        "profile_binding_ref": "agents/hermes-profile-bindings.public.json",
        "authority_level": "read_only",
        "allowed_actions": ["inspect_public_repo", "validate_public_contracts"],
        "forbidden_actions": ["publish_private_evidence", "mutate_github_without_explicit_authority"],
        "required_preflight_checks": ["git_state_probe", "public_safety_scan"],
        "required_post_checks": ["public_json_artifact_validation", "public_safety_scan"],
        "human_gate_triggers": ["authority_escalates_to_github_pr"],
        "public_artifact_policy": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
            "no_raw_screenshots_or_logs": True,
            "allowed_ref_classes": ["repo_relative", "external_sanitized_ref", "github_public_ref"]
        },
        "retry_policy": {
            "max_attempts": 3,
            "retry_when": ["non_human_block"],
            "stop_condition": "Stop after repeated non-human repair failure."
        },
        "stop_condition": "Stop when the bounded target has a validated run record.",
        "cleanup_policy": {
            "temporary_artifacts_policy": "Keep raw run outputs outside the public repo.",
            "branch_cleanup_required": False,
            "private_evidence_cleanup_required": True
        },
        "next_safe_action": "Validate target before scheduling."
    }
    target.update(overrides)
    return target


def automation_record(**overrides: object) -> dict:
    record = {
        "$schema": "https://overkill-factory.dev/schemas/factory-automation-run-record.schema.json",
        "record_type": "factory_automation_run_record",
        "automation_id": "automation-fixture",
        "run_id": "run-fixture",
        "started_at": "2026-06-16T00:00:00+00:00",
        "completed_at": "2026-06-16T00:10:00+00:00",
        "trigger_observed": {
            "trigger_type": "heartbeat",
            "trigger_ref_public_safe": "external:public-heartbeat-trigger",
            "observed_at": "2026-06-16T00:00:00+00:00"
        },
        "target_resolved": {
            "target_kind": "repo",
            "target_ref": "external:public-overkill-repo",
            "scope_summary": "Read-only public repository audit fixture."
        },
        "authority_level": "read_only",
        "status": "completed",
        "allowed_actions_executed": True,
        "actions_taken": ["Inspected public contracts.", "Validated public-safe artifacts."],
        "required_preflight_checks": ["git_state_probe", "public_safety_scan"],
        "required_post_checks": ["public_json_artifact_validation", "public_safety_scan"],
        "checks_run": [
            {
                "check_id": "git_state_probe",
                "phase": "preflight",
                "status": "PASS",
                "evidence_ref": "external:public-git-state-summary"
            },
            {
                "check_id": "public_json_artifact_validation",
                "phase": "post",
                "status": "PASS",
                "evidence_ref": "scripts/validate_public_json_artifacts.py"
            },
            {
                "check_id": "public_safety_scan",
                "phase": "post",
                "status": "PASS",
                "evidence_ref": "scripts/public_safety_scan.py"
            }
        ],
        "evidence_refs_public_safe": [
            "schemas/factory-automation-run-record.schema.json",
            "tests/test_factory_automation_run_contracts.py"
        ],
        "git_state": {
            "branch": "main",
            "head_sha": "abcdef1",
            "dirty_state": "clean",
            "remote_state": "pushed",
            "publication_state": "no_publication_attempted"
        },
        "issues_created_or_updated": [],
        "prs_created_or_updated": [],
        "next_safe_action": "Continue with the next bounded audit cycle.",
        "residual_risk": "Fixture proves contract behavior only.",
        "public_artifact_policy": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
            "no_raw_screenshots_or_logs": True
        }
    }
    record.update(overrides)
    return record


class FactoryAutomationRunContractsTest(unittest.TestCase):
    def test_valid_read_only_target_and_record_validate(self) -> None:
        self.assertEqual(factoryctl.validate_factory_automation_run_target(automation_target()), [])
        self.assertEqual(factoryctl.validate_factory_automation_run_record(automation_record()), [])

    def test_missing_trigger_is_rejected(self) -> None:
        target = automation_target()
        del target["trigger"]

        errors = factoryctl.validate_factory_automation_run_target(target)

        self.assertTrue(any("trigger" in error for error in errors), errors)

    def test_missing_target_is_rejected(self) -> None:
        record = automation_record()
        del record["target_resolved"]

        errors = factoryctl.validate_factory_automation_run_record(record)

        self.assertTrue(any("target_resolved" in error for error in errors), errors)

    def test_github_authority_requires_safety_gates_and_human_triggers(self) -> None:
        target = automation_target(
            authority_level="github_pr",
            required_preflight_checks=["git_state_probe"],
            required_post_checks=["public_json_artifact_validation"],
            human_gate_triggers=[]
        )

        errors = factoryctl.validate_factory_automation_run_target(target)

        self.assertTrue(any("preflight checks" in error and "secret_safety_scan" in error for error in errors), errors)
        self.assertTrue(any("post checks" in error and "secret_safety_scan" in error for error in errors), errors)
        self.assertTrue(any("human_gate_triggers" in error for error in errors), errors)

    def test_completed_record_requires_passed_post_checks(self) -> None:
        record = automation_record(checks_run=[])

        errors = factoryctl.validate_factory_automation_run_record(record)

        self.assertTrue(any("checks_run" in error for error in errors), errors)
        self.assertTrue(any("passed post checks" in error for error in errors), errors)

    def test_private_refs_are_rejected(self) -> None:
        record = automation_record(evidence_refs_public_safe=[".tmp/factory-runs/private/raw-log.json"])

        errors = factoryctl.validate_factory_automation_run_record(record)

        self.assertTrue(any("evidence_refs_public_safe[0] must be public-safe" in error for error in errors), errors)

    def test_repo_bound_record_requires_git_state_and_publication_state(self) -> None:
        record = automation_record()
        del record["git_state"]

        errors = factoryctl.validate_factory_automation_run_record(record)

        self.assertTrue(any("repo-bound run requires git_state" in error for error in errors), errors)

    def test_github_record_requires_passed_public_and_secret_safety_checks(self) -> None:
        record = automation_record(
            authority_level="github_pr",
            required_preflight_checks=["public_safety_scan", "secret_safety_scan"],
            required_post_checks=["public_safety_scan", "secret_safety_scan"],
            checks_run=[
                {
                    "check_id": "public_safety_scan",
                    "phase": "post",
                    "status": "PASS",
                    "evidence_ref": "scripts/public_safety_scan.py"
                }
            ],
            prs_created_or_updated=["external:public-pr-245"]
        )

        errors = factoryctl.validate_factory_automation_run_record(record)

        self.assertTrue(any("secret_safety_scan" in error for error in errors), errors)

    def test_external_research_record_allows_public_url_with_synthesis_only(self) -> None:
        record = automation_record(
            target_resolved={
                "target_kind": "external_research_track",
                "target_ref": "external:public-factory-ai-research-track",
                "scope_summary": "Public research track for software factory comparison."
            },
            git_state=None,
            external_research_sources=[
                {
                    "source_url": "https://factory.ai/news/software-factory",
                    "source_type": "official_docs",
                    "public_safe_synthesis": "Factory 2.0 emphasizes end-to-end software factory visibility.",
                    "raw_capture_embedded": False
                }
            ]
        )
        del record["git_state"]

        self.assertEqual(factoryctl.validate_factory_automation_run_record(record), [])

    def test_external_research_rejects_raw_capture_fields(self) -> None:
        record = automation_record(
            target_resolved={
                "target_kind": "external_research_track",
                "target_ref": "external:public-factory-ai-research-track",
                "scope_summary": "Public research track for software factory comparison."
            },
            external_research_sources=[
                {
                    "source_url": "https://factory.ai/news/software-factory",
                    "source_type": "official_docs",
                    "public_safe_synthesis": "Factory 2.0 emphasizes end-to-end software factory visibility.",
                    "raw_capture_embedded": True
                }
            ]
        )
        record["raw_notes"] = "Do not publish raw notes."

        errors = factoryctl.validate_factory_automation_run_record(record)

        self.assertTrue(any("raw dump field raw_notes" in error for error in errors), errors)
        self.assertTrue(any("raw_capture_embedded must be false" in error for error in errors), errors)

    def test_public_templates_validate_with_schema_and_domain_rules(self) -> None:
        schemas = public_json_validator.load_schemas()
        for filename in ("factory-automation-run-target.json", "factory-automation-run-record.json"):
            artifact = json.loads((ROOT / "templates" / filename).read_text(encoding="utf-8"))
            schema = schemas[Path(artifact["$schema"]).name]

            errors = public_json_validator.validate_node(schema, artifact, "$", schemas=schemas, root_schema=schema)
            errors.extend(public_json_validator.validate_domain_rules(artifact, "$"))

            self.assertEqual(errors, [], filename)

    def test_public_validator_rejects_private_automation_ref(self) -> None:
        record = automation_record(evidence_refs_public_safe=[".tmp/factory-runs/private/raw-log.json"])

        errors = public_json_validator.validate_domain_rules(record, "$")

        self.assertTrue(any("$.evidence_refs_public_safe[0]" in error for error in errors), errors)

    def test_factoryctl_cli_validates_target_and_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = Path(tmpdir) / "target.json"
            record_path = Path(tmpdir) / "record.json"
            target_path.write_text(json.dumps(automation_target()), encoding="utf-8")
            record_path.write_text(json.dumps(automation_record()), encoding="utf-8")

            target_result = factoryctl.main_with_args_for_test(["validate-automation-target", str(target_path)])
            record_result = factoryctl.main_with_args_for_test(["validate-automation-record", str(record_path)])

        self.assertEqual(target_result, 0)
        self.assertEqual(record_result, 0)


if __name__ == "__main__":
    unittest.main()
