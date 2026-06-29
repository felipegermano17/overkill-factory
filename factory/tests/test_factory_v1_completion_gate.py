import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FACTORYCTL_PATH = ROOT / "scripts" / "factoryctl.py"
FACTORYCTL_SPEC = importlib.util.spec_from_file_location("factoryctl_v1_completion_gate", FACTORYCTL_PATH)
assert FACTORYCTL_SPEC is not None
factoryctl = importlib.util.module_from_spec(FACTORYCTL_SPEC)
assert FACTORYCTL_SPEC.loader is not None
sys.modules["factoryctl_v1_completion_gate"] = factoryctl
FACTORYCTL_SPEC.loader.exec_module(factoryctl)

VALIDATOR_PATH = ROOT / "scripts" / "validate_public_json_artifacts.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_public_json_artifacts_v1_gate", VALIDATOR_PATH)
assert VALIDATOR_SPEC is not None
public_json_validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
sys.modules["validate_public_json_artifacts_v1_gate"] = public_json_validator
VALIDATOR_SPEC.loader.exec_module(public_json_validator)


def load_template(name: str) -> dict:
    return json.loads((ROOT / "templates" / name).read_text(encoding="utf-8"))


def release_preflight_pass() -> dict:
    return {
        "$schema": "https://overkill-factory.dev/schemas/release-integration-preflight.schema.json",
        "record_type": "release_integration_preflight",
        "created_at": "2026-06-17T00:00:00Z",
        "result": "PASS",
        "branch": {"current": "main", "is_main": True},
        "counts": {
            "status_entries": 0,
            "generated_status_entries": 0,
            "unintegrated_release_entries": 0,
            "release_candidate_entries": 0,
            "generated_receipt_entries": 0,
            "needs_human_review_entries": 0,
            "safe_cleanup_candidates": 0
        },
        "checks": {
            "fresh_preflight_materialization_provided": True,
            "preflight_materializers_passed": True,
            "worktree_public_safety_passed": True,
            "head_public_safety_passed": True,
            "origin_main_public_safety_passed": True,
            "preflight_evidence_refs_exist": True,
            "worktree_inventory_has_no_unknown_entries": True,
            "worktree_inventory_has_no_cleanup_candidates": True,
            "worktree_has_release_candidate_material": False,
            "release_ref_has_no_unintegrated_worktree_entries": True,
            "current_branch_is_not_dirty_main": True
        },
        "release_candidate_plan": {
            "safe_to_prepare_candidate_branch": False,
            "recommended_branch": "not_required",
            "why": "Current release ref has no unintegrated release work.",
            "steps": [],
            "must_not_do": []
        },
        "blocking_items": [],
        "attention_items": [],
        "evidence_refs": ["external:public-release-preflight"],
        "missing_evidence_refs": [],
        "next_required_actions": [],
        "limits": ["Public-safe release integration receipt."]
    }


class FactoryV1CompletionGateTest(unittest.TestCase):
    def test_template_is_valid_blocked_gate_not_live_proof(self) -> None:
        gate = load_template("factory-v1-completion-gate.json")
        schemas = public_json_validator.load_schemas()
        schema = schemas["factory-v1-completion-gate.schema.json"]

        schema_errors = public_json_validator.validate_node(schema, gate, "$", schemas=schemas, root_schema=schema)
        domain_errors = public_json_validator.validate_factory_v1_completion_gate_domain(gate, "$")

        self.assertEqual(schema_errors, [])
        self.assertEqual(domain_errors, [])
        self.assertEqual(gate["decision"], "BLOCKED")
        self.assertFalse(gate["completion_claim_allowed"])

    def test_build_gate_passes_when_current_release_inputs_are_green(self) -> None:
        gate = factoryctl.build_factory_v1_completion_gate(
            readiness_scorecard=load_template("factory-readiness-scorecard.json"),
            signal_corpus=load_template("universal-signal-golden-corpus.json"),
            release_preflight=release_preflight_pass(),
            github_actions_result="PASS",
            open_v1_blockers=0,
            open_prs=0,
            created_at="2026-06-17T00:00:00+00:00",
        )

        errors = factoryctl.validate_factory_v1_completion_gate(gate)
        represented_routes = {item["route_class"] for item in gate["representative_signals"]}

        self.assertEqual(errors, [])
        self.assertEqual(gate["decision"], "PASS")
        self.assertTrue(gate["completion_claim_allowed"])
        self.assertEqual(represented_routes, set(factoryctl.registry_routes(factoryctl.load_route_registry())))
        self.assertTrue(any(item["classification"] == "vnext" for item in gate["classified_findings"]))

    def test_gate_blocks_when_v1_blocker_is_open(self) -> None:
        gate = factoryctl.build_factory_v1_completion_gate(
            readiness_scorecard=load_template("factory-readiness-scorecard.json"),
            signal_corpus=load_template("universal-signal-golden-corpus.json"),
            release_preflight=release_preflight_pass(),
            github_actions_result="PASS",
            open_v1_blockers=0,
            open_prs=0,
            created_at="2026-06-17T00:00:00+00:00",
        )
        gate["classified_findings"].append(
            {
                "finding_id": "manual-public-promise-break",
                "title": "Public promise would be false",
                "classification": "v1_blocker",
                "status": "open",
                "rationale": "This must reopen v1 until fixed.",
                "owner": "factory-orchestrator",
                "evidence_refs": ["external:public-v1-blocker"]
            }
        )

        errors = factoryctl.validate_factory_v1_completion_gate(gate)

        self.assertTrue(any("PASS has open v1 blockers" in error for error in errors), errors)

    def test_v1_completion_gate_cli_writes_pass_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            release_path = tmp / "release-preflight.json"
            out = tmp / "factory-v1-completion-gate.json"
            release_path.write_text(json.dumps(release_preflight_pass()), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(
                [
                    "v1-completion-gate",
                    "--release-preflight",
                    str(release_path),
                    "--github-actions-result",
                    "PASS",
                    "--open-v1-blockers",
                    "0",
                    "--open-prs",
                    "0",
                    "--created-at",
                    "2026-06-17T00:00:00+00:00",
                    "--out",
                    str(out),
                ]
            )
            gate = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(gate["decision"], "PASS")
        self.assertEqual(factoryctl.validate_factory_v1_completion_gate(gate), [])


if __name__ == "__main__":
    unittest.main()
