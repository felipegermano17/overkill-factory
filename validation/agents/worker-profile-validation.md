# Worker Profile Validation

Date: 2026-06-06

## Scope

This validation covers the live agent profile layer:

- `agents/worker-profiles.public.json`
- `agents/hermes-profile-bindings.public.json`
- `schemas/worker-profile.schema.json`
- `schemas/hermes-profile-binding.schema.json`
- `scripts/validate_worker_profiles.py`
- `tests/test_worker_profiles.py`
- `docs/agents/live-agent-configuration.md`
- `docs/agents/security-specialist-matrix.md`
- `docs/agents/hermes-profile-manifest.md`
- `validation/hermes-live/factory12-agent-profile-smoke.md`
- `validation/hermes-live/factory12-agent-profile-smoke.json`
- `validation/hermes-live/factory13-devnet-receipt-pass-builder-pilot-smoke.md`
- `validation/hermes-live/factory13-devnet-receipt-pass-builder-pilot-smoke.json`
- `validation/agents/worker-scorecard-factory13.md`

## Why This Exists

The worker registry names process roles, but it does not fully define executable
agents. The profile layer closes that gap by requiring identity, authority,
tool policy, input/output contracts, evidence, review, handoff, understanding
and bounded failure behavior for every registered worker.

## Commands Run

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

## Result

All commands returned `OK` or passing unit-test output.

## What Was Proven

- Every registered worker has exactly one public-safe agent profile.
- Every registered worker has exactly one Hermes profile binding.
- Profile topology matches worker mode.
- Profile receipt field matches worker output contract.
- Hermes bindings include required skill refs.
- Worker packets now carry `profile_binding`.
- Transition plans expose profile binding on worker subtasks.
- Worker queue is computed by `factoryctl.worker_queue_class`, not duplicated as
  a static binding queue.
- Specialized workers emit the result schema promised by their binding.
- `block_and_create_before_ready_tasks` is accepted by transition-plan, hook and
  worker-ledger schemas.
- `factoryctl transition-plan --enforce` fails closed for every blocking
  transition action, including before-ready blockers.
- A `security_scan_packet` that names Codex Security makes `codex-security`
  mandatory even on R2 cards.
- Security specialists cover the required domain matrix, including supply chain
  and Solana/Quasar/Auditor as first-class domains.
- Security-critical profiles carry machine-checkable domain and waiver
  contracts.
- Hermes-bound profiles passed a public-safe structural smoke: 37/37, backed by
  machine-readable smoke JSON.
- The builder layer is now explicit: frontend, backend/API, data, Solana/Quasar
  build, Solana/Quasar QA, wallet/transaction, integration, test automation,
  infra/DevOps and agent runtime.
- `implementation-worker` is fallback only; specialist builders own matching
  product surfaces.
- A Solana/Quasar card now requires builder and QA result fields before `done`,
  in addition to Auditor, security, QA, review, handoff and human gates.
- Public JSON validation accepts the new artifacts.
- The Factory 13 Devnet Receipt Pass pilot ran a product-specific card with 28
  required workers, 28 worker result records and 8 surface-specific builders.
- `implementation-worker` was not required in that pilot because matching
  builders owned the implementation surfaces.
- Public safety scan, secret scan, full unit-test discovery and completion
  audit pass for the current branch state.

## What Was Not Proven

This validation does not prove production readiness. The Factory 13 pilot proves
bounded product-specific builder routing and evidence closure, but Solana/Quasar
build, Solana/Quasar QA and Auditor code audit remain explicit waivers until a
real Quasar-capable runtime is used.
