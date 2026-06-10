# Overkill Factory vFinal

This is the canonical architecture document for Overkill Factory vFinal.

It describes how the factory is supposed to work. It is not a backlog and it
does not track open implementation gaps. Runtime readiness lives in:

```text
docs/validation/hermes-vfinal-production-readiness-status.md
docs/roadmap/factory-vfinal-upgrade-plan.md
```

## Simple Definition

Overkill Factory vFinal is a modular software factory for autonomous agents.

Its job is to turn an input into a planned, built, verified, reviewed,
operated, and auditable product change.

In one line:

```text
input -> sources -> outcome -> Product SOT -> right method -> executable plan
-> autonomous execution -> evidence -> review -> operation -> release or block
-> learnback -> factory maturity audit
```

The factory should stay light for simple work and become strict for risky work.

## Core Decision

Hermes is the first supported factory floor.

Overkill Factory is the system above the floor.

Hermes keeps durable work state: boards, cards, tasks, workers, transitions,
results, comments, receipts, and evidence references.

Overkill defines:

- what outcome matters;
- which method applies;
- what risk exists;
- what authority is allowed;
- which gates block;
- which workers are required;
- what evidence proves the work;
- what review is required;
- what must be ready before release.

Discord can be the owner-facing cockpit, but it is not the source of truth.

The owner-facing voice is the Factory Concierge. Specialist workers stay behind
the scenes by default. The Concierge explains state, asks structured questions,
and records owner decisions back into the runtime.

## Non-Negotiable Rules

1. Source before opinion.
2. Outcome before plan.
3. Method before execution.
4. Access before material execution.
5. Security architecture before risky implementation.
6. Evidence before done.
7. Independent review before trust on material work.
8. Human approval for material human risk.
9. Runtime state beats chat history.
10. Learnback turns failures into durable factory improvements.

## Architecture At A Glance

```text
Owner / Product Input
  -> Intake
  -> Source Ledger
  -> Source Resolution
  -> Product Outcome and Discovery
  -> Product SOT
  -> Agentic Method Router
  -> Method Contract
  -> Plans, packs, gates and workers
  -> Autonomy Readiness
  -> Ready Gate
  -> Hermes or selected runtime
  -> Worker Results
  -> Verification and Review
  -> Receipt Five
  -> Completion Audit
  -> Production Operations
  -> Release or Block
  -> Monitoring, Incident and Support
  -> Learnback
  -> Factory Maturity Audit
```

The factory is not a single methodology such as TDD, BDD, SDD, DDD, or
spec-first. Those are tools. The Agentic Method Router chooses the right mix
for the work.

## The Five Practical Layers

### 1. Truth Layer

This layer answers:

```text
What do we know, where did it come from, and what is actually decided?
```

It includes intake, source ledger, source resolution, outcome discovery,
Product SOT, product packs, decision records, conflicts, and gaps.

It prevents memory, assumptions, old documents, or attractive guesses from
becoming truth without being marked as such.

### 2. Method And Planning Layer

This layer answers:

```text
How should this work be conducted?
```

It includes the Agentic Method Router, Method Contract, Product Pack and
Surface Pack selection, Software Development Plan, Product Experience Plan,
Data/Metrics Plan, Agent Eval Plan, Spec Graph, and Loop Plan.

It prevents a large product from becoming loose tasks and prevents a tiny task
from being buried under needless ceremony.

### 3. Risk, Authority, Access And Cost Layer

This layer answers:

```text
What can go wrong, who can authorize it, do we have access, and what can it cost?
```

It includes risk tiers, authority limits, dependency gate, access and capability
gate, privacy/compliance gate, budget gate, autonomy readiness, security
architecture gate, human gate, and ready gate.

It prevents agents from starting work they cannot finish safely.

### 4. Execution And Evidence Layer

This layer answers:

```text
What was done, how do we know, and who checked it?
```

It includes the runtime adapter, Hermes execution, worker packets, worker
results, verification, Product Face proof, remote proof, independent review,
Receipt Five, and Completion Audit.

It prevents "the agent said it is done" from becoming "done".

### 5. Operations, Learnback And Maturity Layer

This layer answers:

```text
Can this operate, what happens if it breaks, and did the factory miss anything?
```

It includes production readiness, release channel, rollback, monitoring,
incident/support, learnback, documentation updates, eval updates, and Factory
Maturity Audit.

It prevents code completion from being mistaken for product readiness.

## Inputs

The factory can start from:

- product paper;
- idea;
- PRD or TRD;
- design;
- issue;
- bug;
- incident;
- existing repository;
- story;
- release request;
- refactor request;
- research question;
- integration request;
- migration request;
- analytics request;
- UX/UI request;
- agent, skill, prompt, or model change.

All inputs first become source material. They do not become truth until the
factory records what was read, what is missing, what conflicts, and what was
decided.

## Work Units

The units do not compete. They fit together.

```text
Product
-> Outcome Contract
-> Product SOT
-> Slice
-> PRD/TRD when needed
-> Story when development needs user context
-> Factory Card for risk, authority and gates
-> Worker Packet for specialist execution
-> Worker Result for specialist output
-> Evidence Pack for proof
-> Receipt Five for closure
```

Definitions:

- Outcome Contract: the result the product must create.
- Product SOT: the official product or slice agreement.
- Story: implementation context from a user or operator perspective.
- Factory Card: controlled unit of agentic execution.
- Worker Packet: structured request to a specialist.
- Worker Result: structured specialist output with evidence.
- Evidence Pack: proof collected during the work.
- Receipt Five: final closure receipt.

## Canonical Journey

### 1. Intake

The factory receives the request and classifies it.

It identifies the owner, product context, initial scope, risk, urgency, whether
the request is planning-only or execution, and whether the work touches code,
product, users, data, release, agents, dependency, or production.

Output:

- intake record;
- initial risk;
- initial source list;
- continue, ask for more source, or block.

### 2. Source Ledger

The factory records where important information came from.

Sources can be documents, repositories, issues, PRDs, TRDs, designs,
conversations, logs, screenshots, boards, test results, runtime state, public
links, private documents, or human comments.

Output:

- source map;
- trusted sources;
- weak sources;
- conflicts;
- gaps.

### 3. Source Resolution

The factory separates fact, summary, inference, decision, conflict, stale
material, and gap.

Output:

- resolved facts;
- unresolved questions;
- decision boundaries;
- conflicts that must not be hidden.

### 4. Product Outcome And Discovery

The factory checks whether the product result is clear.

It asks who the product is for, what problem is real, what behavior must change,
what metric shows success, what risk metric matters, and what assumptions still
need discovery.

Output:

- Outcome Contract;
- discovery brief;
- assumption ledger;
- human questions when needed.

### 5. Product SOT

The factory creates the official agreement for the product or slice.

It records what is in scope, what is out of scope, expected outcome, risks,
authority, dependencies, access, data, metrics, operations, and acceptance
criteria.

Output:

- Product SOT;
- scope boundaries;
- success criteria;
- risk and decision records.

### 6. Agentic Method Router

The router chooses the work method.

It is a factory stage, not a magic agent with unlimited authority. It uses the
input type, source confidence, Product SOT, risk, ambiguity, surfaces,
dependencies, access, cost, reversibility, authority, product pack, surface
pack, evidence, environment, and release path.

It may choose:

- lightweight source and receipt path;
- spec-first planning;
- PRD/TRD path;
- Domain Map or DDD-style modeling;
- BDD/ATDD-style acceptance scenarios;
- TDD or regression-first development;
- discovery-first work;
- prototype-first work;
- legacy diagnosis;
- incident-first work;
- hardening-first work;
- Product Experience route;
- Agent Eval route;
- Security Architecture route;
- Production Operations route.

Output:

- Method Contract.

The router must explain the choice in plain language.

### 7. Method Contract

The Method Contract records what the router chose and why.

It says:

- methods selected;
- methods waived;
- reason for each waiver;
- required artifacts;
- gates;
- workers;
- reviewers;
- evidence;
- authority limits;
- done definition.

Waiving a method is allowed. Waiving it without a reason is not.

### 8. Product Pack And Surface Pack Selection

Product Packs teach the factory how a specific product domain works.

Surface Packs teach the factory how a specific product surface must be planned,
tested, and proven.

Surfaces include websites, web apps, dashboards, mobile apps, desktop apps,
CLI/TUI, extensions, plugins, AI interfaces, agentic interfaces, design systems,
user docs, onboarding, and education.

Output:

- selected Product Pack or recorded reason why none applies;
- selected Surface Pack when the work touches a human surface;
- required workers, templates, and evidence.

### 9. Risk, Authority, Dependency, Compliance, Access And Budget Gates

Before planning execution, the factory checks whether the work has hidden risk.

It decides the effective risk tier, required authority, dependencies, access,
privacy/compliance, budget, and whether a human gate is required.

Important rule:

```text
Planning may continue with pending access.
Material execution must not start without indispensable access.
```

### 10. Security Architecture Plan

When the work has material risk, security must be designed before
implementation.

This plan covers trust boundaries, authentication, authorization, secrets,
data flows, infrastructure, supply chain, logging, abuse cases, rollback or
mitigation, and the later security review path.

Security Review checks the result later. It does not replace Security
Architecture.

### 11. Software Development Plan

This layer organizes software work.

It may include PRD, TRD, domain map, acceptance examples, stories, factory
cards, test plan, QA plan, review plan, legacy/migration plan, platform/devex
plan, release plan, and documentation plan.

Legacy rule:

```text
No agent touches legacy systems without map, baseline and rollback.
```

### 12. Product Experience Plan

This layer handles any product surface used by humans.

It covers experience intake, surface selection, UX discovery, design direction,
Product Face Packet, prototype lane, empty/loading/error states, accessibility,
content, onboarding, Product Face Result, screenshots or equivalent proof,
experience QA, and review.

Product Face remains important, but it is now a packet and result inside the
larger Product Experience OS.

### 13. Data, Metrics And Analytics Plan

When the product needs to be measured, the factory defines success metrics, risk
metrics, product events, dashboards, health indicators, privacy limits, and
decision rules before declaring success.

### 14. Agent Quality And Evals Plan

When agents, AI behavior, prompts, skills, models, or tools matter, the factory
defines evals and regression checks.

It asks what behavior must stay stable, what failure modes matter, what examples
prove the agent is safe enough, and what tests prevent regression.

### 15. Spec Graph

The Spec Graph connects requirements, outcome, examples, decisions, risks,
dependencies, access, security architecture, data, gates, workers, and proof.

It keeps the factory from planning pieces that do not connect.

### 16. Loop Plan

The Loop Plan turns the plan into executable work.

It defines lanes, order, workers, inputs, limits, timeouts, budget, access,
expected evidence, stop criteria, and block criteria.

### 17. Autonomy Readiness Packet

Before material execution, the factory lists everything needed to act
autonomously:

- repository access;
- branch and pull request permissions;
- cloud access;
- database access;
- storage access;
- domain/DNS access;
- external APIs;
- payment or store accounts;
- secrets through a safe path;
- environments;
- billing limits;
- observability;
- runtime profiles;
- human approvers.

The packet records whether each item is granted, pending, not needed, needed
later, or blocking now.

Secrets are never stored in plaintext in the packet.

### 18. Ready Gate

Ready Gate checks whether execution may begin.

It verifies sources, outcome, Product SOT, Method Contract, packs, required
plans, risk, authority, dependencies, access/capability, compliance, budget,
workers, forbidden actions, done definition, and evidence plan.

If something material is missing, execution blocks.

### 19. Control Tower Projection And Owner Interface

Before material execution, the factory creates a clear owner-facing projection.

It shows:

- current phase;
- whether execution has started;
- what is already planned;
- what is missing;
- blockers;
- pending access;
- pending approvals;
- next steps;
- forecast confidence;
- risks that can change the plan;
- existing evidence.

When Discord is active, this projection appears in the Discord Control Tower.

The Factory Concierge explains state, asks scoped questions, records decisions
back into Hermes or the selected runtime, and prevents worker noise from
reaching the owner by default.

### 20. Runtime Execution

Hermes or another selected runtime executes the work.

The runtime does not choose methodology. It executes what the Method Contract
and Loop Plan authorize.

Before a card becomes `ready`, the runtime adapter must call the factory gate,
materialize required subtasks, and block if required plans, access, security,
authority, Control Tower visibility, or other indispensable inputs are missing.

This applies to manual promotion, direct creation in `ready`, automatic
recompute, unblock-to-ready, dashboard/API routes, and worker routes.

Subtasks created by the factory do not automatically mean execution is allowed.
They can be created as blocked work until access, authority, profile, model,
tools, and evidence requirements are ready.

The correct dependency direction is:

```text
worker subtask -> parent card
```

That means the parent card waits for worker evidence before closing.

Before a card becomes `done`, the runtime adapter must reconcile Receipt Five,
Worker Results, evidence, reviews, human gates, and remaining blockers.

If required proof is missing, `done` does not exist.

### 21. Worker Result

Workers return structured results.

Allowed result shapes include:

- PASS;
- FAIL;
- WAIVED;
- PENDING;
- BLOCKED.

A result must say what the worker received, what it did, what changed, where the
evidence is, what risk remains, and whether another worker or human is needed.

### 22. Verification

Verification may include tests, lint, build, browser proof, screenshots, scans,
audits, evals, dependency checks, logs, release smoke, monitoring evidence, or
remote proof.

Remote proof is used when local proof is not enough. It needs a reason, limit,
cost boundary, TTL, cleanup, and artifacts.

### 23. Independent Review

Independent review is required for meaningful code work, R2+, R3/R4,
security-sensitive work, release material, agent/skill changes, and any work
where the Method Contract requires it.

The executor does not approve its own work.

### 24. Human Gate

Human approval is required for material decisions such as production, signing,
funds, custody, mainnet, R4 release, blocking waiver, economic decision,
legal/regulatory risk, sensitive privacy risk, budget exception, critical
dependency without fallback, material access exception, or security architecture
without an owner.

The factory prepares the decision packet. It does not invent approval.

### 25. Closure Summary

The Closure Summary explains the request, delivery, proof, residual risks,
waivers, approved scope, forbidden scope, and next action.

It is the readable story of what happened, not a substitute for evidence.

### 26. Receipt Five

Receipt Five closes the work by answering five questions:

1. What changed?
2. Where is it?
3. How was it verified?
4. Who reviewed it?
5. What is the next step?

Without Receipt Five, there is no done.

### 27. Completion Audit

Completion Audit compares required work against delivered work.

It checks Method Contract, gates, workers, evidence, reviews, human approvals,
autonomy readiness, security architecture, release requirements, and Receipt
Five.

If a required proof, worker, gate, review, or approval is missing, it blocks.

### 28. Production Operations

When release or live operation is in scope, the factory requires declared
environment, operational owner, health check, logs, metrics, rollback or
mitigation, release channel, support path, incident path, and deploy proof.

Production readiness is not code completion.

### 29. Release Or Block

The work can end as:

- released;
- release candidate;
- done;
- blocked;
- superseded;
- archived.

Release needs channel, version, build or publication evidence, rollback or
mitigation, monitoring, owner, and channel-specific restrictions.

### 30. Monitoring, Incident And Support

After release, the factory watches health, alerts, metrics, errors, incidents,
support, cost, dependencies, UX signals, and risk signals.

Incidents need severity, owner, impact, mitigation, communication, fix,
evidence, postmortem, and learnback.

### 31. Learnback

Learnback turns lessons into durable factory improvements.

A lesson may become a test, eval, skill, policy, checklist, template, doc, gate,
worker, Product Pack update, or Surface Pack update.

### 32. Factory Maturity Audit

The Factory Maturity Auditor checks whether the factory was mature enough for
the work type.

It is required for large projects, R3/R4 work, complex new products, structural
factory changes, and real production readiness.

It can approve, block, request a complement, reroute the method, or create a
future maturity check.

## Core Layers

### Factory Kernel

The kernel stores common rules:

- states;
- schemas;
- contracts;
- gates;
- risk tiers;
- authority limits;
- worker registry;
- evidence rules;
- completion audit rules;
- public/private boundary;
- validation scripts.

The kernel must not carry private product context.

### Product Outcome And Discovery OS

This layer prevents agents from building a polished answer to the wrong
question.

It produces outcome and discovery evidence before planning becomes execution.

### Product Pack SDK

Product Packs keep product-specific knowledge outside the generic core.

A pack can contain domain rules, glossary, risk policy, security policy,
privacy/compliance notes, release policy, dependencies, supported surfaces,
required workers, evidence templates, evals, examples, and docs.

Packs have owners, versions, compatibility, public/private boundaries, and
deprecation rules.

### Software Development OS

This layer organizes PRD/TRD, domain map, acceptance examples, stories, cards,
development loops, debugging, legacy work, migration, platform/devex, QA,
review, release, docs, and retro.

It exists so autonomous agents do not treat software development as a pile of
unrelated tasks.

### Product Experience OS

This layer organizes the experience of websites, web apps, mobile apps,
desktop apps, CLI/TUI, extensions, plugins, AI interfaces, agentic interfaces,
design systems, user docs, onboarding, and education.

It requires surface-specific proof. A visual product is not done because code
compiled.

### Data, Metrics And Analytics OS

This layer defines success, risk, product events, dashboards, technical health,
operational health, quality signals, privacy limits, and decision rules.

### Agent Quality And Evals OS

This layer tests agents, skills, prompts, models, tools, authority behavior,
evidence discipline, hallucination, omission, over-action, passivity, and
method routing.

Important agent behavior without evals is not reliable enough.

### Dependency And Integration OS

This layer maps APIs, SDKs, databases, auth, payments, stores, oracles, AI
models, cloud, MCPs, accounts, credentials, rate limits, quotas, costs,
environments, mocks, stubs, fallbacks, contract tests, supply chain, secrets,
and permissions.

### Security And Authority

Security is split into architecture before implementation and review after
implementation.

Security Architecture decides how the product should be born safe. Security
Review checks whether the result honored that architecture.

### Production Operations OS

This layer prepares the product to run in the real world: environments, deploy,
release channels, versioning, changelog, rollout, rollback, health checks, logs,
metrics, alerts, backup, restore, runbooks, incident response, support,
operational owner, monitoring, and maintenance.

### Owner Interface And Control Tower

The recommended owner cockpit is Discord.

```text
Discord = human cockpit
Hermes or selected runtime = durable source of truth
Overkill Factory = method, gates, workers and evidence
Factory Concierge = official owner-facing voice
```

The Control Tower shows status, phase, blockers, pending access, pending
approvals, forecast, forecast confidence, evidence links, release decisions,
incident alerts, and bot/bridge health.

It must not store secrets, replace runtime state, approve risk for the owner,
treat free-form chat as sensitive approval, let workers bypass gates, or let
Discord become a parallel source of truth.

### Worktrees And Parallel Agents

The factory can use worktrees and parallel agents, but only with clear lane
ownership.

Parallel work is allowed when lanes are independent and have separate write
scopes. Examples include read-only audits, distinct proof harnesses, separate
docs, separate schemas, and independent validation reviews.

Parallel work must not create hidden authority. The main factory agent remains
responsible for integration, public-safety hygiene, validation, and deciding
whether subagent output belongs in canonical docs, roadmap, validation, or
private context.

Each parallel lane needs:

- lane name;
- owner agent or worker;
- input refs;
- write scope;
- forbidden files or surfaces;
- expected output;
- validation command;
- evidence refs;
- cleanup rule;
- integration owner.

If a lane cannot name its write scope, it stays read-only.

Worktrees are execution containers, not proof by themselves. A worktree result
must still provide changed files, evidence, validation, residual risk and
cleanup status before integration.

## Gates

A gate returns one of three outcomes:

- pass;
- block;
- pass with explicit risk and owner.

vFinal gates include:

- Source Gate;
- Outcome Gate;
- Discovery Gate;
- Method Gate;
- Pack Gate;
- Experience Gate;
- Data/Metrics Gate;
- Agent Eval Gate;
- Dependency Gate;
- Access and Capability Gate;
- Compliance/Privacy Gate;
- Budget Gate;
- Security Architecture Gate;
- Ready Gate;
- Control Tower Gate;
- Review Gate;
- Production Readiness Gate;
- Release Channel Gate;
- Human Gate;
- Done Gate;
- Completion Audit;
- Factory Maturity Gate;
- Release Gate.

## Risk Tiers

| Tier | Meaning | Typical handling |
| --- | --- | --- |
| R0 | Tiny, reversible work | Light path |
| R1 | Low risk | Basic source, acceptance, verification |
| R2 | Non-trivial product work | Review and stronger evidence |
| R3 | Security, privacy, infra, critical dependency, complex legacy, important agent behavior, or high impact | Full method contract, specialist gates, independent review |
| R4 | Production, signing, funds, regulated work, critical release, high cost, or material human risk | Human gates, autonomy readiness, rollback, monitoring, completion audit |

Any gate can raise the tier.

Small work should not become heavy by default. Risky work should not move
forward just because the agent sounds confident.

## Worker Model

The worker registry is the source for supported public workers:

```text
agents/worker-registry.public.json
```

The architecture expects these worker categories:

- orchestration;
- source and SOT;
- method routing;
- product architecture;
- product experience;
- software planning;
- implementation;
- QA and verification;
- security and specialist review;
- dependency and access;
- data and evals;
- production operations;
- control tower and owner interface;
- public safety;
- maturity audit.

Workers do not approve their own gates. They produce structured results and
evidence for gates to inspect.

## Runtime Adapter Contract

Every runtime adapter must:

- enforce before-ready gates;
- enforce before-done gates;
- create required worker subtasks;
- keep required subtasks upstream of the parent card;
- ingest worker results back into the parent;
- preserve evidence references;
- block unsafe execution without pretending success;
- keep owner-facing projections derived from runtime truth;
- support update, compatibility and rollback checks.

The Hermes adapter is the first implementation of this contract.

The current Hermes readiness evidence is intentionally tracked outside this
canonical architecture document so this file remains the final model rather
than a moving status report.

## Access And Capability

The factory must know whether it has the required access before material
execution starts:

- repository access;
- cloud access;
- account access;
- runtime access;
- safe secret path;
- billing limits;
- required tools;
- approval to perform the action.

If indispensable access is missing, the work is blocked, narrowed, or converted
to planning-only.

## Evidence

The factory judges work by evidence, not by confidence.

Useful evidence includes source ledgers, plans, worker packets, worker results,
command output, test logs, screenshots, browser proof, scan reports, review
reports, human gate records, receipts, completion audits, runtime logs, release
smokes, rollback proof, and monitoring proof.

Local scripts are preflight. They help, but they are not the same as runtime
validation.

## Done Definition

A vFinal work item is done only when:

- the source was resolved;
- the outcome is clear;
- the method was chosen and explained;
- required plans exist;
- required gates passed or blocked with owner;
- required workers produced results;
- verification evidence exists;
- independent review happened when required;
- human approval happened when required;
- Receipt Five exists;
- Completion Audit reconciles promise, work, proof, risk, and next action;
- production readiness exists when release or operation is in scope;
- owner approvals are structured and registered in the runtime;
- the control tower mirrors runtime truth instead of becoming a parallel source
  of truth;
- learnback records what the factory should remember.

## Public Repository Rule

Public artifacts must not contain private product names, local paths, personal
identities, private board ids, private runtime details, raw study dumps, or
secret-bearing material.

Private context may shape decisions, but only public-safe rules belong here.
