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

## Boundary

Point 5 is intentionally deferred. This guide makes installation easy, but it
does not claim an official real Hermes E2E harness. Until that harness exists,
operator-owned Hermes validation must happen in the user's own test runtime.
