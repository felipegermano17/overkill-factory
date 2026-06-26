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
python scripts/generate_factory_reference_docs.py --check
python scripts/validate_public_json_artifacts.py
python scripts/validate_promise_implementation_map.py
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
python scripts/factory_production_gate_receipts.py \
  --runtime-status-evidence .tmp/factory-runs/hermes-live/hermes-runtime-readonly-evidence.json
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

`factory_production_gate_receipts.py` materializes the public-safe receipts that
the aggregate production gate consumes. It may write `BLOCKED` receipts when
Hermes runtime status, private Control Tower evidence or release integration is
not ready. That is expected: the aggregate gate remains
`factory_production_readiness.py`, not the materializer.

For a live Hermes validation run, pass a public-safe runtime evidence JSON with
`--runtime-status-evidence`. Running without that file intentionally fails the
runtime status receipt closed.

## Hermes Update Guard

Run this whenever Hermes itself is updated or when a gateway restart is needed
after an update:

```bash
python scripts/hermes_update_guard.py plan --board <board-slug>
python scripts/hermes_update_guard.py evaluate \
  --doctor .tmp/hermes-update/doctor.txt \
  --gateway-status .tmp/hermes-update/gateway-status.txt \
  --kanban-stats .tmp/hermes-update/kanban-stats.txt \
  --processes .tmp/hermes-update/processes.txt \
  --sudo-check .tmp/hermes-update/sudo-check.txt \
  --board <board-slug> \
  --out .tmp/hermes-update/update-guard.json
```

The receipt is `BLOCKED` while an update process is still active or the board
has `running` tasks. It is `ATTENTION` when a human operator must migrate config
or restart the system gateway. Do not dispatch, unblock or complete factory work
until the guard is clear and `hermes gateway status` is current.

## Factory v1 Completion Gate

Use this after the release preflight and GitHub checks are current, when the
question is whether the public Factory v1 kernel can be closed instead of
continuing an open-ended audit:

```bash
factoryctl signal-coverage --out .tmp/factory-runs/signal-coverage/factory-signal-coverage-scorecard.json
factoryctl v1-completion-gate \
  --release-preflight .tmp/factory-runs/release/release-integration-preflight.json \
  --github-actions-result PASS \
  --open-v1-blockers 0 \
  --open-prs 0 \
  --out .tmp/factory-runs/v1-completion/factory-v1-completion-gate.json
```

A `PASS` here means the public Factory v1 kernel may be closed. It does not
claim product-specific completion, hosted service release, mainnet release or
universal runtime proof. New findings after this gate must be classified as
`v1_blocker`, `vnext` or `not_planned`; only a real v1 blocker reopens the v1
finish line.

## Full Product Worker Graph

Production completion uses a product-scoped worker graph. The default contract
is the QVG product-shaped validation fixture:

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
python scripts/generate_factory_reference_docs.py --check
python scripts/validate_worker_profiles.py
python scripts/validate_public_json_artifacts.py
python scripts/validate_promise_implementation_map.py
python scripts/validate_public_surface_sync.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python scripts/supply_chain_proof.py --check --no-write
factoryctl signal-coverage --out .tmp/factory-runs/signal-coverage/factory-signal-coverage-scorecard.json
factoryctl validate-method-engines templates/method-engine-registry.json
factoryctl operating-system-scorecard --out .tmp/factory-runs/operating-systems/factory-operating-system-scorecard.json
python scripts/hermes_runtime_proof.py --boards-json .tmp/hermes-runtime/boards.json --profile-list-text .tmp/hermes-runtime/profile-list.txt --status-text .tmp/hermes-runtime/status.txt --task-list-json .tmp/hermes-runtime/task-list.json --done-task-runs-json .tmp/hermes-runtime/done-task-runs.json --blocked-task-show-json .tmp/hermes-runtime/blocked-task-show.json --out .tmp/factory-runs/hermes-runtime/hermes-worker-runtime-proof.json
factoryctl operating-system-scorecard --runtime-proof .tmp/factory-runs/hermes-runtime/hermes-worker-runtime-proof.json --out .tmp/factory-runs/operating-systems/factory-operating-system-scorecard-runtime-proven.json
python scripts/factory_completion_audit.py --runtime-proof .tmp/factory-runs/hermes-runtime/hermes-worker-runtime-proof.json --no-write --require-complete
python -m unittest discover -s tests -p "test_*.py" -q
```

If a command fails, do not weaken the validator. Fix the contract, data model,
docs or fixture that caused the failure.

Keep the scorecards separate:

- OS scorecard with runtime proof proves the factory operating spine.
- Completion audit proves whether the current product/release can be claimed.
- Completion audit with `--runtime-proof` clears only runtime-backed
  requirements; it does not clear product/release/security proof.
- A product can remain `BLOCKED` even when the operating spine is green.

## Windows Notes

PowerShell examples:

```powershell
New-Item -ItemType Directory -Force .tmp
factoryctl doctor
factoryctl run minimal
python -m unittest discover -s tests -p "test_*.py" -q
python scripts\release_integration_preflight.py --out .tmp\release-check.json
python scripts\factory_production_gate_receipts.py
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
- a Factory v1 Completion Gate `PASS` before claiming the public Factory v1
  kernel is closed.

Release authority cannot be satisfied by a string ref alone. A production or
R4 release gate must dereference and validate the human gate record before it
can claim `PASS`.

No single chat answer, dashboard status or worker packet is a release proof.
