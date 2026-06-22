# Overkill Factory Bridge Plugin

The Bridge plugin packages the public operator bridge for Codex.

It is a distribution layer, not a new runtime. Hermes, `factoryctl`, worker
results, Receipt Five and production-readiness receipts remain authoritative.
For new projects, the plugin must hand a start request to the factory
gateway/orchestrator. It must not create Hermes boards or cards directly.

## What It Contains

- `overkill-factory-bridge` skill.
- `scripts/factory_bridge.py` for sealed source envelopes, start requests,
  inbox summaries, decision records and handoff packets.
- Codex lifecycle hooks in `hooks/hooks.json`.
- A repo-local marketplace at `.agents/plugins/marketplace.json`.

## Install

From the repository root:

```bash
codex plugin marketplace add .
codex plugin add overkill-factory-bridge@overkill-factory
```

Start a new Codex thread after installation so Codex loads the plugin skill and
hooks.

## Hook Trust

Plugin hooks require trust review before they run.

Review `hooks/hooks.json` and
`hooks/overkill_factory_bridge_hook.py` inside the plugin package. The hooks are
read-only wake-up hooks:

- `SessionStart` summarizes pending inbox events.
- `UserPromptSubmit` classifies the operator prompt and adds context.

They must not approve human gates, close cards, mutate Hermes, run workers,
publish to GitHub or make Discord a source of truth.

For `new_project`, the plugin creates a `factory_bridge_source_envelope` and a
`factory_bridge_start_request` addressed to `overkill-factory-gerente` /
`factory-orchestrator`. The factory start path owns board creation. For
`existing_project`, the operator/runtime must provide an explicit existing board
or run reference.

## Inbox

The plugin hook reads the Durable Operator Inbox in this order:

1. `OVERKILL_FACTORY_INBOX`;
2. `OVERKILL_FACTORY_ROOT/.tmp/factory-runs/operator-inbox`;
3. `<current workspace>/.tmp/factory-runs/operator-inbox`;
4. a single nearby child checkout with the `overkill-factory` marketplace and
   operator inbox, when Codex was opened from the parent workspace;
5. `PLUGIN_DATA/operator-inbox`;
6. plugin-local `.tmp` fallback.

This supports queue catch-up when Codex was closed without keeping Codex active
24/7.

## Validation

Run:

```bash
python /path/to/plugin-creator/scripts/validate_plugin.py plugins/overkill-factory-bridge
python -m unittest tests.test_overkill_factory_bridge_plugin -q
```

The normal repo validation still applies:

```bash
python scripts/validate_public_json_artifacts.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
```
