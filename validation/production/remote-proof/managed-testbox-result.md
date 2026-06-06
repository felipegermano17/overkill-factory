# Crabbox Ephemeral Container Remote Proof

Result: `PASS`
Provider: `local-container`
Reusable for product: `true`
Lease stopped: `true`
Lease id: `cbx_dee862ddecd0`
Total runtime ms: `3897`

## What Ran

`python3 --version && python3 scripts/validate_public_json_artifacts.py && python3 scripts/secret_safety_scan.py && python3 scripts/public_safety_scan.py && python3 scripts/full_product_worker_graph.py --require-pass`

## Boundary

This is a real Crabbox-managed ephemeral container proof. It is not a brokered cloud lease and not Blacksmith Testbox; those paths still require their own credentials if a project policy mandates that exact provider.
