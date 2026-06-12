# Release Policy

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: README.md, CHANGELOG.md, pyproject.toml,
> docs/operations/validation-and-release.md, tests/
> Runtime boundary: This policy governs public repository releases. It does not
> approve production use of any user's product.

## Versioning

Use semantic versioning:

- patch for docs, examples, validation and compatibility fixes;
- minor for new public CLI commands, schemas, adapters or worker contracts;
- major for breaking card, receipt, adapter or CLI behavior.

## Before A Release

Run:

```bash
factoryctl doctor
factoryctl run minimal
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/validate_document_governance.py
python scripts/validate_public_json_artifacts.py
python scripts/validate_worker_profiles.py
python scripts/secret_safety_scan.py
python scripts/public_safety_scan.py
python scripts/supply_chain_proof.py --check --no-write
```

## Release Artifact Rules

- Update `CHANGELOG.md`.
- Keep generated proof under `.tmp/` or release artifacts, not committed docs.
- Tag only from a clean `main` that matches `origin/main`.
- Publish package artifacts only after the release checks pass.

## Deferred Runtime Harness

Point 5 is intentionally deferred. A public release may validate local CLI,
schemas, docs, examples and adapter compatibility, but it must not claim an
official real Hermes E2E harness until that harness exists and is tested.
