```json
{
  "card_id": "KFP-V35-POS-SEC-SCAN",
  "slice_id": "KAXIS_FACTORY_V35_10",
  "owner_profile": "kaxis-security",
  "source_refs": ["KAXIS V3.5 Agent Workforce methodology", "Codex Security timing requirement"],
  "source_state": "compiled",
  "outcome": "Positive gate test: R3 security work has role separation and Codex Security scan packet.",
  "acceptance_criteria": [
    "promote dry-run passes",
    "completion without security_scan_result fails",
    "completion with security_scan_result passes"
  ],
  "scope_in": ["gate validation only", "security scan metadata validation"],
  "scope_out": ["code edit", "deploy", "secret access", "public endpoint change"],
  "target_repo_paths": ["docs/kaxis/factory-v35-10"],
  "conflict_set": ["Security review must be operational evidence, not just prose."],
  "risk_class": "R3-financial-critical",
  "why_this_class": "Security-sensitive agent-runtime surface can affect execution integrity.",
  "codex_mode": "advisory",
  "why_codex_mode": "Codex observes and validates gates only.",
  "product_security_checks": ["no product approval"],
  "code_security_checks": ["Codex Security scan plan and result required"],
  "system_security_checks": ["no secrets or infra mutation"],
  "process_security_checks": ["role separation, scan packet, Receipt Five and transition event required"],
  "verify_commands": [
    "hermes kanban promote --dry-run <task_id>",
    "hermes kanban complete <task_id> --metadata <json>"
  ],
  "evidence_expected": [
    "promotion accepted by V3.5 ready gate",
    "completion refused without security_scan_result",
    "completion accepted with security_scan_result"
  ],
  "review": {
    "QA_required": true,
    "independent_review_required": true,
    "security_review_required": true,
    "cybersecurity_review_required": true,
    "CTO_gate_required": true,
    "Felipe_gate_required": true
  },
  "rollback_or_recovery": "Keep blocked if scan result is missing or has blocking findings.",
  "protected_assets": ["Hermes agent runtime", "Kanban promotion boundary"],
  "factory_method_version": "KAXIS_V3_5_FACTORY_10",
  "phase": "F8",
  "surfaces": ["security", "agent-runtime", "prompt-injection"],
  "risk_initial": "R3",
  "risk_effective": "R3",
  "authority_max": "validate_gate_only",
  "owner_worker": "Security Architect",
  "executor_identity": "kaxis-security",
  "reviewer_identity": "kaxis-cybersecurity",
  "runtime_decision": "codex_security_required",
  "runtime_contract": {"mode": "read_only_gate_test"},
  "security_contract": {"security_boundary": "scan_required"},
  "forbidden_actions": ["code_edit", "deploy", "secret_access", "runtime_change"],
  "done_definition": "Gate validates scan packet and completion requires scan result evidence.",
  "transition_event_required": true,
  "kanban_transition_event_ref": "required_before_ready",
  "security_role_separation": true,
  "security_scan_packet": {
    "security_owner": "kaxis-security",
    "scanner_agent": "kaxis-cybersecurity",
    "scan_timing": "before_done",
    "scan_scope": ["card contract", "runtime boundary", "prompt injection risk", "agent handoff risk"],
    "required_tools": ["codex-security:security-scan", "cybersecurity-review"],
    "acceptance_policy": {
      "blocking_findings_allowed": false,
      "waiver_requires_human": true,
      "evidence_required": true
    }
  }
}
```
