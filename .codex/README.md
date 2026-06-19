# Codex Project Hooks

Codex project hooks provide local wake-up context for the Overkill Factory
Bridge.

## What Belongs Here

- Project-local Codex hook configuration that reads the Durable Operator Inbox.
- Thin hook wrappers that delegate deterministic work to `scripts/factory_bridge.py`.
- Public-safe hook docs that can be reviewed before a user trusts the hooks.

## What Does Not Belong Here

- Private credentials, local machine paths or private board references.
- Long-running watchers or background agents.
- Hook logic that approves gates, closes Hermes cards or executes factory work.

## Source Of Truth

`scripts/factory_bridge.py`, Hermes runtime state, worker results and Receipt
Five remain authoritative. Hooks only add context when Codex starts or receives
a prompt.

## How It Is Validated

Run the bridge and hook tests:

```bash
python -m unittest tests.test_factory_bridge tests.test_hermes_transition_hook -q
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
```
