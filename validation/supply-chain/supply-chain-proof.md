# Supply Chain Proof

Result: `PASS`

## Controls

- Workflow security: `PASS`
- Dependency posture: `PASS`
- SBOM: `validation/supply-chain/source-sbom.spdx.json`
- SBOM SHA-256: `9ebb0fa1cb0b32f930e971d3b077a2037296f25244d471b5e57846f24624a36e`

## Boundary

This proof covers the public factory repository CI and source inventory. It is not product-specific deployment, runtime dependency, signing, custody or production approval evidence.

## Next Action

Run this gate in CI and rerun via Hermes supply-chain-gate after workflow or dependency changes.
