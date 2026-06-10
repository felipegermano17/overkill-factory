{
  "card_id": "VAL-VFINAL-R3-READY",
  "slice_id": "VAL_VFINAL_02",
  "owner_profile": "factory-orchestrator",
  "source_refs": ["synthetic vFinal source"],
  "source_state": "promoted",
  "outcome": "Validate that a high-risk vFinal card routes the new workers when readiness exists.",
  "acceptance_criteria": ["vFinal validation passes", "new vFinal workers are required", "no worker is blocked by missing input"],
  "scope_in": ["preflight validation only"],
  "scope_out": ["deploy", "secret access", "production"],
  "risk_class": "R3-security-api",
  "codex_mode": "plan_and_validate",
  "review": {"independent_review_required": true, "human_gate_required": true},
  "factory_method_version": "OVERKILL_VFINAL",
  "phase": "F12",
  "surfaces": ["code", "api", "auth", "cloud", "dependency", "access", "metrics", "agent"],
  "risk_initial": "R3",
  "risk_effective": "R3",
  "authority_max": "bounded_execution",
  "owner_worker": "factory-orchestrator",
  "executor_identity": "implementation-worker",
  "reviewer_identity": "independent-reviewer",
  "runtime_decision": "hermes_default",
  "runtime_contract": {
    "mode": "bounded_worker",
    "remote_proof_required": true,
    "ttl": "1 hour",
    "cost_owner": "product-owner",
    "cleanup_plan": "delete disposable artifacts",
    "secret_policy": "no secrets in remote proof",
    "artifact_policy": "public-safe logs only"
  },
  "security_contract": {
    "security_boundary": "auth/API/cloud",
    "agentic_ai_security_required": true
  },
  "security_role_separation": true,
  "forbidden_actions": ["deploy", "secret_access", "production_change"],
  "done_definition": ["preflight validates", "required workers are routed"],
  "transition_event_required": true,
  "kanban_transition_event_ref": "required_before_ready",
  "target_repo_paths": ["validation/cards/vfinal-r3-ready.md"],
  "material_execution": true,
  "requires_access": true,
  "rollback_or_recovery": {"owner": "release-owner", "plan": "revert the validation slice"},
  "security_scan_packet": {
    "scan_scope": ["api", "auth", "cloud"],
    "scanner_agent": "codex-security-runner",
    "security_owner": "security-owner"
  },
  "human_gate_packet": {
    "risk_owner": "product-owner",
    "security_owner": "security-owner",
    "rollback_owner": "release-owner"
  },
  "outcome_contract": {
    "outcome": "Prove vFinal high-risk routing with readiness present.",
    "users_or_actors": ["factory operator"],
    "problem": "The factory needs executable contracts for high-risk autonomous work.",
    "success_signals": ["gate report routes vFinal workers"],
    "non_goals": ["real deployment"],
    "open_questions": [],
    "evidence_refs": ["validation/cards/vfinal-r3-ready.md"]
  },
  "method_contract": {
    "selected_method": "spec-first with security architecture and access gate",
    "why_this_method": "High-risk material work needs plans and gates before execution.",
    "risk_tier": "R3",
    "required_plans": ["security_architecture_plan", "access_capability", "agent_eval_plan", "data_metrics_plan"],
    "required_gates": ["Security Architecture Gate", "Access & Capability Gate", "Agent Eval Gate", "Data/Metrics Gate"],
    "waivers": []
  },
  "software_development_plan": {
    "development_loop": "bounded implementation with QA and independent review",
    "qa": ["unit tests", "security preflight"],
    "review": ["independent review"]
  },
  "data_metrics_plan": {
    "events": ["validation_gate_report_created"],
    "metrics": ["blocked_worker_count", "required_worker_count"],
    "privacy_limits": ["no user data"]
  },
  "agent_eval_plan": {
    "behaviors": ["does not execute without access readiness"],
    "eval_cases": ["missing access", "ready access"],
    "failure_modes": ["agent ignores blocked gate"]
  },
  "dependency_map": {
    "providers": ["example cloud", "example repository"],
    "owners": ["product-owner"],
    "failure_modes": ["missing account", "provider unavailable"]
  },
  "access_capability": {
    "status": "ready",
    "required_capabilities": ["repository access", "cloud sandbox"],
    "available_capabilities": ["repository access", "cloud sandbox"],
    "missing_capabilities": [],
    "owner": "product-owner",
    "execution_limit": "preflight-only material simulation",
    "evidence_refs": ["validation/access-ready.md"]
  },
  "autonomy_readiness_packet": {
    "execution_mode": "bounded_execution",
    "accounts_ready": true,
    "tools_ready": true,
    "environment_ready": true,
    "cost_limit": "no real spend",
    "forbidden_actions": ["deploy", "secret_access", "production_change"],
    "rollback_path": "revert validation slice",
    "human_gates": ["R3 human gate"],
    "evidence_refs": ["validation/autonomy-ready.md"]
  },
  "security_architecture_plan": {
    "trust_boundaries": ["factory worker to repository", "worker to cloud sandbox"],
    "data_flows": ["public-safe validation metadata only"],
    "authn_authz": ["least privilege repository access", "sandbox-only cloud access"],
    "secrets_and_keys": ["no secrets available to this card"],
    "logging_and_detection": ["gate report and worker packet logs"],
    "threats": ["agent attempts forbidden deployment"],
    "security_owner": "security-owner",
    "evidence_refs": ["validation/security-architecture.md"]
  },
  "budget_contract": {
    "budget_owner": "product-owner",
    "limit": "no real spend",
    "cleanup": "delete disposable artifacts"
  },
  "factory_maturity_scorecard": {
    "project_type": "high-risk vFinal validation",
    "areas_checked": ["outcome", "method", "security architecture", "access", "agent evals", "metrics", "evidence"],
    "missing_areas": [],
    "risk_residuals": ["live Hermes validation still required before production claim"],
    "decision": "pass_with_owner",
    "evidence_refs": ["validation/factory-maturity.md"]
  },
  "loop_plan": {
    "unit_of_work": "preflight validation of vFinal routing",
    "verify": ["python scripts/factoryctl.py gate-report --card validation/cards/vfinal-r3-ready.md"],
    "review": ["independent review of gate report"],
    "rollback": "no material change"
  }
}
