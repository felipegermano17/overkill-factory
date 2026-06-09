# Hermes Supply-Chain Gate Summary

Result: PASS

## Scope

This summary covers the public repository supply-chain gate proof for the currently applied uncommitted diff. It is public-safe gate evidence only. It is not product runtime approval, deployment approval, signing approval, custody evidence, or production approval.

## Diff reviewed

- `.github/workflows/ci.yml` adds a CI step named `Supply-chain proof` that runs `python scripts/supply_chain_proof.py --check --no-write`.
- New public supply-chain artifacts are present under `validation/supply-chain/`.
- New supply-chain proof implementation, schema, and tests are present under `scripts/`, `schemas/`, and `tests/`.
- F44 map/docs references add public supply-chain CI/SBOM proof language and map labels only; no local paths, private workspace names, Hermes task identifiers, Hermes board identifiers, auth paths, tokens, secrets, devnet/mainnet authority claims, funds, custody, deployment approval, or production approval evidence were identified in the F44 additions.

## Required command evidence

All required commands completed successfully in the repository workspace:

1. `python3 scripts/supply_chain_proof.py`
   - Exit: 0
   - Output: wrote `validation/supply-chain/supply-chain-proof.json`, `validation/supply-chain/source-sbom.spdx.json`, and `validation/supply-chain/supply-chain-proof.md`; result `PASS`.
2. `python3 scripts/validate_public_json_artifacts.py`
   - Exit: 0
   - Output: `OK`.
3. `python3 scripts/public_safety_scan.py`
   - Exit: 0
   - Output: `OK`.
4. `python3 scripts/secret_safety_scan.py`
   - Exit: 0
   - Output: `OK`.
5. `python3 -m unittest discover -s tests -p "test_*.py" -q`
   - Exit: 0
   - Output: `Ran 65 tests`; result `OK`.
6. `git diff --check`
   - Exit: 0
   - Output: no whitespace errors reported.

## Workflow inspection

`.github/workflows/ci.yml` was inspected directly:

- Top-level permissions are least-privilege for this CI job: `contents: read` only.
- External GitHub Actions are commit-pinned to full 40-character SHAs:
  - `actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5`
  - `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`
- No unpinned external action references were found in the workflow.

## Generated proof artifacts

- `validation/supply-chain/supply-chain-proof.json`
  - Result: `PASS`
  - Blocking findings: `false`
  - Evidence kind: `real`
  - Reusable for public repository release: `true`
  - Reusable for product work: `false`
- `validation/supply-chain/source-sbom.spdx.json`
  - Format: SPDX 2.3 JSON
  - Source file inventory count: 504 files
  - SHA-256: `ae31aa843994a01830f8ce57550637c290bc4368ffd43ffe5f7670dc0dd39f72`
- `validation/supply-chain/supply-chain-proof.md`
  - Result: `PASS`
  - Workflow security: `PASS`
  - Dependency posture: `PASS`

## Boundary and residual risk

- No package dependency manifest is currently present, so the dependency posture proof is limited to the current standard-library Python proof runners and pinned GitHub Actions.
- Future runtime dependencies must add lockfile and audit evidence before release.
- This summary intentionally omits local absolute paths, task or board identifiers, private runtime identifiers, authentication paths, tokens, and private workspace names.
