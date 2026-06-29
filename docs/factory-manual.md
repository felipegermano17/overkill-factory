# Factory manual

This manual explains Overkill Factory as a product system.

It is written for a person trying to understand what the factory does, why it exists and how it behaves when real work arrives. It intentionally avoids starting with schemas, scripts or internal file names. Those matter, but they are not the first thing a new operator needs.

## 1. The promise

Overkill Factory takes an initial signal and turns it into controlled product work.

The signal can be messy. It can be an idea, a bug report, a repository, a product definition draft, an incident, a migration request, a release request or a set of notes. The operator does not need to know the factory vocabulary before asking for work.

The factory promise is not “an agent will try hard.”

The promise is:

- source is separated from assumption;
- the product target becomes explicit;
- the method is chosen before execution;
- work becomes durable Hermes state;
- workers execute bounded tasks;
- recoverable gaps are repaired by the system;
- humans are asked only for real human decisions;
- completion requires evidence;
- closure requires Receipt Five.

A normal chat can produce useful text. The factory exists because useful text is not enough for serious product work.

## 2. Why this exists

Agentic work usually fails between the obvious steps.

The model can forget. A plan can look complete but never become durable state. A worker can be assigned but never produce a result. A test can pass while the product experience is still bad. A release can be declared complete without rollback, owner or monitoring. A security-sensitive task can start with implementation before threat and access boundaries are clear. A human can be asked to approve something without the evidence needed to decide.

Overkill Factory turns those failure modes into named controls.

If source is unclear, it is a source-boundary problem.
If the target is vague, it is a product-definition problem.
If the route is missing, it is a method problem.
If capability is missing, it is a capability problem.
If a packet exists but no result exists, execution has not happened.
If evidence is missing, the work fails closed.
If human authority is needed, the manager must present a decision package.

The goal is not bureaucracy. The goal is to make the system safe enough to keep moving without pretending uncertainty is proof.

## 3. The roles

There are five important roles.

### Operator

The operator is the human who asks for work and makes decisions that require human authority. The operator should not need to watch every internal status change. The operator should receive clear questions, clear progress and clear receipts.

### Manager

The manager is the human-facing voice of the factory. The manager receives the signal, explains what matters, asks bounded questions, presents human gates and reports progress.

The manager should be the normal interface. Raw worker logs, schema errors and internal runtime events should not become the operator experience unless they are relevant evidence.

### Hermes

Hermes is the runtime. Hermes owns boards, cards, dependencies, statuses, typed blockers, dispatch, task state, worker runs, logs and comments.

Hermes is where work becomes durable. If a chat disappears, the work should still be recoverable from Hermes state and factory artifacts.

### Factory

The factory is the method. It owns source handling, product definition rules, method contracts, gates, worker packets, evidence rules, review policy, release policy, human-gate policy and Receipt Five.

The factory must not become a mini-Hermes. Hermes executes the graph. The factory defines and verifies the rails.

### Workers

Workers are bounded specialists. A worker can implement, review, test, research, inspect security, prepare product experience proof, repair an artifact or reconcile evidence.

A worker does not own the whole route. A worker does not approve its own parent work. A worker does not replace Hermes state. A worker result only matters when it is valid, evidence-bearing and consumable.

## 4. The first step: source boundary

The first step is not coding.

The first step is source boundary.

When the operator sends a signal, the factory records what was actually provided and separates it from what the model inferred. This matters because a chat message is not automatically product truth.

A source boundary answers:

- what did the operator provide;
- where did the material come from;
- whether this is a new product, existing product, bug, incident, release, migration or continuation;
- which facts are explicit;
- which assumptions were inferred;
- which parts conflict;
- which gaps can be researched;
- which gaps require operator input;
- which decisions are human-only.

This prevents the factory from building on invisible assumptions.

## 5. Product definition / PRD

After the source boundary, the factory creates or updates product definition.

In common product language, this is the PRD area: the product definition document or target. Older internal contracts may call part of this the Product SOT. Public documentation should explain PRD / product definition first because that is the clearer human concept.

The product definition answers:

- what is being built;
- who it is for;
- what problem it solves;
- what is in scope;
- what is out of scope;
- what user journeys matter;
- what examples prove acceptance;
- what risks matter;
- what dependencies exist;
- what access or environment is needed;
- what evidence will prove completion;
- what requires human approval.

A product definition is not a summary. It is the target the rest of the run is measured against.

If the operator already provides a PRD-like document, the factory treats it as source. If the operator provides only notes, the factory creates a candidate definition and asks only for decisions it cannot safely infer.

## 6. Full-scope coverage

The factory must not allow the first useful slice to become the entire product by accident.

Before work is treated as complete, every important requirement must be accounted for. It can be planned, done with evidence, blocked, deferred, out of scope, human-owned or replaced by an approved decision. It cannot simply vanish.

This protects the operator from a common agent failure: progress on the most visible part of the task while the less visible product obligations disappear.

## 7. Method selection

The factory chooses the method before execution.

Different work needs different process:

- new product work needs definition, architecture, experience and delivery planning;
- bug repair needs reproduction, a failing proof where possible, fix and regression evidence;
- documentation work needs source truth, audience, structure and link/build validation;
- security-sensitive work needs threat and control thinking before implementation;
- design-heavy work needs product experience before frontend implementation;
- incident work needs containment, diagnosis, repair and learning;
- release work needs rollback, owner, monitoring and promotion gates.

The selected method becomes the control contract for the run.

A worker can execute inside a method. A worker does not get to invent the method.

## 8. Routing by domain, risk and capability

The factory then routes the work.

It asks whether the work touches web, backend, data, mobile, command line, documentation, AI, agent runtime, Solana/onchain, payments, keys, secrets, privacy, production, security or release.

This route determines required specialists, checks and capabilities.

If a capability is missing, the factory should not immediately ask the operator to solve it. It should search configured skills, providers, capability packs and references. Only after that search fails safely should it block for human help.

## 9. Architecture, experience and security

Good product work is shaped before implementation starts.

Architecture decides boundaries, dependencies, data flow, runtime responsibilities and source of truth.

Product experience decides journeys, states, user-facing quality, design-system expectations, accessibility, loading states, error states, empty states and what visual proof is required.

Security decides access, secrets, data exposure, supply chain, abuse cases, rollback, monitoring, review and domain-specific risk.

These are not decorations. They are production controls.

## 10. Product creation plan

The product creation plan turns definition into work units.

Each work unit should say:

- which requirement it serves;
- which worker owns it;
- which reviewer checks it;
- what evidence is required;
- which dependencies must complete first;
- what makes it ready;
- what blocks it;
- what makes it done.

This is where product intent becomes executable structure.

## 11. Hermes work graph

Work must become durable Hermes state.

That means cards, dependencies, statuses, typed blocks, dispatch, runs, comments and worker task state. The next step must not live only in agent memory.

This is why Hermes is central. If the agent process dies or the chat is lost, the work should still be recoverable from Hermes and factory artifacts.

The factory defines what should happen. Hermes records and executes what is happening.

## 12. Worker packets and worker results

A worker packet is an assignment.

It is not execution.

The actual path is:

```text
worker packet created
-> dispatch requested in Hermes
-> task running
-> worker result produced
-> result validated
-> result consumed by parent work
```

Only a valid, evidence-bearing, consumable worker result can advance the parent work.

This distinction prevents a false claim: “the worker was created, therefore the work happened.” No. The packet is a request. The result is the evidence-bearing output.

## 13. Gates

A gate decides whether work may advance.

Examples:

- source gate: source and assumptions are separated;
- product-definition gate: the PRD/product target is usable;
- scope gate: requirements are accounted for;
- method gate: process and evidence rules exist;
- capability gate: required capability exists or failed safely;
- architecture gate: boundaries and dependencies are clear;
- product-experience gate: user-facing states and proof path exist;
- security gate: risk controls and review path exist;
- worker-result gate: the right result exists and validates;
- human gate: human authority is required;
- Receipt Five gate: closure evidence exists.

Gates must fail closed. Missing proof means no promotion.

## 14. No-idle and autonomous progress

Autonomy is not the agent remembering to continue.

Autonomy comes from three things:

1. Hermes stores durable runtime state.
2. Factory contracts define what can safely advance.
3. No-idle reads the current frontier and wakes the next safe action.

No-idle should consume valid results, repair recoverable gaps, dispatch ready work through Hermes, or emit a typed blocker. It should not approve gates, mark work done, replace Hermes, invent phases or turn internal repair into a human question.

The operator should not be pinged for things the factory can repair.

## 15. Human gates

A human gate is a real decision.

Examples:

- approve or correct product definition;
- provide missing source only the operator has;
- grant access;
- approve cost;
- approve production release;
- approve mainnet, signer, funds or secrets;
- accept material risk;
- choose between product directions.

A human gate should include context, options, consequences, recommendation, evidence and safe default. It should not be a vague “can I continue?”

## 16. Evidence

Evidence depends on the work type.

Code needs tests, build/lint where relevant, diff and runtime proof.

User-facing product needs screenshots or equivalent visual proof, state coverage, viewports, accessibility and journey proof.

Security needs threat/control evidence, scan or review results, secret/supply-chain checks and ownership.

Release needs rollback, monitoring, owner, version and promotion gate.

Onchain work needs domain-specific proof and strict signer/funds/mainnet boundaries.

The factory should never accept confidence as evidence.

## 17. Receipt Five

Receipt Five closes the run.

It answers:

1. What changed?
2. Where does it live?
3. How was it verified?
4. Who or what reviewed it?
5. What remains: release, block, operate, risk or learnback?

A run without Receipt Five is not closed. It may be in progress. It may be blocked. It may have useful artifacts. But it is not closed.

## 18. Honest status

The factory should distinguish local implementation from live proof.

A local test can prove code paths and contracts. It does not prove the full external operator experience. Live proof requires the real chain: operator signal, manager intake, FactoryRun, Hermes board, worker execution, progress delivery and Receipt Five returned to the operator.

This boundary matters because the factory is supposed to make work easier to trust. Calling local proof “live autonomy” would break that trust.
