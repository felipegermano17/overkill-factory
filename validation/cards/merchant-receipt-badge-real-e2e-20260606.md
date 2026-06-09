```json
{
  "card_id": "MRB-REAL-E2E-20260606",
  "slice_id": "MRB_FACTORY13_REAL_E2E_001",
  "owner_profile": "factory-orchestrator",
  "source_refs": [
    "validation/hermes-live/real-e2e-202606062115/raw-paper.md",
    "Factory 13 real Hermes E2E validation round"
  ],
  "source_state": "raw",
  "outcome": "Run a real Hermes/Kanban end-to-end Overkill Factory validation from raw paper to worker graph, evidence, review, human-gate boundary, Receipt Five and done reconciliation for a small offchain + Product Face + Solana/Quasar devnet-read product.",
  "acceptance_criteria": [
    "Hermes materializes a real main card and required worker cards on the disposable board",
    "required worker routing includes builders instead of relying on implementation-worker",
    "Product Face, frontend, backend/API, data, wallet boundary, integration, test automation, Solana/Quasar, security, QA, review, handoff and human gate are represented as worker cards when triggered",
    "workers that cannot honestly prove a toolchain boundary record WAIVED or PENDING rather than fake PASS",
    "done is blocked until worker results and Receipt Five reconcile",
    "final evidence records board, task ids, worker ids, pass/fail state, boundaries and remaining risk"
  ],
  "scope_in": [
    "raw paper intake",
    "Product SOT candidate",
    "architecture candidate",
    "Product Face packet and result",
    "offchain receipt API boundary",
    "dashboard proof boundary",
    "file or JSON persistence",
    "Solana/Quasar work package",
    "Auditor route",
    "worker packets",
    "worker result records",
    "Receipt Five",
    "Hermes Kanban reconciliation"
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
    "real Auditor code-audit claim without toolchain proof",
    "real Quasar build/test claim without toolchain proof"
  ],
  "target_repo_paths": [
    "validation/hermes-live/real-e2e-202606062115",
    "products/devnet-receipt-pass"
  ],
  "conflict_set": [
    "The product mentions devnet, but this run forbids devnet writes.",
    "The product has wallet and signing concepts, but the validation can only prove UI/transaction boundaries.",
    "The onchain package must be Quasar-oriented and must not assume Anchor.",
    "Local scripts may support validation, but Hermes/Kanban is the test floor."
  ],
  "risk_class": "R3-onchain-product-validation",
  "why_this_class": "The card combines product-facing UI, backend/API, data persistence, wallet boundaries, Solana/Quasar, security, public artifacts and release-like evidence while sensitive authority remains forbidden.",
  "codex_mode": "required",
  "why_codex_mode": "Codex/Hermes workers need to inspect files, create evidence, run validators and preserve a public-safe audit trail.",
  "product_security_checks": [
    "signing-disabled state is visible",
    "deploy-disabled state is visible",
    "offline/error/loading states are visible",
    "desktop and mobile proof are required"
  ],
  "code_security_checks": [
    "no committed secrets",
    "no external browser scripts",
    "read-only devnet proof only",
    "public-safe evidence paths"
  ],
  "system_security_checks": [
    "no deploy",
    "no devnet write",
    "no mainnet write",
    "no key access",
    "no funds"
  ],
  "process_security_checks": [
    "Hermes worker cards are created",
    "worker results are reconciled before done",
    "human gate is validation-only",
    "Receipt Five is required",
    "toolchain gaps are recorded as boundaries"
  ],
  "verify_commands": [
    "python scripts/factoryctl.py validate-card validation/cards/merchant-receipt-badge-real-e2e-20260606.md",
    "python scripts/factoryctl.py gate-report --card validation/cards/merchant-receipt-badge-real-e2e-20260606.md",
    "python scripts/factoryctl.py worker-packet --worker all --required-only --card validation/cards/merchant-receipt-badge-real-e2e-20260606.md --out validation/hermes-live/real-e2e-202606062115/worker-packets",
    "python scripts/validate_public_json_artifacts.py",
    "python scripts/public_safety_scan.py",
    "python scripts/secret_safety_scan.py",
    "python scripts/validate_worker_profiles.py"
  ],
  "evidence_expected": [
    "Hermes board evidence",
    "Hermes main task id",
    "Hermes worker task ids",
    "gate report",
    "worker packets",
    "worker result records",
    "Product Face proof or explicit boundary",
    "security scan result",
    "Auditor result or explicit bounded waiver",
    "human gate record",
    "Receipt Five",
    "done transition plan"
  ],
  "review": {
    "QA_required": true,
    "independent_review_required": true,
    "security_review_required": true,
    "cybersecurity_review_required": true,
    "human_gate_required": true,
    "autoreview_required": true,
    "test_automation_required": true
  },
  "rollback_or_recovery": "If Hermes materialization, worker execution, evidence reconciliation, public safety or Receipt Five fails, keep the main card blocked and record the failure in validation/hermes-live/real-e2e-202606062115.",
  "security_role_separation": true,
  "protected_assets": [
    "receipt integrity",
    "operator identity",
    "signing boundary",
    "future Quasar program",
    "public release boundary"
  ],
  "factory_method_version": "OVERKILL_FACTORY_13",
  "phase": "F13",
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
    "data",
    "storage",
    "security",
    "cybersecurity",
    "onchain",
    "solana-quasar",
    "account-pda",
    "cpi",
    "compute-units",
    "devnet",
    "wallet",
    "wallet-ui",
    "transaction",
    "signing",
    "crypto",
    "keys",
    "integration",
    "fullstack",
    "e2e",
    "test",
    "qa",
    "regression",
    "automation",
    "public",
    "opensource",
    "repo-public"
  ],
  "risk_initial": "R3",
  "risk_effective": "R3",
  "authority_max": "local_validation_and_read_only_devnet",
  "owner_worker": "Factory Orchestrator",
  "executor_identity": "codex-overkill-factory",
  "reviewer_identity": "independent-reviewer",
  "runtime_decision": "hermes_kanban_with_codex_artifact_execution",
  "runtime_contract": {
    "mode": "factory13_real_hermes_e2e_validation",
    "hermes_board": "private-validation-board",
    "codex_runtime_allowed": true,
    "remote_proof_required": false,
    "ttl": "single_validation_run",
    "cost_owner": "test-product-owner",
    "cleanup_plan": "keep public-safe evidence and remove only failed runtime scratch when needed",
    "secret_policy": "no secrets may be mounted, requested, copied or inferred",
    "artifact_policy": "only public-relative validation artifacts may be written",
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
    ],
    "acceptance_policy": {
      "blocking_findings_allowed": false,
      "waiver_requires_human": true,
      "evidence_required": true
    }
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
  "done_definition": "The Hermes E2E validation card is done only when the disposable board has real worker cards, required worker results, a validation-only human gate, Receipt Five and done transition reconciliation.",
  "transition_event_required": true,
  "kanban_transition_event_ref": "validation/hermes-live/real-e2e-202606062115/receipt-five.json",
  "product_face_packet": {
    "screen_inventory": [
      "Merchant Receipt Badge",
      "Receipt State Matrix",
      "Safety Boundary Panel",
      "Mobile Merchant Review"
    ],
    "state_matrix": {
      "loading": "required",
      "devnet-read-ok": "required",
      "offline": "required",
      "error": "required",
      "signing-disabled": "required",
      "deploy-disabled": "required"
    },
    "mobile_breakpoints": [
      "390",
      "768",
      "1440"
    ],
    "wallet_flow_matrix": {
      "connect": "out_of_scope",
      "sign": "disabled_for_validation",
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
  "product_face_result_ref": "validation/hermes-live/real-e2e-202606062115/product-face-result.json",
  "onchain_work_package": {
    "quasar_source_ref": "products/devnet-receipt-pass/onchain/quasar/src/lib.rs",
    "quasar_required": true,
    "framework_default": "quasar_non_anchor",
    "account_map": [
      "merchant_receipt_state",
      "merchant_identity",
      "receipt_event",
      "audit_receipt"
    ],
    "instruction_abi": [
      "init_receipt_badge",
      "append_receipt_event",
      "close_receipt_badge"
    ],
    "pda_derivation": [
      "[merchant-receipt, merchant, receipt_hash]",
      "[merchant-receipt-event, receipt_hash, event_hash]",
      "[merchant-audit, receipt_hash]"
    ],
    "cpi_allowlist": [
      "none_for_validation"
    ],
    "compute_unit_budget": "bounded_future_work_not_measured_in_this_card",
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
      "receipt API boundary",
      "dashboard",
      "Quasar work package",
      "worker results",
      "public safety",
      "authority boundaries"
    ],
    "required_tools": [
      "codex-security",
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
