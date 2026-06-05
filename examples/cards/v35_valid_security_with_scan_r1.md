```json
{
  "card_id": "KFP-V35-POS-SEC-SCAN-R1",
  "slice_id": "KAXIS_FACTORY_V35_10",
  "owner_profile": "kaxis-security",
  "source_refs": ["KAXIS V3.5 Agent Workforce methodology", "Codex Security timing requirement"],
  "source_state": "compiled",
  "outcome": "Positive gate test: a safe security-scan fixture can pass ready and done only with Codex Security result metadata.",
  "acceptance_criteria": [
    "promote passes",
    "completion without security_scan_result fails",
    "completion with security_scan_result passes"
  ],
  "scope_in": ["gate validation only", "security scan metadata validation"],
  "scope_out": ["code edit", "deploy", "secret access", "public endpoint change"],
  "target_repo_paths": ["docs/kaxis/factory-v35-10"],
  "conflict_set": ["Security scan evidence must be operational and machine-checkable."],
  "risk_class": "R1-dev-safe",
  "why_this_class": "Local gate proof only; no production, code, secret, deploy or financial action.",
  "codex_mode": "advisory",
  "why_codex_mode": "Codex observes and validates gates only.",
  "product_security_checks": ["no product approval"],
  "code_security_checks": ["Codex Security scan plan and result required"],
  "system_security_checks": ["no secrets or infra mutation"],
  "process_security_checks": ["scan packet, Receipt Five and transition event required"],
  "verify_commands": [
    "hermes kanban promote <task_id>",
    "hermes kanban complete <task_id> --metadata <json>"
  ],
  "evidence_expected": [
    "promotion accepted by V3.5 ready gate",
    "completion refused without security_scan_result",
    "completion accepted with security_scan_result"
  ],
  "review": {
    "QA_required": false,
    "independent_review_required": false,
    "security_review_required": false,
    "cybersecurity_review_required": false,
    "CTO_gate_required": false,
    "Felipe_gate_required": false
  },
  "factory_method_version": "KAXIS_V3_5_FACTORY_10",
  "phase": "F8",
  "surfaces": ["security", "agent-runtime"],
  "risk_initial": "R1",
  "risk_effective": "R1",
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
  "security_scan_packet_required": true,
  "security_scan_packet": {
    "security_owner": "kaxis-security",
    "scanner_agent": "kaxis-cybersecurity",
    "scan_timing": "before_done",
    "scan_scope": ["card contract", "runtime boundary", "agent handoff risk"],
    "required_tools": ["codex-security:security-scan", "cybersecurity-review"],
    "acceptance_policy": {
      "blocking_findings_allowed": false,
      "waiver_requires_human": true,
      "evidence_required": true
    }
  }
}
```
