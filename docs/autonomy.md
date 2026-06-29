# Autonomy and no-idle

Autonomy in Overkill Factory does not mean the model remembers to continue.

It means the next safe action can be recovered from durable state.

## The autonomy spine

There are three parts:

1. Hermes stores runtime truth: boards, cards, dependencies, status, typed blocks, dispatch, runs and logs.
2. Factory contracts define what is allowed to advance: source, product definition, method, capability, gates, worker result, evidence and Receipt Five.
3. No-idle watches the frontier and wakes the next safe action when the board would otherwise stall.

If any of those are missing, autonomy becomes improvisation.

## What no-idle should do

No-idle reads current runtime and factory state. Then it chooses the next safe action:

- consume a completed worker result;
- dispatch ready work through Hermes;
- create a repair task for recoverable gaps;
- wait for a real dependency;
- continue a capability search;
- emit a typed blocker;
- ask the manager to request operator input only when no safe autonomous action remains.

No-idle is not the main brain. It is the recovery and continuity guard.

## What no-idle must not do

No-idle must not:

- approve gates;
- mark work done;
- invent the next phase;
- bypass Hermes dispatch;
- treat chat memory as runtime state;
- turn every blocker into a human question;
- pretend a worker packet is a worker result;
- replace the manager as the human-facing voice.

## Repair before interruption

The factory should repair what it can safely repair.

Examples:

- missing generated artifact;
- recoverable schema mismatch;
- stale result after newer evidence;
- dependency edge missing from the graph;
- retryable dispatch issue;
- capability search still in progress;
- readback failure that can retry.

The operator should not be interrupted for these.

## Human input boundary

The operator is contacted for real human authority:

- product definition approval or correction;
- source only the operator has;
- access, cost, secrets or production;
- mainnet, funds or signer authority;
- material risk acceptance;
- product-direction choice.

When the operator is contacted, the manager should provide a readable package, not raw internal noise.

## Failure mode this prevents

Without no-idle, agentic systems stop between tasks.

A worker completes, but nobody consumes the result. A repair is possible, but nobody creates it. A dependency clears, but the next work unit stays idle. Or the model asks the operator “should I continue?” even though the system already knows the next safe action.

No-idle exists to close those gaps while preserving Hermes as the runtime authority.

## Honest live-proof boundary

A local no-idle test can prove the code path. It does not prove the real external operator loop.

Live autonomy requires the real chain:

```text
operator signal
-> manager intake
-> FactoryRun
-> Hermes board
-> worker dispatch
-> worker result
-> no-idle continuation or repair
-> manager progress delivery
-> Receipt Five
```

Until that chain is proven in the live environment, the documentation should say the autonomy mechanism is implemented locally and live proof remains pending.
