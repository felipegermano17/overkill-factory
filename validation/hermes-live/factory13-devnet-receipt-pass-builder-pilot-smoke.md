# Factory 13 Devnet Receipt Pass Builder Pilot Smoke

Date: 2026-06-06

Machine-readable smoke:

- `validation/hermes-live/factory13-devnet-receipt-pass-builder-pilot-smoke.json`

## Scope

This smoke records the product-specific Factory 13 builder-layer pilot. It is
stronger than the profile smoke because it uses a real card, worker packets,
worker result records, Product Face proof, devnet read proof, Receipt Five and
an enforced done transition plan.

## Result

PASS for bounded validation scope.

- Required workers: 28.
- Worker result records: 28.
- Worker packets: 28.
- Builder workers triggered: 8.
- `implementation-worker`: not required because surface-specific builders owned
  the matched implementation surfaces.
- Done transition: `allow_done`.

## Builders Triggered

- `frontend-builder`
- `backend-api-builder`
- `data-persistence-builder`
- `solana-quasar-builder`
- `solana-quasar-qa-engineer`
- `wallet-transaction-builder`
- `integration-builder`
- `test-automation-builder`

## Evidence

- Card: `pilots/devnet-receipt-pass-factory13-test/cards/drp-factory13-builder-pilot.md`
- Receipt: `pilots/devnet-receipt-pass-factory13-test/evidence/receipt-five-factory13.json`
- Transition plan: `pilots/devnet-receipt-pass-factory13-test/evidence/transition-plan-done.json`
- Worker index: `pilots/devnet-receipt-pass-factory13-test/evidence/worker-result-index.json`
- Product Face: `pilots/devnet-receipt-pass-factory13-test/worker-results/product-face-result.json`
- Devnet proof: `products/devnet-receipt-pass/offchain/devnet-read-proof.json`
- Pilot devnet proof: `pilots/devnet-receipt-pass-factory13-test/devnet/devnet-read-proof.json`

## Boundary

This is not production readiness. Solana/Quasar builder, Solana/Quasar QA and
Auditor did not fake a code-build or audit pass. They produced explicit waivers
because the validation runtime lacks Solana, Quasar, Rust and Docker toolchain
proof.

Before any write-capable or production onchain claim, run real Quasar build,
Quasar/SVM/devnet-safe QA and the full Auditor code-audit path.
