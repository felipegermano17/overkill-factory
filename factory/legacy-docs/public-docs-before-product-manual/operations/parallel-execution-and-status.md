# Parallel Execution And Status

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `factory/scripts/factoryctl.py`, `factory/schemas/parallel-lane-contract.schema.json`,
> `factory/schemas/factory-status-snapshot.schema.json`, Hermes runtime state.
> Runtime boundary: this guide defines public contracts. Hermes or the operator's
> runtime remains the source of truth.

## Parallel Decision Ladder

Default to the minimum viable parallelization:

1. Single lane for small, sequential or high-ambiguity work.
2. Read-only fork for research, audit, source intake or critique.
3. Two-agent split when one lane can plan/review while another executes.
4. Three to four bounded lanes only when write scopes are separable and a
   synthesizer is named.
5. Larger fan-out only with explicit budget, active-lane cap and approval.

Parallelism is a cost and conflict decision. It is not a default throughput
button.

## Lane Contract

Every parallel lane needs a `parallel_lane_contract` before it can affect the
canonical card, repository, release branch or Receipt Five.

Required fields include:

- lane id and objective;
- read scope and write scope;
- branch or worktree ref;
- owner agent and reviewer or synthesizer;
- expected artifact;
- timeout, token/cost budget and stop condition;
- conflict risk;
- merge/reconciliation policy with `no_self_promotion=true`;
- cleanup policy for stale, failed or superseded lanes.

Editing lanes need a worktree or branch ref different from the base ref. Read-only
lanes may use the base ref, but their output still requires synthesis before it
changes canonical state.

## Hermes Delegation Modes

Hermes Kanban tasks are the durable factory lanes. Hermes `delegate_task`
subagents are auxiliary execution lanes: useful for bounded research, review,
candidate repair plans or parallel analysis, but not authoritative state.

Use the modes this way:

- `delegate_task` synchronous: bounded helper work inside the parent turn. The
  parent still reconciles the answer before card, Receipt Five or release state
  changes.
- `delegate_task(background=true)`: a `background_subagent_lane`. It needs
  `delegation_id`, parent card/worker ids, toolsets, public-safe context,
  retry/supersession policy, candidate evidence refs and a named reconciliation
  owner.
- Hermes Kanban card/task: durable work that can block, retry, receive worker
  packets, produce worker results and participate in Receipt Five.

A background subagent lane is candidate-only until `delegation_status=reconciled`
and `accepted_by_worker_result_ref` points to the worker result that accepted it.
`completed` is not enough. `failed`, `cancelled`, `stale`, `superseded` and
`rejected` cannot unblock anything. Background output cannot approve human gates,
move canonical Kanban state, publish public artifacts, or directly satisfy
Receipt Five.

## Cascade Operating Protocol

Use a named-lane sweep:

1. List active lanes from oldest to newest.
2. Stop or mark superseded lanes that lost their source, budget or objective.
3. Reconcile lane outputs before any merge, card update or receipt claim.
4. Prefer one synthesizer over lane-by-lane self-approval.
5. Keep cleanup explicit: branch/worktree, generated output and stale evidence.

No merge happens by title, summary or agent confidence alone.

## Status Snapshot

`factory_status_snapshot` is a operator console projection. It is not a source of truth.
It links back to card, gate, lane and evidence refs so another operator can
continue without reading chat history.

A snapshot must show:

- current phase and state;
- gate status and blockers;
- active workers and lanes;
- evidence refs and Receipt Five status;
- whether work is implemented, validated, integrated, released, blocked or
  superseded;
- next safe actions and forbidden actions;
- staleness warning.

Generate a local snapshot with:

```bash
factoryctl status-snapshot --card factory/examples/minimal-hermes-project/card.md --out .tmp/factory-status-snapshot.json
```

Add lane contracts or evidence refs when applicable:

```bash
factoryctl status-snapshot \
  --card factory/examples/minimal-hermes-project/card.md \
  --lane-contract factory/templates/parallel-lane-contract.json \
  --evidence-ref external:operator-summary \
  --out .tmp/factory-status-snapshot.json
```

The snapshot must fail closed when source refs are missing, stale state claims
ready/released, blocked gate state has no blockers, next action is missing or
public/private boundary flags are false.

## Receipt Five

Receipt Five should mention the lane outputs that actually affected the final
decision and the reconciliation decision that accepted, rejected or superseded
them. Do not attach stale or failed lane output as completion proof.
