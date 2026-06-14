# Open Source Security

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: SECURITY.md, scripts/supply_chain_proof.py,
> scripts/public_safety_scan.py, scripts/secret_safety_scan.py, tests/
> Runtime boundary: This is repository security posture. It does not replace
> product-specific security review, Codex Security, Auditor or human gates.

## Required Controls

- CodeQL runs for Python code scanning.
- Dependency Review runs on pull requests.
- Dependabot tracks GitHub Actions and Python dependency surfaces.
- `scripts/supply_chain_proof.py` validates pinned workflow actions and writes
  an SPDX SBOM when requested.
- `scripts/secret_safety_scan.py` blocks obvious secrets.
- `scripts/public_safety_scan.py` blocks private/public boundary leaks.
- `secret_delivery_policy` and `agent_runtime_hardening_profile` describe how
  material workers receive credentials and what runtime boundaries enforce.

## Local Check

```bash
python scripts/secret_safety_scan.py
python scripts/public_safety_scan.py
python scripts/supply_chain_proof.py --check --no-write
```

## Boundary

These checks protect the public repository. They do not prove that a user's
product, Hermes runtime, production deployment, keys, wallets or cloud
environment are secure.

Passing `scripts/secret_safety_scan.py` means the scanned files did not contain
known secret patterns. It does not prove that an autonomous worker received
credentials safely at runtime. Material execution must use placeholder,
simulator, user-mediated, JIT, signer or scoped-service delivery unless a real
human-gated exception exists.
