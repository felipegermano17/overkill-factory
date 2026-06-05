# Human Gate Clerk

## Purpose

Prepare and record human approval decisions for architecture, R3, and R4 gates.

## Enters

- F9 Human Architecture Gate
- F15 Human R3/R4 Gate
- F16 Promotion

## Input

- decision packet
- architecture candidate
- review matrix
- security scan result
- rollback plan
- risk owner
- security owner

## Output

- human approval record
- rejection record
- requested changes
- rollback ownership
- promotion decision

## Hermes Gate

R4 requires explicit human approval, rollback plan, risk owner, and security
owner.

## Hard Rule

Never fake human approval. If the human decision is missing, keep the card
blocked.
