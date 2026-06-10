# Hermes Worker Completion Source Notes

This is a public-safe source note for the real-worker completion blocker.

It summarizes the official Hermes material and the current implementation
behavior that matter before running more real Hermes worker tests.

## Sources Studied

- Official Hermes docs site: `https://hermes-agent.nousresearch.com/docs/`
- Official Hermes repository: `NousResearch/hermes-agent`
- Official Kanban design spec: `docs/hermes-kanban-v1-spec.pdf`
- Current implementation files:
  - `agent/prompt_builder.py`
  - `tools/kanban_tools.py`
  - `hermes_cli/kanban_db.py`
  - `hermes_cli/config.py`

No raw private runtime logs, board ids, task ids, local paths, tokens or
provider responses are stored here.

## What The Official Kanban Spec Says

Hermes Kanban has six main task states:

- `todo`: created, waiting for dependencies;
- `ready`: dependencies are done and the task may be claimed;
- `running`: a worker process claimed the task;
- `blocked`: the worker needs human or peer input;
- `done`: the worker wrote a completion result;
- `archived`: hidden from default views.

The ownership rule is important:

- dispatcher owns `ready -> running`;
- worker owns `running -> done`;
- worker owns `running -> blocked`;
- human or peer agents own `blocked -> ready`;
- user owns archive.

So a spawned worker that never calls `kanban_complete` or `kanban_block` has not
finished the protocol, even if it produced text in a log.

## What The Worker Sees

The official assignment model is explicit: one task has one assignee profile.

When a worker is spawned, its visible context should come from the board:

- task title;
- task body;
- comments in chronological order;
- parent handoffs;
- the profile's normal skills and memory.

If a fact is not visible through the task context, the worker should not be
assumed to know it.

## Dispatcher Behavior

The dispatcher is intentionally simple:

- promote dependency-satisfied work to `ready`;
- atomically claim `ready` tasks with an assignee;
- spawn a worker process;
- reclaim stale or failed work.

The implementation adds practical safety around this:

- workers receive environment variables that pin task id, board, workspace,
  run id and claim lock;
- workers write completion or block state through `kanban_*` tools;
- worker stdout/stderr goes to per-task logs;
- live worker PID is only a crash/stale safety net, not proof of completion;
- clean exit without `kanban_complete` or `kanban_block` is treated as a
  protocol violation;
- heartbeat extends liveness but does not count as completion.

## Worker Lifecycle Contract

The current worker prompt tells a spawned worker to:

1. call `kanban_show()` first;
2. work only inside its workspace;
3. call `kanban_heartbeat(note=...)` during long work;
4. call `kanban_block(reason=...)` for genuine ambiguity;
5. call `kanban_complete(summary=..., metadata=...)` for completion.

The `kanban_complete` tool requires a `summary` or `result`. Metadata must be a
JSON object. The `kanban_block` tool requires a human-readable reason.

## Real Runtime Finding

A bounded real-worker terminal-completion smoke was run after studying the
official docs and implementation.

Initial result: `BLOCKED`.

Follow-up result after auth repair: `PASS`.

What it proved:

- disposable board and task creation worked;
- the worker profile was spawnable;
- the dispatcher spawned a real worker;
- cleanup and archive completed;
- status-level auth is not enough;
- stale local profile auth can shadow fresh global auth;
- after removing the stale `factory-orchestrator` auth shadow, a profile-level
  provider/model probe passed;
- the real worker called `kanban_complete` and reached `done`.

What the initial blocked run did not prove:

- the worker did not reach `done`;
- the worker did not call `kanban_complete`;
- the worker did not call `kanban_block`;
- the worker did not produce a terminal runtime event.

The sanitized log classification showed the initial worker failed before using
the Kanban tool protocol: provider/model authentication failed on a live
`openai-codex` request. This means a status-only auth check is not enough for
production readiness. A live provider probe is required before dispatching
production worker routes.

The follow-up repair refreshed global OpenAI Codex auth and removed the stale
local `openai-codex` shadow from the `factory-orchestrator` profile, allowing
the profile to use Hermes' global auth fallback. The profile probe then passed,
and the disposable worker completed through `kanban_complete`.

The runtime also showed why this matters: status surfaces can report configured
or logged-in auth while a live worker request still fails. Production readiness
must therefore check the exact worker profile/provider/model path with a live
minimal request, not just stored-auth presence.

## Factory Implication

The next blocker is not generic Hermes dispatch anymore.

The next blocker is:

```text
every production worker profile must pass a profile/provider live auth probe before dispatch
```

The factory should treat a profile as production-ready only when:

- the profile exists;
- the expected Kanban tools are available in worker mode;
- the profile's configured provider/model can answer a live minimal request;
- the worker can call `kanban_complete` or `kanban_block`;
- the runtime records the terminal state and run metadata.

Until then, real-runtime update preflight must stay `BLOCKED`.
