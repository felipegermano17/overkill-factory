# Quickstart: Use Overkill Factory With Your Own Hermes

This guide gets an external operator from a fresh checkout to a local factory
smoke. It assumes no private Discord server, no private runtime and no prior
knowledge of this repository.

## 1. Prerequisites

Install:

- Git;
- Python 3.11 or newer;
- Hermes, if you want to run real Kanban cards instead of local contract checks;
- optional worker tools, such as Codex Security, Auditor, browser tooling or a
  remote proof runner, only when a card requires them.

You do not need Discord for the first run. Discord is optional cockpit UI, not
the source of truth.

## 2. Clone And Validate The Repository

```bash
git clone https://github.com/<owner>/overkill-factory.git
cd overkill-factory
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/validate_public_json_artifacts.py
python scripts/secret_safety_scan.py
python scripts/public_safety_scan.py
```

On Windows PowerShell, the same commands work with backslashes:

```powershell
python -m unittest discover -s tests -p "test_*.py" -q
python scripts\validate_public_json_artifacts.py
python scripts\secret_safety_scan.py
python scripts\public_safety_scan.py
```

If these fail, fix that first. A failing public validation means the checkout is
not a clean base for agent execution.

## 3. Configure Local Environment Values

Use `.env.example` as a safe template. Keep real values in your shell, password
manager or local-only dotenv file.

Minimum local-only settings:

```bash
HERMES_BIN=hermes
HERMES_PROFILES_DIR=./.hermes-profiles
OVERKILL_FACTORY_REPO=.
DISCORD_CONTROL_TOWER_ENABLED=false
```

Do not commit real bot tokens, API keys, private runtime paths or account ids.

## 4. Create Hermes Profiles For Public Workers

The public worker registry describes roles. Hermes profiles make those roles
operable in a runtime.

Preview profile materialization:

```bash
python scripts/materialize_hermes_profiles.py --profiles-dir ./.hermes-profiles
```

Apply it when the preview is acceptable:

```bash
python scripts/materialize_hermes_profiles.py --profiles-dir ./.hermes-profiles --apply
```

If you already have a trusted source profile and intentionally want to copy its
non-secret runtime shape, inspect the script help first:

```bash
python scripts/materialize_hermes_profiles.py --help
```

Only copy authentication after you understand the risk and can keep secrets
outside this public repository.

## 5. Run The Minimal Example

The smallest public-safe example lives in
`examples/minimal-hermes-project/`.

```bash
python scripts/factoryctl.py validate-card examples/minimal-hermes-project/card.md
python scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md
python scripts/factoryctl.py worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
```

The commands prove three things:

- the card has the required factory contract;
- the gate report can classify what must happen before the card moves;
- worker packets can be generated for Hermes profiles.

## 6. Connect The Adapter To Hermes

Read `adapters/hermes/README.md` before patching your Hermes checkout. The
adapter provides:

- a Kanban gate patch;
- a transition hook for worker routing;
- a done-time reconciliation model for Receipt Five and worker results.

From a Hermes checkout:

```bash
git switch -c overkill-factory-adapter
git apply <path-to-overkill-factory>/adapters/hermes/patches/0001-overkill-factory-v35-gates-official-main.patch
python -m pytest -q -o addopts='' tests/hermes_cli/test_overkill_factory_v35_gate.py
```

Then wire Hermes transition events to:

```bash
python <path-to-overkill-factory>/adapters/hermes/transition_hook.py --help
```

The adapter should be introduced in a test runtime before any real product or
release work.

## 7. Create A Real Project Entry

For your own project:

1. Start with a short paper or product brief.
2. Create a factory card from the relevant example in `examples/cards/`.
3. Fill source refs, scope, risk, runtime, security, forbidden actions and done
   definition.
4. Run `factoryctl.py validate-card`.
5. Run `factoryctl.py gate-report`.
6. Generate required worker packets.
7. Let Hermes create or route worker cards.
8. Attach worker results and Receipt Five before any `done` transition.

## 8. Observe Evidence And Receipts

Worker packets are assignments, not proof. A card is not complete until current
worker results, required reviews, human gates when needed and Receipt Five agree.

Look for:

- worker result artifacts;
- `receipt_five` metadata;
- `kanban_transition_event`;
- independent review records;
- human gate records for high-risk work;
- public safety and secret scan results before public release.

## 9. Full Validation Checklist

Before release or contribution, run:

```bash
python -m unittest discover -s tests
python scripts/validate_public_json_artifacts.py
python scripts/secret_safety_scan.py
python scripts/public_safety_scan.py
python scripts/release_integration_preflight.py --out .tmp/release-check.json
python scripts/factory_production_readiness.py --out .tmp/readiness-check.json
python scripts/worktree_release_inventory.py --out .tmp/inventory-check.json
```

Use `docs/operations/validation-and-release.md` for what each command proves.
