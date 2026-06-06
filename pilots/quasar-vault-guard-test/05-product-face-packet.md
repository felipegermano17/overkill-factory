# F5 Product Face Packet

## Screen Inventory

| Screen | Purpose |
| --- | --- |
| Vault Guard Dashboard | Main operator view for a pending vault instruction. |
| Evidence Drawer | Shows security, Auditor, human gate, and Receipt Five status. |
| Mobile Review View | Same decision on narrow viewport. |

## State Matrix

| State | UI Requirement |
| --- | --- |
| Loading | Show skeleton/status that data is being prepared. |
| Unknown | Show missing evidence and disable action. |
| Safe | Show pass status and required evidence refs. |
| Blocked | Show blocking reason and next owner. |
| Simulation Failed | Show simulation error and retry boundary. |
| Wallet Rejected | Show rejected wallet action without retry loop. |

## Wallet Flow Matrix

| Flow | Expected Behavior |
| --- | --- |
| Connect wallet | Show connected identity, no signing. |
| Sign requested | Forbidden in pilot. UI must show action disabled. |
| User rejects | Show rejection state and no background retry. |
| Unknown authority | Block and request human/security review. |

## Breakpoints

- `375px` mobile.
- `768px` tablet.
- `1440px` desktop.

## Accessibility

- Keyboard-visible controls.
- High-contrast status labels.
- No color-only risk state.
- Buttons must have clear labels.

## Performance Budget

- Static prototype should load without external assets.
- No network dependency for pilot evidence.
- Primary decision must be visible above the fold.

## Visual Evidence Plan

- Desktop screenshot.
- Mobile screenshot.
- HTML prototype source.
- Product Face validation report.
