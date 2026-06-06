# QVG Product-Like Quasar Program

This is a public, product-like Quasar target for Overkill Factory validation.
It is intentionally bounded: no deploy, no devnet/mainnet write, no wallet
signing, no custody and no funds movement.

The target exists so the factory can test the Solana/Quasar/Auditor path
against source code that is closer to a product than the generated minimal
Quasar template.

## Scope

- `review_vault_instruction`: validates an operator-signed review request for a
  vault instruction hash.
- `record_audit_receipt`: validates an operator-signed audit receipt hash.
- `block_instruction`: validates an operator-signed block reason.

## Accounts

- `operator`: signer for the dry product proof.
- `vault_state`: PDA derived from `["vault", operator]`.
- `pending_instruction`: PDA derived from `["pending", vault_state]`.
- `audit_receipt`: PDA derived from `["audit", vault_state]`.

## Boundary

This is a product-like validation target, not production source. It is useful
for proving the factory can compile, test and audit a Quasar target through
Hermes. It is not reusable as an approval for a real product without a separate
product paper, source ledger, architecture, threat model, Auditor run and human
gate.
