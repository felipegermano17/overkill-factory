# Factory Operating Systems

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `templates/factory-operating-system-registry.json`,
> `schemas/factory-operating-system-registry.schema.json`,
> `scripts/factoryctl.py`, tests.
> Runtime boundary: this registry maps owners and proof obligations. It does
> not claim product-specific production readiness by itself.

Overkill Factory has many contracts. The operating-system registry groups the
critical areas that must behave like systems instead of scattered documents.

An OS is allowed only when the area is repeated, cross-cutting, risky enough to
need gates, and important enough that the operator should not coordinate it by
hand.

## Canonical OS Set

Run:

```bash
factoryctl operating-systems
factoryctl validate-operating-systems templates/factory-operating-system-registry.json
factoryctl operating-system-scorecard
factoryctl operating-system-scorecard --runtime-proof .tmp/factory-runs/hermes-runtime/hermes-worker-runtime-proof.json
```

The current set is:

| Priority | OS | Issue | Why it exists |
| --- | --- | --- | --- |
| P0 | Product Truth and Research OS | #401 | Prevents shallow starts and unsafe Product SOT promotion. |
| P0 | Method OS | #400 | Makes method routing executable through method engines. |
| P0 | Authority and Autonomy OS | #402 | Reduces unnecessary human gates without allowing unsafe YOLO. |
| P0 | Hermes Worker Runtime OS | #403 | Proves live worker orchestration, profile freshness and no-idle behavior. |
| P0 | Evidence and Product Proof OS | #404 | Separates contract proof, runtime proof and product-specific proof. |
| P0 | Capability and Domain Pack OS | #405 | Activates domain packs deterministically, including `solana-ai-kit-core`. |
| P0 | Operator Experience OS | #406 | Makes Telegram-first operation proactive and deep enough for real decisions. |
| P0 | Security and Release OS | #407 | Owns high-risk release, secrets, supply chain, rollback and R4 authority. |
| P1 | Product Quality OS | #408 | Extends Product Experience OS into complete product quality. |
| P1 | Velocity and Cost OS | #409 | Governs speed, parallelism, budgets, dedupe and stop conditions. |
| P1 | Factory Learning OS | #410 | Keeps learnback and Hermes `/learn` as inactive, reviewed proposals. |

## Method OS Engines

Method OS is the first OS with a dedicated engine registry:

```bash
factoryctl method-engines
factoryctl validate-method-engines templates/method-engine-registry.json
```

The Method Contract must bind every selected method to a selected engine. For
example, `spec-first` maps to `spec_first_sdd` and `test-first` maps to
`test_first_tdd`. Engine selection still does not allow execution; it only
declares required artifacts, gates, workers and proof.

## Claim Boundary

The registry is not production proof.

It can say which OS owns a risk, which issue tracks the work, which contracts
must exist and which runtime proofs are required. It cannot say a product is
done, released, customer-ready or mainnet-safe.

Production claims still require:

- Hermes runtime state;
- current worker results;
- Receipt Five;
- product-specific proof;
- human gates when risk requires them;
- release, rollback and monitoring evidence.

`factoryctl operating-system-scorecard` is intentionally stricter than the
registry. It returns `BLOCKED` while P0 systems are only planned, while runtime
proof is missing, or while a completion-audit blocker maps to an OS owner. That
blocked state is valid evidence; it prevents overclaiming.

## Runtime Proof

Hermes Worker Runtime OS is the only P0 OS whose readiness cannot be proven by
repo contracts alone. The public-safe proof path is:

```bash
python scripts/hermes_runtime_proof.py \
  --boards-json .tmp/hermes-runtime/boards.json \
  --profile-list-text .tmp/hermes-runtime/profile-list.txt \
  --status-text .tmp/hermes-runtime/status.txt \
  --task-list-json .tmp/hermes-runtime/task-list.json \
  --done-task-runs-json .tmp/hermes-runtime/done-task-runs.json \
  --blocked-task-show-json .tmp/hermes-runtime/blocked-task-show.json \
  --out .tmp/factory-runs/hermes-runtime/hermes-worker-runtime-proof.json

factoryctl operating-system-scorecard \
  --runtime-proof .tmp/factory-runs/hermes-runtime/hermes-worker-runtime-proof.json \
  --out .tmp/factory-runs/operating-systems/factory-operating-system-scorecard-runtime-proven.json
```

The proof file is deliberately redacted. It keeps counts and state flags such as
gateway running, Codex auth, Telegram configured, manager profile running,
representative worker run completed, and human gate blocked. It must not embed
raw private card bodies, product material, local paths or operator data.

A `PASS` scorecard with runtime proof means the factory operating spine has no
P0 OS blocker at that proof level. It still does not mean a specific product is
complete, released, mainnet-safe or customer-ready. Product claims remain under
the completion audit, Receipt Five and product-specific evidence.

## Anti-Bureaucracy Rule

Do not create an OS for a one-off artifact. Create or keep an OS only when it
reduces manual coordination and makes the factory faster, safer or more
auditable.

If a proposed OS does not have an issue, owner worker, fail-closed rule,
runtime boundary and proof obligation, it should remain a doc section,
template or checklist.
