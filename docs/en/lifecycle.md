# Factory lifecycle

The compiled workflow is the factual source for this page. It currently contains `26` phases in `docs/factory-workflow.catalog.json`.

Do not read this as a rigid waterfall. It is a map of what the factory protects. Hermes state, dependencies, blockers, risk, and evidence still decide what can move in a live run.

The practical reading is simple: every phase answers a question, requires artifacts, blocks dangerous shortcuts, and gives the operator a clearer next state.

```bash
cd factory
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
```

## F0 — Pre-Start / Sealed Source Envelope

The factory separates conversation from execution. Source enters a sealed envelope before it becomes a card, so the first summary cannot destroy the original intent.

Required artifacts: `factory_bridge_source_envelope`, `factory_bridge_start_request`.

Gates that hold progress: `Start Boundary`.

Workers normally involved: `overkill-factory-gerente`, `factory-orchestrator`.

Shortcuts this phase prevents:

- summarize or reinterpret source material in the bridge.
- create Hermes board/card directly from bridge.
- start without explicit runtime target policy.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F1 — Intake

The request becomes a classified signal. Operator interface, start conversation, and source resolution prevent the factory from starting from a polished guess.

Required artifacts: `operator_interface_profile`, `factory_start_conversation`, `universal_signal_intake`, `source_refs`, `source_resolution_packet`.

Gates that hold progress: `Source Gate`.

Workers normally involved: `factory-orchestrator`.

Shortcuts this phase prevents:

- route implementation before source resolution.
- create Product SOT from raw input.
- require the operator to poll for status.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F2 — Source Ledger

The source ledger records where each claim came from. Fact, inference, decision, conflict, and gap must not collapse into one convenient story.

Required artifacts: `source_refs`, `product_source_ledger`, `operator_understanding_confirmation`.

Gates that hold progress: `Source Gate`.

Workers normally involved: `source-ledger-worker`.

Shortcuts this phase prevents:

- ask user to reconcile internal source bookkeeping.
- create outcome contract or Product SOT before understanding is confirmed.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F3 — Source Resolution

Source becomes operational understanding. If discovery is still missing, the factory blocks instead of letting a worker fill the gap with imagination.

Required artifacts: `discovery_brief`.

Gates that hold progress: `Discovery Gate`.

Workers normally involved: `source-ledger-worker`, `product-sot-planner`.

Shortcuts this phase prevents:

- turn unresolved gaps into execution scope.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F4 — Product Outcome And Discovery

The expected outcome, user, problem, and assumptions become explicit. The operator must be able to correct direction before planning hardens.

Required artifacts: `operator_understanding_confirmation`, `operator_briefing_package`, `outcome_contract`, `discovery_brief`.

Gates that hold progress: `Outcome Gate`, `Discovery Gate`.

Workers normally involved: `product-sot-planner`.

Shortcuts this phase prevents:

- treat outcome candidate as approved Product SOT.
- draft Product SOT before operator understanding confirmation.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F5 — Product SOT

Product SOT becomes product truth. It protects scope, non-scope, acceptance criteria, and complete coverage before material execution.

Required artifacts: `product_sot`, `operator_briefing_package`, `full_product_sot_scope_coverage`, `factory_phase_lock`.

Gates that hold progress: `Product SOT Gate`.

Workers normally involved: `product-sot-planner`.

Shortcuts this phase prevents:

- execute from paper instead of Product SOT.
- ask operator to approve Product SOT from a short chat summary only.
- start architecture, repo cleanup, human gate or worker packet while Product SOT owner package is missing.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F6 — Agentic Method Router

The route chooses the lane: product, bug, release, incident, security, UX, analytics, integration, or agent work. The factory stops treating every request as generic work.

Required artifacts: `factory_phase_lock`, `method_contract`.

Gates that hold progress: `Method Gate`.

Workers normally involved: `factory-orchestrator`.

Shortcuts this phase prevents:

- ask user to choose internal method machinery.
- start architecture or repo cleanup before Method Contract.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F7 — Method Contract

The method records how the work will be done and proven. TDD, security-first, or design-first must change artifacts, gates, and evidence, not just wording.

Required artifacts: `factory_phase_lock`, `method_contract`.

Gates that hold progress: `Method Gate`.

Workers normally involved: `factory-orchestrator`.

Shortcuts this phase prevents:

- start implementation with undocumented process choices.
- materialize future-phase cards while active frontier is still product_sot or method_contract.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F8 — Pack And Product Experience Selection

The factory checks capability packs and surface proof for the product type. Web, CLI, docs, agentic UI, Solana, mobile, and fintech do not need the same proof.

Required artifacts: `capability_pack_contract`, `product_experience_plan`, `product_face_packet`, `project_design_system`, `professional_design_process`, `surface_evidence_profile`, `product_delivery_quality_profile`.

Gates that hold progress: `Pack Gate`, `Product Experience Gate`, `Surface Pack Gate`.

Workers normally involved: `product-face`, `factory-orchestrator`.

Shortcuts this phase prevents:

- activate a pack without proof or coverage.
- start product-facing implementation before surface state coverage.
- treat generic UI proof as Product Experience proof.
- move to implementation with unnamed surface pack or proof profile.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F9 — Risk And Authority Gates

Authority, access, budget, and risk are checked before sensitive execution. If the decision belongs to the operator, the factory prepares a decision package; if it is internal repair, it does not dump the problem on the human.

Required artifacts: `access_capability`, `budget_contract`.

Gates that hold progress: `Access Gate`, `Budget Gate`, `Human Gate when required`.

Workers normally involved: `human-gate-clerk`.

Shortcuts this phase prevents:

- infer approval from silence.
- ask for planning-only continuation approval.
- ask for architecture or repo cleanup approval while downstream is frozen.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F10 — Security Architecture

Security enters as architecture, not as an end scan. Trust boundaries, secrets, keys, supply chain, privacy, onchain, and rollback need to appear early when they matter.

Required artifacts: `factory_phase_lock`, `security_architecture_plan`.

Gates that hold progress: `Security Architecture Gate`.

Workers normally involved: `security-orchestrator`.

Shortcuts this phase prevents:

- build material risk before architecture.
- start security architecture while Product SOT or Method Contract is still missing.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F11 — Executable Plans

Architecture and risk become a development plan. The goal is to move from idea to executable units without losing dependencies or stop criteria.

Required artifacts: `software_development_plan`, `spec_graph`, `loop_plan`, `product_creation_plan`.

Gates that hold progress: `Ready Gate`.

Workers normally involved: `decomposition-planner`.

Shortcuts this phase prevents:

- execute before plans, coverage review and stop criteria exist.
- mark decomposition review as passed from the planner that created the decomposition.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F12 — Autonomy Readiness

The product is decomposed into work units. Each unit needs owner, reviewer, proof, dependency, and done rule; otherwise it becomes loose agent work.

Required artifacts: `decomposition_coverage_review`, `product_implementation_readiness`, `autonomy_readiness_packet`.

Gates that hold progress: `Decomposition Coverage Gate`, `Access & Capability Gate`.

Workers normally involved: `independent-reviewer`, `factory-orchestrator`.

Shortcuts this phase prevents:

- start autonomous work with missing review, access or limits.
- let a single reviewer approve the complete decomposition alone.
- create Product Implementation Readiness from a failed or missing decomposition coverage review.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F13 — Ready Gate

Before work runs, the factory checks implementation readiness: SOT, method, research, architecture, packs, access, workers, and required proof.

Required artifacts: `gate_report`.

Gates that hold progress: `Ready Gate`.

Workers normally involved: `factory-orchestrator`.

Shortcuts this phase prevents:

- dispatch blocked workers.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F15 — Runtime Execution

Workers execute narrow scopes and return structured results. The result must carry evidence, authority boundary, and next state.

Required artifacts: `worker_packets`.

Gates that hold progress: `Runtime Gate`.

Workers normally involved: `implementation-worker`, `qa-verification-worker`.

Shortcuts this phase prevents:

- spawn without route readiness.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F16 — Worker Results

The factory runs objective verification: tests, scans, screenshots, journeys, logs, contracts, or remote proof depending on the work.

Required artifacts: `worker_results`.

Gates that hold progress: `Done Gate`.

Workers normally involved: `evidence-reconciler`.

Shortcuts this phase prevents:

- treat packet existence as proof.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F17 — Verification

Independent review consumes the actual artifact. A pass without readback, same executor/reviewer, or unconsumed finding is false progress.

Required artifacts: `verification_plan`, `verification_result`.

Gates that hold progress: `Verification Gate`.

Workers normally involved: `qa-verification-worker`.

Shortcuts this phase prevents:

- claim done without command evidence.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F18 — Independent Review

Receipt Five reconciles request, change, evidence, review, and remaining work. It is the line between “changed” and “proven”.

Required artifacts: `review_result`.

Gates that hold progress: `Review Gate`.

Workers normally involved: `independent-reviewer`.

Shortcuts this phase prevents:

- allow executor to self-approve.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F20 — Closure Summary

Handoff preserves replayable state for pause, transfer, or recovery. It is not approval; it is honest context and evidence transfer.

Required artifacts: `closure_summary`.

Gates that hold progress: `Closure Gate`.

Workers normally involved: `handoff-packer`.

Shortcuts this phase prevents:

- hide unresolved blockers in prose.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F21 — Receipt Five

Completion audit compares obligations to delivered proof. It closes when they match and blocks when anything material is missing.

Required artifacts: `receipt_five`.

Gates that hold progress: `Done Gate`.

Workers normally involved: `evidence-reconciler`.

Shortcuts this phase prevents:

- mark done without Receipt Five.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F22 — Completion Audit

Production operations check owner, environment, monitoring, rollback, incident route, and release channel. A live product needs operational ground.

Required artifacts: `completion_audit`.

Gates that hold progress: `Completion Audit`.

Workers normally involved: `evidence-reconciler`.

Shortcuts this phase prevents:

- close skipped method or evidence requirements.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F23 — Production Operations

Release only happens with promotion, evidence, and authority. If the proof does not support it, the correct state is blocked.

Required artifacts: `production_readiness_plan`.

Gates that hold progress: `Release Gate`.

Workers normally involved: `release-ops-worker`.

Shortcuts this phase prevents:

- release without owner, rollback or approval.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F24 — Release Or Block

After delivery, monitoring and support keep the product observable. Incidents become routes, not improvisation.

Required artifacts: `release_decision`.

Gates that hold progress: `Release Gate`, `Human Gate when required`.

Workers normally involved: `release-ops-worker`, `human-gate-clerk`.

Shortcuts this phase prevents:

- promote without production-strict evidence.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F25 — Monitoring Support

Learnback turns repeated findings into docs, tests, skills, gates, or issues. The factory learns, but it does not mutate itself silently.

Required artifacts: `incident_support_plan`.

Gates that hold progress: `Support Gate`.

Workers normally involved: `release-ops-worker`.

Shortcuts this phase prevents:

- ship without support owner when support is material.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F26 — Learnback

Maturity audit asks whether the chosen method was good enough. It defends against a factory that follows process while choosing a weak process.

Required artifacts: `factory_learning_proposal`.

Gates that hold progress: `Learning Gate`.

Workers normally involved: `skill-eval-distiller`.

Shortcuts this phase prevents:

- auto-activate critical factory changes.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.

## F27 — Factory Maturity Audit

The final audit looks at the factory itself: coverage, gaps, reliability, operators, workers, and rules that need to evolve.

Required artifacts: `factory_maturity_scorecard`.

Gates that hold progress: `Maturity Gate`.

Workers normally involved: `skill-eval-distiller`.

Shortcuts this phase prevents:

- commit raw study or private evidence.

The operator should not need to read this phase JSON to understand the run. The human projection should say what is clear, what is missing, who owns the next step, and what proof unlocks progress.
