# Factory 12 Pilot Retrospective

## Result

The Devnet Receipt Pass pilot completed the full validation line for public
artifact scope.

The card generated 27 worker packets, required the blocking workers for this
bounded validation scope, generated 27 worker result records,
validated Receipt Five and produced an `allow_done` transition plan with no
missing or invalid blocking workers.

This was a Factory 12 pilot. It predates the Factory 13 builder-layer split, so
it should not be read as proof that the ten specialist builders have executed a
real product card.

## What Worked

- The factory handled raw paper, source ledger, Product SOT, architecture,
  Product Face, security, onchain preflight, decomposition, worker packets,
  worker results, review, human gate, handoff, public safety and closure.
- Solana devnet was contacted through read-only JSON-RPC.
- Product Face screenshots were captured for desktop and mobile.
- Public safety, secret safety, worker profile validation and unit tests passed.
- The card used the full worker graph instead of only the obvious workers.
- Product-specific packet smoke verified that 27/27 generated worker packets
  have Hermes profile bindings, queue policy, skill refs, result schemas and
  evidence policy.

## Honest Boundaries

- No deploy was attempted.
- No devnet write was attempted.
- No wallet signing was attempted.
- No secret or key was used.
- No production release was approved.
- The Auditor result is a preflight waiver, not a code-audit pass.
- Remote proof was waived because local proof satisfied the validation scope;
  remote proof remains a future production-parity gate.

## What This Proves

The factory can route a complete worker set and fail closed when core contracts
are missing. During the pilot, the public JSON validator caught missing schemas
and an invalid worker-result index shape. The correct response was to add
schemas and fix the artifact, not bypass validation.

## What Still Needs A Future Gate

- Real Quasar toolchain install.
- Real Solana/Quasar build and tests.
- `solanabr/Auditor` code audit with corpus/checklist coverage.
- Write-capable devnet test with signer controls.
- Remote proof with cleanup evidence.
- Production release and monitoring plan.

## Score

Factory-line validation score: 10/10 for the bounded public validation goal.

Production-readiness score: not claimed. That would require a separate card
with write, deploy, audit, monitoring and release authority.

Factory 13 builder-readiness score: not claimed by this pilot. It requires a
new full-line run with specialist builder result fields.
