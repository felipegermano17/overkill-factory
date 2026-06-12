# Operator Journey

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `scripts/factoryctl.py`, `schemas/`, adapter hooks, tests and `README.md`.
> Runtime boundary: This guide explains how a human operator experiences the factory; runtime state and receipts decide completion.

This page explains what happens inside Overkill Factory from the point of view
of a human operator or external contributor. It is intentionally human-readable:
start here when the README tells you what the project is, but you still want to
understand how the factory thinks.

## The Journey In One Line

```text
request
-> source
-> outcome
-> method
-> gates
-> execution
-> evidence
-> review
-> release or block
-> learnback
```

The factory is not a single agent doing tasks. It is a system for deciding what
should happen, assigning the right workers, proving what happened and preserving
human authority where the risk requires it.

## The Five Layers

### Truth Layer

This layer answers:

```text
What do we know? Where did it come from? What is actually decided?
```

It includes intake, source ledger, source resolution, product outcome,
discovery, Product SOT, product packs, human decisions, conflicts and gaps.

### Method And Planning Layer

This layer answers:

```text
How should this work be carried out?
```

It includes the Method Router, Method Contract, product and surface packs,
security architecture, software plan, product experience plan, data plan, eval
plan, spec graph and loop plan.

### Risk, Authority, Access And Cost Layer

This layer answers:

```text
What can go wrong? Who can authorize? Do we have access? What can it cost?
```

It includes risk tiering, authority limits, dependency checks, access checks,
privacy and compliance checks, security gates, budget limits, autonomy
readiness and human gates.

### Execution And Evidence Layer

This layer answers:

```text
What was done? How do we know? Who reviewed it?
```

It includes the runtime adapter, Hermes or another runtime, worker packets,
worker execution, worker results, verification, Product Face proof, remote proof
when needed, independent review, Receipt Five and completion audit.

### Operations, Learning And Maturity Layer

This layer answers:

```text
Can this run? How is it supported? What did we learn? Did the factory miss a gap?
```

It includes production operations, release or block, monitoring, incident
support, learnback and factory maturity audit.

## Stage-By-Stage Journey

| Stage | What happens | Output |
| --- | --- | --- |
| 1. Intake | The operator brings a paper, bug, repo, incident, feature, release or research request. | Input type and initial scope. |
| 2. Source Ledger | The factory records where source material came from. | Source list. |
| 3. Source Resolution | Facts, inference, decisions, conflicts and gaps are separated. | Source resolution. |
| 4. Product Outcome & Discovery | The desired result, user, problem and assumptions are clarified. | Outcome and discovery notes. |
| 5. Product SOT | The product or slice is defined in one source-of-truth candidate. | Product SOT. |
| 6. Method Router | The factory chooses the right process weight. | Router decision. |
| 7. Method Contract | The chosen method, exclusions, evidence and blockers are recorded. | Method contract. |
| 8. Pack Selection | Product and surface capability needs are identified. | Required packs and missing packs. |
| 9. Gates | Risk, authority, dependency, compliance, access and budget are checked. | Gate status. |
| 10. Security Architecture | Material risk is designed before implementation. | Security architecture plan. |
| 11. Software Plan | The technical work is broken into a buildable plan. | Software plan. |
| 12. Product Experience Plan | Product-facing surfaces get flows, states and proof requirements. | Product Face packet. |
| 13. Data & Metrics Plan | Success, health and learning signals are defined. | Metrics plan. |
| 14. Agent Evals Plan | Important agentic behavior gets evals before trust. | Evals plan. |
| 15. Spec Graph | Specs, stories, cards and dependencies are connected. | Spec graph. |
| 16. Loop Plan | Workers, order, limits and stop criteria become executable. | Loop plan. |
| 17. Autonomy Readiness | Required access, accounts, tools and permissions are checked. | Readiness packet. |
| 18. Ready Gate | The factory decides whether execution can start. | Ready, blocked or revise. |
| 19. Operator Projection | The human view summarizes phase, blockers and next moves. | Operator status view. |
| 20. Runtime Execution | Hermes or another runtime runs the card and worker tasks. | Runtime events. |
| 21. Worker Results | Each worker returns structured output with evidence. | Worker result records. |
| 22. Verification | Tests, checks and product proof are run. | Verification result. |
| 23. Independent Review | A separate reviewer checks the work when required. | Review result. |
| 24. Human Gate | A real human decision is recorded for material risk. | Decision record. |
| 25. Closure Summary | The factory summarizes what actually happened. | Closure summary. |
| 26. Receipt Five | The done receipt records change, evidence, review and next action. | Receipt Five. |
| 27. Completion Audit | Required process is compared with delivered evidence. | Audit result. |
| 28. Production Operations | Runbooks, ownership, health and rollback are prepared. | Ops readiness. |
| 29. Release Or Block | The factory releases only when the gate is satisfied. | Release or block decision. |
| 30. Monitoring & Support | The product is watched and incidents get a route. | Monitoring and support path. |
| 31. Learnback | Lessons become docs, tests, policies, skills or product changes. | Learnback item. |
| 32. Maturity Audit | The factory checks whether the method itself missed something. | Maturity audit. |

## Short Paths By Request Type

### Simple Documentation Or Text Change

```text
Intake -> Source Ledger -> light router -> short method contract
-> execution -> verification -> Receipt Five
```

Use this for low-risk wording, naming or local documentation edits.

### Bug

```text
Intake -> Source Ledger -> reproduction -> diagnosis -> fix
-> regression check -> review -> Receipt Five -> Learnback when repeated
```

A bug needs reproduction, or a clear reason why reproduction was not possible.

### Common Feature

```text
Intake -> Source -> light outcome -> Product SOT or slice
-> Method Contract -> story -> build loop -> QA -> review -> Receipt Five
```

A normal feature still needs success criteria and evidence.

### Product With Interface

```text
Intake -> Outcome & Discovery -> Product SOT -> Surface Pack
-> Product Face Packet -> Software Plan -> execution -> Product Face Result
-> Experience Gate -> review -> Receipt Five
```

A surface is not ready until flows, states, viewports, accessibility and layout
behavior have been checked.

### Complex Product Or Material Change

```text
Intake -> Source Ledger -> Source Resolution -> Outcome & Discovery
-> Product SOT -> Product Pack -> Method Router -> Method Contract
-> Risk/Dependency/Access/Compliance/Budget Gates -> Security Architecture
-> Software Plan -> Experience Plan -> Data Plan -> Evals Plan when relevant
-> Spec Graph -> Loop Plan -> Autonomy Readiness -> Ready Gate
-> Runtime execution -> Verification -> Review -> Human Gate when required
-> Completion Audit -> Production Operations -> Release or Block
-> Learnback -> Factory Maturity Audit
```

A complex product cannot depend on one line of planning. It needs truth, method,
packs, gates, safe architecture, granted access, worker results, evidence,
operations and maturity review.

### Critical Integration

```text
Intake -> Source -> Product or slice SOT -> Dependency Gate
-> Integration Contract -> tests, mocks and fallback -> Verification
-> Review -> Receipt Five
```

A critical integration needs an owner, auth model, limits, cost, expected
failure behavior and contract tests.

### Legacy Or Migration

```text
Intake -> Source -> brownfield discovery -> legacy system map
-> baseline -> migration plan -> regression -> rollback -> execution
-> Verification -> Review -> Completion Audit
```

Legacy work should not be treated as a clean-field product.

### Agent, Skill, Prompt Or Model

```text
Intake -> Source -> Method Contract -> Agent Quality & Evals Plan
-> change -> evals -> review -> Receipt Five -> Learnback
```

An important agentic change without evals should not be trusted.

### R4 Release

```text
Product SOT -> Method Contract -> Production Operations
-> Security Architecture -> Security/Compliance/Dependency/Access/Budget Gates
-> Autonomy Readiness -> Release Channel Gate -> Human Gate
-> Release Evidence -> Monitoring -> Learnback
```

R4 release needs a human decision, rollback or mitigation, monitoring, owner and
strong evidence.

### Production Incident

```text
Incident intake -> severity -> owner -> mitigation -> evidence
-> fix route -> review -> release or rollback -> postmortem -> Learnback
```

An incident should become durable learning.

## What Ready Means

Ready means the factory has enough source, method, scope, access, authority and
worker routing to begin execution. It does not mean the work is done.

A card should stay blocked when:

- source facts and inference are mixed;
- the expected outcome is vague;
- required access is absent;
- the method is not recorded;
- the risk tier is unclear;
- a required pack or specialist is missing;
- human authority is required but not available;
- the work cannot be verified.

## What Done Means

Done means the factory can show:

- the source and scope;
- the method and gates used;
- the worker packets created;
- the worker results returned;
- the commands, checks or product proofs run;
- the independent review result when required;
- the human decision when required;
- the Receipt Five;
- the completion audit result;
- the next action.

Done without evidence is only a claim.

## Common Anti-Patterns

Avoid:

- starting execution from a vague prompt;
- treating a product paper as truth without source resolution;
- letting a worker review its own work;
- using chat messages as approval for material risk;
- treating a screenshot or status summary as the source of truth;
- putting generated evidence archives into the public repository;
- calling an interface ready without checking flows and states;
- releasing without owner, rollback, monitoring and channel;
- making the operator talk to every worker instead of a controlled operator view;
- skipping learnback after repeated failure.
