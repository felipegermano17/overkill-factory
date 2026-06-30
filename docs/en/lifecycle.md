# Factory lifecycle

The compiled workflow is the factual source for this page. It currently contains `26` compiled phases from `docs/factory-workflow.catalog.json`.

You can regenerate or inspect the plan from the implementation side:

```bash
cd factory
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
```

Read the lifecycle as a production path, not as a rigid waterfall. Hermes runtime state, dependencies, blockers, risk, and evidence decide what can move. The phase list tells you what the factory is protecting at each step.

### F0 — Pre-Start / Sealed Source Envelope

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Pre-Start / Sealed Source Envelope`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `factory_bridge_source_envelope`, `factory_bridge_start_request`. The gate holding the line is: Start Boundary. The workers normally involved are: `overkill-factory-gerente`, `factory-orchestrator`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F1 — Intake

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Intake`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `operator_interface_profile`, `factory_start_conversation`, `universal_signal_intake`, `source_refs`, `source_resolution_packet`. The gate holding the line is: Source Gate. The workers normally involved are: `factory-orchestrator`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F2 — Source Ledger

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Source Ledger`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `source_refs`, `product_source_ledger`, `operator_understanding_confirmation`. The gate holding the line is: Source Gate. The workers normally involved are: `source-ledger-worker`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F3 — Source Resolution

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Source Resolution`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `discovery_brief`. The gate holding the line is: Discovery Gate. The workers normally involved are: `source-ledger-worker`, `product-sot-planner`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F4 — Product Outcome And Discovery

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Product Outcome And Discovery`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `operator_understanding_confirmation`, `operator_briefing_package`, `outcome_contract`, `discovery_brief`. The gate holding the line is: Outcome Gate, Discovery Gate. The workers normally involved are: `product-sot-planner`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F5 — Product SOT

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Product SOT`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `product_sot`, `operator_briefing_package`, `full_product_sot_scope_coverage`, `factory_phase_lock`. The gate holding the line is: Product SOT Gate. The workers normally involved are: `product-sot-planner`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F6 — Agentic Method Router

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Agentic Method Router`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `factory_phase_lock`, `method_contract`. The gate holding the line is: Method Gate. The workers normally involved are: `factory-orchestrator`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F7 — Method Contract

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Method Contract`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `factory_phase_lock`, `method_contract`. The gate holding the line is: Method Gate. The workers normally involved are: `factory-orchestrator`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F8 — Pack And Product Experience Selection

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Pack And Product Experience Selection`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `capability_pack_contract`, `product_experience_plan`, `product_face_packet`, `project_design_system`, `professional_design_process`, `surface_evidence_profile`, `product_delivery_quality_profile`. The gate holding the line is: Pack Gate, Product Experience Gate, Surface Pack Gate. The workers normally involved are: `product-face`, `factory-orchestrator`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F9 — Risk And Authority Gates

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Risk And Authority Gates`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `access_capability`, `budget_contract`. The gate holding the line is: Access Gate, Budget Gate, Human Gate when required. The workers normally involved are: `human-gate-clerk`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F10 — Security Architecture

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Security Architecture`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `factory_phase_lock`, `security_architecture_plan`. The gate holding the line is: Security Architecture Gate. The workers normally involved are: `security-orchestrator`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F11 — Executable Plans

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Executable Plans`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `software_development_plan`, `spec_graph`, `loop_plan`, `product_creation_plan`. The gate holding the line is: Ready Gate. The workers normally involved are: `decomposition-planner`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F12 — Autonomy Readiness

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Autonomy Readiness`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `decomposition_coverage_review`, `product_implementation_readiness`, `autonomy_readiness_packet`. The gate holding the line is: Decomposition Coverage Gate, Access & Capability Gate. The workers normally involved are: `independent-reviewer`, `factory-orchestrator`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F13 — Ready Gate

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Ready Gate`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `gate_report`. The gate holding the line is: Ready Gate. The workers normally involved are: `factory-orchestrator`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F15 — Runtime Execution

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Runtime Execution`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `worker_packets`. The gate holding the line is: Runtime Gate. The workers normally involved are: `implementation-worker`, `qa-verification-worker`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F16 — Worker Results

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Worker Results`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `worker_results`. The gate holding the line is: Done Gate. The workers normally involved are: `evidence-reconciler`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F17 — Verification

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Verification`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `verification_plan`, `verification_result`. The gate holding the line is: Verification Gate. The workers normally involved are: `qa-verification-worker`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F18 — Independent Review

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Independent Review`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `review_result`. The gate holding the line is: Review Gate. The workers normally involved are: `independent-reviewer`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F20 — Closure Summary

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Closure Summary`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `closure_summary`. The gate holding the line is: Closure Gate. The workers normally involved are: `handoff-packer`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F21 — Receipt Five

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Receipt Five`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `receipt_five`. The gate holding the line is: Done Gate. The workers normally involved are: `evidence-reconciler`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F22 — Completion Audit

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Completion Audit`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `completion_audit`. The gate holding the line is: Completion Audit. The workers normally involved are: `evidence-reconciler`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F23 — Production Operations

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Production Operations`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `production_readiness_plan`. The gate holding the line is: Release Gate. The workers normally involved are: `release-ops-worker`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F24 — Release Or Block

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Release Or Block`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `release_decision`. The gate holding the line is: Release Gate, Human Gate when required. The workers normally involved are: `release-ops-worker`, `human-gate-clerk`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F25 — Monitoring Support

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Monitoring Support`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `incident_support_plan`. The gate holding the line is: Support Gate. The workers normally involved are: `release-ops-worker`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F26 — Learnback

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Learnback`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `factory_learning_proposal`. The gate holding the line is: Learning Gate. The workers normally involved are: `skill-eval-distiller`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.

### F27 — Factory Maturity Audit

This phase answers a plain question: "do we have enough ground to move forward without inventing the missing pieces?" The internal name is `Factory Maturity Audit`, but its practical job is to protect the next step. If the phase skips evidence, the rest of the run can look orderly while being weak in reality.

What must exist before the run moves on: `factory_maturity_scorecard`. The gate holding the line is: Maturity Gate. The workers normally involved are: `skill-eval-distiller`.

The common failure is rushing. The factory blocks shortcuts such as: none listed. That is not ceremony. It is the difference between autonomous work and autonomous theater.

The operator should not need to read every JSON field in this phase. They should see the state in plain language: what is understood, what is missing, who owns the next step, and what evidence will unlock the phase. If the answer is "we do not know yet", the factory should say that early, open the right blocker, and propose the smallest safe next step.
