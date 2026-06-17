# UI

This directory contains static public-safe UI surfaces that project factory
state from fixtures or sanitized local data.

## What Belongs Here

- Local-only static interfaces that help inspect factory state without mutating
  Hermes, GitHub, releases or human gates.
- Public-safe fixture datasets generated from committed fixtures.
- UI code with tests proving read-only behavior and public-boundary limits.

## What Does Not Belong Here

- Hosted production apps.
- Private runtime dashboards, screenshots, local browser captures or raw
  evidence exports.
- UIs that approve gates, mutate Hermes cards, close issues, deploy, push to
  GitHub or claim production readiness.

## Source Of Truth

UI surfaces are projections. Hermes, schemas, `factoryctl`, worker results and
Receipt Five remain authoritative for real factory execution.

Current surface:

| Path | Purpose |
| --- | --- |
| `ui/local-status-cockpit/` | Static local cockpit for StatusSnapshot fixture inspection. It is read-only and loopback-only. |

## How It Is Validated

```bash
python scripts/status_snapshot/build_local_cockpit_data.py --root . --out ui/local-status-cockpit/data/status-cockpit.json
python scripts/status_snapshot/validate_status_snapshot_fixtures.py fixtures/status-snapshot-v0 --schema schemas/factory-status-snapshot.schema.json --require-cases FX01,FX02,FX03,FX04,FX05,FX06,FX07,FX08,FX09,FX10,FX11,FX12,FX13,FX14,FX15,FX16,FX17,FX18 --fail-closed
python -m unittest tests.test_local_status_cockpit_ui tests.test_status_snapshot_readonly_adapter -q
```
