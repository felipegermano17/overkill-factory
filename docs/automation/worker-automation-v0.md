# Critical Worker Automation V0

This layer turns a Factory card into explicit worker execution requests.

It is not a fake approval system. It prepares the work for Hermes agents and
keeps the factory honest about what still needs to run.

## Why This Exists

Autonomous workers fail when they receive vague tasks such as "review security"
or "check frontend." The factory needs a narrower contract:

- when the worker enters;
- why the worker is required;
- what inputs are missing;
- what evidence the worker must write;
- what gate must stay blocked until evidence exists.

This is better than generic assignment text because Hermes can inspect the
packet before execution and refuse weak cards before agents start improvising.

## Worker Profiles

Worker packets now include `profile_binding`.

That binding connects the card to:

- a public-safe agent profile in `agents/worker-profiles.public.json`;
- a Hermes profile name;
- a dispatch queue;
- required skill refs;
- the expected result schema;
- the receipt field the worker must produce.

This is better than assigning by worker name alone. Hermes profile names can
drift, skills can be missing and a worker can be too vague to operate. The
binding makes that drift visible and testable.

## CLI

Use the repo-level helper:

```bash
python scripts/factoryctl.py validate-card examples/cards/v35_valid_product_face.md
python scripts/factoryctl.py validate-receipt examples/receipts/v35_valid_completion_metadata.json
python scripts/factoryctl.py gate-report --card examples/cards/v35_valid_onchain_auditor_scan.md
python scripts/factoryctl.py worker-packet --worker all --card examples/cards/v35_valid_onchain_auditor_scan.md --out examples/worker-packets/onchain-card
python scripts/validate_worker_profiles.py
python scripts/factoryctl.py evidence-record --worker codex-security --card examples/cards/v35_valid_security_with_scan.md --result PASS --tool codex-security:security-scan --actor security-runner --evidence-ref reports/security-scan.md
python scripts/factoryctl.py human-gate-record --card examples/cards/v35_valid_onchain_auditor_scan.md --decision approved --human-actor product-owner --evidence-ref decisions/r3-human-approval.md
```

## Workers Covered

| Worker | Trigger | Output Field | Hard Block |
| --- | --- | --- | --- |
| Codex Security Runner | R3/R4 or sensitive surface | `security_scan_result` | no done/promotion without real scan evidence or human waiver |
| Solana/Quasar Auditor Runner | onchain/Solana/Quasar surface | `auditor_result` | no complete onchain work without Auditor evidence or waiver |
| Product Face Validator | UX/frontend/mobile/wallet UI surface | `product_face_result` | no product completion without visible screen/state/mobile/a11y evidence |
| Independent Reviewer | R2+ or explicit review | `independent_review_result` | no self-review; executor and reviewer must differ |
| Human Gate Clerk | architecture, R3/R4, CTO/product-owner gate | `human_gate_record` | no fake approval; missing human decision keeps card blocked |

## Status Values

`requires_execution`

The worker must run. The packet is ready enough for Hermes to assign.

`blocked_missing_inputs`

The worker is required, but the card is still missing fields the worker needs.
This is a planning failure, not an execution task.

`not_required_by_current_card`

The current card does not trigger that worker.

## R3/R4 Human Gate

R3 and R4 now require `human_gate_packet`.

R4 still additionally requires `r4_gate`.

This split matters. R3 needs explicit human risk ownership, but R4 needs a
stronger release/promotion gate with rollback and production authority details.

## What This Does Not Do Yet

This V0 does not run Codex Security, solanabr/Auditor, browser screenshots, or
human approval collection by itself.

That is intentional. A packet is not evidence. It is the handoff contract that
prevents agents from pretending a specialist review happened.

`evidence-record` and `human-gate-record` create the structured output format
after the specialist or human decision actually happened. They do not replace
the scanner, Auditor, browser validation, reviewer, or human actor.

Approved human records and PASS/WAIVED worker results require evidence refs.

## Closure Summary

After workers run, create a closure summary before Receipt Five.

This is separate from the gate report:

- gate report says which workers are required before execution;
- worker packets tell specialists what to do;
- worker results prove what happened;
- `scripts/evidence_reconciler.py` chooses the current result per receipt field,
  records superseded stale results and blocks unresolved current failures;
- closure summary explains the reconciled evidence set in human-readable form;
- Receipt Five closes the Kanban transition.

This avoids a common agent error: treating `requires_execution` in a preflight
gate report as either proof of failure or proof of completion.

## Hermes V2/V3.5 Completion Metadata

For high-risk Hermes/Overkill completion, Receipt Five must carry both the Factory
10 fields and the legacy Hermes V2 fields.

Required V3.5 security result fields:

- `scanner_agent`
- `tool`
- `scope`
- `result`
- `findings_summary`
- `evidence_refs`

Required V2 metadata when `hermes_legacy_completion_required=true`:

- `evidence_paths`
- `verification.passed=true`
- `sandbox.passed=true`
- `rollback.verified=true`
- approval records for QA, independent review, security, cybersecurity, CTO
  and product-owner gate

This is intentionally stricter than a normal task receipt. Hermes should reject
weak completion before agents can mark high-risk work done.

## Next Runtime Hook

Hermes should use the executable transition hook instead of a simple helper
call:

```bash
python adapters/hermes/transition_hook.py \
  --card path/to/card.md \
  --from-status draft \
  --to-status ready \
  --ledger path/to/worker-ledger.json \
  --out path/to/ready-hook-result.json

python adapters/hermes/transition_hook.py \
  --card path/to/card.md \
  --from-status ready \
  --to-status done \
  --receipt path/to/receipt-five.json \
  --worker-results-dir path/to/worker-results \
  --ledger path/to/worker-ledger.json \
  --out path/to/done-hook-result.json \
  --enforce
```

At `ready`, Hermes should:

- call the factory gate/reporting layer for the card;
- produce a `hermes_kanban_transition_plan`;
- create or update one Hermes subtask for each required worker;
- route each subtask by `queue_class`;
- preserve the worker packet on the subtask so the assigned worker receives the
  exact input and output contract;
- reject `ready` when card validation fails or a required worker packet is
  `blocked_missing_inputs`.

At `done`, Hermes should:

- reload the required-worker set for the card;
- inspect delivered worker results;
- run `scripts/evidence_reconciler.py` to produce the current evidence index,
  supersession ledger and `receipt_five_reconciliation_result`;
- reconcile each result against its expected Receipt Five field;
- reject missing, failed, unsupported or preflight-only results;
- reject Receipt Five without required evidence refs and transition metadata;
- allow done only when worker results and Receipt Five agree.

Hermes should reject a transition when:

- `card_validation_errors` is not empty;
- a required worker packet is `blocked_missing_inputs`;
- a required evidence field is missing from Receipt Five metadata at `done`.

The hook writes a durable worker ledger and returns a machine-readable action:
`allow_and_create_worker_tasks`, `allow_done` or `block_transition`. With
`--enforce`, blocked transitions return a non-zero exit code so Hermes cannot
silently ignore the gate.

## What Integration Still Needs

The public repository currently documents and validates the contract, and now
includes the executable hook Hermes should call. It does not yet make a live
Hermes runtime perform automatic orchestration without wiring this hook into the
runtime.

Real integration still needs:

- Kanban transition event wiring for `ready` and `done`;
- mapping hook ledger rows to real Hermes subtasks;
- queue mapping for `blocking-before-ready`, `blocking-before-done` and
  `advisory-review`;
- result ingestion from worker artifacts into card metadata or Receipt Five;
- a single gate path shared by CLI, dashboard, API and worker-driven updates;
- clear blocked-state messages for missing inputs and missing evidence;
- regression tests proving dashboard/API paths cannot bypass CLI behavior;
- a disposable Hermes smoke before any real runtime update.
