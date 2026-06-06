# Supply Chain Proof

Result: `PASS`

## Controls

- Workflow security: `PASS`
- Dependency posture: `PASS`
- SBOM: `validation/supply-chain/source-sbom.spdx.json`
- SBOM SHA-256: `4c1c41a5099c5259bf7477d0e3710ff97db2c452cf802157fb727770582c0f1e`

## Boundary

This proof covers the public factory repository CI and source inventory. It is not product-specific deployment, runtime dependency, signing, custody or production approval evidence.

## Next Action

Run this gate in CI and rerun via Hermes supply-chain-gate after workflow or dependency changes.
