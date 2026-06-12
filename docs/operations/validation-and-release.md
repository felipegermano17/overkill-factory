# Validation And Release

This page lists the commands an external contributor or release operator should
run before claiming that a checkout is ready.

## Fast Local Check

Use this before editing cards, docs or examples:

```bash
factoryctl doctor
factoryctl run minimal
python -m unittest discover -s tests
python scripts/validate_document_governance.py
python scripts/validate_public_json_artifacts.py
python scripts/validate_worker_profiles.py
python scripts/secret_safety_scan.py
python scripts/public_safety_scan.py
python scripts/supply_chain_proof.py --check --no-write
```

## Factory Contract Check

Use a card-specific check before sending work to Hermes:

```bash
factoryctl validate-card examples/minimal-hermes-project/card.md
factoryctl gate-report --card examples/minimal-hermes-project/card.md
factoryctl worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
```

What this proves:

- the card has the required fields;
- the risk, surface and phase routing can be inspected;
- worker packets can be produced without inventing completion evidence.

## Public Release Preflight

Run this before a public branch, release tag or pull request:

```bash
python scripts/release_integration_preflight.py --out .tmp/release-check.json
python scripts/factory_production_readiness.py --out .tmp/readiness-check.json
python scripts/worktree_release_inventory.py --out .tmp/inventory-check.json
```

These commands write local summaries under `.tmp` when an output path is
provided. Generated summaries must not be committed as release proof.

## Full Validation Battery

For a stronger local pass:

```bash
factoryctl doctor
factoryctl run minimal
python scripts/factory_battery.py
python scripts/validate_document_governance.py
python scripts/validate_worker_profiles.py
python scripts/validate_public_json_artifacts.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python scripts/supply_chain_proof.py --check --no-write
python scripts/factory_completion_audit.py --no-write --require-complete
python -m unittest discover -s tests -p "test_*.py" -q
```

If a command fails, do not weaken the validator. Fix the contract, data model,
docs or fixture that caused the failure.

## Windows Notes

PowerShell examples:

```powershell
New-Item -ItemType Directory -Force .tmp
factoryctl doctor
factoryctl run minimal
python -m unittest discover -s tests -p "test_*.py" -q
python scripts\release_integration_preflight.py --out .tmp\release-check.json
python scripts\factory_production_readiness.py --out .tmp\readiness-check.json
python scripts\worktree_release_inventory.py --out .tmp\inventory-check.json
```

Keep generated `.tmp` outputs out of commits.

## Release Claim Rule

A release claim needs:

- passing tests and scans;
- current worker evidence, not stale worker packets;
- Receipt Five with verification commands and artifact refs;
- independent review when required;
- real human gate records for high-risk or release authority;
- public-safety pass before public publication.

No single chat answer, dashboard status or worker packet is a release proof.
