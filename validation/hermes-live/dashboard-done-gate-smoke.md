# Dashboard Done Gate Smoke

Date: 2026-06-06

Purpose: prove that the live Hermes dashboard/API cannot close Factory cards
when critical worker evidence is missing or weak.

## Product Face Negative Smoke

Observed result:

- dashboard/API response: HTTP 409;
- final task state: `ready`;
- gate reason mentioned `product_face_result`;
- completion-blocked event preserved the same reason;
- disposable board was removed after the smoke.

Public aliases:

- board: `public-dashboard-done-smoke-board`;
- task: `public-dashboard-done-smoke-task`.

## Solana/Quasar Auditor Negative Smoke

Observed result:

- dashboard/API response: HTTP 409;
- final task state: `ready`;
- gate reason mentioned `auditor_result` and `code_audit`;
- completion-blocked event preserved the same reason;
- disposable board was removed after the smoke.

Public aliases:

- board: `public-dashboard-auditor-smoke-board`;
- task: `public-dashboard-auditor-smoke-task`.

## Boundary

This proves live dashboard/API `done` rejection. It does not prove a real
product audit, production Product Face approval, provider-backed remote proof,
or real dispatched specialist execution.
