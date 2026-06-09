# Product Face Packet

## Screens

- Receipt dashboard.
- Safety boundary panel.
- State matrix.
- Mobile receipt review.

## Required States

- Loading.
- Devnet OK.
- Offline.
- Error.
- Signing disabled.
- Deploy disabled.

## Acceptance

- Desktop screenshot exists.
- Mobile screenshot exists.
- No blocking overlap.
- Basic accessibility checks pass.
- Console has no blocking runtime error.
- The primary boundary is visible without relying only on color.

## Why Product Face Is Mandatory

The product is not just an API. It has a user-facing decision surface where a
human sees whether a receipt is safe to trust. A product that hides signing or
write boundaries in docs would be too easy for an autonomous worker to
misinterpret.
