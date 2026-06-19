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
- compare worker results to Receipt Five;
- enforce independent review and human gate requirements;
- return an explicit block reason instead of silently closing.

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
