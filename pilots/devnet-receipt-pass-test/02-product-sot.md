# Product SOT

Devnet Receipt Pass is a validation product that turns a product event into a
deterministic offchain receipt anchored to a read-only Solana devnet
observation.

The source of truth for this slice is:

- The product creates a receipt proof from a sample event and live devnet read.
- The dashboard shows the proof and explicitly disables signing and deploy.
- The onchain package defines the intended Quasar account and instruction model.
- The factory card routes every required worker and collects evidence before
  closure.
- Any claim beyond read-only devnet proof is blocked.

## Done Means

- The raw paper has a ledger, SOT and architecture.
- Product Face proof exists for desktop and mobile.
- Devnet read proof exists or the failure is recorded as blocking.
- Security, Auditor, Product Face, QA, independent review, release, monitoring,
  public safety, handoff, memory and skill/eval workers all have records.
- Receipt Five validates.
- Transition to done is allowed by the factory contract.
