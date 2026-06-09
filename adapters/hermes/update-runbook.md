# Hermes Update Runbook

Do not update a real Hermes factory runtime directly.

## Order

1. Identify the current Hermes version and target Hermes version.
2. Create or use a disposable Hermes checkout/runtime.
3. Apply all Overkill adapter patches.
4. Run compatibility checks.
5. Run negative and positive smoke tests.
6. Record the update receipt.
7. Decide whether to update the real runtime.
8. Keep rollback ready until the first post-update factory card succeeds.

## Required Smokes

1. Product-facing card without `product_face_packet` fails before `ready`.
2. Self-review card fails before `ready`.
3. Completion without `receipt_five` and `kanban_transition_event` fails before `done`.
4. Security-required card cannot close without `security_scan_result`.
5. Product-facing card cannot close without `product_face_result`.
6. Onchain/Solana/Quasar card cannot close when Auditor evidence is only
   preflight or lacks `audit_mode=code_audit`.
7. R4 card without `r4_gate` fails.
8. Blocked transition returns non-zero exit code.
9. Dashboard direct `ready` path cannot bypass the same gate.
10. Dashboard bulk `ready` path cannot bypass the same gate.
11. Dashboard edits/reassignments cannot leave an invalid `ready` card
   dispatchable.
12. Dashboard/API `done` failures return HTTP 409 with the gate reason.

## What To Adopt From New Hermes Releases

Adopt new Hermes features only when they map to a factory use case:

- dashboard: human supervision and gate visibility;
- admin controls: runtime safety and profile hygiene;
- memory controls: trust tier, freshness and poisoning review;
- remote gateway: remote proof and controlled operator access;
- update checks: compatibility receipt and rollback workflow;
- security fixes: always reviewed, never blindly merged.

## Rollback Rule

If any gate bypass, exit-code regression, missing symbol or public-safety leak is
found, the update is blocked. Roll back or keep the factory on the previous
runtime until the adapter is repaired.
