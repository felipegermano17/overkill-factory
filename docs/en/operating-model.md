# Operating Model

This page describes the factory as it operates, not as an internal folder tree.

The simple mental model is: the factory receives a signal, protects the truth, chooses a safe route, creates bounded work, executes through Hermes, verifies evidence, and either releases, blocks, or learns.

## 1. A signal enters

A signal can be a product paper, bug report, feature idea, incident, repository, release request, UX request, integration, migration, security issue, analytics request, or agent/runtime change.

The route registry currently exposes these route classes:

- `product_creation`: request types product_new; method family `spec_first`; gates Source Gate, Product SOT Gate, Ready Gate.
- `feature_delivery`: request types feature, slice; method family `behavior_first`; gates Source Gate, Method Gate, Ready Gate.
- `bug_repair`: request types bug; method family `test_first`; gates Reproduction Gate, Regression Gate, Receipt Gate.
- `incident_response`: request types incident; method family `incident_first`; gates Severity Gate, Mitigation Gate, Learnback Gate.
- `brownfield_discovery`: request types migration, refactor, integration; method family `legacy_diagnosis`; gates Brownfield Baseline Gate, Regression Gate, Rollback Gate.
- `release_promotion`: request types release; method family `spec_first`; gates Production Readiness Gate, Rollback Gate, Release Gate.
- `research_validation`: request types feature, product_new, security, ux_ui, data_analytics, agent_skill; method family `research_first`; gates Source Quality Gate, Specialist Decision Gate, SOT Impact Gate.
- `docs_onboarding`: request types doc; method family `docs_first`; gates Docs Utility Gate, First Run Gate.
- `security_remediation`: request types security; method family `security_first`; gates Security Architecture Gate, Security Review Gate.
- `critical_integration`: request types integration; method family `spec_first`; gates Dependency Gate, Contract Test Gate, Fallback Gate.
- `migration_execution`: request types migration; method family `legacy_diagnosis`; gates Migration Plan Gate, Regression Gate, Rollback Gate.
- `ux_product_experience`: request types ux_ui, product_new, feature; method family `design_first`; gates Product Experience Gate, Product Face Gate, Independent Design Review Gate.
- `analytics_data`: request types data_analytics, product_new, feature; method family `analytics_first`; gates Data Contract Gate, Privacy Gate, Metrics Proof Gate.
- `agent_quality_change`: request types agent_skill; method family `agent_eval_first`; gates Agent Eval Gate, Worker Profile Readiness Gate, Learnback Gate.

The route class matters because a bug should not be handled like a greenfield product, and a release should not be handled like discovery. The method and gates change with the route.

## 2. Source comes before interpretation

The factory first captures and resolves source material. It should not turn a long product paper into a shallow summary and call that truth.

The expected sequence is:

- capture the source envelope;
- classify the signal;
- resolve source references;
- build a source ledger;
- identify conflicts or missing material;
- confirm understanding with the operator when product truth matters.

Only after this can the factory create the product definition artifacts that downstream workers depend on.

## 3. Product truth becomes executable scope

The Product SOT is the source-of-truth product definition used by the factory. It is not a casual summary. It is the artifact that downstream method, architecture, planning, decomposition, implementation, and review must trace to.

A product-facing run must also cover the full Product SOT scope. That prevents a first slice from silently becoming the whole product.

## 4. Method is selected by contract

The method engine registry currently contains:

- `spec_first_sdd` — Spec-First SDD Engine: family `spec_first`; used by product_creation, feature_delivery, critical_integration, migration_execution.
- `test_first_tdd` — Test-First TDD Engine: family `test_first`; used by feature_delivery, bug_repair, critical_integration, migration_execution.
- `behavior_first_bdd` — Behavior-First BDD Engine: family `behavior_first`; used by product_creation, feature_delivery, ux_product_experience.
- `discovery_research` — Discovery and Research Engine: family `discovery_first`; used by product_creation, research_validation, brownfield_discovery.
- `security_first_threat_model` — Security-First Threat Model Engine: family `security_first`; used by security_remediation, release_promotion, critical_integration, agent_quality_change.
- `design_first_product_experience` — Design-First Product Experience Engine: family `design_first`; used by ux_product_experience, product_creation, feature_delivery.
- `legacy_diagnosis` — Legacy Diagnosis Engine: family `legacy_diagnosis`; used by brownfield_discovery, migration_execution, bug_repair.
- `incident_first` — Incident-First Engine: family `incident_first`; used by incident_response, bug_repair, security_remediation.

A method label is not enough. The factory must bind the selected route to artifacts, gates, workers, and proof requirements. For example, test-first work needs test proof. Design-first work needs Product Experience proof. Security-first work needs threat modeling and security evidence.

## 5. Planning creates bounded execution

The Product Creation Plan and work units convert product truth into executable packets. A worker packet should tell a specialist what to do, what not to do, what evidence to return, and what authority it has.

This is where the factory avoids the classic failure: "agent, please build everything." The worker receives a bounded job instead of a vague mission.

## 6. Hermes executes the runtime work

Hermes Kanban remains the runtime source of truth. Cards, dependencies, worker status, comments, workspaces, and transitions live there.

The factory can validate contracts and prepare packets, but execution authority comes from the runtime state. If the runtime says a card is blocked, the factory must respect that and either repair the blocker or deliver the correct human gate.

## 7. Review is separate from execution

A worker's `done` event is not automatically proof. The factory expects readback, verification, and independent review where required.

Executor and reviewer should be separate identities for material work. Review can pass, fail, or create repair work. A review that passes but is not reduced back into the original task is still an orchestration problem.

## Operator bridge modes

The public operator bridge is an interface layer. It can translate operator messages into factory-safe records, but it must not execute factory work by itself. Runtime work still belongs to Hermes cards and assigned workers.

The bridge modes are `status_bridge`, `start_bridge`, `question_bridge`, `decision_bridge`, `change_bridge`, `exception_bridge`, `handoff_bridge`, and `learnback_forwarding`. A start request creates or forwards `factory_bridge_start_request` context; it does not bypass source, method, or readiness gates.

The bridge separates `overkill-factory-gerente` as the operator-facing concierge from `factory-orchestrator` as the factory routing/runtime-control role. Durable Operator Inbox records preserve decisions, questions, and handoffs in the default Hermes store. Factory Mechanic remains the self-improvement owner for learnback and factory changes. The bridge cannot grant authority, invent approvals, close gates, or claim runtime completion without evidence.

## 8. Human gates are explicit

A human gate is not an excuse to stop. It is a real decision package. The operator should receive the artifact, the decision needed, the risks, the evidence, and the recommended choices.

Internal review-required blockers are factory-owned unless they require explicit operator authority.

## 9. Receipt Five closes the loop

Receipt Five is the evidence package for completion or blocking. It should answer:

- what was requested;
- what was built or decided;
- what evidence proves it;
- what was reviewed;
- what remains blocked or risky;
- what the next operational state is.

Without that package, "done" is not a factory-grade claim.

## 10. Learnback improves the factory

A finished run can expose better methods, missing skills, weak validators, or new failure patterns. Learnback turns those into reviewable improvements instead of silently changing the factory.
