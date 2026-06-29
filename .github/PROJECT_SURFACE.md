# GitHub Project Surface

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: root README, `docs/`, `factory/pyproject.toml`, `.github/workflows/`, `factory/tests/`.
> Runtime boundary: GitHub automation protects the public repository. Hermes remains the runtime source of truth for real factory cards.

## What Belongs Here

This folder contains GitHub project automation: issue templates, pull request templates, Dependabot configuration, community files and CI/security workflows.

## Root Repository Shape

The repository root is intentionally small:

- `README.md` explains the product quickly.
- `LICENSE` is the public license.
- `docs/` is the human documentation.
- `factory/` is the factory code, schemas, tests, internal technical contracts and fixtures.
- `.github/` is repository automation and contribution hygiene.

Do not add generated worker packets, historical proof, screenshots, private runtime exports, local workspace paths, secrets or internal validation logs. Those belong in local `.tmp/`, private evidence storage or sanitized release artifacts.

## Validation

```bash
cd factory
python scripts/supply_chain_proof.py --check --no-write
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python -m unittest discover -s tests -p "test_*.py" -q
```
