# Operating model

This page follows the life of a request inside the factory. The central question is not “which script runs?”, but “how does a request become safe, proven, reviewable work?”.

A request starts as a signal. It may be a product idea, a bug, a release, an incident, a screen, an integration, an audit, an agent change, or an improvement to the factory itself. The wrong answer is to start building. The right answer is to preserve source, understand the work type, choose the method, and only then execute.

## 1. The request enters through the right door

The factory may speak with the operator through Telegram, Discord, a cockpit, CLI, or another channel. The channel is the front desk. It is not the source of truth.

The operator provides material, goal, constraints, and decisions when those decisions truly belong to the operator. The factory should own the rest: source recording, fact/inference separation, Product SOT, routing, worker packets, Hermes state, evidence, review, human gates, and Receipt Five closure.

That removes babysitting from the operator. The human should not have to notice that a worker was shallow, a review was not consumed, a board is idle because of process laziness, or a decision package is missing. When that happens, the factory failed.

## 2. Source is protected before planning

The first important artifact is the source envelope. It preserves what arrived before the factory summarizes, interprets, or decomposes it. Then the source ledger separates five things agents often mix:

- fact from the source;
- reasonable inference;
- decision already made;
- conflict between sources;
- gap that still needs resolution.

This simple separation changes the run. Without it, a short summary becomes “truth” and the product starts crooked.

## 3. The factory works in five layers

The legacy docs had a useful map that is still current. The factory operates in five layers:

1. Truth layer: source, source resolution, Product SOT, decisions, conflicts, and gaps.
2. Method and planning layer: route, method, architecture, Product Creation Plan, Product Experience Plan, data, evals, and loop plan.
3. Risk, authority, access, and cost layer: risk, budget, secrets, production, mainnet, privacy, compliance, and human gates.
4. Execution and evidence layer: Hermes, worker packets, worker results, Product Face, QA, review, remote proof, and Receipt Five.
5. Operations and learning layer: release, monitoring, support, incidents, learnback, and maturity audit.

The point of the map is that “doing the task” is only one part. The factory also needs to know whether the right task was chosen, authority existed, the product was proven, and the factory learned from the run.

## 4. Routing chooses the right weight

Routes are how the factory says: this request is not like the others.

A bug needs reproduction and regression. A new product needs Product SOT and scope coverage. A release needs readiness, rollback, and owner. An incident needs severity, mitigation, and learnback. A critical integration needs contract, fallback, and tests. A security change needs architecture and review. A screen needs Product Face, states, journey, and visual proof.

The factory has fourteen route classes. Exact detail lives in the registries, but the public idea is this: every work type gets different gates and proof. That prevents one generic agent from treating docs, mainnet, UI, release, and incidents as variations of the same task.

## 5. Product SOT is product truth, not a pretty document

Product SOT is the reviewable product definition. It should state what is in scope, what is out, which users matter, which promises must be kept, what risks exist, and what evidence counts as acceptance.

For whole-product work, the factory also needs Full Product SOT Scope Coverage. That prevents the first practical slice from silently becoming the whole product. Every important requirement must be planned, blocked with owner, out of scope with rationale, human-owned, or done with proof.

Without that coverage, workers can do a lot of work and still deliver a product that is too narrow.

## 6. Method connects intent to proof

The Method Contract records how the work will be done. It may choose a spec-first, test-first, behavior-first, discovery-first, security-first, design-first, legacy-diagnosis, or incident-first path.

The point is not the method name. The point is that the method changes evidence:

- test-first needs tests and regression proof;
- design-first needs Product Experience Plan, Product Face Packet, and surface proof;
- security-first needs threat model, trust boundary, scan, and review;
- discovery-first needs uncertainty turned into operational decision;
- legacy-diagnosis needs baseline, rollback, and regression protection;
- incident-first needs mitigation, status, cause, and learnback.

A method that does not change artifact, gate, or proof is just a slogan.



## Operator bridge modes

The public operator bridge is an interface layer. It can translate operator messages into factory-safe records, but it must not execute factory work by itself. Runtime work still belongs to Hermes cards and assigned workers.

The bridge modes are `status_bridge`, `start_bridge`, `question_bridge`, `decision_bridge`, `change_bridge`, `exception_bridge`, `handoff_bridge`, and `learnback_forwarding`. A start request creates or forwards `factory_bridge_start_request` context; it does not bypass source, method, or readiness gates.

The bridge separates `overkill-factory-gerente` as the operator-facing concierge from `factory-orchestrator` as the factory routing/runtime-control role. Durable Operator Inbox records preserve decisions, questions, and handoffs in the default Hermes store. Factory Mechanic remains the self-improvement owner for learnback and factory changes. The bridge cannot grant authority, invent approvals, close gates, or claim runtime completion without evidence.

## 7. Capability packs prevent fake competence

The factory should not pretend one generic agent covers every product. Web SaaS, CLI/TUI, cloud, agent runtime, Solana, native mobile, desktop, games, fintech, analytics, browser extensions, and hardware need different proof.

Capability packs say what is ready and what is still a template. Core packs such as web, CLI/TUI, cloud, agent-runtime, Solana AI Kit, onboarding, and public docs may proceed when route and gates match. Mobile, desktop, game, AI/ML, fintech, regulated domain, analytics, browser extension, and hardware packs need specialists, bindings, smoke, eval, and evidence before material execution.

That is an honesty boundary. Blocking for a missing pack is better than pretending expertise.

## 8. Work becomes small worker packets

A worker packet is a bounded task. It tells the worker what to do, what it receives, what to return, what evidence to attach, and what authority it does not have.

A good packet can be executed, reviewed, and retried. A bad packet says “build the product” and leaves the operator to guess whether it is good.

Important workers cover orchestration, source ledger, Product SOT, architecture, Product Face, builders, QA, security, review, release, handoff, evidence reconciliation, human gates, and skill/eval distillation. The name is not enough. Every worker needs a profile, Hermes binding, receipt field, evidence policy, and authority boundary.

## 9. Hermes is the floor, the factory is the contract

Hermes Kanban remains the runtime source of truth. It stores cards, dependencies, status, workers, workspaces, comments, and transitions. The factory should not create a hidden second runtime.

The factory prepares the contract: missing artifacts, blocking gates, required workers, acceptable evidence, and real human approvals. Hermes records live work.

When the factory creates Hermes tasks, it should use native dependencies. If a phase depends on work units, those work units must be parents of the following phase. If mandatory work is discovered late, it must enter the graph before downstream work moves. Discovering required work after a phase is already done is a graph violation.

## 10. No-idle is not a parallel dispatcher

No-idle exists to detect dangerous silence. If work is running, it observes. If work is ready, Hermes dispatches. If the block is dependency_wait, it waits for the dependency. If the block is needs_input and a decision package exists, the manager calls the operator. If a package, readback, PDF, artifact, or internal repair is missing, the factory repairs instead of dumping the problem on the human.

That rule matters. No-idle must not become mini-Hermes. It is a board-integrity auditor, not the normal source of authority.

## 11. Product Face proves the face of the product

A product with an interface needs product experience proof, not only backend or architecture. Product Face covers web visual UI, CLI/TUI, docs/onboarding, agentic interfaces, wallet UI, and other surface types.

For web, proof may include screenshots, viewports, states, journeys, console, accessibility basics, overflow, and comparison with the Product Face Packet. For CLI/TUI, it needs transcript, help, install, error, and terminal behavior. For docs/onboarding, it needs first-success replay and reader criteria. For agentic interfaces, it needs user control, permissions, recovery, and boundaries.

A screenshot does not prove the whole product. Product Face is one evidence layer, consumed together with SOT, method, QA, review, and Receipt Five.

## 12. Human gates are packages, not loose questions

A human gate enters only when the decision belongs to the operator: production, mainnet, funds, secrets, budget, authority, release, material risk, or explicit waiver.

The gate must be artifact-first. The operator receives the artifact or a faithful projection, a one-screen summary, clear options, consequences, authorized scope, and what approval does not authorize. Raw JSON, local paths, or vague chat questions are not valid human gates.

The human-facing voice is the manager. Worker, cron, Kanban event, and artifact dump may feed internal state, but they should not notify the operator directly.

## 13. Honest closure

A run ends in release, block, or learn.

Release needs current evidence, readback, consumed review, Receipt Five, and satisfied gates. Block needs a clear reason, owner, and smallest safe next action. Learnback needs proposal, test, review, and promotion; the factory should not silently mutate itself because one run felt strange.
