# Overkill Factory Method

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `scripts/factoryctl.py`, `schemas/`, adapter hooks, tests and `README.md`.
> Runtime boundary: This guide explains the public method; executable gates and runtime receipts decide whether work can move.

Overkill Factory is a gated production line for agentic product work. It turns
a product paper, bug, incident, release request, repository or research request
into a controlled path of source resolution, planning, specialist execution,
proof, review, human authority and release readiness.

It exists because agents are useful when work is scoped, but unreliable when a
single prompt mixes source facts, assumptions, planning, execution, review and
approval. The factory separates those responsibilities so every important claim
has an owner, a contract and a way to be checked.

## One-Line Model

```text
input
-> source
-> outcome
-> discovery
-> Product SOT
-> method
-> executable plan
-> agentic execution
-> evidence
-> review
-> operations
-> release or block
-> learnback
-> factory maturity audit
```

Not every project runs every step with the same weight. The Method Router
chooses the minimum safe path for the input, risk and surface.

## Core Principles

1. Source before opinion.
2. Outcome before plan.
3. Discovery before treating a paper as truth.
4. The right method before execution.
5. Organized development before loose worker activity.
6. Product experience before calling a surface ready.
7. Data and metrics before claiming success.
8. Security architecture before material build work.
9. Explicit dependencies before integration.
10. Access and capability before material execution.
11. Cost and limits before expensive or remote execution.
12. Explicit authority before material action.
13. Privacy, compliance and security throughout the process.
14. Evals before trusting important agents, skills, prompts or models.
15. Evidence before done.
16. Independent review before confidence.
17. Human authority for material risk.
18. Release needs an owner, rollback path, monitoring and channel.
19. Incidents become tests, policies, skills, docs or product changes.
20. The factory itself must be audited so gaps do not depend on memory.
21. Human interfaces mirror the factory; they do not replace durable state.
22. A runtime records the operational truth; chat is an operator view.

## Public Vocabulary

| Term | Meaning |
| --- | --- |
| Factory Kernel | Generic rules, schemas, risk tiers, gates, states and validation behavior. |
| Runtime | The system where durable work happens. Hermes is the first supported runtime. |
| Runtime Adapter | The bridge that turns factory rules into runtime events, worker tasks and transition blocks. |
| Product Outcome & Discovery OS | The layer that defines the result, user, problem, assumptions and missing research. |
| Product SOT | The source-of-truth candidate for scope, non-goals, acceptance criteria and success. |
| Product Pack | Product-specific rules, glossary, risks, policies, examples and specialist routing. |
| Surface Pack | Rules for a visible or operational surface such as web, mobile, CLI, docs or onboarding. |
| Method Router | The decision step that chooses the process weight and required gates. |
| Method Contract | The recorded router decision: included methods, excluded methods, evidence and blockers. |
| Loop Plan | The executable plan: workers, order, scope, limits, evidence and stop criteria. |
| Worker Packet | A structured request for one specialist worker. |
| Worker Result | The structured result produced after the worker actually runs. |
| Evidence OS | The proof layer: tests, logs, screenshots, audit results, hashes, findings and decisions. |
| Receipt Five | The final done receipt: what changed, where it lives, how it was verified, who reviewed and what comes next. |
| Completion Audit | The final comparison between required work and delivered work. |
| Factory Maturity Auditor | The check that the factory chose the right process and did not skip a critical area. |

## Accepted Inputs

The factory can start from:

- a product paper;
- a feature idea;
- a bug report;
- an incident;
- an existing repository;
- an existing PRD, story or architecture;
- a release request;
- a refactor request;
- a research request;
- a documentation request;
- a security review request;
- an integration or migration request;
- a UX/UI request;
- an analytics request;
- an agent, skill, prompt or model change.

Every input becomes source material. Product or material product-change work
also needs outcome and discovery before the Product SOT is treated as stable.

## Canonical Flow

This is the full flow. Small work can take a lighter path, but the router must
record why a step is omitted.

```text
1. Intake
2. Source Ledger
3. Source Resolution
4. Product Outcome & Discovery
5. Product SOT
6. Agentic Method Router
7. Method Contract
8. Product Pack and Surface Pack selection
9. Risk, Authority, Dependency, Compliance, Access and Budget Gates
10. Security Architecture Plan when material risk exists
11. Software Development Plan
12. Product Experience Plan when a product surface exists
13. Data, Metrics & Analytics Plan when success must be measured
14. Agent Quality & Evals Plan when agents, skills or models matter
15. Spec Graph
16. Loop Plan
17. Autonomy Readiness Packet
18. Ready Gate
19. Operator Projection
20. Runtime execution
21. Worker Results
22. Verification
23. Independent Review
24. Human Gate when required
25. Closure Summary
26. Receipt Five
27. Completion Audit
28. Production Operations
29. Release or Block
30. Monitoring, Incident and Support when needed
31. Learnback
32. Factory Maturity Audit
```

## Work Units

The method uses different units for different parts of the line:

| Unit | Purpose |
| --- | --- |
| Source Ledger | Captures where claims came from. |
| Source Resolution | Separates fact, inference, decision, conflict and gap. |
| Product SOT | Defines the product or slice to build. |
| Method Contract | Records the selected process and required gates. |
| Product Pack | Keeps product-specific context out of the public core. |
| Surface Pack | Defines what a surface must plan, build and prove. |
| Factory Card | Machine-checkable work contract consumed by Hermes and `factoryctl.py`. |
| Worker Packet | Specialist assignment derived from the card. |
| Worker Result | Specialist output with evidence. |
| Receipt Five | Closure record for done. |

## Risk Tiers

| Tier | Typical use | Required rigor |
| --- | --- | --- |
| R0 | Text or local-only inspection with no material impact. | Light routing, source check and receipt. |
| R1 | Low-risk reversible work. | Short method contract, focused validation and review when useful. |
| R2 | Product-facing, code-facing, UX, data or integration work. | Acceptance criteria, QA, review and evidence pack. |
| R3 | Security, privacy, infrastructure, important agents, critical dependency or high-impact behavior. | Full method contract, security/dependency/access route, independent review and possible human gate. |
| R4 | Production, irreversible action, signing, funds, release, regulated work or high cost. | Explicit human gates, rollback, monitoring, risk owner, budget owner and completion audit. |

Any gate can raise the risk tier.

## Required Gates

The important gates are:

| Gate | Blocks when |
| --- | --- |
| Source Gate | Critical claims do not point to usable source material. |
| Outcome Gate | The intended result or user value is vague. |
| Discovery Gate | Unknowns are being treated as decisions. |
| Method Gate | The work has no recorded process choice. |
| Pack Gate | The required product or surface capability is missing. |
| Experience Gate | A product surface has no flow, state, viewport, accessibility or UX proof. |
| Data/Metrics Gate | Success cannot be measured where measurement matters. |
| Agent Eval Gate | Important agentic behavior has no eval route. |
| Dependency Gate | External APIs, SDKs, vendors or integrations are undefined. |
| Access & Capability Gate | Required accounts, secrets, permissions or runtime capabilities are absent. |
| Compliance/Privacy Gate | Data, consent, retention, licensing or legal risk is unhandled. |
| Budget Gate | Expensive, remote or long-running work has no limit or cleanup path. |
| Ready Gate | The work is not executable with the current inputs, access and authority. |
| Review Gate | Required review has not happened or is not independent. |
| Security Gate | Material security work has no specialist result or waiver. |
| Security Architecture Gate | Material risk was not designed before build work. |
| Human Gate | Human authority is required but no real decision exists. |
| Done Gate | Worker results, verification, review or Receipt Five are missing. |
| Completion Audit | Required method, gate or evidence is skipped. |
| Release Gate | Release lacks owner, rollback, monitoring, channel or approval. |

## Definition Of Done

Work is done only when the factory can answer:

- what input started the work;
- which sources were used;
- what result was expected;
- which method and gates applied;
- which workers ran;
- what each worker produced;
- how the result was verified;
- who reviewed it;
- whether a human decision was required;
- where the Receipt Five lives;
- what must happen next.

An agent saying "finished" is not enough.

## Public Repository Boundary

The public repository should contain public-safe method, contracts, examples,
schemas, worker profiles, adapter hooks and runbooks.

The public repository should not contain:

- raw source dumps;
- private product context;
- local absolute paths;
- private board links;
- screenshots or logs from private operations;
- generated evidence bundles from old runs;
- historical pilot output;
- private ledgers;
- local validation archives.

Generated outputs belong under `.tmp/` or another external evidence store. A
release note can summarize validation, but the repository should stay focused
on understanding and using the product.

## How Hermes Fits

Hermes is the first supported runtime. Overkill Factory defines the method,
contracts, gates and worker expectations. Hermes supplies the durable board,
cards, tasks and transition events.

The adapter is responsible for translating method rules into runtime behavior:

- block weak `ready` or `done` transitions;
- generate required worker packets;
- record transition metadata;
- reconcile worker results;
- preserve human authority for material risk.

Hermes does not replace the factory method. The factory method does not replace
runtime evidence.

## Operator Checklist

Before starting work:

- identify the input type;
- capture source material;
- separate facts from inference;
- define the desired outcome;
- choose the method;
- classify risk;
- identify required packs, gates and workers;
- confirm access and authority;
- create a card and run the gate report.

Before moving to done:

- collect worker results;
- run verification;
- run independent review when required;
- record human decisions when required;
- reconcile evidence;
- produce Receipt Five;
- run the completion audit.
