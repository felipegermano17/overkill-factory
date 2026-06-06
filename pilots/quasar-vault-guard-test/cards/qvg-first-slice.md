```json
{
  "card_id": "QVG-PILOT-FIRST-SLICE",
  "slice_id": "QVG_DRY_PILOT_001",
  "owner_profile": "kaxis-pm",
  "source_refs": [
    "pilots/quasar-vault-guard-test/00-raw-paper.md",
    "pilots/quasar-vault-guard-test/02-product-sot.md",
    "pilots/quasar-vault-guard-test/04-architecture-candidate.md",
    "pilots/quasar-vault-guard-test/05-product-face-packet.md",
    "pilots/quasar-vault-guard-test/07-onchain-work-package.md",
    "pilots/quasar-vault-guard-test/08-security-scan-packet.md"
  ],
  "source_state": "compiled",
  "outcome": "Complete the first dry pilot slice by producing Product Face, security, Auditor preflight, independent review, human gate and Receipt Five evidence without sensitive actions.",
  "acceptance_criteria": [
    "factoryctl validate-card passes",
    "gate report lists Product Face, Codex Security, Auditor, Independent Reviewer and Human Gate Clerk as required",
    "Product Face prototype has desktop and mobile screenshots",
    "security_scan_result exists with evidence refs",
    "auditor_result exists with evidence refs and does not claim code audit pass",
    "independent_review_result exists with evidence refs",
    "human_gate_record exists and is test-only",
    "Receipt Five exists",
    "Hermes completion metadata records the evidence"
  ],
  "scope_in": [
    "dry pilot only",
    "static Product Face prototype",
    "factory artifacts",
    "worker packets",
    "structured evidence records",
    "Hermes Kanban completion"
  ],
  "scope_out": [
    "Solana program implementation",
    "Quasar compile",
    "wallet signing",
    "key access",
    "devnet write",
    "mainnet write",
    "funds movement",
    "custody action",
    "production release"
  ],
  "target_repo_paths": [
    "pilots/quasar-vault-guard-test"
  ],
  "conflict_set": [
    "Auditor path is mandatory, but no Quasar code exists yet; record Auditor preflight only.",
    "Human gate is authorized for test pilot only; do not expand to production authority."
  ],
  "risk_class": "R3-financial-critical",
  "why_this_class": "The pilot touches onchain, wallet, security and vault concepts even though it forbids network writes and funds.",
  "codex_mode": "required",
  "why_codex_mode": "Codex is the controlled runtime creating artifacts, validating contracts and recording evidence.",
  "product_security_checks": [
    "visible product states present",
    "wallet signing disabled",
    "mobile and desktop screenshots captured"
  ],
  "code_security_checks": [
    "prototype has no external scripts",
    "factory card forbids sensitive actions",
    "no secrets committed"
  ],
  "system_security_checks": [
    "no deploy",
    "no network write",
    "no key access",
    "no funds"
  ],
  "process_security_checks": [
    "worker packets generated",
    "Receipt Five required",
    "human gate record required",
    "independent review required"
  ],
  "verify_commands": [
    "python tools/factoryctl.py validate-card cards/qvg-first-slice.md",
    "python tools/factoryctl.py gate-report --card cards/qvg-first-slice.md --out evidence/gate-report-first-slice.json",
    "python tools/factoryctl.py validate-receipt evidence/receipt-five-first-slice.json",
    "python scripts/factoryctl.py validate-card pilots/quasar-vault-guard-test/cards/qvg-first-slice.md",
    "python scripts/factoryctl.py gate-report --card pilots/quasar-vault-guard-test/cards/qvg-first-slice.md",
    "python scripts/factoryctl.py validate-receipt pilots/quasar-vault-guard-test/evidence/receipt-five-first-slice.json",
    "python -m unittest discover -s tests -v"
  ],
  "evidence_expected": [
    "gate report",
    "worker packets",
    "desktop screenshot",
    "mobile screenshot",
    "security scan result",
    "auditor preflight result",
    "independent review result",
    "human gate record",
    "Receipt Five",
    "worker closure summary",
    "Hermes QA/security/cybersecurity/CTO/reviewer profile reviews",
    "Hermes task id"
  ],
  "review": {
    "QA_required": true,
    "independent_review_required": true,
    "security_review_required": true,
    "cybersecurity_review_required": true,
    "CTO_gate_required": true,
    "Felipe_gate_required": true
  },
  "rollback_or_recovery": "If any evidence is missing, keep the Hermes card blocked and do not claim pilot completion.",
  "security_role_separation": true,
  "protected_assets": [
    "KAXIS vault concept",
    "future Quasar program",
    "wallet identity",
    "operator authority",
    "human approval trail"
  ],
  "factory_method_version": "KAXIS_V3_5_FACTORY_10",
  "phase": "F11",
  "surfaces": [
    "ux",
    "frontend",
    "mobile",
    "wallet-ui",
    "security",
    "agent-runtime",
    "solana-quasar",
    "account-pda",
    "cpi",
    "compute-units"
  ],
  "risk_initial": "R3",
  "risk_effective": "R3",
  "authority_max": "dry_pilot_artifacts_only",
  "owner_worker": "Pilot Decomposition Planner",
  "executor_identity": "codex-overkill-factory",
  "reviewer_identity": "kaxis-reviewer",
  "runtime_decision": "hermes_default_with_codex_artifact_execution",
  "runtime_contract": {
    "mode": "dry_pilot",
    "hermes_board": "overkill-factory-pilot-10",
    "no_sensitive_runtime": true
  },
  "security_contract": {
    "security_boundary": "no_secrets_no_network_writes_no_signing",
    "scan_required": true,
    "auditor_required": true
  },
  "forbidden_actions": [
    "deploy",
    "quasar_compile_with_real_keys",
    "devnet_write",
    "mainnet_write",
    "wallet_signing",
    "secret_access",
    "funds_movement",
    "custody_action",
    "production_release"
  ],
  "done_definition": "Dry pilot first slice is complete when Product Face, security, Auditor preflight, independent review, human gate, Hermes completion and Receipt Five evidence exist.",
  "transition_event_required": true,
  "kanban_transition_event_ref": "required_before_done",
  "product_face_packet": {
    "screen_inventory": [
      "Vault Guard Dashboard",
      "Evidence Drawer",
      "Mobile Review View"
    ],
    "state_matrix": {
      "loading": "shown",
      "unknown": "shown",
      "safe": "shown",
      "blocked": "shown",
      "simulation_failed": "shown",
      "wallet_rejected": "shown"
    },
    "design_contract_ref": "pilots/quasar-vault-guard-test/05-product-face-packet.md",
    "mobile_breakpoints": [
      "375",
      "768",
      "1440"
    ],
    "wallet_flow_matrix": {
      "connect": "shown",
      "sign": "disabled_for_pilot",
      "reject": "shown",
      "unknown_authority": "blocked"
    },
    "a11y_acceptance": [
      "keyboard",
      "contrast",
      "labels",
      "no_color_only_state"
    ],
    "performance_budget": {
      "external_assets": "none",
      "primary_decision_above_fold": true
    },
    "visual_evidence_plan": [
      "desktop screenshot",
      "mobile screenshot"
    ]
  },
  "onchain_work_package": {
    "quasar_source_ref": "pilots/quasar-vault-guard-test/07-onchain-work-package.md",
    "quasar_required": true,
    "framework_default": "quasar_non_anchor",
    "account_map": [
      "vault_state",
      "operator_identity",
      "pending_instruction",
      "audit_receipt"
    ],
    "instruction_abi": [
      "review_vault_instruction",
      "record_audit_receipt",
      "block_instruction"
    ],
    "pda_derivation": [
      "[vault, vault_id]",
      "[pending, vault_id, instruction_hash]",
      "[audit, vault_id, receipt_hash]"
    ],
    "cpi_allowlist": [
      "none_for_pilot"
    ],
    "compute_unit_budget": "not_measured_no_program_code",
    "auditor_required": true,
    "auditor_tool_ref": "solanabr/Auditor"
  },
  "security_scan_packet": {
    "security_owner": "kaxis-cybersecurity",
    "scanner_agent": "codex-security-runner",
    "scan_timing": "before_done",
    "scan_scope": [
      "Product SOT",
      "architecture",
      "Product Face prototype",
      "onchain work package",
      "worker packets",
      "human gate",
      "Receipt Five",
      "authority boundaries"
    ],
    "required_tools": [
      "codex-security:security-scan",
      "solanabr/Auditor"
    ],
    "acceptance_policy": {
      "blocking_findings_allowed": false,
      "waiver_requires_human": true,
      "evidence_required": true
    }
  },
  "human_gate_packet": {
    "gate_type": "R3_dry_pilot",
    "required_approvers": [
      "Felipe"
    ],
    "decision_state": "approved_for_dry_pilot_only",
    "risk_owner": "Felipe",
    "security_owner": "kaxis-cybersecurity",
    "rollback_owner": "codex-overkill-factory",
    "waiver_policy": "no production waiver; test-only authorization from active user instruction"
  }
}
```
