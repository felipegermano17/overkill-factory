# Ciclo da Fábrica

O workflow compilado é a fonte factual desta página.

Plano compilado atual: `26` fases a partir de `docs/factory-workflow.catalog.json`, gerado com:

```bash
cd factory
python3 scripts/factoryctl.py compile-workflow --out .tmp/docs-rewrite-workflow-plan.json
```

A lista de fases é um modelo de ensino e uma superfície de contrato. A execução de runtime ainda é em grafo: dependências, gates, evidência, risco e estado Hermes decidem o que pode andar.

## Referência de fases

### F0 — Pre-Start / Sealed Source Envelope

Objetivo: atravessar **Pre-Start / Sealed Source Envelope** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `factory_bridge_source_envelope`, `factory_bridge_start_request`.

Gates exigidos: Start Boundary.

Workers: `overkill-factory-gerente`, `factory-orchestrator`.

Atalhos bloqueados: summarize or reinterpret source material in the bridge, create Hermes board/card directly from bridge, start without explicit runtime target policy.
### F1 — Intake

Objetivo: atravessar **Intake** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `operator_interface_profile`, `factory_start_conversation`, `universal_signal_intake`, `source_refs`, `source_resolution_packet`.

Gates exigidos: Source Gate.

Workers: `factory-orchestrator`.

Atalhos bloqueados: route implementation before source resolution, create Product SOT from raw input, require the operator to poll for status.
### F2 — Source Ledger

Objetivo: atravessar **Source Ledger** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `source_refs`, `product_source_ledger`, `operator_understanding_confirmation`.

Gates exigidos: Source Gate.

Workers: `source-ledger-worker`.

Atalhos bloqueados: ask user to reconcile internal source bookkeeping, create outcome contract or Product SOT before understanding is confirmed.
### F3 — Source Resolution

Objetivo: atravessar **Source Resolution** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `discovery_brief`.

Gates exigidos: Discovery Gate.

Workers: `source-ledger-worker`, `product-sot-planner`.

Atalhos bloqueados: turn unresolved gaps into execution scope.
### F4 — Product Outcome And Discovery

Objetivo: atravessar **Product Outcome And Discovery** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `operator_understanding_confirmation`, `operator_briefing_package`, `outcome_contract`, `discovery_brief`.

Gates exigidos: Outcome Gate, Discovery Gate.

Workers: `product-sot-planner`.

Atalhos bloqueados: treat outcome candidate as approved Product SOT, draft Product SOT before operator understanding confirmation.
### F5 — Product SOT

Objetivo: atravessar **Product SOT** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `product_sot`, `operator_briefing_package`, `full_product_sot_scope_coverage`, `factory_phase_lock`.

Gates exigidos: Product SOT Gate.

Workers: `product-sot-planner`.

Atalhos bloqueados: execute from paper instead of Product SOT, ask operator to approve Product SOT from a short chat summary only, start architecture, repo cleanup, human gate or worker packet while Product SOT owner package is missing.
### F6 — Agentic Method Router

Objetivo: atravessar **Agentic Method Router** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `factory_phase_lock`, `method_contract`.

Gates exigidos: Method Gate.

Workers: `factory-orchestrator`.

Atalhos bloqueados: ask user to choose internal method machinery, start architecture or repo cleanup before Method Contract.
### F7 — Method Contract

Objetivo: atravessar **Method Contract** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `factory_phase_lock`, `method_contract`.

Gates exigidos: Method Gate.

Workers: `factory-orchestrator`.

Atalhos bloqueados: start implementation with undocumented process choices, materialize future-phase cards while active frontier is still product_sot or method_contract.
### F8 — Pack And Product Experience Selection

Objetivo: atravessar **Pack And Product Experience Selection** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `capability_pack_contract`, `product_experience_plan`, `product_face_packet`, `project_design_system`, `professional_design_process`, `surface_evidence_profile`, `product_delivery_quality_profile`.

Gates exigidos: Pack Gate, Product Experience Gate, Surface Pack Gate.

Workers: `product-face`, `factory-orchestrator`.

Atalhos bloqueados: activate a pack without proof or coverage, start product-facing implementation before surface state coverage, treat generic UI proof as Product Experience proof, move to implementation with unnamed surface pack or proof profile.
### F9 — Risk And Authority Gates

Objetivo: atravessar **Risk And Authority Gates** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `access_capability`, `budget_contract`.

Gates exigidos: Access Gate, Budget Gate, Human Gate when required.

Workers: `human-gate-clerk`.

Atalhos bloqueados: infer approval from silence, ask for planning-only continuation approval, ask for architecture or repo cleanup approval while downstream is frozen.
### F10 — Security Architecture

Objetivo: atravessar **Security Architecture** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `factory_phase_lock`, `security_architecture_plan`.

Gates exigidos: Security Architecture Gate.

Workers: `security-orchestrator`.

Atalhos bloqueados: build material risk before architecture, start security architecture while Product SOT or Method Contract is still missing.
### F11 — Executable Plans

Objetivo: atravessar **Executable Plans** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `software_development_plan`, `spec_graph`, `loop_plan`, `product_creation_plan`.

Gates exigidos: Ready Gate.

Workers: `decomposition-planner`.

Atalhos bloqueados: execute before plans, coverage review and stop criteria exist, mark decomposition review as passed from the planner that created the decomposition.
### F12 — Autonomy Readiness

Objetivo: atravessar **Autonomy Readiness** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `decomposition_coverage_review`, `product_implementation_readiness`, `autonomy_readiness_packet`.

Gates exigidos: Decomposition Coverage Gate, Access & Capability Gate.

Workers: `independent-reviewer`, `factory-orchestrator`.

Atalhos bloqueados: start autonomous work with missing review, access or limits, let a single reviewer approve the complete decomposition alone, create Product Implementation Readiness from a failed or missing decomposition coverage review.
### F13 — Ready Gate

Objetivo: atravessar **Ready Gate** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `gate_report`.

Gates exigidos: Ready Gate.

Workers: `factory-orchestrator`.

Atalhos bloqueados: dispatch blocked workers.
### F15 — Runtime Execution

Objetivo: atravessar **Runtime Execution** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `worker_packets`.

Gates exigidos: Runtime Gate.

Workers: `implementation-worker`, `qa-verification-worker`.

Atalhos bloqueados: spawn without route readiness.
### F16 — Worker Results

Objetivo: atravessar **Worker Results** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `worker_results`.

Gates exigidos: Done Gate.

Workers: `evidence-reconciler`.

Atalhos bloqueados: treat packet existence as proof.
### F17 — Verification

Objetivo: atravessar **Verification** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `verification_plan`, `verification_result`.

Gates exigidos: Verification Gate.

Workers: `qa-verification-worker`.

Atalhos bloqueados: claim done without command evidence.
### F18 — Independent Review

Objetivo: atravessar **Independent Review** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `review_result`.

Gates exigidos: Review Gate.

Workers: `independent-reviewer`.

Atalhos bloqueados: allow executor to self-approve.
### F20 — Closure Summary

Objetivo: atravessar **Closure Summary** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `closure_summary`.

Gates exigidos: Closure Gate.

Workers: `handoff-packer`.

Atalhos bloqueados: hide unresolved blockers in prose.
### F21 — Receipt Five

Objetivo: atravessar **Receipt Five** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `receipt_five`.

Gates exigidos: Done Gate.

Workers: `evidence-reconciler`.

Atalhos bloqueados: mark done without Receipt Five.
### F22 — Completion Audit

Objetivo: atravessar **Completion Audit** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `completion_audit`.

Gates exigidos: Completion Audit.

Workers: `evidence-reconciler`.

Atalhos bloqueados: close skipped method or evidence requirements.
### F23 — Production Operations

Objetivo: atravessar **Production Operations** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `production_readiness_plan`.

Gates exigidos: Release Gate.

Workers: `release-ops-worker`.

Atalhos bloqueados: release without owner, rollback or approval.
### F24 — Release Or Block

Objetivo: atravessar **Release Or Block** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `release_decision`.

Gates exigidos: Release Gate, Human Gate when required.

Workers: `release-ops-worker`, `human-gate-clerk`.

Atalhos bloqueados: promote without production-strict evidence.
### F25 — Monitoring Support

Objetivo: atravessar **Monitoring Support** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `incident_support_plan`.

Gates exigidos: Support Gate.

Workers: `release-ops-worker`.

Atalhos bloqueados: ship without support owner when support is material.
### F26 — Learnback

Objetivo: atravessar **Learnback** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `factory_learning_proposal`.

Gates exigidos: Learning Gate.

Workers: `skill-eval-distiller`.

Atalhos bloqueados: auto-activate critical factory changes.
### F27 — Factory Maturity Audit

Objetivo: atravessar **Factory Maturity Audit** sem permitir que um worker pule o estado da fábrica.

Artefatos exigidos: `factory_maturity_scorecard`.

Gates exigidos: Maturity Gate.

Workers: `skill-eval-distiller`.

Atalhos bloqueados: commit raw study or private evidence.

