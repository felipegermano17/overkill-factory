# Parallel Execution And Status

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `scripts/factoryctl.py`, `schemas/parallel-lane-contract.schema.json`,
> `schemas/factory-status-snapshot.schema.json`, Hermes runtime state.
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

## Cascade Operating Protocol

Use a named-lane sweep:

1. List active lanes from oldest to newest.
2. Stop or mark superseded lanes that lost their source, budget or objective.
3. Reconcile lane outputs before any merge, card update or receipt claim.
4. Prefer one synthesizer over lane-by-lane self-approval.
5. Keep cleanup explicit: branch/worktree, generated output and stale evidence.

No merge happens by title, summary or agent confidence alone.

## Status Snapshot

`factory_status_snapshot` is a cockpit projection. It is not a source of truth.
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
factoryctl status-snapshot --card examples/minimal-hermes-project/card.md --out .tmp/factory-status-snapshot.json
```

Add lane contracts or evidence refs when applicable:

```bash
factoryctl status-snapshot \
  --card examples/minimal-hermes-project/card.md \
  --lane-contract templates/parallel-lane-contract.json \
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
