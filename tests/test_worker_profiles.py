from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


factoryctl = load_module("factoryctl_for_profiles", ROOT / "scripts" / "factoryctl.py")
profile_validator = load_module("validate_worker_profiles", ROOT / "scripts" / "validate_worker_profiles.py")


CONCEPTUAL_ROLE_PROFILE_DUPLICATES = {
    "access-capability-worker",
    "agent-eval-worker",
    "agentic-method-router",
    "budget-cost-worker",
    "data-metrics-worker",
    "dependency-integration-worker",
    "factory-concierge",
    "factory-maturity-auditor",
    "incident-support-worker",
    "platform-devex-worker",
    "privacy-compliance-worker",
    "product-experience-router",
    "product-outcome-discovery-worker",
    "production-readiness-worker",
    "security-architect-worker",
    "software-development-planner",
    "user-docs-onboarding-worker",
}


class WorkerProfilesTest(unittest.TestCase):
    def write_readiness_ledger(self, data: dict) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        path = Path(tempdir.name) / "worker-profile-readiness.public.json"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return path

    def readiness_ledger(self) -> dict:
        return json.loads((ROOT / "agents" / "worker-profile-readiness.public.json").read_text(encoding="utf-8"))

    def test_worker_profiles_are_complete_and_bound_to_hermes(self) -> None:
        self.assertEqual(profile_validator.validate(), [])

    def test_workflow_required_workers_must_have_phase_coverage(self) -> None:
        registry = json.loads((ROOT / "agents" / "worker-registry.public.json").read_text(encoding="utf-8"))
        profiles = json.loads((ROOT / "agents" / "worker-profiles.public.json").read_text(encoding="utf-8"))
        bindings = json.loads((ROOT / "agents" / "hermes-profile-bindings.public.json").read_text(encoding="utf-8"))
        aliases = profile_validator.load_profile_aliases()

        workers = {worker["worker_id"]: worker for worker in registry["workers"]}
        worker = workers["independent-reviewer"]
        worker["phase"] = [phase for phase in worker["phase"] if phase != "F12"]
        profiles["profiles"]["independent-reviewer"]["activation"]["phases"] = [
            phase for phase in profiles["profiles"]["independent-reviewer"]["activation"]["phases"] if phase != "F12"
        ]

        findings = profile_validator.validate_workflow_catalog_alignment(
            workers,
            profiles["profiles"],
            bindings["bindings"],
            aliases,
        )

        self.assertIn("F12: required worker independent-reviewer missing registry phase coverage", findings)
        self.assertIn("F12: required worker independent-reviewer missing profile activation phase", findings)

    def test_missing_worker_profile_readiness_ledger_blocks_profile_readiness_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            missing_path = Path(tempdir) / "missing-readiness.json"

            findings = profile_validator.validate(readiness_ledger_path=missing_path)

        self.assertIn(
            "agents/worker-profile-readiness.public.json: missing worker profile readiness ledger",
            findings,
        )

    def test_worker_profile_readiness_ledger_rejects_wrong_profile(self) -> None:
        ledger = self.readiness_ledger()
        ledger["worker_readiness"]["product-face"]["profile_id"] = "wrong-profile.profile.v1"
        path = self.write_readiness_ledger(ledger)

        findings = profile_validator.validate(readiness_ledger_path=path)

        self.assertIn("product-face: readiness ledger profile_id must match profile", findings)

    def test_current_worker_profile_readiness_cannot_use_stale_evidence(self) -> None:
        ledger = self.readiness_ledger()
        ledger["worker_readiness"]["product-face"].update(
            {
                "smoke_result": "PASS",
                "eval_result": "PASS",
                "readiness_state": "current_profile_ready",
                "checked_at": "2026-06-01T00:00:00Z",
                "freshness_policy": {
                    "current_runtime_claim": True,
                    "current_claim_requires": "fresh sanitized smoke and eval ledger",
                    "max_age_days_for_current_claim": 7,
                },
            }
        )
        path = self.write_readiness_ledger(ledger)

        findings = profile_validator.validate(
            readiness_ledger_path=path,
            now=datetime(2026, 6, 14, tzinfo=timezone.utc),
        )

        self.assertIn("product-face: current_profile_ready evidence is stale", findings)

    def test_current_worker_profile_readiness_passes_with_fresh_smoke_and_eval(self) -> None:
        ledger = self.readiness_ledger()
        ledger["worker_readiness"]["product-face"].update(
            {
                "smoke_result": "PASS",
                "eval_result": "PASS",
                "readiness_state": "current_profile_ready",
                "checked_at": "2026-06-14T00:00:00Z",
                "freshness_policy": {
                    "current_runtime_claim": True,
                    "current_claim_requires": "fresh sanitized smoke and eval ledger",
                    "max_age_days_for_current_claim": 7,
                },
            }
        )
        path = self.write_readiness_ledger(ledger)

        findings = profile_validator.validate(
            readiness_ledger_path=path,
            now=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )

        self.assertEqual(findings, [])

    def test_conceptual_role_names_are_not_registered_as_loose_workers(self) -> None:
        registry = json.loads((ROOT / "agents" / "worker-registry.public.json").read_text(encoding="utf-8"))
        profiles = json.loads((ROOT / "agents" / "worker-profiles.public.json").read_text(encoding="utf-8"))
        bindings = json.loads((ROOT / "agents" / "hermes-profile-bindings.public.json").read_text(encoding="utf-8"))
        permissions = json.loads((ROOT / "agents" / "worker-permission-classes.public.json").read_text(encoding="utf-8"))

        registered_workers = {worker["worker_id"] for worker in registry["workers"]}
        official_profiles = set(profiles["profiles"])
        official_bindings = set(bindings["bindings"])
        worker_permissions = set(permissions["worker_assignments"])
        gateway_profiles = set(permissions["gateway_profile_assignments"])

        for profile_name in sorted(CONCEPTUAL_ROLE_PROFILE_DUPLICATES):
            with self.subTest(profile_name=profile_name):
                self.assertNotIn(profile_name, registered_workers)
                self.assertNotIn(profile_name, official_profiles)
                self.assertNotIn(profile_name, official_bindings)
                self.assertNotIn(profile_name, worker_permissions)
                self.assertNotIn(profile_name, gateway_profiles)

        self.assertEqual(gateway_profiles, {"overkill-factory-gerente"})

    def test_worker_packet_carries_profile_binding(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_product_face.md"
        card = factoryctl.load_json_like(card_path)

        packet = factoryctl.build_worker_packet("product-face", card, card_path)

        self.assertEqual(packet["profile_binding"]["profile_id"], "product-face.profile.v1")
        self.assertEqual(packet["profile_binding"]["hermes_profile_name"], "product-face")
        self.assertEqual(packet["profile_binding"]["gate_timing_source"], "worker_task.gate_timing_class")
        timing_policy = packet["profile_binding"]["factory_gate_timing_policy"]
        self.assertEqual(timing_policy["policy_kind"], "factory_gate_timing_policy")
        self.assertEqual(timing_policy["policy_basis"], "factoryctl.worker_gate_timing_class")
        self.assertEqual(timing_policy["runtime_authority"], "hermes_kanban")
        self.assertNotIn("source_of_truth", timing_policy)
        self.assertIn("overkill-factory", packet["profile_binding"]["skill_refs"])
        self.assertIn("hermes-kanban", packet["profile_binding"]["skill_refs"])
        self.assertFalse(packet["profile_binding"]["can_mutate_card_state"])
        self.assertEqual(packet["profile_binding"]["last_hermes_smoke_ref"], ".tmp/factory-runs/hermes-live/factory12-agent-profile-smoke.md")
        readiness = packet["profile_binding"]["profile_readiness"]
        self.assertEqual(readiness["ledger_ref"], "agents/worker-profile-readiness.public.json")
        self.assertEqual(readiness["readiness_state"], "degraded_without_current_runtime_ledger")
        self.assertFalse(readiness["current_runtime_claim"])

    def test_transition_plan_exposes_profile_binding_on_worker_tasks(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="draft",
            to_status="ready",
        )
        tasks = {task["worker_id"]: task for task in plan["worker_tasks"]}

        self.assertEqual(tasks["solana-quasar-auditor"]["profile_binding"]["profile_id"], "solana-quasar-auditor.profile.v1")
        self.assertIn("solana-ai-kit", tasks["solana-quasar-auditor"]["profile_binding"]["skill_refs"])
        self.assertEqual(tasks["codex-security"]["profile_binding"]["receipt_field"], "security_scan_result")
        self.assertEqual(tasks["supply-chain-gate"]["gate_timing_class"], "blocking-before-ready")
        self.assertEqual(tasks["supply-chain-gate"]["queue_class"], "blocking-before-ready")
        self.assertEqual(tasks["supply-chain-gate"]["runtime_authority"], "hermes_kanban")
        self.assertFalse(tasks["supply-chain-gate"]["local_state_authority"])
        self.assertEqual(tasks["supply-chain-gate"]["profile_binding"]["gate_timing_source"], "worker_task.gate_timing_class")

    def test_profile_binding_queue_is_policy_not_second_runtime_source(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)

        task = factoryctl.build_worker_task("security-orchestrator", card, card_path)

        self.assertEqual(task["queue_class"], "blocking-before-ready")
        self.assertEqual(task["gate_timing_class"], "blocking-before-ready")
        self.assertNotIn("dispatch_queue", task["profile_binding"])
        self.assertNotIn("dispatch_queue_policy", task["profile_binding"])
        timing_policy = task["profile_binding"]["factory_gate_timing_policy"]
        self.assertEqual(timing_policy["policy_basis"], "factoryctl.worker_gate_timing_class")
        self.assertEqual(timing_policy["runtime_authority"], "hermes_kanban")
        self.assertNotIn("source_of_truth", timing_policy)

    def test_worker_profile_cannot_hold_process_authority(self) -> None:
        profile = {
            "mission": "Choose route and phase for the factory from agent context.",
            "activation": {"phases": ["F4"], "surfaces": ["route", "phase"], "risk_floor": "R0", "trigger_words": ["route"]},
            "authority": {
                "may": ["choose route", "approve gates"],
                "must_not": ["waive findings"],
                "human_gate_required_when": ["release"],
            },
        }
        worker = {"authority_max": "choose phase and approve gates"}

        errors = profile_validator.process_authority_leakage_errors("bad-router", profile, worker)

        self.assertTrue(any("choose_route" in error for error in errors), errors)
        self.assertTrue(any("choose_phase" in error for error in errors), errors)
        self.assertTrue(any("approve_gate" in error for error in errors), errors)

    def test_worker_profile_may_describe_process_authority_only_as_denial(self) -> None:
        profile = {
            "mission": "Materialize reducer-approved route records without deciding the factory route.",
            "activation": {"phases": ["F4"], "surfaces": ["route", "phase"], "risk_floor": "R0", "trigger_words": ["route"]},
            "authority": {
                "may": ["materialize reducer-approved worker route records"],
                "must_not": ["approve gates", "choose phase", "choose route"],
                "human_gate_required_when": ["release"],
            },
        }
        worker = {"authority_max": "materialize reducer outputs; cannot choose route, phase or approve gates"}

        self.assertEqual([], profile_validator.process_authority_leakage_errors("good-router", profile, worker))


if __name__ == "__main__":
    unittest.main()
