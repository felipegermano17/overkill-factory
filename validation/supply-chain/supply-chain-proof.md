# Supply Chain Proof

Result: `PASS`

## Controls

- Workflow security: `PASS`
- Dependency posture: `PASS`
- SBOM: `validation/supply-chain/source-sbom.spdx.json`
- SBOM SHA-256: `9519267c2ed3d0370cc55173309fb669674bbef01def97e4a9b7563b3221cd42`

## Boundary

This proof covers the public factory repository CI and source inventory. It is not product-specific deployment, runtime dependency, signing, custody or production approval evidence.

## Next Action

Run this gate in CI and rerun via Hermes supply-chain-gate after workflow or dependency changes.
