# Factory V2 Control Plane

> Document status: CURRENT ARCHITECTURE.
> Current authority: `scripts/factory_v2_kernel.py`, `scripts/factoryctl.py`,
> `legacy-docs/factory-workflow.catalog.json`, `schemas/factory-*.schema.json`,
> `templates/factory-*.json` and `tests/test_factory_v2_kernel.py`.
> Runtime boundary: Hermes Kanban remains the runtime source of truth for real
> cards, workers, comments and transitions. Factory V2 controls how state may
> advance; it does not replace Hermes.

Factory V2 turns the factory method into a deterministic control plane.

The point is simple: agents can produce work, but agents cannot choose the
factory route from memory, chat context or card prose. The route is compiled,
commands are validated, events are hashed, human decisions sit in a decision
outbox, and promotion needs a packet with evidence.

## What V2 Adds

| Contract | Purpose | Public files |
| --- | --- | --- |
| Workflow compiled plan | Converts `legacy-docs/factory-workflow.catalog.json` into ordered phases, allowed commands and blocked actions. | `schemas/factory-workflow-compiled-plan.schema.json`, `templates/factory-workflow-compiled-plan.json`, `factoryctl compile-workflow` |
| Factory command | The only shape accepted for proposed state changes. | `schemas/factory-command.schema.json`, `templates/factory-command.json`, `factoryctl validate-factory-command` |
| Factory run event | Append-only event record with hash chaining. | `schemas/factory-run-event.schema.json`, `templates/factory-run-event.json`, `factoryctl validate-factory-event-log` |
| Factory run | Runtime binding for a run, including explicit Hermes target, command inbox, event log, decision outbox and promotion packets. | `schemas/factory-run.schema.json`, `templates/factory-run.json`, `factoryctl validate-factory-run` |
| Decision outbox | Human decisions that the factory needs but cannot auto-resolve. | `schemas/factory-decision-outbox.schema.json`, `templates/factory-decision-outbox.json`, `factoryctl validate-decision-outbox` |
| Promotion packet | Evidence required before phase, product or release promotion. | `schemas/factory-promotion-packet.schema.json`, `templates/factory-promotion-packet.json`, `factoryctl validate-promotion-packet` |
| Phase graph | Canonical V2 taxonomy: product phases stay linear; human gates and operator projections are events/views, not phases. | `schemas/factory-phase-graph.schema.json`, `templates/factory-phase-graph.json`, `factoryctl validate-phase-graph` |
| V2 study traceability | No-simplification ledger that binds raw V2 study claims to bounded truth levels, evidence refs, claim boundaries, known gaps and next actions. | `schemas/v2-study-traceability.schema.json`, `templates/v2-study-traceability.json`, `factoryctl validate-v2-study-traceability` |
| V2 doc implementation obligations | Fails validation when documented V2 obligations are overclaimed as implemented without matching public artifacts, tests and fixture proof. | `schemas/v2-doc-implementation-obligations.schema.json`, `templates/v2-doc-implementation-obligations.json`, `factoryctl validate-v2-doc-implementation-obligations` |
| Worker authority contract | Makes worker profiles operational only; route, gate, waiver and promotion authority stay in reducers and registries. | `schemas/worker-authority-contract.schema.json`, `templates/worker-authority-contract.json`, `factoryctl validate-worker-authority-contract` |
| Profile compatibility aliases | Keeps legacy names explicit and expirable instead of letting old worker ids become hidden authority. | `schemas/profile-compatibility-alias.schema.json`, `agents/profile-compatibility-aliases.public.json`, `factoryctl validate-agent-skill-boundaries` |
| Skill provider registry | Resolves every Hermes `skill_refs` entry to a provider so skills are capability, not process authority. | `schemas/skill-provider-registry.schema.json`, `agents/skill-provider-registry.public.json`, `templates/skill-ref-resolution-report.json`, `factoryctl validate-agent-skill-boundaries` |
| Product Experience control plane | Governs design, brand, frontend, operator UX and Product Face as first-class product surfaces. | `schemas/product-experience-control-plane.schema.json`, `templates/product-experience-control-plane.json`, `factoryctl validate-product-experience-control-plane` |
| Product Experience evidence stack | Requires brand strategy, identity system, component registry, accessibility, visual regression and Storybook-equivalent proof for product-facing work. | `schemas/brand-strategy.schema.json`, `schemas/identity-system.schema.json`, `schemas/component-registry.schema.json`, `schemas/accessibility-report.schema.json`, `schemas/visual-regression-proof.schema.json`, `schemas/storybook-equivalent-catalog.schema.json` |
| Capability acquisition lane | Searches providers, packs and reference sources, writes a `capability_acquisition_run`, and blocks only after completed search. | `schemas/capability-acquisition-run.schema.json`, `templates/capability-acquisition-run.json`, `factoryctl capability-acquisition-run`, `factoryctl validate-capability-acquisition-run` |
| Hermes typed block policy | Maps every blocked state to native Hermes `dependency`, `needs_input`, `capability` or `transient`, with dependency auto-resume and loop escalation. | `schemas/hermes-typed-block-policy.schema.json`, `templates/hermes-typed-block-policy.json`, `factoryctl validate-v2-runtime-contracts` |
| Hermes reducer mutation proof | Proves bridges and adapters cannot become the Kanban mutation authority. | `schemas/hermes-reducer-mutation-proof.schema.json`, `schemas/hermes-blocked-first-protocol-receipt.schema.json`, `templates/hermes-reducer-mutation-proof.json`, `factoryctl validate-v2-runtime-contracts` |
| Operator delivery OS | Requires channel-aware delivery receipts before asking the operator for a human decision. | `schemas/operator-delivery-receipt.schema.json`, `schemas/operator-notification-policy.schema.json`, `schemas/operator-channel-pack.schema.json`, `factoryctl validate-v2-runtime-contracts` |
| Security OS matrix | Makes security route, state, capability broker, capability leases and security profiles explicit before material work. | `schemas/security-route-contract.schema.json`, `schemas/security-state-ledger.schema.json`, `schemas/capability-broker.schema.json`, `schemas/capability-lease.schema.json`, `schemas/security-profile.schema.json` |
| Readiness claim | Separates kernel-ready, runtime-ready, product-run-ready and production-proven claims. | `schemas/factory-v2-readiness-claim.schema.json`, `templates/factory-v2-readiness-claim.json`, `factoryctl validate-readiness-claim` |
| Reference superiority harness | Public-safe way to claim the factory is stronger than a reference, tied to negative fixtures and a runner. | `schemas/reference-derived-negative-fixture.schema.json`, `fixtures/v2/reference-derived-negative-fixtures.json`, `factoryctl validate-reference-superiority` |

## Invariants

Factory V2 fails closed on these rules:

- A status, question, decision, change, exception or handoff request must resolve
  an explicit runtime target before reading Hermes state.
- A bridge cannot create Hermes boards, create Hermes cards, dispatch workers,
  close gates, approve human gates or promote work.
- A new product start uses `factory_must_create_new_board`; an existing project
  must provide an explicit `kanban:`, `hermes:`, `run:` or `board:` reference.
- A formal human gate response requires `human_gate_record_ref`; chat text alone
  is not a gate record.
- `request_decision` is generated only by explicit human/approval gates, not by
  planning, understanding confirmation or operator briefing text.
- Event logs require contiguous sequence numbers, correct previous hashes and
  correct event hashes.
- Product or release promotion requires Receipt Five, completion audit, release
  readiness, rollback, monitoring and human gate record when scope requires it.
- `.tmp/factory-runs` is runtime evidence, not public release surface.

## Hermes Kanban Compatibility

Factory V2 now treats current Hermes Kanban primitives as the runtime lane:
`gateway start`, `kanban dispatch`, `kanban watch`, `kanban tail`,
`kanban runs`, `kanban diagnostics`, `kanban notify-list` and
`kanban notify-unsubscribe`.

That matters because Overkill Factory should not create a shadow dispatcher.
The factory owns contracts, gates, route decisions, receipts and validation.
Hermes owns durable cards, workers, runs, comments, transitions and native
dispatch behavior. Direct `kanban notify-subscribe` is not the operator UX path
for the factory: raw events may feed the manager, but the selected manager
profile is the only human-facing voice.

Factory V2 also uses Hermes typed block reasons as a hard runtime contract:

- `dependency` is a native Kanban wait state: it stays in TODO, does not page
  the operator, and auto-resumes when the parent completes.
- `needs_input` is the only typed block that may page the operator, and only
  after a complete operator delivery/decision package exists.
- `capability` means a provider, profile, model, skill or access capability is
  missing after capability acquisition has completed.
- `transient` means runtime/readback/repair/anti-spawn safety hold; it must
  retry or route repair and must not become a generic human gate.

Repeated same-cause blocks use Hermes `block_loop_detected` after recurrence
limit 2. The factory treats that as deterministic triage/repair, not as another
round of the same block and not as an operator approval question.

## Phase Cards And Native Dependencies

Each project should load the factory rail as visible Hermes Kanban cards at the
start of the run. Those cards are not a decorative checklist and they are not
agent memory. They are the durable rail that makes the next allowed phase
visible.

Hermes `parent -> child` links are execution dependencies, not visual nesting.
If phase F15 creates required work-unit cards, the closure/advance card for the
next phase must carry those work-unit cards as parents. The next phase can only
be promoted after the required parents are `done` or otherwise terminal by
contract. If a required child card is discovered later, it must be linked while
the next phase is still `todo`. If the next phase is already `ready`, `running`
or `done`, that is a factory invariant violation, not something an agent may
explain away.

This keeps modular/adaptive work Kanban-native: known work can be born when a
phase opens, unknown work can be born when the method deterministically discovers
it, and the phase rail still advances through Hermes dependencies instead of a
sidecar scheduler.

## CLI Proof

Compile and validate the control plane:

```bash
factoryctl compile-workflow --out .tmp/factory-workflow-compiled-plan.json
factoryctl validate-workflow-compiled-plan .tmp/factory-workflow-compiled-plan.json
factoryctl validate-factory-command templates/factory-command.json
factoryctl validate-factory-event-log templates/factory-run-event.json
factoryctl validate-decision-outbox templates/factory-decision-outbox.json
factoryctl validate-promotion-packet templates/factory-promotion-packet.json
factoryctl validate-factory-run templates/factory-run.json
factoryctl validate-phase-graph templates/factory-phase-graph.json
factoryctl validate-v2-study-traceability templates/v2-study-traceability.json
factoryctl validate-v2-doc-implementation-obligations templates/v2-doc-implementation-obligations.json --traceability templates/v2-study-traceability.json
factoryctl validate-v2-runtime-contracts
factoryctl validate-agent-skill-boundaries
factoryctl validate-reference-superiority
factoryctl validate-worker-authority-contract templates/worker-authority-contract.json
factoryctl validate-product-experience-control-plane templates/product-experience-control-plane.json
factoryctl validate-capability-acquisition-contract templates/capability-acquisition-contract.json
factoryctl capability-acquisition-run --capability-gap solana-ai-kit --surface solana --out .tmp/factory-runs/capability/v2-control-plane-capability-run.json
factoryctl validate-capability-acquisition-run .tmp/factory-runs/capability/v2-control-plane-capability-run.json
factoryctl validate-hermes-reducer-mutation-proof templates/hermes-reducer-mutation-proof.json
factoryctl validate-readiness-claim templates/factory-v2-readiness-claim.json
```

Run the focused regression suite:

```bash
python -m unittest tests.test_factory_v2_kernel tests.test_factory_bridge tests.test_factory_board_reconciler -q
```

## Why This Matters

V1 added many gates, workers, templates and runtime checks. The hard lesson was
that too much route authority still lived in agent instructions and local
context. V2 moves that authority into replayable contracts:

- the catalog says what phases exist;
- the compiled plan says which commands each phase accepts;
- commands propose changes;
- events record accepted or rejected transitions;
- the decision outbox names real human decisions;
- promotion packets prove that completion is not just prose.

That is the professional boundary: agents operate inside the factory, while the
factory control plane decides whether the state can advance.
