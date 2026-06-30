# Factory Lifecycle

The compiled workflow is the factual source for this page.

Current compiled plan: `26` phases from `docs/factory-workflow.catalog.json`, generated with:

```bash
cd factory
python3 scripts/factoryctl.py compile-workflow --out .tmp/docs-rewrite-workflow-plan.json
```

The phase list is a teaching model and a contract surface. Runtime execution is still graph-shaped: dependencies, gates, evidence, risk, and Hermes state decide what can move.

## Phase reference

### F0 — Pre-Start / Sealed Source Envelope

Purpose: move the run through **Pre-Start / Sealed Source Envelope** without letting a worker skip the factory state.

Required artifacts: `factory_bridge_source_envelope`, `factory_bridge_start_request`.

Required gates: Start Boundary.

Workers: `overkill-factory-gerente`, `factory-orchestrator`.

Blocked shortcuts: summarize or reinterpret source material in the bridge, create Hermes board/card directly from bridge, start without explicit runtime target policy.
### F1 — Intake

Purpose: move the run through **Intake** without letting a worker skip the factory state.

Required artifacts: `operator_interface_profile`, `factory_start_conversation`, `universal_signal_intake`, `source_refs`, `source_resolution_packet`.

Required gates: Source Gate.

Workers: `factory-orchestrator`.

Blocked shortcuts: route implementation before source resolution, create Product SOT from raw input, require the operator to poll for status.
### F2 — Source Ledger

Purpose: move the run through **Source Ledger** without letting a worker skip the factory state.

Required artifacts: `source_refs`, `product_source_ledger`, `operator_understanding_confirmation`.

Required gates: Source Gate.

Workers: `source-ledger-worker`.

Blocked shortcuts: ask user to reconcile internal source bookkeeping, create outcome contract or Product SOT before understanding is confirmed.
### F3 — Source Resolution

Purpose: move the run through **Source Resolution** without letting a worker skip the factory state.

Required artifacts: `discovery_brief`.

Required gates: Discovery Gate.

Workers: `source-ledger-worker`, `product-sot-planner`.

Blocked shortcuts: turn unresolved gaps into execution scope.
### F4 — Product Outcome And Discovery

Purpose: move the run through **Product Outcome And Discovery** without letting a worker skip the factory state.

Required artifacts: `operator_understanding_confirmation`, `operator_briefing_package`, `outcome_contract`, `discovery_brief`.

Required gates: Outcome Gate, Discovery Gate.

Workers: `product-sot-planner`.

Blocked shortcuts: treat outcome candidate as approved Product SOT, draft Product SOT before operator understanding confirmation.
### F5 — Product SOT

Purpose: move the run through **Product SOT** without letting a worker skip the factory state.

Required artifacts: `product_sot`, `operator_briefing_package`, `full_product_sot_scope_coverage`, `factory_phase_lock`.

Required gates: Product SOT Gate.

Workers: `product-sot-planner`.

Blocked shortcuts: execute from paper instead of Product SOT, ask operator to approve Product SOT from a short chat summary only, start architecture, repo cleanup, human gate or worker packet while Product SOT owner package is missing.
### F6 — Agentic Method Router

Purpose: move the run through **Agentic Method Router** without letting a worker skip the factory state.

Required artifacts: `factory_phase_lock`, `method_contract`.

Required gates: Method Gate.

Workers: `factory-orchestrator`.

Blocked shortcuts: ask user to choose internal method machinery, start architecture or repo cleanup before Method Contract.
### F7 — Method Contract

Purpose: move the run through **Method Contract** without letting a worker skip the factory state.

Required artifacts: `factory_phase_lock`, `method_contract`.

Required gates: Method Gate.

Workers: `factory-orchestrator`.

Blocked shortcuts: start implementation with undocumented process choices, materialize future-phase cards while active frontier is still product_sot or method_contract.
### F8 — Pack And Product Experience Selection

Purpose: move the run through **Pack And Product Experience Selection** without letting a worker skip the factory state.

Required artifacts: `capability_pack_contract`, `product_experience_plan`, `product_face_packet`, `project_design_system`, `professional_design_process`, `surface_evidence_profile`, `product_delivery_quality_profile`.

Required gates: Pack Gate, Product Experience Gate, Surface Pack Gate.

Workers: `product-face`, `factory-orchestrator`.

Blocked shortcuts: activate a pack without proof or coverage, start product-facing implementation before surface state coverage, treat generic UI proof as Product Experience proof, move to implementation with unnamed surface pack or proof profile.
### F9 — Risk And Authority Gates

Purpose: move the run through **Risk And Authority Gates** without letting a worker skip the factory state.

Required artifacts: `access_capability`, `budget_contract`.

Required gates: Access Gate, Budget Gate, Human Gate when required.

Workers: `human-gate-clerk`.

Blocked shortcuts: infer approval from silence, ask for planning-only continuation approval, ask for architecture or repo cleanup approval while downstream is frozen.
### F10 — Security Architecture

Purpose: move the run through **Security Architecture** without letting a worker skip the factory state.

Required artifacts: `factory_phase_lock`, `security_architecture_plan`.

Required gates: Security Architecture Gate.

Workers: `security-orchestrator`.

Blocked shortcuts: build material risk before architecture, start security architecture while Product SOT or Method Contract is still missing.
### F11 — Executable Plans

Purpose: move the run through **Executable Plans** without letting a worker skip the factory state.

Required artifacts: `software_development_plan`, `spec_graph`, `loop_plan`, `product_creation_plan`.

Required gates: Ready Gate.

Workers: `decomposition-planner`.

Blocked shortcuts: execute before plans, coverage review and stop criteria exist, mark decomposition review as passed from the planner that created the decomposition.
### F12 — Autonomy Readiness

Purpose: move the run through **Autonomy Readiness** without letting a worker skip the factory state.

Required artifacts: `decomposition_coverage_review`, `product_implementation_readiness`, `autonomy_readiness_packet`.

Required gates: Decomposition Coverage Gate, Access & Capability Gate.

Workers: `independent-reviewer`, `factory-orchestrator`.

Blocked shortcuts: start autonomous work with missing review, access or limits, let a single reviewer approve the complete decomposition alone, create Product Implementation Readiness from a failed or missing decomposition coverage review.
### F13 — Ready Gate

Purpose: move the run through **Ready Gate** without letting a worker skip the factory state.

Required artifacts: `gate_report`.

Required gates: Ready Gate.

Workers: `factory-orchestrator`.

Blocked shortcuts: dispatch blocked workers.
### F15 — Runtime Execution

Purpose: move the run through **Runtime Execution** without letting a worker skip the factory state.

Required artifacts: `worker_packets`.

Required gates: Runtime Gate.

Workers: `implementation-worker`, `qa-verification-worker`.

Blocked shortcuts: spawn without route readiness.
### F16 — Worker Results

Purpose: move the run through **Worker Results** without letting a worker skip the factory state.

Required artifacts: `worker_results`.

Required gates: Done Gate.

Workers: `evidence-reconciler`.

Blocked shortcuts: treat packet existence as proof.
### F17 — Verification

Purpose: move the run through **Verification** without letting a worker skip the factory state.

Required artifacts: `verification_plan`, `verification_result`.

Required gates: Verification Gate.

Workers: `qa-verification-worker`.

Blocked shortcuts: claim done without command evidence.
### F18 — Independent Review

Purpose: move the run through **Independent Review** without letting a worker skip the factory state.

Required artifacts: `review_result`.

Required gates: Review Gate.

Workers: `independent-reviewer`.

Blocked shortcuts: allow executor to self-approve.
### F20 — Closure Summary

Purpose: move the run through **Closure Summary** without letting a worker skip the factory state.

Required artifacts: `closure_summary`.

Required gates: Closure Gate.

Workers: `handoff-packer`.

Blocked shortcuts: hide unresolved blockers in prose.
### F21 — Receipt Five

Purpose: move the run through **Receipt Five** without letting a worker skip the factory state.

Required artifacts: `receipt_five`.

Required gates: Done Gate.

Workers: `evidence-reconciler`.

Blocked shortcuts: mark done without Receipt Five.
### F22 — Completion Audit

Purpose: move the run through **Completion Audit** without letting a worker skip the factory state.

Required artifacts: `completion_audit`.

Required gates: Completion Audit.

Workers: `evidence-reconciler`.

Blocked shortcuts: close skipped method or evidence requirements.
### F23 — Production Operations

Purpose: move the run through **Production Operations** without letting a worker skip the factory state.

Required artifacts: `production_readiness_plan`.

Required gates: Release Gate.

Workers: `release-ops-worker`.

Blocked shortcuts: release without owner, rollback or approval.
### F24 — Release Or Block

Purpose: move the run through **Release Or Block** without letting a worker skip the factory state.

Required artifacts: `release_decision`.

Required gates: Release Gate, Human Gate when required.

Workers: `release-ops-worker`, `human-gate-clerk`.

Blocked shortcuts: promote without production-strict evidence.
### F25 — Monitoring Support

Purpose: move the run through **Monitoring Support** without letting a worker skip the factory state.

Required artifacts: `incident_support_plan`.

Required gates: Support Gate.

Workers: `release-ops-worker`.

Blocked shortcuts: ship without support owner when support is material.
### F26 — Learnback

Purpose: move the run through **Learnback** without letting a worker skip the factory state.

Required artifacts: `factory_learning_proposal`.

Required gates: Learning Gate.

Workers: `skill-eval-distiller`.

Blocked shortcuts: auto-activate critical factory changes.
### F27 — Factory Maturity Audit

Purpose: move the run through **Factory Maturity Audit** without letting a worker skip the factory state.

Required artifacts: `factory_maturity_scorecard`.

Required gates: Maturity Gate.

Workers: `skill-eval-distiller`.

Blocked shortcuts: commit raw study or private evidence.

