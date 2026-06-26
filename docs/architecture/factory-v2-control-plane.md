# Factory V2 Control Plane

> Document status: CURRENT ARCHITECTURE.
> Current authority: `scripts/factory_v2_kernel.py`, `scripts/factoryctl.py`,
> `docs/factory-workflow.catalog.json`, `schemas/factory-*.schema.json`,
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
| Workflow compiled plan | Converts `docs/factory-workflow.catalog.json` into ordered phases, allowed commands and blocked actions. | `schemas/factory-workflow-compiled-plan.schema.json`, `templates/factory-workflow-compiled-plan.json`, `factoryctl compile-workflow` |
| Factory command | The only shape accepted for proposed state changes. | `schemas/factory-command.schema.json`, `templates/factory-command.json`, `factoryctl validate-factory-command` |
| Factory run event | Append-only event record with hash chaining. | `schemas/factory-run-event.schema.json`, `templates/factory-run-event.json`, `factoryctl validate-factory-event-log` |
| Factory run | Runtime binding for a run, including explicit Hermes target, command inbox, event log, decision outbox and promotion packets. | `schemas/factory-run.schema.json`, `templates/factory-run.json`, `factoryctl validate-factory-run` |
| Decision outbox | Human decisions that the factory needs but cannot auto-resolve. | `schemas/factory-decision-outbox.schema.json`, `templates/factory-decision-outbox.json`, `factoryctl validate-decision-outbox` |
| Promotion packet | Evidence required before phase, product or release promotion. | `schemas/factory-promotion-packet.schema.json`, `templates/factory-promotion-packet.json`, `factoryctl validate-promotion-packet` |
| Phase graph | Canonical V2 taxonomy: product phases stay linear; human gates and operator projections are events/views, not phases. | `schemas/factory-phase-graph.schema.json`, `templates/factory-phase-graph.json`, `factoryctl validate-phase-graph` |
| V2 study traceability | No-simplification ledger that binds raw V2 study claims to schemas, runtime commands, tests and negative fixtures. | `schemas/v2-study-traceability.schema.json`, `templates/v2-study-traceability.json`, `factoryctl validate-v2-study-traceability` |
| Worker authority contract | Makes worker profiles operational only; route, gate, waiver and promotion authority stay in reducers and registries. | `schemas/worker-authority-contract.schema.json`, `templates/worker-authority-contract.json`, `factoryctl validate-worker-authority-contract` |
| Product Experience control plane | Governs design, brand, frontend, operator UX and Product Face as first-class product surfaces. | `schemas/product-experience-control-plane.schema.json`, `templates/product-experience-control-plane.json`, `factoryctl validate-product-experience-control-plane` |
| Capability acquisition contract | Requires reference search, template match, create/install attempt and smoke/eval before missing capability can block. | `schemas/capability-acquisition-contract.schema.json`, `templates/capability-acquisition-contract.json`, `factoryctl validate-capability-acquisition-contract` |
| Hermes reducer mutation proof | Proves bridges and adapters cannot become the Kanban mutation authority. | `schemas/hermes-reducer-mutation-proof.schema.json`, `templates/hermes-reducer-mutation-proof.json`, `factoryctl validate-hermes-reducer-mutation-proof` |
| Readiness claim | Separates kernel-ready, runtime-ready, product-run-ready and production-proven claims. | `schemas/factory-v2-readiness-claim.schema.json`, `templates/factory-v2-readiness-claim.json`, `factoryctl validate-readiness-claim` |
| Reference superiority claim | Public-safe way to claim the factory is stronger than a reference, tied to schema, reducer and test proof. | `schemas/reference-superiority-claim.schema.json`, `templates/reference-superiority-claim.json` |

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
factoryctl validate-worker-authority-contract templates/worker-authority-contract.json
factoryctl validate-product-experience-control-plane templates/product-experience-control-plane.json
factoryctl validate-capability-acquisition-contract templates/capability-acquisition-contract.json
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
