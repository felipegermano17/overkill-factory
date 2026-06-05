# Product Face Validator

## Purpose

Verify that product work has a visible, testable face.

## Enters

- F5 Product Face
- F13 Verification

## Input

- Product Face Packet
- design contract
- screen inventory
- state matrix
- wallet flow matrix
- breakpoints
- accessibility acceptance
- performance budget

## Output

- screenshot evidence
- mobile evidence
- state coverage result
- accessibility result
- performance result

## Hermes Gate

Cards with `ux`, `frontend`, `mobile`, or `wallet-ui` surfaces must not reach
`ready` without Product Face Packet.

## Hard Rule

Backend completion is not product completion when the user-facing surface is
undefined or unverified.
