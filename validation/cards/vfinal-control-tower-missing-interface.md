{
  "card_id": "VAL-VFINAL-CONTROL-TOWER-MISSING-INTERFACE",
  "slice_id": "VAL_VFINAL_CONTROL_TOWER_01",
  "owner_profile": "factory-orchestrator",
  "source_refs": ["synthetic vFinal source"],
  "source_state": "promoted",
  "outcome": "Validate that vFinal routes and blocks owner-interface work when Control Tower evidence is missing.",
  "acceptance_criteria": [
    "Factory Concierge is required",
    "Discord Control Tower Bridge is required",
    "Control Tower Projection Worker is required",
    "missing project projection and Discord mapping block material visibility"
  ],
  "scope_in": ["preflight validation only"],
  "scope_out": ["Discord API calls", "real approval", "production", "secret access"],
  "risk_class": "R2-owner-interface",
  "codex_mode": "plan_and_validate",
  "review": {"independent_review_required": true, "human_gate_required": false},
  "factory_method_version": "OVERKILL_VFINAL",
  "phase": "F19",
  "surfaces": ["discord", "control-tower", "owner-interface", "approval", "forecast"],
  "risk_initial": "R2",
  "risk_effective": "R2",
  "authority_max": "preflight_only",
  "owner_worker": "factory-orchestrator",
  "executor_identity": "discord-control-tower-bridge",
  "reviewer_identity": "independent-reviewer",
  "runtime_decision": "preflight_only",
  "runtime_contract": {"mode": "preflight_only"},
  "security_contract": {"security_boundary": "owner-interface"},
  "security_role_separation": true,
  "forbidden_actions": ["real_discord_message", "approval_spoofing", "production_change", "secret_access"],
  "done_definition": ["preflight routes Control Tower workers", "missing interface evidence blocks"],
  "transition_event_required": true,
  "kanban_transition_event_ref": "required_before_ready",
  "target_repo_paths": ["validation/cards/vfinal-control-tower-missing-interface.md"],
  "material_execution": true,
  "owner_interface_required": true,
  "control_tower_required": true,
  "discord_control_tower_required": true,
  "approval_required": true,
  "outcome_contract": {
    "outcome": "Prove owner-facing Control Tower work is visible, structured and runtime-backed.",
    "users_or_actors": ["factory owner", "factory operator"],
    "problem": "A chat interface can become a dangerous parallel source of truth unless projection and approval records are enforced.",
    "success_signals": ["gate report routes and blocks owner interface workers"],
    "non_goals": ["real Discord integration"],
    "open_questions": [],
    "evidence_refs": ["validation/cards/vfinal-control-tower-missing-interface.md"]
  },
  "method_contract": {
    "selected_method": "preflight validation of owner interface contracts",
    "why_this_method": "The interface layer must be validated before it can ask for approvals or show production status.",
    "risk_tier": "R2",
    "required_plans": ["project_projection", "approval_request", "control_tower_event", "discord_control_tower_mapping"],
    "required_gates": ["Control Tower Gate", "Review Gate"],
    "waivers": []
  },
  "loop_plan": {
    "unit_of_work": "preflight validation of Control Tower routing",
    "verify": [
      "python scripts/factoryctl.py gate-report --card validation/cards/vfinal-control-tower-missing-interface.md"
    ],
    "review": ["independent review of gate report"],
    "rollback": "no material change"
  }
}
