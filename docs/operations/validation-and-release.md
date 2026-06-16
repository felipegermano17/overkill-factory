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
python scripts/validate_planning_bundles.py
python scripts/validate_public_surface_sync.py
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
factoryctl status-snapshot --card examples/minimal-hermes-project/card.md --out .tmp/factory-status-snapshot.json
```

What this proves:

- the card has the required fields;
- the risk, surface and phase routing can be inspected;
- worker packets can be produced without inventing completion evidence.
- operator status can be projected without becoming the source of truth.

## Public Release Preflight

Run this before a public branch, release tag or pull request:

```bash
python scripts/release_integration_preflight.py --out .tmp/release-check.json
python scripts/factory_production_readiness.py --out .tmp/readiness-check.json
python scripts/worktree_release_inventory.py --out .tmp/inventory-check.json
python scripts/validate_public_surface_sync.py --check-published
```

These commands write local summaries under `.tmp` when an output path is
provided. Generated summaries must not be committed as release proof.

`release_integration_preflight.py` must run its materializers in the current
process. Existing `.tmp` summaries are evidence inputs only after fresh
materialization; stale files cannot support a release `PASS`.

`validate_public_surface_sync.py --check-published` compares the validated local
map to the published public object. Run it only after the public object has been
published or refreshed; before publication it may correctly report the remote
map as out of sync.

## Full Product Worker Graph

Production completion uses a product-scoped worker graph. The default contract
is the public QVG validation product:

```bash
python scripts/production_full_product_worker_graph.py --no-write
```

For another product, provide a graph contract instead of editing the script:

```bash
python scripts/production_full_product_worker_graph.py \
  --graph-contract path/to/production-full-product-graph.contract.json \
  --out .tmp/factory-runs/production/full-product-worker-graph.json
```

The contract binds the graph to Product SOT, selected capability packs, delivery
quality profile, risk class, promotion ladder, environment class and evidence
lanes. Strict lanes must prove the same `product_id` as the contract; a PASS for
one product cannot be reused for another product by changing prose.

## Full Validation Battery

For a stronger local pass:

```bash
factoryctl doctor
factoryctl run minimal
python scripts/factory_battery.py
python scripts/validate_document_governance.py
python scripts/validate_worker_profiles.py
python scripts/validate_public_json_artifacts.py
python scripts/validate_planning_bundles.py
python scripts/validate_public_surface_sync.py
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

Release authority cannot be satisfied by a string ref alone. A production or
R4 release gate must dereference and validate the human gate record before it
can claim `PASS`.

No single chat answer, dashboard status or worker packet is a release proof.
