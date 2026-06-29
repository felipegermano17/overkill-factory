# Deterministic Control Plane

Document status: CURRENT SUPPORTING GUIDE
Current authority: scripts/factoryctl.py, schemas/, tests/
Runtime boundary: Hermes Kanban remains the durable runtime. The factory
control plane computes whether Hermes may create, release or dispatch work.

## Operating Mantra

Every factory runtime change should make the system less mirabolante, more
Kanban-native, more Hermes-native, more deterministic and easier to trust.

When solving an autonomy or performance problem, prefer a durable Kanban graph,
explicit dependencies, typed blocks and native Hermes dispatch before adding a
new sidecar controller, polling loop, agent memory rule or chat-level
interpretation. `no-idle` exists as an integrity auditor and recovery path; it
must not become the main engine that invents the production line after the board
has already gone silent.

Overkill Factory must not let an agent choose the next phase, worker, gate or
transition from memory, chat, title, prose or declared phase alone. The runtime
path is:

1. Hermes exposes board state.
2. `factoryctl build_board_reconcile_plan` computes the next allowed action.
3. The Hermes adapter follows only that plan.
4. Native Hermes dispatch runs only when the plan action is `dispatch_ready`.

## Hard Rules

- A `ready` task without structured phase binding is not dispatchable.
- A future phase cannot run while an earlier structured phase is blocked.
- Human gates require a complete `human_gate_packet` before the operator is
  asked for a decision.
- Text-only approval prose is not a human gate.
- Solana/onchain F4+ work requires the Solana AI Kit provider record or a valid
  Solana AI Kit usage receipt before execution.
- Bridge/plugin code never closes gates, approves decisions or acts as a worker.

## Required Binding

Every runtime task that can be dispatched by Hermes must carry at least one
structured phase source:

- native `current_step_key`;
- native `workflow_template_id`;
- body `kanban_workflow_binding.current_step_key`;
- body `phase_engine.computed_phase_id`;
- a canonical factory card whose strict phase engine can compute the frontier.

Plain `phase` text is not enough.

## Adapter Boundaries

`adapters/hermes/live_kanban_adapter.py dispatch` performs a reconcile preflight
before calling `hermes kanban dispatch --json`. If the plan action is not
`dispatch_ready`, native dispatch is skipped and the plan is returned for repair
or operator handling.

`no-idle` reads the same reconcile plan before legacy no-idle classification.
Complete human/operator gates may still surface to the operator, but incomplete
or text-only gates become deterministic repair work.

`materialize-bridge-start` may create the fresh start board/card through the
factory adapter path, but the bridge itself does not release, dispatch, approve
or close gates.

## Regression Fixtures

Incident replay fixtures under `fixtures/incidents/` pin the failures that must
not return:

- F3 blocked while F4 ready;
- text-only human gate;
- Solana F4+ work without Solana AI Kit provider.

The public test suite replays them through the reconciler.
