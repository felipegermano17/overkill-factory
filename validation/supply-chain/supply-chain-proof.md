# Supply Chain Proof

Result: `PASS`

## Controls

- Workflow security: `PASS`
- Dependency posture: `PASS`
- SBOM: `validation/supply-chain/source-sbom.spdx.json`
- SBOM SHA-256: `ae31aa843994a01830f8ce57550637c290bc4368ffd43ffe5f7670dc0dd39f72`

## Boundary

This proof covers the public factory repository CI and source inventory. It is not product-specific deployment, runtime dependency, signing, custody or production approval evidence.

## Next Action

Run this gate in CI and rerun via Hermes supply-chain-gate after workflow or dependency changes.
