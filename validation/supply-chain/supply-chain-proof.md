# Supply Chain Proof

Result: `PASS`

## Controls

- Workflow security: `PASS`
- Dependency posture: `PASS`
- SBOM: `validation/supply-chain/source-sbom.spdx.json`
- SBOM SHA-256: `3707ec22070c1764cce456699e5e4b1be6adc809688ef4e8112aa943c2daf9ea`

## Boundary

This proof covers the public factory repository CI and source inventory. It is not product-specific deployment, runtime dependency, signing, custody or production approval evidence.

## Next Action

Run this gate in CI and rerun via Hermes supply-chain-gate after workflow or dependency changes.
