{
  "card_id": "VAL-VFINAL-R3-MISSING-ACCESS",
  "slice_id": "VAL_VFINAL_01",
  "owner_profile": "factory-orchestrator",
  "source_refs": ["synthetic vFinal source"],
  "source_state": "promoted",
  "outcome": "Validate that vFinal blocks material execution without security architecture and access readiness.",
  "acceptance_criteria": ["preflight reports missing security architecture", "preflight reports missing access readiness"],
  "scope_in": ["preflight validation only"],
  "scope_out": ["deploy", "secret access", "production"],
  "risk_class": "R3-security-api",
  "codex_mode": "plan_and_validate",
  "review": {"independent_review_required": true, "human_gate_required": true},
  "factory_method_version": "OVERKILL_VFINAL",
  "phase": "F12",
  "surfaces": ["code", "api", "auth", "access"],
  "risk_initial": "R3",
  "risk_effective": "R3",
  "authority_max": "planning_only",
  "owner_worker": "factory-orchestrator",
  "executor_identity": "implementation-worker",
  "reviewer_identity": "independent-reviewer",
  "runtime_decision": "preflight_only",
  "runtime_contract": {"mode": "preflight_only"},
  "security_contract": {"security_boundary": "auth/API"},
  "security_role_separation": true,
  "forbidden_actions": ["deploy", "secret_access", "production_change"],
  "done_definition": ["preflight blocks for the right reasons"],
  "transition_event_required": true,
  "kanban_transition_event_ref": "required_before_ready",
  "target_repo_paths": ["validation/cards/vfinal-r3-missing-security-access.md"],
  "material_execution": true,
  "requires_access": true,
  "security_scan_packet": {
    "scan_scope": ["api", "auth"],
    "scanner_agent": "codex-security-runner",
    "security_owner": "security-owner"
  },
  "human_gate_packet": {
    "risk_owner": "product-owner",
    "security_owner": "security-owner",
    "rollback_owner": "release-owner"
  },
  "outcome_contract": {
    "outcome": "Prove vFinal access/security gates block material execution.",
    "users_or_actors": ["factory operator"],
    "problem": "Agents must not start material execution without required readiness.",
    "success_signals": ["expected validation errors are produced"],
    "non_goals": ["real deployment"],
    "open_questions": [],
    "evidence_refs": ["validation/cards/vfinal-r3-missing-security-access.md"]
  },
  "method_contract": {
    "selected_method": "preflight validation",
    "why_this_method": "This card validates gate behavior only.",
    "risk_tier": "R3",
    "required_plans": ["security_architecture_plan", "access_capability"],
    "required_gates": ["Security Architecture Gate", "Access & Capability Gate"],
    "waivers": []
  },
  "loop_plan": {
    "unit_of_work": "preflight validation",
    "verify": ["python scripts/factoryctl.py validate-card validation/cards/vfinal-r3-missing-security-access.md"],
    "review": ["independent review of validation errors"],
    "rollback": "no material change"
  }
}
