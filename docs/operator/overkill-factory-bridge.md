# Overkill Factory Bridge

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: Hermes runtime state, worker results, Receipt Five,
> `scripts/factoryctl.py`, `scripts/factory_bridge.py`, schemas and tests.
> Runtime boundary: This bridge is an operator interface. It does not execute
> factory work, close gates or approve human decisions.

The Overkill Factory Bridge lets Codex or another assistant act like the human
operator's delegate, not like the factory itself.

It can collect the initial signal, start a factory run, read observability,
surface human gates, record the operator's answer and hand that answer back to
the factory. It can intervene only for operational exceptions such as a broken
hook, malformed artifact or missing bridge file.

The bridge does not create Hermes boards or cards for a new project. For a new
project, it creates a sealed source envelope and a `factory_bridge_start_request`
addressed to the factory gateway/orchestrator. The factory start path then owns
board creation, card creation, worker routing and blocking state.

## One-Line Architecture

```text
human prompt
-> bridge skill
-> factory_bridge.py
-> Durable Operator Inbox
-> sealed source envelope
-> factory_bridge_start_request
-> overkill-factory-gerente / factory-orchestrator
-> adapters/hermes/live_kanban_adapter.py materialize-bridge-start
-> Hermes/factory transition hooks
-> Codex SessionStart/UserPromptSubmit context
-> operator response artifact
-> factory/Hermes consumes the response through normal gates
```

## Durable Operator Inbox

The Durable Operator Inbox is a repo-local JSONL queue under
`.tmp/factory-runs/operator-inbox/`:

| File | Purpose |
| --- | --- |
| `events.jsonl` | Append-only event stream from Hermes, factoryctl, hooks or the bridge. |
| `pending.jsonl` | Events that still require operator attention. |
| `acks.jsonl` | Operator or bridge acknowledgements, decisions and response refs. |

The inbox is deliberately local and boring. It survives Codex being closed
because the events are files. Codex hooks do not watch the machine while Codex is closed. They only read the inbox when Codex starts, resumes or receives a
prompt.

If Codex opens from the parent workspace instead of the factory checkout, the
Bridge plugin may resolve one nearby child checkout that contains the
`overkill-factory` marketplace and operator inbox. Operators can make that
resolution explicit with `OVERKILL_FACTORY_INBOX` or `OVERKILL_FACTORY_ROOT`.

That means there is no 24/7 token burn. Hermes or deterministic scripts write
events. Codex wakes only when the user opens it, prompts it or schedules an
automation.

## Codex Hooks

Use hooks for wake-up context, not runtime ownership.

The repo also ships a final-stage Codex plugin package for this bridge. See
`docs/operator/overkill-factory-bridge-plugin.md` for install, hook trust and
plugin validation.

| Hook | Role | Why it is safe |
| --- | --- | --- |
| `SessionStart` | Summarize pending inbox events when Codex opens, resumes or compacts. | It reads local JSONL and adds context. |
| `UserPromptSubmit` | Classify the operator prompt into a bridge mode and include pending events. | It does not mutate Hermes or close gates. |
| `Stop` | Optional no-op continuation hook for future local persistence. | It cannot approve factory work. |

Project-local hooks require the repo `.codex/` layer to be trusted by Codex.
Changed hooks must be reviewed and trusted again. That is a feature: hook code
is executable code, not passive documentation.

## Automations

Automations are optional heartbeat checks. Use them only when the operator wants
scheduled follow-up, for example "check this inbox every 30 minutes while this
run is active."

Keep automations narrow:

- read the Durable Operator Inbox;
- report only when there are new pending events;
- stop when the run is complete or the operator cancels it;
- do not poll Hermes continuously through Codex when a deterministic Hermes hook
  can write an event instead.

This follows the product boundary: skills define the method, automations define
the schedule.

## Bridge Modes

| Mode | Trigger | Allowed action |
| --- | --- | --- |
| `intake_bridge` | The operator brings a new product/request/signal. | Create or update a sealed source envelope. Do not summarize, interpret, scope or select truth for the factory. |
| `start_bridge` | The operator says to start an approved run. | Create a bridge run record plus `factory_bridge_start_request` for `overkill-factory-gerente` / `factory-orchestrator`. Do not create Hermes boards/cards directly. |
| `resume_bridge` | Codex restarts or the operator returns later. | Read the inbox and summarize pending state. |
| `status_bridge` | "Como esta?", "quanto falta?", "status". | Resolve an explicit board/run target, then read Hermes/factory artifacts and separate proved, inferred, blocked and next action. |
| `question_bridge` | "Por que bloqueou?", "qual worker falhou?". | Explain from artifacts without mutating runtime state. |
| `decision_bridge` | Approval, rejection, waiver or gate response. | Record a bridge decision and point to the required factory/human-gate artifact. `human_gate_response` requires `human_gate_record_ref`. |
| `change_bridge` | Pause, resume, change scope, add/remove requirement. | Classify whether the change needs replan, human gate or runtime action. |
| `exception_bridge` | Hook/script/runtime bridge failure. | Repair the bridge layer or create an incident-style event. |
| `handoff_bridge` | Another agent/session must continue. | Create a replayable handoff packet. |
| `learnback_forwarding` | Operator says "learn from this". | Forward a candidate learning signal only. |

## Start Contract

There are two start modes:

| Project mode | Required behavior |
| --- | --- |
| `new_project` | The bridge must mark `factory_must_create_new_board`. It must not provide or select an existing board. Board creation belongs to the factory start path. |
| `existing_project` | The bridge must require an explicit `kanban:`, `hermes:`, `run:` or `board:` reference from the operator/runtime. It must not guess a board from nearby state. |

The canonical handoff is:

```text
operator material
-> factory_bridge_source_envelope
-> factory_bridge_run
-> factory_bridge_start_request
-> overkill-factory-gerente / factory-orchestrator
-> factory start path materializes Hermes board/cards
```

`overkill-factory-gerente` is the interface/gateway profile. `factory-orchestrator`
is the factory routing worker. The bridge may address them, but it must not do
their work.

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
event and assigns the card to `factory-orchestrator`. The adapter applies the
factory start reducer; only that path may release and dispatch the first
orchestrator run. Use `--hold-start` only for an intentional diagnostic hold, or
`--no-dispatch` when another runtime component will dispatch immediately. It
must not claim product work is complete.

## Learnback Boundary

`learnback_forwarding` is not Factory Mechanic.

Factory Mechanic remains the self-improvement owner. The bridge may collect and
forward a learning signal, but it must not activate new gates, hooks, workers,
skills, prompts or registry changes. Sensitive factory changes still require a
public-safe proposal or issue, independent review and explicit human gate.

## Status And Change Requests

When the operator asks for status, information or a change, the bridge must
answer from the strongest available source:

1. Hermes runtime/card state.
2. Worker result artifacts.
3. Receipt Five or reconciliation result.
4. Factory bridge inbox events.
5. `factoryctl` projections and gate reports.
6. Explicit inference, labeled as inference.

Before reading Hermes for a status answer, resolve the explicit factory runtime
target for the run. A default Hermes store, shell default, or unrelated
workspace is not proof that a run is missing in the configured runtime.

For change requests, the bridge classifies the request before acting:

| Classification | Meaning |
| --- | --- |
| safe operator action | It only records or summarizes state. |
| requires human gate artifact | It affects authority, risk, release, funds, privacy or R3/R4 scope. |
| requires factory replan | It changes product scope, method, worker graph or evidence requirements. |
| requires runtime intervention | Hermes/hook/adapter is broken or blocked by infrastructure. |
| forbidden without explicit approval | It would publish, delete, bypass evidence, close gates or mutate production state. |

## Hook-To-Inbox Events

Hermes transition hooks may emit operator events when a transition blocks or
requires human attention. The event is informational and durable. It does not
make the bridge a source of truth.

Example:

```bash
python adapters/hermes/transition_hook.py \
  --card examples/cards/v35_valid_onchain_auditor_scan.md \
  --from-status draft \
  --to-status ready \
  --ledger .tmp/factory-runs/example/worker-ledger.json \
  --operator-inbox .tmp/factory-runs/operator-inbox \
  --operator-run-id example-run \
  --out .tmp/factory-runs/example/ready-hook-result.json \
  --report-only
```

## Telegram Autonomy Heartbeat

When Telegram is the only cockpit, the operator should not need to ask "andou?"
for the factory to continue. The supported heartbeat is a Hermes cron job that
runs `scripts/factory_no_idle_watchdog.py`.

The watchdog:

- scans explicit boards or non-empty boards;
- asks the Hermes adapter to classify no-idle state;
- creates one safe factory-owned remediation card when unfinished work is stuck
  without `ready`, `running` or a sole human gate;
- calls native Hermes dispatch only when the adapter reports dispatch is the
  next action;
- emits Durable Operator Inbox events for human gates or attention-worthy
  remediation.

It does not run product work, close gates, approve human decisions or replace
Receipt Five. Telegram receives only state changes, remediations and real human
gate requests; repeated identical states are deduplicated by the watchdog state
file.

## Public Contracts

The bridge exposes these machine contracts:

| Contract | Purpose |
| --- | --- |
| `schemas/factory-bridge-event.schema.json` | Durable operator event. |
| `schemas/factory-bridge-decision.schema.json` | Operator response forwarding record. |
| `schemas/factory-bridge-handoff.schema.json` | Replayable continuation packet. |
| `schemas/factory-bridge-run.schema.json` | Bridge run record. |
| `schemas/factory-bridge-source-envelope.schema.json` | Sealed source refs for factory-owned source resolution. |
| `schemas/factory-bridge-start-request.schema.json` | Request addressed to the factory gateway/orchestrator. |

Templates live under `templates/factory-bridge-*.json`.

## Non-Goals

The bridge must not:

- act as a factory worker;
- run specialist scans by itself;
- summarize or interpret source material as Product SOT;
- select or reuse an old board for a new project;
- create Hermes boards or cards directly;
- dispatch workers;
- approve human gates;
- close Hermes cards;
- replace Receipt Five;
- keep Codex active 24/7;
- turn learnback into active factory changes.

Its job is to keep the operator loop crisp without corrupting the factory's
autonomy or evidence model.
