# Expected Flow

The local web cockpit slice starts as factory planning, not as implementation.

Expected operator observations:

1. `validate-card` passes because the card has Product SOT, Method Contract,
   Product Experience, Product Face, security and loop contracts.
2. `gate-report` identifies required workers and blocks completion until real
   worker results exist.
3. `worker-packet --required-only` writes the packets needed for the factory
   runtime to execute the slice.
4. `status-snapshot` creates a structured local snapshot suitable for cockpit
   projection tests.
5. No UI is accepted until Product Face proof includes professional visual
   quality review, screenshots, state coverage, accessibility basics,
   performance notes and independent review.

Implementation must remain blocked if:

- the proposed surface looks like a generic generated dashboard;
- it reads raw private evidence instead of structured refs;
- it treats Discord, chat history or screenshots as source of truth;
- request, approval, blocked, done, released or superseded states are visually
  ambiguous;
- local run mode is missing;
- public safety or secret scans fail.
