# Quasar Work Package

This package is a Quasar-oriented source outline for the Devnet Receipt Pass
pilot. It is not compiled in this validation environment because Rust, Solana
CLI and Quasar are intentionally not assumed to exist.

The factory must treat this as an onchain work package, not as a deployed
program. Auditor evidence is mandatory before any production claim.

## Planned Account Model

- `receipt_state`: PDA keyed by operator and receipt hash.
- `operator_identity`: signer in a future write-capable environment.
- `receipt_event`: append-only event metadata for the offchain receipt.
- `audit_receipt`: durable audit pointer produced after Auditor review.

## Planned Instructions

- `init_receipt`: initializes a receipt PDA.
- `append_receipt_event`: appends a bounded receipt event.
- `close_receipt`: closes a test receipt after review.

## Forbidden In This Pilot

- Real signing.
- Devnet write.
- Mainnet write.
- Funds movement.
- Upgrade authority changes.
- Custody or key handling.
