# Architecture Candidate

## Components

- `receipt-service.mjs`: Node.js read-only devnet runner.
- `dashboard.html`: static Product Face.
- `onchain/quasar`: Quasar-oriented program outline.
- Factory artifacts: card, worker packets, worker results, Receipt Five and
  transition plan.

## Flow

1. Operator provides the raw paper.
2. Source Ledger separates facts, inference, decisions and conflicts.
3. Product SOT defines the validation product.
4. Architecture defines offchain, Product Face and onchain boundaries.
5. Product Face captures screenshots and state evidence.
6. Security and onchain workers review boundaries.
7. Human gate approves validation-only scope.
8. Decomposition creates a Hermes-ready card.
9. Workers produce result records.
10. Receipt Five closes the card only if validation and worker closure pass.

## Why This Shape

Read-only devnet is better than a fake onchain proof because it exercises a real
network dependency. It is better than write access for this pilot because write
access would require signing, keys and a stricter human gate that is outside the
current validation scope.

Quasar preflight is better than claiming a full onchain audit because the local
runtime does not prove a real Quasar build and Auditor run. The factory should
prefer an honest waiver over a false pass.
