# Dashboard Ready Gate Smoke

Date: 2026-06-06

Purpose: prove that a live Hermes dashboard/API route cannot move an invalid
Factory card to `ready` through a direct browser/API status change.

## Setup

- Runtime: live Hermes dashboard backend.
- Board: disposable smoke board, deleted after the check.
- Card: synthetic product-facing Factory card missing `product_face_packet`.
- Attempted transition: `todo` -> `ready` through dashboard PATCH API.

## Observed Result

- HTTP response: `409`.
- Final task status: `blocked`.
- Failure reason preserved: includes missing `product_face_packet`.
- Disposable board cleanup: complete.

## Interpretation

This closes one practical bypass: dashboard direct movement to `ready` now
reuses the same Factory ready gate semantics as the Kanban kernel.

This does not prove the full runtime hook yet. The remaining Hermes work is to
prove `done`, worker/API routes and dispatched specialist execution under the
same no-bypass policy.
