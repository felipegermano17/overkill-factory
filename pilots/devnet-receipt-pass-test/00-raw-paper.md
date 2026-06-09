# Raw Paper: Devnet Receipt Pass

## Product Idea

Build a small receipt product that proves a product event happened near a
Solana devnet observation. The first version reads devnet only, creates an
offchain receipt proof, shows the receipt in a simple dashboard and prepares a
future Quasar onchain receipt program.

## User Need

Operators need a quick way to attach a verifiable development receipt to a
product event without accidentally signing, deploying or touching funds.

## Scope

- Read Solana devnet using JSON-RPC.
- Create a deterministic offchain proof.
- Show receipt, cluster and safety boundary states.
- Prepare a Quasar-oriented onchain work package.
- Exercise the full factory line with agents, reviews, evidence and closure.

## Non-Goals

- No wallet signing.
- No devnet write.
- No mainnet write.
- No production deploy.
- No funds, custody or key management.
- No claim of real Quasar code audit.

## Success

The pilot succeeds when the factory can move from this paper to a validated
completion packet with Product Face proof, security evidence, Auditor preflight,
specialist reviews, handoff, release boundary, monitoring boundary and Receipt
Five metadata.
