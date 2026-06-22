# Overkill Factory Bridge Plugin

Codex plugin for operating Overkill Factory as the human bridge, not as the
factory runtime.

It packages:

- the `overkill-factory-bridge` skill;
- `scripts/factory_bridge.py` for sealed source envelopes, start requests,
  durable inbox summaries, decisions and handoff packets;
- Codex lifecycle hooks in `hooks/hooks.json` for wake-up context.

## Install From This Repo Marketplace

From the repo root:

```bash
codex plugin marketplace add .
codex plugin add overkill-factory-bridge@overkill-factory
```

Then start a new Codex thread and ask for the Overkill Factory Bridge.

## Hook Trust

Installing or enabling the plugin does not automatically trust its hooks. Review
and trust the hook definitions through Codex before expecting `SessionStart` or
`UserPromptSubmit` hooks to run.

The hooks only read the durable operator inbox and classify the operator prompt.
They do not approve human gates, close cards, mutate Hermes, run workers or make
Discord the source of truth.

For a new project, the plugin must hand a `factory_bridge_start_request` to
`overkill-factory-gerente` / `factory-orchestrator`. The bridge must not create
Hermes boards or cards directly. For an existing project, the operator/runtime
must provide the explicit board or run reference.

Inside the public factory repository, the deterministic factory start path is:

```bash
python adapters/hermes/live_kanban_adapter.py materialize-bridge-start \
  --start-request .tmp/factory-runs/<run-id>/start-request.json \
  --source-envelope .tmp/factory-runs/<run-id>/source-envelope.json \
  --out .tmp/factory-runs/<run-id>/hermes-start-result.json
```

That command is the factory/Hermes adapter consuming the bridge request. It
creates the fresh board/card for `new_project`, verifies a blocked root card and
does not dispatch workers.

For status requests, the bridge must resolve the explicit runtime target for the
run before reading Hermes. Do not use an ambient/default Hermes store as proof
that a configured remote or project-specific Hermes runtime is empty.

## Inbox Resolution

The hook reads the inbox in this order:

1. `OVERKILL_FACTORY_INBOX`, when explicitly set;
2. `OVERKILL_FACTORY_ROOT/.tmp/factory-runs/operator-inbox`, when explicitly set;
3. `<current workspace>/.tmp/factory-runs/operator-inbox`;
4. a single nearby child checkout with the `overkill-factory` marketplace and
   operator inbox, when Codex was opened from the parent workspace;
5. `PLUGIN_DATA/operator-inbox`;
6. the plugin-local `.tmp` fallback.

This lets Codex catch up after being closed without staying alive 24/7.
