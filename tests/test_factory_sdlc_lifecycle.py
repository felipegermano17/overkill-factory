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


def lifecycle_state(**overrides: object) -> dict:
    state = {
        "$schema": "https://overkill-factory.dev/schemas/factory-sdlc-lifecycle-state.schema.json",
        "record_type": "factory_sdlc_lifecycle_state",
        "lifecycle_id": "lifecycle-fixture-001",
        "created_at": "2026-06-16T00:00:00+00:00",
        "factory_method_version": "OVERKILL_VFINAL",
        "workflow_catalog_ref": "docs/factory-workflow.catalog.json",
        "subject": {
            "subject_type": "factory_improvement",
            "subject_id": "issue-247",
            "scope_type": "factory_execution",
            "source_ref": "https://github.com/felipegermano17/overkill-factory/issues/247"
        },
        "active_phase_id": "F11",
        "delivery_state": "local_only",
        "phase_states": [
            {
                "phase_id": "F11",
                "phase_name": "Executable Plans",
                "status": "ACTIVE",
                "owner_worker": "decomposition-planner",
                "gate_predicate": {
                    "gate_id": "fixture-gate",
                    "result": "PENDING",
                    "predicate": "Fixture lifecycle is under validation.",
                    "evidence_refs": ["schemas/factory-sdlc-lifecycle-state.schema.json"]
                },
                "evidence_refs": [
                    "schemas/factory-sdlc-lifecycle-state.schema.json",
                    "tests/test_factory_sdlc_lifecycle.py"
                ],
                "next_safe_action": "Validate lifecycle state before consumer projection.",
                "human_gate": {
                    "required": False,
                    "classification": "not_required",
                    "authority_ref": "not_required",
                    "factory_may_simulate": False
                },
                "recovery_route": {
                    "required": False,
                    "route_ref": "not_required",
                    "factory_owned_repair_allowed": False,
                    "retry_policy": {
                        "max_attempts": 1,
                        "attempt_number": 1,
                        "stop_condition": "No recovery route is active while the phase is not blocked."
                    }
                }
            }
        ],
        "current_owner_worker": "decomposition-planner",
        "gate_predicate": {
            "gate_id": "fixture-lifecycle-gate",
            "result": "PENDING",
            "predicate": "Fixture lifecycle validates without production claim.",
            "evidence_refs": ["templates/factory-sdlc-lifecycle-state.json"]
        },
        "evidence_refs": [
            "schemas/factory-sdlc-lifecycle-state.schema.json",
            "templates/factory-sdlc-lifecycle-state.json",
            "tests/test_factory_sdlc_lifecycle.py"
        ],
        "next_safe_action": "Use factoryctl validate-sdlc-lifecycle before consumption.",
        "lifecycle_acceptance": {
            "scope_completion_state": "in_progress",
            "proof_level": "static_or_schema_validated",
            "implemented_by_contract": True,
            "runtime_proven": False,
            "production_ready_claimed": False,
            "customer_ready_claimed": False,
            "limits": ["Fixture does not prove runtime or production readiness."]
        },
        "public_private_boundary": {
            "raw_private_evidence_embedded": False,
            "public_safe_refs_only": True,
            "private_runtime_evidence_stays_local": True
        },
        "projection_policy": {
            "cockpit_is_source_of_truth": False,
            "dashboard_visibility_is_evidence": False,
            "consumer_role": "projection_only"
        },
        "linked_operational_evidence_bundle_refs": ["templates/operational-evidence-bundle.json"]
    }
    state.update(overrides)
    return state


class FactorySdlcLifecycleTest(unittest.TestCase):
    def test_lifecycle_template_validates(self) -> None:
        state = json.loads((ROOT / "templates" / "factory-sdlc-lifecycle-state.json").read_text(encoding="utf-8"))

        errors = factoryctl.validate_factory_sdlc_lifecycle_state(state)

        self.assertEqual(errors, [])

    def test_unknown_phase_is_rejected(self) -> None:
        state = lifecycle_state(active_phase_id="F404")
        state["phase_states"][0]["phase_id"] = "F404"

        errors = factoryctl.validate_factory_sdlc_lifecycle_state(state)

        self.assertTrue(any("unknown phase" in error for error in errors), errors)

    def test_unknown_status_is_rejected_by_schema(self) -> None:
        state = lifecycle_state()
        state["phase_states"][0]["status"] = "MAYBE"

        errors = factoryctl.validate_factory_sdlc_lifecycle_state(state)

        self.assertTrue(any("status" in error and "not in enum" in error for error in errors), errors)

    def test_missing_owner_gate_evidence_and_next_action_are_rejected(self) -> None:
        state = lifecycle_state(current_owner_worker="", next_safe_action="", evidence_refs=[])
        phase = state["phase_states"][0]
        phase["owner_worker"] = ""
        phase["evidence_refs"] = []
        phase["next_safe_action"] = ""
        phase["gate_predicate"]["evidence_refs"] = []

        errors = factoryctl.validate_factory_sdlc_lifecycle_state(state)

        self.assertTrue(any("current_owner_worker" in error for error in errors), errors)
        self.assertTrue(any("owner_worker" in error for error in errors), errors)
        self.assertTrue(any("evidence_refs" in error for error in errors), errors)
        self.assertTrue(any("next_safe_action" in error for error in errors), errors)

    def test_non_human_blocked_state_requires_recovery_route(self) -> None:
        state = lifecycle_state()
        state["phase_states"][0]["status"] = "BLOCKED"
        state["phase_states"][0]["gate_predicate"]["result"] = "BLOCK"

        errors = factoryctl.validate_factory_sdlc_lifecycle_state(state)

        self.assertTrue(any("recovery_route.required=true" in error for error in errors), errors)
        self.assertTrue(any("factory-owned repair route" in error for error in errors), errors)

        state["phase_states"][0]["recovery_route"] = {
            "required": True,
            "route_ref": "schemas/factory-recovery-plan.schema.json",
            "factory_owned_repair_allowed": True,
            "retry_policy": {
                "max_attempts": 3,
                "attempt_number": 1,
                "stop_condition": "Escalate after repeated failed factory-owned repair attempts."
            }
        }

        self.assertEqual(factoryctl.validate_factory_sdlc_lifecycle_state(state), [])

    def test_human_gate_boundary_rejects_factory_simulation(self) -> None:
        state = lifecycle_state()
        phase = state["phase_states"][0]
        phase["status"] = "BLOCKED"
        phase["gate_predicate"]["result"] = "BLOCK"
        phase["human_gate"] = {
            "required": True,
            "classification": "not_required",
            "authority_ref": "worker-result",
            "factory_may_simulate": False
        }
        phase["recovery_route"]["factory_owned_repair_allowed"] = True

        errors = factoryctl.validate_factory_sdlc_lifecycle_state(state)

        self.assertTrue(any("human gate classification is ambiguous" in error for error in errors), errors)
        self.assertTrue(any("real authority ref" in error for error in errors), errors)
        self.assertTrue(any("human gate cannot allow factory-owned repair" in error for error in errors), errors)

    def test_private_or_transient_refs_are_rejected(self) -> None:
        state = lifecycle_state(evidence_refs=[".tmp/factory-runs/private-lifecycle.json"])

        errors = factoryctl.validate_factory_sdlc_lifecycle_state(state)

        self.assertTrue(any("evidence_refs[0] must be public-safe" in error for error in errors), errors)

    def test_stale_and_superseded_states_validate_as_explicit_states(self) -> None:
        stale = lifecycle_state()
        stale["phase_states"][0]["status"] = "STALE"
        stale["phase_states"][0]["gate_predicate"]["result"] = "STALE"
        superseded = lifecycle_state()
        superseded["phase_states"][0]["status"] = "SUPERSEDED"
        superseded["phase_states"][0]["gate_predicate"]["result"] = "SUPERSEDED"

        self.assertEqual(factoryctl.validate_factory_sdlc_lifecycle_state(stale), [])
        self.assertEqual(factoryctl.validate_factory_sdlc_lifecycle_state(superseded), [])

    def test_production_readiness_overclaim_is_rejected(self) -> None:
        state = lifecycle_state(
            delivery_state="deployed",
            lifecycle_acceptance={
                "scope_completion_state": "production_complete",
                "proof_level": "implemented_by_contract",
                "implemented_by_contract": True,
                "runtime_proven": False,
                "production_ready_claimed": True,
                "customer_ready_claimed": False,
                "limits": ["Contract-only proof."]
            }
        )

        errors = factoryctl.validate_factory_sdlc_lifecycle_state(state)

        self.assertTrue(any("production readiness requires" in error for error in errors), errors)

    def test_customer_readiness_overclaim_is_rejected(self) -> None:
        acceptance = lifecycle_state()["lifecycle_acceptance"]
        acceptance.update(
            {
                "scope_completion_state": "customer_ready",
                "proof_level": "production_strict",
                "runtime_proven": True,
                "production_ready_claimed": True,
                "customer_ready_claimed": True
            }
        )
        state = lifecycle_state(lifecycle_acceptance=acceptance)

        errors = factoryctl.validate_factory_sdlc_lifecycle_state(state)

        self.assertTrue(any("customer readiness requires" in error for error in errors), errors)

    def test_public_template_validates_with_schema_and_domain_rules(self) -> None:
        schemas = public_json_validator.load_schemas()
        schema = schemas["factory-sdlc-lifecycle-state.schema.json"]
        state = json.loads((ROOT / "templates" / "factory-sdlc-lifecycle-state.json").read_text(encoding="utf-8"))

        schema_errors = public_json_validator.validate_node(schema, state, "$", schemas=schemas, root_schema=schema)
        domain_errors = public_json_validator.validate_domain_rules(state, "$")

        self.assertEqual(schema_errors + domain_errors, [])

    def test_public_validator_rejects_private_lifecycle_ref(self) -> None:
        state = lifecycle_state(evidence_refs=[".tmp/factory-runs/private-lifecycle.json"])

        errors = public_json_validator.validate_domain_rules(state, "$")

        self.assertTrue(any("$.evidence_refs[0]" in error for error in errors), errors)

    def test_factoryctl_cli_validates_lifecycle_independently(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "lifecycle.json"
            path.write_text(json.dumps(lifecycle_state()), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(["validate-sdlc-lifecycle", str(path)])

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
