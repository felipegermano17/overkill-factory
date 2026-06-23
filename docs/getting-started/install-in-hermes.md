# Install In Your Hermes

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: README.md, scripts/factoryctl.py, adapters/hermes/README.md,
> agents/hermes-profile-bindings.public.json, tests/
> Runtime boundary: This guide prepares an operator-owned Hermes integration. It
> does not claim a real Hermes E2E harness.

## Goal

A person or AI should be able to clone the factory, check the install, create a
workspace and know exactly what to connect to their Hermes runtime.

## Install

```bash
git clone https://github.com/felipegermano17/overkill-factory.git
cd overkill-factory
python -m pip install -e .
factoryctl doctor
factoryctl run minimal
factoryctl init --out ../my-product-factory --project-name my-product
```

Package-installed CLI commands can run outside this checkout for health checks,
minimal smoke and workspace initialization. Keep the checkout when applying the
Hermes adapter patch or inspecting public docs and examples.

## Fresh Adapter Smoke

Before touching a real Hermes board, prove the public adapter path locally:

```bash
factoryctl gate-report --card examples/minimal-hermes-project/card.md
factoryctl worker-packet \
  --worker all \
  --required-only \
  --card examples/minimal-hermes-project/card.md \
  --out .tmp/external-hermes-worker-packets
python adapters/hermes/transition_hook.py \
  --card examples/minimal-hermes-project/card.md \
  --from-status draft \
  --to-status ready \
  --ledger .tmp/external-hermes-worker-ledger.json \
  --out .tmp/external-hermes-ready-hook-result.json \
  --report-only
```

All generated output stays under `.tmp/`. Do not commit worker packets, ledgers,
screenshots or runtime proof from your own Hermes instance.

## What Gets Installed

- `factoryctl`: the supported CLI.
- Public Codex skill material under `skills/codex/overkill-factory/`.
- Hermes adapter material under `adapters/hermes/`.
- Public worker bindings under `agents/hermes-profile-bindings.public.json`.

## Connect To Hermes

1. Review the workspace created by `factoryctl init`.
2. Install the Codex skill into the agent environment that will operate Hermes.
3. Apply the Hermes adapter patch in a test Hermes checkout first.
4. Wire Hermes transition events to `adapters/hermes/transition_hook.py`.
5. Generate worker packets with `factoryctl worker-packet`.
6. Create or route Hermes worker cards from those packets.
7. Attach real worker result artifacts and Receipt Five before `done`.

## Telegram-First Autonomy

If the operator talks only to `overkill-factory-gerente` through Telegram, add a
Hermes cron job for the no-idle watchdog after the adapter path is installed:

```bash
mkdir -p ~/.hermes/scripts
cat > ~/.hermes/scripts/overkill_factory_no_idle_watchdog.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
export HOME="${HERMES_HOME:-$HOME}"
export HERMES_HOME="${HERMES_HOME:-$HOME}"
cd /path/to/overkill-factory
python scripts/factory_no_idle_watchdog.py \
  --all-nonempty-boards \
  --exclude-board old-product-board-if-not-archived \
  --create-remediation \
  --dispatch \
  --emit-events
SH
chmod +x ~/.hermes/scripts/overkill_factory_no_idle_watchdog.sh
hermes cron create "every 5m" \
  --name overkill-factory-no-idle-watchdog \
  --script overkill_factory_no_idle_watchdog.sh \
  --no-agent \
  --deliver telegram
```

This gives the factory a heartbeat without giving the watchdog authority over
the product. It may create safe remediation work and trigger native dispatch. It
must not close human gates, execute factory work as the manager, or approve
production, mainnet, funds, signing, secrets, billing or destructive actions.

Archive obsolete boards or pass `--exclude-board <slug>` for abandoned products.
The watchdog should keep active factory runs moving; it should not revive a
product the operator is intentionally replacing.

## Boundary

Point 5 is intentionally deferred. This guide makes installation easy, but it
does not claim an official real Hermes E2E harness. Until that harness exists,
operator-owned Hermes validation must happen in the user's own test runtime.
