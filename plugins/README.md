# Plugins

This directory contains public Codex plugin packages for operating Overkill
Factory.

## What Belongs Here

- Public plugin packages that can be installed from the repo-local marketplace.
- Plugin README files, hook definitions, bundled skills and deterministic
  helper scripts.

## What Does Not Belong Here

- User-specific plugin installs, private hook approvals or local plugin cache.
- Secrets, private runtime evidence, generated worker packets or long-running
  daemon state.

## Source Of Truth

`.agents/plugins/marketplace.json` is the marketplace entrypoint. The current
package is `plugins/overkill-factory-bridge/`, and its operator guide is
`docs/operator/overkill-factory-bridge-plugin.md`.

The Bridge plugin is not the factory runtime. Hermes Kanban, worker results and
Receipt Five remain authoritative for real factory execution.

## How It Is Validated

Run:

```bash
python -m unittest tests.test_overkill_factory_bridge_plugin -q
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
```
