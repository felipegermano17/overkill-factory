# Product Face Validator

## Purpose

Verify that product work has a visible, testable face.

## Enters

- F5 Product Face
- F13 Verification

## Input

- Product Experience Plan when the card is vFinal or declares Product Experience.
- Product Face Packet 2.0 with user, job-to-be-done, flows, states, design direction, proof, reviewers and human gate.
- original product promise/source refs that define what the user should feel, understand or accomplish.
- screen inventory, state matrix, wallet flow matrix, breakpoints, accessibility acceptance and performance budget.

## Output

- screenshot evidence
- mobile evidence
- state coverage result
- accessibility result
- performance result
- packet comparison result
- source-promise coverage result
- design-fit review result

## Hermes Gate

Cards with `ux`, `frontend`, `mobile`, or `wallet-ui` surfaces must not reach
`ready` without Product Face Packet.

vFinal product-facing cards must not pass card validation without Product
Experience Plan and Product Face Packet 2.0.

Product-facing completion must not pass when Product Face Result only proves
screenshots. It must also prove that the delivered surface matches the Product
Face Packet, the original product promise and the recorded visual direction.

## Hard Rule

Backend completion is not product completion when the user-facing surface is
undefined or unverified.

Visual taste is not enough. The validator approves product fit, not just whether
pixels exist.
