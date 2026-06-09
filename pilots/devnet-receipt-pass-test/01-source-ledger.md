# Source Ledger

## Source Facts

- The raw paper requests an offchain receipt product tied to Solana devnet.
- The pilot must use Quasar as the onchain direction, not Anchor.
- The local validation boundary allows read-only devnet JSON-RPC.
- Signing, deploy, write access, secrets and funds are out of scope.
- The factory itself must prove agent routing, evidence and closure.

## Inferences

- A real devnet read is enough to prove network contact without crossing a
  signing boundary.
- A Quasar work package can be reviewed in preflight, but it is not a substitute
  for a real Auditor code audit.
- Product Face evidence must include desktop/mobile screenshots and state
  coverage because this product has a visible dashboard.

## Decisions

- The first slice will produce local artifacts only.
- The human gate is valid for this validation scope only.
- The card will intentionally trigger the full worker set so agent routing can
  be tested as a production-line mechanism.

## Open Conflicts

- The product has onchain intent, but the validation runtime lacks confirmed
  Quasar, Solana CLI and Rust toolchains. Resolution: mark Auditor as preflight
  with waiver and forbid any production audit claim.
- Release and monitoring workers are useful for line coverage, but no production
  promotion is authorized. Resolution: release workers review the boundary and
  record "no promotion".
