# Hermes Kanban Transition Hook Integration

This note defines the required installed-Hermes integration for Overkill
Factory vFinal.

It is public-safe and does not describe any private runtime.

## Verdict

Shell hooks are not enough for Factory gates.

Hermes shell hooks can block or observe agent/tool events such as
`pre_tool_call`, `pre_llm_call` and gateway dispatch. They do not, by
themselves, guarantee that every Kanban transition calls the Factory gate.

Factory vFinal needs a Kanban transition hook.

The hook must run at the same decision point used by CLI, dashboard, API and
worker routes. Otherwise one interface may enforce gates while another bypasses
them.

## Required Decision Points

The installed runtime must call the Overkill transition hook before:

- a card moves toward `ready`;
- a card moves toward `done`.
- a card is born directly in `ready`;
- an automatic recompute would move a card into `ready`.

The preferred integration point is the shared Kanban state layer, not a
CLI-only wrapper.

At minimum, the implementation must protect the shared equivalents of:

- `promote_task`: before a task becomes `ready`;
- `complete_task`: before a task becomes `done`.
- `create_task`: before a Factory task is created in `ready`;
- `recompute_ready`: before dependency completion auto-promotes a Factory task.

## Candidate Hermes v0.16 Patch

The public candidate patch is:

```text
adapters/hermes/patches/0002-add-overkill-vfinal-kanban-transition-hook.patch
```

The patch is opt-in. It only runs when:

```text
OVERKILL_FACTORY_KANBAN_GATE=1
OVERKILL_FACTORY_ADAPTER_ROOT=/path/to/overkill-factory
```

Optional runtime paths:

```text
OVERKILL_FACTORY_RUNTIME_DIR=/path/to/runtime-artifacts
OVERKILL_FACTORY_WORKER_RESULTS_DIR=/path/to/worker-results
OVERKILL_FACTORY_HOOK_TIMEOUT_SECONDS=30
```

The patch calls `adapters/hermes/kanban_event_bridge.py` before direct `ready`
creation, automatic ready recompute, manual `promote_task`, `unblock_task` to
`ready` and `complete_task` transitions. It records allow/block transition
events and returns a blocked transition instead of silently allowing weak
Factory cards forward.

Validated patch-level evidence:

```text
validation/hermes-v016-transition-patch/patch-apply-receipt.json
```

That receipt proves the patch file is public-safe, applies cleanly to a clean
Hermes v0.16 `kanban_db.py`, and the patched file compiles.

It does not yet prove production readiness. A disposable installed-Hermes
CLI/Kanban smoke now proves the main state transitions in an isolated installed
runtime, including positive `ready`, positive `done` and patch reversal
rollback. Later receipts prove dashboard `ready` parity, worker-result
ingestion, real child-process local-stub worker completion across all 23
workers, dashboard `done` parity, and a disposable rollback-by-release-restore
drill. Remaining dashboard/API/worker parity, non-stub model/tool-auth proof,
autonomous specialist quality and production service-manager rollback/monitoring
still need explicit proof.

## Required Inputs

The transition hook needs:

- the factory card body;
- current status;
- target status;
- worker ledger path;
- Receipt Five path or metadata when moving to `done`;
- worker-result artifact directory when moving to `done`;
- board/task identifiers for evidence and idempotency.

If the card body is not a Factory card, the hook must no-op and preserve normal
Hermes behavior.

If the card is a Factory card and required inputs are missing, the hook must
return `block_transition`.

## Required Behavior Before Ready

When a Factory card moves toward `ready`, Hermes must:

- parse the card body;
- call `adapters/hermes/transition_hook.py`;
- persist or update the worker ledger;
- create or update real Hermes worker subtasks from ledger rows;
- block `ready` when the hook returns `block_transition`;
- record the blocked reason as a durable event/comment;
- avoid duplicate subtasks on retry.

## Required Behavior Before Done

When a Factory card moves toward `done`, Hermes must:

- load Receipt Five;
- load worker results;
- call `adapters/hermes/transition_hook.py`;
- block `done` when any required result is missing or invalid;
- allow `done` only when Receipt Five and worker results agree;
- record the reconciliation summary in durable evidence.

## Required Tests

The installed runtime smoke must prove:

- before-ready block for missing security/access/autonomy evidence;
- direct `ready` creation cannot bypass the gate;
- automatic recompute to `ready` cannot bypass the gate;
- manual unblock-to-ready cannot bypass the gate;
- a complete card can pass `ready`;
- before-ready worker ledger creation for a ready vFinal card;
- retry does not duplicate worker subtasks;
- Control Tower work blocks without owner-interface evidence;
- before-done blocks without required worker results;
- before-done allows with Receipt Five plus valid worker results;
- CLI, dashboard, API and worker routes return the same decision.

## Non-Goal

Do not use a shell hook as the production gate for Kanban transitions.

A shell hook may be useful as an extra guard for agent terminal actions, but it
is not the canonical transition gate.
