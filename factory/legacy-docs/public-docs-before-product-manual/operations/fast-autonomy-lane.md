# Fast Autonomy Lane

Fast autonomy is how Overkill Factory moves quickly without turning every run
into global YOLO.

The lane is an authority contract. It decides what agents may do before a human
is asked again. It does not replace Hermes, worker results, independent review,
human gates or Receipt Five.

## Modes

| Mode | Use it for | Hard stop |
| --- | --- | --- |
| `planning_only` | Source handling, scope, method routing and questions. | Material implementation. |
| `fast_autonomy` | Reversible R0/R1/R2 work such as docs, tests, local refactors, validation, fixtures and repair cards. | Production, mainnet, funds, signing, secrets, billing, destructive actions or human-gate approval. |
| `yolo_sandbox` | Throwaway R0/R1 diagnostics and experiments in a disposable environment. | R2+, persistent workspace, production-like data or missing cleanup. |
| `bounded_execution` | Normal gated worker execution after Ready Gate. | Missing worker packet, readiness or required proof. |
| `material_execution` | Higher-stakes implementation with stronger proof and review. | Unreviewed R3/R4, unclear authority or missing security architecture. |
| `production_operation` | Production operations with runbook, rollback and monitoring proof. | No human authority, no rollback or irreversible action. |

## Required Policy

Cards using `fast_autonomy` or `yolo_sandbox` must declare
`autonomy_lane_policy` and must fail closed when the policy is missing.

Required policy fields:

- `lane`
- `dispatch_authority=hermes_native_dispatch_only`
- `human_gate_authority=false`
- `production_authority=false`
- `budget`
- `allowed_work`
- `forbidden_actions`
- `human_gate_triggers`
- `stop_conditions`
- `rollback_path`
- `evidence_required`

`yolo_sandbox` additionally requires:

- `disposable_environment_required=true`
- `cleanup_required=true`

## Forbidden Everywhere In Fast Lanes

The combined card, readiness packet and lane policy must explicitly forbid:

- `production`
- `deploy`
- `mainnet`
- `funds`
- `signing`
- `secret_access`
- `billing_change`
- `destructive_action`
- `human_gate_approval`

If any of those actions are needed, the work must leave the fast lane and route
through the normal gate path.

## Runtime Boundary

Hermes remains the only worker scheduler. A fast lane may create or release
properly gated work only through the existing Hermes path. It must not create a
shadow dispatcher, approve a human gate, mark a product complete or publish a
release by itself.

Worker packets carry `autonomy_mode` and `autonomy_lane_policy` so the worker
receives the same authority envelope that `factoryctl validate-card` checked.

## Operator Interruptions

The manager/operator surface should not ask the human to approve internal
factory work. The default behavior is: keep moving and report status.

Interrupt the operator only for:

- authority that only the human has;
- access, credential, spend or account decisions;
- risk acceptance, scope change, release, mainnet, funds, signing or
  irreversible/destructive action;
- a blocker marked human-only after the factory has prepared the bounded packet.

Do not interrupt for:

- planning-only continuation, source resolution, Product SOT review, method
  routing or specialist routing when they do not change material scope or
  accept risk;
- discoverable information in source material, Hermes state, repo files or
  worker outputs;
- worker packet routing, schema details or gate report mechanics;
- missing non-human worker evidence that has a registered owner;
- recoverable non-human blockers with a repair route, retry budget and fresh
  review path.

Do not phrase these as `approve plan`, `approve planning`,
`approve specialist routing` or `approve source resolution`. They are factory
work. The operator may be notified and may receive a briefing package, but the
factory should keep moving unless a real authority trigger is present.

`factoryctl help-next` exposes this split as `user_decision_required` versus
`factory_resolved_without_user`. Telegram, Discord, Codex bridge or any other
cockpit should show the first as a real user action and the second as factory
work already owned by the system.

## Validation

Run before handing a fast-lane card to Hermes:

```bash
factoryctl validate-card path/to/card.json
factoryctl gate-report --card path/to/card.json
factoryctl worker-packet --worker all --required-only --card path/to/card.json --out .tmp/worker-packets
```

For public repo changes, also run:

```bash
python factory/scripts/validate_public_json_artifacts.py
python -m unittest tests.test_factoryctl -q
```

Do not weaken a failing validator to make a fast lane pass. Fix the authority
contract, scope, budget, rollback or risk classification.
