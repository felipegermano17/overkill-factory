# Overkill Factory Bridge Plugin

Codex plugin for operating Overkill Factory as the human bridge, not as the
factory runtime.

It packages:

- the `overkill-factory-bridge` skill;
- `scripts/factory_bridge.py` for durable inbox summaries, decisions and
  handoff packets;
- Codex lifecycle hooks in `hooks/hooks.json` for wake-up context.

## Install From This Repo Marketplace

From the repo root:

```bash
codex plugin marketplace add .agents/plugins
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

## Inbox Resolution

The hook reads the inbox in this order:

1. `OVERKILL_FACTORY_INBOX`, when explicitly set;
2. `<current workspace>/.tmp/factory-runs/operator-inbox`;
3. `PLUGIN_DATA/operator-inbox`;
4. the plugin-local `.tmp` fallback.

This lets Codex catch up after being closed without staying alive 24/7.
