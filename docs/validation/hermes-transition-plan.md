# Hermes Transition Plan Validation

This note defines what the public validation fixtures prove and what they do not
prove yet.

## What The Fixtures Prove

The transition-plan schema and hook result fixtures can represent two separate
runtime decisions:

- moving a card toward `ready`;
- moving a card toward `done`.

For `ready`, the fixture shows a plan with:

- `transition_action: allow_and_create_worker_tasks`;
- one `worker_subtask` per required worker;
- a `queue_class` for each subtask;
- a `required_before` value;
- the worker packet the runtime should hand to the worker;
- the expected Receipt Five field for the worker result.

For `done`, the fixture shows:

- `transition_action: block_transition` when required results are missing;
- `completion_reconciliation` listing required workers;
- per-worker satisfaction status;
- missing blocking workers;
- evidence refs when a result exists.

That means the model can distinguish planning, execution requests and closure
evidence. It avoids the common failure where a generated worker packet is
mistaken for proof that the worker already ran.

The hook fixtures under `validation/hermes-hook/` additionally prove:

- the runtime can persist an idempotent worker ledger;
- retrying the same transition does not create duplicate task ids;
- a blocked `done` transition exposes missing worker results;
- `--enforce` can make blocked transitions fail at process level.

## Required Runtime Behavior

A real Hermes integration should implement this sequence:

```text
ready event
-> call adapters/hermes/transition_hook.py
-> persist or update worker ledger rows
-> map ledger rows to Hermes subtasks by queue class
-> allow ready only when before-ready blockers are satisfied

done event
-> call adapters/hermes/transition_hook.py with Receipt Five and worker results
-> reconcile expected Receipt Five fields and worker result artifacts
-> block missing or weak evidence
-> allow done only after Receipt Five and worker evidence agree
```

## What Still Needs Live Proof

The current public repository has schemas, examples, validation results and an
executable transition hook. It does not yet prove live Hermes orchestration
inside an installed runtime.

Still needed:

- Hermes Kanban event wiring before `ready`;
- Hermes Kanban event wiring before `done`;
- mapping hook ledger rows to real Hermes subtasks;
- queue routing for `blocking-before-ready`, `blocking-before-done` and
  `advisory-review`;
- worker result ingestion into card metadata, Receipt Five or both;
- enforcement parity across CLI, dashboard, API and worker routes;
- blocked-state messages that identify the missing input or missing evidence;
- disposable runtime smoke with a public-safe card.

## Pass Criteria For The Next Smoke

The next Hermes smoke should pass only when:

- a public-safe card moving toward `ready` creates the expected worker subtasks;
- retrying the same transition does not duplicate subtasks;
- before-ready blockers prevent `ready`;
- before-done worker tasks do not prevent `ready`, but do prevent weak `done`;
- partial worker results produce a blocked done reconciliation;
- completed worker results plus complete Receipt Five produce `allow_done`;
- CLI, dashboard and API paths return the same decision.
