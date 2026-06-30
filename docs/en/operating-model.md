# Operating model

This page explains what happens during a factory run. It avoids the internal folder tour and follows the life of a request instead.

A request starts as a signal. It may be a product idea, a bug, a release, an incident, a security change, a UX request, a data request, an integration, or a worker improvement. The factory's first job is not to build. Its first job is to understand what kind of work it is and what would make progress safe.

## 1. Intake protects the source

The factory receives source material and turns it into a source envelope. That envelope should preserve what the operator actually provided. It should not silently compress the request into a convenient summary.

Then the source ledger records what is known, what is missing, what conflicts, and what still needs the operator. This sounds basic, but it prevents one of the most expensive agent failures: building from a misunderstood brief.

The operator should see a plain explanation: "this is what we understood, this is what we still need, this is what we cannot assume." If that explanation is not clear, the run is already weak.

## 2. Routing chooses the kind of factory run

The route class decides the shape of the work. A bug repair is not a release. A release is not a greenfield product. A Solana/onchain audit is not a docs update. The factory currently exposes these route classes:

- `product_creation`: used for `product_new` requests. Method family `None`; main gates: Source Gate, Product SOT Gate, Ready Gate.
- `feature_delivery`: used for `feature, slice` requests. Method family `None`; main gates: Source Gate, Method Gate, Ready Gate.
- `bug_repair`: used for `bug` requests. Method family `None`; main gates: Reproduction Gate, Regression Gate, Receipt Gate.
- `incident_response`: used for `incident` requests. Method family `None`; main gates: Severity Gate, Mitigation Gate, Learnback Gate.
- `brownfield_discovery`: used for `migration, refactor, integration` requests. Method family `None`; main gates: Brownfield Baseline Gate, Regression Gate, Rollback Gate.
- `release_promotion`: used for `release` requests. Method family `None`; main gates: Production Readiness Gate, Rollback Gate, Release Gate.
- `research_validation`: used for `feature, product_new, security, ux_ui, data_analytics, agent_skill` requests. Method family `None`; main gates: Source Quality Gate, Specialist Decision Gate, SOT Impact Gate.
- `docs_onboarding`: used for `doc` requests. Method family `None`; main gates: Docs Utility Gate, First Run Gate.
- `security_remediation`: used for `security` requests. Method family `None`; main gates: Security Architecture Gate, Security Review Gate.
- `critical_integration`: used for `integration` requests. Method family `None`; main gates: Dependency Gate, Contract Test Gate, Fallback Gate.
- `migration_execution`: used for `migration` requests. Method family `None`; main gates: Migration Plan Gate, Regression Gate, Rollback Gate.
- `ux_product_experience`: used for `ux_ui, product_new, feature` requests. Method family `None`; main gates: Product Experience Gate, Product Face Gate, Independent Design Review Gate.
- `analytics_data`: used for `data_analytics, product_new, feature` requests. Method family `None`; main gates: Data Contract Gate, Privacy Gate, Metrics Proof Gate.
- `agent_quality_change`: used for `agent_skill` requests. Method family `None`; main gates: Agent Eval Gate, Worker Profile Readiness Gate, Learnback Gate.

The route does not give a worker permission to do anything by itself. It selects the lane, the method family, and the gates that must be satisfied.

## 3. Product truth becomes the contract

For product work, the Product SOT turns source material into a usable product definition. This is the point where the factory says: "this is the product we are actually building".

A weak Product SOT makes every downstream step weaker. Workers can still produce code, docs, designs, or review comments, but they may be optimizing for the wrong thing. That is why the factory blocks downstream execution when product truth is missing or unreviewed.

## 4. Method binds the route to evidence

The method contract says how this run should be handled. The method engines currently include:

- `spec_first_sdd`: None. Used when the route needs `spec_first`. Routes: .
- `test_first_tdd`: None. Used when the route needs `test_first`. Routes: .
- `behavior_first_bdd`: None. Used when the route needs `behavior_first`. Routes: .
- `discovery_research`: None. Used when the route needs `discovery_first`. Routes: .
- `security_first_threat_model`: None. Used when the route needs `security_first`. Routes: .
- `design_first_product_experience`: None. Used when the route needs `design_first`. Routes: .
- `legacy_diagnosis`: None. Used when the route needs `legacy_diagnosis`. Routes: .
- `incident_first`: None. Used when the route needs `incident_first`. Routes: .

The method matters because it changes the evidence. Test-first work needs tests and regression proof. Design-first work needs product experience proof. Security-first work needs threat modeling and security evidence. Incident-first work needs mitigation, status, and learnback.

A method is not a slogan. It should produce artifacts, gates, worker packets, and stop conditions.

## 5. Work is broken into packets

A worker packet is a small contract. It tells the worker what to do, what not to do, what evidence to attach, and what authority it has. This is where the factory avoids the vague instruction "build the thing".

Good packets are narrow. They can be executed, reviewed, retried, and closed. Bad packets are broad missions with no clear proof. The factory should create the former and block the latter.

## 6. Hermes runs the floor

Hermes Kanban remains the runtime source of truth. Cards, dependencies, comments, worker status, workspaces, and transitions live there. The factory prepares and validates production contracts; Hermes records what is actually happening.

This split is important. Local files can prove that the public kernel is coherent. They cannot prove that a live operator-owned Hermes run completed. Live completion needs runtime state, worker results, review, evidence, and human decisions when required.

## Operator bridge modes

The public operator bridge is an interface layer. It can translate operator messages into factory-safe records, but it must not execute factory work by itself. Runtime work still belongs to Hermes cards and assigned workers.

The bridge modes are `status_bridge`, `start_bridge`, `question_bridge`, `decision_bridge`, `change_bridge`, `exception_bridge`, `handoff_bridge`, and `learnback_forwarding`. A start request creates or forwards `factory_bridge_start_request` context; it does not bypass source, method, or readiness gates.

The bridge separates `overkill-factory-gerente` as the operator-facing concierge from `factory-orchestrator` as the factory routing/runtime-control role. Durable Operator Inbox records preserve decisions, questions, and handoffs in the default Hermes store. Factory Mechanic remains the self-improvement owner for learnback and factory changes. The bridge cannot grant authority, invent approvals, close gates, or claim runtime completion without evidence.

## 7. Review is a different job from execution

The executor should not be the final judge of material work. The factory uses readback, verification, independent review, and Receipt Five to separate "the worker says it is done" from "the factory can prove it is done".

If review passes, the result must be consumed back into the original task. If review fails, the factory should create repair work. A review result that sits unused is not progress. It is another blocked state.

## 8. Human gates are rare but real

A human gate is required when the decision belongs to the operator: risk acceptance, budget, production authority, mainnet, secrets, release, or another explicit ownership boundary. The factory should not ask for human approval just because it is unsure how to continue.

When a human gate is needed, the operator should receive a decision package: the choice, the evidence, the risk, the recommended option, and the consequence of each path. A raw JSON file is not a good human gate. A vague chat question is worse.

## 9. Release, block, or learn

A run ends in one of three honest states.

It can release when the evidence is strong enough and the required gates passed. It can block when proof, access, authority, or safety is missing. Or it can learn when the run exposes a better method, a missing worker, a weak validator, or a repeated failure pattern.

Learning is also gated. The factory should not silently rewrite itself because one run felt awkward. It should propose a change, test it, and promote it only when it is safe.
