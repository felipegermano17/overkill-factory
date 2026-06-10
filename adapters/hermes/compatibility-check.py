#!/usr/bin/env python3
"""Check that the public Hermes adapter package still carries core contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "adapters" / "hermes" / "patches" / "0001-add-overkill-factory-10-kanban-gates.patch"
VFINAL_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0002-add-overkill-vfinal-kanban-transition-hook.patch"
VFINAL_WORKER_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0003-materialize-overkill-vfinal-worker-subtasks.patch"
VFINAL_DASHBOARD_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0004-guard-overkill-vfinal-dashboard-ready-route.patch"
VFINAL_WORKER_RESULT_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0005-ingest-overkill-worker-results-from-subtasks.patch"
VFINAL_WORKER_DEPENDENCY_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0006-fix-overkill-worker-subtask-dependency-direction.patch"
VFINAL_DASHBOARD_DEPENDENCY_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0007-add-dashboard-python-multipart-web-extra.patch"
VFINAL_DASHBOARD_DELETE_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0008-guard-overkill-vfinal-dashboard-delete-route.patch"
VFINAL_DASHBOARD_LINKS_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0009-guard-overkill-vfinal-dashboard-links-route.patch"
VFINAL_DASHBOARD_ATTACHMENT_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0010-guard-overkill-vfinal-dashboard-attachment-delete-route.patch"
VFINAL_DASHBOARD_BULK_ARCHIVE_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0011-guard-overkill-vfinal-dashboard-bulk-archive-route.patch"
VFINAL_DASHBOARD_REASSIGN_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0012-guard-overkill-vfinal-dashboard-reassign-route.patch"
VFINAL_DASHBOARD_RECLAIM_TERMINATE_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0013-guard-overkill-vfinal-dashboard-reclaim-terminate-routes.patch"
VFINAL_DASHBOARD_SPECIFY_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0014-guard-overkill-vfinal-dashboard-specify-route.patch"
VFINAL_DASHBOARD_DECOMPOSE_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0015-guard-overkill-vfinal-dashboard-decompose-route.patch"
VFINAL_DASHBOARD_BOARD_DELETE_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0016-guard-overkill-vfinal-dashboard-board-delete-route.patch"
FACTORYCTL = ROOT / "scripts" / "factoryctl.py"
TRANSITION_HOOK = ROOT / "adapters" / "hermes" / "transition_hook.py"
WORKER_ROUTE_READINESS = ROOT / "adapters" / "hermes" / "worker_route_readiness.py"
WORKER_PROFILE_READINESS = ROOT / "adapters" / "hermes" / "worker_profile_readiness_smoke.py"
WORKER_DISPATCH_COMPLETION = ROOT / "adapters" / "hermes" / "worker_dispatch_completion_smoke.py"
WORKER_REAL_PROCESS_LOCAL_STUB = ROOT / "adapters" / "hermes" / "worker_real_process_local_stub_smoke.py"
WORKER_REAL_PROCESS_MATRIX_LOCAL_STUB = ROOT / "adapters" / "hermes" / "worker_real_process_matrix_local_stub_smoke.py"
SERVICE_ROLLBACK_DRILL = ROOT / "adapters" / "hermes" / "service_rollback_drill_smoke.py"
DASHBOARD_DONE_ROUTE_PARITY = ROOT / "adapters" / "hermes" / "dashboard_done_route_parity_smoke.py"
DASHBOARD_CREATE_ROUTE_PARITY = ROOT / "adapters" / "hermes" / "dashboard_create_route_parity_smoke.py"
DASHBOARD_DISPATCH_ROUTE_PARITY = ROOT / "adapters" / "hermes" / "dashboard_dispatch_route_parity_smoke.py"
DASHBOARD_DELETE_ROUTE_GUARD = ROOT / "adapters" / "hermes" / "dashboard_delete_route_guard_smoke.py"
DASHBOARD_LINKS_ROUTE_GUARD = ROOT / "adapters" / "hermes" / "dashboard_links_route_guard_smoke.py"
DASHBOARD_ATTACHMENT_ROUTE_SAFETY = ROOT / "adapters" / "hermes" / "dashboard_attachment_route_safety_smoke.py"
DASHBOARD_BULK_ARCHIVE_GUARD = ROOT / "adapters" / "hermes" / "dashboard_bulk_archive_guard_smoke.py"
DASHBOARD_REASSIGN_ROUTE_GUARD = ROOT / "adapters" / "hermes" / "dashboard_reassign_route_guard_smoke.py"
DASHBOARD_RECLAIM_TERMINATE_GUARD = ROOT / "adapters" / "hermes" / "dashboard_reclaim_terminate_guard_smoke.py"
DASHBOARD_SPECIFY_ROUTE_GUARD = ROOT / "adapters" / "hermes" / "dashboard_specify_route_guard_smoke.py"
DASHBOARD_DECOMPOSE_ROUTE_GUARD = ROOT / "adapters" / "hermes" / "dashboard_decompose_route_guard_smoke.py"
DASHBOARD_COMMENTS_APPEND_ONLY = ROOT / "adapters" / "hermes" / "dashboard_comments_route_append_only_smoke.py"
DASHBOARD_HOME_SUBSCRIBE_VISIBILITY = ROOT / "adapters" / "hermes" / "dashboard_home_subscribe_route_visibility_smoke.py"
DASHBOARD_BOARD_DELETE_ROUTE_GUARD = ROOT / "adapters" / "hermes" / "dashboard_board_delete_route_guard_smoke.py"
DASHBOARD_BOARD_LIFECYCLE_OPERATIONAL_SAFETY = ROOT / "adapters" / "hermes" / "dashboard_board_lifecycle_operational_safety_smoke.py"
DASHBOARD_PROFILE_ROUTES_OPERATIONAL_SAFETY = ROOT / "adapters" / "hermes" / "dashboard_profile_routes_operational_safety_smoke.py"
DASHBOARD_ORCHESTRATION_ROUTE_OPERATIONAL_SAFETY = ROOT / "adapters" / "hermes" / "dashboard_orchestration_route_operational_safety_smoke.py"
INSTALLED_RUNTIME_RECEIPTS_DIR = ROOT / "validation" / "hermes-installed-runtime-smoke"
DASHBOARD_ROUTE_INVENTORY_RECEIPT = INSTALLED_RUNTIME_RECEIPTS_DIR / "dashboard-route-inventory-smoke.json"
PRODUCTION_UPDATE_PREFLIGHT_RECEIPT = (
    ROOT / "validation" / "hermes-production-update-preflight" / "real-runtime-update-blocked.json"
)
REAL_RUNTIME_NO_SPAWN_SMOKE_RECEIPT = (
    ROOT / "validation" / "hermes-real-runtime-smoke" / "no-spawn-blocked-board-smoke.json"
)
REAL_WORKER_DISPATCH_BOUNDED_SMOKE_RECEIPT = (
    ROOT / "validation" / "hermes-real-runtime-smoke" / "real-worker-dispatch-bounded-smoke.json"
)
REAL_WORKER_TERMINAL_COMPLETION_SMOKE_RECEIPT = (
    ROOT / "validation" / "hermes-real-runtime-smoke" / "real-worker-terminal-completion-smoke.json"
)
WORKER_PROFILE_LIVE_AUTH_MATRIX_SMOKE_RECEIPT = (
    ROOT / "validation" / "hermes-real-runtime-smoke" / "worker-profile-live-auth-matrix-smoke.json"
)
REAL_WORKER_LOCAL_TOOL_QUALITY_SMOKE_RECEIPT = (
    ROOT / "validation" / "hermes-real-runtime-smoke" / "real-worker-local-tool-quality-smoke.json"
)
REAL_WORKER_PARENT_DONE_RECONCILIATION_SMOKE_RECEIPT = (
    ROOT / "validation" / "hermes-real-runtime-smoke" / "real-worker-parent-done-reconciliation-smoke.json"
)
REAL_WORKER_SPECIALIST_OUTPUT_QUALITY_SMOKE_RECEIPT = (
    ROOT / "validation" / "hermes-real-runtime-smoke" / "real-worker-specialist-output-quality-smoke.json"
)
PRODUCTION_ROLLBACK_MONITORING_SMOKE_RECEIPT = (
    ROOT / "validation" / "hermes-real-runtime-smoke" / "production-rollback-monitoring-smoke.json"
)

REQUIRED_PRODUCTION_UPDATE_PROOFS = {
    "non_stub_worker_execution",
    "real_tool_auth",
    "specialist_output_quality",
    "real_worker_done_reconciliation",
    "production_rollback_monitoring",
    "operator_control_tower",
    "complete_update_receipt",
}

REQUIRED_PRODUCTION_UPDATE_PASSED_PROOFS = {
    "non_stub_worker_execution",
    "real_tool_auth",
    "specialist_output_quality",
    "real_worker_done_reconciliation",
    "production_rollback_monitoring",
}

REQUIRED_PRODUCTION_UPDATE_BLOCKERS = REQUIRED_PRODUCTION_UPDATE_PROOFS - REQUIRED_PRODUCTION_UPDATE_PASSED_PROOFS

REQUIRED_INSTALLED_RUNTIME_RECEIPTS = {
    "installed-runtime-smoke.json": "PASS",
    "worker-subtasks-smoke.json": "PASS",
    "worker-subtasks-idempotency-smoke.json": "PASS",
    "dashboard-route-parity-smoke.json": "PASS",
    "worker-result-ingestion-smoke.json": "PASS",
    "worker-dispatch-route-smoke.json": "PASS",
    "worker-real-process-auth-block-smoke.json": "PASS",
    "worker-route-readiness-blocked.json": "BLOCKED",
    "worker-profile-readiness-local-stub-smoke.json": "PASS",
    "worker-dispatch-completion-smoke.json": "PASS",
    "worker-real-process-local-stub-smoke.json": "PASS",
    "worker-real-process-matrix-local-stub-smoke.json": "PASS",
    "dashboard-create-route-parity-smoke.json": "PASS",
    "dashboard-dispatch-route-parity-smoke.json": "PASS",
    "dashboard-delete-route-guard-smoke.json": "PASS",
    "dashboard-links-route-guard-smoke.json": "PASS",
    "dashboard-attachment-route-safety-smoke.json": "PASS",
    "dashboard-bulk-archive-guard-smoke.json": "PASS",
    "dashboard-reassign-route-guard-smoke.json": "PASS",
    "dashboard-reclaim-terminate-guard-smoke.json": "PASS",
    "dashboard-specify-route-guard-smoke.json": "PASS",
    "dashboard-decompose-route-guard-smoke.json": "PASS",
    "dashboard-comments-route-append-only-smoke.json": "PASS",
    "dashboard-home-subscribe-route-visibility-smoke.json": "PASS",
    "dashboard-board-delete-route-guard-smoke.json": "PASS",
    "dashboard-board-lifecycle-operational-safety-smoke.json": "PASS",
    "dashboard-profile-routes-operational-safety-smoke.json": "PASS",
    "dashboard-orchestration-route-operational-safety-smoke.json": "PASS",
    "dashboard-done-route-parity-smoke.json": "PASS",
    "dashboard-route-inventory-smoke.json": "PASS",
    "service-rollback-drill-smoke.json": "PASS",
}

OPTIONAL_INSTALLED_RUNTIME_RECEIPTS = {
    "worker-route-readiness-preflight.json": "BLOCKED",
}

REQUIRED_PATCH_MARKERS = [
    "_overkill_is_v35_card",
    "_overkill_validate_v35_card",
    "_overkill_validate_v35_completion",
    "OVERKILL_V3_5_FACTORY_10",
    "receipt_five",
    "kanban_transition_event",
    "security_scan_packet",
    "security_scan_result",
]

REQUIRED_VFINAL_PATCH_MARKERS = [
    "diff --git a/hermes_cli/kanban_db.py b/hermes_cli/kanban_db.py",
    "OverkillFactoryTransitionBlocked",
    "OVERKILL_FACTORY_KANBAN_GATE",
    "kanban_event_bridge.py",
    "overkill_factory_transition_gate",
    "overkill_factory_transition_blocked",
    "to_status=\"ready\"",
    "to_status=\"done\"",
    "from_status=\"created\"",
    "allowed direct ready creation",
    "allowed automatic ready recompute",
    "allowed unblock to ready",
    "def create_task(",
    "def recompute_ready(",
    "def unblock_task(",
    "def promote_task(",
    "def complete_task(",
]

REQUIRED_VFINAL_WORKER_PATCH_MARKERS = [
    "diff --git a/hermes_cli/kanban_db.py b/hermes_cli/kanban_db.py",
    "OVERKILL_FACTORY_CREATE_WORKER_TASKS",
    "OVERKILL_FACTORY_WORKER_TASK_STATUS",
    "record_type\": \"overkill_factory_worker_subtask",
    "overkill_worker_tasks_materialized",
    "materialized_worker_tasks",
    "_overkill_materialize_worker_tasks_in_txn",
    "allow_and_create_worker_tasks",
    "INSERT OR IGNORE INTO task_links",
    "worker-route parity is proven",
]

REQUIRED_VFINAL_DASHBOARD_PATCH_MARKERS = [
    "diff --git a/plugins/kanban/dashboard/plugin_api.py b/plugins/kanban/dashboard/plugin_api.py",
    "def _is_overkill_factory_card(",
    "def _set_ready_status(",
    "kanban_db.promote_task(",
    "actor=\"dashboard\"",
    "actor=\"dashboard-bulk\"",
    "ready_error",
    "Overkill Factory cards cannot move directly to 'ready'",
]

REQUIRED_VFINAL_WORKER_RESULT_PATCH_MARKERS = [
    "diff --git a/hermes_cli/kanban_db.py b/hermes_cli/kanban_db.py",
    "record_type\") != \"overkill_factory_worker_subtask",
    "_overkill_worker_results_dir",
    "_overkill_worker_result_from_completion",
    "_overkill_persist_worker_result_from_subtask",
    "overkill_worker_result",
    "overkill_worker_result_ingested",
    "Use this worker result during parent done reconciliation.",
]

REQUIRED_VFINAL_WORKER_DEPENDENCY_PATCH_MARKERS = [
    "diff --git a/hermes_cli/kanban_db.py b/hermes_cli/kanban_db.py",
    "Worker subtasks are prerequisites for the parent Factory card.",
    "Linking worker -> parent lets the dispatcher run the worker",
    "(worker_task_id, parent_task_id)",
    "Preserve worker -> parent on idempotent updates too.",
]

REQUIRED_VFINAL_DASHBOARD_DEPENDENCY_PATCH_MARKERS = [
    "diff --git a/pyproject.toml b/pyproject.toml",
    "diff --git a/uv.lock b/uv.lock",
    "python-multipart==0.0.27",
    "File/Form parameters",
    "extra == 'web'",
]

REQUIRED_VFINAL_DASHBOARD_DELETE_PATCH_MARKERS = [
    "diff --git a/plugins/kanban/dashboard/plugin_api.py b/plugins/kanban/dashboard/plugin_api.py",
    "def _is_overkill_worker_subtask(",
    "Overkill Factory cards and worker subtasks cannot be",
    "hard-deleted from dashboard/API",
    "operator-safe path",
]

REQUIRED_VFINAL_DASHBOARD_LINKS_PATCH_MARKERS = [
    "diff --git a/plugins/kanban/dashboard/plugin_api.py b/plugins/kanban/dashboard/plugin_api.py",
    "def _guard_overkill_link_edit(",
    "Overkill Factory card dependencies cannot be edited from",
    "operator-safe dependency workflow",
    "def add_link(",
    "def delete_link(",
]

REQUIRED_VFINAL_DASHBOARD_ATTACHMENT_PATCH_MARKERS = [
    "diff --git a/plugins/kanban/dashboard/plugin_api.py b/plugins/kanban/dashboard/plugin_api.py",
    "def remove_attachment(",
    "kanban_db.get_attachment(",
    "attachments_root(board=board).resolve()",
    "attachment file path is outside the board attachment root",
    "kanban_db.delete_attachment(",
]

REQUIRED_VFINAL_DASHBOARD_BULK_ARCHIVE_PATCH_MARKERS = [
    "diff --git a/plugins/kanban/dashboard/plugin_api.py b/plugins/kanban/dashboard/plugin_api.py",
    "def bulk_update(",
    "payload.archive",
    "Overkill Factory cards and worker subtasks cannot be",
    "archived from dashboard/API bulk actions",
    "operator-safe archive workflow",
]

REQUIRED_VFINAL_DASHBOARD_REASSIGN_PATCH_MARKERS = [
    "diff --git a/plugins/kanban/dashboard/plugin_api.py b/plugins/kanban/dashboard/plugin_api.py",
    "def reassign_task_endpoint(",
    "worker identity is part",
    "of the Factory method contract",
    "operator-safe recovery workflow",
]

REQUIRED_VFINAL_DASHBOARD_RECLAIM_TERMINATE_PATCH_MARKERS = [
    "diff --git a/plugins/kanban/dashboard/plugin_api.py b/plugins/kanban/dashboard/plugin_api.py",
    "def _guard_overkill_recovery_action(",
    "def terminate_run_endpoint(",
    "def reclaim_task_endpoint(",
    "Overkill Factory cards and worker subtasks cannot be",
    "operator-safe recovery workflow",
]

REQUIRED_VFINAL_DASHBOARD_SPECIFY_PATCH_MARKERS = [
    "diff --git a/plugins/kanban/dashboard/plugin_api.py b/plugins/kanban/dashboard/plugin_api.py",
    "def specify_task_endpoint(",
    "Overkill Factory cards and worker subtasks cannot be",
    "specified from dashboard/API",
    "operator-safe specification",
]

REQUIRED_VFINAL_DASHBOARD_DECOMPOSE_PATCH_MARKERS = [
    "diff --git a/plugins/kanban/dashboard/plugin_api.py b/plugins/kanban/dashboard/plugin_api.py",
    "def decompose_task_endpoint(",
    "Overkill Factory cards and worker subtasks cannot be",
    "decomposed from dashboard/API",
    "vFinal method router",
    "operator-safe decomposition workflow",
]

REQUIRED_VFINAL_DASHBOARD_BOARD_DELETE_PATCH_MARKERS = [
    "diff --git a/plugins/kanban/dashboard/plugin_api.py b/plugins/kanban/dashboard/plugin_api.py",
    "def _board_overkill_task_refs(",
    "def _guard_overkill_board_removal(",
    "Boards containing Overkill Factory cards or worker subtasks",
    "board retirement workflow",
    "def delete_board(",
]

REQUIRED_FACTORYCTL_MARKERS = [
    "OVERKILL_VFINAL",
    "security-architect-worker",
    "access-capability-worker",
    "factory-maturity-auditor",
    "public-safety-gate",
    "autoreview-gate",
    "handoff-packer",
    "remote-proof-runner",
    "agentic-ai-security-specialist",
    "supply-chain-gate",
]

REQUIRED_TRANSITION_HOOK_MARKERS = [
    "overkill_factory_hermes_transition_hook",
    "persist_worker_tasks",
    "allow_and_create_worker_tasks",
    "block_transition",
    "worker-ledger",
    "completion_reconciliation",
]

REQUIRED_WORKER_ROUTE_READINESS_MARKERS = [
    "overkill_factory_hermes_worker_route_readiness.v1",
    "Do not set OVERKILL_FACTORY_WORKER_TASK_STATUS=ready in production",
    "provider_auto_without_detectable_auth",
    "local_endpoint_unreachable",
    "local_endpoint_model_listed",
    "local_endpoint_model_missing",
    "redacted-hermes-home",
]

REQUIRED_WORKER_PROFILE_READINESS_MARKERS = [
    "overkill_factory_hermes_worker_profile_readiness_smoke.v1",
    "disposable-local-openai-stub-only",
    "local-loopback-openai-compatible-stub",
    "OVERKILL_LOCAL_STUB_OK",
    "does not prove real model quality",
    "check_readiness",
]

REQUIRED_WORKER_DISPATCH_COMPLETION_MARKERS = [
    "VFINAL-HERMES-WORKER-DISPATCH-COMPLETION-SMOKE",
    "synthetic worker completion",
    "worker_result_ingested",
    "OVERKILL_FACTORY_WORKER_TASK_STATUS",
    "allow_non_disposable",
    "does not authorize updating a real Hermes runtime",
]

REQUIRED_WORKER_REAL_PROCESS_LOCAL_STUB_MARKERS = [
    "VFINAL-HERMES-WORKER-REAL-PROCESS-LOCAL-STUB-SMOKE",
    "LocalToolCallStub",
    "text/event-stream",
    "kanban_complete",
    "real Hermes child process",
    "does not authorize updating a real Hermes runtime",
]

REQUIRED_WORKER_REAL_PROCESS_MATRIX_LOCAL_STUB_MARKERS = [
    "VFINAL-HERMES-WORKER-REAL-PROCESS-MATRIX-LOCAL-STUB-SMOKE",
    "worker_count",
    "worker_real_process_local_stub_smoke",
    "broad real Hermes child-process/tool-loop parity",
    "does not authorize updating a real Hermes runtime",
]

REQUIRED_SERVICE_ROLLBACK_DRILL_MARKERS = [
    "VFINAL-HERMES-SERVICE-ROLLBACK-DRILL",
    "rollback-by-release-restore",
    "baseline source restore",
    "service_stop_start_probe",
    "patched_state_restored_after_drill",
    "does not authorize updating a real Hermes runtime",
]

REQUIRED_DASHBOARD_DONE_ROUTE_PARITY_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-DONE-ROUTE-PARITY-SMOKE",
    "status=done",
    "weak_dashboard_done_rejected_by_gate",
    "positive_dashboard_done_allowed_by_gate",
    "bulk_dashboard_done_rejected_by_gate",
    "does not start an authenticated HTTP dashboard server",
]

REQUIRED_DASHBOARD_CREATE_ROUTE_PARITY_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-CREATE-ROUTE-PARITY-SMOKE",
    "POST /tasks",
    "create_body_status_field_not_exposed",
    "weak_dashboard_create_blocked_by_gate",
    "positive_dashboard_create_allowed_by_gate",
    "worker_subtasks_created_blocked",
    "does not start an authenticated HTTP dashboard server",
]

REQUIRED_DASHBOARD_DISPATCH_ROUTE_PARITY_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-DISPATCH-ROUTE-PARITY-SMOKE",
    "POST /dispatch",
    "dashboard_dispatch_blocked_workers_no_spawn",
    "dashboard_dispatch_parent_not_spawned_before_workers_done",
    "dashboard_dispatch_selected_ready_worker_spawned",
    "The spawn function was stubbed",
    "does not start an authenticated HTTP dashboard server",
]

REQUIRED_DASHBOARD_DELETE_ROUTE_GUARD_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-DELETE-ROUTE-GUARD-SMOKE",
    "DELETE /tasks/{task_id}",
    "dashboard_delete_parent_vfinal_blocked",
    "dashboard_delete_worker_subtask_blocked",
    "dashboard_delete_normal_task_allowed",
    "worker_prerequisite_links_preserved",
    "does not start an authenticated HTTP dashboard server",
]

REQUIRED_DASHBOARD_LINKS_ROUTE_GUARD_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-LINKS-ROUTE-GUARD-SMOKE",
    "/links",
    "dashboard_delete_worker_parent_link_blocked",
    "dashboard_add_factory_link_blocked",
    "dashboard_normal_link_add_delete_allowed",
    "worker_prerequisite_links_preserved",
    "does not start an authenticated HTTP dashboard server",
]

REQUIRED_DASHBOARD_ATTACHMENT_ROUTE_SAFETY_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-ATTACHMENT-ROUTE-SAFETY-SMOKE",
    "POST /tasks/{task_id}/attachments",
    "DELETE /attachments/{attachment_id}",
    "attachment_traversal_filename_sanitized",
    "attachment_delete_outside_root_blocked",
    "attachment_normal_delete_allowed",
    "does not start an authenticated HTTP dashboard server",
]

REQUIRED_DASHBOARD_BULK_ARCHIVE_GUARD_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-BULK-ARCHIVE-GUARD-SMOKE",
    "POST /tasks/bulk",
    "archive=True",
    "dashboard_bulk_archive_parent_vfinal_blocked",
    "dashboard_bulk_archive_worker_subtask_blocked",
    "dashboard_bulk_archive_normal_task_allowed",
    "does not start an authenticated HTTP dashboard server",
]

REQUIRED_DASHBOARD_REASSIGN_ROUTE_GUARD_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-REASSIGN-ROUTE-GUARD-SMOKE",
    "POST /tasks/{task_id}/reassign",
    "dashboard_reassign_parent_vfinal_blocked",
    "dashboard_reassign_worker_subtask_blocked",
    "dashboard_reassign_normal_task_allowed",
    "does not start an authenticated HTTP dashboard server",
]

REQUIRED_DASHBOARD_RECLAIM_TERMINATE_GUARD_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-RECLAIM-TERMINATE-GUARD-SMOKE",
    "POST /tasks/{task_id}/reclaim",
    "POST /runs/{run_id}/terminate",
    "dashboard_reclaim_worker_subtask_blocked",
    "dashboard_terminate_worker_run_blocked",
    "dashboard_reclaim_normal_task_allowed",
    "dashboard_terminate_normal_run_allowed",
    "does not start an authenticated HTTP dashboard server",
]

REQUIRED_DASHBOARD_SPECIFY_ROUTE_GUARD_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-SPECIFY-ROUTE-GUARD-SMOKE",
    "POST /tasks/{task_id}/specify",
    "dashboard_specify_parent_vfinal_blocked",
    "dashboard_specify_worker_subtask_blocked",
    "specifier_not_called_for_vfinal_tasks",
    "dashboard_specify_normal_task_allowed",
    "does not start an authenticated HTTP dashboard server",
]

REQUIRED_DASHBOARD_DECOMPOSE_ROUTE_GUARD_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-DECOMPOSE-ROUTE-GUARD-SMOKE",
    "POST /tasks/{task_id}/decompose",
    "dashboard_decompose_parent_vfinal_blocked",
    "dashboard_decompose_worker_subtask_blocked",
    "decomposer_not_called_for_vfinal_tasks",
    "dashboard_decompose_normal_task_allowed",
    "does not start an authenticated HTTP dashboard server",
]

REQUIRED_DASHBOARD_COMMENTS_APPEND_ONLY_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-COMMENTS-APPEND-ONLY-SMOKE",
    "POST /tasks/{task_id}/comments",
    "dashboard_comment_parent_vfinal_allowed",
    "dashboard_comment_worker_subtask_allowed",
    "dashboard_comment_parent_append_only",
    "dashboard_comment_worker_append_only",
    "Comments are operator notes; this smoke does not make comments authoritative gate evidence.",
    "does not start an authenticated HTTP dashboard server",
]

REQUIRED_DASHBOARD_HOME_SUBSCRIBE_VISIBILITY_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-HOME-SUBSCRIBE-VISIBILITY-SMOKE",
    "POST /tasks/{task_id}/home-subscribe/{platform}",
    "DELETE /tasks/{task_id}/home-subscribe/{platform}",
    "dashboard_home_subscribe_parent_vfinal_allowed",
    "dashboard_home_unsubscribe_worker_subtask_allowed",
    "dashboard_home_parent_visibility_only",
    "dashboard_home_worker_visibility_only",
    "Home subscriptions are visibility/notification routing only; they are not authoritative gate evidence.",
    "does not start an authenticated HTTP dashboard server",
]

REQUIRED_DASHBOARD_BOARD_DELETE_ROUTE_GUARD_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-BOARD-DELETE-ROUTE-GUARD-SMOKE",
    "DELETE /boards/{slug}",
    "dashboard_board_archive_factory_board_blocked",
    "dashboard_board_hard_delete_factory_board_blocked",
    "dashboard_board_archive_normal_board_allowed",
    "dashboard_board_hard_delete_normal_board_allowed",
    "receipt_sanitizes_local_paths",
    "does not start a production dashboard server",
]

REQUIRED_DASHBOARD_BOARD_LIFECYCLE_OPERATIONAL_SAFETY_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-BOARD-LIFECYCLE-OPERATIONAL-SAFETY-SMOKE",
    "POST /boards",
    "PATCH /boards/{slug}",
    "POST /boards/{slug}/switch",
    "dashboard_board_create_invalid_slug_rejected",
    "dashboard_board_patch_metadata_only_allowed",
    "dashboard_board_switch_updates_current_pointer",
    "factory_board_tasks_unchanged",
    "factory_worker_prerequisites_preserved",
    "does not start a production dashboard server",
]

REQUIRED_DASHBOARD_PROFILE_ROUTES_OPERATIONAL_SAFETY_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-PROFILE-ROUTES-OPERATIONAL-SAFETY-SMOKE",
    "PATCH /profiles/{profile_name}",
    "POST /profiles/{profile_name}/describe-auto",
    "dashboard_profile_patch_existing_allowed",
    "dashboard_profile_describe_auto_stubbed_allowed",
    "factory_board_tasks_unchanged",
    "factory_worker_prerequisites_preserved",
    "does not start a production dashboard server",
]

REQUIRED_DASHBOARD_ORCHESTRATION_ROUTE_OPERATIONAL_SAFETY_MARKERS = [
    "VFINAL-HERMES-DASHBOARD-ORCHESTRATION-ROUTE-OPERATIONAL-SAFETY-SMOKE",
    "PUT /orchestration",
    "dashboard_orchestration_missing_profile_rejected",
    "dashboard_orchestration_valid_update_allowed",
    "dashboard_orchestration_clear_overrides_allowed",
    "factory_board_tasks_unchanged",
    "factory_worker_prerequisites_preserved",
    "does not start a production dashboard server",
]


def missing_markers(path: Path, markers: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing file: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [marker for marker in markers if marker not in text]


def read_json_object(path: Path) -> tuple[dict | None, str | None]:
    if not path.exists():
        return None, f"missing file: {path}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"
    if not isinstance(data, dict):
        return None, "JSON root must be an object"
    return data, None


def installed_runtime_receipt_bundle_failures(receipts_dir: Path) -> list[str]:
    if not receipts_dir.exists():
        return [f"missing directory: {receipts_dir}"]

    failures: list[str] = []
    expected_receipts = {
        **REQUIRED_INSTALLED_RUNTIME_RECEIPTS,
        **OPTIONAL_INSTALLED_RUNTIME_RECEIPTS,
    }

    for name, expected_result in sorted(REQUIRED_INSTALLED_RUNTIME_RECEIPTS.items()):
        data, error = read_json_object(receipts_dir / name)
        if error:
            failures.append(f"{name}: {error}")
            continue
        result = data.get("result")
        if result != expected_result:
            failures.append(f"{name}: result must be {expected_result}")
        if expected_result == "PASS" and data.get("blocking_findings") is True:
            failures.append(f"{name}: blocking_findings must not be true for PASS receipt")
        if expected_result == "BLOCKED" and data.get("checks") is not None and not isinstance(data.get("checks"), list):
            failures.append(f"{name}: checks must be a list when present")

    for name, expected_result in sorted(OPTIONAL_INSTALLED_RUNTIME_RECEIPTS.items()):
        path = receipts_dir / name
        if not path.exists():
            continue
        data, error = read_json_object(path)
        if error:
            failures.append(f"{name}: {error}")
            continue
        if data.get("result") != expected_result:
            failures.append(f"{name}: result must be {expected_result}")

    for path in sorted(receipts_dir.glob("*.json")):
        data, error = read_json_object(path)
        if error:
            failures.append(f"{path.name}: {error}")
            continue
        result = data.get("result")
        if result == "FAIL":
            failures.append(f"{path.name}: result must not be FAIL")
        elif result not in {"PASS", "BLOCKED"}:
            failures.append(f"{path.name}: result must be PASS or BLOCKED")
        elif result == "BLOCKED" and path.name not in expected_receipts:
            failures.append(f"{path.name}: unexpected BLOCKED receipt")

    return failures


def production_update_preflight_failures(path: Path) -> list[str]:
    data, error = read_json_object(path)
    if error:
        return [error]

    failures: list[str] = []
    if data.get("record_type") != "hermes_production_update_preflight":
        failures.append("record_type must be hermes_production_update_preflight")
    if data.get("target") != "real-hermes-runtime-update":
        failures.append("target must be real-hermes-runtime-update")
    if data.get("result") != "BLOCKED":
        failures.append("result must remain BLOCKED until real proof refs exist")

    decision = data.get("decision")
    if not isinstance(decision, dict):
        failures.append("decision must be an object")
    else:
        if decision.get("real_runtime_update") != "blocked":
            failures.append("decision.real_runtime_update must be blocked")
        if decision.get("worker_task_status") != "keep_blocked":
            failures.append("decision.worker_task_status must be keep_blocked")

    required_proofs = data.get("required_proofs")
    if not isinstance(required_proofs, list) or not required_proofs:
        failures.append("required_proofs must be a non-empty list")
    else:
        proof_ids = {str(item.get("id")) for item in required_proofs if isinstance(item, dict)}
        missing_ids = sorted(REQUIRED_PRODUCTION_UPDATE_PROOFS.difference(proof_ids))
        failures.extend(f"missing required production proof: {proof_id}" for proof_id in missing_ids)
        for item in required_proofs:
            if not isinstance(item, dict):
                failures.append("required_proofs entries must be objects")
                continue
            proof_id = str(item.get("id"))
            if proof_id in REQUIRED_PRODUCTION_UPDATE_BLOCKERS and item.get("status") != "BLOCKED":
                failures.append(f"{proof_id}: status must be BLOCKED")
            if proof_id in REQUIRED_PRODUCTION_UPDATE_PASSED_PROOFS:
                if item.get("status") != "PASS":
                    failures.append(f"{proof_id}: status must be PASS")
                if not item.get("proof_ref"):
                    failures.append(f"{proof_id}: proof_ref must be present")

    blocking_items = data.get("blocking_items")
    if not isinstance(blocking_items, list):
        failures.append("blocking_items must be a list")
    else:
        missing_blockers = sorted(REQUIRED_PRODUCTION_UPDATE_BLOCKERS.difference(str(item) for item in blocking_items))
        failures.extend(f"missing blocking item: {proof_id}" for proof_id in missing_blockers)
        unexpected_blockers = sorted(REQUIRED_PRODUCTION_UPDATE_PASSED_PROOFS.intersection(str(item) for item in blocking_items))
        failures.extend(f"proved production proof must not remain blocking: {proof_id}" for proof_id in unexpected_blockers)

    return failures


def real_runtime_no_spawn_smoke_failures(path: Path) -> list[str]:
    data, error = read_json_object(path)
    if error:
        return [error]

    failures: list[str] = []
    if data.get("record_type") != "hermes_real_runtime_smoke":
        failures.append("record_type must be hermes_real_runtime_smoke")
    if data.get("smoke_type") != "real_kanban_no_spawn_blocked_board":
        failures.append("smoke_type must be real_kanban_no_spawn_blocked_board")
    if data.get("result") != "PASS":
        failures.append("result must be PASS")

    checks = data.get("checks")
    if not isinstance(checks, dict) or not checks:
        failures.append("checks must be a non-empty object")
    else:
        false_checks = sorted(key for key, value in checks.items() if value is not True)
        failures.extend(f"check must be true: {key}" for key in false_checks)

    cleanup = data.get("cleanup")
    if not isinstance(cleanup, dict):
        failures.append("cleanup must be an object")
    elif cleanup.get("result") != "PASS":
        failures.append("cleanup.result must be PASS")

    limits = data.get("limits")
    if not isinstance(limits, list) or not limits:
        failures.append("limits must be a non-empty list")

    return failures


def real_worker_dispatch_bounded_smoke_failures(path: Path) -> list[str]:
    data, error = read_json_object(path)
    if error:
        return [error]

    failures: list[str] = []
    if data.get("record_type") != "hermes_real_runtime_smoke":
        failures.append("record_type must be hermes_real_runtime_smoke")
    if data.get("smoke_type") != "real_worker_dispatch_bounded_smoke":
        failures.append("smoke_type must be real_worker_dispatch_bounded_smoke")
    if data.get("result") != "BLOCKED":
        failures.append("result must remain BLOCKED until worker completion is proven")

    checks = data.get("checks")
    required_true_checks = {
        "read_only_status_checked_first",
        "disposable_board_created",
        "disposable_task_created",
        "task_assigned_to_worker_profile",
        "dispatch_command_passed",
        "exactly_one_worker_spawned",
        "run_record_exists",
        "worker_pid_recorded",
        "heartbeat_observed",
        "task_reclaimed_after_timeout",
        "task_blocked_after_timeout",
        "board_was_archived",
        "spawned_process_cleanup_verified",
    }
    required_false_checks = {
        "task_reached_terminal_status",
        "task_completed",
    }
    if not isinstance(checks, dict) or not checks:
        failures.append("checks must be a non-empty object")
    else:
        for key in sorted(required_true_checks):
            if checks.get(key) is not True:
                failures.append(f"check must be true: {key}")
        for key in sorted(required_false_checks):
            if checks.get(key) is not False:
                failures.append(f"check must be false while receipt is BLOCKED: {key}")

    cleanup = data.get("cleanup")
    if not isinstance(cleanup, dict):
        failures.append("cleanup must be an object")
    elif cleanup.get("result") != "PASS":
        failures.append("cleanup.result must be PASS")

    limits = data.get("limits")
    if not isinstance(limits, list) or not limits:
        failures.append("limits must be a non-empty list")

    return failures


def real_worker_terminal_completion_smoke_failures(path: Path) -> list[str]:
    data, error = read_json_object(path)
    if error:
        return [error]

    failures: list[str] = []
    if data.get("record_type") != "hermes_real_runtime_smoke":
        failures.append("record_type must be hermes_real_runtime_smoke")
    if data.get("smoke_type") != "real_worker_terminal_completion_smoke":
        failures.append("smoke_type must be real_worker_terminal_completion_smoke")
    result = data.get("result")
    if result not in {"PASS", "BLOCKED"}:
        failures.append("result must be PASS or BLOCKED")

    checks = data.get("checks")
    base_required_true_checks = {
        "official_hermes_docs_studied_first",
        "implementation_completion_path_studied_first",
        "disposable_board_created",
        "disposable_task_created",
        "explicit_terminal_instruction_given",
        "worker_profile_had_kanban_worker_skill",
        "dispatch_command_passed",
        "worker_spawned",
        "cleanup_verified",
        "board_was_archived",
    }
    blocked_required_true_checks = {
        "provider_live_auth_blocker_observed",
    }
    blocked_required_false_checks = {
        "global_provider_live_probe_passed",
        "worker_profile_live_probe_passed",
        "terminal_status_reached",
        "task_completed",
        "task_blocked_by_worker",
        "kanban_complete_observed",
        "kanban_block_observed",
    }
    pass_required_true_checks = {
        "global_provider_live_probe_passed",
        "worker_profile_live_probe_passed",
        "terminal_status_reached",
        "task_completed",
        "kanban_complete_observed",
        "summary_marker_observed",
    }
    pass_required_false_checks = {
        "provider_live_auth_blocker_observed",
        "task_blocked_by_worker",
        "kanban_block_observed",
    }
    if not isinstance(checks, dict) or not checks:
        failures.append("checks must be a non-empty object")
    else:
        for key in sorted(base_required_true_checks):
            if checks.get(key) is not True:
                failures.append(f"check must be true: {key}")
        if result == "BLOCKED":
            for key in sorted(blocked_required_true_checks):
                if checks.get(key) is not True:
                    failures.append(f"check must be true while receipt is BLOCKED: {key}")
            for key in sorted(blocked_required_false_checks):
                if checks.get(key) not in {False, None}:
                    failures.append(f"check must be false while receipt is BLOCKED: {key}")
        if result == "PASS":
            for key in sorted(pass_required_true_checks):
                if checks.get(key) is not True:
                    failures.append(f"check must be true while receipt is PASS: {key}")
            for key in sorted(pass_required_false_checks):
                if checks.get(key) is not False:
                    failures.append(f"check must be false while receipt is PASS: {key}")

    if result == "PASS":
        auth_resolution = data.get("auth_resolution")
        if not isinstance(auth_resolution, dict):
            failures.append("auth_resolution must be an object when result is PASS")
        else:
            if auth_resolution.get("result") != "PASS":
                failures.append("auth_resolution.result must be PASS")
            for key in ("profile_ref", "provider_ref", "model_ref", "method"):
                if not isinstance(auth_resolution.get(key), str) or not auth_resolution.get(key):
                    failures.append(f"auth_resolution.{key} must be a non-empty string")
            if auth_resolution.get("status_only_auth_rejected_as_proof") is not True:
                failures.append("auth_resolution.status_only_auth_rejected_as_proof must be true")
            if auth_resolution.get("global_provider_probe") != "PASS":
                failures.append("auth_resolution.global_provider_probe must be PASS")
            if auth_resolution.get("worker_profile_provider_probe") != "PASS":
                failures.append("auth_resolution.worker_profile_provider_probe must be PASS")

    cleanup = data.get("cleanup")
    if not isinstance(cleanup, dict):
        failures.append("cleanup must be an object")
    elif cleanup.get("result") != "PASS":
        failures.append("cleanup.result must be PASS")

    limits = data.get("limits")
    if not isinstance(limits, list) or not limits:
        failures.append("limits must be a non-empty list")

    evidence_refs = data.get("evidence_refs")
    if not isinstance(evidence_refs, list) or "docs/research/hermes-worker-completion-source-notes.md" not in evidence_refs:
        failures.append("evidence_refs must include official-docs source notes")

    return failures


def worker_profile_live_auth_matrix_smoke_failures(path: Path) -> list[str]:
    data, error = read_json_object(path)
    if error:
        return [error]

    failures: list[str] = []
    if data.get("record_type") != "hermes_real_runtime_smoke":
        failures.append("record_type must be hermes_real_runtime_smoke")
    if data.get("smoke_type") != "worker_profile_live_auth_matrix_smoke":
        failures.append("smoke_type must be worker_profile_live_auth_matrix_smoke")
    if data.get("result") != "PASS":
        failures.append("result must be PASS after all registry profile live probes pass")
    if data.get("provider_ref") != "openai-codex":
        failures.append("provider_ref must be openai-codex")
    if data.get("model_ref") != "gpt-5.5":
        failures.append("model_ref must be gpt-5.5")

    checks = data.get("checks")
    required_true_checks = {
        "official_hermes_profile_docs_studied_first",
        "official_hermes_worker_completion_docs_studied_first",
        "registry_worker_count_checked",
        "pre_repair_missing_profiles_observed",
        "missing_profiles_created_from_public_worker_registry",
        "new_profiles_created_without_env_clone",
        "no_profile_local_openai_codex_auth_copied",
        "profile_local_auth_shadows_absent_for_registry_workers",
        "all_registry_profiles_exist",
        "all_non_human_profiles_have_config",
        "all_non_human_live_provider_model_probes_passed",
        "human_gate_clerk_skipped_as_human_authority",
        "no_raw_runtime_logs_stored",
        "cleanup_or_recovery_path_recorded",
    }
    if not isinstance(checks, dict) or not checks:
        failures.append("checks must be a non-empty object")
    else:
        for key in sorted(required_true_checks):
            if checks.get(key) is not True:
                failures.append(f"check must be true: {key}")

    summary = data.get("summary")
    expected_summary = {
        "registry_worker_count": 47,
        "non_human_worker_count": 46,
        "human_worker_count": 1,
        "pre_repair_existing_profile_count": 27,
        "pre_repair_missing_profile_count": 20,
        "profiles_created_count": 20,
        "post_repair_profile_exists_count": 47,
        "post_repair_missing_profile_count": 0,
        "registry_local_openai_codex_shadow_count": 0,
        "non_human_config_exists_count": 46,
        "live_probe_attempted_count": 46,
        "live_probe_passed_count": 46,
        "live_probe_failed_count": 0,
        "human_skipped_count": 1,
        "new_profiles_env_cloned_count": 0,
        "created_profiles_without_env_count": 20,
    }
    if not isinstance(summary, dict):
        failures.append("summary must be an object")
    else:
        for key, expected in expected_summary.items():
            if summary.get(key) != expected:
                failures.append(f"summary.{key} must be {expected}")
        if summary.get("live_probe_passed_count") != summary.get("live_probe_attempted_count"):
            failures.append("summary.live_probe_passed_count must equal summary.live_probe_attempted_count")
        if summary.get("post_repair_missing_profile_count") != 0:
            failures.append("summary.post_repair_missing_profile_count must be 0 when result is PASS")

    profile_matrix = data.get("profile_matrix")
    if not isinstance(profile_matrix, dict):
        failures.append("profile_matrix must be an object")
    else:
        passed_existing = profile_matrix.get("passed_existing_profiles")
        created_and_passed = profile_matrix.get("created_and_passed_profiles")
        skipped_human = profile_matrix.get("human_profiles_skipped")
        failed_profiles = profile_matrix.get("failed_profiles")
        missing_after = profile_matrix.get("missing_profiles_after_repair")
        if not isinstance(passed_existing, list) or len(passed_existing) != 26:
            failures.append("profile_matrix.passed_existing_profiles must contain 26 profiles")
        if not isinstance(created_and_passed, list) or len(created_and_passed) != 20:
            failures.append("profile_matrix.created_and_passed_profiles must contain 20 profiles")
        if skipped_human != ["human-gate-clerk"]:
            failures.append("profile_matrix.human_profiles_skipped must be ['human-gate-clerk']")
        if failed_profiles != []:
            failures.append("profile_matrix.failed_profiles must be empty")
        if missing_after != []:
            failures.append("profile_matrix.missing_profiles_after_repair must be empty")

    provisioning = data.get("profile_provisioning")
    if not isinstance(provisioning, dict):
        failures.append("profile_provisioning must be an object")
    else:
        if provisioning.get("created_profile_count") != 20:
            failures.append("profile_provisioning.created_profile_count must be 20")
        if provisioning.get("env_clone_used") is not False:
            failures.append("profile_provisioning.env_clone_used must be false")
        if provisioning.get("profile_local_auth_clone_used") is not False:
            failures.append("profile_provisioning.profile_local_auth_clone_used must be false")

    cleanup = data.get("cleanup")
    if not isinstance(cleanup, dict):
        failures.append("cleanup must be an object")
    elif cleanup.get("result") != "PASS":
        failures.append("cleanup.result must be PASS")

    limits = data.get("limits")
    if not isinstance(limits, list) or not limits:
        failures.append("limits must be a non-empty list")

    evidence_refs = data.get("evidence_refs")
    required_refs = {
        "agents/worker-registry.public.json",
        "docs/research/hermes-worker-completion-source-notes.md",
        "validation/hermes-real-runtime-smoke/real-worker-terminal-completion-smoke.json",
    }
    if not isinstance(evidence_refs, list):
        failures.append("evidence_refs must be a list")
    else:
        missing_refs = sorted(required_refs.difference(str(ref) for ref in evidence_refs))
        failures.extend(f"missing profile auth evidence ref: {ref}" for ref in missing_refs)

    return failures


def real_worker_local_tool_quality_smoke_failures(path: Path) -> list[str]:
    data, error = read_json_object(path)
    if error:
        return [error]

    failures: list[str] = []
    if data.get("record_type") != "hermes_real_runtime_smoke":
        failures.append("record_type must be hermes_real_runtime_smoke")
    if data.get("smoke_type") != "real_worker_local_tool_quality_smoke":
        failures.append("smoke_type must be real_worker_local_tool_quality_smoke")
    if data.get("result") != "PASS":
        failures.append("result must be PASS")
    if data.get("worker_ref") != "public-safety-gate":
        failures.append("worker_ref must be public-safety-gate")

    checks = data.get("checks")
    required_true_checks = {
        "official_hermes_toolset_docs_studied_first",
        "official_hermes_kanban_tool_docs_studied_first",
        "real_gateway_running_checked_first",
        "disposable_board_created",
        "disposable_task_created",
        "worker_profile_assigned",
        "real_workspace_used",
        "dispatch_command_passed",
        "worker_spawned",
        "kanban_show_required",
        "terminal_tool_used",
        "read_only_terminal_commands_used",
        "files_checked_with_terminal",
        "git_status_checked_with_terminal",
        "terminal_status_reached",
        "task_completed",
        "kanban_complete_observed",
        "quality_marker_observed",
        "structured_metadata_required",
        "cleanup_verified",
        "board_was_archived",
        "no_raw_runtime_logs_stored",
    }
    if not isinstance(checks, dict) or not checks:
        failures.append("checks must be a non-empty object")
    else:
        for key in sorted(required_true_checks):
            if checks.get(key) is not True:
                failures.append(f"check must be true: {key}")

    summary = data.get("summary")
    if not isinstance(summary, dict):
        failures.append("summary must be an object")
    else:
        expected_summary = {
            "worker": "public-safety-gate",
            "profile_mode": "closed",
            "tool_proven": "terminal",
            "tool_auth_kind": "local Hermes terminal tool authorization",
            "run_outcome": "completed",
            "terminal_status": "done",
            "commands_required_count": 3,
            "commands_completed_count": 3,
            "files_checked_count": 2,
        }
        for key, expected in expected_summary.items():
            if summary.get(key) != expected:
                failures.append(f"summary.{key} must be {expected!r}")

    worker_result = data.get("worker_result_contract")
    if not isinstance(worker_result, dict):
        failures.append("worker_result_contract must be an object")
    else:
        if worker_result.get("record_type") != "overkill_real_tool_auth_smoke_worker_result":
            failures.append("worker_result_contract.record_type must be overkill_real_tool_auth_smoke_worker_result")
        if worker_result.get("terminal_tool_used") is not True:
            failures.append("worker_result_contract.terminal_tool_used must be true")
        if worker_result.get("read_only") is not True:
            failures.append("worker_result_contract.read_only must be true")
        if worker_result.get("result") != "PASS":
            failures.append("worker_result_contract.result must be PASS")
        if worker_result.get("files_checked") != ["README.md", "scripts/factoryctl.py"]:
            failures.append("worker_result_contract.files_checked must match the bounded proof files")

    cleanup = data.get("cleanup")
    if not isinstance(cleanup, dict):
        failures.append("cleanup must be an object")
    elif cleanup.get("result") != "PASS":
        failures.append("cleanup.result must be PASS")

    limits = data.get("limits")
    if not isinstance(limits, list) or not limits:
        failures.append("limits must be a non-empty list")
    else:
        joined_limits = " ".join(str(item) for item in limits).lower()
        for phrase in ("does not prove external saas", "does not prove", "production"):
            if phrase not in joined_limits:
                failures.append(f"limits must include bounded non-production caveat: {phrase}")

    evidence_refs = data.get("evidence_refs")
    required_refs = {
        "docs/research/hermes-worker-completion-source-notes.md",
        "validation/hermes-real-runtime-smoke/real-worker-terminal-completion-smoke.json",
        "validation/hermes-real-runtime-smoke/worker-profile-live-auth-matrix-smoke.json",
        "agents/worker-registry.public.json",
    }
    if not isinstance(evidence_refs, list):
        failures.append("evidence_refs must be a list")
    else:
        missing_refs = sorted(required_refs.difference(str(ref) for ref in evidence_refs))
        failures.extend(f"missing local tool smoke evidence ref: {ref}" for ref in missing_refs)

    return failures


def real_worker_parent_done_reconciliation_smoke_failures(path: Path) -> list[str]:
    data, error = read_json_object(path)
    if error:
        return [error]

    failures: list[str] = []
    if data.get("record_type") != "hermes_real_runtime_smoke":
        failures.append("record_type must be hermes_real_runtime_smoke")
    if data.get("smoke_type") != "real_worker_parent_done_reconciliation_smoke":
        failures.append("smoke_type must be real_worker_parent_done_reconciliation_smoke")
    if data.get("result") != "PASS":
        failures.append("result must be PASS")
    if data.get("worker_ref") != "public-safety-gate":
        failures.append("worker_ref must be public-safety-gate")

    checks = data.get("checks")
    required_true_checks = {
        "official_hermes_kanban_docs_checked_first",
        "real_gateway_running_checked_first",
        "disposable_board_created",
        "real_worker_spawned",
        "real_worker_reached_done",
        "kanban_complete_observed",
        "terminal_tool_signal_observed",
        "public_safety_result_observed",
        "public_safety_result_sanitized",
        "worker_result_contract_valid",
        "parent_done_hook_executed",
        "parent_done_transition_allowed",
        "missing_blocking_workers_empty",
        "invalid_blocking_workers_empty",
        "public_safety_gate_satisfied",
        "cleanup_verified",
        "board_was_archived",
        "no_raw_runtime_logs_stored",
    }
    if not isinstance(checks, dict) or not checks:
        failures.append("checks must be a non-empty object")
    else:
        for key in sorted(required_true_checks):
            if checks.get(key) is not True:
                failures.append(f"check must be true: {key}")

    summary = data.get("summary")
    if not isinstance(summary, dict):
        failures.append("summary must be an object")
    else:
        if summary.get("worker") != "public-safety-gate":
            failures.append("summary.worker must be public-safety-gate")
        if summary.get("real_worker_terminal_status") != "done":
            failures.append("summary.real_worker_terminal_status must be done")
        if summary.get("hook_transition_action") != "allow_done":
            failures.append("summary.hook_transition_action must be allow_done")
        if summary.get("satisfied_before_done_worker") != "public-safety-gate":
            failures.append("summary.satisfied_before_done_worker must be public-safety-gate")

    cleanup = data.get("cleanup")
    if not isinstance(cleanup, dict):
        failures.append("cleanup must be an object")
    elif cleanup.get("result") != "PASS":
        failures.append("cleanup.result must be PASS")

    evidence_refs = data.get("evidence_refs")
    required_refs = {
        "validation/hermes-real-runtime-smoke/real-worker-local-tool-quality-smoke.json",
        "validation/hermes-real-runtime-smoke/parent-done-reconciliation/worker-results/public_safety_result.json",
        "validation/hermes-real-runtime-smoke/parent-done-reconciliation/receipt-five.json",
        "validation/hermes-real-runtime-smoke/parent-done-reconciliation/hook-result.json",
        "validation/cards/real-worker-parent-done-reconciliation-r1.md",
    }
    if not isinstance(evidence_refs, list):
        failures.append("evidence_refs must be a list")
    else:
        missing_refs = sorted(required_refs.difference(str(ref) for ref in evidence_refs))
        failures.extend(f"missing parent done reconciliation evidence ref: {ref}" for ref in missing_refs)

    limits = data.get("limits")
    if not isinstance(limits, list) or not limits:
        failures.append("limits must be a non-empty list")
    else:
        joined_limits = " ".join(str(item) for item in limits).lower()
        for phrase in ("does not prove broad specialist quality", "raw runtime output"):
            if phrase not in joined_limits:
                failures.append(f"limits must include parent reconciliation caveat: {phrase}")

    return failures


def real_worker_specialist_output_quality_smoke_failures(path: Path) -> list[str]:
    data, error = read_json_object(path)
    if error:
        return [error]

    failures: list[str] = []
    if data.get("record_type") != "hermes_real_runtime_smoke":
        failures.append("record_type must be hermes_real_runtime_smoke")
    if data.get("smoke_type") != "real_worker_specialist_output_quality_smoke":
        failures.append("smoke_type must be real_worker_specialist_output_quality_smoke")
    if data.get("result") != "PASS":
        failures.append("result must be PASS")
    if data.get("worker_ref") != "public-safety-gate":
        failures.append("worker_ref must be public-safety-gate")

    checks = data.get("checks")
    required_true_checks = {
        "real_gateway_running_checked_first",
        "disposable_workspace_created",
        "direct_scanner_precheck_passed",
        "disposable_board_created",
        "disposable_task_created",
        "worker_profile_assigned",
        "worker_spawned",
        "terminal_tool_used",
        "public_safety_scan_command_observed",
        "secret_safety_scan_command_observed",
        "scanner_ok_output_observed",
        "public_safety_result_shape_observed",
        "quality_marker_observed",
        "task_completed",
        "kanban_complete_observed",
        "cleanup_verified",
        "board_was_archived",
        "disposable_workspace_removed",
        "no_raw_runtime_logs_stored",
    }
    if not isinstance(checks, dict) or not checks:
        failures.append("checks must be a non-empty object")
    else:
        for key in sorted(required_true_checks):
            if checks.get(key) is not True:
                failures.append(f"check must be true: {key}")

    summary = data.get("summary")
    if not isinstance(summary, dict):
        failures.append("summary must be an object")
    else:
        if summary.get("worker") != "public-safety-gate":
            failures.append("summary.worker must be public-safety-gate")
        if summary.get("terminal_status") != "done":
            failures.append("summary.terminal_status must be done")
        scanner_results = summary.get("scanner_results")
        if not isinstance(scanner_results, dict):
            failures.append("summary.scanner_results must be an object")
        else:
            if scanner_results.get("public_safety_scan") != "PASS":
                failures.append("summary.scanner_results.public_safety_scan must be PASS")
            if scanner_results.get("secret_safety_scan") != "PASS":
                failures.append("summary.scanner_results.secret_safety_scan must be PASS")
        if summary.get("worker_result_ref") != (
            "validation/hermes-real-runtime-smoke/specialist-output-quality/worker-results/public_safety_result.json"
        ):
            failures.append("summary.worker_result_ref must point at the specialist worker result")

    cleanup = data.get("cleanup")
    if not isinstance(cleanup, dict):
        failures.append("cleanup must be an object")
    elif cleanup.get("result") != "PASS":
        failures.append("cleanup.result must be PASS")

    evidence_refs = data.get("evidence_refs")
    required_refs = {
        "validation/hermes-real-runtime-smoke/real-worker-local-tool-quality-smoke.json",
        "validation/hermes-real-runtime-smoke/specialist-output-quality/worker-results/public_safety_result.json",
        "scripts/public_safety_scan.py",
        "scripts/secret_safety_scan.py",
    }
    if not isinstance(evidence_refs, list):
        failures.append("evidence_refs must be a list")
    else:
        missing_refs = sorted(required_refs.difference(str(ref) for ref in evidence_refs))
        failures.extend(f"missing specialist quality blocker evidence ref: {ref}" for ref in missing_refs)

    limits = data.get("limits")
    if not isinstance(limits, list) or not limits:
        failures.append("limits must be a non-empty list")
    else:
        joined_limits = " ".join(str(item) for item in limits).lower()
        for phrase in ("scanner-backed specialist output quality", "target hermes worker workspace"):
            if phrase not in joined_limits:
                failures.append(f"limits must include specialist proof caveat: {phrase}")

    return failures


def production_rollback_monitoring_smoke_failures(path: Path) -> list[str]:
    data, error = read_json_object(path)
    if error:
        return [error]

    failures: list[str] = []
    if data.get("record_type") != "hermes_real_runtime_smoke":
        failures.append("record_type must be hermes_real_runtime_smoke")
    if data.get("smoke_type") != "production_rollback_monitoring_smoke":
        failures.append("smoke_type must be production_rollback_monitoring_smoke")
    if data.get("result") != "PASS":
        failures.append("result must be PASS")
    if data.get("service_ref") != "hermes-gateway.service":
        failures.append("service_ref must be hermes-gateway.service")

    checks = data.get("checks")
    required_true_checks = {
        "local_hermes_runbook_studied_first",
        "service_rollback_drill_limitations_studied_first",
        "real_gateway_state_checked_first",
        "systemd_unit_visible",
        "gateway_active_before",
        "restart_policy_always_observed",
        "process_owner_verified",
        "controlled_termination_used",
        "service_manager_recreated_gateway_process",
        "gateway_active_after",
        "new_service_process_observed",
        "hermes_status_after_passed",
        "kanban_cli_after_passed",
        "direct_systemctl_restart_nonzero_recorded",
        "recovery_start_not_needed",
        "no_raw_runtime_logs_stored",
        "no_runtime_ids_stored",
    }
    if not isinstance(checks, dict) or not checks:
        failures.append("checks must be a non-empty object")
    else:
        for key in sorted(required_true_checks):
            if checks.get(key) is not True:
                failures.append(f"check must be true: {key}")

    summary = data.get("summary")
    if not isinstance(summary, dict):
        failures.append("summary must be an object")
    else:
        if summary.get("service_manager") != "systemd":
            failures.append("summary.service_manager must be systemd")
        if summary.get("unit") != "hermes-gateway.service":
            failures.append("summary.unit must be hermes-gateway.service")
        recovery_method = str(summary.get("recovery_method") or "").lower()
        if "restart=always" not in recovery_method:
            failures.append("summary.recovery_method must mention Restart=always")
        post_recovery_checks = summary.get("post_recovery_checks")
        if not isinstance(post_recovery_checks, dict):
            failures.append("summary.post_recovery_checks must be an object")
        else:
            if post_recovery_checks.get("hermes_status") != "PASS":
                failures.append("summary.post_recovery_checks.hermes_status must be PASS")
            if post_recovery_checks.get("kanban_boards_list") != "PASS":
                failures.append("summary.post_recovery_checks.kanban_boards_list must be PASS")

    cleanup = data.get("cleanup")
    if not isinstance(cleanup, dict):
        failures.append("cleanup must be an object")
    elif cleanup.get("result") != "PASS":
        failures.append("cleanup.result must be PASS")

    evidence_refs = data.get("evidence_refs")
    required_refs = {
        "adapters/hermes/update-runbook.md",
        "adapters/hermes/service_rollback_drill_smoke.py",
        "validation/hermes-installed-runtime-smoke/service-rollback-drill-smoke.json",
    }
    if not isinstance(evidence_refs, list):
        failures.append("evidence_refs must be a list")
    else:
        missing_refs = sorted(required_refs.difference(str(ref) for ref in evidence_refs))
        failures.extend(f"missing production rollback monitoring evidence ref: {ref}" for ref in missing_refs)

    limits = data.get("limits")
    if not isinstance(limits, list) or not limits:
        failures.append("limits must be a non-empty list")
    else:
        joined_limits = " ".join(str(item) for item in limits).lower()
        for phrase in ("real hermes gateway recovery", "code-version rollback", "restart=always"):
            if phrase not in joined_limits:
                failures.append(f"limits must include rollback monitoring caveat: {phrase}")

    return failures


def dashboard_route_inventory_failures(path: Path) -> list[str]:
    if not path.exists():
        return [f"missing file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]

    failures: list[str] = []
    route_inventory = data.get("route_inventory") if isinstance(data, dict) else None
    coverage_summary = data.get("coverage_summary") if isinstance(data, dict) else None
    if data.get("result") != "PASS":
        failures.append("result must be PASS")
    if not isinstance(route_inventory, dict):
        failures.append("route_inventory must be an object")
        return failures
    mutating = route_inventory.get("mutating_routes")
    covered = route_inventory.get("covered_mutating_route_families")
    pending = route_inventory.get("pending_mutating_route_families")
    if mutating != covered:
        failures.append("covered_mutating_route_families must equal mutating_routes")
    if pending != 0:
        failures.append("pending_mutating_route_families must be 0")
    if isinstance(coverage_summary, dict) and coverage_summary.get("pending") not in ([], None):
        failures.append("coverage_summary.pending must be empty")
    evidence_refs = data.get("evidence_refs")
    if isinstance(evidence_refs, list):
        required_refs = {
            "validation/hermes-installed-runtime-smoke/dashboard-profile-routes-operational-safety-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-orchestration-route-operational-safety-smoke.json",
        }
        missing_refs = sorted(required_refs.difference(str(ref) for ref in evidence_refs))
        failures.extend(f"missing inventory evidence ref: {ref}" for ref in missing_refs)
    else:
        failures.append("evidence_refs must be a list")
    return failures


def main() -> int:
    failures = []
    failures.extend(f"patch missing marker: {m}" for m in missing_markers(PATCH, REQUIRED_PATCH_MARKERS))
    failures.extend(f"vfinal patch missing marker: {m}" for m in missing_markers(VFINAL_PATCH, REQUIRED_VFINAL_PATCH_MARKERS))
    failures.extend(
        f"vfinal worker patch missing marker: {m}"
        for m in missing_markers(VFINAL_WORKER_PATCH, REQUIRED_VFINAL_WORKER_PATCH_MARKERS)
    )
    failures.extend(
        f"vfinal dashboard patch missing marker: {m}"
        for m in missing_markers(VFINAL_DASHBOARD_PATCH, REQUIRED_VFINAL_DASHBOARD_PATCH_MARKERS)
    )
    failures.extend(
        f"vfinal worker-result patch missing marker: {m}"
        for m in missing_markers(VFINAL_WORKER_RESULT_PATCH, REQUIRED_VFINAL_WORKER_RESULT_PATCH_MARKERS)
    )
    failures.extend(
        f"vfinal worker-dependency patch missing marker: {m}"
        for m in missing_markers(VFINAL_WORKER_DEPENDENCY_PATCH, REQUIRED_VFINAL_WORKER_DEPENDENCY_PATCH_MARKERS)
    )
    failures.extend(
        f"vfinal dashboard dependency patch missing marker: {m}"
        for m in missing_markers(VFINAL_DASHBOARD_DEPENDENCY_PATCH, REQUIRED_VFINAL_DASHBOARD_DEPENDENCY_PATCH_MARKERS)
    )
    failures.extend(
        f"vfinal dashboard delete patch missing marker: {m}"
        for m in missing_markers(VFINAL_DASHBOARD_DELETE_PATCH, REQUIRED_VFINAL_DASHBOARD_DELETE_PATCH_MARKERS)
    )
    failures.extend(
        f"vfinal dashboard links patch missing marker: {m}"
        for m in missing_markers(VFINAL_DASHBOARD_LINKS_PATCH, REQUIRED_VFINAL_DASHBOARD_LINKS_PATCH_MARKERS)
    )
    failures.extend(
        f"vfinal dashboard attachment patch missing marker: {m}"
        for m in missing_markers(
            VFINAL_DASHBOARD_ATTACHMENT_PATCH, REQUIRED_VFINAL_DASHBOARD_ATTACHMENT_PATCH_MARKERS
        )
    )
    failures.extend(
        f"vfinal dashboard bulk archive patch missing marker: {m}"
        for m in missing_markers(
            VFINAL_DASHBOARD_BULK_ARCHIVE_PATCH, REQUIRED_VFINAL_DASHBOARD_BULK_ARCHIVE_PATCH_MARKERS
        )
    )
    failures.extend(
        f"vfinal dashboard reassign patch missing marker: {m}"
        for m in missing_markers(VFINAL_DASHBOARD_REASSIGN_PATCH, REQUIRED_VFINAL_DASHBOARD_REASSIGN_PATCH_MARKERS)
    )
    failures.extend(
        f"vfinal dashboard reclaim/terminate patch missing marker: {m}"
        for m in missing_markers(
            VFINAL_DASHBOARD_RECLAIM_TERMINATE_PATCH,
            REQUIRED_VFINAL_DASHBOARD_RECLAIM_TERMINATE_PATCH_MARKERS,
        )
    )
    failures.extend(
        f"vfinal dashboard specify patch missing marker: {m}"
        for m in missing_markers(VFINAL_DASHBOARD_SPECIFY_PATCH, REQUIRED_VFINAL_DASHBOARD_SPECIFY_PATCH_MARKERS)
    )
    failures.extend(
        f"vfinal dashboard decompose patch missing marker: {m}"
        for m in missing_markers(VFINAL_DASHBOARD_DECOMPOSE_PATCH, REQUIRED_VFINAL_DASHBOARD_DECOMPOSE_PATCH_MARKERS)
    )
    failures.extend(
        f"vfinal dashboard board delete patch missing marker: {m}"
        for m in missing_markers(
            VFINAL_DASHBOARD_BOARD_DELETE_PATCH,
            REQUIRED_VFINAL_DASHBOARD_BOARD_DELETE_PATCH_MARKERS,
        )
    )
    failures.extend(f"factoryctl missing marker: {m}" for m in missing_markers(FACTORYCTL, REQUIRED_FACTORYCTL_MARKERS))
    failures.extend(f"transition hook missing marker: {m}" for m in missing_markers(TRANSITION_HOOK, REQUIRED_TRANSITION_HOOK_MARKERS))
    failures.extend(
        f"worker route readiness missing marker: {m}"
        for m in missing_markers(WORKER_ROUTE_READINESS, REQUIRED_WORKER_ROUTE_READINESS_MARKERS)
    )
    failures.extend(
        f"worker profile readiness smoke missing marker: {m}"
        for m in missing_markers(WORKER_PROFILE_READINESS, REQUIRED_WORKER_PROFILE_READINESS_MARKERS)
    )
    failures.extend(
        f"worker dispatch completion smoke missing marker: {m}"
        for m in missing_markers(WORKER_DISPATCH_COMPLETION, REQUIRED_WORKER_DISPATCH_COMPLETION_MARKERS)
    )
    failures.extend(
        f"worker real-process local-stub smoke missing marker: {m}"
        for m in missing_markers(WORKER_REAL_PROCESS_LOCAL_STUB, REQUIRED_WORKER_REAL_PROCESS_LOCAL_STUB_MARKERS)
    )
    failures.extend(
        f"worker real-process matrix local-stub smoke missing marker: {m}"
        for m in missing_markers(WORKER_REAL_PROCESS_MATRIX_LOCAL_STUB, REQUIRED_WORKER_REAL_PROCESS_MATRIX_LOCAL_STUB_MARKERS)
    )
    failures.extend(
        f"service rollback drill smoke missing marker: {m}"
        for m in missing_markers(SERVICE_ROLLBACK_DRILL, REQUIRED_SERVICE_ROLLBACK_DRILL_MARKERS)
    )
    failures.extend(
        f"dashboard done route parity smoke missing marker: {m}"
        for m in missing_markers(DASHBOARD_DONE_ROUTE_PARITY, REQUIRED_DASHBOARD_DONE_ROUTE_PARITY_MARKERS)
    )
    failures.extend(
        f"dashboard create route parity smoke missing marker: {m}"
        for m in missing_markers(DASHBOARD_CREATE_ROUTE_PARITY, REQUIRED_DASHBOARD_CREATE_ROUTE_PARITY_MARKERS)
    )
    failures.extend(
        f"dashboard dispatch route parity smoke missing marker: {m}"
        for m in missing_markers(DASHBOARD_DISPATCH_ROUTE_PARITY, REQUIRED_DASHBOARD_DISPATCH_ROUTE_PARITY_MARKERS)
    )
    failures.extend(
        f"dashboard delete route guard smoke missing marker: {m}"
        for m in missing_markers(DASHBOARD_DELETE_ROUTE_GUARD, REQUIRED_DASHBOARD_DELETE_ROUTE_GUARD_MARKERS)
    )
    failures.extend(
        f"dashboard links route guard smoke missing marker: {m}"
        for m in missing_markers(DASHBOARD_LINKS_ROUTE_GUARD, REQUIRED_DASHBOARD_LINKS_ROUTE_GUARD_MARKERS)
    )
    failures.extend(
        f"dashboard attachment route safety smoke missing marker: {m}"
        for m in missing_markers(
            DASHBOARD_ATTACHMENT_ROUTE_SAFETY, REQUIRED_DASHBOARD_ATTACHMENT_ROUTE_SAFETY_MARKERS
        )
    )
    failures.extend(
        f"dashboard bulk archive guard smoke missing marker: {m}"
        for m in missing_markers(DASHBOARD_BULK_ARCHIVE_GUARD, REQUIRED_DASHBOARD_BULK_ARCHIVE_GUARD_MARKERS)
    )
    failures.extend(
        f"dashboard reassign route guard smoke missing marker: {m}"
        for m in missing_markers(DASHBOARD_REASSIGN_ROUTE_GUARD, REQUIRED_DASHBOARD_REASSIGN_ROUTE_GUARD_MARKERS)
    )
    failures.extend(
        f"dashboard reclaim/terminate guard smoke missing marker: {m}"
        for m in missing_markers(
            DASHBOARD_RECLAIM_TERMINATE_GUARD,
            REQUIRED_DASHBOARD_RECLAIM_TERMINATE_GUARD_MARKERS,
        )
    )
    failures.extend(
        f"dashboard specify route guard smoke missing marker: {m}"
        for m in missing_markers(DASHBOARD_SPECIFY_ROUTE_GUARD, REQUIRED_DASHBOARD_SPECIFY_ROUTE_GUARD_MARKERS)
    )
    failures.extend(
        f"dashboard decompose route guard smoke missing marker: {m}"
        for m in missing_markers(DASHBOARD_DECOMPOSE_ROUTE_GUARD, REQUIRED_DASHBOARD_DECOMPOSE_ROUTE_GUARD_MARKERS)
    )
    failures.extend(
        f"dashboard comments append-only smoke missing marker: {m}"
        for m in missing_markers(DASHBOARD_COMMENTS_APPEND_ONLY, REQUIRED_DASHBOARD_COMMENTS_APPEND_ONLY_MARKERS)
    )
    failures.extend(
        f"dashboard home-subscribe visibility smoke missing marker: {m}"
        for m in missing_markers(DASHBOARD_HOME_SUBSCRIBE_VISIBILITY, REQUIRED_DASHBOARD_HOME_SUBSCRIBE_VISIBILITY_MARKERS)
    )
    failures.extend(
        f"dashboard board delete route guard smoke missing marker: {m}"
        for m in missing_markers(DASHBOARD_BOARD_DELETE_ROUTE_GUARD, REQUIRED_DASHBOARD_BOARD_DELETE_ROUTE_GUARD_MARKERS)
    )
    failures.extend(
        f"dashboard board lifecycle operational-safety smoke missing marker: {m}"
        for m in missing_markers(
            DASHBOARD_BOARD_LIFECYCLE_OPERATIONAL_SAFETY,
            REQUIRED_DASHBOARD_BOARD_LIFECYCLE_OPERATIONAL_SAFETY_MARKERS,
        )
    )
    failures.extend(
        f"dashboard profile routes operational-safety smoke missing marker: {m}"
        for m in missing_markers(
            DASHBOARD_PROFILE_ROUTES_OPERATIONAL_SAFETY,
            REQUIRED_DASHBOARD_PROFILE_ROUTES_OPERATIONAL_SAFETY_MARKERS,
        )
    )
    failures.extend(
        f"dashboard orchestration route operational-safety smoke missing marker: {m}"
        for m in missing_markers(
            DASHBOARD_ORCHESTRATION_ROUTE_OPERATIONAL_SAFETY,
            REQUIRED_DASHBOARD_ORCHESTRATION_ROUTE_OPERATIONAL_SAFETY_MARKERS,
        )
    )
    failures.extend(
        f"dashboard route inventory receipt invalid: {m}"
        for m in dashboard_route_inventory_failures(DASHBOARD_ROUTE_INVENTORY_RECEIPT)
    )
    failures.extend(
        f"installed runtime receipt bundle invalid: {m}"
        for m in installed_runtime_receipt_bundle_failures(INSTALLED_RUNTIME_RECEIPTS_DIR)
    )
    failures.extend(
        f"production update preflight receipt invalid: {m}"
        for m in production_update_preflight_failures(PRODUCTION_UPDATE_PREFLIGHT_RECEIPT)
    )
    failures.extend(
        f"real runtime no-spawn smoke receipt invalid: {m}"
        for m in real_runtime_no_spawn_smoke_failures(REAL_RUNTIME_NO_SPAWN_SMOKE_RECEIPT)
    )
    failures.extend(
        f"real worker dispatch bounded smoke receipt invalid: {m}"
        for m in real_worker_dispatch_bounded_smoke_failures(REAL_WORKER_DISPATCH_BOUNDED_SMOKE_RECEIPT)
    )
    failures.extend(
        f"real worker terminal completion smoke receipt invalid: {m}"
        for m in real_worker_terminal_completion_smoke_failures(REAL_WORKER_TERMINAL_COMPLETION_SMOKE_RECEIPT)
    )
    failures.extend(
        f"worker profile live-auth matrix smoke receipt invalid: {m}"
        for m in worker_profile_live_auth_matrix_smoke_failures(WORKER_PROFILE_LIVE_AUTH_MATRIX_SMOKE_RECEIPT)
    )
    failures.extend(
        f"real worker local tool quality smoke receipt invalid: {m}"
        for m in real_worker_local_tool_quality_smoke_failures(REAL_WORKER_LOCAL_TOOL_QUALITY_SMOKE_RECEIPT)
    )
    failures.extend(
        f"real worker parent done reconciliation smoke receipt invalid: {m}"
        for m in real_worker_parent_done_reconciliation_smoke_failures(
            REAL_WORKER_PARENT_DONE_RECONCILIATION_SMOKE_RECEIPT
        )
    )
    failures.extend(
        f"real worker specialist output quality smoke receipt invalid: {m}"
        for m in real_worker_specialist_output_quality_smoke_failures(
            REAL_WORKER_SPECIALIST_OUTPUT_QUALITY_SMOKE_RECEIPT
        )
    )
    failures.extend(
        f"production rollback monitoring smoke receipt invalid: {m}"
        for m in production_rollback_monitoring_smoke_failures(
            PRODUCTION_ROLLBACK_MONITORING_SMOKE_RECEIPT
        )
    )

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
