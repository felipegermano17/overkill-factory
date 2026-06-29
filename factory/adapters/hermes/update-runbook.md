# Hermes Update Runbook

Do not update a real Hermes factory runtime directly. Treat every Hermes update
as runtime compatibility work plus an operational service change.

## Order

1. Identify the current Hermes version, target Hermes version and active gateway
   profile.
2. Capture read-only evidence from the real runtime before updating:
   `hermes --version`, Hermes git status, `hermes doctor`,
   `hermes gateway status`, board list, active board stats and process list.
3. Create or use a disposable Hermes checkout/runtime.
4. Apply all Overkill adapter patches in the disposable checkout.
5. Run compatibility checks and smoke tests.
6. Record the update receipt.
7. Decide whether to update the real runtime.
8. After the real update, capture the same read-only evidence again.
9. Run the update guard and do not restart the gateway while update processes or
   Kanban `running` tasks exist.
10. If the guard reports only attention items, back up config/systemd evidence,
    run `hermes doctor --fix` only when doctor reports config migration, then
    restart the gateway with the Hermes-supported system command.
11. Keep rollback ready until the first post-update factory card succeeds.

## Operational Guard

Use the public-safe guard to turn captured output into an explicit PASS,
ATTENTION or BLOCKED receipt:

```bash
python scripts/hermes_update_guard.py plan --board <board-slug>
python scripts/hermes_update_guard.py evaluate \
  --doctor .tmp/hermes-update/doctor.txt \
  --gateway-status .tmp/hermes-update/gateway-status.txt \
  --kanban-stats .tmp/hermes-update/kanban-stats.txt \
  --processes .tmp/hermes-update/processes.txt \
  --sudo-check .tmp/hermes-update/sudo-check.txt \
  --board <board-slug> \
  --out .tmp/hermes-update/update-guard.json
```

The guard blocks when an update process is still running or any Kanban task is
`running`. It reports attention when Hermes requires config migration, the
gateway unit is outdated, or the operator must run the sudo restart manually.

When the gateway status says the installed service definition is outdated, the
intended restart path is:

```bash
sudo hermes gateway restart --system
```

Run it only after:

- the active board has zero `running` tasks;
- the systemd service file and drop-ins have been snapshotted;
- `hermes doctor --fix` has been run if doctor reported config version drift;
- a human operator is present when sudo requires an interactive password.

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

If a gateway restart fails after a real update, restore the previous Hermes
checkout/ref and the snapshotted service definition before allowing factory
dispatch again.
