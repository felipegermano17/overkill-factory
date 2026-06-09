# Merchant Receipt Badge - Raw Paper

## Product Idea

Merchant Receipt Badge is a small validation product for the factory itself. A
merchant can display a read-only receipt badge for a simulated Solana devnet
order. The badge has an offchain receipt API, a visible dashboard and a
Quasar-oriented onchain work package, but the validation run must not sign,
deploy, write to devnet, touch mainnet or move funds.

## Business Shape

- User: a small merchant who wants a public proof that an order receipt exists.
- Buyer-visible value: the badge shows status, receipt hash and verification
  boundary.
- Merchant-visible value: the dashboard shows whether the receipt is verified,
  stale, offline or blocked by missing proof.
- Factory value: the product forces frontend, backend/API, data persistence,
  Product Face, Solana/Quasar, wallet boundary, security, QA, review, handoff
  and human gate routing.

## Constraints

- The run is public-safe validation only.
- No secrets may be requested, mounted, copied or inferred.
- No wallet signing.
- No devnet write.
- No mainnet write.
- No deploy.
- No production release.
- Onchain work is a Quasar package and Auditor route, not Anchor.
- If a real toolchain is missing, the worker must record a bounded waiver
  instead of claiming PASS.

## Expected Factory Outcome

The factory should turn this messy paper into a Hermes/Kanban execution graph,
route required workers, execute bounded evidence, block missing proof, reconcile
worker results and close only with Receipt Five evidence.
