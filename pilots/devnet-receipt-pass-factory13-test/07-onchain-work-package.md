# Onchain Work Package

## Framework

Quasar, not Anchor.

## Planned Accounts

- `receipt_state`: PDA using `[receipt, operator, receipt_hash]`.
- `operator_identity`: signer in future write-enabled work.
- `receipt_event`: event record for append-only proof.
- `audit_receipt`: evidence pointer after Auditor review.

## Planned Instructions

- `init_receipt(operator, receipt_hash, created_slot)`.
- `append_receipt_event(receipt_hash, event_hash, observed_slot)`.
- `close_receipt(receipt_hash)`.

## Security Questions

- Are seeds collision-resistant and domain separated?
- Can events be replayed across operators?
- Does closing a receipt prevent append?
- Are compute and storage bounded?
- Is upgrade authority handled by a later production gate?

## Pilot Boundary

This is not deployed. The pilot only produces source outline and preflight
review evidence. Any real write path requires a new card with signer handling,
toolchain proof and Auditor code audit.
