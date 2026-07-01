# Factory flow and Hermes technical architecture

This is the dense document. It replaces the split conceptual pages about request flow, operator experience, evidence, human decisions, workers, status, glossary and Hermes boundary.

The previous structure was easier to skim but too shallow. This page is intentionally more useful: it explains what the Factory is technically, how it sits on top of Hermes, what actually happens in every phase, what state is written, what workers are allowed to do, how evidence is consumed, and where false progress is blocked.

## The short version

Overkill Factory is the production contract around Hermes. Hermes is the live runtime floor: cards, statuses, dependencies, comments, attachments, workers, board state and transitions. The Factory is the deterministic contract that says what a request must become before Hermes work starts, what each worker must receive, what proof must return, when review is consumed, when a human decision is legitimate, and what is required before done.

Hermes is the live runtime source of truth. The Factory must not keep a hidden second status system. If Hermes says the card is blocked, the Factory cannot secretly treat it as done. If the Factory has a local artifact but Hermes has no worker result, the correct claim is local proof, not live delivery.

## What the Factory is technically

Technically, the Factory is a contract layer made of:

- a compiled phase catalog: `26 compiled phases` in `docs/factory-workflow.catalog.json`;
- route classes: `14 route classes` in `factory/templates/factory-route-registry.json`;
- method engines: `8 method engines` in `factory/templates/method-engine-registry.json`;
- operating-system areas: `17 operating-system areas` in `factory/templates/factory-operating-system-registry.json`;
- public workers: `40 public workers` in `factory/agents/worker-registry.public.json`;
- schemas that define valid records;
- templates that materialize contracts and example records;
- scripts, especially `factory/scripts/factoryctl.py`, that validate, project and materialize the public-safe parts of the system;
- tests that prevent public documentation from overclaiming runtime delivery.

That means “Factory” is not a mood, a prompt, a Kanban board, or a document set. It is a set of executable constraints around agentic work.

## How it fits into Hermes

Hermes owns runtime. The Factory owns production discipline.

```text
operator signal
  -> Factory source/intake contract
  -> Factory phase engine and method selection
  -> Hermes board/card/workers as live runtime
  -> Worker Packet sent through Hermes profile/binding
  -> Worker Result returned with evidence refs
  -> Factory readback and gate evaluation
  -> Hermes transition, repair, human decision or closure
```

### Runtime ownership

Hermes owns:

- board identity;
- card status;
- card dependencies;
- comments and attachments;
- worker assignment runtime;
- live blocked/running/done transitions;
- operator-visible work state.

Factory owns:

- source preservation rules;
- Product SOT and scope coverage;
- route and method selection;
- Worker Packet shape;
- worker authority boundaries;
- gate predicates;
- evidence requirements;
- readback rules;
- review consumption;
- human decision packet requirements;
- Receipt Five closure requirements.

The bridge between them is not allowed to execute factory work. Bridge adapters do not execute factory work; they only carry status, start, question, decision, change, exception, handoff or learnback signals across the boundary. Bridge modes such as status_bridge, start_bridge, question_bridge, decision_bridge, change_bridge, exception_bridge, handoff_bridge and learnback_forwarding move intent, status or decisions across the boundary. They do not replace Factory phases and they do not authorize hidden completion.


### Operator bridge details

Durable Operator Inbox is the operator-facing mailbox pattern for decisions, status and attachments. It must point to the default Hermes store as the runtime source for the board/card state, not to a private duplicate tracker. Factory Mechanic remains the self-improvement owner for Factory process improvements; bridge adapters must not silently mutate the production method.

The bridge cannot execute work, approve gates, mutate card truth behind Hermes, or turn a question into implementation authority. It can carry start, status, question, decision, change, exception, handoff and learnback signals into the Factory boundary.

## The runtime object model

The main objects are:

- source envelope: sealed raw signal before interpretation;
- source ledger: facts, assumptions, decisions, conflicts and gaps;
- Product SOT: product truth for the requested work;
- Method Contract: how this type of work will be done and proven;
- factory_phase_lock: current frontier and frozen downstream scope;
- Worker Packet: bounded task sent to a worker;
- Worker Result: structured return from a worker;
- Gate Report: predicate result for promotion/block;
- Receipt Five: closure record containing request, work, evidence, review and remaining risk;
- Status Snapshot: operator-facing projection of where the work stands.

A file existing is not enough. A worker saying “done” is not enough. A card moving is not enough. The Factory reads fields, validates schemas, opens referenced artifacts, checks command output, consumes review and reconciles back into Hermes.

## Product truth is not summary

A shallow summary says: “build onboarding.” Product truth says who enters onboarding, what success means, what is out of scope, what evidence proves the journey and what risks are still unresolved. Product SOT prevents each worker from building a different interpretation.

Bad Product SOT:

```text
Build onboarding and make it good.
```

Usable Product SOT:

```text
User: new workspace admin.
Goal: create a workspace and reach the first useful dashboard state.
Must include: account creation, workspace name, invite step, loading state, empty state, confirmation state.
Out of scope: billing, KYC, role editor, production email migration.
Risks: account permissions, email deliverability, confusing empty state, mobile overflow.
Acceptance evidence: Product Face screenshots, first-run journey test, backend workspace-state check, review result, Receipt Five.
Open gaps: invite provider for staging.
```

## Worker packets and authority

A Worker Packet is not “please help.” It is an executable boundary. A valid packet contains task, inputs, allowed files/surfaces, forbidden actions, evidence requirements, result field, reviewer expectations and what to do if blocked.

Bad packet:

```text
Build onboarding and make sure it works.
```

Good packet:

```text
Worker: Product Face reviewer
Task: verify onboarding UI against Product Face Packet.
Inputs: screenshots, viewport list, acceptance criteria, Product SOT section.
Must check: empty state, loading, error, mobile overflow, first-run path.
Must return: pass/fail, evidence refs, defects, repair recommendation.
Cannot: approve release, change scope, waive backend proof, touch production.
```

## Evidence, readback and Receipt Five

Weak proof:

```text
Tests passed.
```

Strong proof:

```text
The regression test reproduced the reset-password bug before the fix, passed after the fix, and maps to the Product SOT acceptance criterion for password recovery.
```

Weak proof:

```text
Screenshot attached.
```

Strong proof:

```text
Screenshots cover desktop, mobile, loading, empty, error and success states. Console was inspected. The Product Face reviewer found one defect, the worker repaired it, and the second review passed.
```

Receipt Five closes the loop:

1. what was requested;
2. what was done;
3. what evidence proves it;
4. who reviewed it;
5. what remains blocked, risky or explicitly out of scope.

## Human decisions

Human decisions are required for production, mainnet, funds, secrets, budget, release, waiver, residual risk and authority change. Missing readback, stale worker output, missing attachment, unconsumed review and internal repair are not human decisions; they are Factory work.

Bad request:

```text
Can I deploy?
```

Good request:

```text
Decision needed: promote onboarding v2 to staging.
You are approving: deploy version X to staging only.
Evidence: build link, test output, Product Face screenshots, independent review.
Risk remaining: analytics event not yet load-tested.
Approval does not authorize: production, billing, KYC, mainnet, secrets or funds.
If rejected: Factory opens repair work and keeps release blocked.
```

## Status and proof boundaries

local tests prove checkout coherence. They do not prove live Hermes delivery.

The visual map explains the system. It does not prove runtime.

Do not claim public documentation is runtime proof. Do not say local commands prove private product delivery. Do not say a worker result proves done before readback, review and Receipt Five. Do not say generic approval covers production, mainnet, funds or secrets.

## Registry names maintainers actually use

Route classes are the public routing categories in `factory/templates/factory-route-registry.json`; one of them is `product_creation`. Method engines are the execution strategies in `factory/templates/method-engine-registry.json`. Operating-system areas are the owner surfaces in `factory/templates/factory-operating-system-registry.json`. These names matter because worker packets, gates and tests point back to them.

## Security domains

Security-sensitive work can route to specialist domains when needed: networking, linux-systems, web-security, ethical-hacking, security-tools, cloud-security, detection-monitoring, cryptography, security-operations, future-security, supply-chain, onchain-solana-quasar.

## Phase-by-phase operating manual

The sections below are generated from the public workflow catalog and then explained in human terms. This is the real factory flow, not a simplified pitch.


### F0 — Pre-Start / Sealed Source Envelope

#### What actually happens

Factory has a sealed start packet before the production line begins.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Bridge/intake is a handoff boundary, not factory execution. New projects must create a fresh Hermes board through the factory start path.

#### Entry conditions

- operator intent or external signal exists before factory execution

#### Required artifacts

- factory_bridge_source_envelope
- factory_bridge_start_request

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Start Boundary

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- overkill-factory-gerente
- factory-orchestrator

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- seal source envelope
- create start request
- select new_project or existing_project explicitly

#### Blocked actions

- summarize or reinterpret source material in the bridge
- create Hermes board/card directly from bridge
- start without explicit runtime target policy

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.factory_bridge_source_envelope_ref
- card.factory_bridge_start_request_ref
- run.board_binding

#### Completion detection

- sealed source envelope exists
- factory_bridge_start_request exists
- board policy is explicit

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/factory-bridge-source-envelope.schema.json
- factory/schemas/factory-bridge-start-request.schema.json
- factory/schemas/factory-run.schema.json

Commands:
- factoryctl validate-factory-run
- factoryctl validate-card

### F1 — Intake

#### What actually happens

Factory has the input, the chosen interface and the conversational start boundary.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Normalize the input into a route contract without treating user prose as approved scope. The interface profile controls proactive status and briefing attachments.

#### Entry conditions

- user material or intent exists
- primary operator interface is selected

#### Required artifacts

- operator_interface_profile
- factory_start_conversation
- universal_signal_intake
- source_refs
- source_resolution_packet

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Source Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- factory-orchestrator

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- select operator interface
- hold conversational start
- classify intake
- create universal signal intake
- create source resolution packet

#### Blocked actions

- route implementation before source resolution
- create Product SOT from raw input
- require the operator to poll for status

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.operator_interface_profile_ref
- card.factory_start_conversation_ref
- card.universal_signal_intake_ref
- card.source_refs
- card.source_resolution_packet_ref

#### Completion detection

- operator_interface_profile exists
- factory_start_conversation exists
- universal_signal_intake exists
- source_refs is non-empty
- source_resolution_packet exists

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/operator-interface-profile.schema.json
- factory/schemas/factory-start-conversation.schema.json
- factory/schemas/universal-signal-intake.schema.json
- factory/schemas/source-resolution-packet.schema.json

Commands:
- factoryctl operator-interface
- factoryctl start-conversation
- factoryctl validate-signal-intake
- factoryctl source-resolution
- factoryctl validate-card

### F2 — Source Ledger

#### What actually happens

Factory is separating facts, assumptions and gaps, then checking whether it understood the product.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Keep raw extraction private; publish only public-safe refs. The operator confirmation is product understanding, not execution approval.

#### Entry conditions

- intake classified

#### Required artifacts

- source_refs
- product_source_ledger
- operator_understanding_confirmation

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Source Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- source-ledger-worker

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- record claims
- materialize product source ledger
- mark gaps and conflicts
- ask concise operator understanding confirmation

#### Blocked actions

- ask user to reconcile internal source bookkeeping
- create outcome contract or Product SOT before understanding is confirmed

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.source_refs
- card.product_source_ledger_ref
- card.operator_understanding_confirmation_ref

#### Completion detection

- critical claims point to source refs
- product source ledger exists
- operator understanding confirmation is confirmed when Product SOT is required

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/reference-source-registry.schema.json
- factory/schemas/product-source-ledger.schema.json
- factory/schemas/operator-understanding-confirmation.schema.json

Commands:
- factoryctl source-ledger
- factoryctl understanding-confirmation
- factoryctl validate-source-ledger
- factoryctl validate-understanding-confirmation
- factoryctl gate-report

### F3 — Source Resolution

#### What actually happens

Factory is deciding what can be known safely.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Only authority/access/risk questions should reach the user.

#### Entry conditions

- source ledger exists

#### Required artifacts

- discovery_brief

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Discovery Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- source-ledger-worker
- product-sot-planner

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- resolve conflicts
- raise bounded human questions

#### Blocked actions

- turn unresolved gaps into execution scope

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.discovery_brief

#### Completion detection

- open gaps are resolved, blocked or owner-assigned

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/discovery-brief.schema.json

Commands:
- factoryctl help-next

### F4 — Product Outcome And Discovery

#### What actually happens

Factory is turning confirmed understanding into a product outcome.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Outcome is still candidate until Product SOT approval or bounded acceptance. Product creation cannot skip understanding confirmation.

#### Entry conditions

- material outcome is known
- operator understanding is confirmed when Product SOT is required

#### Required artifacts

- operator_understanding_confirmation
- operator_briefing_package
- outcome_contract
- discovery_brief

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Outcome Gate
- Discovery Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- product-sot-planner

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- draft Product SOT candidate

#### Blocked actions

- treat outcome candidate as approved Product SOT
- draft Product SOT before operator understanding confirmation

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.outcome_contract
- card.discovery_brief

#### Completion detection

- operator understanding confirmation exists when needed
- operator briefing package exists for decision artifacts
- outcome, user, problem and success signals exist

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/operator-understanding-confirmation.schema.json
- factory/schemas/operator-briefing-package.schema.json
- factory/schemas/outcome-contract.schema.json
- factory/schemas/discovery-brief.schema.json

Commands:
- factoryctl understanding-confirmation
- factoryctl briefing-package
- factoryctl outcome-contract
- factoryctl validate-outcome-contract
- factoryctl validate-card

### F5 — Product SOT

#### What actually happens

Factory has a candidate source of truth and a deep review package for the product.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: SOT can evolve beyond the input paper; paper is source, not final authority. The operator must not approve from a shallow message when a deep briefing is required.

#### Entry conditions

- outcome and discovery are resolved enough
- operator understanding is confirmed when Product SOT is required

#### Required artifacts

- product_sot
- operator_briefing_package
- full_product_sot_scope_coverage
- factory_phase_lock

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Product SOT Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- product-sot-planner

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- create or update Product SOT
- create Product SOT briefing package
- create full Product SOT scope coverage
- set factory_phase_lock active_frontier=product_sot until material is delivered
- request bounded scope approval only after material is delivered

#### Blocked actions

- execute from paper instead of Product SOT
- ask operator to approve Product SOT from a short chat summary only
- start architecture, repo cleanup, human gate or worker packet while Product SOT owner package is missing

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.product_sot
- card.operator_briefing_package_ref
- card.full_product_sot_scope_coverage
- card.factory_phase_lock

#### Completion detection

- product_sot exists and scope is explicit
- operator briefing package includes markdown and PDF when a decision is needed
- factory_phase_lock.owner_surface_first.product_sot_review_packet_delivered is true before downstream phases
- product_sot.handoff.next_artifact points to full_product_sot_scope_coverage

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/product-sot.schema.json
- factory/schemas/operator-briefing-package.schema.json
- factory/schemas/full-product-sot-scope-coverage.schema.json
- factory/schemas/factory-phase-lock.schema.json
- factory/schemas/user-facing-autonomy-contract.schema.json

Commands:
- factoryctl product-sot
- factoryctl briefing-package
- factoryctl validate-product-sot
- factoryctl full-scope-coverage
- factoryctl validate-full-scope-coverage
- factoryctl help-next

### F6 — Agentic Method Router

#### What actually happens

Factory is choosing the safest production path.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: The router records decisions; it does not hand method selection to the user.

#### Entry conditions

- owner-readable Product SOT review packet exists
- Product SOT candidate exists
- full Product SOT scope coverage exists

#### Required artifacts

- factory_phase_lock
- method_contract

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Method Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- factory-orchestrator

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- select route and required methods
- keep architecture and worker packets frozen until Method Contract is materialized

#### Blocked actions

- ask user to choose internal method machinery
- start architecture or repo cleanup before Method Contract

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.method_contract

#### Completion detection

- selected method, gates, workers and evidence are recorded
- factory_phase_lock can advance only after method_contract is materialized

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/factory-phase-lock.schema.json
- factory/schemas/method-contract.schema.json

Commands:
- factoryctl method-contract
- factoryctl validate-method-contract
- factoryctl gate-report

### F7 — Method Contract

#### What actually happens

Factory has recorded how the work will be produced.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Any omitted method needs a reason, not silence.

#### Entry conditions

- method route chosen
- owner-readable Product SOT review material exists

#### Required artifacts

- factory_phase_lock
- method_contract

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Method Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- factory-orchestrator

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- record required plans, gates and workers

#### Blocked actions

- start implementation with undocumented process choices
- materialize future-phase cards while active frontier is still product_sot or method_contract

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.method_contract

#### Completion detection

- required artifacts and workers are named

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/factory-phase-lock.schema.json
- factory/schemas/method-contract.schema.json

Commands:
- factoryctl validate-card

### F8 — Pack And Product Experience Selection

#### What actually happens

Factory is choosing the capability packs and defining product surfaces, states, experience bar and proof before implementation.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Pack templates are not execution approval. Product-facing work cannot use generic implementation planning as a substitute for Product Experience and Product Face contracts.

#### Entry conditions

- method contract exists

#### Required artifacts

- capability_pack_contract
- product_experience_plan
- product_face_packet
- project_design_system
- professional_design_process
- surface_evidence_profile
- product_delivery_quality_profile

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Pack Gate
- Product Experience Gate
- Surface Pack Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- product-face
- factory-orchestrator

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- match capability packs
- mark missing capabilities
- create Product Experience Plan
- create Product Face Packet
- create Project DESIGN.md contract
- select surface evidence profile

#### Blocked actions

- activate a pack without proof or coverage
- start product-facing implementation before surface state coverage
- treat generic UI proof as Product Experience proof
- move to implementation with unnamed surface pack or proof profile

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.product_experience_plan
- card.product_face_packet
- card.project_design_system
- card.professional_design_process
- card.product_delivery_quality_profile_ref

#### Completion detection

- required surfaces are covered or blocked
- product_experience_plan exists and names surface_pack
- product_face_packet exists and names required states and proof
- project_design_system exists and exports an AI-readable DESIGN.md contract
- surface_evidence_profile or surface_evidence_profiles are declared
- product_delivery_quality_profile_ref or product_delivery_quality_profile is declared
- professional_design_process exists before product-facing implementation

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/capability-pack-contract.schema.json
- factory/schemas/product-experience-plan.schema.json
- factory/schemas/product-face-packet.schema.json
- factory/schemas/project-design-system.schema.json
- factory/schemas/professional-design-process.schema.json
- factory/schemas/product-delivery-quality-profile.schema.json

Commands:
- factoryctl help-next
- factoryctl gate-report
- factoryctl validate-card

### F9 — Risk And Authority Gates

#### What actually happens

Factory will ask only for bounded authority, access or risk decisions.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Human approval must name scope and evidence.

#### Entry conditions

- risk tier and surfaces are known
- factory_phase_lock permits authority review for the current frontier

#### Required artifacts

- access_capability
- budget_contract

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Access Gate
- Budget Gate
- Human Gate when required

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- human-gate-clerk

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- prepare bounded approval requests only for real authority, access, risk, release, funds, secrets or irreversible action

#### Blocked actions

- infer approval from silence
- ask for planning-only continuation approval
- ask for architecture or repo cleanup approval while downstream is frozen

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.access_capability
- card.budget_contract

#### Completion detection

- required authority is granted, blocked or not needed

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/access-capability.schema.json
- factory/schemas/budget-contract.schema.json

Commands:
- factoryctl human-gate-record

### F10 — Security Architecture

#### What actually happens

Factory is planning security before build work.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Security review is not a substitute for architecture.

#### Entry conditions

- material security or privacy risk exists
- Product SOT owner-review material exists
- Method Contract exists
- factory_phase_lock active_frontier is architecture or later

#### Required artifacts

- factory_phase_lock
- security_architecture_plan

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Security Architecture Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- security-orchestrator

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- route specialist security planning

#### Blocked actions

- build material risk before architecture
- start security architecture while Product SOT or Method Contract is still missing

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.security_architecture_plan

#### Completion detection

- controls, threats and reviewers are named

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/factory-phase-lock.schema.json
- factory/schemas/security-architecture-plan.schema.json

Commands:
- factoryctl worker-packet

### F11 — Executable Plans

#### What actually happens

Factory is creating the execution plan.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: The user should see plan status, not internal planning machinery. F11 plans the complete product; F12 independently reviews the coverage before readiness can exist.

#### Entry conditions

- method and required gates are known

#### Required artifacts

- software_development_plan
- spec_graph
- loop_plan
- product_creation_plan

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Ready Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- decomposition-planner

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- create work units, verification plan and Product Creation Plan
- handoff Product Creation Plan to Decomposition Coverage Review before readiness

#### Blocked actions

- execute before plans, coverage review and stop criteria exist
- mark decomposition review as passed from the planner that created the decomposition

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.software_development_plan
- card.spec_graph
- card.loop_plan
- card.product_creation_plan

#### Completion detection

- work units, checks, reviewers, dependencies and rollback are named in Product Creation Plan
- Product Creation Plan handoff points to decomposition_coverage_review
- declared data, metrics, docs and onboarding plans pass strict schema-backed runtime validation

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/software-development-plan.schema.json
- factory/schemas/spec-graph.schema.json
- factory/schemas/loop-plan.schema.json
- factory/schemas/product-creation-plan.schema.json
- factory/schemas/data-metrics-plan.schema.json
- factory/schemas/user-docs-onboarding-plan.schema.json

Commands:
- factoryctl product-creation-plan
- factoryctl help-next

### F12 — Autonomy Readiness

#### What actually happens

Factory is checking whether it can act safely.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Missing access becomes a bounded request, not vague user labor. Decomposition review is independent of the planner and must pass before readiness or dispatch can exist.

#### Entry conditions

- Product Creation Plan exists
- Decomposition Coverage Review is PASS

#### Required artifacts

- decomposition_coverage_review
- product_implementation_readiness
- autonomy_readiness_packet

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Decomposition Coverage Gate
- Access & Capability Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- independent-reviewer
- factory-orchestrator

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- run multi-operator decomposition coverage review from Product Creation Plan
- create Product Implementation Readiness only after Decomposition Coverage Review is PASS
- confirm tools, environment, limits and rollback

#### Blocked actions

- start autonomous work with missing review, access or limits
- let a single reviewer approve the complete decomposition alone
- create Product Implementation Readiness from a failed or missing decomposition coverage review

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.decomposition_coverage_review
- card.product_implementation_readiness
- card.autonomy_readiness_packet

#### Completion detection

- Decomposition Coverage Review exists and is PASS
- every planned work-unit owner and reviewer signs the decomposition coverage matrix with evidence
- Product Implementation Readiness references the PASS Decomposition Coverage Review
- tools, accounts, environment and rollback are ready or blocked

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/decomposition-coverage-review.schema.json
- factory/schemas/product-implementation-readiness.schema.json
- factory/schemas/autonomy-readiness-packet.schema.json

Commands:
- factoryctl decomposition-coverage-review
- factoryctl product-implementation-readiness
- factoryctl gate-report

### F13 — Ready Gate

#### What actually happens

Factory can say whether execution may start.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Gate report must separate factory work from user decisions.

#### Entry conditions

- Product Implementation Readiness exists and references a PASS Decomposition Coverage Review

#### Required artifacts

- gate_report

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Ready Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- factory-orchestrator

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- create required worker tasks when gate passes

#### Blocked actions

- dispatch blocked workers

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- factoryctl gate-report

#### Completion detection

- gate_predicate_result is PASS
- ready worker task materialization is allowed only for reviewed work units

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/gate-report.schema.json

Commands:
- factoryctl gate-report
- factoryctl help-next

### F15 — Runtime Execution

#### What actually happens

Factory is executing through routed workers.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: The user does not manage the worker queue.

#### Entry conditions

- Ready Gate passed

#### Required artifacts

- worker_packets

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Runtime Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- implementation-worker
- qa-verification-worker

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- dispatch required worker packets

#### Blocked actions

- spawn without route readiness

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- .tmp/worker-packets
- Hermes worker tasks

#### Completion detection

- required worker tasks exist in runtime

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/worker-packet.schema.json

Commands:
- factoryctl worker-packet

### F16 — Worker Results

#### What actually happens

Factory is collecting what workers actually proved.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Generated requests are not execution evidence.

#### Entry conditions

- worker packets were executed

#### Required artifacts

- worker_results

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Done Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- evidence-reconciler

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- collect worker result records

#### Blocked actions

- treat packet existence as proof

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- worker result artifacts

#### Completion detection

- required workers returned valid records

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/worker-result.schema.json

Commands:
- factoryctl evidence-record

### F17 — Verification

#### What actually happens

Factory is proving the work with checks.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Verification is scoped to the card and cannot be implied.

#### Entry conditions

- implementation or proof exists

#### Required artifacts

- verification_plan
- verification_result

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Verification Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- qa-verification-worker

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- run named checks and record outputs

#### Blocked actions

- claim done without command evidence

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.verification_plan
- receipt.verification_commands

#### Completion detection

- verification commands and results are attached
- product-facing work has product_face_result with usage_evidence_matrix before completion

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/qa-verification-plan.schema.json

Commands:
- factoryctl validate-completion

### F18 — Independent Review

#### What actually happens

Factory is checking the work with an independent reviewer.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Review may find blockers; it is not ceremony.

#### Entry conditions

- verification evidence exists

#### Required artifacts

- review_result

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Review Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- independent-reviewer

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- route independent review

#### Blocked actions

- allow executor to self-approve

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- worker result artifacts

#### Completion detection

- reviewer is different from executor and result is attached

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/reviewer-selection-plan.schema.json

Commands:
- factoryctl worker-packet

### F20 — Closure Summary

#### What actually happens

Factory is packaging what happened.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Handoff is replayable state, not a chat summary.

#### Entry conditions

- workers, checks and review are complete or blocked

#### Required artifacts

- closure_summary

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Closure Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- handoff-packer

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- summarize delivered work and remaining risk

#### Blocked actions

- hide unresolved blockers in prose

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.closure_summary

#### Completion detection

- closure result and next step are explicit

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/worker-closure-summary.schema.json

Commands:
- factoryctl status-snapshot

### F21 — Receipt Five

#### What actually happens

Factory is preparing the done receipt.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Receipt Five is the durable proof boundary.

#### Entry conditions

- closure summary is ready

#### Required artifacts

- receipt_five

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Done Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- evidence-reconciler

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- reconcile receipt with evidence

#### Blocked actions

- mark done without Receipt Five

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.receipt_five
- receipt artifact

#### Completion detection

- changed, artifacts, commands, review and next action exist
- product-facing receipts include Product Face result evidence refs

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/receipt-five.schema.json

Commands:
- factoryctl validate-completion

### F22 — Completion Audit

#### What actually happens

Factory is checking whether the promised work was actually delivered.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Audit must not inflate contract-level proof into runtime proof.

#### Entry conditions

- receipt exists

#### Required artifacts

- completion_audit

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Completion Audit

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- evidence-reconciler

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- compare required work with delivered work

#### Blocked actions

- close skipped method or evidence requirements

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.completion_audit

#### Completion detection

- audit result is PASS, BLOCKED or PENDING with reasons

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/completion-audit.schema.json

Commands:
- factoryctl validate-completion

### F23 — Production Operations

#### What actually happens

Factory is preparing production operation or blocking release.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Production readiness is stronger than passing tests.

#### Entry conditions

- completion audit allows promotion

#### Required artifacts

- production_readiness_plan

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Release Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- release-ops-worker

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- prepare release, rollback and monitoring

#### Blocked actions

- release without owner, rollback or approval

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.production_readiness_plan

#### Completion detection

- owner, rollback, health checks and approval rule exist

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/production-readiness-plan.schema.json

Commands:
- factoryctl gate-report

### F24 — Release Or Block

#### What actually happens

Factory is ready to release or can explain why not.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Blocked is a valid result when evidence is insufficient.

#### Entry conditions

- production operations plan exists

#### Required artifacts

- release_decision

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Release Gate
- Human Gate when required

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- release-ops-worker
- human-gate-clerk

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- release with authority or block with next action

#### Blocked actions

- promote without production-strict evidence

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- release decision artifact

#### Completion detection

- release or block has owner, evidence and next action

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/gate-report.schema.json

Commands:
- factoryctl help-next

### F25 — Monitoring Support

#### What actually happens

Factory has a support and incident path.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Support is part of production, not afterthought docs.

#### Entry conditions

- release or production block is decided

#### Required artifacts

- incident_support_plan

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Support Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- release-ops-worker

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- activate monitoring or support path

#### Blocked actions

- ship without support owner when support is material

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.incident_support_plan

#### Completion detection

- incident triggers, triage and escalation exist

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/incident-support-plan.schema.json

Commands:
- factoryctl validate-card

### F26 — Learnback

#### What actually happens

Factory is learning from the run without changing critical rules silently.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Critical factory changes require explicit human approval.

#### Entry conditions

- work closed, blocked or released

#### Required artifacts

- factory_learning_proposal

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Learning Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- skill-eval-distiller

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- convert repeated failure into proposal

#### Blocked actions

- auto-activate critical factory changes

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- factory/templates/factory-learning-proposal.json

#### Completion detection

- proposal is accepted, rejected or gated

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/factory-learning-proposal.schema.json

Commands:
- factoryctl validate-card

### F27 — Factory Maturity Audit

#### What actually happens

Factory is auditing its own process gaps.

At this phase the Factory is not doing generic project management. It is transforming the current card into a stricter machine-checkable state. The phase engine looks at the card, the materialized artifacts, the route/method registries, and the available worker evidence. It then decides whether this phase can advance, must block, or must create bounded work inside Hermes.

Maintainer detail: Public repo gets proposals and contracts, not raw evidence.

#### Entry conditions

- learnback exists or repeated blind spot is detected

#### Required artifacts

- factory_maturity_scorecard

These artifacts are not decorative documents. They are the state that later phases read. If one is missing, downstream phases must not pretend the missing state exists.

#### Required gates

- Maturity Gate

A gate is not a polite checkpoint. It is a promotion predicate. If the predicate is not satisfied, the card stays blocked or a repair route is created.

#### Required workers

- skill-eval-distiller

Workers do not receive open-ended intent. They receive a Worker Packet with scope, input, authority, evidence requirements, and a result field. Hermes profiles materialize worker roles, but the Factory decides whether the worker result is consumable.

#### Allowed next actions

- open public-safe improvement issue

#### Blocked actions

- commit raw study or private evidence

These are the anti-theater rules for the phase. If a worker or operator tries to do one of these things, the correct result is not “continue anyway”; it is block, repair, or escalate to the right authority.

#### Output locations read by later phases

- card.factory_maturity_scorecard

#### Completion detection

- blind spots and actions are recorded

Completion detection is where shallow docs usually lie. The Factory does not ask “does it sound complete?” It asks whether the exact fields, artifacts, worker results, gates, and proof refs needed by the next phase are present and consumable.

#### Schemas and commands

Schemas:
- factory/schemas/factory-maturity-scorecard.schema.json

Commands:
- factoryctl status-snapshot


## How a card really advances

A card advances only when the phase engine sees the next required artifact, the relevant gate predicate passes, required workers are either satisfied or not applicable, and the next transition is legal for the current frontier. If any of those are false, the Factory should either create bounded repair work in Hermes or block with a reason.

The no-idle posture does not mean “spam workers until something moves.” It means a blocked card must have an owner, next safe action, freeze scope, and evidence requirement. If the Factory can resolve the blocker without a human, it should. If the blocker is truly human authority, it prepares a decision packet.

## How to debug the Factory

When something looks wrong, inspect in this order:

1. source refs and source ledger;
2. Product SOT and full scope coverage;
3. factory_phase_lock;
4. route and method contract;
5. worker packets created in Hermes;
6. worker results and evidence refs;
7. readback and schema validation;
8. review result and whether it was consumed;
9. human gate packet, if required;
10. Receipt Five and closure summary.

Do not debug from vibes. Debug from fields, gates, worker results and Hermes state.
