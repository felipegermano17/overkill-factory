# Fixtures

This directory contains public and negative test fixtures.

## What belongs here

- Public-safe repository assets that are required to validate or operate the Overkill Factory kernel.
- Source-controlled contracts, fixtures, helpers, or documentation that can be inspected by maintainers.
- No generated runtime output unless a test explicitly requires a stable fixture.

## What does not belong here

- Private Hermes runtime evidence.
- Operator secrets, local paths, keys, screenshots with private data, or generated worker packets.
- Temporary outputs from `.tmp`.
- Narrative product documentation that belongs under `docs/en` or `docs/pt-BR`.

## Validation

After changing this directory, run the relevant local checks from `factory/`:

```bash
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
python3 -m unittest discover -s tests -p 'test_*.py' -q
```

## Public documentation link

See `docs/pt-BR/uso.md` for the canonical public explanation. Internal README files are maintainer guides; they are not the product manual and must not become a second source of truth.
