# Swiss Watch Gear Matrix

> Document status: GENERATED MAINTAINER BASELINE.
> Source: `.tmp/swiss-watch/factory-workflow-compiled-plan.json`, `agents/worker-registry.public.json`, `templates/hermes-typed-block-policy.json`.
> Runtime boundary: Hermes Kanban remains the runtime source of truth. This matrix is an audit view, not a parallel state store.

## Purpose

This matrix turns the Swiss Watch Reliability Program into a phase-by-phase audit baseline. It preserves every factory phase and asks whether each gear has enough explicit input, worker ownership, gates, proof and Hermes-native runtime authority to move the next gear without operator babysitting or shallow agent output.

## Hermes-Native Runtime Rule

- Use Hermes Kanban cards, parent dependencies, typed blocks, dispatch, comments, runs, logs and attachments whenever those primitives exist.
- Factory code may validate contracts, route gates and produce proof requirements. It must not become a shadow dispatcher, shadow scheduler or mini-Hermes.
- `dependency`, `needs_input`, `capability` and `transient` typed block semantics come from Hermes. Factory no-idle/watchdog logic audits and repairs; it does not own normal route authority.

## Phase Gear Baseline

### F0: Pre-Start / Sealed Source Envelope

- Next gear: `F1`
- Auto-pass allowed: `false`
- Required artifacts:
  - `factory_bridge_source_envelope`
  - `factory_bridge_start_request`
- Required gates:
  - `Start Boundary`
- Workflow-required workers:
  - `overkill-factory-gerente`
  - `factory-orchestrator`
- Registry workers with this phase:
  - `factory-orchestrator` -> `orchestration_result`
  - `source-ledger-worker` -> `source_ledger_result`
  - `memory-steward` -> `memory_steward_result`
- Blocked actions:
  - `summarize or reinterpret source material in the bridge`
  - `create Hermes board/card directly from bridge`
  - `start without explicit runtime target policy`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F1: Intake

- Next gear: `F2`
- Auto-pass allowed: `false`
- Required artifacts:
  - `operator_interface_profile`
  - `factory_start_conversation`
  - `universal_signal_intake`
  - `source_refs`
  - `source_resolution_packet`
- Required gates:
  - `Source Gate`
- Workflow-required workers:
  - `factory-orchestrator`
- Registry workers with this phase:
  - `factory-orchestrator` -> `orchestration_result`
  - `source-ledger-worker` -> `source_ledger_result`
  - `agentic-ai-security-specialist` -> `agentic_ai_security_result`
  - `memory-steward` -> `memory_steward_result`
- Blocked actions:
  - `route implementation before source resolution`
  - `create Product SOT from raw input`
  - `require the operator to poll for status`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F2: Source Ledger

- Next gear: `F3`
- Auto-pass allowed: `false`
- Required artifacts:
  - `source_refs`
  - `product_source_ledger`
  - `operator_understanding_confirmation`
- Required gates:
  - `Source Gate`
- Workflow-required workers:
  - `source-ledger-worker`
- Registry workers with this phase:
  - `source-ledger-worker` -> `source_ledger_result`
  - `product-sot-planner` -> `product_sot_result`
- Blocked actions:
  - `ask user to reconcile internal source bookkeeping`
  - `create outcome contract or Product SOT before understanding is confirmed`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F3: Source Resolution

- Next gear: `F4`
- Auto-pass allowed: `false`
- Required artifacts:
  - `discovery_brief`
- Required gates:
  - `Discovery Gate`
- Workflow-required workers:
  - `source-ledger-worker`
  - `product-sot-planner`
- Registry workers with this phase:
  - `source-ledger-worker` -> `source_ledger_result`
  - `product-sot-planner` -> `product_sot_result`
- Blocked actions:
  - `turn unresolved gaps into execution scope`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F4: Product Outcome And Discovery

- Next gear: `F5`
- Auto-pass allowed: `false`
- Required artifacts:
  - `operator_understanding_confirmation`
  - `operator_briefing_package`
  - `outcome_contract`
  - `discovery_brief`
- Required gates:
  - `Outcome Gate`
  - `Discovery Gate`
- Workflow-required workers:
  - `product-sot-planner`
- Registry workers with this phase:
  - `product-sot-planner` -> `product_sot_result`
  - `product-architect` -> `architecture_result`
  - `security-orchestrator` -> `security_orchestration_result`
  - `detection-monitoring-worker` -> `detection_monitoring_result`
- Blocked actions:
  - `treat outcome candidate as approved Product SOT`
  - `draft Product SOT before operator understanding confirmation`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F5: Product SOT

- Next gear: `F6`
- Auto-pass allowed: `false`
- Required artifacts:
  - `product_sot`
  - `operator_briefing_package`
  - `full_product_sot_scope_coverage`
  - `factory_phase_lock`
- Required gates:
  - `Product SOT Gate`
- Workflow-required workers:
  - `product-sot-planner`
- Registry workers with this phase:
  - `product-sot-planner` -> `product_sot_result`
  - `product-face` -> `product_face_result`
- Blocked actions:
  - `execute from paper instead of Product SOT`
  - `ask operator to approve Product SOT from a short chat summary only`
  - `start architecture, repo cleanup, human gate or worker packet while Product SOT owner package is missing`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F6: Agentic Method Router

- Next gear: `F7`
- Auto-pass allowed: `false`
- Required artifacts:
  - `factory_phase_lock`
  - `method_contract`
- Required gates:
  - `Method Gate`
- Workflow-required workers:
  - `factory-orchestrator`
- Registry workers with this phase:
  - `factory-orchestrator` -> `orchestration_result`
  - `product-architect` -> `architecture_result`
  - `security-orchestrator` -> `security_orchestration_result`
- Blocked actions:
  - `ask user to choose internal method machinery`
  - `start architecture or repo cleanup before Method Contract`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F7: Method Contract

- Next gear: `F8`
- Auto-pass allowed: `false`
- Required artifacts:
  - `factory_phase_lock`
  - `method_contract`
- Required gates:
  - `Method Gate`
- Workflow-required workers:
  - `factory-orchestrator`
- Registry workers with this phase:
  - `factory-orchestrator` -> `orchestration_result`
  - `solana-quasar-auditor` -> `auditor_result`
  - `appsec-owasp-specialist` -> `appsec_owasp_result`
  - `agentic-ai-security-specialist` -> `agentic_ai_security_result`
  - `security-orchestrator` -> `security_orchestration_result`
  - `cloud-infra-security-specialist` -> `cloud_infra_security_result`
  - `crypto-key-management-specialist` -> `crypto_key_management_result`
- Blocked actions:
  - `start implementation with undocumented process choices`
  - `materialize future-phase cards while active frontier is still product_sot or method_contract`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F8: Pack And Product Experience Selection

- Next gear: `F9`
- Auto-pass allowed: `false`
- Required artifacts:
  - `capability_pack_contract`
  - `product_experience_plan`
  - `product_face_packet`
  - `project_design_system`
  - `professional_design_process`
  - `surface_evidence_profile`
  - `product_delivery_quality_profile`
- Required gates:
  - `Pack Gate`
  - `Product Experience Gate`
  - `Surface Pack Gate`
- Workflow-required workers:
  - `product-face`
  - `factory-orchestrator`
- Registry workers with this phase:
  - `factory-orchestrator` -> `orchestration_result`
  - `product-face` -> `product_face_result`
  - `codex-security` -> `security_scan_result`
  - `security-orchestrator` -> `security_orchestration_result`
  - `skill-eval-distiller` -> `skill_eval_result`
- Blocked actions:
  - `activate a pack without proof or coverage`
  - `start product-facing implementation before surface state coverage`
  - `treat generic UI proof as Product Experience proof`
  - `move to implementation with unnamed surface pack or proof profile`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F9: Risk And Authority Gates

- Next gear: `F10`
- Auto-pass allowed: `false`
- Required artifacts:
  - `access_capability`
  - `budget_contract`
- Required gates:
  - `Access Gate`
  - `Budget Gate`
  - `Human Gate when required`
- Workflow-required workers:
  - `human-gate-clerk`
- Registry workers with this phase:
  - `factory-orchestrator` -> `orchestration_result`
  - `handoff-packer` -> `handoff_packet_result`
  - `human-gate-clerk` -> `human_gate_record`
- Blocked actions:
  - `infer approval from silence`
  - `ask for planning-only continuation approval`
  - `ask for architecture or repo cleanup approval while downstream is frozen`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F10: Security Architecture

- Next gear: `F11`
- Auto-pass allowed: `false`
- Required artifacts:
  - `factory_phase_lock`
  - `security_architecture_plan`
- Required gates:
  - `Security Architecture Gate`
- Workflow-required workers:
  - `security-orchestrator`
- Registry workers with this phase:
  - `docs-os-worker` -> `documentation_os_result`
  - `security-orchestrator` -> `security_orchestration_result`
- Blocked actions:
  - `build material risk before architecture`
  - `start security architecture while Product SOT or Method Contract is still missing`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F11: Executable Plans

- Next gear: `F12`
- Auto-pass allowed: `false`
- Required artifacts:
  - `software_development_plan`
  - `spec_graph`
  - `loop_plan`
  - `product_creation_plan`
- Required gates:
  - `Ready Gate`
- Workflow-required workers:
  - `decomposition-planner`
- Registry workers with this phase:
  - `factory-orchestrator` -> `orchestration_result`
  - `decomposition-planner` -> `decomposition_result`
  - `supply-chain-gate` -> `supply_chain_result`
- Blocked actions:
  - `execute before plans, coverage review and stop criteria exist`
  - `mark decomposition review as passed from the planner that created the decomposition`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F12: Autonomy Readiness

- Next gear: `F13`
- Auto-pass allowed: `false`
- Required artifacts:
  - `decomposition_coverage_review`
  - `product_implementation_readiness`
  - `autonomy_readiness_packet`
- Required gates:
  - `Decomposition Coverage Gate`
  - `Access & Capability Gate`
- Workflow-required workers:
  - `independent-reviewer`
  - `factory-orchestrator`
- Registry workers with this phase:
  - `factory-orchestrator` -> `orchestration_result`
  - `agentic-ai-security-specialist` -> `agentic_ai_security_result`
  - `independent-reviewer` -> `independent_review_result`
  - `implementation-worker` -> `implementation_result`
  - `frontend-builder` -> `frontend_build_result`
  - `backend-api-builder` -> `backend_api_build_result`
  - `data-persistence-builder` -> `data_persistence_result`
  - `solana-quasar-builder` -> `solana_quasar_build_result`
  - `wallet-transaction-builder` -> `wallet_transaction_result`
  - `integration-builder` -> `integration_build_result`
  - `test-automation-builder` -> `test_automation_result`
  - `infra-devops-builder` -> `infra_devops_result`
  - ... 1 more
- Blocked actions:
  - `start autonomous work with missing review, access or limits`
  - `let a single reviewer approve the complete decomposition alone`
  - `create Product Implementation Readiness from a failed or missing decomposition coverage review`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F13: Ready Gate

- Next gear: `F15`
- Auto-pass allowed: `false`
- Required artifacts:
  - `gate_report`
- Required gates:
  - `Ready Gate`
- Workflow-required workers:
  - `factory-orchestrator`
- Registry workers with this phase:
  - `factory-orchestrator` -> `orchestration_result`
  - `product-face` -> `product_face_result`
  - `solana-quasar-auditor` -> `auditor_result`
  - `codex-security` -> `security_scan_result`
  - `remote-proof-runner` -> `remote_proof_result`
  - `evidence-reconciler` -> `receipt_five_reconciliation_result`
  - `frontend-builder` -> `frontend_build_result`
  - `backend-api-builder` -> `backend_api_build_result`
  - `data-persistence-builder` -> `data_persistence_result`
  - `solana-quasar-builder` -> `solana_quasar_build_result`
  - `solana-quasar-qa-engineer` -> `solana_quasar_qa_result`
  - `wallet-transaction-builder` -> `wallet_transaction_result`
  - ... 5 more
- Blocked actions:
  - `dispatch blocked workers`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F15: Runtime Execution

- Next gear: `F16`
- Auto-pass allowed: `false`
- Required artifacts:
  - `worker_packets`
- Required gates:
  - `Runtime Gate`
- Workflow-required workers:
  - `implementation-worker`
  - `qa-verification-worker`
- Registry workers with this phase:
  - `factory-orchestrator` -> `orchestration_result`
  - `solana-quasar-auditor` -> `auditor_result`
  - `appsec-owasp-specialist` -> `appsec_owasp_result`
  - `autoreview-gate` -> `autoreview_result`
  - `handoff-packer` -> `handoff_packet_result`
  - `evidence-reconciler` -> `receipt_five_reconciliation_result`
  - `human-gate-clerk` -> `human_gate_record`
  - `implementation-worker` -> `implementation_result`
  - `solana-quasar-qa-engineer` -> `solana_quasar_qa_result`
  - `qa-verification-worker` -> `qa_verification_result`
- Blocked actions:
  - `spawn without route readiness`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F16: Worker Results

- Next gear: `F17`
- Auto-pass allowed: `false`
- Required artifacts:
  - `worker_results`
- Required gates:
  - `Done Gate`
- Workflow-required workers:
  - `evidence-reconciler`
- Registry workers with this phase:
  - `remote-proof-runner` -> `remote_proof_result`
  - `evidence-reconciler` -> `receipt_five_reconciliation_result`
  - `human-gate-clerk` -> `human_gate_record`
  - `infra-devops-builder` -> `infra_devops_result`
  - `security-orchestrator` -> `security_orchestration_result`
  - `cloud-infra-security-specialist` -> `cloud_infra_security_result`
  - `crypto-key-management-specialist` -> `crypto_key_management_result`
  - `release-ops-worker` -> `release_ops_result`
  - `public-safety-gate` -> `public_safety_result`
  - `supply-chain-gate` -> `supply_chain_result`
  - `detection-monitoring-worker` -> `detection_monitoring_result`
- Blocked actions:
  - `treat packet existence as proof`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F17: Verification

- Next gear: `F18`
- Auto-pass allowed: `false`
- Required artifacts:
  - `verification_plan`
  - `verification_result`
- Required gates:
  - `Verification Gate`
- Workflow-required workers:
  - `qa-verification-worker`
- Registry workers with this phase:
  - `qa-verification-worker` -> `qa_verification_result`
  - `release-ops-worker` -> `release_ops_result`
  - `public-safety-gate` -> `public_safety_result`
  - `detection-monitoring-worker` -> `detection_monitoring_result`
- Blocked actions:
  - `claim done without command evidence`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F18: Independent Review

- Next gear: `F20`
- Auto-pass allowed: `false`
- Required artifacts:
  - `review_result`
- Required gates:
  - `Review Gate`
- Workflow-required workers:
  - `independent-reviewer`
- Registry workers with this phase:
  - `factory-orchestrator` -> `orchestration_result`
  - `appsec-owasp-specialist` -> `appsec_owasp_result`
  - `agentic-ai-security-specialist` -> `agentic_ai_security_result`
  - `autoreview-gate` -> `autoreview_result`
  - `independent-reviewer` -> `independent_review_result`
  - `evidence-reconciler` -> `receipt_five_reconciliation_result`
  - `test-automation-builder` -> `test_automation_result`
  - `agent-runtime-builder` -> `agent_runtime_result`
  - `memory-steward` -> `memory_steward_result`
  - `skill-eval-distiller` -> `skill_eval_result`
- Blocked actions:
  - `allow executor to self-approve`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F20: Closure Summary

- Next gear: `F21`
- Auto-pass allowed: `false`
- Required artifacts:
  - `closure_summary`
- Required gates:
  - `Closure Gate`
- Workflow-required workers:
  - `handoff-packer`
- Registry workers with this phase:
  - `handoff-packer` -> `handoff_packet_result`
- Blocked actions:
  - `hide unresolved blockers in prose`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F21: Receipt Five

- Next gear: `F22`
- Auto-pass allowed: `false`
- Required artifacts:
  - `receipt_five`
- Required gates:
  - `Done Gate`
- Workflow-required workers:
  - `evidence-reconciler`
- Registry workers with this phase:
  - `evidence-reconciler` -> `receipt_five_reconciliation_result`
- Blocked actions:
  - `mark done without Receipt Five`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F22: Completion Audit

- Next gear: `F23`
- Auto-pass allowed: `false`
- Required artifacts:
  - `completion_audit`
- Required gates:
  - `Completion Audit`
- Workflow-required workers:
  - `evidence-reconciler`
- Registry workers with this phase:
  - `evidence-reconciler` -> `receipt_five_reconciliation_result`
- Blocked actions:
  - `close skipped method or evidence requirements`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F23: Production Operations

- Next gear: `F24`
- Auto-pass allowed: `false`
- Required artifacts:
  - `production_readiness_plan`
- Required gates:
  - `Release Gate`
- Workflow-required workers:
  - `release-ops-worker`
- Registry workers with this phase:
  - `release-ops-worker` -> `release_ops_result`
- Blocked actions:
  - `release without owner, rollback or approval`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F24: Release Or Block

- Next gear: `F25`
- Auto-pass allowed: `false`
- Required artifacts:
  - `release_decision`
- Required gates:
  - `Release Gate`
  - `Human Gate when required`
- Workflow-required workers:
  - `release-ops-worker`
  - `human-gate-clerk`
- Registry workers with this phase:
  - `human-gate-clerk` -> `human_gate_record`
  - `release-ops-worker` -> `release_ops_result`
  - `discord-control-tower-bridge` -> `control_tower_bridge_result`
- Blocked actions:
  - `promote without production-strict evidence`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F25: Monitoring Support

- Next gear: `F26`
- Auto-pass allowed: `false`
- Required artifacts:
  - `incident_support_plan`
- Required gates:
  - `Support Gate`
- Workflow-required workers:
  - `release-ops-worker`
- Registry workers with this phase:
  - `release-ops-worker` -> `release_ops_result`
- Blocked actions:
  - `ship without support owner when support is material`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F26: Learnback

- Next gear: `F27`
- Auto-pass allowed: `false`
- Required artifacts:
  - `factory_learning_proposal`
- Required gates:
  - `Learning Gate`
- Workflow-required workers:
  - `skill-eval-distiller`
- Registry workers with this phase:
  - `skill-eval-distiller` -> `skill_eval_result`
- Blocked actions:
  - `auto-activate critical factory changes`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

### F27: Factory Maturity Audit

- Next gear: `terminal`
- Auto-pass allowed: `false`
- Required artifacts:
  - `factory_maturity_scorecard`
- Required gates:
  - `Maturity Gate`
- Workflow-required workers:
  - `skill-eval-distiller`
- Registry workers with this phase:
  - `skill-eval-distiller` -> `skill_eval_result`
- Blocked actions:
  - `commit raw study or private evidence`
- Swiss Watch audit questions:
  - Does Hermes native state already expose the current status/dependency for this gear?
  - Is the next action derived from compiled workflow/phase graph/reducer state, not agent prose?
  - Would an internal dependency/capability/transient block avoid paging the operator?
  - Does every required worker output have product-specific evidence and a quality floor?
  - Does the operator receive a clear package before any real human decision?

## Typed Block Gear Baseline

| Hermes typed block | Owner | Operator page? | Required behavior |
| --- | --- | --- | --- |
| `dependency` | Hermes Kanban dependency lane | No | Native wait in TODO; auto-resume from parent completion. |
| `needs_input` | Operator delivery/human gate lane | Only after complete delivery package | Ask the operator only for real input/decision with material first. |
| `capability` | Capability acquisition lane | No until search is complete and blocked | Search providers/packs/references, write receipt, then block if no safe candidate. |
| `transient` | Runtime repair/retry lane | No | Retry or route repair; never become generic human approval. |

## Immediate Gap Inventory Seeds

- Add operator-experience regressions for every typed block and gate false-positive class.
- Add worker quality-floor regressions for shallow Product SOT, shallow architecture, shallow Product Face proof, shallow review and weak Receipt Five.
- Add no-idle regressions for terminal worker metadata, repaired review, duplicate remediation prevention and graph invariant violations.
- Audit every scheduling/dispatch/reconcile path for Hermes-native replacement opportunities before adding factory-native runtime code.

