---
name: overkill-factory-bridge
description: "Use when a human asks Codex or another assistant to bridge an Overkill Factory run: collect/start signals, resume from inbox, report status, answer factory questions, capture human gate decisions, process scope changes, create handoff packets, or forward learnback without acting as a factory worker."
---

# Overkill Factory Bridge

Use this skill to operate between a human operator and Overkill Factory. The
bridge must not act as a factory worker. It observes, reports, records operator
responses and hands those responses back to the factory through normal gates.

## First Move

1. Read `docs/operator/overkill-factory-bridge.md` when the request touches
   hooks, automations, queueing, authority, handoff or learnback.
2. Use `scripts/factory_bridge.py` for durable inbox events, summaries,
   prompt classification, sealed source envelopes, start requests, decision
   records and handoff packets.
3. Treat Hermes state, worker results and Receipt Five as the source of truth.
4. Separate proved facts, inference, pending human decisions and next safe
   action.
5. Never close gates, approve human records, run specialist work or mutate
   Hermes as the bridge.
6. For `new_project`, do not create Hermes boards or cards as the bridge. Create
   `factory_bridge_source_envelope` and `factory_bridge_start_request` for
   `overkill-factory-gerente` / `factory-orchestrator`.
7. For `status_bridge`, resolve the explicit factory runtime target before
   reading Hermes. Do not treat an ambient/default Hermes store as proof that
   a run is missing.

## Bridge Modes

| Mode | Use when | Do |
| --- | --- | --- |
| `intake_bridge` | The operator brings a new request or signal. | Create a sealed source envelope. Do not summarize, interpret, scope or decide truth for the factory. |
| `start_bridge` | The operator explicitly starts an approved factory run. | Create a bridge run record and `factory_bridge_start_request` for `overkill-factory-gerente` / `factory-orchestrator`. Do not create Hermes boards/cards directly. |
| `resume_bridge` | Codex starts/resumes or the operator returns. | Read the Durable Operator Inbox and summarize pending work. |
| `status_bridge` | The operator asks for status or progress. | Report proved, inferred, blocked and next action. |
| `question_bridge` | The operator asks why something happened. | Explain from Hermes, worker results, Receipt Five or inbox events. |
| `decision_bridge` | The operator approves, rejects or gives a gate response. | Record a bridge decision; require a proper factory/human-gate artifact for gates. |
| `change_bridge` | The operator asks to pause, resume or change scope. | Classify whether it needs replan, human gate, runtime action or explicit approval. |
| `exception_bridge` | A hook, script or bridge path is broken. | Repair the bridge layer or create an exception event. |
| `handoff_bridge` | Another session or agent must continue. | Create a replayable handoff packet. |
| `learnback_forwarding` | The operator says the factory should learn. | Forward a candidate signal only; Factory Mechanic owns activation. |

## Durable Inbox Commands

Summarize pending operator work:

```bash
python scripts/factory_bridge.py summarize-inbox --text
```

Create a sealed source envelope for a new project:

```bash
python scripts/factory_bridge.py source-envelope \
  --run-id example-run \
  --project-mode new_project \
  --operator-goal "Start a new product project from operator material." \
  --source-ref external:operator:brief \
  --out .tmp/factory-runs/example/source-envelope.json
```

Create a factory start request for the gateway/orchestrator:

```bash
python scripts/factory_bridge.py start-request \
  --run-id example-run \
  --project-mode new_project \
  --operator-goal "Start a new product project from operator material." \
  --source-envelope-ref external:operator:source-envelope \
  --out .tmp/factory-runs/example/start-request.json
```

When operating inside the public factory repository and the operator explicitly
asked to start, hand the request to the factory/Hermes start path:

```bash
python adapters/hermes/live_kanban_adapter.py materialize-bridge-start \
  --start-request .tmp/factory-runs/example/start-request.json \
  --source-envelope .tmp/factory-runs/example/source-envelope.json \
  --out .tmp/factory-runs/example/hermes-start-result.json
```

This command is the factory adapter path, not bridge work. It creates the fresh
Hermes board/card for `new_project`, blocks the root card with a verified Hermes
block event and applies the factory start reducer. Only that adapter path may
return `RELEASE_AND_DISPATCH`; the bridge never releases, dispatches or closes
gates. Use `--hold-start` only for an intentional diagnostic hold, or
`--no-dispatch` when another runtime component will dispatch immediately.

Record a human decision response:

```bash
python scripts/factory_bridge.py decision-record \
  --run-id example-run \
  --event-id fbe_0123456789abcdef01 \
  --decision-type human_gate_response \
  --decision changes_requested \
  --actor product_owner \
  --summary "Release waits for rollback evidence." \
  --evidence-ref external:operator:release-decision \
  --out .tmp/factory-runs/example/bridge-decision.json
```

Create a handoff packet:

```bash
python scripts/factory_bridge.py handoff \
  --run-id example-run \
  --out .tmp/factory-runs/example/bridge-handoff.json
```

## Authority Rules

- A bridge decision is not a human gate record.
- A bridge event is not runtime evidence.
- A status summary is not Receipt Five.
- A source envelope is not Product SOT.
- A start request is not a Hermes board.
- A default or ambient Hermes store is not proof that another configured runtime
  target is empty.
- `new_project` requires the factory start path to create the board.
- `existing_project` requires an explicit existing board or run reference.
- `learnback_forwarding` is not Factory Mechanic activation.
- Codex hooks wake the bridge with context; they do not watch the machine while
  Codex is closed.
- Automations are optional heartbeats with stop conditions, not a 24/7 agent.

## Output Discipline

When answering the operator, include:

- current state and source;
- pending human gates or decisions;
- blocked reason, if any;
- what the factory can do autonomously next;
- what needs the human;
- what must not be done by the bridge.
