# Factory 13 Agent Review Round

Date: 2026-06-06

Review version: Factory 13 builder layer.

## Scope

This review covers the public-safe worker profile, Hermes binding, worker
packet, queue, result schema, smoke and security-domain contracts.

Factory 13 adds the missing execution-builder layer and updates the review from
"profile hardening" to "profile plus real implementation ownership".

## Reviewers

| Lens | Score | Result |
|---|---:|---|
| Hermes operability | 10/10 | No concrete blocker found after the final patch round. |
| Security and domain routing | 10/10 | No concrete blocker found after the final patch round. |
| Execution ownership | 10/10 | Surface-specific builders now exist and are required by `factoryctl.py`; the generic implementation worker is fallback only. |

## Issues Closed

- Static binding queue was replaced by `dispatch_queue_policy`; runtime queue
  is computed by `factoryctl.worker_queue_class`.
- Product Face and Solana/Quasar Auditor result schemas now match the schemas
  promised by their bindings.
- Security-critical profiles now carry `domain_contract` and `waiver_contract`.
- Supply chain and Solana/Quasar/Auditor are required security domains.
- `security-orchestrator` routes before decomposition for sensitive work.
- `public-safety-gate` requires independent review.
- `security_scan_packet` can require `codex-security` even on lower-risk cards.
- `block_and_create_before_ready_tasks` is valid in transition plan, hook and
  worker-ledger schemas.
- `factoryctl transition-plan --enforce` fails closed for every blocking action.
- Hermes profile smoke is machine-readable and required for every binding.
- Ten specialist builders were added: frontend, backend/API, data persistence,
  Solana/Quasar build, Solana/Quasar QA, wallet/transaction, integration, test
  automation, infra/DevOps and agent runtime.
- `implementation-worker` was demoted to fallback-only routing.
- Solana/Quasar cards now require build and QA result fields before `done`.
- Worker scorecard records 37/37 operators at 10/10 for configuration.

## Validation

```bash
python scripts/validate_worker_profiles.py
python scripts/validate_public_json_artifacts.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python -m unittest tests.test_worker_profiles -q
python -m unittest tests.test_factoryctl -q
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/factory_completion_audit.py --no-write --require-complete
```

All commands passed in the final builder-layer run.

## Boundary

This is a 10/10 for the agent/operator configuration layer in this public-safe
repository: profile, binding, queue, packet, schema, smoke, security routing and
builder routing. It is not a claim that a future product is approved without
product-specific worker execution, Receipt Five evidence, required security
scans, Auditor evidence, monitoring, release checks and human gates.
