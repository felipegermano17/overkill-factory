# Codex Plugin Marketplace

This directory exposes the repo-local Codex plugin marketplace for Overkill
Factory.

## What Belongs Here

- Marketplace metadata that lets a Codex operator install public factory
  plugins from this checkout.
- Pointers to plugin packages that are safe to expose in the public repo.

## What Does Not Belong Here

- Installed plugin caches, user approvals, private config or secrets.
- Local machine paths, generated hook output or long-running automation state.

## Source Of Truth

`.agents/plugins/marketplace.json` is the marketplace entrypoint. The current
Bridge plugin package lives in `plugins/overkill-factory-bridge/`.

Runtime truth remains Hermes Kanban, worker results and Receipt Five. This
directory only tells Codex where installable plugin packages live.

## How It Is Validated

Run:

```bash
python -m unittest tests.test_overkill_factory_bridge_plugin -q
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
```
