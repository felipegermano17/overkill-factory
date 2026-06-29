# Operator Start Bridge

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: Hermes runtime state, worker results, Receipt Five,
> `scripts/factoryctl.py`, `scripts/factory_bridge.py`, schemas and tests.
> Runtime boundary: this bridge is an operator intake/start contract. It does
> not execute factory work, close gates, approve human decisions or replace
> Hermes.

The Operator Start Bridge is the narrow contract between a human operator and a
new factory run.

It exists because a human usually starts with natural language, files or links,
while the factory needs sealed, replayable artifacts before Hermes creates real
cards.

The bridge can:

- preserve the operator's original material as a sealed source envelope;
- create a `factory_bridge_run` record;
- create a `factory_bridge_start_request` for `overkill-factory-gerente` and
  `factory-orchestrator`;
- record operator decisions or handoff packets when a real decision artifact
  exists;
- summarize the Durable Operator Inbox.

The bridge cannot:

- create Hermes boards or cards by itself;
- select the product truth;
- skip Product SOT, gates, security or review;
- approve human gates;
- dispatch workers;
- call work done.

## Simple Flow

```text
operator material
-> factory_bridge_source_envelope
-> factory_bridge_run
-> factory_bridge_start_request
-> overkill-factory-gerente / factory-orchestrator
-> Factory/Hermes start path
-> Hermes board and blocked root card
-> normal factory phases, workers, gates and Receipt Five
```

## Durable Operator Inbox

The Durable Operator Inbox is a local JSONL queue under
`.tmp/factory-runs/operator-inbox/`.

| File | Purpose |
| --- | --- |
| `events.jsonl` | Append-only events from Hermes, factoryctl, transition hooks or bridge scripts. |
| `pending.jsonl` | Events that still require operator attention. |
| `acks.jsonl` | Operator acknowledgements, decisions and response refs. |

The inbox is intentionally boring. It is not a watcher and not a runtime. It is
a durable handoff surface for operator-facing events.

## Bridge Modes

| Mode | Trigger | Allowed action |
| --- | --- | --- |
| `intake_bridge` | The operator brings a new product/request/signal. | Create or update a sealed source envelope. Do not summarize, interpret, scope or select truth for the factory. |
| `start_bridge` | The operator says to start an approved run. | Create a bridge run record plus `factory_bridge_start_request` for `overkill-factory-gerente` / `factory-orchestrator`. Do not create Hermes boards/cards directly. |
| `resume_bridge` | The operator returns later. | Read the inbox and summarize pending state. |
| `status_bridge` | "Como está?", "quanto falta?", "status". | Resolve an explicit board/run target, then read Hermes/factory artifacts and separate proved, inferred, blocked and next action. |
| `question_bridge` | "Por que bloqueou?", "qual worker falhou?". | Explain from artifacts without mutating runtime state. |
| `decision_bridge` | Approval, rejection, waiver or gate response. | Record a bridge decision and point to the required factory/human-gate artifact. `human_gate_response` requires `human_gate_record_ref`. |
| `change_bridge` | Pause, resume, change scope, add/remove requirement. | Classify whether the change needs replan, human gate or runtime action. |
| `exception_bridge` | Script/runtime bridge failure. | Repair the bridge layer or create an incident-style event. |
| `handoff_bridge` | Another agent/session must continue. | Create a replayable handoff packet. |
| `learnback_forwarding` | Operator says "learn from this". | Forward a candidate learning signal only. |

## Start Contract

There are two start modes:

| Project mode | Required behavior |
| --- | --- |
| `new_project` | The bridge must mark `factory_must_create_new_board`. It must not provide or select an existing board. Board creation belongs to the factory start path. |
| `existing_project` | The bridge must require an explicit `kanban:`, `hermes:`, `run:` or `board:` reference from the operator/runtime. It must not guess a board from nearby state. |

The deterministic Hermes start path is:

```bash
python adapters/hermes/live_kanban_adapter.py materialize-bridge-start \
  --start-request .tmp/factory-runs/<run-id>/start-request.json \
  --source-envelope .tmp/factory-runs/<run-id>/source-envelope.json \
  --out .tmp/factory-runs/<run-id>/hermes-start-result.json
```

This command belongs to the factory/Hermes adapter, not to the bridge. It
creates or verifies the fresh project board for `new_project`, creates one root
start card, blocks it with a durable Hermes block event, verifies that blocked
event and assigns the card to `factory-orchestrator`.

## Status And Change Requests

When the operator asks for status, information or a change, answer from the
strongest available source:

1. Hermes runtime/card state.
2. Worker result artifacts.
3. Receipt Five or reconciliation result.
4. Durable Operator Inbox events.
5. `factoryctl` projections and gate reports.
6. Explicit inference, labeled as inference.

Before reading Hermes for a status answer, resolve the explicit factory runtime
target for the run. A default Hermes store, shell default or unrelated workspace
is not proof that a run is missing in the configured runtime.

For change requests, classify before acting:

| Classification | Meaning |
| --- | --- |
| safe operator action | It only records or summarizes state. |
| requires human gate artifact | It affects authority, risk, release, funds, privacy or R3/R4 scope. |
| requires factory replan | It changes product scope, method, worker graph or evidence requirements. |
| requires runtime intervention | Hermes/adapter/start path is broken or blocked by infrastructure. |
| forbidden without explicit approval | It would publish, delete, bypass evidence, close gates or mutate production state. |

## Learnback Boundary

`learnback_forwarding` is not Factory Mechanic.

Factory Mechanic remains the self-improvement owner. The bridge may collect and
forward a learning signal, but it must not activate new gates, workers, skills,
prompts or registry changes. Sensitive factory changes still require a
public-safe proposal or issue, independent review and explicit human gate.

## Authority Rules

- A bridge decision is not a human gate record.
- `human_gate_response` requires `human_gate_record_ref`; chat text alone does
  not close or approve a factory gate.
- A bridge event is not runtime evidence.
- A status summary is not Receipt Five.
- A source envelope is not Product SOT.
- A start request is not a Hermes board.
- A default or ambient Hermes store is not proof that another configured runtime
  target is empty.
- `new_project` requires the factory start path to create the board.
- `existing_project` requires an explicit existing board or run reference.
- `learnback_forwarding` is not Factory Mechanic activation.
- `dependency_wait` is a typed wait state, not permission to ask the operator by
  default.

## Output Discipline

When answering the operator, include:

- current state and source;
- pending human gates or decisions;
- blocked reason, if any;
- what the factory can do autonomously next;
- what needs the human;
- what must not be done by the bridge.
