# Worker Completion Gate Smoke

Date: 2026-06-06

Purpose: prove that a worker-style Hermes completion path cannot close a
Factory card when the required worker result is missing.

## Product Face Worker Negative Smoke

Setup:

- disposable Hermes board alias: `public-worker-completion-smoke-board`;
- disposable task alias: `public-worker-product-face-smoke-task`;
- worker environment carried `HERMES_KANBAN_TASK` and `HERMES_KANBAN_RUN_ID`;
- completion metadata included Receipt Five but omitted `product_face_result`.

Observed result:

- worker CLI return code: `1`;
- stderr contained the gate reason `product_face_result metadata is required`;
- final task state after the rejected completion: `running`;
- active run remained open;
- last event kind: `completion_blocked_overkill_gate`;
- disposable board was removed after the smoke.

## Product Face Worker Positive Smoke

The same task was retried with a structured `product_face_result`.

Observed result:

- worker CLI return code: `0`;
- stdout contained `Completed`;
- final task state: `done`;
- active run closed;
- completion metadata preserved `product_face_result`.

## Boundary

This proves worker-style CLI completion uses the same done gate and does not
silently close a card without required evidence. It does not prove that every
specialist profile has executed real product work, nor does it prove production
Product Face, real onchain audit, deploy safety, or provider-backed remote
proof.
