```json
{
  "card_id": "DRP-FULL-LINE-PILOT",
  "slice_id": "DRP_FACTORY12_FULL_001",
  "owner_profile": "factory-orchestrator",
  "source_refs": [
    "pilots/devnet-receipt-pass-test/00-raw-paper.md",
    "pilots/devnet-receipt-pass-test/01-source-ledger.md",
    "pilots/devnet-receipt-pass-test/02-product-sot.md",
    "pilots/devnet-receipt-pass-test/04-architecture-candidate.md",
    "pilots/devnet-receipt-pass-test/05-product-face-packet.md",
    "pilots/devnet-receipt-pass-test/07-onchain-work-package.md",
    "pilots/devnet-receipt-pass-test/08-security-scan-packet.md",
    "validation product pilot"
  ],
  "source_state": "compiled",
  "outcome": "Complete a full-line factory validation from raw paper to Receipt Five using a product that includes read-only Solana devnet evidence, a visible offchain product face and a Quasar-oriented onchain work package.",
  "acceptance_criteria": [
    "factoryctl validate-card passes",
    "gate report lists all blocking workers without missing inputs",
    "read-only devnet proof exists or the card remains blocked",
    "Product Face proof has desktop and mobile screenshots",
    "Codex Security result exists with evidence refs",
    "Solana/Quasar Auditor result exists and does not claim code audit without toolchain proof",
    "all required worker result records validate and the advisory remote proof boundary is recorded",
    "human gate record is validation-only",
    "Receipt Five validates",
    "transition plan allows done only after worker closure"
  ],
  "scope_in": [
    "raw paper intake",
    "source ledger",
    "Product SOT",
    "architecture",
    "Product Face",
    "Quasar work package",
    "security scan packet",
    "Hermes-ready decomposition card",
    "worker packets",
    "worker result records",
    "read-only devnet proof",
    "Receipt Five closure"
  ],
  "scope_out": [
    "wallet signing",
    "devnet write",
    "mainnet write",
    "program deploy",
    "production release",
    "funds movement",
    "custody action",
    "secret access",
    "real Auditor code-audit claim"
  ],
  "target_repo_paths": [
    "products/devnet-receipt-pass",
    "pilots/devnet-receipt-pass-test"
  ],
  "conflict_set": [
    "The product has onchain intent, but this runtime only proves read-only devnet access.",
    "Auditor is mandatory, but without Quasar toolchain proof the result must be preflight or waiver.",
    "Release and monitoring workers are triggered for line coverage, but production promotion remains forbidden."
  ],
  "risk_class": "R3-onchain-security-validation",
  "why_this_class": "The validation includes onchain, wallet, signing, security, public release and agentic-operation surfaces even though sensitive actions are forbidden.",
  "codex_mode": "required",
  "why_codex_mode": "Codex creates files, runs validation commands and records evidence while Hermes remains the durable agent orchestration model.",
  "product_security_checks": [
    "visible boundaries for signing and deploy",
    "desktop screenshot",
    "mobile screenshot",
    "state matrix for loading, devnet ok, offline and error"
  ],
  "code_security_checks": [
    "no external browser scripts",
    "no committed secrets",
    "read-only devnet RPC",
    "Quasar outline only"
  ],
  "system_security_checks": [
    "no deploy",
    "no devnet write",
    "no mainnet write",
    "no key access",
    "no funds"
  ],
  "process_security_checks": [
    "worker packets generated",
    "specialist results required",
    "human gate validation-only",
    "Receipt Five required",
    "transition plan enforceable"
  ],
  "verify_commands": [
    "node products/devnet-receipt-pass/offchain/receipt-service.mjs",
    "python scripts/factoryctl.py validate-card pilots/devnet-receipt-pass-test/cards/drp-full-line-pilot.md",
    "python scripts/factoryctl.py gate-report --card pilots/devnet-receipt-pass-test/cards/drp-full-line-pilot.md --out pilots/devnet-receipt-pass-test/evidence/gate-report-full-line.json",
    "python scripts/factoryctl.py worker-packet --worker all --card pilots/devnet-receipt-pass-test/cards/drp-full-line-pilot.md --out pilots/devnet-receipt-pass-test/worker-packets",
    "python scripts/product_face_proof.py --target products/devnet-receipt-pass/offchain/dashboard.html --out pilots/devnet-receipt-pass-test/worker-results/product-face-result.json",
    "python scripts/factoryctl.py validate-receipt pilots/devnet-receipt-pass-test/evidence/receipt-five-full-line.json",
    "python scripts/factoryctl.py validate-completion --card pilots/devnet-receipt-pass-test/cards/drp-full-line-pilot.md --receipt pilots/devnet-receipt-pass-test/evidence/receipt-five-full-line.json",
    "python scripts/factoryctl.py transition-plan --card pilots/devnet-receipt-pass-test/cards/drp-full-line-pilot.md --from-status in_progress --to-status done --receipt pilots/devnet-receipt-pass-test/evidence/receipt-five-full-line.json --worker-results-dir pilots/devnet-receipt-pass-test/worker-results --enforce --out pilots/devnet-receipt-pass-test/evidence/transition-plan-done.json",
    "python scripts/public_safety_scan.py",
    "python scripts/secret_safety_scan.py",
    "python -m unittest discover -s tests -p \"test_*.py\" -q"
  ],
  "evidence_expected": [
    "devnet read proof",
    "gate report",
    "worker packets",
    "Product Face screenshots",
    "security scan result",
    "Auditor preflight waiver",
    "OWASP/AppSec review",
    "agentic AI security review",
    "cloud/infra review",
    "crypto/key review",
    "supply-chain review",
    "remote proof boundary or waiver record",
    "release boundary record",
    "monitoring boundary record",
    "public safety result",
    "independent review result",
    "human gate record",
    "handoff packet",
    "memory stewardship result",
    "skill/eval result",
    "Receipt Five",
    "transition plan"
  ],
  "review": {
    "QA_required": true,
    "independent_review_required": true,
    "security_review_required": true,
    "cybersecurity_review_required": true,
    "CTO_gate_required": true,
    "human_gate_required": true,
    "autoreview_required": true
  },
  "rollback_or_recovery": "If devnet read, Product Face, worker closure, Receipt Five or public safety fails, keep the card blocked and delete only generated validation artifacts before rerun.",
  "security_role_separation": true,
  "protected_assets": [
    "receipt integrity",
    "future Quasar program",
    "operator identity",
    "signing boundary",
    "public release boundary"
  ],
  "factory_method_version": "OVERKILL_V3_6_FACTORY_12",
  "phase": "F16",
  "surfaces": [
    "sot",
    "architecture",
    "docs",
    "documentation",
    "decomposition",
    "kanban-card-graph",
    "implementation",
    "code",
    "frontend",
    "mobile",
    "ux",
    "product-face",
    "web",
    "browser",
    "api",
    "backend",
    "auth",
    "security",
    "cybersecurity",
    "agent",
    "agents",
    "llm",
    "prompt",
    "memory",
    "tools",
    "autonomous",
    "skill",
    "eval",
    "onchain",
    "solana-quasar",
    "account-pda",
    "cpi",
    "compute-units",
    "wallet",
    "wallet-ui",
    "signing",
    "crypto",
    "keys",
    "secrets",
    "cloud",
    "infra",
    "deploy",
    "ci",
    "supply-chain",
    "public",
    "opensource",
    "repo-public",
    "release",
    "production",
    "rollback",
    "monitoring",
    "observability",
    "logging",
    "alerting",
    "incident"
  ],
  "risk_initial": "R3",
  "risk_effective": "R3",
  "authority_max": "local_validation_and_read_only_devnet",
  "owner_worker": "Factory Orchestrator",
  "executor_identity": "codex-overkill-factory",
  "reviewer_identity": "independent-reviewer",
  "runtime_decision": "hermes_kanban_with_codex_artifact_execution",
  "runtime_contract": {
    "mode": "full_line_public_validation",
    "hermes_board": "overkill-factory-validation",
    "codex_runtime_allowed": true,
    "remote_proof_required": false,
    "ttl": "single_validation_run",
    "cost_owner": "test-product-owner",
    "cleanup_plan": "delete generated runtime artifacts after failed rerun and keep only validation evidence",
    "secret_policy": "no secrets may be mounted, requested, copied or inferred",
    "artifact_policy": "only public-relative validation artifacts may be written",
    "remote_proof_policy": {
      "runtime": "local_proof_for_validation_remote_proof_before_production_parity",
      "ttl": "single_validation_run",
      "cleanup": "required"
    },
    "devnet_access": "read_only_json_rpc",
    "no_sensitive_runtime": true
  },
  "security_contract": {
    "security_boundary": "no_secrets_no_signing_no_network_writes_no_funds",
    "scan_required": true,
    "auditor_required": true,
    "agentic_ai_security_required": true,
    "owasp_controls": [
      "access control",
      "cryptographic failures",
      "injection",
      "insecure design",
      "security misconfiguration",
      "vulnerable components",
      "auth failures",
      "integrity failures",
      "logging and monitoring",
      "ssrf",
      "api authorization",
      "agent tool boundaries"
    ]
  },
  "forbidden_actions": [
    "wallet_signing",
    "devnet_write",
    "mainnet_write",
    "program_deploy",
    "secret_access",
    "funds_movement",
    "custody_action",
    "production_release",
    "upgrade_authority_change",
    "claim_real_auditor_code_audit_without_toolchain"
  ],
  "done_definition": "The full-line validation card is done only when devnet read proof, Product Face proof, all blocking worker results, validation-only human gate, Receipt Five and done transition plan validate.",
  "transition_event_required": true,
  "kanban_transition_event_ref": "pilots/devnet-receipt-pass-test/evidence/receipt-five-full-line.json",
  "product_face_packet": {
    "screen_inventory": [
      "Receipt Dashboard",
      "Safety Boundary Panel",
      "State Matrix",
      "Mobile Receipt Review"
    ],
    "state_matrix": {
      "loading": "shown",
      "devnet-ok": "shown",
      "offline": "shown",
      "error": "shown",
      "signing-disabled": "shown",
      "deploy-disabled": "shown"
    },
    "design_contract_ref": "pilots/devnet-receipt-pass-test/05-product-face-packet.md",
    "mobile_breakpoints": [
      "390",
      "768",
      "1440"
    ],
    "wallet_flow_matrix": {
      "connect": "out_of_scope",
      "sign": "disabled_for_pilot",
      "reject": "shown_as_boundary",
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
  "product_face_result_ref": "pilots/devnet-receipt-pass-test/worker-results/product-face-result.json",
  "onchain_work_package": {
    "quasar_source_ref": "products/devnet-receipt-pass/onchain/quasar/src/lib.rs",
    "work_package_ref": "pilots/devnet-receipt-pass-test/07-onchain-work-package.md",
    "quasar_required": true,
    "framework_default": "quasar_non_anchor",
    "account_map": [
      "receipt_state",
      "operator_identity",
      "receipt_event",
      "audit_receipt"
    ],
    "instruction_abi": [
      "init_receipt",
      "append_receipt_event",
      "close_receipt"
    ],
    "pda_derivation": [
      "[receipt, operator, receipt_hash]",
      "[receipt-event, receipt_hash, event_hash]",
      "[audit, receipt_hash]"
    ],
    "cpi_allowlist": [
      "none_for_pilot"
    ],
    "compute_unit_budget": "bounded_future_work_not_measured_in_this_runtime",
    "auditor_required": true,
    "auditor_tool_ref": "solanabr/Auditor"
  },
  "security_scan_packet": {
    "security_owner": "security-runner",
    "scanner_agent": "codex-security-runner",
    "scan_timing": "before_done",
    "scan_scope": [
      "raw paper",
      "Product SOT",
      "architecture",
      "Product Face",
      "receipt service",
      "Quasar work package",
      "worker packets",
      "worker results",
      "public safety",
      "authority boundaries"
    ],
    "required_tools": [
      "codex-security",
      "codex-security:security-scan",
      "OWASP Web",
      "OWASP API",
      "OWASP LLM",
      "solanabr/Auditor",
      "supply-chain"
    ],
    "acceptance_policy": {
      "blocking_findings_allowed": false,
      "waiver_requires_human": true,
      "evidence_required": true
    }
  },
  "human_gate_packet": {
    "gate_type": "R3_validation",
    "required_approvers": [
      "active-user-instruction"
    ],
    "decision_state": "external_active_user_instruction_approved_for_validation_only",
    "risk_owner": "test-product-owner",
    "security_owner": "security-runner",
    "rollback_owner": "factory-orchestrator",
    "waiver_policy": "no production waiver; Auditor and remote proof waivers allowed only for bounded validation when explicitly recorded"
  }
}
```
