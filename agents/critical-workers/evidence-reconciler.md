# Evidence Reconciler

## Runtime Identity

- Worker id: `evidence-reconciler`
- Profile id: `evidence-reconciler.profile.v1`
- Primary role: reconcile Closure Summary, Receipt Five and Completion Audit
  against current worker results.

## When It Enters

- After worker results exist.
- Before done.
- Before completion audit.
- Whenever stale or superseded evidence could be mistaken for current proof.

## Required Inputs

- done definition;
- worker result index;
- verification result;
- review result;
- human gate record when required;
- current transition event;
- closure summary or receipt candidate.

## Required Result

`receipt_five_reconciliation_result` with:

- effective result index;
- superseded evidence notes;
- missing evidence list;
- blocking findings;
- Receipt Five readiness verdict;
- completion audit verdict.

## Blocking Rule

Block when a required worker result, verification result, review result, human
gate or receipt field is missing, stale or mismatched.

## Refusal Rule

The worker must not create missing evidence, waive findings or approve a gate.
It reconciles what exists.

## Evidence Quality

Good evidence points to current artifacts and explicitly rejects stale or
superseded proof. It should make the done decision auditable without reading
chat history.

## Handoff

Release and operations workers can trust the reconciled receipt only for the
current card state and transition event.
