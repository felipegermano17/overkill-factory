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

For a gateway launched with a dedicated profile, put the wrapper in that
profile's script directory. For a default-profile gateway, `~/.hermes/scripts`
is also valid.

```bash
export FACTORY_GATEWAY_PROFILE=overkill-factory-gerente
export HERMES_PROFILE_HOME="$HERMES_HOME/profiles/$FACTORY_GATEWAY_PROFILE"
mkdir -p "$HERMES_PROFILE_HOME/scripts"
cat > "$HERMES_PROFILE_HOME/scripts/overkill_factory_no_idle_watchdog.sh" <<'SH'
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
chmod +x "$HERMES_PROFILE_HOME/scripts/overkill_factory_no_idle_watchdog.sh"
hermes --profile "$FACTORY_GATEWAY_PROFILE" cron create "every 5m" \
  --name overkill-factory-no-idle-watchdog \
  --script overkill_factory_no_idle_watchdog.sh \
  --no-agent \
  --deliver telegram
```

This gives the factory a heartbeat without giving the watchdog authority over
the product. It may create safe remediation work and trigger native dispatch. It
must not close human gates, execute factory work as the manager, or approve
production, mainnet, funds, signing, secrets, billing or destructive actions.
When unfinished work is silent, the adapter first runs the deterministic
`factoryctl reconcile-board` plan. That plan either points to native dispatch,
repairs the canonical factory card, creates the next required artifact from the
phase engine, repairs a decision package, or asks for a real bounded decision
only when `phase_engine.human_gate_allowed=true` and the decision package is
already approval-ready.

Package/readback failures are factory work. If the blocker says the factory has
not delivered owner-readable material, PDF, `APPROVAL_REQUEST`,
`EVIDENCE_INDEX`, `OWNER_REVIEW`, or attachment readback, the watchdog should
route repair and continue through native dispatch instead of asking the
Telegram operator to approve a summary. If the repair task was accidentally
linked behind the same blocked gate it repairs, the watchdog treats that as a
Kanban graph defect and routes a graph/package fix.

For Solana/onchain products, the same path checks for the Solana AI Kit
domain-brain record before architecture and later gates. Missing Solana AI Kit
state is a factory-owned planning repair, not a Telegram approval request.
When the adapter returns `input_required`, the Telegram operator should ask for
the exact missing inputs instead of saying there is no human action. This is not
approval bureaucracy; it is source/input collection for a blocked dependency
chain.

Archive obsolete boards or pass `--exclude-board <slug>` for abandoned products.
The watchdog should keep active factory runs moving; it should not revive a
product the operator is intentionally replacing.

## Boundary

Point 5 is intentionally deferred. This guide makes installation easy, but it
does not claim an official real Hermes E2E harness. Until that harness exists,
operator-owned Hermes validation must happen in the user's own test runtime.
