{
  "card_id": "VFINAL-HERMES-REAL-WORKER-PARENT-DONE-RECONCILIATION",
  "slice_id": "VFINAL_HERMES_REAL_PARENT_DONE",
  "owner_profile": "public-safety-gate",
  "source_refs": ["real Hermes disposable worker result smoke"],
  "source_state": "promoted",
  "outcome": "Validate parent done reconciliation using a sanitized real Hermes worker result.",
  "acceptance_criteria": [
    "real worker result is valid",
    "transition hook allows done",
    "no raw Hermes runtime ids are stored in the public repo"
  ],
  "scope_in": ["docs", "public-safe validation metadata"],
  "scope_out": ["production update", "private logs", "raw Hermes runtime ids", "secret access"],
  "risk_class": "R1-public-safe-validation",
  "codex_mode": "plan_and_validate",
  "review": {
    "independent_review_required": false,
    "human_gate_required": false,
    "autoreview_required": false
  },
  "factory_method_version": "OVERKILL_V3_5_FACTORY_10",
  "phase": "F8",
  "surfaces": ["docs"],
  "risk_initial": "R1",
  "risk_effective": "R1",
  "authority_max": "validation_only",
  "owner_worker": "public-safety-gate",
  "executor_identity": "public-safety-gate",
  "reviewer_identity": "not-required",
  "runtime_decision": "hermes_real_disposable_worker_result",
  "runtime_contract": {
    "local_tests_required": true,
    "real_runtime_smoke_required": true
  },
  "security_contract": {
    "public_safety_scan_required": true,
    "no_private_runtime_data_in_public_repo": true
  },
  "forbidden_actions": ["publish", "push", "merge", "deploy", "secret_access", "private_path_leak"],
  "done_definition": [
    "real public-safety-gate worker result exists",
    "worker result validates",
    "parent done reconciliation allows done",
    "disposable Hermes board is archived"
  ],
  "transition_event_required": true,
  "kanban_transition_event_ref": "real_worker_parent_done_reconciliation_smoke",
  "target_repo_paths": ["README.md", "scripts/factoryctl.py", "validation/hermes-real-runtime-smoke"]
}
