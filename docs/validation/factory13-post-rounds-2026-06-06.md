# Factory 13 Post-Rounds Validation

Date: 2026-06-06

This note records the immediate post-Factory 13 validation rerun after the
builder/operator layer was added and the Whimsical factory map was updated.

## What Was Rerun

| Check | Result | Meaning |
|---|---:|---|
| `python scripts/factory_battery.py` | PASS, 12/12 | Multi-context routing, invalid-card rejection and `done` reconciliation still pass. |
| `python scripts/validate_worker_profiles.py` | PASS | Public worker profiles and bindings are still schema-valid. |
| `python scripts/validate_public_json_artifacts.py` | PASS | Public JSON artifacts remain schema-valid. |
| `python scripts/public_safety_scan.py` | PASS | No public-safety leak was detected by the repository scanner. |
| `python scripts/secret_safety_scan.py` | PASS | No secret-like content was detected by the repository scanner. |
| `python scripts/factory_completion_audit.py --no-write --require-complete` | COMPLETE | The current public validation branch still satisfies the completion audit. |
| `python -m unittest discover -s tests -p "test_*.py" -q` | PASS, 107 tests | Unit and regression tests still pass. |

## Battery Coverage

The current battery covers:

- Product Face SaaS R2 routing;
- Solana/Quasar R3 routing;
- cloud release R4 routing;
- public repository release blocking;
- agentic/browser/memory R3 routing;
- invalid Product Face blocking;
- invalid onchain/no-Auditor blocking;
- invalid R4/no-human-gate blocking;
- invalid security/no-scan blocking;
- invalid self-review blocking;
- `done` blocked when worker results are missing;
- `done` allowed when all required worker results are present.

## Factory 13 Product-Specific Pilot Evidence

The Factory 13 pilot remains the product-specific proof for the new builder
layer:

- required workers: 28;
- worker result records: 28;
- worker packets: 28;
- builders triggered: frontend, backend/API, data persistence, Solana/Quasar,
  Solana/Quasar QA, wallet/transaction, integration and test automation;
- `implementation-worker` was not required because a surface-specific builder
  owned the card;
- honest boundary preserved: no wallet signing, no devnet write, no program
  deploy, no real Quasar build/test claim and no real Auditor code-audit claim
  in that pilot.

## Factory 13 Hermes Evidence Reconciliation Rerun

Testing standard: this is only counted as a factory test when Hermes itself runs
the production line through durable Kanban state: board, card, assigned profile,
run log, worker result, Receipt Five evidence and gate transition. Local scripts
are preflight/debug support, not a substitute for end-to-end factory execution.

The follow-up real Hermes run added `evidence-reconciler` as a first-class
closure worker and executed it on a private validation board.

Evidence:

- real Hermes profile created: `evidence-reconciler`;
- failed attempt recorded: Codex-only `hermes-kanban` skill is not a Hermes
  runtime skill;
- failed attempt recorded: the new profile needed runtime auth copied from an
  existing worker profile;
- successful Hermes worker card: redacted private card id;
- generated artifacts:
  `validation/hermes-live/real-e2e-202606062115/evidence-reconciliation-index.json`,
  `validation/hermes-live/real-e2e-202606062115/worker-results/evidence-reconciler-result.json`,
  `validation/hermes-live/real-e2e-202606062115/receipt-five-reconciliation-draft.json`,
  `validation/hermes-live/real-e2e-202606062115/transition-plan-receipt-five-to-done.json`;
- `validate-receipt` now passes for the blocked draft shape;
- final transition action remains `block_transition`.

Current blockers found by the real reconciler:

- `appsec_owasp_result`;
- `autoreview_result`;
- `crypto_key_management_result`;
- `independent_review_result`;
- `public_safety_result`;
- `qa_verification_result`;
- `solana_quasar_build_result`;
- `solana_quasar_qa_result`.

This is a better result than forcing a green pilot. The factory now preserves
stale-result supersession, recognizes current blocking evidence and prevents an
agent from treating scattered worker output as a completed Receipt Five.

## Real Hermes Battery Checkpoint

The follow-up production-floor battery is still a checkpoint, not a completed
release verdict. Hermes was used as the actual execution surface, not just as a
fixture generator.

Observed board state at the checkpoint:

- 25 total real Hermes cards in scope;
- 19 cards completed with worker evidence;
- 4 cards blocked;
- 2 cards still running;
- 0 cards waiting in `ready`.

Completed worker coverage includes source ledger, Product SOT, architecture,
decomposition, implementation, QA, Product Face, Codex Security, Solana/Quasar
Auditor route, independent review, human-gate clerk, AppSec/OWASP, agentic AI
security, crypto/key management, public safety, supply chain, handoff and the
security orchestrator.

The remaining blockers are product-real blockers, not paperwork:

- main factory gate: blocked until dependent evidence and Receipt Five reconcile;
- documentation OS: blocked and still needs a valid durable docs result;
- AutoReview: blocked because the done transition still returns blocking
  Receipt Five reasons;
- remote proof: blocked because the clean container proof found failures and the
  retry path was denied by the worker environment.

The two running repair cards are also meaningful:

- evidence reconciliation repair for public JSON/profile validation;
- Product Face repair for measured horizontal overflow across desktop, tablet
  and mobile states.

This checkpoint is valuable because it caught exactly the failure modes the
factory is supposed to catch: stale evidence, missing durable documentation,
visual overflow, public JSON/profile drift, and an attempted done transition
before all required worker results were valid.

## Critical Read

This rerun proves the current factory rules did not regress after Factory 13.
It also proves the operator layer can route builders instead of using a generic
implementation worker for every task.

It does not, by itself, prove that every future product can be delivered
end-to-end. The battery is still stronger at routing, blocking and evidence
reconciliation than at full product diversity. A real universal `10/10` requires
more product-shaped rounds, not just more passing gate fixtures.

## Next Heavy Rounds

Run at least these next product-shaped validations before treating the factory
as broadly validated:

1. a visible SaaS/offchain product from raw paper through Product Face,
   implementation, browser proof, review and release gate;
2. an onchain devnet product with Quasar source changes, Auditor route, CU/SVM
   or equivalent runtime proof and no simulated approval;
3. an agentic/browser/memory product that stresses prompt injection, memory
   poisoning, handoff replay and tool boundaries;
4. a public open-source release candidate that stresses public-safety, CI,
   supply chain, docs quality and release control;
5. a deliberately bad product card that tries to bypass worker results,
   Product Face evidence, human gate, Auditor and Receipt Five.

## Current Score

For deterministic public preflight: `10/10`, because the branch-level audit,
schemas, scans and unit tests pass.

For real Hermes production-floor confidence: `9.4/10` at this checkpoint.
The missing 0.6 is concrete: Product Face overflow, public JSON/profile
reconciliation, documentation OS closure, remote proof retry and final Receipt
Five transition still need to complete in Hermes.

For general factory confidence across unknown future products: `9.5/10`.
The factory is now strong enough to expose the right blockers, but it is not yet
honest to call it fully validated until the pending Hermes repair cards close and
at least the next product-shaped rounds finish with real board evidence.
