# Hermes Integration Architecture

Overkill Factory is separate from Hermes. The factory owns method contracts and
public worker definitions. Hermes owns the runtime floor where cards move.

## Layers

```text
factory card
-> factoryctl validation and gate report
-> worker packet generation
-> Hermes profile binding
-> Hermes Kanban worker card
-> worker result artifact
-> Receipt Five reconciliation
-> done or blocked transition
-> optional operator bridge event
```

## Public Files

| File | Purpose |
| --- | --- |
| `adapters/hermes/README.md` | Human-readable adapter contract and patch notes. |
| `adapters/hermes/patches/0001-overkill-factory-v35-gates-official-main.patch` | Kanban gate patch for Hermes. |
| `adapters/hermes/transition_hook.py` | Transition planning and done-time reconciliation helper. |
| `scripts/factory_bridge.py` | Operator inbox, Codex hook context and handoff helper. |
| `agents/worker-registry.public.json` | Process role registry. |
| `agents/worker-profiles.public.json` | Public agent identity, authority and evidence contract. |
| `agents/hermes-profile-bindings.public.json` | Hermes profile name, skill refs, queue policy and receipt field. |
| `schemas/` | JSON schemas for cards, receipts, worker results and release records. |

## Transition Model

Before `ready`, the adapter should:

- validate the card;
- create a gate report;
- identify required workers;
- create or update worker cards;
- block if required before-ready inputs are missing.

Before `done`, the adapter should:

- inspect required worker results;
- reject missing, failed or stale evidence;
- reject metadata-only `external:kanban-artifact:` evidence unless the worker
  result includes successful downstream `artifact_readback` proof;
- project declared local or scratch completion artifacts into durable attachment
  storage before calling Hermes `complete`, then rewrite receipt refs to durable
  logical refs;
- reject native `kanban-attachment:` refs unless readback proves the attachment
  row, blob, size, SHA-256, parse status and safety checks;
- compare worker results to Receipt Five;
- enforce independent review and human gate requirements;
- return an explicit block reason instead of silently closing.

## No-Idle Invariant

Hermes dispatch remains the only worker scheduler. The factory no-idle layer is
only a board-state controller:

- if `running` exists, it reports active work;
- if `ready` exists, it reports that native Hermes dispatch is the next action;
- if only explicit decision-ready human-gate blockers remain, it returns a
  structured human decision request;
- if the blocker is a missing decision package, PDF/readback, owner-readable
  material or gate artifact, it routes factory-owned repair instead of asking
  the operator for approval;
- if a repair task is dependency-gated by the same blocker it should repair, it
  treats that as a Kanban graph defect and creates a bounded repair route;
- if Solana/onchain planning at F4 or later lacks the Solana AI Kit domain-brain
  record, it routes a factory-owned Solana AI Kit repair before architecture or
  human gates;
- if unfinished work remains without `ready`, `running` or a sole human gate, it
  runs `factoryctl reconcile-board` over the Kanban snapshot and may create
  exactly one deterministic reconcile card for the next artifact selected by the
  phase engine.

This closes silent idle without creating a shadow dispatcher or bypassing gates.
The primary runtime shape should still be a durable Hermes Kanban graph created
at project start: backbone cards, explicit dependencies, typed blockers and
bounded expander cards. No-idle is the integrity auditor that notices when the
graph is missing, stale or inconsistent; it is not the normal source of new
factory route authority.

The no-idle layer must not ask for a human gate when the board reconciler says
`phase_engine.human_gate_allowed=false`; it must create or repair the next
factory-owned artifact instead.

With current Hermes Kanban typed block reasons, no-idle also preserves the
native block semantics:

- `dependency_wait` is reported as dependency wait, not as a human decision;
- `block_loop_detected` routes deterministic triage after repeated same-cause
  blocks instead of re-blocking forever;
- `needs_input` may reach the operator only through a delivered decision package;
- `capability` and `transient` stay factory-owned unless a separate delivered
  human gate exists.

## Kanban Workflow Binding

Factory-created Hermes tasks should carry the native workflow fields exposed by
Hermes Kanban:

- `workflow_template_id=overkill-vfinal`;
- `current_step_key=F...` from the deterministic phase engine.

The adapter writes those columns directly when the installed Hermes SQLite
schema contains them. The task body also carries `kanban_workflow_binding` as a
fallback when a Hermes installation or remote API does not expose those
columns. Agents may read those fields, but they do not get to choose them.

## Gate Timing Classes

| Gate timing | Meaning |
| --- | --- |
| `blocking-before-ready` | The main card should not become ready until this planning or gate input exists. |
| `blocking-before-done` | The main card may be ready, but cannot close until the worker result exists. |
| `advisory-review` | Useful review path that becomes blocking only when the card contract requires it. |

Gate timing is computed by `factoryctl.worker_gate_timing_class`; the binding
records semantic policy, not a second dispatch source of truth. Hermes Kanban
owns runtime queueing, dependencies, worker lifecycle and durable state.

## Evidence Boundary

The adapter may create worker tasks and transition plans. It does not fake:

- security scan results;
- Auditor reports;
- Product Face screenshots or state matrices;
- QA results;
- independent review;
- human approval;
- release or rollback proof.

Those must come from the worker that actually ran.

## Operator Bridge

Hermes may call `transition_hook.py` with `--operator-inbox` so blocked
transitions or operator-facing state changes become durable bridge events under
`.tmp/factory-runs/operator-inbox/`.

The transition hook must not turn every blocked transition into a user page.
Generic transition blocks are `transient` repair/triage notices, dependency
blocks are dependency waits, capability blocks go through capability
acquisition, and only `needs_input` becomes an operator decision request.

The bridge is a view and response channel. It is not a worker, not a human gate
record and not a second source of truth. Codex hooks can read this inbox on
`SessionStart` or `UserPromptSubmit` to brief the operator after Codex was
closed.

## First Integration Path

1. Run local repository validation.
2. Generate a gate report from `examples/minimal-hermes-project/card.md`.
3. Preview Hermes profile materialization.
4. Apply the adapter patch in a test Hermes checkout.
5. Wire Hermes transition events to `transition_hook.py`.
6. Prove one card reaches `ready` only after required before-ready gates.
7. Prove `done` blocks until current worker results and Receipt Five agree.

Only after that should you use the factory for a real product card.
