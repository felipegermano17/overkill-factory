from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "adapters" / "hermes" / "compatibility-check.py"
SPEC = importlib.util.spec_from_file_location("hermes_compatibility_check", MODULE_PATH)
assert SPEC is not None
hermes_compatibility_check = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["hermes_compatibility_check"] = hermes_compatibility_check
SPEC.loader.exec_module(hermes_compatibility_check)


class HermesCompatibilityCheckTest(unittest.TestCase):
    def test_installed_runtime_receipt_bundle_accepts_expected_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            self._with_receipt_expectations(
                required={
                    "proof-pass.json": "PASS",
                    "worker-route-readiness-blocked.json": "BLOCKED",
                },
                optional={"optional-preflight.json": "BLOCKED"},
            )
            try:
                self._write_receipt(tmp_path / "proof-pass.json", "PASS")
                self._write_receipt(tmp_path / "worker-route-readiness-blocked.json", "BLOCKED", checks=[])
                self._write_receipt(tmp_path / "optional-preflight.json", "BLOCKED", checks=[])

                failures = hermes_compatibility_check.installed_runtime_receipt_bundle_failures(tmp_path)

                self.assertEqual(failures, [])
            finally:
                self._restore_receipt_expectations()

    def test_installed_runtime_receipt_bundle_rejects_unexpected_blocked_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            self._with_receipt_expectations(required={"proof-pass.json": "PASS"}, optional={})
            try:
                self._write_receipt(tmp_path / "proof-pass.json", "PASS")
                self._write_receipt(tmp_path / "new-blocker.json", "BLOCKED", checks=[])

                failures = hermes_compatibility_check.installed_runtime_receipt_bundle_failures(tmp_path)

                self.assertIn("new-blocker.json: unexpected BLOCKED receipt", failures)
            finally:
                self._restore_receipt_expectations()

    def test_dashboard_route_inventory_failures_rejects_pending_mutating_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "dashboard-route-inventory-smoke.json"
            receipt_path.write_text(
                json.dumps(
                    {
                        "result": "PASS",
                        "route_inventory": {
                            "mutating_routes": 24,
                            "covered_mutating_route_families": 23,
                            "pending_mutating_route_families": 1,
                        },
                        "coverage_summary": {"pending": ["PATCH /unsafe"]},
                        "evidence_refs": [
                            "validation/hermes-installed-runtime-smoke/"
                            "dashboard-profile-routes-operational-safety-smoke.json",
                            "validation/hermes-installed-runtime-smoke/"
                            "dashboard-orchestration-route-operational-safety-smoke.json",
                        ],
                    }
                ),
                encoding="utf-8",
            )

            failures = hermes_compatibility_check.dashboard_route_inventory_failures(receipt_path)

            self.assertIn("covered_mutating_route_families must equal mutating_routes", failures)
            self.assertIn("pending_mutating_route_families must be 0", failures)
            self.assertIn("coverage_summary.pending must be empty", failures)

    def test_production_update_preflight_accepts_current_blocked_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "real-runtime-update-blocked.json"
            self._write_production_update_preflight(receipt_path, result="BLOCKED")

            failures = hermes_compatibility_check.production_update_preflight_failures(receipt_path)

            self.assertEqual(failures, [])

    def test_production_update_preflight_rejects_unproven_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "real-runtime-update-blocked.json"
            self._write_production_update_preflight(receipt_path, result="PASS")

            failures = hermes_compatibility_check.production_update_preflight_failures(receipt_path)

            self.assertIn("result must remain BLOCKED until real proof refs exist", failures)
            self.assertIn("decision.real_runtime_update must be blocked", failures)

    def test_real_runtime_no_spawn_smoke_accepts_sanitized_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "no-spawn-blocked-board-smoke.json"
            self._write_real_runtime_smoke(receipt_path, check_value=True)

            failures = hermes_compatibility_check.real_runtime_no_spawn_smoke_failures(receipt_path)

            self.assertEqual(failures, [])

    def test_real_runtime_no_spawn_smoke_rejects_false_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "no-spawn-blocked-board-smoke.json"
            self._write_real_runtime_smoke(receipt_path, check_value=False)

            failures = hermes_compatibility_check.real_runtime_no_spawn_smoke_failures(receipt_path)

            self.assertIn("check must be true: task_status_was_blocked", failures)

    def test_real_worker_dispatch_bounded_smoke_accepts_honest_blocked_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "real-worker-dispatch-bounded-smoke.json"
            self._write_real_worker_dispatch_bounded_smoke(receipt_path, result="BLOCKED")

            failures = hermes_compatibility_check.real_worker_dispatch_bounded_smoke_failures(receipt_path)

            self.assertEqual(failures, [])

    def test_real_worker_dispatch_bounded_smoke_rejects_unproven_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "real-worker-dispatch-bounded-smoke.json"
            self._write_real_worker_dispatch_bounded_smoke(receipt_path, result="PASS")

            failures = hermes_compatibility_check.real_worker_dispatch_bounded_smoke_failures(receipt_path)

            self.assertIn("result must remain BLOCKED until worker completion is proven", failures)

    def test_real_worker_terminal_completion_smoke_accepts_auth_blocked_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "real-worker-terminal-completion-smoke.json"
            self._write_real_worker_terminal_completion_smoke(receipt_path, result="BLOCKED")

            failures = hermes_compatibility_check.real_worker_terminal_completion_smoke_failures(receipt_path)

            self.assertEqual(failures, [])

    def test_real_worker_terminal_completion_smoke_accepts_proven_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "real-worker-terminal-completion-smoke.json"
            self._write_real_worker_terminal_completion_smoke(
                receipt_path,
                result="PASS",
                proven=True,
            )

            failures = hermes_compatibility_check.real_worker_terminal_completion_smoke_failures(receipt_path)

            self.assertEqual(failures, [])

    def test_real_worker_terminal_completion_smoke_rejects_unproven_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "real-worker-terminal-completion-smoke.json"
            self._write_real_worker_terminal_completion_smoke(receipt_path, result="PASS")

            failures = hermes_compatibility_check.real_worker_terminal_completion_smoke_failures(receipt_path)

            self.assertIn("check must be true while receipt is PASS: kanban_complete_observed", failures)
            self.assertIn("auth_resolution must be an object when result is PASS", failures)

    def test_worker_profile_live_auth_matrix_smoke_accepts_proven_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "worker-profile-live-auth-matrix-smoke.json"
            self._write_worker_profile_live_auth_matrix_smoke(receipt_path)

            failures = hermes_compatibility_check.worker_profile_live_auth_matrix_smoke_failures(receipt_path)

            self.assertEqual(failures, [])

    def test_worker_profile_live_auth_matrix_smoke_rejects_unproven_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "worker-profile-live-auth-matrix-smoke.json"
            self._write_worker_profile_live_auth_matrix_smoke(
                receipt_path,
                probe_passed_count=45,
                probe_failed_count=1,
                missing_after_count=1,
                all_probe_check=False,
            )

            failures = hermes_compatibility_check.worker_profile_live_auth_matrix_smoke_failures(receipt_path)

            self.assertIn("check must be true: all_non_human_live_provider_model_probes_passed", failures)
            self.assertIn("summary.live_probe_passed_count must be 46", failures)
            self.assertIn("summary.post_repair_missing_profile_count must be 0 when result is PASS", failures)
            self.assertIn("profile_matrix.failed_profiles must be empty", failures)

    def test_real_worker_local_tool_quality_smoke_accepts_bounded_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "real-worker-local-tool-quality-smoke.json"
            self._write_real_worker_local_tool_quality_smoke(receipt_path)

            failures = hermes_compatibility_check.real_worker_local_tool_quality_smoke_failures(receipt_path)

            self.assertEqual(failures, [])

    def test_real_worker_local_tool_quality_smoke_rejects_missing_tool_and_caveat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "real-worker-local-tool-quality-smoke.json"
            self._write_real_worker_local_tool_quality_smoke(
                receipt_path,
                terminal_tool_used=False,
                limits=["bounded smoke"],
            )

            failures = hermes_compatibility_check.real_worker_local_tool_quality_smoke_failures(receipt_path)

            self.assertIn("check must be true: terminal_tool_used", failures)
            self.assertIn("worker_result_contract.terminal_tool_used must be true", failures)
            self.assertIn(
                "limits must include bounded non-production caveat: does not prove external saas",
                failures,
            )

    def test_real_worker_parent_done_reconciliation_smoke_accepts_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "real-worker-parent-done-reconciliation-smoke.json"
            self._write_real_worker_parent_done_reconciliation_smoke(receipt_path)

            failures = hermes_compatibility_check.real_worker_parent_done_reconciliation_smoke_failures(receipt_path)

            self.assertEqual(failures, [])

    def test_real_worker_parent_done_reconciliation_smoke_rejects_missing_allow_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "real-worker-parent-done-reconciliation-smoke.json"
            self._write_real_worker_parent_done_reconciliation_smoke(receipt_path, hook_transition_action="block_transition")

            failures = hermes_compatibility_check.real_worker_parent_done_reconciliation_smoke_failures(receipt_path)

            self.assertIn("summary.hook_transition_action must be allow_done", failures)

    def test_real_worker_specialist_output_quality_smoke_accepts_scanner_backed_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "real-worker-specialist-output-quality-smoke.json"
            self._write_real_worker_specialist_output_quality_smoke(receipt_path)

            failures = hermes_compatibility_check.real_worker_specialist_output_quality_smoke_failures(receipt_path)

            self.assertEqual(failures, [])

    def test_real_worker_specialist_output_quality_smoke_rejects_missing_scanner_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "real-worker-specialist-output-quality-smoke.json"
            self._write_real_worker_specialist_output_quality_smoke(receipt_path, scanner_pass=False)

            failures = hermes_compatibility_check.real_worker_specialist_output_quality_smoke_failures(receipt_path)

            self.assertIn("check must be true: scanner_ok_output_observed", failures)
            self.assertIn("summary.scanner_results.public_safety_scan must be PASS", failures)

    def test_production_rollback_monitoring_smoke_accepts_gateway_recovery_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "production-rollback-monitoring-smoke.json"
            self._write_production_rollback_monitoring_smoke(receipt_path)

            failures = hermes_compatibility_check.production_rollback_monitoring_smoke_failures(receipt_path)

            self.assertEqual(failures, [])

    def test_production_rollback_monitoring_smoke_rejects_missing_recovery_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "production-rollback-monitoring-smoke.json"
            self._write_production_rollback_monitoring_smoke(receipt_path, recovered=False)

            failures = hermes_compatibility_check.production_rollback_monitoring_smoke_failures(receipt_path)

            self.assertIn("check must be true: service_manager_recreated_gateway_process", failures)
            self.assertIn("summary.post_recovery_checks.hermes_status must be PASS", failures)

    def _with_receipt_expectations(self, required: dict[str, str], optional: dict[str, str]) -> None:
        self._old_required_receipts = hermes_compatibility_check.REQUIRED_INSTALLED_RUNTIME_RECEIPTS
        self._old_optional_receipts = hermes_compatibility_check.OPTIONAL_INSTALLED_RUNTIME_RECEIPTS
        hermes_compatibility_check.REQUIRED_INSTALLED_RUNTIME_RECEIPTS = required
        hermes_compatibility_check.OPTIONAL_INSTALLED_RUNTIME_RECEIPTS = optional

    def _restore_receipt_expectations(self) -> None:
        hermes_compatibility_check.REQUIRED_INSTALLED_RUNTIME_RECEIPTS = self._old_required_receipts
        hermes_compatibility_check.OPTIONAL_INSTALLED_RUNTIME_RECEIPTS = self._old_optional_receipts

    def _write_receipt(self, path: Path, result: str, checks: list[dict] | None = None) -> None:
        data: dict[str, object] = {"result": result}
        if checks is not None:
            data["checks"] = checks
        path.write_text(json.dumps(data), encoding="utf-8")

    def _write_production_update_preflight(self, path: Path, result: str) -> None:
        all_proofs = sorted(hermes_compatibility_check.REQUIRED_PRODUCTION_UPDATE_PROOFS)
        blockers = sorted(hermes_compatibility_check.REQUIRED_PRODUCTION_UPDATE_BLOCKERS)
        decision = {
            "real_runtime_update": "blocked" if result == "BLOCKED" else "allowed_for_explicit_operator_gate",
            "worker_task_status": "keep_blocked" if result == "BLOCKED" else "ready_requires_operator_gate",
        }
        required_proofs = []
        for proof_id in all_proofs:
            if proof_id in hermes_compatibility_check.REQUIRED_PRODUCTION_UPDATE_PASSED_PROOFS:
                required_proofs.append(
                    {
                        "id": proof_id,
                        "status": "PASS",
                        "proof_ref": "validation/hermes-production-proof/non-stub-worker-execution.json",
                        "reason": None,
                    }
                )
            else:
                required_proofs.append(
                    {"id": proof_id, "status": "BLOCKED", "proof_ref": None, "reason": "missing proof ref"}
                )
        path.write_text(
            json.dumps(
                {
                    "record_type": "hermes_production_update_preflight",
                    "target": "real-hermes-runtime-update",
                    "result": result,
                    "required_proofs": required_proofs,
                    "blocking_items": blockers,
                    "decision": decision,
                }
            ),
            encoding="utf-8",
        )

    def _write_real_runtime_smoke(self, path: Path, check_value: bool) -> None:
        path.write_text(
            json.dumps(
                {
                    "record_type": "hermes_real_runtime_smoke",
                    "smoke_type": "real_kanban_no_spawn_blocked_board",
                    "result": "PASS",
                    "checks": {"task_status_was_blocked": check_value},
                    "cleanup": {"method": "recoverable board archive", "result": "PASS"},
                    "limits": ["bounded smoke"],
                }
            ),
            encoding="utf-8",
        )

    def _write_real_worker_dispatch_bounded_smoke(self, path: Path, result: str) -> None:
        path.write_text(
            json.dumps(
                {
                    "record_type": "hermes_real_runtime_smoke",
                    "smoke_type": "real_worker_dispatch_bounded_smoke",
                    "result": result,
                    "checks": {
                        "read_only_status_checked_first": True,
                        "disposable_board_created": True,
                        "disposable_task_created": True,
                        "task_assigned_to_worker_profile": True,
                        "dispatch_command_passed": True,
                        "exactly_one_worker_spawned": True,
                        "run_record_exists": True,
                        "worker_pid_recorded": True,
                        "heartbeat_observed": True,
                        "task_reached_terminal_status": False,
                        "task_completed": False,
                        "task_reclaimed_after_timeout": True,
                        "task_blocked_after_timeout": True,
                        "board_was_archived": True,
                        "spawned_process_cleanup_verified": True,
                    },
                    "cleanup": {"method": "bounded cleanup", "result": "PASS"},
                    "limits": ["bounded smoke"],
                }
            ),
            encoding="utf-8",
        )

    def _write_real_worker_terminal_completion_smoke(
        self,
        path: Path,
        result: str,
        proven: bool = False,
    ) -> None:
        checks = {
            "official_hermes_docs_studied_first": True,
            "implementation_completion_path_studied_first": True,
            "disposable_board_created": True,
            "disposable_task_created": True,
            "explicit_terminal_instruction_given": True,
            "worker_profile_had_kanban_worker_skill": True,
            "dispatch_command_passed": True,
            "worker_spawned": True,
            "terminal_status_reached": False,
            "task_completed": False,
            "task_blocked_by_worker": False,
            "kanban_complete_observed": False,
            "kanban_block_observed": False,
            "provider_live_auth_blocker_observed": True,
            "cleanup_verified": True,
            "board_was_archived": True,
        }
        data: dict[str, object] = {
            "record_type": "hermes_real_runtime_smoke",
            "smoke_type": "real_worker_terminal_completion_smoke",
            "result": result,
            "checks": checks,
            "cleanup": {"method": "bounded cleanup", "result": "PASS"},
            "evidence_refs": ["docs/research/hermes-worker-completion-source-notes.md"],
            "limits": ["bounded smoke"],
        }
        if proven:
            checks.update(
                {
                    "global_provider_live_probe_passed": True,
                    "worker_profile_live_probe_passed": True,
                    "terminal_status_reached": True,
                    "task_completed": True,
                    "kanban_complete_observed": True,
                    "summary_marker_observed": True,
                    "provider_live_auth_blocker_observed": False,
                }
            )
            data["auth_resolution"] = {
                "result": "PASS",
                "method": "removed stale local auth shadow and used validated global fallback",
                "profile_ref": "factory-orchestrator",
                "provider_ref": "openai-codex",
                "model_ref": "gpt-5.5",
                "status_only_auth_rejected_as_proof": True,
                "global_provider_probe": "PASS",
                "worker_profile_provider_probe": "PASS",
            }
        path.write_text(
            json.dumps(data),
            encoding="utf-8",
        )

    def _write_worker_profile_live_auth_matrix_smoke(
        self,
        path: Path,
        probe_passed_count: int = 46,
        probe_failed_count: int = 0,
        missing_after_count: int = 0,
        all_probe_check: bool = True,
    ) -> None:
        path.write_text(
            json.dumps(
                {
                    "record_type": "hermes_real_runtime_smoke",
                    "smoke_type": "worker_profile_live_auth_matrix_smoke",
                    "result": "PASS",
                    "provider_ref": "openai-codex",
                    "model_ref": "gpt-5.5",
                    "checks": {
                        "official_hermes_profile_docs_studied_first": True,
                        "official_hermes_worker_completion_docs_studied_first": True,
                        "registry_worker_count_checked": True,
                        "pre_repair_missing_profiles_observed": True,
                        "missing_profiles_created_from_public_worker_registry": True,
                        "new_profiles_created_without_env_clone": True,
                        "no_profile_local_openai_codex_auth_copied": True,
                        "profile_local_auth_shadows_absent_for_registry_workers": True,
                        "all_registry_profiles_exist": True,
                        "all_non_human_profiles_have_config": True,
                        "all_non_human_live_provider_model_probes_passed": all_probe_check,
                        "human_gate_clerk_skipped_as_human_authority": True,
                        "no_raw_runtime_logs_stored": True,
                        "cleanup_or_recovery_path_recorded": True,
                    },
                    "summary": {
                        "registry_worker_count": 47,
                        "non_human_worker_count": 46,
                        "human_worker_count": 1,
                        "pre_repair_existing_profile_count": 27,
                        "pre_repair_missing_profile_count": 20,
                        "profiles_created_count": 20,
                        "post_repair_profile_exists_count": 47 - missing_after_count,
                        "post_repair_missing_profile_count": missing_after_count,
                        "registry_local_openai_codex_shadow_count": 0,
                        "non_human_config_exists_count": 46,
                        "live_probe_attempted_count": 46,
                        "live_probe_passed_count": probe_passed_count,
                        "live_probe_failed_count": probe_failed_count,
                        "human_skipped_count": 1,
                        "new_profiles_env_cloned_count": 0,
                        "created_profiles_without_env_count": 20,
                    },
                    "profile_matrix": {
                        "passed_existing_profiles": [f"existing-{index}" for index in range(26)],
                        "created_and_passed_profiles": [f"created-{index}" for index in range(20)],
                        "human_profiles_skipped": ["human-gate-clerk"],
                        "failed_profiles": ["created-19"] if probe_failed_count else [],
                        "missing_profiles_after_repair": ["created-19"] if missing_after_count else [],
                    },
                    "profile_provisioning": {
                        "created_profile_count": 20,
                        "env_clone_used": False,
                        "profile_local_auth_clone_used": False,
                    },
                    "cleanup": {"method": "bounded cleanup", "result": "PASS"},
                    "evidence_refs": [
                        "agents/worker-registry.public.json",
                        "docs/research/hermes-worker-completion-source-notes.md",
                        "validation/hermes-real-runtime-smoke/real-worker-terminal-completion-smoke.json",
                    ],
                    "limits": ["bounded smoke"],
                }
            ),
            encoding="utf-8",
        )

    def _write_real_worker_local_tool_quality_smoke(
        self,
        path: Path,
        terminal_tool_used: bool = True,
        limits: list[str] | None = None,
    ) -> None:
        path.write_text(
            json.dumps(
                {
                    "record_type": "hermes_real_runtime_smoke",
                    "smoke_type": "real_worker_local_tool_quality_smoke",
                    "result": "PASS",
                    "worker_ref": "public-safety-gate",
                    "checks": {
                        "official_hermes_toolset_docs_studied_first": True,
                        "official_hermes_kanban_tool_docs_studied_first": True,
                        "real_gateway_running_checked_first": True,
                        "disposable_board_created": True,
                        "disposable_task_created": True,
                        "worker_profile_assigned": True,
                        "real_workspace_used": True,
                        "dispatch_command_passed": True,
                        "worker_spawned": True,
                        "kanban_show_required": True,
                        "terminal_tool_used": terminal_tool_used,
                        "read_only_terminal_commands_used": True,
                        "files_checked_with_terminal": True,
                        "git_status_checked_with_terminal": True,
                        "terminal_status_reached": True,
                        "task_completed": True,
                        "kanban_complete_observed": True,
                        "quality_marker_observed": True,
                        "structured_metadata_required": True,
                        "cleanup_verified": True,
                        "board_was_archived": True,
                        "no_raw_runtime_logs_stored": True,
                    },
                    "summary": {
                        "worker": "public-safety-gate",
                        "profile_mode": "closed",
                        "tool_proven": "terminal",
                        "tool_auth_kind": "local Hermes terminal tool authorization",
                        "run_outcome": "completed",
                        "terminal_status": "done",
                        "commands_required_count": 3,
                        "commands_completed_count": 3,
                        "files_checked_count": 2,
                    },
                    "worker_result_contract": {
                        "record_type": "overkill_real_tool_auth_smoke_worker_result",
                        "worker": "public-safety-gate",
                        "terminal_tool_used": terminal_tool_used,
                        "read_only": True,
                        "commands_run": [
                            "pwd",
                            "python path existence check",
                            "git status --short",
                        ],
                        "files_checked": ["README.md", "scripts/factoryctl.py"],
                        "result": "PASS",
                    },
                    "cleanup": {"method": "bounded cleanup", "result": "PASS"},
                    "evidence_refs": [
                        "docs/research/hermes-worker-completion-source-notes.md",
                        "validation/hermes-real-runtime-smoke/real-worker-terminal-completion-smoke.json",
                        "validation/hermes-real-runtime-smoke/worker-profile-live-auth-matrix-smoke.json",
                        "agents/worker-registry.public.json",
                    ],
                    "limits": limits
                    or [
                        "This does not prove external SaaS credentials.",
                        "This does not prove production rollout readiness.",
                    ],
                }
            ),
            encoding="utf-8",
        )

    def _write_real_worker_parent_done_reconciliation_smoke(
        self,
        path: Path,
        hook_transition_action: str = "allow_done",
    ) -> None:
        path.write_text(
            json.dumps(
                {
                    "record_type": "hermes_real_runtime_smoke",
                    "smoke_type": "real_worker_parent_done_reconciliation_smoke",
                    "result": "PASS",
                    "worker_ref": "public-safety-gate",
                    "checks": {
                        "official_hermes_kanban_docs_checked_first": True,
                        "real_gateway_running_checked_first": True,
                        "disposable_board_created": True,
                        "real_worker_spawned": True,
                        "real_worker_reached_done": True,
                        "kanban_complete_observed": True,
                        "terminal_tool_signal_observed": True,
                        "public_safety_result_observed": True,
                        "public_safety_result_sanitized": True,
                        "worker_result_contract_valid": True,
                        "parent_done_hook_executed": True,
                        "parent_done_transition_allowed": True,
                        "missing_blocking_workers_empty": True,
                        "invalid_blocking_workers_empty": True,
                        "public_safety_gate_satisfied": True,
                        "cleanup_verified": True,
                        "board_was_archived": True,
                        "no_raw_runtime_logs_stored": True,
                    },
                    "summary": {
                        "worker": "public-safety-gate",
                        "real_worker_terminal_status": "done",
                        "hook_transition_action": hook_transition_action,
                        "satisfied_before_done_worker": "public-safety-gate",
                    },
                    "cleanup": {"method": "bounded cleanup", "result": "PASS"},
                    "evidence_refs": [
                        "validation/hermes-real-runtime-smoke/real-worker-local-tool-quality-smoke.json",
                        "validation/hermes-real-runtime-smoke/parent-done-reconciliation/worker-results/public_safety_result.json",
                        "validation/hermes-real-runtime-smoke/parent-done-reconciliation/receipt-five.json",
                        "validation/hermes-real-runtime-smoke/parent-done-reconciliation/hook-result.json",
                        "validation/cards/real-worker-parent-done-reconciliation-r1.md",
                    ],
                    "limits": [
                        "This does not prove broad specialist quality.",
                        "Raw runtime output is intentionally excluded.",
                    ],
                }
            ),
            encoding="utf-8",
        )

    def _write_real_worker_specialist_output_quality_smoke(
        self,
        path: Path,
        scanner_pass: bool = True,
    ) -> None:
        path.write_text(
            json.dumps(
                {
                    "record_type": "hermes_real_runtime_smoke",
                    "smoke_type": "real_worker_specialist_output_quality_smoke",
                    "result": "PASS",
                    "worker_ref": "public-safety-gate",
                    "checks": {
                        "real_gateway_running_checked_first": True,
                        "disposable_workspace_created": True,
                        "direct_scanner_precheck_passed": True,
                        "disposable_board_created": True,
                        "disposable_task_created": True,
                        "worker_profile_assigned": True,
                        "worker_spawned": True,
                        "terminal_tool_used": True,
                        "public_safety_scan_command_observed": True,
                        "secret_safety_scan_command_observed": True,
                        "scanner_ok_output_observed": scanner_pass,
                        "public_safety_result_shape_observed": True,
                        "quality_marker_observed": True,
                        "task_completed": True,
                        "kanban_complete_observed": True,
                        "cleanup_verified": True,
                        "board_was_archived": True,
                        "disposable_workspace_removed": True,
                        "no_raw_runtime_logs_stored": True,
                    },
                    "summary": {
                        "worker": "public-safety-gate",
                        "terminal_status": "done",
                        "scanner_results": {
                            "public_safety_scan": "PASS" if scanner_pass else "FAIL",
                            "secret_safety_scan": "PASS",
                        },
                        "worker_result_ref": (
                            "validation/hermes-real-runtime-smoke/specialist-output-quality/"
                            "worker-results/public_safety_result.json"
                        ),
                    },
                    "cleanup": {"method": "bounded cleanup", "result": "PASS"},
                    "evidence_refs": [
                        "validation/hermes-real-runtime-smoke/real-worker-local-tool-quality-smoke.json",
                        "validation/hermes-real-runtime-smoke/specialist-output-quality/worker-results/public_safety_result.json",
                        "scripts/public_safety_scan.py",
                        "scripts/secret_safety_scan.py",
                    ],
                    "limits": [
                        "This proves scanner-backed specialist output quality.",
                        "The target Hermes worker workspace still needs the release package.",
                    ],
                }
            ),
            encoding="utf-8",
        )

    def _write_production_rollback_monitoring_smoke(
        self,
        path: Path,
        recovered: bool = True,
    ) -> None:
        path.write_text(
            json.dumps(
                {
                    "record_type": "hermes_real_runtime_smoke",
                    "smoke_type": "production_rollback_monitoring_smoke",
                    "result": "PASS",
                    "service_ref": "hermes-gateway.service",
                    "checks": {
                        "local_hermes_runbook_studied_first": True,
                        "service_rollback_drill_limitations_studied_first": True,
                        "real_gateway_state_checked_first": True,
                        "systemd_unit_visible": True,
                        "gateway_active_before": True,
                        "restart_policy_always_observed": True,
                        "process_owner_verified": True,
                        "controlled_termination_used": True,
                        "service_manager_recreated_gateway_process": recovered,
                        "gateway_active_after": True,
                        "new_service_process_observed": True,
                        "hermes_status_after_passed": recovered,
                        "kanban_cli_after_passed": True,
                        "direct_systemctl_restart_nonzero_recorded": True,
                        "recovery_start_not_needed": True,
                        "no_raw_runtime_logs_stored": True,
                        "no_runtime_ids_stored": True,
                    },
                    "summary": {
                        "service_manager": "systemd",
                        "unit": "hermes-gateway.service",
                        "recovery_method": "controlled termination and systemd Restart=always recovery",
                        "post_recovery_checks": {
                            "hermes_status": "PASS" if recovered else "FAIL",
                            "kanban_boards_list": "PASS",
                        },
                    },
                    "cleanup": {"method": "gateway recovered", "result": "PASS"},
                    "evidence_refs": [
                        "adapters/hermes/update-runbook.md",
                        "adapters/hermes/service_rollback_drill_smoke.py",
                        "validation/hermes-installed-runtime-smoke/service-rollback-drill-smoke.json",
                    ],
                    "limits": [
                        "This proves real Hermes gateway recovery.",
                        "This does not prove code-version rollback.",
                        "Recovery used systemd Restart=always.",
                    ],
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
