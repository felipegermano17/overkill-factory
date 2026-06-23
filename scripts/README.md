# Scripts

Scripts provide the public CLI path, validation tools and maintainer checks.

## What Belongs Here

- CLI entrypoints such as `factoryctl.py`.
- Operator bridge helpers such as `factory_bridge.py` when they stay
  public-safe and do not replace factory gates.
- Validation scripts for cards, schemas, worker profiles, public safety and
  release readiness.
- Runtime maintenance guards such as `hermes_update_guard.py` when they are
  public-safe, deterministic and covered by tests.
- Cron-friendly autonomy helpers such as `factory_no_idle_watchdog.py` when
  they call the Hermes adapter and native Hermes dispatch instead of creating a
  shadow scheduler.
- Small maintainer utilities that are documented and covered by tests.

## What Does Not Belong Here

- One-off local automation from a private workspace.
- Scripts that depend on private paths, private boards or local credentials.
- Generated outputs. Write those to `.tmp/`.

## Source Of Truth

`scripts/factoryctl.py`, package entrypoints and tests define the supported
operator path. `factoryctl doctor`, `factoryctl init` and
`factoryctl run minimal` are the first commands. Experimental helpers must
either graduate into that path or stay clearly secondary.

`factory_no_idle_watchdog.py` is the supported Hermes-cron wrapper for the
no-idle controller. It may inspect non-empty boards, create one safe
factory-owned remediation card through `adapters/hermes/live_kanban_adapter.py`,
and call native Hermes dispatch only when the adapter reports that dispatch is
the next action. It must not approve gates, complete work or bypass Hermes.

## How It Is Validated

Run the script-facing bundle:

```bash
python scripts/quickstart_smoke.py
python scripts/validate_worker_profiles.py
python scripts/hermes_update_guard.py plan
python scripts/factory_no_idle_watchdog.py --board example-board
python scripts/validate_public_json_artifacts.py
python scripts/factory_production_gate_receipts.py --no-write
python -m unittest discover -s tests -p "test_*.py" -q
```
