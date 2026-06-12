# Products

This directory contains public validation products used to exercise product-like
and production-lane factory checks.

## What Belongs Here

- Public validation products that are safe to inspect, rerun and reference in
  tests.
- Product-shaped fixtures that help validate Receipt Five, release readiness,
  Product Face proof or security gates.
- Minimal product material that is intentionally public and reproducible.

## What Does Not Belong Here

- No private product material.
- No customer, workspace, board, key, deployment or internal project evidence.
- A validation product is not production approval and must not be presented as
  a live release.

## Source Of Truth

The public validation product is only a fixture when it is covered by schemas,
tests, scripts or a documented release-readiness command. Production approval
must still come from the real runtime, receipt and human gate records.

## How It Is Validated

Run product and release checks before relying on these fixtures:

```bash
python scripts/validate_public_json_artifacts.py
python scripts/factory_production_readiness.py
python scripts/worktree_release_inventory.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
```
